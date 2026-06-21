"""Goal-chain audit for OpenYield TIME/control metadata-to-prototype progress.

This module does not create placement, routing, or GDS output. It only audits
how far the current clean worktree has progressed along the staged goal chain
described by the active metadata-only objective.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


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


def _stage_status(
    *,
    stage_name: str,
    gate_name: str,
    gate_value: bool,
    report_path: str,
    summary: dict[str, Any],
    next_gate_opened: bool,
    notes: list[str],
) -> dict[str, Any]:
    return {
        "stage_name": stage_name,
        "gate_name": gate_name,
        "gate_value": gate_value,
        "report_path": report_path,
        "summary": summary,
        "next_gate_opened": next_gate_opened,
        "notes": notes,
    }


def build_time_control_goal_progress_audit_report(
    *,
    openyield_root: str | Path,
    contracts_path: str | Path,
    tech_dir: str | Path,
) -> tuple[dict[str, Any], dict[str, Any]]:
    openyield_root = Path(openyield_root)
    contracts_path = Path(contracts_path)
    tech_dir = Path(tech_dir)

    stage_a = _load_json("docs/openyield_time_control_closure_unblock_report.json")
    stage_b = _load_json("docs/openyield_time_control_metadata_closure_report.json")
    stage_c = _load_json("docs/openyield_time_control_placement_readiness_report.json")
    stage_d = _load_json("docs/openyield_time_control_opt_in_prototype_plan_report.json")
    experimental_contract = _load_json("docs/openyield_time_control_experimental_contract_report.json")
    abstract_payload = _load_json("docs/openyield_time_control_abstract_floorplan_payload_report.json")

    stage_records = [
        _stage_status(
            stage_name="Stage A / closure_unblock",
            gate_name="can_enter_time_control_metadata_closure",
            gate_value=bool(stage_a["can_enter_time_control_metadata_closure"]),
            report_path="docs/openyield_time_control_closure_unblock_report.json",
            summary=stage_a["audit_summary"],
            next_gate_opened=bool(stage_b["can_enter_very_limited_abstract_to_placement_readiness"]),
            notes=[
                "Repairs the 6.30 crossing-gap blocker with GENERATED_LOGIC_TO_WORDLINE_ENABLE_CONTROL adjacency.",
                f"PRECHARGE semantics classification={stage_a['precharge_ground_semantics']['precharge_ground_semantics_classification']}.",
            ],
        ),
        _stage_status(
            stage_name="Stage B / metadata_closure",
            gate_name="can_enter_very_limited_abstract_to_placement_readiness",
            gate_value=bool(stage_b["can_enter_very_limited_abstract_to_placement_readiness"]),
            report_path="docs/openyield_time_control_metadata_closure_report.json",
            summary=stage_b["audit_summary"],
            next_gate_opened=bool(stage_c["can_create_experimental_opt_in_placement_plan"]),
            notes=[
                "Closes the metadata chain without claiming legal routing or physical placement.",
                f"PRECHARGE closure status={stage_b['precharge_closure_status']}.",
            ],
        ),
        _stage_status(
            stage_name="Stage C / placement_readiness",
            gate_name="can_create_experimental_opt_in_placement_plan",
            gate_value=bool(stage_c["can_create_experimental_opt_in_placement_plan"]),
            report_path="docs/openyield_time_control_placement_readiness_report.json",
            summary=stage_c["audit_summary"],
            next_gate_opened=bool(stage_d["consistency_checks"]["default_off_experimental_opt_in_prototype_plan_available"]),
            notes=[
                "Very-limited readiness is open only for metadata-only prototype planning.",
                "Physical placement, standalone edits, and GDS generation remain closed.",
            ],
        ),
        _stage_status(
            stage_name="Stage D / default_off_prototype_plan",
            gate_name="default_off_experimental_opt_in_prototype_plan_available",
            gate_value=bool(stage_d["consistency_checks"]["default_off_experimental_opt_in_prototype_plan_available"]),
            report_path="docs/openyield_time_control_opt_in_prototype_plan_report.json",
            summary=stage_d["audit_summary"],
            next_gate_opened=bool(experimental_contract["consistency_checks"]["experimental_contract_available"]),
            notes=[
                "Defines the default-off prototype contract surface.",
                "Still forbidden to wire into standalone, routing, or GDS writer.",
            ],
        ),
        _stage_status(
            stage_name="Post-Stage D / experimental_contract",
            gate_name="experimental_contract_available",
            gate_value=bool(experimental_contract["consistency_checks"]["experimental_contract_available"]),
            report_path="docs/openyield_time_control_experimental_contract_report.json",
            summary=experimental_contract["audit_summary"],
            next_gate_opened=bool(abstract_payload["consistency_checks"]["abstract_floorplan_payload_available"]),
            notes=[
                "Adds structured config + prototype subplans for future default-off work.",
                "Remains metadata-only and does not reopen physical gates.",
            ],
        ),
        _stage_status(
            stage_name="Post-Stage D / abstract_floorplan_payload",
            gate_name="abstract_floorplan_payload_available",
            gate_value=bool(abstract_payload["consistency_checks"]["abstract_floorplan_payload_available"]),
            report_path="docs/openyield_time_control_abstract_floorplan_payload_report.json",
            summary=abstract_payload["audit_summary"],
            next_gate_opened=False,
            notes=[
                "Packages regions, subblocks, and handoffs into a consumable metadata payload.",
                "This is the current farthest safe boundary in the clean worktree.",
            ],
        ),
    ]

    highest_stage_reached = "Post-Stage D / abstract_floorplan_payload"
    if not abstract_payload["consistency_checks"]["abstract_floorplan_payload_available"]:
        highest_stage_reached = "Post-Stage D / experimental_contract"
    if not experimental_contract["consistency_checks"]["experimental_contract_available"]:
        highest_stage_reached = "Stage D / default_off_prototype_plan"
    if not stage_d["consistency_checks"]["default_off_experimental_opt_in_prototype_plan_available"]:
        highest_stage_reached = "Stage C / placement_readiness"
    if not stage_c["can_create_experimental_opt_in_placement_plan"]:
        highest_stage_reached = "Stage B / metadata_closure"
    if not stage_b["can_enter_very_limited_abstract_to_placement_readiness"]:
        highest_stage_reached = "Stage A / closure_unblock"

    stop_condition_status = {
        "evidence_conflict_found": bool(stage_a["consistency_checks"]["evidence_conflict_found"]),
        "crossing_gap_unresolved": not bool(stage_a["crossing_coverage_summary"]["all_required_crossings_have_adjacency"]),
        "metadata_closure_impossible": not bool(stage_b["consistency_checks"]["time_control_metadata_closure_available"]),
        "would_require_modifying_hardcell_gds": False,
        "would_require_claiming_physical_proof_without_evidence": True,
        "would_require_changing_standalone_routing_gds_writer_before_readiness": True,
    }

    current_gates = {
        "can_enter_time_control_metadata_closure": bool(stage_a["can_enter_time_control_metadata_closure"]),
        "can_enter_very_limited_abstract_to_placement_readiness": bool(
            stage_b["can_enter_very_limited_abstract_to_placement_readiness"]
        ),
        "can_create_experimental_opt_in_placement_plan": bool(stage_c["can_create_experimental_opt_in_placement_plan"]),
        "can_modify_standalone_now": False,
        "can_generate_time_control_gds_now": False,
        "can_enter_physical_placement_now": False,
        "legacy_path_unchanged": True,
        "standalone_modified": False,
        "routing_modified": False,
        "gds_writer_modified": False,
    }

    unresolved_blockers = [
        "rail continuity proof is still missing",
        "legal routing proof is still missing",
        "delay timing proof is still missing",
        "wen-delay timing proof is still missing",
        "no TIME/control physical placement proof exists",
        "no TIME/control GDS generation is allowed yet",
        "standalone integration remains blocked",
    ]

    report = {
        "scope": "goal_chain_openyield_time_control_progress_audit",
        "openyield_root": str(openyield_root.resolve()),
        "contracts_path": str(contracts_path.resolve()),
        "tech_dir": str(tech_dir.resolve()),
        "stage_records": stage_records,
        "highest_stage_reached": highest_stage_reached,
        "current_gates": current_gates,
        "stop_condition_status": stop_condition_status,
        "unresolved_blockers": unresolved_blockers,
        "audit_summary": {
            "highest_stage_reached": highest_stage_reached,
            "can_enter_time_control_metadata_closure": current_gates["can_enter_time_control_metadata_closure"],
            "can_enter_very_limited_abstract_to_placement_readiness": current_gates["can_enter_very_limited_abstract_to_placement_readiness"],
            "can_create_experimental_opt_in_placement_plan": current_gates["can_create_experimental_opt_in_placement_plan"],
            "can_modify_standalone_now": False,
            "can_generate_time_control_gds_now": False,
            "can_enter_physical_placement_now": False,
            "legacy_path_unchanged": True,
        },
        "standalone_modified": False,
        "routing_modified": False,
        "gds_writer_modified": False,
    }

    graph = {
        "scope": report["scope"],
        "nodes": [{"id": item["stage_name"], "kind": "stage"} for item in stage_records],
        "edges": [
            {
                "source": stage_records[index]["stage_name"],
                "target": stage_records[index + 1]["stage_name"],
                "relation": "progresses_to",
                "next_gate_opened": stage_records[index]["next_gate_opened"],
            }
            for index in range(len(stage_records) - 1)
        ],
        "summary": report["audit_summary"],
    }
    return report, graph


def build_time_control_goal_progress_audit_markdown(report: dict[str, Any]) -> str:
    stage_rows = [
        [
            item["stage_name"],
            item["gate_name"],
            item["gate_value"],
            item["next_gate_opened"],
            item["report_path"],
            "<br>".join(item["notes"]),
        ]
        for item in report["stage_records"]
    ]
    gate_rows = [[key, value] for key, value in report["current_gates"].items()]
    stop_rows = [[key, value] for key, value in report["stop_condition_status"].items()]

    lines = [
        "# OpenYield TIME Control Goal Progress Audit",
        "",
        "This is a consolidated evidence audit for the current goal chain. It does not create placement, routing, or GDS output.",
        "",
        "## Audit Summary",
        "",
        "```json",
        json.dumps(report["audit_summary"], ensure_ascii=False, indent=2),
        "```",
        "",
        "## Stage Records",
        "",
        _md_table(
            ["stage", "gate", "value", "next gate opened", "report", "notes"],
            stage_rows,
        ),
        "",
        "## Current Gates",
        "",
        _md_table(["gate", "value"], gate_rows),
        "",
        "## Stop Condition Status",
        "",
        _md_table(["condition", "value"], stop_rows),
        "",
        "## Unresolved Blockers",
        "",
    ]
    lines.extend(f"- {item}" for item in report["unresolved_blockers"])
    lines.append("")
    return "\n".join(lines)
