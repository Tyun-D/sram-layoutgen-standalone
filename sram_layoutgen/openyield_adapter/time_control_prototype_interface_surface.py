"""Interface-surface audit for future default-off TIME/control prototype builders.

This audit constrains the future builder's public surface to a minimal,
metadata-only interface. It checks allowed config fields, payload/report input
dependencies, and output artifact classes so that later implementation work
does not silently expand into standalone, routing, GDS, or physical flows.
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


def build_time_control_prototype_interface_surface_report(
    *,
    openyield_root: str | Path,
    contracts_path: str | Path,
    tech_dir: str | Path,
) -> tuple[dict[str, Any], dict[str, Any]]:
    openyield_root = Path(openyield_root)
    contracts_path = Path(contracts_path)
    tech_dir = Path(tech_dir)

    experimental_contract = _load_json("docs/openyield_time_control_experimental_contract_report.json")
    payload_report = _load_json("docs/openyield_time_control_abstract_floorplan_payload_report.json")
    completeness_report = _load_json("docs/openyield_time_control_payload_completeness_report.json")
    consumption_report = _load_json("docs/openyield_time_control_payload_consumption_contract_report.json")
    materialization_report = _load_json("docs/openyield_time_control_payload_materialization_boundary_report.json")
    execution_guard = _load_json("docs/openyield_time_control_prototype_execution_guard_report.json")
    state_machine = _load_json("docs/openyield_time_control_prototype_state_machine_report.json")

    config_surface = experimental_contract["config_surface"]
    payload = payload_report["payload"]

    allowed_config_fields = {
        "flag_name",
        "default_enabled",
        "allowed_mode",
        "legacy_path_unchanged",
        "standalone_py_modified",
        "routing_modified",
        "gds_writer_modified",
        "physical_gds_generated",
        "shared_rail_enabled",
        "uses_time_as_single_macro",
        "notes",
    }
    config_rows = []
    config_violations: list[str] = []
    for key, value in config_surface.items():
        allowed = key in allowed_config_fields
        metadata_only_ok = not (
            key in {"standalone_py_modified", "routing_modified", "gds_writer_modified", "physical_gds_generated", "shared_rail_enabled", "uses_time_as_single_macro"}
            and value is not False
        )
        config_rows.append(
            {
                "field_name": key,
                "allowed": allowed,
                "value": value,
                "metadata_only_ok": metadata_only_ok,
            }
        )
        if not (allowed and metadata_only_ok):
            config_violations.append(key)

    input_rows = [
        {
            "input_name": "experimental_contract.config_surface",
            "required": True,
            "metadata_only": True,
            "present": bool(config_surface),
        },
        {
            "input_name": "abstract_floorplan_payload.payload",
            "required": True,
            "metadata_only": True,
            "present": bool(payload),
        },
        {
            "input_name": "payload_completeness_report",
            "required": True,
            "metadata_only": True,
            "present": completeness_report["consistency_checks"]["consumption_contract_complete_for_metadata"],
        },
        {
            "input_name": "payload_consumption_contract_report",
            "required": True,
            "metadata_only": True,
            "present": consumption_report["consistency_checks"]["future_default_off_builder_can_consume_metadata"],
        },
        {
            "input_name": "payload_materialization_boundary_report",
            "required": True,
            "metadata_only": True,
            "present": materialization_report["consistency_checks"]["future_default_off_builder_can_materialize_metadata_plan"],
        },
        {
            "input_name": "prototype_execution_guard_report",
            "required": True,
            "metadata_only": True,
            "present": execution_guard["consistency_checks"]["future_default_off_builder_guardrails_clean"],
        },
        {
            "input_name": "prototype_state_machine_report",
            "required": True,
            "metadata_only": True,
            "present": state_machine["consistency_checks"]["future_default_off_builder_state_machine_clean"],
        },
    ]
    input_violations = [row["input_name"] for row in input_rows if row["required"] and not row["present"]]

    output_rows = [
        {
            "artifact_class": "metadata_plan_object",
            "allowed": True,
            "must_remain_nonphysical": True,
            "notes": "Abstract builder output may be an in-memory metadata plan only.",
        },
        {
            "artifact_class": "json_report",
            "allowed": True,
            "must_remain_nonphysical": True,
            "notes": "Audit/report outputs are allowed.",
        },
        {
            "artifact_class": "markdown_report",
            "allowed": True,
            "must_remain_nonphysical": True,
            "notes": "Human-readable audit outputs are allowed.",
        },
        {
            "artifact_class": "gds_layout",
            "allowed": False,
            "must_remain_nonphysical": True,
            "notes": "GDS generation remains forbidden.",
        },
        {
            "artifact_class": "routed_geometry",
            "allowed": False,
            "must_remain_nonphysical": True,
            "notes": "Routing geometry remains forbidden.",
        },
        {
            "artifact_class": "standalone_generator_patch",
            "allowed": False,
            "must_remain_nonphysical": True,
            "notes": "Main generator integration remains forbidden.",
        },
    ]
    output_violations = [row["artifact_class"] for row in output_rows if not row["allowed"] and not row["must_remain_nonphysical"]]

    payload_input_counts = {
        "region_count": len(payload["regions"]),
        "subblock_count": len(payload["subblocks"]),
        "handoff_count": len(payload["handoffs"]),
        "blocked_capability_count": len(payload["blocked_capabilities"]),
    }
    payload_surface_explicit = all(value > 0 for value in payload_input_counts.values())

    future_default_off_builder_interface_surface_clean = (
        not config_violations
        and not input_violations
        and not output_violations
        and payload_surface_explicit
        and config_surface["allowed_mode"] == "metadata_prototype_only"
        and config_surface["default_enabled"] is False
        and execution_guard["consistency_checks"]["future_default_off_builder_guardrails_clean"]
        and state_machine["consistency_checks"]["future_default_off_builder_state_machine_clean"]
    )

    report = {
        "scope": "step6_39_openyield_time_control_prototype_interface_surface_audit",
        "openyield_root": str(openyield_root.resolve()),
        "contracts_path": str(contracts_path.resolve()),
        "tech_dir": str(tech_dir.resolve()),
        "config_rows": config_rows,
        "input_rows": input_rows,
        "output_rows": output_rows,
        "payload_input_counts": payload_input_counts,
        "source_reports": {
            "experimental_contract": experimental_contract["scope"],
            "abstract_floorplan_payload": payload_report["scope"],
            "payload_completeness": completeness_report["scope"],
            "payload_consumption_contract": consumption_report["scope"],
            "payload_materialization_boundary": materialization_report["scope"],
            "prototype_execution_guard": execution_guard["scope"],
            "prototype_state_machine": state_machine["scope"],
        },
        "violations": {
            "config_violations": config_violations,
            "input_violations": input_violations,
            "output_violations": output_violations,
            "payload_surface_not_explicit": not payload_surface_explicit,
        },
        "consistency_checks": {
            "prototype_interface_surface_audit_available": True,
            "config_surface_restricted": not config_violations,
            "input_surface_restricted": not input_violations,
            "output_surface_restricted": not output_violations,
            "payload_surface_explicit": payload_surface_explicit,
            "metadata_only_mode_preserved": config_surface["allowed_mode"] == "metadata_prototype_only",
            "default_off_preserved": config_surface["default_enabled"] is False,
            "future_default_off_builder_interface_surface_clean": future_default_off_builder_interface_surface_clean,
            "can_modify_standalone_now": False,
            "can_generate_time_control_gds_now": False,
            "can_enter_physical_placement_now": False,
        },
        "audit_summary": {
            "prototype_interface_surface_audit_available": True,
            "config_surface_restricted": not config_violations,
            "input_surface_restricted": not input_violations,
            "output_surface_restricted": not output_violations,
            "future_default_off_builder_interface_surface_clean": future_default_off_builder_interface_surface_clean,
            "can_modify_standalone_now": False,
            "can_generate_time_control_gds_now": False,
            "can_enter_physical_placement_now": False,
        },
        "notes": [
            "This audit constrains the future builder's public interface to a minimal metadata-only surface.",
            "Passing this audit still does not authorize standalone integration, routing, GDS generation, or physical placement.",
            "The purpose is to keep future implementation scope narrow and explicit.",
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
            [{"id": row["field_name"], "kind": "config_field"} for row in config_rows]
            + [{"id": row["input_name"], "kind": "input"} for row in input_rows]
            + [{"id": row["artifact_class"], "kind": "output"} for row in output_rows]
        ),
        "edges": (
            [
                {
                    "source": "future_builder",
                    "target": row["field_name"],
                    "relation": "config_surface",
                }
                for row in config_rows
            ]
            + [
                {
                    "source": row["input_name"],
                    "target": "future_builder",
                    "relation": "required_input",
                }
                for row in input_rows
            ]
            + [
                {
                    "source": "future_builder",
                    "target": row["artifact_class"],
                    "relation": "allowed_output" if row["allowed"] else "forbidden_output",
                }
                for row in output_rows
            ]
        ),
        "summary": report["audit_summary"],
    }
    return report, graph


def build_time_control_prototype_interface_surface_markdown(report: dict[str, Any]) -> str:
    config_rows = [
        [row["field_name"], row["allowed"], row["value"], row["metadata_only_ok"]]
        for row in report["config_rows"]
    ]
    input_rows = [
        [row["input_name"], row["required"], row["metadata_only"], row["present"]]
        for row in report["input_rows"]
    ]
    output_rows = [
        [row["artifact_class"], row["allowed"], row["must_remain_nonphysical"], row["notes"]]
        for row in report["output_rows"]
    ]
    consistency_rows = [[key, value] for key, value in report["consistency_checks"].items()]

    lines = [
        "# OpenYield TIME Control Prototype Interface Surface Audit",
        "",
        "This is a metadata-only interface-surface audit for future default-off prototype builders.",
        "",
        "## Audit Summary",
        "",
        "```json",
        json.dumps(report["audit_summary"], ensure_ascii=False, indent=2),
        "```",
        "",
        "## Config Surface",
        "",
        _md_table(["field", "allowed", "value", "metadata-only ok"], config_rows),
        "",
        "## Required Inputs",
        "",
        _md_table(["input", "required", "metadata-only", "present"], input_rows),
        "",
        "## Output Surface",
        "",
        _md_table(["artifact", "allowed", "must remain nonphysical", "notes"], output_rows),
        "",
        "## Payload Input Counts",
        "",
        "```json",
        json.dumps(report["payload_input_counts"], ensure_ascii=False, indent=2),
        "```",
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
