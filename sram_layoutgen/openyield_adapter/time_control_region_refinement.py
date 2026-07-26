"""Read-only OpenYield TIME control-row region refinement bundle."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from sram_layoutgen.openyield_adapter.time_control_precharge_constraints_bundle import (
    build_time_control_precharge_constraints_bundle_report,
)


def _load_json(path: str | Path) -> dict[str, Any]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _md_table(headers: list[str], rows: list[list[Any]]) -> str:
    lines = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join("---" for _ in headers) + " |",
    ]
    for row in rows:
        lines.append(
            "| "
            + " | ".join(str(cell).replace("|", "\\|").replace("\n", "<br>") for cell in row)
            + " |"
        )
    return "\n".join(lines)


def _risk_level(margin: float) -> str:
    if margin < 0:
        return "fail"
    if margin == 0:
        return "tight_zero_margin"
    if margin < 0.4:
        return "pass_low_margin"
    return "pass_moderate_margin"


def _region_refinement(
    *,
    region: dict[str, Any],
    handoff_constraints: list[dict[str, Any]],
    reservation_rules: list[dict[str, Any]],
    preferred_neighbor_regions: list[str],
    route_pitch: float,
    route_margin: float,
    default_control_channel_width: float,
) -> dict[str, Any]:
    region_name = region["region_name"]
    region_constraints = [
        item["constraint_name"]
        for item in handoff_constraints
        if item["source_region"] == region_name or item["target_region"] == region_name
    ]
    region_rules = [
        item["rule_name"]
        for item in reservation_rules
        if item["source_region"] == region_name or item["target_region"] == region_name
    ]
    estimated_signal_count = len(set(region.get("output_signals", [])))
    estimated_track_count = max(
        1,
        sum(
            item["estimated_tracks"]
            for item in handoff_constraints
            if item["source_region"] == region_name
        ),
    )
    required_channel_width = round(estimated_track_count * route_pitch + route_margin, 6)
    reserved_channel_width = round(
        max(
            [default_control_channel_width]
            + [item["reserved_width"] for item in reservation_rules if item["source_region"] == region_name]
        ),
        6,
    )
    budget_margin = round(reserved_channel_width - required_channel_width, 6)
    return {
        "region_name": region_name,
        "source_contracts": region.get("source_contracts", []),
        "input_signals": region.get("input_signals", []),
        "output_signals": region.get("output_signals", []),
        "consumer_targets": region.get("consumer_targets", []),
        "preferred_neighbor_regions": preferred_neighbor_regions,
        "handoff_constraints": region_constraints,
        "reservation_rules": region_rules,
        "estimated_signal_count": estimated_signal_count,
        "estimated_track_count": estimated_track_count,
        "route_pitch": route_pitch,
        "route_margin": route_margin,
        "required_channel_width": required_channel_width,
        "reserved_channel_width": reserved_channel_width,
        "budget_margin": budget_margin,
        "risk_level": _risk_level(budget_margin),
        "bbox_proxy_policy": region.get("bbox_proxy_policy"),
        "metadata_only": True,
        "legal_physical_placement": False,
        "physical_routing_proven": False,
        "requires_generated_layout_or_stdcell_row": region.get("requires_generated_layout_or_stdcell_row", True),
        "requires_timing_proof": region.get("requires_timing_proof", True),
        "requires_routing_proof": region.get("requires_routing_proof", True),
    }


def _adjacency(
    *,
    adjacency_name: str,
    source_region: str,
    target_region: str,
    signals_crossing: list[str],
    route_pitch: float,
    route_margin: float,
    reserved_width: float,
) -> dict[str, Any]:
    estimated_tracks = max(1, len(signals_crossing))
    required_width = round(estimated_tracks * route_pitch + route_margin, 6)
    margin = round(reserved_width - required_width, 6)
    return {
        "adjacency_name": adjacency_name,
        "source_region": source_region,
        "target_region": target_region,
        "signals_crossing": signals_crossing,
        "estimated_tracks": estimated_tracks,
        "required_width": required_width,
        "reserved_width": reserved_width,
        "margin": margin,
        "risk_level": _risk_level(margin),
        "metadata_only": True,
        "physical_routing_proven": False,
    }


def build_time_control_region_refinement_report(
    *,
    openyield_root: str | Path,
    contracts_path: str | Path,
    tech_dir: str | Path,
    route_pitch: float = 0.2,
    route_margin: float = 0.2,
    default_control_channel_width: float = 2.0,
) -> tuple[dict[str, Any], dict[str, Any]]:
    openyield_root = Path(openyield_root)
    contracts_path = Path(contracts_path)
    tech_dir = Path(tech_dir)

    bundle_report, _ = build_time_control_precharge_constraints_bundle_report(
        openyield_root=openyield_root,
        contracts_path=contracts_path,
        tech_dir=tech_dir,
        route_pitch=route_pitch,
        route_margin=route_margin,
        default_control_channel_width=default_control_channel_width,
    )
    fast_report = _load_json("docs/openyield_time_control_fast_bundle_report.json")

    precharge_prev = bundle_report["precharge_adapter_metadata_closure"]
    precharge_closure_status = "partial_missing_gnd"
    if precharge_prev["precharge_vdd_pin_known"] and precharge_prev["precharge_gnd_pin_known"]:
        precharge_closure_status = "metadata_power_closed_rail_unproven"

    precharge_power_metadata_closure = {
        "precharge_power_metadata_audit_available": True,
        "precharge_macro_candidate": precharge_prev["gds_macro_candidate"],
        "precharge_consumer_signal": precharge_prev["precharge_consumer_signal"],
        "precharge_consumer_pin": precharge_prev["precharge_consumer_pin"],
        "precharge_pin_aliases": precharge_prev["precharge_consumer_pin_aliases"],
        "precharge_active_level": precharge_prev["precharge_active_level"],
        "precharge_vdd_pin_known": precharge_prev["precharge_vdd_pin_known"],
        "precharge_gnd_pin_known": precharge_prev["precharge_gnd_pin_known"],
        "precharge_vdd_side": precharge_prev["power_rail_summary"]["vdd_side"],
        "precharge_gnd_side": precharge_prev["power_rail_summary"]["gnd_side"],
        "precharge_power_domain_known": True if precharge_prev["precharge_power_metadata_complete"] else "partial",
        "precharge_power_metadata_complete": precharge_prev["precharge_power_metadata_complete"],
        "precharge_rail_continuity_proven": False,
        "precharge_shared_rail_safe": False,
        "precharge_safe_for_metadata_planning": (
            True if precharge_prev["precharge_power_metadata_complete"] else "partial"
        ),
        "precharge_safe_for_physical_placement": False,
        "precharge_closure_status": precharge_closure_status,
        "notes": [
            "This is power metadata closure only; it is not rail continuity proof.",
            "Shared rail remains disabled even if VDD metadata is present.",
            "Current closure still does not allow physical placement or legal routing claims.",
        ],
    }

    neighbor_map = {
        "delay_chain_region": ["generated_logic_region", "sense_write_enable_region"],
        "pdrive_region": ["generated_logic_region", "precharge_control_region", "wordline_enable_control_region"],
        "generated_logic_region": ["delay_chain_region", "pdrive_region", "consumer_handoff_region"],
        "consumer_handoff_region": [
            "generated_logic_region",
            "precharge_control_region",
            "wordline_enable_control_region",
            "sense_write_enable_region",
        ],
        "precharge_control_region": ["pdrive_region", "consumer_handoff_region", "wordline_enable_control_region"],
        "wordline_enable_control_region": ["pdrive_region", "consumer_handoff_region", "precharge_control_region"],
        "sense_write_enable_region": ["delay_chain_region", "generated_logic_region", "consumer_handoff_region"],
    }

    regions = [
        _region_refinement(
            region=region,
            handoff_constraints=bundle_report["control_row_handoff_constraints"],
            reservation_rules=bundle_report["control_channel_reservation_rules"],
            preferred_neighbor_regions=neighbor_map.get(region["region_name"], []),
            route_pitch=route_pitch,
            route_margin=route_margin,
            default_control_channel_width=default_control_channel_width,
        )
        for region in fast_report["control_row_abstract_placement_envelope"]["regions"]
    ]

    adjacencies = [
        _adjacency(
            adjacency_name="DELAY_CHAIN_TO_GENERATED_LOGIC",
            source_region="delay_chain_region",
            target_region="generated_logic_region",
            signals_crossing=["rbl_delay", "rbl_delay_bar_wen"],
            route_pitch=route_pitch,
            route_margin=route_margin,
            reserved_width=default_control_channel_width,
        ),
        _adjacency(
            adjacency_name="PDRIVE_TO_GENERATED_LOGIC",
            source_region="pdrive_region",
            target_region="generated_logic_region",
            signals_crossing=["clk_buf", "PRE", "wl_en"],
            route_pitch=route_pitch,
            route_margin=route_margin,
            reserved_width=default_control_channel_width,
        ),
        _adjacency(
            adjacency_name="GENERATED_LOGIC_TO_CONSUMER_HANDOFF",
            source_region="generated_logic_region",
            target_region="consumer_handoff_region",
            signals_crossing=["w_en", "s_en", "PRE", "wl_en"],
            route_pitch=route_pitch,
            route_margin=route_margin,
            reserved_width=default_control_channel_width,
        ),
        _adjacency(
            adjacency_name="PRECHARGE_CONTROL_TO_CONSUMER_HANDOFF",
            source_region="precharge_control_region",
            target_region="consumer_handoff_region",
            signals_crossing=["precharge_enb"],
            route_pitch=route_pitch,
            route_margin=route_margin,
            reserved_width=default_control_channel_width,
        ),
        _adjacency(
            adjacency_name="WORDLINE_ENABLE_TO_CONSUMER_HANDOFF",
            source_region="wordline_enable_control_region",
            target_region="consumer_handoff_region",
            signals_crossing=["wordline_enable"],
            route_pitch=route_pitch,
            route_margin=route_margin,
            reserved_width=default_control_channel_width,
        ),
        _adjacency(
            adjacency_name="SENSE_WRITE_ENABLE_TO_CONSUMER_HANDOFF",
            source_region="sense_write_enable_region",
            target_region="consumer_handoff_region",
            signals_crossing=["write_enable", "sense_enable"],
            route_pitch=route_pitch,
            route_margin=route_margin,
            reserved_width=default_control_channel_width,
        ),
        _adjacency(
            adjacency_name="WORDLINE_ENABLE_TO_PRECHARGE_CONTROL",
            source_region="wordline_enable_control_region",
            target_region="precharge_control_region",
            signals_crossing=["wl_en_bar"],
            route_pitch=route_pitch,
            route_margin=route_margin,
            reserved_width=default_control_channel_width,
        ),
    ]

    interface_refinement = [
        {
            "interface_name": item["interface_name"],
            "source_regions": sorted(
                {
                    constraint["source_region"]
                    for constraint in bundle_report["control_row_handoff_constraints"]
                    if constraint["constraint_name"] in item["handoff_constraints"]
                }
            ),
            "target_macro": item["target_macro"],
            "target_pins": item["target_pins"],
            "control_signals": item["source_signals"],
            "polarity_expectation": item["polarity_expectation"],
            "consumer_contracts": item["consumer_contracts"],
            "generated_logic_contracts": item["generated_logic_contracts"],
            "handoff_constraints": item["handoff_constraints"],
            "reservation_rules": item["reservation_rules"],
            "precharge_power_dependency_if_any": (
                precharge_closure_status if item["target_macro"] == "PRECHARGE" else None
            ),
            "metadata_ready": (
                "partial" if item["target_macro"] == "PRECHARGE" and precharge_closure_status == "partial_missing_gnd"
                else True
            ),
            "physical_ready": False,
            "blocked_by": item["blocked_by"],
        }
        for item in bundle_report["grouped_planning_interfaces"]
    ]

    all_region_budgets_pass = all(item["budget_margin"] >= 0 for item in regions)
    all_adjacency_budgets_pass = all(item["margin"] >= 0 for item in adjacencies)
    precharge_interface_metadata_ready = next(
        item["metadata_ready"]
        for item in interface_refinement
        if item["interface_name"] == "TIME_CONTROL_TO_PRECHARGE_INTERFACE"
    )

    unresolved_items = [
        "PRECHARGE power metadata may remain partial if GND is still missing",
        "rail continuity proof is missing",
        "region budgets are metadata-only",
        "region adjacency is not legal routing",
        "abstract region refinement is not legal placement",
        "control routing proof is missing",
        "delay timing proof is missing",
        "wen-delay timing proof is missing",
        "shared rail is disabled",
        "no DRC/LVS proof exists",
        "standalone integration is not allowed yet",
    ]

    consistency_checks = {
        "time_control_region_refinement_available": True,
        "precharge_power_metadata_audit_available": True,
        "precharge_power_metadata_complete": precharge_power_metadata_closure["precharge_power_metadata_complete"],
        "precharge_closure_status": precharge_closure_status,
        "control_row_region_refinement_available": True,
        "region_adjacency_metadata_available": True,
        "grouped_planning_interface_refinement_available": True,
        "all_region_budgets_pass": all_region_budgets_pass,
        "all_adjacency_budgets_pass": all_adjacency_budgets_pass,
        "precharge_interface_metadata_ready": precharge_interface_metadata_ready,
        "safe_for_metadata_planning": all_region_budgets_pass and all_adjacency_budgets_pass,
        "safe_for_physical_placement": False,
        "can_enter_time_control_region_metadata_planning": all_region_budgets_pass and all_adjacency_budgets_pass,
        "can_enter_time_control_physical_placement": False,
        "can_enter_standalone_control_placement": False,
    }

    report = {
        "scope": "step6_29_openyield_time_control_region_refinement_bundle",
        "openyield_root": str(openyield_root.resolve()),
        "contracts_path": str(contracts_path.resolve()),
        "tech_dir": str(tech_dir.resolve()),
        "bundle_mode": "fast_metadata_bundle",
        "source_reports": {
            "time_control_precharge_constraints_bundle": bundle_report["scope"],
            "time_control_fast_bundle": fast_report["scope"],
        },
        "precharge_power_metadata_closure": precharge_power_metadata_closure,
        "control_row_region_refinement": regions,
        "region_adjacency_handoff_planning": adjacencies,
        "grouped_planning_interface_refinement": interface_refinement,
        "consistency_checks": consistency_checks,
        "unresolved_items": unresolved_items,
        "audit_summary": {
            "time_control_region_refinement_available": True,
            "precharge_closure_status": precharge_closure_status,
            "all_region_budgets_pass": all_region_budgets_pass,
            "all_adjacency_budgets_pass": all_adjacency_budgets_pass,
            "can_enter_time_control_region_metadata_planning": consistency_checks["can_enter_time_control_region_metadata_planning"],
            "can_enter_time_control_physical_placement": False,
            "can_enter_standalone_control_placement": False,
        },
        "can_enter_time_control_region_metadata_planning": consistency_checks["can_enter_time_control_region_metadata_planning"],
        "can_enter_time_control_physical_placement": False,
        "can_enter_standalone_control_placement": False,
        "step_6_30_recommendation": {
            "recommended_next_phase": "time_control_precharge_gnd_evidence_or_region_crossing_fanout_refinement",
            "candidate_directions": [
                "precharge_gnd_evidence_search",
                "control_region_crossing_signal_proof",
                "time_control_delay_timing_metadata_refinement",
                "control_row_macro_handoff_side_refinement",
            ],
            "reason": [
                "PRECHARGE power metadata remains the least-closed part of the bundle because GND is still not proven in current metadata.",
                "Region-level planning is now structured enough for metadata planning, but it still does not prove legal routing or legal placement.",
                "The next safe step is deeper evidence gathering, not standalone integration.",
            ],
        },
        "standalone_modified": False,
        "routing_modified": False,
        "gds_writer_modified": False,
    }

    graph = {
        "scope": report["scope"],
        "nodes": (
            [{"id": "PRECHARGE_POWER_METADATA_CLOSURE", "kind": "power_metadata"}]
            + [{"id": item["region_name"], "kind": "control_region"} for item in regions]
            + [{"id": item["adjacency_name"], "kind": "region_adjacency"} for item in adjacencies]
            + [{"id": item["interface_name"], "kind": "grouped_interface"} for item in interface_refinement]
        ),
        "edges": (
            [
                {
                    "source": "PRECHARGE_POWER_METADATA_CLOSURE",
                    "target": "TIME_CONTROL_TO_PRECHARGE_INTERFACE",
                    "relation": "gates_metadata_readiness",
                }
            ]
            + [
                {
                    "source": item["source_region"],
                    "target": item["target_region"],
                    "relation": "adjacent_via_metadata",
                    "adjacency_name": item["adjacency_name"],
                }
                for item in adjacencies
            ]
            + [
                {
                    "source": interface["interface_name"],
                    "target": region_name,
                    "relation": "draws_from_region",
                }
                for interface in interface_refinement
                for region_name in interface["source_regions"]
            ]
        ),
        "summary": report["audit_summary"],
    }
    return report, graph


def build_time_control_region_refinement_markdown(report: dict[str, Any]) -> str:
    region_rows = [
        [
            item["region_name"],
            ", ".join(item["input_signals"]),
            ", ".join(item["output_signals"]),
            ", ".join(item["preferred_neighbor_regions"]),
            item["estimated_signal_count"],
            item["estimated_track_count"],
            item["required_channel_width"],
            item["reserved_channel_width"],
            item["budget_margin"],
            item["risk_level"],
        ]
        for item in report["control_row_region_refinement"]
    ]
    adjacency_rows = [
        [
            item["adjacency_name"],
            item["source_region"],
            item["target_region"],
            ", ".join(item["signals_crossing"]),
            item["estimated_tracks"],
            item["required_width"],
            item["reserved_width"],
            item["margin"],
            item["risk_level"],
        ]
        for item in report["region_adjacency_handoff_planning"]
    ]
    interface_rows = [
        [
            item["interface_name"],
            ", ".join(item["source_regions"]),
            item["target_macro"],
            ", ".join(item["control_signals"]),
            item["precharge_power_dependency_if_any"] or "-",
            item["metadata_ready"],
            item["physical_ready"],
        ]
        for item in report["grouped_planning_interface_refinement"]
    ]
    consistency_rows = [[key, value] for key, value in report["consistency_checks"].items()]

    lines = [
        "# OpenYield TIME Control Region Refinement Report",
        "",
        "This report refines metadata-only control-row regions and PRECHARGE power closure. It does not prove rail continuity, legal routing, legal placement, timing closure, DRC, or LVS.",
        "",
        "## Audit Summary",
        "",
        "```json",
        json.dumps(report["audit_summary"], ensure_ascii=False, indent=2),
        "```",
        "",
        "## PRECHARGE Power Metadata Closure",
        "",
        "```json",
        json.dumps(report["precharge_power_metadata_closure"], ensure_ascii=False, indent=2),
        "```",
        "",
        "## Control-Row Region Refinement",
        "",
        _md_table(
            [
                "region",
                "inputs",
                "outputs",
                "preferred neighbors",
                "signal count",
                "track count",
                "required width",
                "reserved width",
                "margin",
                "risk",
            ],
            region_rows,
        ),
        "",
        "## Region Adjacency / Handoff Planning",
        "",
        _md_table(
            [
                "adjacency",
                "source",
                "target",
                "signals",
                "tracks",
                "required width",
                "reserved width",
                "margin",
                "risk",
            ],
            adjacency_rows,
        ),
        "",
        "## Grouped Planning Interface Refinement",
        "",
        _md_table(
            [
                "interface",
                "source regions",
                "target macro",
                "control signals",
                "precharge power dependency",
                "metadata ready",
                "physical ready",
            ],
            interface_rows,
        ),
        "",
        "## Consistency Checks",
        "",
        _md_table(["check", "value"], consistency_rows),
        "",
        "## Unresolved Items",
        "",
    ]
    lines.extend(f"- {item}" for item in report["unresolved_items"])
    lines.extend(
        [
            "",
            "## Step 6.30 Recommendation",
            "",
            "```json",
            json.dumps(report["step_6_30_recommendation"], ensure_ascii=False, indent=2),
            "```",
            "",
            "## Entry Decisions",
            "",
            f"- can_enter_time_control_region_metadata_planning: `{report['can_enter_time_control_region_metadata_planning']}`",
            f"- can_enter_time_control_physical_placement: `{report['can_enter_time_control_physical_placement']}`",
            f"- can_enter_standalone_control_placement: `{report['can_enter_standalone_control_placement']}`",
            "",
        ]
    )
    return "\n".join(lines)
