"""Execution-guard audit for future default-off TIME/control prototype builders.

This audit formalizes the non-physical execution boundary for any future
default-off prototype builder. It confirms that current metadata artifacts only
authorize abstract planning actions and explicitly forbid standalone
integration, routing, GDS generation, rail merge, and physical legalization.
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


def build_time_control_prototype_execution_guard_report(
    *,
    openyield_root: str | Path,
    contracts_path: str | Path,
    tech_dir: str | Path,
) -> tuple[dict[str, Any], dict[str, Any]]:
    openyield_root = Path(openyield_root)
    contracts_path = Path(contracts_path)
    tech_dir = Path(tech_dir)

    prototype_plan = _load_json("docs/openyield_time_control_opt_in_prototype_plan_report.json")
    experimental_contract = _load_json("docs/openyield_time_control_experimental_contract_report.json")
    payload_report = _load_json("docs/openyield_time_control_abstract_floorplan_payload_report.json")
    completeness_report = _load_json("docs/openyield_time_control_payload_completeness_report.json")
    consumption_report = _load_json("docs/openyield_time_control_payload_consumption_contract_report.json")
    materialization_report = _load_json("docs/openyield_time_control_payload_materialization_boundary_report.json")
    readiness_report = _load_json("docs/openyield_time_control_placement_readiness_report.json")

    prototype_contract = prototype_plan["prototype_contract"]
    config_surface = experimental_contract["config_surface"]
    payload_gate_snapshot = payload_report["payload"]["gate_snapshot"]

    guard_rows = []
    allowed_rows = []
    violations: list[str] = []

    guard_expectations = [
        ("default_enabled_false", prototype_contract["default_enabled"] is False and config_surface["default_enabled"] is False),
        ("legacy_path_unchanged", prototype_contract["legacy_path_unchanged"] is True and config_surface["legacy_path_unchanged"] is True),
        ("standalone_unmodified", prototype_contract["standalone_py_modified"] is False and config_surface["standalone_py_modified"] is False),
        ("routing_unmodified", prototype_contract["routing_modified"] is False and config_surface["routing_modified"] is False),
        ("gds_writer_unmodified", prototype_contract["gds_writer_modified"] is False and config_surface["gds_writer_modified"] is False),
        ("physical_gds_not_generated", prototype_contract["physical_gds_generated"] is False and config_surface["physical_gds_generated"] is False),
        ("shared_rail_disabled", prototype_contract["shared_rail_enabled"] is False and config_surface["shared_rail_enabled"] is False),
        ("time_not_single_macro", prototype_contract["uses_time_as_single_macro"] is False and config_surface["uses_time_as_single_macro"] is False),
        ("metadata_only_mode", prototype_contract["allows_only_metadata_prototype"] is True and config_surface["allowed_mode"] == "metadata_prototype_only"),
        ("cannot_modify_standalone_now", readiness_report["can_modify_standalone"] is False and payload_gate_snapshot["can_modify_standalone_now"] is False),
        ("cannot_generate_gds_now", readiness_report["can_generate_time_control_gds"] is False and payload_gate_snapshot["can_generate_time_control_gds_now"] is False),
        ("cannot_enter_physical_now", readiness_report["can_enter_physical_placement"] is False and payload_gate_snapshot["can_enter_physical_placement_now"] is False),
    ]
    for name, passed in guard_expectations:
        guard_rows.append({"guard_name": name, "passed": passed})
        if not passed:
            violations.append(name)

    allowed_keywords = {
        "metadata plan objects",
        "abstract region packing",
        "metadata-only consumer handoff reservations",
        "future spec/config surface only",
    }
    forbidden_keywords = {
        "standalone.py",
        "routing",
        "gds writer",
        "physical placement",
        "GDS generation",
        "real routed wires",
        "sense/write/WL physical rewiring",
        "shared rail",
        "current turn integration",
    }
    phased_step_violations: list[str] = []
    for step in prototype_plan["phased_steps"]:
        allowed_set = set(step["touches"])
        forbidden_set = set(step["forbidden"])
        allowed_ok = step["allowed"] in (True, False)
        forbidden_explicit = forbidden_set.issubset(forbidden_keywords) and len(forbidden_set) > 0
        touch_scope_known = all(item in allowed_keywords or "standalone.py only after a later gate" in item for item in allowed_set)
        default_off_preserved = step["default_enabled"] is False
        row = {
            "step_name": step["step_name"],
            "allowed": step["allowed"],
            "default_enabled": step["default_enabled"],
            "touches": step["touches"],
            "forbidden": step["forbidden"],
            "forbidden_explicit": forbidden_explicit,
            "touch_scope_known": touch_scope_known,
            "default_off_preserved": default_off_preserved,
        }
        allowed_rows.append(row)
        if not (allowed_ok and forbidden_explicit and touch_scope_known and default_off_preserved):
            phased_step_violations.append(step["step_name"])

    capability_rows = []
    allowed_capabilities = set(experimental_contract["allowed_capabilities"])
    blocked_capabilities = set(experimental_contract["blocked_capabilities"])
    capability_pairs = [
        ("default-off config surfacing", True),
        ("abstract row/region metadata packing", True),
        ("consumer handoff reservation modeling", True),
        ("future gate bookkeeping", True),
        ("standalone integration", False),
        ("physical TIME/control placement", False),
        ("TIME/control GDS generation", False),
        ("legal routing proof", False),
        ("rail continuity proof", False),
        ("shared rail enablement", False),
    ]
    capability_violations: list[str] = []
    for capability, should_be_allowed in capability_pairs:
        present = capability in (allowed_capabilities if should_be_allowed else blocked_capabilities)
        capability_rows.append(
            {
                "capability": capability,
                "should_be_allowed": should_be_allowed,
                "present": present,
            }
        )
        if not present:
            capability_violations.append(capability)

    residual_risk_explicit = (
        "A complete metadata consumption contract does not imply legal placement, legal routing, timing closure, DRC, or LVS."
        in completeness_report["notes"]
        and "Passing this audit still does not prove legal placement, legal routing, timing closure, DRC, or LVS."
        in consumption_report["notes"]
        and "Passing this audit still does not prove legal placement, legal routing, timing closure, DRC, or LVS."
        in materialization_report["notes"]
    )

    future_default_off_builder_guardrails_clean = (
        not violations
        and not phased_step_violations
        and not capability_violations
        and residual_risk_explicit
        and consumption_report["consistency_checks"]["future_default_off_builder_can_consume_metadata"]
        and materialization_report["consistency_checks"]["future_default_off_builder_can_materialize_metadata_plan"]
    )

    report = {
        "scope": "step6_37_openyield_time_control_prototype_execution_guard_audit",
        "openyield_root": str(openyield_root.resolve()),
        "contracts_path": str(contracts_path.resolve()),
        "tech_dir": str(tech_dir.resolve()),
        "guard_rows": guard_rows,
        "phased_step_rows": allowed_rows,
        "capability_rows": capability_rows,
        "source_reports": {
            "prototype_plan": prototype_plan["scope"],
            "experimental_contract": experimental_contract["scope"],
            "payload": payload_report["scope"],
            "payload_completeness": completeness_report["scope"],
            "payload_consumption_contract": consumption_report["scope"],
            "payload_materialization_boundary": materialization_report["scope"],
            "placement_readiness": readiness_report["scope"],
        },
        "violations": {
            "guard_violations": violations,
            "phased_step_violations": phased_step_violations,
            "capability_violations": capability_violations,
            "residual_risk_note_missing": not residual_risk_explicit,
        },
        "consistency_checks": {
            "prototype_execution_guard_audit_available": True,
            "default_off_preserved": not prototype_contract["default_enabled"],
            "standalone_guard_explicit": prototype_contract["standalone_py_modified"] is False,
            "routing_guard_explicit": prototype_contract["routing_modified"] is False,
            "gds_writer_guard_explicit": prototype_contract["gds_writer_modified"] is False,
            "physical_gds_guard_explicit": prototype_contract["physical_gds_generated"] is False,
            "shared_rail_guard_explicit": prototype_contract["shared_rail_enabled"] is False,
            "time_macro_guard_explicit": prototype_contract["uses_time_as_single_macro"] is False,
            "phased_step_guards_explicit": not phased_step_violations,
            "blocked_capabilities_explicit": not capability_violations,
            "residual_risk_notes_explicit": residual_risk_explicit,
            "future_default_off_builder_guardrails_clean": future_default_off_builder_guardrails_clean,
            "can_modify_standalone_now": False,
            "can_generate_time_control_gds_now": False,
            "can_enter_physical_placement_now": False,
        },
        "audit_summary": {
            "prototype_execution_guard_audit_available": True,
            "default_off_preserved": not prototype_contract["default_enabled"],
            "phased_step_guards_explicit": not phased_step_violations,
            "blocked_capabilities_explicit": not capability_violations,
            "future_default_off_builder_guardrails_clean": future_default_off_builder_guardrails_clean,
            "can_modify_standalone_now": False,
            "can_generate_time_control_gds_now": False,
            "can_enter_physical_placement_now": False,
        },
        "notes": [
            "This audit formalizes which actions a future default-off prototype builder may and may not perform.",
            "Passing this audit still does not authorize standalone integration, routing, GDS generation, or physical placement.",
            "The purpose is to make non-physical execution boundaries explicit before any builder implementation begins.",
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
            [{"id": row["guard_name"], "kind": "guard"} for row in guard_rows]
            + [{"id": row["step_name"], "kind": "phased_step"} for row in allowed_rows]
            + [{"id": row["capability"], "kind": "capability"} for row in capability_rows]
        ),
        "edges": (
            [
                {
                    "source": row["step_name"],
                    "target": item,
                    "relation": "forbidden_action",
                }
                for row in allowed_rows
                for item in row["forbidden"]
            ]
            + [
                {
                    "source": row["step_name"],
                    "target": item,
                    "relation": "allowed_touch_scope",
                }
                for row in allowed_rows
                for item in row["touches"]
            ]
        ),
        "summary": report["audit_summary"],
    }
    return report, graph


def build_time_control_prototype_execution_guard_markdown(report: dict[str, Any]) -> str:
    guard_rows = [[row["guard_name"], row["passed"]] for row in report["guard_rows"]]
    phased_rows = [
        [
            row["step_name"],
            row["allowed"],
            row["default_enabled"],
            row["touches"],
            row["forbidden"],
            row["forbidden_explicit"],
            row["touch_scope_known"],
        ]
        for row in report["phased_step_rows"]
    ]
    capability_rows = [
        [row["capability"], row["should_be_allowed"], row["present"]] for row in report["capability_rows"]
    ]
    consistency_rows = [[key, value] for key, value in report["consistency_checks"].items()]

    lines = [
        "# OpenYield TIME Control Prototype Execution Guard Audit",
        "",
        "This is a metadata-only guardrail audit for future default-off prototype builders.",
        "",
        "## Audit Summary",
        "",
        "```json",
        json.dumps(report["audit_summary"], ensure_ascii=False, indent=2),
        "```",
        "",
        "## Guard Checks",
        "",
        _md_table(["guard", "passed"], guard_rows),
        "",
        "## Phased Step Guardrails",
        "",
        _md_table(
            ["step", "allowed", "default off", "touches", "forbidden", "forbidden explicit", "touch scope known"],
            phased_rows,
        ),
        "",
        "## Capability Boundary",
        "",
        _md_table(["capability", "should be allowed", "present"], capability_rows),
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
