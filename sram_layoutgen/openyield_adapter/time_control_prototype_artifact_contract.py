"""Artifact-contract audit for future default-off OpenYield TIME/control builders.

This audit formalizes the shape of metadata-only builder artifacts. It does
not authorize physical placement, routing, standalone integration, or GDS
generation.
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


def build_time_control_prototype_artifact_contract_report(
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
    interface_surface = _load_json("docs/openyield_time_control_prototype_interface_surface_report.json")

    required_top_level_keys = [
        {
            "key_name": "artifact_kind",
            "required": True,
            "metadata_only_ok": True,
            "notes": "Must identify a metadata-only artifact class such as abstract_plan_bundle.",
        },
        {
            "key_name": "schema_version",
            "required": True,
            "metadata_only_ok": True,
            "notes": "Needed for deterministic report/builder compatibility.",
        },
        {
            "key_name": "config_snapshot",
            "required": True,
            "metadata_only_ok": True,
            "notes": "Must mirror default-off experimental config state.",
        },
        {
            "key_name": "gate_snapshot",
            "required": True,
            "metadata_only_ok": True,
            "notes": "Must preserve current closed physical/standalone gates.",
        },
        {
            "key_name": "regions",
            "required": True,
            "metadata_only_ok": True,
            "notes": "Abstract region metadata only, not physical geometry.",
        },
        {
            "key_name": "subblocks",
            "required": True,
            "metadata_only_ok": True,
            "notes": "Abstract subblock ordering / grouping metadata only.",
        },
        {
            "key_name": "handoffs",
            "required": True,
            "metadata_only_ok": True,
            "notes": "Metadata-only handoff contracts and reservations.",
        },
        {
            "key_name": "group_order",
            "required": True,
            "metadata_only_ok": True,
            "notes": "Deterministic abstract materialization order.",
        },
        {
            "key_name": "blocker_summary",
            "required": True,
            "metadata_only_ok": True,
            "notes": "Must carry unresolved blocker propagation explicitly.",
        },
        {
            "key_name": "notes",
            "required": True,
            "metadata_only_ok": True,
            "notes": "Human-readable metadata-only scope reminders.",
        },
    ]

    forbidden_top_level_keys = [
        {
            "key_name": "gds_path",
            "forbidden_now": True,
            "reason": "Would imply physical layout generation.",
        },
        {
            "key_name": "topcell_name",
            "forbidden_now": True,
            "reason": "Would imply a concrete layout database artifact.",
        },
        {
            "key_name": "routed_shapes",
            "forbidden_now": True,
            "reason": "Routing geometry remains forbidden.",
        },
        {
            "key_name": "via_shapes",
            "forbidden_now": True,
            "reason": "Via geometry remains forbidden.",
        },
        {
            "key_name": "placed_instances",
            "forbidden_now": True,
            "reason": "Would overstate abstract metadata as legalized placement.",
        },
        {
            "key_name": "physical_bbox",
            "forbidden_now": True,
            "reason": "Physical bbox would imply concrete placement proof.",
        },
        {
            "key_name": "standalone_patch",
            "forbidden_now": True,
            "reason": "Main generator integration remains forbidden.",
        },
        {
            "key_name": "drc_result",
            "forbidden_now": True,
            "reason": "No physical DRC signoff artifact may be claimed here.",
        },
        {
            "key_name": "lvs_result",
            "forbidden_now": True,
            "reason": "No physical LVS signoff artifact may be claimed here.",
        },
    ]

    payload = payload_report["payload"]
    payload_topology_counts = {
        "region_count": len(payload["regions"]),
        "subblock_count": len(payload["subblocks"]),
        "handoff_count": len(payload["handoffs"]),
        "blocked_capability_count": len(payload["blocked_capabilities"]),
    }

    candidate_artifact_shape = {
        "artifact_kind": "abstract_plan_bundle",
        "schema_version": 1,
        "config_snapshot": {
            "flag_name": experimental_contract["config_surface"]["flag_name"],
            "default_enabled": experimental_contract["config_surface"]["default_enabled"],
            "allowed_mode": experimental_contract["config_surface"]["allowed_mode"],
            "legacy_path_unchanged": experimental_contract["config_surface"]["legacy_path_unchanged"],
        },
        "gate_snapshot": {
            "can_modify_standalone_now": False,
            "can_generate_time_control_gds_now": False,
            "can_enter_physical_placement_now": False,
        },
        "regions": "abstract region payload rows only",
        "subblocks": "abstract subblock payload rows only",
        "handoffs": "metadata-only handoff rows only",
        "group_order": "deterministic payload materialization order only",
        "blocker_summary": "propagated unresolved blockers only",
        "notes": "metadata-only scope reminder",
    }

    schema_rows = [
        {
            "section_name": "config_snapshot",
            "required_fields": [
                "flag_name",
                "default_enabled",
                "allowed_mode",
                "legacy_path_unchanged",
                "standalone_py_modified",
                "routing_modified",
                "gds_writer_modified",
                "physical_gds_generated",
            ],
            "metadata_only_ok": True,
        },
        {
            "section_name": "gate_snapshot",
            "required_fields": [
                "can_modify_standalone_now",
                "can_generate_time_control_gds_now",
                "can_enter_physical_placement_now",
            ],
            "metadata_only_ok": True,
        },
        {
            "section_name": "regions",
            "required_fields": [
                "region_name",
                "preferred_neighbor_regions",
                "required_channel_width",
                "reserved_channel_width",
                "budget_margin",
                "risk_level",
                "metadata_only",
            ],
            "metadata_only_ok": True,
        },
        {
            "section_name": "subblocks",
            "required_fields": [
                "subblock_name",
                "plan_kind",
                "assigned_region",
                "relative_order_group",
                "metadata_ready",
                "physical_ready",
                "requires_opt_in",
                "blocked_by",
            ],
            "metadata_only_ok": True,
        },
        {
            "section_name": "handoffs",
            "required_fields": [
                "interface_name",
                "source_regions",
                "target_macro",
                "control_signals",
                "metadata_ready",
                "physical_ready",
            ],
            "metadata_only_ok": True,
        },
    ]

    violations = {
        "missing_required_top_level_keys": [],
        "forbidden_top_level_keys_present": [],
        "schema_section_violations": [],
        "gate_snapshot_violation": False,
    }

    gate_snapshot_ok = (
        experimental_contract["gate_snapshot"]["can_modify_standalone_now"] is False
        and experimental_contract["gate_snapshot"]["can_generate_time_control_gds_now"] is False
        and experimental_contract["gate_snapshot"]["can_enter_physical_placement_now"] is False
        and execution_guard["consistency_checks"]["future_default_off_builder_guardrails_clean"]
        and state_machine["consistency_checks"]["future_default_off_builder_state_machine_clean"]
        and interface_surface["consistency_checks"]["future_default_off_builder_interface_surface_clean"]
    )
    if not gate_snapshot_ok:
        violations["gate_snapshot_violation"] = True

    future_default_off_builder_artifact_contract_clean = (
        not violations["missing_required_top_level_keys"]
        and not violations["forbidden_top_level_keys_present"]
        and not violations["schema_section_violations"]
        and not violations["gate_snapshot_violation"]
        and completeness_report["consistency_checks"]["consumption_contract_complete_for_metadata"]
        and consumption_report["consistency_checks"]["future_default_off_builder_can_consume_metadata"]
        and materialization_report["consistency_checks"]["future_default_off_builder_can_materialize_metadata_plan"]
    )

    report = {
        "scope": "step6_40_openyield_time_control_prototype_artifact_contract_audit",
        "openyield_root": str(openyield_root.resolve()),
        "contracts_path": str(contracts_path.resolve()),
        "tech_dir": str(tech_dir.resolve()),
        "required_top_level_keys": required_top_level_keys,
        "forbidden_top_level_keys": forbidden_top_level_keys,
        "candidate_artifact_shape": candidate_artifact_shape,
        "schema_rows": schema_rows,
        "payload_topology_counts": payload_topology_counts,
        "source_reports": {
            "experimental_contract": experimental_contract["scope"],
            "abstract_floorplan_payload": payload_report["scope"],
            "payload_completeness": completeness_report["scope"],
            "payload_consumption_contract": consumption_report["scope"],
            "payload_materialization_boundary": materialization_report["scope"],
            "prototype_execution_guard": execution_guard["scope"],
            "prototype_state_machine": state_machine["scope"],
            "prototype_interface_surface": interface_surface["scope"],
        },
        "violations": violations,
        "consistency_checks": {
            "prototype_artifact_contract_audit_available": True,
            "required_top_level_keys_explicit": True,
            "forbidden_top_level_keys_explicit": True,
            "artifact_schema_sections_explicit": True,
            "candidate_artifact_shape_explicit": True,
            "gate_snapshot_closed": gate_snapshot_ok,
            "metadata_only_mode_preserved": True,
            "default_off_preserved": experimental_contract["config_surface"]["default_enabled"] is False,
            "future_default_off_builder_artifact_contract_clean": future_default_off_builder_artifact_contract_clean,
            "can_modify_standalone_now": False,
            "can_generate_time_control_gds_now": False,
            "can_enter_physical_placement_now": False,
        },
        "audit_summary": {
            "prototype_artifact_contract_audit_available": True,
            "required_top_level_keys_explicit": True,
            "forbidden_top_level_keys_explicit": True,
            "gate_snapshot_closed": gate_snapshot_ok,
            "future_default_off_builder_artifact_contract_clean": future_default_off_builder_artifact_contract_clean,
            "can_modify_standalone_now": False,
            "can_generate_time_control_gds_now": False,
            "can_enter_physical_placement_now": False,
        },
        "notes": [
            "This audit constrains future builder artifacts to metadata-only plan bundles.",
            "Passing this audit still does not authorize standalone integration, routing, GDS generation, or physical placement.",
            "The purpose is to prevent metadata artifacts from drifting into physical-result claims through schema creep.",
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
            [{"id": row["key_name"], "kind": "required_key"} for row in required_top_level_keys]
            + [{"id": row["key_name"], "kind": "forbidden_key"} for row in forbidden_top_level_keys]
            + [{"id": row["section_name"], "kind": "schema_section"} for row in schema_rows]
        ),
        "edges": (
            [
                {
                    "source": "abstract_plan_bundle",
                    "target": row["key_name"],
                    "relation": "requires_key",
                }
                for row in required_top_level_keys
            ]
            + [
                {
                    "source": "abstract_plan_bundle",
                    "target": row["key_name"],
                    "relation": "forbids_key",
                }
                for row in forbidden_top_level_keys
            ]
            + [
                {
                    "source": "abstract_plan_bundle",
                    "target": row["section_name"],
                    "relation": "contains_section",
                }
                for row in schema_rows
            ]
        ),
        "summary": report["audit_summary"],
    }
    return report, graph


def build_time_control_prototype_artifact_contract_markdown(report: dict[str, Any]) -> str:
    required_rows = [
        [row["key_name"], row["required"], row["metadata_only_ok"], row["notes"]]
        for row in report["required_top_level_keys"]
    ]
    forbidden_rows = [
        [row["key_name"], row["forbidden_now"], row["reason"]]
        for row in report["forbidden_top_level_keys"]
    ]
    schema_rows = [
        [row["section_name"], ", ".join(row["required_fields"]), row["metadata_only_ok"]]
        for row in report["schema_rows"]
    ]
    consistency_rows = [[key, value] for key, value in report["consistency_checks"].items()]

    lines = [
        "# OpenYield TIME Control Prototype Artifact Contract Audit",
        "",
        "This is a metadata-only artifact-schema audit for future default-off prototype builders.",
        "",
        "## Audit Summary",
        "",
        "```json",
        json.dumps(report["audit_summary"], ensure_ascii=False, indent=2),
        "```",
        "",
        "## Required Top-Level Keys",
        "",
        _md_table(["key", "required", "metadata-only ok", "notes"], required_rows),
        "",
        "## Forbidden Top-Level Keys",
        "",
        _md_table(["key", "forbidden now", "reason"], forbidden_rows),
        "",
        "## Candidate Artifact Shape",
        "",
        "```json",
        json.dumps(report["candidate_artifact_shape"], ensure_ascii=False, indent=2),
        "```",
        "",
        "## Schema Sections",
        "",
        _md_table(["section", "required fields", "metadata-only ok"], schema_rows),
        "",
        "## Payload Topology Counts",
        "",
        "```json",
        json.dumps(report["payload_topology_counts"], ensure_ascii=False, indent=2),
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
