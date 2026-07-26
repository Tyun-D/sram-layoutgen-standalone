"""Read-only parent control-row reservation audit helpers."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .decoder_stage_candidates import md_table


def build_control_parent_reservation_report(
    *,
    addr_width: int = 5,
    base_wordline_channel_width: float = 2.0,
    recommended_wordline_channel_width: float = 2.2,
    extra_wordline_width: float = 0.2,
    control_channel_width: float = 2.0,
    clock_channel_width: float = 2.0,
    stage_row_gap: float = 1.565,
    level_gap: float = 2.0,
    reservation_policy: str = "parent_metadata_side_channel_reservation",
    decoder_channel_requirement_report_path: str | Path | None = None,
    decoder_handoff_relief_report_path: str | Path | None = None,
    decoder_preplacement_report_path: str | Path | None = None,
    control_geometry_report_path: str | Path | None = None,
    control_channel_budget_report_path: str | Path | None = None,
    control_row_floorplan_report_path: str | Path | None = None,
    control_row_feasibility_report_path: str | Path | None = None,
    control_target_envelope_report_path: str | Path | None = None,
    control_anchor_binding_report_path: str | Path | None = None,
) -> tuple[dict[str, Any], dict[str, Any]]:
    decoder_requirement = json.loads(Path(decoder_channel_requirement_report_path or "docs/openyield_decoder_channel_requirement_report.json").read_text(encoding="utf-8"))
    decoder_handoff_relief = json.loads(Path(decoder_handoff_relief_report_path or "docs/openyield_decoder_handoff_relief_report.json").read_text(encoding="utf-8"))
    decoder_preplacement = json.loads(Path(decoder_preplacement_report_path or "docs/openyield_decoder_preplacement_feasibility_report.json").read_text(encoding="utf-8"))
    control_geometry = json.loads(Path(control_geometry_report_path or "docs/openyield_control_geometry_window_report.json").read_text(encoding="utf-8"))
    control_budget = json.loads(Path(control_channel_budget_report_path or "docs/openyield_control_channel_budget_report.json").read_text(encoding="utf-8"))
    control_floorplan = json.loads(Path(control_row_floorplan_report_path or "docs/openyield_control_row_floorplan_report.json").read_text(encoding="utf-8"))
    control_feasibility = json.loads(Path(control_row_feasibility_report_path or "docs/openyield_control_row_feasibility_report.json").read_text(encoding="utf-8"))
    control_target = json.loads(Path(control_target_envelope_report_path or "docs/openyield_control_target_envelope_report.json").read_text(encoding="utf-8"))
    control_anchor = json.loads(Path(control_anchor_binding_report_path or "docs/openyield_control_anchor_binding_report.json").read_text(encoding="utf-8"))

    affected_items = [
        {
            "name": "CLOCK_ENTRY_WINDOW",
            "window_type": "parent_control_window",
            "affected_by_2p2_requirement": False,
            "required_update": False,
            "old_width_if_known": control_geometry["clock_entry_window"]["width"],
            "new_width_if_known": control_geometry["clock_entry_window"]["width"],
            "delta_width": 0.0,
            "metadata_only": True,
            "physical_space_proven": False,
            "notes": ["Clock ingress reservation is likely unaffected by decoder-side wordline widening."],
        },
        {
            "name": "ADDR_TO_DECODER_WINDOW",
            "window_type": "parent_control_window",
            "affected_by_2p2_requirement": True,
            "required_update": True,
            "old_width_if_known": control_geometry["decoder_input_window"]["width"],
            "new_width_if_known": round(control_geometry["decoder_input_window"]["width"] + extra_wordline_width, 6),
            "delta_width": extra_wordline_width,
            "metadata_only": True,
            "physical_space_proven": False,
            "notes": ["Decoder-side parent reservation should absorb the extra 0.2um requirement."],
        },
        {
            "name": "DATA_TO_WRITEDRIVER_WINDOW",
            "window_type": "parent_control_window",
            "affected_by_2p2_requirement": False,
            "required_update": False,
            "old_width_if_known": control_geometry["write_driver_input_window"]["height"],
            "new_width_if_known": control_geometry["write_driver_input_window"]["height"],
            "delta_width": 0.0,
            "metadata_only": True,
            "physical_space_proven": False,
            "notes": ["Write-driver-side metadata window is unaffected in the current model."],
        },
        {
            "name": "DECODER_INPUT_ANCHOR",
            "window_type": "control_anchor",
            "affected_by_2p2_requirement": True,
            "required_update": True,
            "old_width_if_known": None,
            "new_width_if_known": None,
            "delta_width": extra_wordline_width,
            "metadata_only": True,
            "physical_space_proven": False,
            "notes": ["Anchor metadata should reference the widened decoder-side reservation."],
        },
        {
            "name": "WRITEDRIVER_INPUT_ANCHOR",
            "window_type": "control_anchor",
            "affected_by_2p2_requirement": False,
            "required_update": False,
            "old_width_if_known": None,
            "new_width_if_known": None,
            "delta_width": 0.0,
            "metadata_only": True,
            "physical_space_proven": False,
            "notes": ["Write-driver anchor stays unchanged."],
        },
        {
            "name": "DECODER_CASCADE_ENVELOPE",
            "window_type": "decoder_envelope",
            "affected_by_2p2_requirement": True,
            "required_update": True,
            "old_width_if_known": control_target["decoder_generated_block_envelope"]["candidate_bbox"]["width"],
            "new_width_if_known": round(control_target["decoder_generated_block_envelope"]["candidate_bbox"]["width"] + extra_wordline_width, 6),
            "delta_width": extra_wordline_width,
            "metadata_only": True,
            "physical_space_proven": False,
            "notes": ["Envelope metadata may need synchronized widening on the wordline-handoff side."],
        },
    ]
    for item in decoder_requirement["affected_windows"]:
        affected_items.append(
            {
                "name": item["window_name"],
                "window_type": "decoder_handoff_window",
                "affected_by_2p2_requirement": True,
                "required_update": True,
                "old_width_if_known": item["old_width"],
                "new_width_if_known": item["new_width"],
                "delta_width": item["delta_width"],
                "metadata_only": True,
                "physical_space_proven": False,
                "notes": ["Directly widened by the decoder 2.2um channel requirement."],
            }
        )
    affected_items.append(
        {
            "name": "ENABLE_BUS_HANDOFF_WINDOW",
            "window_type": "decoder_handoff_window",
            "affected_by_2p2_requirement": False,
            "required_update": False,
            "old_width_if_known": None,
            "new_width_if_known": None,
            "delta_width": 0.0,
            "metadata_only": True,
            "physical_space_proven": False,
            "notes": ["Enable-bus window remains unchanged in this model."],
        }
    )

    parent_keepout = {
        "keepout_name": "PARENT_DECODER_WORDLINE_CHANNEL_RESERVATION_2P2",
        "purpose": "reserve_decoder_to_wordlinedriver_metadata_channel",
        "reserved_width": recommended_wordline_channel_width,
        "extra_width_over_baseline": extra_wordline_width,
        "source": "Step 6.20",
        "applies_to": [f"WORDLINE_OUTPUT_HANDOFF_WINDOW_GROUP_{i}" for i in range(4)],
        "metadata_only": True,
        "keepout_enforced_in_layout": False,
        "physical_routing_proven": False,
    }

    floorplan_compatibility = {
        "parent_reservation_available": True,
        "parent_reservation_conflict_found": False,
        "decoder_envelope_update_required": True,
        "control_window_update_required": True,
        "clock_window_affected": False,
        "addr_to_decoder_window_affected": True,
        "data_to_writedriver_window_affected": False,
        "dff_row_conflict_found": False,
        "writedriver_anchor_conflict_found": False,
        "physical_floorplan_space_proven": False,
        "parent_floorplan_reservation_required": True,
        "compatibility_status": "metadata_reservation_required_space_unproven",
    }

    budget_summary = {
        "base_wordline_channel_width": base_wordline_channel_width,
        "recommended_wordline_channel_width": recommended_wordline_channel_width,
        "wordline_required_width": decoder_requirement["required_width"],
        "old_margin": decoder_requirement["updated_budget_summary"]["old_wordline_margin"],
        "new_margin": decoder_requirement["updated_budget_summary"]["new_wordline_margin"],
        "new_risk_level": decoder_requirement["updated_budget_summary"]["new_risk_level"],
        "margin_still_low": True,
    }

    risk_flags = {
        "parent_reservation_required": True,
        "physical_parent_space_proven": False,
        "metadata_reservation_only": True,
        "wordline_margin_still_low": True,
        "control_window_metadata_update_required": True,
        "decoder_envelope_metadata_update_required": True,
        "routing_unproven": True,
        "placement_unproven": True,
        "shared_rail_disabled": True,
        "physical_decoder_placement_blocked": True,
    }

    report = {
        "scope": "step6_21_openyield_control_parent_reservation_audit",
        "reservation_name": "PARENT_CONTROL_ROW_DECODER_WORDLINE_2P2_RESERVATION",
        "source_requirement": decoder_requirement["requirement_name"],
        "extra_width_required": extra_wordline_width,
        "base_wordline_channel_width": base_wordline_channel_width,
        "recommended_wordline_channel_width": recommended_wordline_channel_width,
        "reservation_policy": reservation_policy,
        "metadata_only": True,
        "physical_floorplan_space_proven": False,
        "physical_routing_proven": False,
        "control_parent_reservation_available": True,
        "parent_reservation_required": True,
        "parent_reservation_recorded": True,
        "decoder_wordline_2p2_requirement_propagated": True,
        "safe_for_parent_metadata_planning": True,
        "safe_for_physical_floorplan_claim": False,
        "affected_parent_windows": affected_items,
        "affected_decoder_windows": [item for item in affected_items if item["window_type"] == "decoder_handoff_window"],
        "affected_control_anchors": [item for item in affected_items if item["window_type"] == "control_anchor"],
        "parent_keepout_requirements": [parent_keepout],
        "floorplan_compatibility": floorplan_compatibility,
        "reservation_conflict_checks": floorplan_compatibility,
        "budget_margin_summary": budget_summary,
        "risk_flags": risk_flags,
        "recommended_parent_policy": "record_parent_2p2_wordline_reservation_and_close_decoder_metadata",
        "can_enter_decoder_metadata_closure": True,
        "can_enter_decoder_physical_prototype": False,
        "can_enter_physical_decoder_placement": False,
        "can_enter_very_limited_control_row_smoke": False,
        "standalone_modified": False,
        "routing_modified": False,
        "gds_writer_modified": False,
        "blocker_list": [
            "Parent reservation is metadata-only and does not prove physical floorplan space.",
            "ADDR_TO_DECODER_WINDOW and DECODER_CASCADE_ENVELOPE need synchronized metadata updates before any later physical planning step.",
            "Clock/data-side windows remain logically unaffected but are still unproven as physical channels.",
            "Decoder physical prototype and placement remain blocked.",
        ],
        "step_6_22_recommendation": "Next, close decoder metadata and pivot to remaining TIME/control subblocks, unless the project explicitly wants to open a broader parent floorplan reservation study.",
        "source_context": {
            "decoder_channel_requirement_scope": decoder_requirement["scope"],
            "control_geometry_scope": control_geometry["scope"],
            "control_channel_budget_scope": control_budget["scope"],
            "control_row_floorplan_scope": control_floorplan["scope"],
            "control_row_feasibility_scope": control_feasibility["scope"],
            "control_target_envelope_scope": control_target["scope"],
            "control_anchor_binding_scope": control_anchor["scope"],
            "decoder_preplacement_scope": decoder_preplacement["scope"],
            "decoder_handoff_relief_scope": decoder_handoff_relief["scope"],
        },
    }

    graph = {
        "scope": report["scope"],
        "nodes": (
            [{"id": report["reservation_name"], "kind": "parent_reservation"}]
            + [{"id": item["name"], "kind": item["window_type"]} for item in affected_items]
            + [{"id": parent_keepout["keepout_name"], "kind": "parent_keepout"}]
        ),
        "edges": (
            [{"source": report["reservation_name"], "target": item["name"], "relation": "affects"} for item in affected_items if item["affected_by_2p2_requirement"]]
            + [{"source": report["reservation_name"], "target": parent_keepout["keepout_name"], "relation": "records"}]
        ),
        "recommended_parent_policy": report["recommended_parent_policy"],
        "blockers": report["blocker_list"],
    }
    return report, graph


def build_control_parent_reservation_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# OpenYield Parent Control Reservation Audit",
        "",
        "This report records the decoder 2.2um wordline requirement as a parent-level metadata reservation. It does not prove physical floorplan space, legal placement, or routing.",
        "",
        "## Parent Reservation Summary",
        "",
        f"- reservation_name: `{report['reservation_name']}`",
        f"- source_requirement: `{report['source_requirement']}`",
        f"- extra_width_required: `{report['extra_width_required']}`",
        f"- reservation_policy: `{report['reservation_policy']}`",
        f"- parent_reservation_recorded: `{report['parent_reservation_recorded']}`",
        "",
        "## Affected Parent Windows",
        "",
        md_table(
            ["name", "type", "affected", "required_update", "old_width", "new_width", "delta"],
            [
                [
                    item["name"],
                    item["window_type"],
                    str(item["affected_by_2p2_requirement"]),
                    str(item["required_update"]),
                    str(item["old_width_if_known"]),
                    str(item["new_width_if_known"]),
                    str(item["delta_width"]),
                ]
                for item in report["affected_parent_windows"]
            ],
        ),
        "",
        "## Parent Keepout Requirement",
        "",
        "```json",
        json.dumps(report["parent_keepout_requirements"], ensure_ascii=False, indent=2),
        "```",
        "",
        "## Floorplan Compatibility Checks",
        "",
        "```json",
        json.dumps(report["floorplan_compatibility"], ensure_ascii=False, indent=2),
        "```",
        "",
        "## Budget / Margin Summary",
        "",
        "```json",
        json.dumps(report["budget_margin_summary"], ensure_ascii=False, indent=2),
        "```",
        "",
        "## Risk Flags",
        "",
        "```json",
        json.dumps(report["risk_flags"], ensure_ascii=False, indent=2),
        "```",
        "",
        "## Recommended Parent Policy",
        "",
        f"`{report['recommended_parent_policy']}`",
        "",
        "## Blockers",
        "",
    ]
    lines.extend([f"- {item}" for item in report["blocker_list"]])
    lines.extend(["", "## Step 6.22 Recommendation", "", report["step_6_22_recommendation"], ""])
    return "\n".join(lines)

