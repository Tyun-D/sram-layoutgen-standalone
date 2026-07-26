"""State-machine audit for future default-off TIME/control prototype builders.

This audit formalizes the metadata-only phase progression and forbidden
auto-upgrades for future default-off prototype builders. It checks that current
reports support deterministic stage transitions on the metadata side while
keeping physical-placement, routing, standalone integration, and GDS generation
hard-blocked.
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


def build_time_control_prototype_state_machine_report(
    *,
    openyield_root: str | Path,
    contracts_path: str | Path,
    tech_dir: str | Path,
) -> tuple[dict[str, Any], dict[str, Any]]:
    openyield_root = Path(openyield_root)
    contracts_path = Path(contracts_path)
    tech_dir = Path(tech_dir)

    closure = _load_json("docs/openyield_time_control_metadata_closure_report.json")
    readiness = _load_json("docs/openyield_time_control_placement_readiness_report.json")
    prototype_plan = _load_json("docs/openyield_time_control_opt_in_prototype_plan_report.json")
    completeness = _load_json("docs/openyield_time_control_payload_completeness_report.json")
    consumption = _load_json("docs/openyield_time_control_payload_consumption_contract_report.json")
    materialization = _load_json("docs/openyield_time_control_payload_materialization_boundary_report.json")
    execution_guard = _load_json("docs/openyield_time_control_prototype_execution_guard_report.json")

    stage_rows = [
        {
            "stage_name": "metadata_closure",
            "scope": closure["scope"],
            "entry_condition_met": closure["consistency_checks"]["time_control_metadata_closure_available"],
            "next_stage": "placement_readiness",
            "next_stage_allowed": closure["consistency_checks"]["can_enter_very_limited_abstract_to_placement_readiness"],
            "physical_gate_open": closure["consistency_checks"]["can_enter_time_control_physical_placement"],
            "standalone_gate_open": closure["consistency_checks"]["can_enter_standalone_control_placement"],
        },
        {
            "stage_name": "placement_readiness",
            "scope": readiness["scope"],
            "entry_condition_met": readiness["consistency_checks"]["time_control_placement_readiness_available"],
            "next_stage": "prototype_plan",
            "next_stage_allowed": readiness["consistency_checks"]["can_create_experimental_opt_in_placement_plan"],
            "physical_gate_open": readiness["consistency_checks"]["can_enter_physical_placement"],
            "standalone_gate_open": readiness["consistency_checks"]["can_modify_standalone"],
        },
        {
            "stage_name": "prototype_plan",
            "scope": prototype_plan["scope"],
            "entry_condition_met": prototype_plan["consistency_checks"]["default_off_experimental_opt_in_prototype_plan_available"],
            "next_stage": "payload_completeness",
            "next_stage_allowed": prototype_plan["consistency_checks"]["safe_for_metadata_prototype_only"],
            "physical_gate_open": prototype_plan["can_enter_physical_placement_now"],
            "standalone_gate_open": prototype_plan["can_modify_standalone_now"],
        },
        {
            "stage_name": "payload_completeness",
            "scope": completeness["scope"],
            "entry_condition_met": completeness["consistency_checks"]["payload_completeness_audit_available"],
            "next_stage": "payload_consumption_contract",
            "next_stage_allowed": completeness["consistency_checks"]["consumption_contract_complete_for_metadata"],
            "physical_gate_open": completeness["can_enter_physical_placement_now"],
            "standalone_gate_open": completeness["can_modify_standalone_now"],
        },
        {
            "stage_name": "payload_consumption_contract",
            "scope": consumption["scope"],
            "entry_condition_met": consumption["consistency_checks"]["payload_consumption_contract_available"],
            "next_stage": "payload_materialization_boundary",
            "next_stage_allowed": consumption["consistency_checks"]["future_default_off_builder_can_consume_metadata"],
            "physical_gate_open": consumption["can_enter_physical_placement_now"],
            "standalone_gate_open": consumption["can_modify_standalone_now"],
        },
        {
            "stage_name": "payload_materialization_boundary",
            "scope": materialization["scope"],
            "entry_condition_met": materialization["consistency_checks"]["payload_materialization_boundary_audit_available"],
            "next_stage": "prototype_execution_guard",
            "next_stage_allowed": materialization["consistency_checks"]["future_default_off_builder_can_materialize_metadata_plan"],
            "physical_gate_open": materialization["can_enter_physical_placement_now"],
            "standalone_gate_open": materialization["can_modify_standalone_now"],
        },
        {
            "stage_name": "prototype_execution_guard",
            "scope": execution_guard["scope"],
            "entry_condition_met": execution_guard["consistency_checks"]["prototype_execution_guard_audit_available"],
            "next_stage": "future_builder_implementation",
            "next_stage_allowed": execution_guard["consistency_checks"]["future_default_off_builder_guardrails_clean"],
            "physical_gate_open": execution_guard["can_enter_physical_placement_now"],
            "standalone_gate_open": execution_guard["can_modify_standalone_now"],
        },
    ]

    transition_rows = []
    transition_violations: list[str] = []
    for row in stage_rows:
        metadata_only_transition = bool(row["entry_condition_met"] and row["next_stage_allowed"])
        forbidden_auto_upgrade_clean = not row["physical_gate_open"] and not row["standalone_gate_open"]
        transition_rows.append(
            {
                "from_stage": row["stage_name"],
                "to_stage": row["next_stage"],
                "metadata_only_transition": metadata_only_transition,
                "forbidden_auto_upgrade_clean": forbidden_auto_upgrade_clean,
            }
        )
        if not (metadata_only_transition and forbidden_auto_upgrade_clean):
            transition_violations.append(f"{row['stage_name']}->{row['next_stage']}")

    global_guard_rows = [
        {
            "guard_name": "physical_gate_stays_closed_through_all_stages",
            "passed": all(not row["physical_gate_open"] for row in stage_rows),
        },
        {
            "guard_name": "standalone_gate_stays_closed_through_all_stages",
            "passed": all(not row["standalone_gate_open"] for row in stage_rows),
        },
        {
            "guard_name": "metadata_chain_monotonic",
            "passed": all(row["entry_condition_met"] for row in stage_rows[:-1]) and stage_rows[-1]["entry_condition_met"],
        },
        {
            "guard_name": "metadata_transition_chain_monotonic",
            "passed": all(row["metadata_only_transition"] for row in transition_rows),
        },
    ]
    global_guard_violations = [row["guard_name"] for row in global_guard_rows if not row["passed"]]

    auto_upgrade_rows = [
        {
            "auto_upgrade_name": "to_physical_placement",
            "allowed_now": False,
            "blocked_by": [
                "no legal placement proof",
                "no routing proof",
                "no DRC/LVS proof",
            ],
        },
        {
            "auto_upgrade_name": "to_standalone_integration",
            "allowed_now": False,
            "blocked_by": [
                "standalone gate remains closed",
                "physical proof missing",
                "generator-path integration forbidden",
            ],
        },
        {
            "auto_upgrade_name": "to_time_control_gds",
            "allowed_now": False,
            "blocked_by": [
                "physical GDS generation forbidden",
                "routing proof missing",
                "signoff proof missing",
            ],
        },
    ]

    future_default_off_builder_state_machine_clean = (
        not transition_violations
        and not global_guard_violations
        and closure["consistency_checks"]["time_control_metadata_closure_available"]
        and readiness["consistency_checks"]["can_create_experimental_opt_in_placement_plan"]
        and completeness["consistency_checks"]["consumption_contract_complete_for_metadata"]
        and consumption["consistency_checks"]["future_default_off_builder_can_consume_metadata"]
        and materialization["consistency_checks"]["future_default_off_builder_can_materialize_metadata_plan"]
        and execution_guard["consistency_checks"]["future_default_off_builder_guardrails_clean"]
    )

    report = {
        "scope": "step6_38_openyield_time_control_prototype_state_machine_audit",
        "openyield_root": str(openyield_root.resolve()),
        "contracts_path": str(contracts_path.resolve()),
        "tech_dir": str(tech_dir.resolve()),
        "stage_rows": stage_rows,
        "transition_rows": transition_rows,
        "global_guard_rows": global_guard_rows,
        "auto_upgrade_rows": auto_upgrade_rows,
        "source_reports": {
            "metadata_closure": closure["scope"],
            "placement_readiness": readiness["scope"],
            "prototype_plan": prototype_plan["scope"],
            "payload_completeness": completeness["scope"],
            "payload_consumption_contract": consumption["scope"],
            "payload_materialization_boundary": materialization["scope"],
            "prototype_execution_guard": execution_guard["scope"],
        },
        "violations": {
            "transition_violations": transition_violations,
            "global_guard_violations": global_guard_violations,
        },
        "consistency_checks": {
            "prototype_state_machine_audit_available": True,
            "metadata_stage_chain_complete": not global_guard_violations,
            "metadata_only_transitions_clean": not transition_violations,
            "physical_gate_closed_across_stages": global_guard_rows[0]["passed"],
            "standalone_gate_closed_across_stages": global_guard_rows[1]["passed"],
            "forbidden_auto_upgrades_explicit": True,
            "future_default_off_builder_state_machine_clean": future_default_off_builder_state_machine_clean,
            "can_modify_standalone_now": False,
            "can_generate_time_control_gds_now": False,
            "can_enter_physical_placement_now": False,
        },
        "audit_summary": {
            "prototype_state_machine_audit_available": True,
            "metadata_only_transitions_clean": not transition_violations,
            "physical_gate_closed_across_stages": global_guard_rows[0]["passed"],
            "standalone_gate_closed_across_stages": global_guard_rows[1]["passed"],
            "future_default_off_builder_state_machine_clean": future_default_off_builder_state_machine_clean,
            "can_modify_standalone_now": False,
            "can_generate_time_control_gds_now": False,
            "can_enter_physical_placement_now": False,
        },
        "notes": [
            "This audit formalizes the metadata-only phase progression for future default-off prototype builders.",
            "Passing this audit still does not authorize standalone integration, routing, GDS generation, or physical placement.",
            "The purpose is to prevent silent or accidental gate escalation when a builder implementation is introduced later.",
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
            [{"id": row["stage_name"], "kind": "stage"} for row in stage_rows]
            + [{"id": row["auto_upgrade_name"], "kind": "forbidden_auto_upgrade"} for row in auto_upgrade_rows]
        ),
        "edges": (
            [
                {
                    "source": row["from_stage"],
                    "target": row["to_stage"],
                    "relation": "metadata_transition",
                    "allowed": row["metadata_only_transition"],
                }
                for row in transition_rows
            ]
            + [
                {
                    "source": stage["stage_name"],
                    "target": auto["auto_upgrade_name"],
                    "relation": "must_not_auto_upgrade",
                    "allowed": auto["allowed_now"],
                }
                for stage in stage_rows
                for auto in auto_upgrade_rows
            ]
        ),
        "summary": report["audit_summary"],
    }
    return report, graph


def build_time_control_prototype_state_machine_markdown(report: dict[str, Any]) -> str:
    stage_rows = [
        [
            row["stage_name"],
            row["next_stage"],
            row["entry_condition_met"],
            row["next_stage_allowed"],
            row["physical_gate_open"],
            row["standalone_gate_open"],
        ]
        for row in report["stage_rows"]
    ]
    transition_rows = [
        [
            row["from_stage"],
            row["to_stage"],
            row["metadata_only_transition"],
            row["forbidden_auto_upgrade_clean"],
        ]
        for row in report["transition_rows"]
    ]
    global_rows = [[row["guard_name"], row["passed"]] for row in report["global_guard_rows"]]
    auto_rows = [
        [row["auto_upgrade_name"], row["allowed_now"], row["blocked_by"]] for row in report["auto_upgrade_rows"]
    ]
    consistency_rows = [[key, value] for key, value in report["consistency_checks"].items()]

    lines = [
        "# OpenYield TIME Control Prototype State Machine Audit",
        "",
        "This is a metadata-only phase-transition audit for future default-off prototype builders.",
        "",
        "## Audit Summary",
        "",
        "```json",
        json.dumps(report["audit_summary"], ensure_ascii=False, indent=2),
        "```",
        "",
        "## Stage Chain",
        "",
        _md_table(
            ["stage", "next stage", "entry met", "next allowed", "physical gate open", "standalone gate open"],
            stage_rows,
        ),
        "",
        "## Transition Checks",
        "",
        _md_table(
            ["from", "to", "metadata-only transition", "forbidden auto-upgrade clean"],
            transition_rows,
        ),
        "",
        "## Global Guards",
        "",
        _md_table(["guard", "passed"], global_rows),
        "",
        "## Forbidden Auto-Upgrades",
        "",
        _md_table(["auto-upgrade", "allowed now", "blocked by"], auto_rows),
        "",
        "## Violations",
        "",
        "```json",
        json.dumps(report["violations"], ensure_ascii=False, indent=2),
        "```",
        "",
        "## Consistency Checks",
        "",
        _md_table(["check", "value"], consistency_rows),
        "",
        "## Notes",
        "",
    ]
    lines.extend(f"- {item}" for item in report["notes"])
    lines.append("")
    return "\n".join(lines)
