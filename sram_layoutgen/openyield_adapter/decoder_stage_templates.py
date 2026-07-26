"""Read-only OpenYield decoder stage metadata template audit helpers."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from .decoder_composite_leaf_conventions import build_decoder_composite_leaf_convention_report
from .decoder_stage_candidates import build_decoder_stage_candidate_report, md_table, _notes_text


@dataclass(frozen=True)
class DecoderStageTemplate:
    template_name: str
    source_class: str
    stage_role: str
    input_pin_slots: tuple[dict[str, Any], ...]
    output_pin_slots: tuple[dict[str, Any], ...]
    enable_pin_slot: dict[str, Any]
    leaf_slots: tuple[dict[str, Any], ...]
    leaf_slot_order: tuple[str, ...]
    internal_net_reservation_zones: tuple[dict[str, Any], ...]
    stage_bbox_proxy: dict[str, Any]
    input_anchor: dict[str, Any]
    output_anchor: dict[str, Any]
    enable_anchor: dict[str, Any]
    power_policy: dict[str, Any]
    metadata_only: bool
    pin_proven: bool
    internal_routing_proven: bool
    rail_continuity_proven: bool
    safe_for_metadata_planning: bool
    safe_for_physical_placement: bool
    notes: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def build_decoder_stage_template_report(
    openyield_root: str | Path,
    tech_dir: str | Path,
    addr_width: int = 5,
    internal_gap: float = 0.2,
    contracts_path: str | Path | None = None,
    gds_pin_report_path: str | Path | None = None,
    decomposition_report_path: str | Path | None = None,
    target_envelope_report_path: str | Path | None = None,
) -> tuple[dict[str, Any], dict[str, Any]]:
    cwd = Path.cwd()
    contracts_path = contracts_path or cwd / "docs/openyield_module_contracts.json"
    gds_pin_report_path = gds_pin_report_path or cwd / "docs/openyield_gds_pin_audit_report.json"
    decomposition_report_path = decomposition_report_path or cwd / "docs/openyield_time_control_decomposition_report.json"
    target_envelope_report_path = target_envelope_report_path or cwd / "docs/openyield_control_target_envelope_report.json"

    convention_report, _convention_graph = build_decoder_composite_leaf_convention_report(
        tech_dir=tech_dir,
        addr_width=addr_width,
        internal_gap=internal_gap,
        openyield_root=openyield_root,
        contracts_path=contracts_path,
        gds_pin_report_path=gds_pin_report_path,
        decomposition_report_path=decomposition_report_path,
        target_envelope_report_path=target_envelope_report_path,
    )
    stage_candidate_report, _stage_graph = build_decoder_stage_candidate_report(
        openyield_root=openyield_root,
        contracts_path=contracts_path,
        tech_dir=tech_dir,
        addr_width=addr_width,
        num_rows=None,
        gds_pin_report_path=gds_pin_report_path,
        decomposition_report_path=decomposition_report_path,
        target_envelope_report_path=target_envelope_report_path,
    )

    conventions = {
        item["convention_name"]: item
        for item in convention_report["composite_leaf_conventions"]
    }
    pnand3 = conventions["PNAND3_COMPOSITE_NAND2_INV"]
    and3 = conventions["AND3_COMPOSITE_NAND2_INV"]

    input_slots = tuple(
        {
            "slot_name": name,
            "side": "west" if name in {"A0", "A1", "A2"} else ("top" if name == "VDD" else ("bottom" if name == "VSS" else "north_or_west_enable_side")),
            "metadata_available": True,
            "physical_access_proven": False,
        }
        for name in ("EN", "A0", "A1", "A2", "VDD", "VSS")
    )
    output_slots = tuple(
        {
            "slot_name": f"WL{i}",
            "side": "east",
            "metadata_available": True,
            "physical_access_proven": False,
        }
        for i in range(8)
    )
    enable_slot = {
        "slot_name": "EN",
        "side": "north_or_west_enable_side",
        "metadata_available": True,
        "physical_access_proven": False,
    }

    leaf_slots = _build_leaf_slots()
    leaf_slot_order = tuple(item["slot_name"] for item in leaf_slots)
    zones = _build_stage_zones(and3, pnand3)
    stage_bbox_proxy = _stage_bbox_proxy(leaf_slots, internal_gap)

    decoder_template = DecoderStageTemplate(
        template_name="DECODER3_8_STAGE_TEMPLATE",
        source_class="DECODER3_8",
        stage_role="decoder_stage",
        input_pin_slots=input_slots,
        output_pin_slots=output_slots,
        enable_pin_slot=enable_slot,
        leaf_slots=tuple(leaf_slots),
        leaf_slot_order=leaf_slot_order,
        internal_net_reservation_zones=tuple(zones),
        stage_bbox_proxy=stage_bbox_proxy,
        input_anchor={
            "anchor_name": "DECODER_STAGE_INPUT_ANCHOR",
            "slot_names": ["A0", "A1", "A2"],
            "side": "west",
            "metadata_only": True,
            "physical_access_proven": False,
        },
        output_anchor={
            "anchor_name": "DECODER_STAGE_OUTPUT_ANCHOR",
            "slot_names": [f"WL{i}" for i in range(8)],
            "side": "east",
            "metadata_only": True,
            "physical_access_proven": False,
        },
        enable_anchor={
            "anchor_name": "DECODER_STAGE_ENABLE_ANCHOR",
            "slot_names": ["EN"],
            "side": "north_or_west_enable_side",
            "metadata_only": True,
            "physical_access_proven": False,
        },
        power_policy={
            "policy_name": "local_horizontal_vdd_gnd_only_no_shared_rail",
            "safe_for_shared_rail": False,
            "rail_continuity_proven": False,
            "stage_power_policy_available": True,
            "stage_power_physical_proven": False,
        },
        metadata_only=True,
        pin_proven=False,
        internal_routing_proven=False,
        rail_continuity_proven=False,
        safe_for_metadata_planning=True,
        safe_for_physical_placement=False,
        notes=(
            "Template binds Pinv, AND2, and AND3 composite slots into a decoder-stage shell.",
            "truth_table_binding_complete remains false until WL polarity combinations are explicitly bound from decoder.py at per-output level.",
        ),
    )

    level0_template = DecoderStageTemplate(
        template_name="DECODER_LEVEL0_STAGE_TEMPLATE",
        source_class="DECODER3_8",
        stage_role="intermediate_enable_bus",
        input_pin_slots=input_slots,
        output_pin_slots=tuple(
            {
                "slot_name": f"EN_0_0_{i}",
                "side": "east",
                "metadata_available": True,
                "physical_access_proven": False,
            }
            for i in range(8)
        ),
        enable_pin_slot={"slot_name": "EN", "side": "north_or_tiehigh_side", "metadata_available": True, "physical_access_proven": False},
        leaf_slots=tuple(leaf_slots),
        leaf_slot_order=leaf_slot_order,
        internal_net_reservation_zones=tuple(zones),
        stage_bbox_proxy=stage_bbox_proxy,
        input_anchor={
            "anchor_name": "DECODER_INPUT_ANCHOR",
            "slot_names": ["A0", "A1", "A2"],
            "side": "decoder_input_side",
            "metadata_only": True,
            "physical_access_proven": False,
        },
        output_anchor={
            "anchor_name": "EAST_ENABLE_BUS_ANCHOR",
            "slot_names": [f"EN_0_0_{i}" for i in range(8)],
            "side": "east_enable_bus_side",
            "metadata_only": True,
            "physical_access_proven": False,
        },
        enable_anchor={
            "anchor_name": "LEVEL0_TIEHIGH_ENABLE_ANCHOR",
            "slot_names": ["EN"],
            "side": "north_or_tiehigh_side",
            "metadata_only": True,
            "physical_access_proven": False,
        },
        power_policy=decoder_template.power_policy,
        metadata_only=True,
        pin_proven=False,
        internal_routing_proven=False,
        rail_continuity_proven=False,
        safe_for_metadata_planning=True,
        safe_for_physical_placement=False,
        notes=("Level 0 stage emits intermediate enable bus nets.",),
    )

    level1_template = DecoderStageTemplate(
        template_name="DECODER_LEVEL1_STAGE_TEMPLATE",
        source_class="DECODER3_8",
        stage_role="wordline_outputs",
        input_pin_slots=input_slots,
        output_pin_slots=output_slots,
        enable_pin_slot={"slot_name": "EN", "side": "north_enable_bus_side", "metadata_available": True, "physical_access_proven": False},
        leaf_slots=tuple(leaf_slots),
        leaf_slot_order=leaf_slot_order,
        internal_net_reservation_zones=tuple(zones),
        stage_bbox_proxy=stage_bbox_proxy,
        input_anchor={
            "anchor_name": "LOCAL_ADDR_BUS_ANCHOR",
            "slot_names": ["A0", "A1", "A2"],
            "side": "decoder_input_side",
            "metadata_only": True,
            "physical_access_proven": False,
        },
        output_anchor={
            "anchor_name": "WORDLINE_DRIVER_INPUT_HANDOFF_ANCHOR",
            "slot_names": [f"WL{i}" for i in range(8)],
            "side": "wordline_driver_side",
            "metadata_only": True,
            "physical_access_proven": False,
        },
        enable_anchor={
            "anchor_name": "ENABLE_BUS_ANCHOR",
            "slot_names": ["EN"],
            "side": "north_enable_bus_side",
            "metadata_only": True,
            "physical_access_proven": False,
        },
        power_policy=decoder_template.power_policy,
        metadata_only=True,
        pin_proven=False,
        internal_routing_proven=False,
        rail_continuity_proven=False,
        safe_for_metadata_planning=True,
        safe_for_physical_placement=False,
        notes=("Level 1 stages consume intermediate enable nets and drive WL outputs.",),
    )

    stage_instances = stage_candidate_report["decoder_cascade_hierarchy"]["stage_instances"]
    level0_binding = next(item for item in stage_instances if item["level"] == 0)
    level1_binding = [item for item in stage_instances if item["level"] == 1]

    report = {
        "scope": "step6_13_openyield_decoder_stage_template_audit",
        "recommended_decoder_logic_strategy": convention_report["recommended_decoder_logic_strategy"],
        "decoder_stage_templates_available": True,
        "decoder_composite_leaf_conventions_bound": True,
        "stage_pin_slots_available": True,
        "stage_internal_net_zones_available": True,
        "stage_bbox_proxy_available": True,
        "stage_power_policy_available": True,
        "stage_internal_routing_proven": False,
        "stage_rail_continuity_proven": False,
        "truth_table_binding_complete": False,
        "requires_decoder_truth_table_binding": True,
        "pin_slot_metadata_available": True,
        "pin_slot_physical_access_proven": False,
        "templates": [
            decoder_template.to_dict(),
            level0_template.to_dict(),
            level1_template.to_dict(),
        ],
        "level0_binding": {
            "stage_name": level0_binding["stage_name"],
            "role": "intermediate_enable_bus",
            "inputs": level0_binding["address_node_order"],
            "enable": level0_binding["enable_net"],
            "outputs": level0_binding["output_nets"],
            "template": "DECODER_LEVEL0_STAGE_TEMPLATE",
            "input_anchor": "DECODER_INPUT_ANCHOR",
            "output_anchor": "EAST_ENABLE_BUS_ANCHOR",
        },
        "level1_binding": [
            {
                "stage_name": item["stage_name"],
                "role": "wordline_outputs",
                "inputs": item["address_node_order"],
                "enable": item["enable_net"],
                "outputs": item["output_nets"],
                "template": "DECODER_LEVEL1_STAGE_TEMPLATE",
                "input_anchor": "LOCAL_ADDR_BUS_ANCHOR",
                "enable_anchor": "ENABLE_BUS_ANCHOR",
                "output_anchor": "WORDLINE_DRIVER_INPUT_HANDOFF_ANCHOR",
            }
            for item in level1_binding
        ],
        "can_enter_decoder_generated_block_planning": True,
        "can_enter_physical_decoder_placement": False,
        "can_enter_very_limited_control_row_smoke": False,
        "standalone_modified": False,
        "routing_modified": False,
        "gds_writer_modified": False,
        "blocker_list": [
            "Stage templates are metadata-only and do not prove legal stage packing.",
            "Per-slot physical access, internal routing, and rail continuity are still unproven.",
            "WL truth-table binding from decoder.py is not yet explicitly expanded into slot polarity bindings.",
            "Physical decoder placement and control-row smoke remain blocked.",
        ],
        "step_6_14_recommendation": "Expand decoder truth-table binding next: map each WL slot to its input polarity combination and bind stage templates to output-specific metadata contracts before any placement-oriented decoder prototype.",
    }

    graph = {
        "scope": report["scope"],
        "nodes": [
            {"id": "DECODER3_8_STAGE_TEMPLATE", "kind": "stage_template"},
            {"id": "DECODER_LEVEL0_STAGE_TEMPLATE", "kind": "stage_template"},
            {"id": "DECODER_LEVEL1_STAGE_TEMPLATE", "kind": "stage_template"},
        ],
        "edges": [
            {"source": "DECODER_LEVEL0_STAGE_TEMPLATE", "target": "DECODER3_8_STAGE_TEMPLATE", "relation": "specializes"},
            {"source": "DECODER_LEVEL1_STAGE_TEMPLATE", "target": "DECODER3_8_STAGE_TEMPLATE", "relation": "specializes"},
            {"source": "DECODER3_8_STAGE_TEMPLATE", "target": "PNAND3_COMPOSITE_NAND2_INV", "relation": "binds_leaf_convention"},
            {"source": "DECODER3_8_STAGE_TEMPLATE", "target": "AND3_COMPOSITE_NAND2_INV", "relation": "binds_leaf_convention"},
        ],
        "level0_binding": report["level0_binding"],
        "level1_binding": report["level1_binding"],
        "blockers": report["blocker_list"],
    }
    return report, graph


def build_decoder_stage_template_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# OpenYield Decoder Stage Template Audit",
        "",
        "This is a metadata-only audit for decoder stage templates. It does not modify placement, routing, standalone.py, or the GDS writer.",
        "",
        "## Summary",
        "",
        f"- recommended_decoder_logic_strategy: `{report['recommended_decoder_logic_strategy']}`",
        f"- decoder_stage_templates_available: `{report['decoder_stage_templates_available']}`",
        f"- decoder_composite_leaf_conventions_bound: `{report['decoder_composite_leaf_conventions_bound']}`",
        f"- stage_pin_slots_available: `{report['stage_pin_slots_available']}`",
        f"- stage_internal_net_zones_available: `{report['stage_internal_net_zones_available']}`",
        f"- stage_bbox_proxy_available: `{report['stage_bbox_proxy_available']}`",
        f"- stage_power_policy_available: `{report['stage_power_policy_available']}`",
        f"- truth_table_binding_complete: `{report['truth_table_binding_complete']}`",
        f"- can_enter_decoder_generated_block_planning: `{report['can_enter_decoder_generated_block_planning']}`",
        f"- can_enter_physical_decoder_placement: `{report['can_enter_physical_decoder_placement']}`",
        f"- can_enter_very_limited_control_row_smoke: `{report['can_enter_very_limited_control_row_smoke']}`",
        "",
        "## Templates",
        "",
        md_table(
            ["template", "role", "input_slots", "output_slots", "enable_slot", "leaf_slot_count", "zone_count", "bbox_proxy", "safe_metadata", "safe_physical"],
            [
                [
                    item["template_name"],
                    item["stage_role"],
                    ", ".join(slot["slot_name"] for slot in item["input_pin_slots"]),
                    ", ".join(slot["slot_name"] for slot in item["output_pin_slots"][:4]) + (" ..." if len(item["output_pin_slots"]) > 4 else ""),
                    item["enable_pin_slot"]["slot_name"],
                    len(item["leaf_slots"]),
                    len(item["internal_net_reservation_zones"]),
                    json.dumps(item["stage_bbox_proxy"], ensure_ascii=False),
                    item["safe_for_metadata_planning"],
                    item["safe_for_physical_placement"],
                ]
                for item in report["templates"]
            ],
        ),
        "",
        "## Level 0 Binding",
        "",
        "```json",
        json.dumps(report["level0_binding"], ensure_ascii=False, indent=2),
        "```",
        "",
        "## Level 1 Binding",
        "",
        "```json",
        json.dumps(report["level1_binding"], ensure_ascii=False, indent=2),
        "```",
        "",
        "## Blockers",
        "",
        *[f"- {item}" for item in report["blocker_list"]],
        "",
        "## Step 6.14 Recommendation",
        "",
        f"- {report['step_6_14_recommendation']}",
        "",
    ]
    return "\n".join(lines)


def write_decoder_stage_template_reports(
    openyield_root: str | Path,
    tech_dir: str | Path,
    addr_width: int,
    internal_gap: float,
    out_json: str | Path,
    out_md: str | Path,
    out_graph: str | Path,
    contracts_path: str | Path | None = None,
    gds_pin_report_path: str | Path | None = None,
    decomposition_report_path: str | Path | None = None,
    target_envelope_report_path: str | Path | None = None,
) -> dict[str, Any]:
    report, graph = build_decoder_stage_template_report(
        openyield_root=openyield_root,
        tech_dir=tech_dir,
        addr_width=addr_width,
        internal_gap=internal_gap,
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
    out_md.write_text(build_decoder_stage_template_markdown(report), encoding="utf-8")
    out_graph.write_text(json.dumps(graph, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return report


def _build_leaf_slots() -> list[dict[str, Any]]:
    slots: list[dict[str, Any]] = []
    for name in ("a0", "a1", "a2"):
        slots.append(
            {
                "slot_name": f"Xdec_inv_{name}",
                "slot_type": "Pinv",
                "macro_sequence": ["gen_inv"],
                "row_order_group": "input_inversion",
            }
        )
    for i in range(8):
        slots.append(
            {
                "slot_name": f"Xdec_and3_wl{i}",
                "slot_type": "AND3_COMPOSITE_NAND2_INV",
                "macro_sequence": ["gen_nand2", "gen_inv", "gen_nand2", "gen_inv"],
                "row_order_group": "and3_composite",
            }
        )
    for i in range(8):
        slots.append(
            {
                "slot_name": f"Xdec_and2_wl{i}",
                "slot_type": "AND2",
                "macro_sequence": ["gen_nand2", "gen_inv"],
                "row_order_group": "and2_composite",
            }
        )
    return slots


def _build_stage_zones(and3: dict[str, Any], pnand3: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        {
            "zone_name": "INPUT_INVERSION_ZONE",
            "purpose": "reserve_input_inverter_outputs",
            "reserved_nets": ["A0_bar", "A1_bar", "A2_bar"],
            "x0": 0.0,
            "y0": 0.0,
            "x1": 2.8,
            "y1": 1.48,
            "metadata_only": True,
            "physical_routing_proven": False,
            "overlap_policy": "no_output_zone_overlap",
        },
        {
            "zone_name": "AND2_COMPOSITE_ZONE",
            "purpose": "reserve_and2_composite_nets",
            "reserved_nets": [f"wl{i}_and2_ab_n" for i in range(8)] + [f"wl{i}_and2_ab" for i in range(8)],
            "x0": 2.8,
            "y0": 0.0,
            "x1": 12.0,
            "y1": 1.48,
            "metadata_only": True,
            "physical_routing_proven": False,
            "overlap_policy": "adjacent_only_to_and3_zone",
        },
        {
            "zone_name": "AND3_COMPOSITE_ZONE",
            "purpose": "reserve_and3_composite_nets",
            "reserved_nets": [f"wl{i}_and3_ab_n" for i in range(8)] + [f"wl{i}_and3_ab" for i in range(8)] + [f"wl{i}_and3_abc_n" for i in range(8)],
            "x0": 12.0,
            "y0": 0.0,
            "x1": 24.0,
            "y1": 1.48,
            "metadata_only": True,
            "physical_routing_proven": False,
            "overlap_policy": "adjacent_only_to_and2_zone",
        },
        {
            "zone_name": "OUTPUT_HANDOFF_ZONE",
            "purpose": "reserve_wl_output_slots",
            "reserved_nets": [f"WL{i}" for i in range(8)],
            "x0": 24.0,
            "y0": 0.0,
            "x1": 27.0,
            "y1": 1.48,
            "metadata_only": True,
            "physical_routing_proven": False,
            "overlap_policy": "east_edge_only",
        },
        {
            "zone_name": "ENABLE_DISTRIBUTION_ZONE",
            "purpose": "reserve_enable_distribution",
            "reserved_nets": ["EN", "EN_buf", "EN_local"] if False else ["EN"],
            "x0": 0.0,
            "y0": 1.48,
            "x1": 27.0,
            "y1": 2.0,
            "metadata_only": True,
            "physical_routing_proven": False,
            "overlap_policy": "top_strip_only",
        },
    ]


def _stage_bbox_proxy(leaf_slots: list[dict[str, Any]], internal_gap: float) -> dict[str, Any]:
    # Conservative proxy, not legal physical bbox.
    total_width = (3 * 0.8225) + (8 * 4.32) + (8 * 1.86) + internal_gap * (len(leaf_slots) - 1)
    return {
        "stage_bbox_proxy_policy": "conservative_leaf_slot_sum",
        "stage_bbox_width": round(total_width, 6),
        "stage_bbox_height": 2.0,
        "internal_gap": internal_gap,
        "stage_bbox_proxy_is_metadata_only": True,
        "stage_bbox_not_legal_physical_layout": True,
    }
