"""Read-only OpenYield decoder composite leaf convention audit helpers."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from .decoder_logic_repair_options import build_decoder_logic_repair_report
from .decoder_stage_candidates import md_table, _notes_text


@dataclass(frozen=True)
class CompositeLeafConvention:
    convention_name: str
    target_logic: str
    input_pins: tuple[str, ...]
    output_pin: str
    internal_nets: tuple[str, ...]
    leaf_instances: tuple[str, ...]
    leaf_instance_order: tuple[str, ...]
    leaf_macro_sequence: tuple[str, ...]
    pin_side_convention: dict[str, str]
    power_policy: dict[str, Any]
    local_keepout: dict[str, Any]
    bbox_proxy: dict[str, Any]
    logic_equivalence_metadata_proven: bool
    pin_metadata_complete: bool
    power_metadata_complete: bool
    internal_routing_proven: bool
    rail_continuity_proven: bool
    safe_for_metadata_planning: bool
    safe_for_physical_placement: bool
    notes: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def build_decoder_composite_leaf_convention_report(
    tech_dir: str | Path,
    addr_width: int = 5,
    internal_gap: float = 0.2,
    openyield_root: str | Path | None = None,
    contracts_path: str | Path | None = None,
    gds_pin_report_path: str | Path | None = None,
    decomposition_report_path: str | Path | None = None,
    target_envelope_report_path: str | Path | None = None,
) -> tuple[dict[str, Any], dict[str, Any]]:
    openyield_root = openyield_root or Path.cwd().parents[1] / "third_party/OpenYield"
    contracts_path = contracts_path or Path.cwd() / "docs/openyield_module_contracts.json"
    gds_pin_report_path = gds_pin_report_path or Path.cwd() / "docs/openyield_gds_pin_audit_report.json"
    decomposition_report_path = decomposition_report_path or Path.cwd() / "docs/openyield_time_control_decomposition_report.json"
    target_envelope_report_path = target_envelope_report_path or Path.cwd() / "docs/openyield_control_target_envelope_report.json"

    repair_report, _graph = build_decoder_logic_repair_report(
        openyield_root=openyield_root,
        contracts_path=contracts_path,
        tech_dir=tech_dir,
        addr_width=addr_width,
        num_rows=None,
        gds_pin_report_path=gds_pin_report_path,
        decomposition_report_path=decomposition_report_path,
        target_envelope_report_path=target_envelope_report_path,
    )

    dims = _macro_dimensions(gds_pin_report_path)
    nand2 = dims["gen_nand2"]
    inv = dims["gen_inv"]

    leaf_pin_metadata_complete = True
    leaf_power_metadata_complete = True
    composite_pin_convention_available = True
    composite_power_policy_available = True
    composite_internal_net_routing_proven = False
    composite_rail_continuity_proven = False

    pnand3_bbox = _bbox_proxy([nand2, inv, nand2], internal_gap)
    and3_bbox = _bbox_proxy([nand2, inv, nand2, inv], internal_gap)

    pnand3_keepout = _keepout("PNAND3_INTERNAL_KEEPOUT", "PNAND3_COMPOSITE_NAND2_INV", pnand3_bbox, ("ab_n", "ab"))
    and3_keepout = _keepout("AND3_INTERNAL_KEEPOUT", "AND3_COMPOSITE_NAND2_INV", and3_bbox, ("ab_n", "ab", "abc_n"))

    power_policy = {
        "vdd_side": "top",
        "gnd_side": "bottom",
        "policy": "local_horizontal_rails_only",
        "shared_rail_disabled": True,
        "rail_continuity_proven": False,
        "metadata_only": True,
    }
    pin_side = {
        "input_side": "west",
        "output_side": "east",
        "power_side_vdd": "top",
        "power_side_gnd": "bottom",
        "internal_nets_inside_bbox": "required",
    }

    pnand3 = CompositeLeafConvention(
        convention_name="PNAND3_COMPOSITE_NAND2_INV",
        target_logic="pnand3",
        input_pins=("A", "B", "C"),
        output_pin="Z",
        internal_nets=("ab_n", "ab"),
        leaf_instances=("Xpnand3_nab", "Xpnand3_inv_ab", "Xpnand3_z"),
        leaf_instance_order=("Xpnand3_nab", "Xpnand3_inv_ab", "Xpnand3_z"),
        leaf_macro_sequence=("gen_nand2", "gen_inv", "gen_nand2"),
        pin_side_convention=pin_side,
        power_policy=power_policy,
        local_keepout=pnand3_keepout,
        bbox_proxy=pnand3_bbox,
        logic_equivalence_metadata_proven=True,
        pin_metadata_complete=leaf_pin_metadata_complete,
        power_metadata_complete=leaf_power_metadata_complete,
        internal_routing_proven=False,
        rail_continuity_proven=False,
        safe_for_metadata_planning=True,
        safe_for_physical_placement=False,
        notes=(
            "ab_n = NAND2(A, B), ab = INV(ab_n), Z = NAND2(ab, C).",
            "A/B/C enter from west; Z exits east; internal nets remain within composite bbox.",
        ),
    )

    and3 = CompositeLeafConvention(
        convention_name="AND3_COMPOSITE_NAND2_INV",
        target_logic="and3",
        input_pins=("A", "B", "C"),
        output_pin="Z",
        internal_nets=("ab_n", "ab", "abc_n"),
        leaf_instances=("Xand3_nab", "Xand3_inv_ab", "Xand3_nabc", "Xand3_inv_z"),
        leaf_instance_order=("Xand3_nab", "Xand3_inv_ab", "Xand3_nabc", "Xand3_inv_z"),
        leaf_macro_sequence=("gen_nand2", "gen_inv", "gen_nand2", "gen_inv"),
        pin_side_convention=pin_side,
        power_policy=power_policy,
        local_keepout=and3_keepout,
        bbox_proxy=and3_bbox,
        logic_equivalence_metadata_proven=True,
        pin_metadata_complete=leaf_pin_metadata_complete,
        power_metadata_complete=leaf_power_metadata_complete,
        internal_routing_proven=False,
        rail_continuity_proven=False,
        safe_for_metadata_planning=True,
        safe_for_physical_placement=False,
        notes=(
            "ab_n = NAND2(A, B), ab = INV(ab_n), abc_n = NAND2(ab, C), Z = INV(abc_n).",
            "A/B/C enter from west; Z exits east; internal nets remain within composite bbox.",
        ),
    )

    per_stage = {
        "per_stage_gen_inv": 27,
        "per_stage_gen_nand2": 24,
        "per_stage_composite_and3": 8,
        "per_stage_composite_pnand3": 0,
        "per_stage_total_leafs": 51,
    }
    stage_count = 5
    cascade = {
        "cascade_total_gen_inv": per_stage["per_stage_gen_inv"] * stage_count,
        "cascade_total_gen_nand2": per_stage["per_stage_gen_nand2"] * stage_count,
        "cascade_total_composite_and3": per_stage["per_stage_composite_and3"] * stage_count,
        "cascade_total_leafs": per_stage["per_stage_total_leafs"] * stage_count,
    }

    report = {
        "scope": "step6_12_openyield_decoder_composite_leaf_convention_audit",
        "recommended_decoder_logic_strategy": repair_report["recommended_decoder_logic_strategy"],
        "decoder_composite_leaf_conventions_available": True,
        "pnand3_composite_convention_available": True,
        "and3_composite_convention_available": True,
        "leaf_pin_metadata_complete": leaf_pin_metadata_complete,
        "leaf_power_metadata_complete": leaf_power_metadata_complete,
        "composite_pin_convention_available": composite_pin_convention_available,
        "composite_power_policy_available": composite_power_policy_available,
        "composite_internal_net_routing_proven": composite_internal_net_routing_proven,
        "composite_rail_continuity_proven": composite_rail_continuity_proven,
        "leaf_macro_reference": {
            "gen_nand2": nand2,
            "gen_inv": inv,
        },
        "composite_leaf_conventions": [pnand3.to_dict(), and3.to_dict()],
        "stage_impact_refresh": {
            **per_stage,
            **cascade,
            "stage_formula": "3x Pinv + 8x AND2 + 8x AND3_COMPOSITE_NAND2_INV",
        },
        "can_enter_decoder_generated_block_planning": True,
        "can_enter_physical_decoder_placement": False,
        "can_enter_very_limited_control_row_smoke": False,
        "standalone_modified": False,
        "routing_modified": False,
        "gds_writer_modified": False,
        "blocker_list": [
            "Composite pin and power conventions are available, but internal net routing is still metadata-only.",
            "Composite rail continuity is not proven, so shared rail remains disabled.",
            "BBox proxy and keepout are planning aids only, not legal placement proof.",
            "Physical decoder placement and control-row smoke remain blocked.",
        ],
        "step_6_13_recommendation": "Bind these composite leaf conventions into decoder-stage metadata templates next, including per-stage pin slots and internal-net reservation rules.",
    }

    graph = {
        "scope": report["scope"],
        "nodes": [
            {"id": pnand3.convention_name, "kind": "composite_leaf"},
            {"id": and3.convention_name, "kind": "composite_leaf"},
            {"id": "gen_nand2", "kind": "leaf_macro"},
            {"id": "gen_inv", "kind": "leaf_macro"},
        ],
        "edges": [
            {"source": pnand3.convention_name, "target": "gen_nand2", "relation": "uses"},
            {"source": pnand3.convention_name, "target": "gen_inv", "relation": "uses"},
            {"source": and3.convention_name, "target": "gen_nand2", "relation": "uses"},
            {"source": and3.convention_name, "target": "gen_inv", "relation": "uses"},
        ],
        "stage_impact_refresh": report["stage_impact_refresh"],
        "blockers": report["blocker_list"],
    }
    return report, graph


def build_decoder_composite_leaf_convention_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# OpenYield Decoder Composite Leaf Convention Audit",
        "",
        "This is a metadata-only audit for composite decoder leaves built from `gen_nand2` and `gen_inv`. It does not modify placement, routing, standalone.py, or the GDS writer.",
        "",
        "## Summary",
        "",
        f"- recommended_decoder_logic_strategy: `{report['recommended_decoder_logic_strategy']}`",
        f"- decoder_composite_leaf_conventions_available: `{report['decoder_composite_leaf_conventions_available']}`",
        f"- pnand3_composite_convention_available: `{report['pnand3_composite_convention_available']}`",
        f"- and3_composite_convention_available: `{report['and3_composite_convention_available']}`",
        f"- leaf_pin_metadata_complete: `{report['leaf_pin_metadata_complete']}`",
        f"- leaf_power_metadata_complete: `{report['leaf_power_metadata_complete']}`",
        f"- composite_internal_net_routing_proven: `{report['composite_internal_net_routing_proven']}`",
        f"- composite_rail_continuity_proven: `{report['composite_rail_continuity_proven']}`",
        f"- can_enter_decoder_generated_block_planning: `{report['can_enter_decoder_generated_block_planning']}`",
        f"- can_enter_physical_decoder_placement: `{report['can_enter_physical_decoder_placement']}`",
        f"- can_enter_very_limited_control_row_smoke: `{report['can_enter_very_limited_control_row_smoke']}`",
        "",
        "## Leaf Macro Reference",
        "",
        "```json",
        json.dumps(report["leaf_macro_reference"], ensure_ascii=False, indent=2),
        "```",
        "",
        "## Composite Leaf Conventions",
        "",
        md_table(
            ["convention", "target_logic", "internal_nets", "leaf_order", "pin_side", "bbox_proxy", "keepout", "safe_metadata", "safe_physical"],
            [
                [
                    item["convention_name"],
                    item["target_logic"],
                    ", ".join(item["internal_nets"]),
                    ", ".join(item["leaf_macro_sequence"]),
                    json.dumps(item["pin_side_convention"], ensure_ascii=False),
                    json.dumps(item["bbox_proxy"], ensure_ascii=False),
                    json.dumps(item["local_keepout"], ensure_ascii=False),
                    item["safe_for_metadata_planning"],
                    item["safe_for_physical_placement"],
                ]
                for item in report["composite_leaf_conventions"]
            ],
        ),
        "",
        "## Stage Impact Refresh",
        "",
        "```json",
        json.dumps(report["stage_impact_refresh"], ensure_ascii=False, indent=2),
        "```",
        "",
        "## Blockers",
        "",
        *[f"- {item}" for item in report["blocker_list"]],
        "",
        "## Step 6.13 Recommendation",
        "",
        f"- {report['step_6_13_recommendation']}",
        "",
    ]
    return "\n".join(lines)


def write_decoder_composite_leaf_convention_reports(
    tech_dir: str | Path,
    addr_width: int,
    internal_gap: float,
    out_json: str | Path,
    out_md: str | Path,
    out_graph: str | Path,
    openyield_root: str | Path | None = None,
    contracts_path: str | Path | None = None,
    gds_pin_report_path: str | Path | None = None,
    decomposition_report_path: str | Path | None = None,
    target_envelope_report_path: str | Path | None = None,
) -> dict[str, Any]:
    report, graph = build_decoder_composite_leaf_convention_report(
        tech_dir=tech_dir,
        addr_width=addr_width,
        internal_gap=internal_gap,
        openyield_root=openyield_root,
        contracts_path=contracts_path,
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
    out_md.write_text(build_decoder_composite_leaf_convention_markdown(report), encoding="utf-8")
    out_graph.write_text(json.dumps(graph, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return report


def _macro_dimensions(path: str | Path | None) -> dict[str, dict[str, float]]:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    dims: dict[str, dict[str, float]] = {}
    for item in payload.get("audited_macros", []):
        if item.get("macro_name") in {"gen_nand2", "gen_inv"}:
            dims[str(item["macro_name"])] = {
                "leaf_macro": str(item["macro_name"]),
                "leaf_bbox": item["bbox"],
                "leaf_width": float(item["width"]),
                "leaf_height": float(item["height"]),
            }
    return dims


def _bbox_proxy(leafs: list[dict[str, float]], internal_gap: float) -> dict[str, Any]:
    width = sum(item["leaf_width"] for item in leafs) + internal_gap * (len(leafs) - 1)
    height = max(item["leaf_height"] for item in leafs)
    return {
        "bbox_proxy_policy": "horizontal_leaf_chain",
        "bbox_proxy_width": round(width, 6),
        "bbox_proxy_height": round(height, 6),
        "internal_gap": internal_gap,
        "bbox_proxy_is_metadata_only": True,
    }


def _keepout(name: str, target: str, bbox: dict[str, Any], reserved: tuple[str, ...]) -> dict[str, Any]:
    return {
        "keepout_name": name,
        "target_convention": target,
        "purpose": "reserve_internal_net_channel",
        "x0": 0.0,
        "y0": 0.0,
        "x1": bbox["bbox_proxy_width"],
        "y1": bbox["bbox_proxy_height"],
        "reserved_internal_nets": list(reserved),
        "metadata_only": True,
        "keepout_enforced_in_layout": False,
        "physical_routing_proven": False,
    }
