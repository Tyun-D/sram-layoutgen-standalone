"""Read-only OpenYield decoder row-rule and stage-packing audit helpers.

This module builds on the Step 6.9 decoder stage candidate audit and stays
strictly metadata-only. It does not create decoder placement or GDS output.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from .decoder_stage_candidates import (
    build_decoder_stage_candidate_report,
    md_table,
    _notes_text,
)


@dataclass(frozen=True)
class DecoderStagePacking:
    stage_name: str
    level: int
    decoder_index: int
    row_name: str
    row_role: str
    input_nets: tuple[str, ...]
    enable_net: str
    output_nets: tuple[str, ...]
    input_side_hint: str
    output_side_hint: str
    enable_side_hint: str
    estimated_cell_count: int
    candidate_bbox: dict[str, float]
    metadata_only: bool
    pin_proven: bool
    physical_routing_proven: bool
    notes: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class DecoderRowRule:
    rule_name: str
    target_candidate: str
    stage_level: int
    stage_count: int
    logic_cell_sequence: tuple[str, ...]
    local_macro_candidates: tuple[str, ...]
    missing_macros: tuple[str, ...]
    input_side: str
    output_side: str
    enable_side: str
    power_policy: str
    pin_metadata_status: str
    placement_status: str
    physical_routing_proven: bool
    notes: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def build_decoder_row_rule_report(
    openyield_root: str | Path,
    contracts_path: str | Path,
    tech_dir: str | Path,
    addr_width: int = 5,
    num_rows: int | None = None,
    gds_pin_report_path: str | Path | None = None,
    decomposition_report_path: str | Path | None = None,
    target_envelope_report_path: str | Path | None = None,
) -> tuple[dict[str, Any], dict[str, Any]]:
    stage_report, _stage_graph = build_decoder_stage_candidate_report(
        openyield_root=openyield_root,
        contracts_path=contracts_path,
        tech_dir=tech_dir,
        addr_width=addr_width,
        num_rows=num_rows,
        gds_pin_report_path=gds_pin_report_path,
        decomposition_report_path=decomposition_report_path,
        target_envelope_report_path=target_envelope_report_path,
    )

    macro_index = {item["macro_name"]: item for item in stage_report["local_macro_availability"]}
    dims = _macro_dimensions(gds_pin_report_path)
    stage_instances = stage_report["decoder_cascade_hierarchy"]["stage_instances"]

    and2_macro_width = dims.get("gen_nand2", {}).get("width", 0.0) + dims.get("gen_inv", {}).get("width", 0.0)
    and3_proxy_width = dims.get("gen_nand4", {}).get("width", 0.0) + dims.get("gen_inv", {}).get("width", 0.0)
    inv_width = dims.get("gen_inv", {}).get("width", 0.0)
    row_height = max(
        dims.get("gen_inv", {}).get("height", 0.0),
        dims.get("gen_nand2", {}).get("height", 0.0),
        dims.get("gen_nand4", {}).get("height", 0.0),
        dims.get("gen_wl_driver", {}).get("height", 0.0),
    )
    row_gap = row_height

    stage_logic_cell_count = {
        "pinv": 3,
        "and2": 8,
        "and3": 8,
        "resolved_cells_without_pnand3": 19,
        "unresolved_pnand3_like_cells": 8,
        "upper_bound_with_nand4_proxy": 27,
    }
    base_stage_width = round((3 * inv_width) + (8 * and2_macro_width) + (8 * and3_proxy_width), 6)
    packing_plan = _build_stage_packing(stage_instances, base_stage_width, row_height, row_gap, stage_logic_cell_count["upper_bound_with_nand4_proxy"])

    gen_nand4_metadata_complete = bool(
        macro_index.get("gen_nand4", {}).get("labels_available")
        and macro_index.get("gen_nand4", {}).get("power_metadata_available")
    )
    gen_nand4_can_substitute_pnand3 = "not_safe_for_physical"
    if macro_index.get("gen_nand4", {}).get("gds_available"):
        gen_nand4_can_substitute_pnand3 = "metadata_only_possible"

    direct_nand3_missing = stage_report["decoder_direct_and3_or_nand3_missing"]
    decoder_generated_logic_unresolved = True
    pin_metadata_complete = bool(
        macro_index.get("gen_inv", {}).get("labels_available")
        and macro_index.get("gen_nand2", {}).get("labels_available")
        and gen_nand4_metadata_complete
    )
    power_metadata_complete = bool(
        macro_index.get("gen_inv", {}).get("power_metadata_available")
        and macro_index.get("gen_nand2", {}).get("power_metadata_available")
        and gen_nand4_metadata_complete
    )

    row_rules = [
        DecoderRowRule(
            rule_name="DECODER_LEVEL0_ROW_RULE",
            target_candidate="DECODER_LEVEL0_ROW",
            stage_level=0,
            stage_count=1,
            logic_cell_sequence=("Pinv", "AND3", "AND2"),
            local_macro_candidates=("gen_inv", "gen_nand2", "gen_nand4"),
            missing_macros=("gen_nand3",),
            input_side="decoder_input_side",
            output_side="east_enable_bus_side",
            enable_side="north_or_tiehigh_side",
            power_policy="local_horizontal_vdd_gnd_only_no_shared_rail",
            pin_metadata_status="partial",
            placement_status="needs_power_metadata_repair",
            physical_routing_proven=False,
            notes=(
                "Level 0 consumes high-order address bits and emits intermediate enable nets.",
                "Tie-high enable uses VDD metadata only; no physical rail proof exists.",
                "AND3 still depends on unresolved PNAND3-like implementation.",
            ),
        ),
        DecoderRowRule(
            rule_name="DECODER_LEVEL1_ROW_RULE",
            target_candidate="DECODER_LEVEL1_ROW_GROUP_*",
            stage_level=1,
            stage_count=4,
            logic_cell_sequence=("Pinv", "AND3", "AND2"),
            local_macro_candidates=("gen_inv", "gen_nand2", "gen_nand4", "gen_wl_driver"),
            missing_macros=("gen_nand3",),
            input_side="west_addr_side",
            output_side="east_wordline_side",
            enable_side="north_enable_bus_side",
            power_policy="local_horizontal_vdd_gnd_only_no_shared_rail",
            pin_metadata_status="partial",
            placement_status="needs_logic_macro_repair",
            physical_routing_proven=False,
            notes=(
                "Each level-1 group is one DECODER3_8 stage driven by one intermediate enable net.",
                "Wordline output ordering is semantic-only and still lacks per-stage physical pin proof.",
                "gen_wl_driver remains a downstream consumer, not a decoder stage leaf.",
            ),
        ),
        DecoderRowRule(
            rule_name="DECODER_STAGE_PROXY_RULE",
            target_candidate="DECODER3_8_GROUP",
            stage_level=-1,
            stage_count=5,
            logic_cell_sequence=("3x Pinv", "8x AND3", "8x AND2"),
            local_macro_candidates=("gen_inv", "gen_nand2", "gen_nand4"),
            missing_macros=("gen_nand3",),
            input_side="left",
            output_side="right",
            enable_side="top",
            power_policy="metadata_only_proxy_power_policy",
            pin_metadata_status="partial",
            placement_status="metadata_row_rule_only",
            physical_routing_proven=False,
            notes=(
                "This is an audit-only proxy rule for stage geometry estimation.",
                "Linear cell-count packing is pessimistic and should not be treated as legal placement geometry.",
            ),
        ),
    ]

    logic_cell_availability = {
        "Pinv_to_gen_inv": {
            "mapping": "direct_metadata_candidate",
            "gds_available": macro_index.get("gen_inv", {}).get("gds_available"),
            "spice_available": macro_index.get("gen_inv", {}).get("spice_available"),
            "pin_metadata_complete": macro_index.get("gen_inv", {}).get("labels_available"),
            "power_metadata_complete": macro_index.get("gen_inv", {}).get("power_metadata_available"),
            "safe_for_physical_placement": macro_index.get("gen_inv", {}).get("safe_for_physical_placement"),
        },
        "PNAND2_to_gen_nand2": {
            "mapping": "direct_metadata_candidate",
            "gds_available": macro_index.get("gen_nand2", {}).get("gds_available"),
            "spice_available": macro_index.get("gen_nand2", {}).get("spice_available"),
            "pin_metadata_complete": macro_index.get("gen_nand2", {}).get("labels_available"),
            "power_metadata_complete": macro_index.get("gen_nand2", {}).get("power_metadata_available"),
            "safe_for_physical_placement": macro_index.get("gen_nand2", {}).get("safe_for_physical_placement"),
        },
        "AND2_to_gen_nand2_plus_gen_inv": {
            "mapping": "composite_metadata_candidate",
            "required_cells": {"gen_nand2": 1, "gen_inv": 1},
            "resolved": True,
            "safe_for_physical_placement": False,
        },
        "PNAND3_direct": {
            "mapping": "missing_direct_macro",
            "direct_nand3_available": False,
        },
        "AND3_resolution": {
            "mapping": "generated_logic_unresolved",
            "required_cells": {"pnand3_like": 1, "gen_inv": 1},
            "gen_nand4_substitution": gen_nand4_can_substitute_pnand3,
            "safe_for_physical_placement": False,
        },
    }

    pin_metadata_audit = _build_pin_metadata_audit(macro_index)
    power_metadata_audit = _build_power_metadata_audit(macro_index)
    decoder_row_rules_available = True
    decoder_stage_packing_available = True
    decoder_logic_row_metadata_available = True
    can_enter_decoder_generated_block_planning = True
    can_enter_physical_decoder_placement = False
    can_enter_very_limited_control_row_smoke = False

    blockers = [
        "Direct PNAND3 / AND3 hard macro is still missing, so decoder stage logic is not fully resolved.",
        "gen_nand4 is not pin/power metadata complete and cannot be treated as a proven PNAND3 replacement.",
        "Shared rail safety is not proven for decoder generated-logic rows.",
        "Per-stage pin metadata is only partial and output routing toward WORDLINEDRIVER.A remains unproven.",
        "Row-rule and stage-packing data are metadata planning aids only, not legal decoder placement evidence.",
    ]

    report = {
        "scope": "step6_10_openyield_decoder_row_rule_audit",
        "addr_width": stage_report["addr_width"],
        "num_rows": stage_report["num_rows"],
        "decoder_hierarchy": stage_report["decoder_cascade_hierarchy"],
        "stage_packing_plan": [item.to_dict() for item in packing_plan],
        "decoder_row_rules": [item.to_dict() for item in row_rules],
        "logic_cell_availability": logic_cell_availability,
        "logic_cell_count_per_stage": stage_logic_cell_count,
        "direct_nand3_and3_missing": direct_nand3_missing,
        "gen_nand4_gds_available": macro_index.get("gen_nand4", {}).get("gds_available"),
        "gen_nand4_label_metadata_complete": macro_index.get("gen_nand4", {}).get("labels_available"),
        "gen_nand4_power_metadata_complete": macro_index.get("gen_nand4", {}).get("power_metadata_available"),
        "gen_nand4_can_substitute_pnand3": gen_nand4_can_substitute_pnand3,
        "pin_metadata_audit": pin_metadata_audit,
        "power_metadata_audit": power_metadata_audit,
        "decoder_input_handoff": stage_report["input_handoff"],
        "decoder_output_handoff": stage_report["output_handoff"],
        "decoder_row_rules_available": decoder_row_rules_available,
        "decoder_stage_packing_available": decoder_stage_packing_available,
        "decoder_logic_row_metadata_available": decoder_logic_row_metadata_available,
        "decoder_direct_nand3_missing": direct_nand3_missing,
        "decoder_generated_logic_unresolved": decoder_generated_logic_unresolved,
        "decoder_power_metadata_complete": power_metadata_complete,
        "decoder_pin_metadata_complete": pin_metadata_complete,
        "can_enter_decoder_generated_block_planning": can_enter_decoder_generated_block_planning,
        "can_enter_physical_decoder_placement": can_enter_physical_decoder_placement,
        "can_enter_very_limited_control_row_smoke": can_enter_very_limited_control_row_smoke,
        "standalone_modified": False,
        "routing_modified": False,
        "gds_writer_modified": False,
        "blocker_list": blockers,
        "step_6_11_recommendation": "Audit decoder logic leaf repair options next: prove or reject PNAND3 substitution strategy, then define per-stage pin/power metadata before any decoder physical smoke.",
    }

    graph = {
        "scope": report["scope"],
        "nodes": _build_graph_nodes(packing_plan, row_rules, pin_metadata_audit, power_metadata_audit),
        "edges": _build_graph_edges(packing_plan),
        "blockers": blockers,
    }
    return report, graph


def build_decoder_row_rule_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# OpenYield Decoder Row Rule Audit",
        "",
        "This is a metadata-only decoder generated-logic row-rule and stage-packing audit. It does not modify standalone.py, routing, or the GDS writer.",
        "",
        "## Summary",
        "",
        f"- addr_width: `{report['addr_width']}`",
        f"- num_rows: `{report['num_rows']}`",
        f"- decoder_row_rules_available: `{report['decoder_row_rules_available']}`",
        f"- decoder_stage_packing_available: `{report['decoder_stage_packing_available']}`",
        f"- decoder_logic_row_metadata_available: `{report['decoder_logic_row_metadata_available']}`",
        f"- decoder_direct_nand3_missing: `{report['decoder_direct_nand3_missing']}`",
        f"- decoder_generated_logic_unresolved: `{report['decoder_generated_logic_unresolved']}`",
        f"- decoder_power_metadata_complete: `{report['decoder_power_metadata_complete']}`",
        f"- decoder_pin_metadata_complete: `{report['decoder_pin_metadata_complete']}`",
        f"- can_enter_decoder_generated_block_planning: `{report['can_enter_decoder_generated_block_planning']}`",
        f"- can_enter_physical_decoder_placement: `{report['can_enter_physical_decoder_placement']}`",
        f"- can_enter_very_limited_control_row_smoke: `{report['can_enter_very_limited_control_row_smoke']}`",
        "",
        "## Decoder Hierarchy",
        "",
        f"- n_levels: `{report['decoder_hierarchy']['n_levels']}`",
        f"- level_groups: `{report['decoder_hierarchy']['level_groups']}`",
        f"- total_decoder3_8_instances: `{report['decoder_hierarchy']['total_decoder3_8_instances']}`",
        "",
        "## Stage Packing Plan",
        "",
        md_table(
            ["row_name", "stage_name", "level", "decoder_index", "enable_net", "input_side", "output_side", "estimated_cell_count", "candidate_bbox", "notes"],
            [
                [
                    item["row_name"],
                    item["stage_name"],
                    item["level"],
                    item["decoder_index"],
                    item["enable_net"],
                    item["input_side_hint"],
                    item["output_side_hint"],
                    item["estimated_cell_count"],
                    json.dumps(item["candidate_bbox"], ensure_ascii=False),
                    _notes_text(item["notes"]),
                ]
                for item in report["stage_packing_plan"]
            ],
        ),
        "",
        "## Decoder Row Rules",
        "",
        md_table(
            ["rule", "target", "level", "stage_count", "logic_cell_sequence", "input_side", "output_side", "enable_side", "power_policy", "pin_metadata_status", "placement_status"],
            [
                [
                    item["rule_name"],
                    item["target_candidate"],
                    item["stage_level"],
                    item["stage_count"],
                    ", ".join(item["logic_cell_sequence"]),
                    item["input_side"],
                    item["output_side"],
                    item["enable_side"],
                    item["power_policy"],
                    item["pin_metadata_status"],
                    item["placement_status"],
                ]
                for item in report["decoder_row_rules"]
            ],
        ),
        "",
        "## Logic Cell Availability",
        "",
        "```json",
        json.dumps(report["logic_cell_availability"], ensure_ascii=False, indent=2),
        "```",
        "",
        "## Pin Metadata Audit",
        "",
        md_table(
            ["macro", "required_pins", "available_labels", "missing_labels", "pin_metadata_complete", "power_metadata_complete", "safe_for_metadata_mapping", "safe_for_physical_placement"],
            [
                [
                    item["macro"],
                    ", ".join(item["required_pins"]),
                    ", ".join(item["available_labels"]) or "-",
                    ", ".join(item["missing_labels"]) or "-",
                    item["pin_metadata_complete"],
                    item["power_metadata_complete"],
                    item["safe_for_metadata_mapping"],
                    item["safe_for_physical_placement"],
                ]
                for item in report["pin_metadata_audit"]
            ],
        ),
        "",
        "## Power Metadata Audit",
        "",
        md_table(
            ["macro", "row_power_policy", "local_power_pins_available", "rail_continuity_proven", "safe_for_shared_rail", "power_metadata_blockers"],
            [
                [
                    item["macro"],
                    item["row_power_policy"],
                    item["local_power_pins_available"],
                    item["rail_continuity_proven"],
                    item["safe_for_shared_rail"],
                    _notes_text(item["power_metadata_blockers"]),
                ]
                for item in report["power_metadata_audit"]
            ],
        ),
        "",
        "## Input Handoff",
        "",
        "```json",
        json.dumps(report["decoder_input_handoff"], ensure_ascii=False, indent=2),
        "```",
        "",
        "## Output Handoff",
        "",
        "```json",
        json.dumps(report["decoder_output_handoff"], ensure_ascii=False, indent=2),
        "```",
        "",
        "## Blockers",
        "",
        *[f"- {item}" for item in report["blocker_list"]],
        "",
        "## Step 6.11 Recommendation",
        "",
        f"- {report['step_6_11_recommendation']}",
        "",
    ]
    return "\n".join(lines)


def write_decoder_row_rule_reports(
    openyield_root: str | Path,
    contracts_path: str | Path,
    tech_dir: str | Path,
    addr_width: int,
    out_json: str | Path,
    out_md: str | Path,
    out_graph: str | Path,
    num_rows: int | None = None,
    gds_pin_report_path: str | Path | None = None,
    decomposition_report_path: str | Path | None = None,
    target_envelope_report_path: str | Path | None = None,
) -> dict[str, Any]:
    report, graph = build_decoder_row_rule_report(
        openyield_root=openyield_root,
        contracts_path=contracts_path,
        tech_dir=tech_dir,
        addr_width=addr_width,
        num_rows=num_rows,
        gds_pin_report_path=gds_pin_report_path,
        decomposition_report_path=decomposition_report_path,
        target_envelope_report_path=target_envelope_report_path,
    )
    out_json = Path(out_json)
    out_md = Path(out_md)
    out_graph = Path(out_graph)
    out_json.parent.mkdir(parents=True, exist_ok=True)
    out_md.parent.mkdir(parents=True, exist_ok=True)
    out_graph.parent.mkdir(parents=True, exist_ok=True)
    out_json.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    out_md.write_text(build_decoder_row_rule_markdown(report), encoding="utf-8")
    out_graph.write_text(json.dumps(graph, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return report


def _macro_dimensions(gds_pin_report_path: str | Path | None) -> dict[str, dict[str, float]]:
    if gds_pin_report_path is None:
        return {}
    path = Path(gds_pin_report_path)
    if not path.exists():
        return {}
    payload = json.loads(path.read_text(encoding="utf-8"))
    dims: dict[str, dict[str, float]] = {}
    for item in payload.get("audited_macros", []):
        dims[str(item.get("macro_name"))] = {
            "width": float(item.get("width") or 0.0),
            "height": float(item.get("height") or 0.0),
        }
    return dims


def _build_stage_packing(
    stage_instances: list[dict[str, Any]],
    base_stage_width: float,
    row_height: float,
    row_gap: float,
    estimated_cell_count: int,
) -> list[DecoderStagePacking]:
    items: list[DecoderStagePacking] = []
    for idx, item in enumerate(stage_instances):
        level = int(item["level"])
        decoder_index = int(item["decoder_index"])
        row_name = "DECODER_LEVEL0_ROW" if level == 0 else f"DECODER_LEVEL1_ROW_GROUP_{decoder_index}"
        y0 = round(idx * (row_height + row_gap), 6)
        bbox = {
            "x0": 0.0,
            "y0": y0,
            "x1": round(base_stage_width, 6),
            "y1": round(y0 + row_height, 6),
            "width": round(base_stage_width, 6),
            "height": round(row_height, 6),
        }
        notes = [
            "Estimated bbox uses a pessimistic linear macro proxy and is metadata-only.",
        ]
        if level == 0:
            notes.append("Output side is an intermediate enable bus, not final WL pins.")
        else:
            notes.append("Output side targets WL nets for downstream WORDLINEDRIVER.A handoff.")
        items.append(
            DecoderStagePacking(
                stage_name=str(item["stage_name"]),
                level=level,
                decoder_index=decoder_index,
                row_name=row_name,
                row_role=str(item["output_role"]),
                input_nets=tuple(item["address_node_order"]),
                enable_net=str(item["enable_net"]),
                output_nets=tuple(item["output_nets"]),
                input_side_hint="decoder_input_side",
                output_side_hint="east_enable_bus_side" if level == 0 else "wordline_driver_side",
                enable_side_hint="north_tiehigh_side" if level == 0 else "north_enable_bus_side",
                estimated_cell_count=estimated_cell_count,
                candidate_bbox=bbox,
                metadata_only=True,
                pin_proven=False,
                physical_routing_proven=False,
                notes=tuple(notes),
            )
        )
    return items


def _build_pin_metadata_audit(macro_index: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    required = {
        "gen_inv": ("a", "z", "vdd", "gnd"),
        "gen_nand2": ("a", "b", "z", "vdd", "gnd"),
        "gen_nand4": ("a", "b", "c", "d", "z", "vdd", "gnd"),
        "gen_wl_driver": ("decoder_input", "wordline_enable", "wl", "vdd", "gnd"),
    }
    result: list[dict[str, Any]] = []
    for macro, pins in required.items():
        item = macro_index.get(macro, {})
        available = []
        if item.get("labels_available"):
            if macro == "gen_inv":
                available = ["a", "z", "vdd", "gnd"]
            elif macro == "gen_nand2":
                available = ["a", "b", "z", "vdd", "gnd"]
            elif macro == "gen_wl_driver":
                available = ["decoder_input", "wordline_enable", "wl", "vdd", "gnd"]
        missing = [pin for pin in pins if pin not in available]
        result.append(
            {
                "macro": macro,
                "required_pins": list(pins),
                "available_labels": available,
                "missing_labels": missing,
                "pin_metadata_complete": len(missing) == 0,
                "power_metadata_complete": bool(item.get("power_metadata_available")),
                "safe_for_metadata_mapping": bool(item.get("safe_for_metadata_mapping")),
                "safe_for_physical_placement": bool(item.get("safe_for_physical_placement")),
            }
        )
    return result


def _build_power_metadata_audit(macro_index: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    macros = ("gen_inv", "gen_nand2", "gen_nand4", "gen_wl_driver")
    result: list[dict[str, Any]] = []
    for macro in macros:
        item = macro_index.get(macro, {})
        blockers = []
        if not item.get("power_metadata_available"):
            blockers.append("power_metadata_incomplete")
        blockers.append("rail_continuity_not_proven")
        blockers.append("shared_rail_not_allowed_for_decoder_generated_logic")
        result.append(
            {
                "macro": macro,
                "row_power_policy": "local_horizontal_vdd_gnd_only_no_shared_rail",
                "local_power_pins_available": bool(item.get("power_metadata_available")),
                "rail_continuity_proven": False,
                "safe_for_shared_rail": False,
                "power_metadata_blockers": blockers,
            }
        )
    return result


def _build_graph_nodes(
    packing_plan: list[DecoderStagePacking],
    row_rules: list[DecoderRowRule],
    pin_metadata_audit: list[dict[str, Any]],
    power_metadata_audit: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    nodes: list[dict[str, Any]] = []
    for item in packing_plan:
        nodes.append({"id": item.row_name, "kind": "stage_row", "level": item.level})
    for item in row_rules:
        nodes.append({"id": item.rule_name, "kind": "row_rule", "placement_status": item.placement_status})
    for item in pin_metadata_audit:
        nodes.append({"id": f"{item['macro']}_pin_meta", "kind": "pin_metadata", "complete": item["pin_metadata_complete"]})
    for item in power_metadata_audit:
        nodes.append({"id": f"{item['macro']}_power_meta", "kind": "power_metadata", "complete": item["local_power_pins_available"]})
    return nodes


def _build_graph_edges(packing_plan: list[DecoderStagePacking]) -> list[dict[str, Any]]:
    edges: list[dict[str, Any]] = []
    for item in packing_plan:
        edges.append({"source": item.row_name, "target": "DECODER3_8_GROUP", "relation": "packs_stage"})
    edges.extend(
        [
            {"source": "DECODER_LEVEL0_ROW", "target": "DECODER_LEVEL0_ROW_RULE", "relation": "governed_by"},
            {"source": "DECODER_LEVEL1_ROW_GROUP_0", "target": "DECODER_LEVEL1_ROW_RULE", "relation": "governed_by"},
            {"source": "DECODER_LEVEL1_ROW_GROUP_1", "target": "DECODER_LEVEL1_ROW_RULE", "relation": "governed_by"},
            {"source": "DECODER_LEVEL1_ROW_GROUP_2", "target": "DECODER_LEVEL1_ROW_RULE", "relation": "governed_by"},
            {"source": "DECODER_LEVEL1_ROW_GROUP_3", "target": "DECODER_LEVEL1_ROW_RULE", "relation": "governed_by"},
        ]
    )
    return edges
