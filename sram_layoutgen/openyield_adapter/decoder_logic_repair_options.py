"""Read-only OpenYield decoder logic repair-option audit helpers.

This module compares metadata-only repair options for missing PNAND3 / AND3
decoder leaves. It does not modify routing, placement, standalone flow, or GDS.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from .decoder_row_rules import build_decoder_row_rule_report
from .decoder_stage_candidates import md_table, _notes_text


@dataclass(frozen=True)
class RepairOption:
    option_name: str
    status: str
    pnand3_direct_macro_available: bool
    and3_direct_macro_available: bool
    safe_for_metadata_planning: bool | str
    safe_for_physical_placement: bool
    logic_equivalence_metadata_proven: bool | None = None
    required_cells: dict[str, int] | None = None
    base_macro: str | None = None
    intended_logic: str | None = None
    unused_input_strategy: tuple[str, ...] = ()
    unused_input_tie_policy_proven: bool | None = None
    requires_pin_metadata_repair: bool = False
    requires_power_metadata_repair: bool = False
    requires_unused_input_tie_proof: bool = False
    gen_nand4_gds_available: bool | None = None
    gen_nand4_spice_available: bool | None = None
    gen_nand4_labels_available: bool | None = None
    gen_nand4_power_metadata_complete: bool | None = None
    gen_nand4_logic_polarity_confirmed: bool | None = None
    notes: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def build_decoder_logic_repair_report(
    openyield_root: str | Path,
    contracts_path: str | Path,
    tech_dir: str | Path,
    addr_width: int = 5,
    num_rows: int | None = None,
    gds_pin_report_path: str | Path | None = None,
    decomposition_report_path: str | Path | None = None,
    target_envelope_report_path: str | Path | None = None,
) -> tuple[dict[str, Any], dict[str, Any]]:
    row_report, _row_graph = build_decoder_row_rule_report(
        openyield_root=openyield_root,
        contracts_path=contracts_path,
        tech_dir=tech_dir,
        addr_width=addr_width,
        num_rows=num_rows,
        gds_pin_report_path=gds_pin_report_path,
        decomposition_report_path=decomposition_report_path,
        target_envelope_report_path=target_envelope_report_path,
    )

    macro_index = {
        item["macro"]: item for item in row_report["pin_metadata_audit"]
    }
    power_index = {
        item["macro"]: item for item in row_report["power_metadata_audit"]
    }
    stage_count = int(row_report["decoder_hierarchy"]["total_decoder3_8_instances"])
    stage_subcells = {
        "pinv": 3,
        "and2": 8,
        "and3": 8,
    }

    gen_inv_ok = bool(macro_index["gen_inv"]["safe_for_metadata_mapping"])
    gen_nand2_ok = bool(macro_index["gen_nand2"]["safe_for_metadata_mapping"])
    gen_nand4_ok = bool(macro_index["gen_nand4"]["safe_for_metadata_mapping"])
    gen_nand4_labels_complete = bool(macro_index["gen_nand4"]["pin_metadata_complete"])
    gen_nand4_power_complete = bool(macro_index["gen_nand4"]["power_metadata_complete"])

    option_direct = RepairOption(
        option_name="direct_pnand3_and3_macro",
        status="unavailable",
        pnand3_direct_macro_available=False,
        and3_direct_macro_available=False,
        safe_for_metadata_planning=False,
        safe_for_physical_placement=False,
        notes=(
            "No direct local gen_nand3 / PNAND3 hard macro was found in technology/freepdk45/gds_lib or sp_lib.",
            "No direct local AND3 hard macro was found either.",
        ),
    )

    option_nand4_proxy = RepairOption(
        option_name="gen_nand4_as_pnand3_proxy",
        status="limited_proxy_only" if gen_nand4_ok else "unavailable",
        pnand3_direct_macro_available=False,
        and3_direct_macro_available=False,
        safe_for_metadata_planning="limited_proxy_only" if gen_nand4_ok else False,
        safe_for_physical_placement=False,
        base_macro="gen_nand4",
        intended_logic="PNAND3 / NAND3-like upper-bound proxy",
        unused_input_strategy=("tie_unused_input_to_vdd", "unknown_if_unproven"),
        unused_input_tie_policy_proven=False,
        requires_pin_metadata_repair=not gen_nand4_labels_complete,
        requires_power_metadata_repair=not gen_nand4_power_complete,
        requires_unused_input_tie_proof=True,
        gen_nand4_gds_available=True,
        gen_nand4_spice_available=False,
        gen_nand4_labels_available=gen_nand4_labels_complete,
        gen_nand4_power_metadata_complete=gen_nand4_power_complete,
        gen_nand4_logic_polarity_confirmed=False,
        notes=(
            "A 4-input NAND could serve only as an upper-bound metadata proxy if an unused input is tied high.",
            "That unused-input tie policy is not proven in local GDS/SPICE metadata.",
            "Missing label/power metadata keeps this option out of physical placement.",
        ),
    )

    pnand3_logic_equivalence = bool(gen_nand2_ok and gen_inv_ok)
    option_pnand3_composite = RepairOption(
        option_name="pnand3_from_nand2_inv",
        status="metadata_composite_candidate" if pnand3_logic_equivalence else "unavailable",
        pnand3_direct_macro_available=False,
        and3_direct_macro_available=False,
        safe_for_metadata_planning=pnand3_logic_equivalence,
        safe_for_physical_placement=False,
        logic_equivalence_metadata_proven=pnand3_logic_equivalence,
        required_cells={"gen_nand2": 2, "gen_inv": 1},
        notes=(
            "Metadata proof uses ab_n=NAND2(A,B), ab=INV(ab_n), z=NAND2(ab,C), so z=~(A&B&C).",
            "This proves logical equivalence only; it does not prove internal routing, legal row packing, or power-rail legality.",
        ),
    )

    and3_logic_equivalence = bool(gen_nand2_ok and gen_inv_ok)
    option_and3_composite = RepairOption(
        option_name="and3_from_nand2_inv",
        status="metadata_composite_candidate" if and3_logic_equivalence else "unavailable",
        pnand3_direct_macro_available=False,
        and3_direct_macro_available=False,
        safe_for_metadata_planning=and3_logic_equivalence,
        safe_for_physical_placement=False,
        logic_equivalence_metadata_proven=and3_logic_equivalence,
        required_cells={"gen_nand2": 2, "gen_inv": 2},
        notes=(
            "Metadata proof uses ab_n=NAND2(A,B), ab=INV(ab_n), abc_n=NAND2(ab,C), z=INV(abc_n).",
            "This proves logical equivalence only; it does not prove internal routing, legal row packing, or power-rail legality.",
        ),
    )

    option_unresolved = RepairOption(
        option_name="keep_and3_generated_logic_unresolved",
        status="fallback",
        pnand3_direct_macro_available=False,
        and3_direct_macro_available=False,
        safe_for_metadata_planning=True,
        safe_for_physical_placement=False,
        notes=(
            "This keeps decoder planning conservative and avoids overclaiming any leaf repair.",
            "It preserves row-rule metadata but blocks physical decoder smoke until macro repair/proof exists.",
        ),
    )

    options = [
        option_direct,
        option_nand4_proxy,
        option_pnand3_composite,
        option_and3_composite,
        option_unresolved,
    ]

    counts = {
        option_direct.option_name: _count_impact(stage_subcells, option_direct.required_cells, stage_count),
        option_nand4_proxy.option_name: _count_impact(stage_subcells, {"gen_inv": 19, "gen_nand4": 8}, stage_count),
        option_pnand3_composite.option_name: _count_impact(stage_subcells, {"gen_inv": 19, "gen_nand2": 24}, stage_count),
        option_and3_composite.option_name: _count_impact(stage_subcells, {"gen_inv": 27, "gen_nand2": 24}, stage_count),
        option_unresolved.option_name: _count_impact(stage_subcells, {"gen_inv": 11, "gen_nand2": 8}, stage_count, unresolved_and3=8),
    }

    blocker_audit = [
        _blockers_for_option(option_direct, macro_index, power_index),
        _blockers_for_option(option_nand4_proxy, macro_index, power_index),
        _blockers_for_option(option_pnand3_composite, macro_index, power_index),
        _blockers_for_option(option_and3_composite, macro_index, power_index),
        _blockers_for_option(option_unresolved, macro_index, power_index),
    ]

    recommended_decoder_logic_strategy = "keep_unresolved_until_macro_repair"
    if option_pnand3_composite.safe_for_metadata_planning and option_and3_composite.safe_for_metadata_planning:
        recommended_decoder_logic_strategy = "metadata_composite_nand2_inv"
    elif option_nand4_proxy.safe_for_metadata_planning:
        recommended_decoder_logic_strategy = "metadata_nand4_proxy_upper_bound"

    report = {
        "scope": "step6_11_openyield_decoder_logic_repair_audit",
        "direct_pnand3_exists": False,
        "direct_and3_exists": False,
        "repair_options": [item.to_dict() for item in options],
        "per_option_stage_and_cascade_impact": counts,
        "pin_power_blocker_audit": blocker_audit,
        "recommended_decoder_logic_strategy": recommended_decoder_logic_strategy,
        "decoder_logic_repair_options_available": True,
        "pnand3_composite_metadata_available": bool(option_pnand3_composite.safe_for_metadata_planning),
        "and3_composite_metadata_available": bool(option_and3_composite.safe_for_metadata_planning),
        "gen_nand4_proxy_only": True,
        "gen_nand4_safe_for_physical_substitution": False,
        "can_enter_decoder_generated_block_planning": True,
        "can_enter_physical_decoder_placement": False,
        "can_enter_very_limited_control_row_smoke": False,
        "standalone_modified": False,
        "routing_modified": False,
        "gds_writer_modified": False,
        "blocker_list": [
            "Direct PNAND3 / AND3 local hard macros are still absent.",
            "gen_nand4 remains only a limited metadata proxy because label, power, polarity, and unused-input tie proof are incomplete.",
            "Composite gen_nand2 + gen_inv logic equivalence is metadata-proven, but physical row routing and rail legality are still unproven.",
            "Decoder generated-block planning can continue, but physical decoder placement and control-row smoke remain blocked.",
        ],
        "step_6_12_recommendation": "Refine composite decoder-leaf metadata next: add internal-net and pin-side conventions for the gen_nand2/gen_inv composition before any placement-oriented decoder prototype.",
    }

    graph = {
        "scope": report["scope"],
        "nodes": _build_graph_nodes(options),
        "edges": _build_graph_edges(),
        "counts": counts,
        "blockers": report["blocker_list"],
    }
    return report, graph


def build_decoder_logic_repair_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# OpenYield Decoder Logic Repair Audit",
        "",
        "This is a metadata-only audit for missing PNAND3 / AND3 decoder leaves. It does not modify placement, routing, standalone.py, or the GDS writer.",
        "",
        "## Summary",
        "",
        f"- direct PNAND3 exists: `{report['direct_pnand3_exists']}`",
        f"- direct AND3 exists: `{report['direct_and3_exists']}`",
        f"- decoder_logic_repair_options_available: `{report['decoder_logic_repair_options_available']}`",
        f"- recommended_decoder_logic_strategy: `{report['recommended_decoder_logic_strategy']}`",
        f"- pnand3_composite_metadata_available: `{report['pnand3_composite_metadata_available']}`",
        f"- and3_composite_metadata_available: `{report['and3_composite_metadata_available']}`",
        f"- gen_nand4_proxy_only: `{report['gen_nand4_proxy_only']}`",
        f"- gen_nand4_safe_for_physical_substitution: `{report['gen_nand4_safe_for_physical_substitution']}`",
        f"- can_enter_decoder_generated_block_planning: `{report['can_enter_decoder_generated_block_planning']}`",
        f"- can_enter_physical_decoder_placement: `{report['can_enter_physical_decoder_placement']}`",
        f"- can_enter_very_limited_control_row_smoke: `{report['can_enter_very_limited_control_row_smoke']}`",
        "",
        "## Repair Options",
        "",
        md_table(
            ["option", "status", "safe_metadata", "safe_physical", "logic_equivalence", "required_cells", "notes"],
            [
                [
                    item["option_name"],
                    item["status"],
                    item["safe_for_metadata_planning"],
                    item["safe_for_physical_placement"],
                    item.get("logic_equivalence_metadata_proven", "-"),
                    json.dumps(item.get("required_cells") or {}, ensure_ascii=False),
                    _notes_text(item["notes"]),
                ]
                for item in report["repair_options"]
            ],
        ),
        "",
        "## Stage / Cascade Count Impact",
        "",
        md_table(
            ["option", "per_stage_gen_inv", "per_stage_gen_nand2", "per_stage_gen_nand4", "per_stage_proxy_cell_count", "cascade_gen_inv", "cascade_gen_nand2", "cascade_gen_nand4", "cascade_proxy_cell_count"],
            [
                [
                    key,
                    value["per_stage_required_gen_inv"],
                    value["per_stage_required_gen_nand2"],
                    value["per_stage_required_gen_nand4"],
                    value["per_stage_proxy_cell_count"],
                    value["cascade_total_required_gen_inv"],
                    value["cascade_total_required_gen_nand2"],
                    value["cascade_total_required_gen_nand4"],
                    value["cascade_total_proxy_cell_count"],
                ]
                for key, value in report["per_option_stage_and_cascade_impact"].items()
            ],
        ),
        "",
        "## Blocker Audit",
        "",
        md_table(
            ["option", "pin blockers", "power blockers", "internal net blockers", "rail blockers", "unused input blockers", "physical blockers"],
            [
                [
                    item["option_name"],
                    _notes_text(item["pin_metadata_blockers"]),
                    _notes_text(item["power_metadata_blockers"]),
                    _notes_text(item["internal_net_routing_blockers"]),
                    _notes_text(item["rail_continuity_blockers"]),
                    _notes_text(item["unused_input_blockers"]),
                    _notes_text(item["physical_placement_blockers"]),
                ]
                for item in report["pin_power_blocker_audit"]
            ],
        ),
        "",
        "## Blockers",
        "",
        *[f"- {item}" for item in report["blocker_list"]],
        "",
        "## Step 6.12 Recommendation",
        "",
        f"- {report['step_6_12_recommendation']}",
        "",
    ]
    return "\n".join(lines)


def write_decoder_logic_repair_reports(
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
    report, graph = build_decoder_logic_repair_report(
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
    out_md.write_text(build_decoder_logic_repair_markdown(report), encoding="utf-8")
    out_graph.write_text(json.dumps(graph, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return report


def _count_impact(
    stage_subcells: dict[str, int],
    required_cells: dict[str, int] | None,
    stage_count: int,
    unresolved_and3: int = 0,
) -> dict[str, int]:
    required_cells = required_cells or {}
    per_stage_gen_inv = int(required_cells.get("gen_inv", 0))
    per_stage_gen_nand2 = int(required_cells.get("gen_nand2", 0))
    per_stage_gen_nand4 = int(required_cells.get("gen_nand4", 0))
    per_stage_proxy = per_stage_gen_inv + per_stage_gen_nand2 + per_stage_gen_nand4 + int(unresolved_and3)
    return {
        "per_stage_required_gen_inv": per_stage_gen_inv,
        "per_stage_required_gen_nand2": per_stage_gen_nand2,
        "per_stage_required_gen_nand4": per_stage_gen_nand4,
        "per_stage_proxy_cell_count": per_stage_proxy,
        "cascade_total_required_gen_inv": per_stage_gen_inv * stage_count,
        "cascade_total_required_gen_nand2": per_stage_gen_nand2 * stage_count,
        "cascade_total_required_gen_nand4": per_stage_gen_nand4 * stage_count,
        "cascade_total_proxy_cell_count": per_stage_proxy * stage_count,
        "stage_subcell_signature": dict(stage_subcells),
    }


def _blockers_for_option(
    option: RepairOption,
    macro_index: dict[str, dict[str, Any]],
    power_index: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    pin_blockers: list[str] = []
    power_blockers: list[str] = []
    internal_blockers: list[str] = []
    rail_blockers: list[str] = []
    unused_blockers: list[str] = []
    physical_blockers: list[str] = ["physical_row_placement_unproven", "internal_routing_unproven", "shared_rail_forbidden"]

    if option.option_name == "gen_nand4_as_pnand3_proxy":
        if not option.gen_nand4_labels_available:
            pin_blockers.append("gen_nand4_label_metadata_incomplete")
        if not option.gen_nand4_power_metadata_complete:
            power_blockers.append("gen_nand4_power_metadata_incomplete")
        internal_blockers.append("unused_input_logic_polarity_unproven")
        internal_blockers.append("proxy_internal_net_routing_unproven")
        rail_blockers.extend(power_index["gen_nand4"]["power_metadata_blockers"])
        unused_blockers.append("unused_input_tie_policy_not_proven")
    elif option.option_name in {"pnand3_from_nand2_inv", "and3_from_nand2_inv"}:
        internal_blockers.append("composite_internal_nets_need_routing_convention")
        internal_blockers.append("composite_row_packing_unproven")
        rail_blockers.extend(power_index["gen_nand2"]["power_metadata_blockers"])
        rail_blockers.extend(power_index["gen_inv"]["power_metadata_blockers"])
    elif option.option_name == "keep_and3_generated_logic_unresolved":
        internal_blockers.append("pnand3_leaf_unresolved")
        physical_blockers.append("decoder_logic_leaf_still_missing")
    else:
        physical_blockers.append("direct_leaf_macro_missing")

    if option.option_name in {"pnand3_from_nand2_inv", "and3_from_nand2_inv"}:
        if not macro_index["gen_nand2"]["pin_metadata_complete"]:
            pin_blockers.append("gen_nand2_pin_metadata_incomplete")
        if not macro_index["gen_inv"]["pin_metadata_complete"]:
            pin_blockers.append("gen_inv_pin_metadata_incomplete")

    return {
        "option_name": option.option_name,
        "pin_metadata_blockers": pin_blockers,
        "power_metadata_blockers": power_blockers,
        "internal_net_routing_blockers": internal_blockers,
        "rail_continuity_blockers": rail_blockers,
        "unused_input_blockers": unused_blockers,
        "physical_placement_blockers": physical_blockers,
    }


def _build_graph_nodes(options: list[RepairOption]) -> list[dict[str, Any]]:
    return [
        {
            "id": item.option_name,
            "kind": "repair_option",
            "status": item.status,
            "safe_for_metadata_planning": item.safe_for_metadata_planning,
            "safe_for_physical_placement": item.safe_for_physical_placement,
        }
        for item in options
    ]


def _build_graph_edges() -> list[dict[str, Any]]:
    return [
        {"source": "direct_pnand3_and3_macro", "target": "gen_nand4_as_pnand3_proxy", "relation": "fallback_to"},
        {"source": "gen_nand4_as_pnand3_proxy", "target": "pnand3_from_nand2_inv", "relation": "compare_against"},
        {"source": "pnand3_from_nand2_inv", "target": "and3_from_nand2_inv", "relation": "paired_composite"},
        {"source": "and3_from_nand2_inv", "target": "keep_and3_generated_logic_unresolved", "relation": "fallback_if_overconstrained"},
    ]
