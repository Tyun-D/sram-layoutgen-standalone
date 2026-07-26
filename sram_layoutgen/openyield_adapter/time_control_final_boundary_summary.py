"""Final boundary summary for metadata-only OpenYield TIME/control progress.

This report consolidates the guard-style audits that define the current safe
boundary for TIME/control work. It remains metadata-only and does not authorize
standalone integration, routing, GDS generation, or physical placement.
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


def build_time_control_final_boundary_summary_report(
    *,
    openyield_root: str | Path,
    contracts_path: str | Path,
    tech_dir: str | Path,
) -> tuple[dict[str, Any], dict[str, Any]]:
    openyield_root = Path(openyield_root)
    contracts_path = Path(contracts_path)
    tech_dir = Path(tech_dir)

    goal_progress = _load_json("docs/openyield_time_control_goal_progress_audit_report.json")
    execution_guard = _load_json("docs/openyield_time_control_prototype_execution_guard_report.json")
    state_machine = _load_json("docs/openyield_time_control_prototype_state_machine_report.json")
    interface_surface = _load_json("docs/openyield_time_control_prototype_interface_surface_report.json")
    artifact_contract = _load_json("docs/openyield_time_control_prototype_artifact_contract_report.json")
    output_regression = _load_json("docs/openyield_time_control_builder_output_regression_report.json")

    boundary_rows = [
        {
            "boundary_name": "goal_progress_highest_stage",
            "status": goal_progress["audit_summary"]["highest_stage_reached"],
            "gate_closed": False,
            "evidence": goal_progress["scope"],
            "notes": "Tracks how far the metadata-only chain has progressed.",
        },
        {
            "boundary_name": "standalone_modification_gate",
            "status": goal_progress["current_gates"]["can_modify_standalone_now"],
            "gate_closed": not goal_progress["current_gates"]["can_modify_standalone_now"],
            "evidence": execution_guard["scope"],
            "notes": "Standalone remains closed across goal audit, execution guard, and state machine.",
        },
        {
            "boundary_name": "time_control_gds_generation_gate",
            "status": goal_progress["current_gates"]["can_generate_time_control_gds_now"],
            "gate_closed": not goal_progress["current_gates"]["can_generate_time_control_gds_now"],
            "evidence": execution_guard["scope"],
            "notes": "TIME/control GDS generation remains forbidden in all metadata-only audits.",
        },
        {
            "boundary_name": "physical_placement_gate",
            "status": goal_progress["current_gates"]["can_enter_physical_placement_now"],
            "gate_closed": not goal_progress["current_gates"]["can_enter_physical_placement_now"],
            "evidence": state_machine["scope"],
            "notes": "Physical placement remains closed through all audited transitions.",
        },
        {
            "boundary_name": "interface_surface_scope",
            "status": interface_surface["consistency_checks"]["future_default_off_builder_interface_surface_clean"],
            "gate_closed": False,
            "evidence": interface_surface["scope"],
            "notes": "Builder I/O surface is restricted to metadata-only plan/report artifacts.",
        },
        {
            "boundary_name": "artifact_contract_scope",
            "status": artifact_contract["consistency_checks"]["future_default_off_builder_artifact_contract_clean"],
            "gate_closed": False,
            "evidence": artifact_contract["scope"],
            "notes": "Artifact schema forbids physical-result fields and requires metadata-only sections.",
        },
        {
            "boundary_name": "output_regression_scope",
            "status": output_regression["consistency_checks"]["future_default_off_builder_output_regression_clean"],
            "gate_closed": False,
            "evidence": output_regression["scope"],
            "notes": "Current sample outputs remain free of forbidden physical-looking fields.",
        },
    ]

    reopening_requirements = [
        {
            "gate_name": "standalone_modification_gate",
            "still_closed": True,
            "required_new_evidence": [
                "legal TIME/control placement proof",
                "routing proof for TIME/control nets",
                "updated execution guard explicitly allowing standalone integration",
                "updated state machine explicitly opening standalone transition",
            ],
        },
        {
            "gate_name": "time_control_gds_generation_gate",
            "still_closed": True,
            "required_new_evidence": [
                "routing geometry proof",
                "layout assembly proof",
                "DRC/LVS-ready physical boundary evidence",
                "updated artifact/output audits allowing physical result classes",
            ],
        },
        {
            "gate_name": "physical_placement_gate",
            "still_closed": True,
            "required_new_evidence": [
                "legal placement proof for TIME/control subblocks",
                "rail continuity proof",
                "delay timing proof",
                "wen-delay timing proof",
                "updated readiness audit explicitly reopening physical placement",
            ],
        },
    ]

    residual_blockers = goal_progress["unresolved_blockers"] + [
        "prototype execution guard still forbids standalone/routing/GDS escalation",
        "prototype state machine still forbids auto-upgrade into physical stages",
        "interface surface still forbids output classes like gds_layout and routed_geometry",
        "artifact contract still forbids keys like gds_path, placed_instances, and physical_bbox",
    ]

    final_boundary_clean = all(
        [
            execution_guard["consistency_checks"]["future_default_off_builder_guardrails_clean"],
            state_machine["consistency_checks"]["future_default_off_builder_state_machine_clean"],
            interface_surface["consistency_checks"]["future_default_off_builder_interface_surface_clean"],
            artifact_contract["consistency_checks"]["future_default_off_builder_artifact_contract_clean"],
            output_regression["consistency_checks"]["future_default_off_builder_output_regression_clean"],
        ]
    )

    report = {
        "scope": "step6_42_openyield_time_control_final_boundary_summary",
        "openyield_root": str(openyield_root.resolve()),
        "contracts_path": str(contracts_path.resolve()),
        "tech_dir": str(tech_dir.resolve()),
        "boundary_rows": boundary_rows,
        "reopening_requirements": reopening_requirements,
        "source_reports": {
            "goal_progress_audit": goal_progress["scope"],
            "prototype_execution_guard": execution_guard["scope"],
            "prototype_state_machine": state_machine["scope"],
            "prototype_interface_surface": interface_surface["scope"],
            "prototype_artifact_contract": artifact_contract["scope"],
            "builder_output_regression": output_regression["scope"],
        },
        "residual_blockers": residual_blockers,
        "consistency_checks": {
            "final_boundary_summary_available": True,
            "highest_stage_reached_is_metadata_only": goal_progress["audit_summary"]["highest_stage_reached"]
            == "Post-Stage D / abstract_floorplan_payload",
            "standalone_gate_closed": not goal_progress["current_gates"]["can_modify_standalone_now"],
            "time_control_gds_gate_closed": not goal_progress["current_gates"]["can_generate_time_control_gds_now"],
            "physical_placement_gate_closed": not goal_progress["current_gates"]["can_enter_physical_placement_now"],
            "guardrails_consistent": execution_guard["consistency_checks"]["future_default_off_builder_guardrails_clean"],
            "state_machine_consistent": state_machine["consistency_checks"]["future_default_off_builder_state_machine_clean"],
            "interface_surface_consistent": interface_surface["consistency_checks"]["future_default_off_builder_interface_surface_clean"],
            "artifact_contract_consistent": artifact_contract["consistency_checks"]["future_default_off_builder_artifact_contract_clean"],
            "output_regression_consistent": output_regression["consistency_checks"]["future_default_off_builder_output_regression_clean"],
            "final_boundary_clean": final_boundary_clean,
            "can_modify_standalone_now": False,
            "can_generate_time_control_gds_now": False,
            "can_enter_physical_placement_now": False,
        },
        "audit_summary": {
            "final_boundary_summary_available": True,
            "highest_stage_reached": goal_progress["audit_summary"]["highest_stage_reached"],
            "final_boundary_clean": final_boundary_clean,
            "can_modify_standalone_now": False,
            "can_generate_time_control_gds_now": False,
            "can_enter_physical_placement_now": False,
            "legacy_path_unchanged": goal_progress["audit_summary"]["legacy_path_unchanged"],
        },
        "notes": [
            "This summary consolidates the final metadata-only boundary after Stage D and later guard audits.",
            "Passing this summary still does not authorize standalone integration, routing, GDS generation, or physical placement.",
            "The reopening requirements list what new evidence would be needed before any currently closed gate may change state.",
        ],
        "standalone_modified": False,
        "routing_modified": False,
        "gds_writer_modified": False,
        "can_modify_standalone_now": False,
        "can_generate_time_control_gds_now": False,
        "can_enter_physical_placement_now": False,
    }

    graph = {
        "scope": report["scope"],
        "nodes": (
            [{"id": row["boundary_name"], "kind": "boundary"} for row in boundary_rows]
            + [{"id": item["gate_name"], "kind": "reopening_requirement"} for item in reopening_requirements]
        ),
        "edges": [
            {
                "source": item["gate_name"],
                "target": item["gate_name"],
                "relation": "reopens_with_new_evidence",
            }
            for item in reopening_requirements
        ],
        "summary": report["audit_summary"],
    }
    return report, graph


def build_time_control_final_boundary_summary_markdown(report: dict[str, Any]) -> str:
    boundary_rows = [
        [
            row["boundary_name"],
            row["status"],
            row["gate_closed"],
            row["evidence"],
            row["notes"],
        ]
        for row in report["boundary_rows"]
    ]
    reopening_rows = [
        [
            row["gate_name"],
            row["still_closed"],
            "<br>".join(row["required_new_evidence"]),
        ]
        for row in report["reopening_requirements"]
    ]
    consistency_rows = [[key, value] for key, value in report["consistency_checks"].items()]

    lines = [
        "# OpenYield TIME Control Final Boundary Summary",
        "",
        "This is a consolidated metadata-only boundary summary for the current clean worktree.",
        "",
        "## Audit Summary",
        "",
        "```json",
        json.dumps(report["audit_summary"], ensure_ascii=False, indent=2),
        "```",
        "",
        "## Boundary Rows",
        "",
        _md_table(
            ["boundary", "status", "gate closed", "evidence", "notes"],
            boundary_rows,
        ),
        "",
        "## Reopening Requirements",
        "",
        _md_table(
            ["gate", "still closed", "required new evidence"],
            reopening_rows,
        ),
        "",
        "## Consistency Checks",
        "",
        _md_table(["check", "value"], consistency_rows),
        "",
        "## Residual Blockers",
        "",
    ]
    lines.extend(f"- {item}" for item in report["residual_blockers"])
    lines.extend(["", "## Notes", ""])
    lines.extend(f"- {item}" for item in report["notes"])
    lines.append("")
    return "\n".join(lines)
