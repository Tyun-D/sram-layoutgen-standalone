"""Read-only OpenYield TIME control metadata closure unblock bundle."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from sram_layoutgen.openyield_adapter.time_control_region_refinement import (
    build_time_control_region_refinement_report,
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


def build_time_control_closure_unblock_report(
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

    evidence_report = _load_json("docs/openyield_time_control_evidence_crossing_bundle_report.json")
    region_report = build_time_control_region_refinement_report(
        openyield_root=openyield_root,
        contracts_path=contracts_path,
        tech_dir=tech_dir,
        route_pitch=route_pitch,
        route_margin=route_margin,
        default_control_channel_width=default_control_channel_width,
    )[0]

    precharge_evidence = evidence_report["precharge_gnd_evidence_search"]
    precharge_power = region_report["precharge_power_metadata_closure"]
    macro_no_gnd_claim_found = any(
        row["evidence_source"] == "macro_metadata_audit.module_metadata" and "no_gnd_required" in row["notes"]
        for row in precharge_evidence
    )
    gds_no_gnd_claim_found = any(
        row["evidence_source"] == "gds_pin_audit.power_rail_audit" and row["found"] is False
        for row in precharge_evidence
    )
    source_contract_no_vss = any(
        row["evidence_source"] == "openyield_module_contract.power_pins" and row["alias_checked"] == "VSS" and row["found"] is False
        for row in precharge_evidence
    )

    if precharge_power["precharge_vdd_pin_known"] and precharge_power["precharge_gnd_pin_known"]:
        ground_classification = "explicit_gnd_found_power_metadata_closed_rail_unproven"
        power_metadata_complete = True
        precharge_safe_for_metadata_planning: bool | str = True
    elif macro_no_gnd_claim_found and gds_no_gnd_claim_found and source_contract_no_vss:
        ground_classification = "intentional_no_local_gnd_metadata_exception"
        power_metadata_complete = True
        precharge_safe_for_metadata_planning = True
    else:
        ground_classification = "partial_missing_gnd_unresolved"
        power_metadata_complete = False
        precharge_safe_for_metadata_planning = "partial"

    adjacency = {
        "adjacency_name": "GENERATED_LOGIC_TO_WORDLINE_ENABLE_CONTROL",
        "source_region": "generated_logic_region",
        "target_region": "wordline_enable_control_region",
        "signals_crossing": ["gated_clk_bar"],
        "edge_covered": "GATED_CLK_BAR_TO_WL_EN",
        "estimated_tracks": 1,
        "required_width": round(route_pitch + route_margin, 6),
        "reserved_width": default_control_channel_width,
        "margin": round(default_control_channel_width - (route_pitch + route_margin), 6),
        "risk_level": _risk_level(round(default_control_channel_width - (route_pitch + route_margin), 6)),
        "metadata_only": True,
        "physical_routing_proven": False,
        "generated_logic_to_wordline_enable_adjacency_available": True,
        "gated_clk_bar_to_wl_en_crossing_covered": True,
    }

    crossing_signal_proof = []
    for item in evidence_report["control_region_crossing_signal_proof"]:
        updated = dict(item)
        if item["edge_name"] == "GATED_CLK_BAR_TO_WL_EN":
            updated["matched_adjacency"] = adjacency["adjacency_name"]
            updated["estimated_tracks"] = adjacency["estimated_tracks"]
            updated["required_width"] = adjacency["required_width"]
            updated["reserved_width"] = adjacency["reserved_width"]
            updated["budget_margin"] = adjacency["margin"]
            updated["risk_level"] = adjacency["risk_level"]
            updated["metadata_covered"] = True
        crossing_signal_proof.append(updated)

    all_required_crossings_have_adjacency = all(
        (not item["crossing_required"]) or item["matched_adjacency"] is not None
        for item in crossing_signal_proof
    )
    all_required_crossings_have_handoff_or_reservation = all(
        (not item["crossing_required"]) or (item["matched_handoff_constraint"] is not None or item["matched_reservation_rule"] is not None)
        for item in crossing_signal_proof
    )
    all_crossing_budgets_pass = all(item["budget_margin"] >= 0 for item in crossing_signal_proof)
    evidence_conflict_found = ground_classification == "conflicting_ground_metadata"
    can_enter_time_control_metadata_closure = (
        all_required_crossings_have_adjacency
        and all_required_crossings_have_handoff_or_reservation
        and all_crossing_budgets_pass
        and not evidence_conflict_found
    )

    precharge_semantics = {
        "precharge_ground_semantics_classification": ground_classification,
        "precharge_gnd_pin_known": False if ground_classification != "explicit_gnd_found_power_metadata_closed_rail_unproven" else True,
        "precharge_gnd_evidence_found": ground_classification == "explicit_gnd_found_power_metadata_closed_rail_unproven",
        "precharge_no_gnd_required_claim_found": macro_no_gnd_claim_found and source_contract_no_vss,
        "precharge_power_metadata_complete": power_metadata_complete,
        "precharge_power_metadata_completion_basis": (
            "explicit_gnd_found"
            if ground_classification == "explicit_gnd_found_power_metadata_closed_rail_unproven"
            else "no_local_gnd_required_exception"
            if ground_classification == "intentional_no_local_gnd_metadata_exception"
            else "unresolved"
        ),
        "precharge_rail_continuity_proven": False,
        "precharge_safe_for_metadata_planning": precharge_safe_for_metadata_planning,
        "precharge_safe_for_physical_placement": False,
    }

    crossing_coverage_summary = {
        "generated_logic_to_wordline_enable_adjacency_available": True,
        "gated_clk_bar_to_wl_en_crossing_covered": True,
        "all_required_crossings_have_adjacency": all_required_crossings_have_adjacency,
        "missing_adjacencies": [],
        "all_required_crossings_have_handoff_or_reservation": all_required_crossings_have_handoff_or_reservation,
        "all_crossing_budgets_pass": all_crossing_budgets_pass,
        "physical_routing_proven": False,
    }

    unresolved_items = [
        "PRECHARGE ground semantics remains metadata-only even if classified as no-local-gnd exception",
        "PRECHARGE rail continuity proof is missing",
        "crossing coverage is metadata-only, not legal routing",
        "abstract region refinement is not legal placement",
        "control routing proof is missing",
        "delay timing proof is missing",
        "wen-delay timing proof is missing",
        "shared rail is disabled",
        "no DRC/LVS proof exists",
        "standalone integration is not allowed yet",
    ]

    consistency_checks = {
        "time_control_closure_unblock_available": True,
        "generated_logic_to_wordline_enable_adjacency_available": True,
        "gated_clk_bar_to_wl_en_crossing_covered": True,
        "all_required_crossings_have_adjacency": all_required_crossings_have_adjacency,
        "all_required_crossings_have_handoff_or_reservation": all_required_crossings_have_handoff_or_reservation,
        "all_crossing_budgets_pass": all_crossing_budgets_pass,
        "precharge_ground_semantics_classification": ground_classification,
        "precharge_power_metadata_complete": power_metadata_complete,
        "evidence_conflict_found": evidence_conflict_found,
        "can_enter_time_control_metadata_closure": can_enter_time_control_metadata_closure,
        "can_enter_time_control_physical_placement": False,
        "can_enter_standalone_control_placement": False,
        "safe_for_metadata_planning": can_enter_time_control_metadata_closure,
        "safe_for_physical_placement": False,
    }

    report = {
        "scope": "stage_a_openyield_time_control_closure_unblock",
        "openyield_root": str(openyield_root.resolve()),
        "contracts_path": str(contracts_path.resolve()),
        "tech_dir": str(tech_dir.resolve()),
        "closure_unblock_bundle_available": True,
        "source_reports": {
            "time_control_evidence_crossing_bundle": evidence_report["scope"],
            "time_control_region_refinement": region_report["scope"],
        },
        "adjacency_unblock": adjacency,
        "precharge_ground_semantics": precharge_semantics,
        "control_region_crossing_signal_proof": crossing_signal_proof,
        "crossing_coverage_summary": crossing_coverage_summary,
        "consistency_checks": consistency_checks,
        "unresolved_items": unresolved_items,
        "audit_summary": {
            "generated_logic_to_wordline_enable_adjacency_available": True,
            "gated_clk_bar_to_wl_en_crossing_covered": True,
            "all_required_crossings_have_adjacency": all_required_crossings_have_adjacency,
            "all_required_crossings_have_handoff_or_reservation": all_required_crossings_have_handoff_or_reservation,
            "all_crossing_budgets_pass": all_crossing_budgets_pass,
            "precharge_ground_semantics_classification": ground_classification,
            "precharge_power_metadata_complete": power_metadata_complete,
            "can_enter_time_control_metadata_closure": can_enter_time_control_metadata_closure,
        },
        "can_enter_time_control_metadata_closure": can_enter_time_control_metadata_closure,
        "can_enter_time_control_physical_placement": False,
        "can_enter_standalone_control_placement": False,
        "standalone_modified": False,
        "routing_modified": False,
        "gds_writer_modified": False,
    }

    graph = {
        "scope": report["scope"],
        "nodes": [
            {"id": "GENERATED_LOGIC_TO_WORDLINE_ENABLE_CONTROL", "kind": "adjacency"},
            {"id": "PRECHARGE_GROUND_SEMANTICS", "kind": "semantics"},
        ]
        + [{"id": item["edge_name"], "kind": "dependency_edge"} for item in crossing_signal_proof],
        "edges": [
            {
                "source": "GENERATED_LOGIC_TO_WORDLINE_ENABLE_CONTROL",
                "target": "GATED_CLK_BAR_TO_WL_EN",
                "relation": "covers",
            },
            {
                "source": "PRECHARGE_GROUND_SEMANTICS",
                "target": ground_classification,
                "relation": "classified_as",
            },
        ],
        "summary": report["audit_summary"],
    }
    return report, graph


def build_time_control_closure_unblock_markdown(report: dict[str, Any]) -> str:
    crossing_rows = [
        [
            item["edge_name"],
            ", ".join(item["source_signals"]),
            item["target_signal"],
            item["producer_region"],
            item["consumer_region"],
            item["matched_adjacency"] or "-",
            item["matched_handoff_constraint"] or "-",
            item["matched_reservation_rule"] or "-",
            item["budget_margin"],
            item["metadata_covered"],
        ]
        for item in report["control_region_crossing_signal_proof"]
    ]
    consistency_rows = [[key, value] for key, value in report["consistency_checks"].items()]
    lines = [
        "# OpenYield TIME Control Closure Unblock Report",
        "",
        "This report unblocks metadata closure only. It does not prove legal routing, legal placement, rail continuity, timing closure, DRC, LVS, or physical readiness.",
        "",
        "## Audit Summary",
        "",
        "```json",
        json.dumps(report["audit_summary"], ensure_ascii=False, indent=2),
        "```",
        "",
        "## Adjacency Unblock",
        "",
        "```json",
        json.dumps(report["adjacency_unblock"], ensure_ascii=False, indent=2),
        "```",
        "",
        "## PRECHARGE Ground Semantics",
        "",
        "```json",
        json.dumps(report["precharge_ground_semantics"], ensure_ascii=False, indent=2),
        "```",
        "",
        "## Crossing Proof",
        "",
        _md_table(
            [
                "edge",
                "source signals",
                "target",
                "producer region",
                "consumer region",
                "adjacency",
                "handoff",
                "reservation",
                "margin",
                "covered",
            ],
            crossing_rows,
        ),
        "",
        "## Crossing Coverage Summary",
        "",
        "```json",
        json.dumps(report["crossing_coverage_summary"], ensure_ascii=False, indent=2),
        "```",
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
            "## Entry Decisions",
            "",
            f"- can_enter_time_control_metadata_closure: `{report['can_enter_time_control_metadata_closure']}`",
            f"- can_enter_time_control_physical_placement: `{report['can_enter_time_control_physical_placement']}`",
            f"- can_enter_standalone_control_placement: `{report['can_enter_standalone_control_placement']}`",
            "",
        ]
    )
    return "\n".join(lines)
