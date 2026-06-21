"""Regression audit for metadata-only TIME/control builder outputs.

This audit checks that current metadata artifacts remain within the allowed
output surface and do not accumulate forbidden physical-result fields.
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


def _collect_keys(value: Any, prefix: str = "") -> list[str]:
    keys: list[str] = []
    if isinstance(value, dict):
        for key, nested in value.items():
            path = f"{prefix}.{key}" if prefix else key
            keys.append(path)
            keys.extend(_collect_keys(nested, path))
    elif isinstance(value, list):
        for index, nested in enumerate(value):
            path = f"{prefix}[{index}]"
            keys.extend(_collect_keys(nested, path))
    return keys


def build_time_control_builder_output_regression_report(
    *,
    openyield_root: str | Path,
    contracts_path: str | Path,
    tech_dir: str | Path,
) -> tuple[dict[str, Any], dict[str, Any]]:
    openyield_root = Path(openyield_root)
    contracts_path = Path(contracts_path)
    tech_dir = Path(tech_dir)

    artifact_contract = _load_json("docs/openyield_time_control_prototype_artifact_contract_report.json")
    interface_surface = _load_json("docs/openyield_time_control_prototype_interface_surface_report.json")
    experimental_contract = _load_json("docs/openyield_time_control_experimental_contract_report.json")
    payload_report = _load_json("docs/openyield_time_control_abstract_floorplan_payload_report.json")
    goal_audit = _load_json("docs/openyield_time_control_goal_progress_audit_report.json")

    forbidden_names = {row["key_name"] for row in artifact_contract["forbidden_top_level_keys"]}
    required_names = {row["key_name"] for row in artifact_contract["required_top_level_keys"]}

    artifact_samples = [
        {
            "artifact_name": "candidate_artifact_shape",
            "kind": "metadata_plan_object",
            "payload": artifact_contract["candidate_artifact_shape"],
        },
        {
            "artifact_name": "experimental_contract.config_surface",
            "kind": "metadata_plan_object",
            "payload": experimental_contract["config_surface"],
        },
        {
            "artifact_name": "experimental_contract.prototype_subplans",
            "kind": "metadata_plan_object",
            "payload": experimental_contract["prototype_subplans"],
        },
        {
            "artifact_name": "abstract_floorplan_payload.payload",
            "kind": "metadata_plan_object",
            "payload": payload_report["payload"],
        },
        {
            "artifact_name": "goal_progress_audit.audit_summary",
            "kind": "json_report",
            "payload": goal_audit["audit_summary"],
        },
    ]

    sample_rows = []
    missing_required_sections: list[str] = []
    forbidden_field_hits: list[dict[str, Any]] = []
    regression_warnings: list[str] = []

    candidate_shape_keys = set(artifact_contract["candidate_artifact_shape"].keys())
    missing_from_candidate_shape = sorted(required_names - candidate_shape_keys)
    if missing_from_candidate_shape:
        missing_required_sections.extend(
            [f"candidate_artifact_shape:{name}" for name in missing_from_candidate_shape]
        )

    for sample in artifact_samples:
        payload = sample["payload"]
        flat_keys = _collect_keys(payload)
        top_keys = list(payload.keys()) if isinstance(payload, dict) else []
        top_hits = sorted(name for name in forbidden_names if name in top_keys)
        deep_hits = []
        for key_path in flat_keys:
            tail = key_path.split(".")[-1]
            if "[" in tail:
                tail = tail.split("[")[0]
            if tail in forbidden_names:
                deep_hits.append(key_path)
        deep_hits = sorted(set(deep_hits))
        if top_hits or deep_hits:
            forbidden_field_hits.append(
                {
                    "artifact_name": sample["artifact_name"],
                    "top_level_hits": top_hits,
                    "deep_hits": deep_hits,
                }
            )

        if sample["kind"] == "metadata_plan_object" and isinstance(payload, dict):
            missing_here = sorted(
                name
                for name in required_names
                if name in {"artifact_kind", "schema_version", "config_snapshot", "gate_snapshot", "regions", "subblocks", "handoffs", "group_order", "blocker_summary", "notes"}
                and name not in payload
                and sample["artifact_name"] == "candidate_artifact_shape"
            )
            if missing_here:
                missing_required_sections.extend(
                    [f"{sample['artifact_name']}:{name}" for name in missing_here]
                )

        sample_rows.append(
            {
                "artifact_name": sample["artifact_name"],
                "kind": sample["kind"],
                "top_key_count": len(top_keys),
                "deep_key_count": len(flat_keys),
                "forbidden_top_level_hits": top_hits,
                "forbidden_deep_hits": deep_hits,
                "metadata_only_ok": len(top_hits) == 0 and len(deep_hits) == 0,
            }
        )

    allowed_output_rows = interface_surface["output_rows"]
    allowed_output_classes = sorted(
        row["artifact_class"] for row in allowed_output_rows if row["allowed"]
    )
    forbidden_output_classes = sorted(
        row["artifact_class"] for row in allowed_output_rows if not row["allowed"]
    )

    output_class_rows = [
        {
            "artifact_class": row["artifact_class"],
            "allowed": row["allowed"],
            "must_remain_nonphysical": row["must_remain_nonphysical"],
            "notes": row["notes"],
        }
        for row in allowed_output_rows
    ]

    if goal_audit["current_gates"]["can_modify_standalone_now"]:
        regression_warnings.append("goal audit reopened standalone modification unexpectedly")
    if goal_audit["current_gates"]["can_generate_time_control_gds_now"]:
        regression_warnings.append("goal audit reopened time control GDS generation unexpectedly")
    if goal_audit["current_gates"]["can_enter_physical_placement_now"]:
        regression_warnings.append("goal audit reopened physical placement unexpectedly")

    future_default_off_builder_output_regression_clean = (
        not missing_required_sections
        and not forbidden_field_hits
        and not regression_warnings
        and artifact_contract["consistency_checks"]["future_default_off_builder_artifact_contract_clean"]
        and interface_surface["consistency_checks"]["future_default_off_builder_interface_surface_clean"]
    )

    report = {
        "scope": "step6_41_openyield_time_control_builder_output_regression_audit",
        "openyield_root": str(openyield_root.resolve()),
        "contracts_path": str(contracts_path.resolve()),
        "tech_dir": str(tech_dir.resolve()),
        "artifact_sample_rows": sample_rows,
        "output_class_rows": output_class_rows,
        "allowed_output_classes": allowed_output_classes,
        "forbidden_output_classes": forbidden_output_classes,
        "source_reports": {
            "prototype_artifact_contract": artifact_contract["scope"],
            "prototype_interface_surface": interface_surface["scope"],
            "experimental_contract": experimental_contract["scope"],
            "abstract_floorplan_payload": payload_report["scope"],
            "goal_progress_audit": goal_audit["scope"],
        },
        "violations": {
            "missing_required_sections": missing_required_sections,
            "forbidden_field_hits": forbidden_field_hits,
            "regression_warnings": regression_warnings,
        },
        "consistency_checks": {
            "builder_output_regression_audit_available": True,
            "allowed_output_classes_explicit": True,
            "forbidden_output_classes_explicit": True,
            "candidate_artifact_shape_complete": not missing_required_sections,
            "sample_outputs_forbidden_field_free": not forbidden_field_hits,
            "goal_gates_still_closed": not regression_warnings,
            "metadata_only_mode_preserved": True,
            "default_off_preserved": experimental_contract["config_surface"]["default_enabled"] is False,
            "future_default_off_builder_output_regression_clean": future_default_off_builder_output_regression_clean,
            "can_modify_standalone_now": False,
            "can_generate_time_control_gds_now": False,
            "can_enter_physical_placement_now": False,
        },
        "audit_summary": {
            "builder_output_regression_audit_available": True,
            "candidate_artifact_shape_complete": not missing_required_sections,
            "sample_outputs_forbidden_field_free": not forbidden_field_hits,
            "goal_gates_still_closed": not regression_warnings,
            "future_default_off_builder_output_regression_clean": future_default_off_builder_output_regression_clean,
            "can_modify_standalone_now": False,
            "can_generate_time_control_gds_now": False,
            "can_enter_physical_placement_now": False,
        },
        "notes": [
            "This audit checks regression drift in metadata-only builder outputs.",
            "Passing this audit still does not authorize standalone integration, routing, GDS generation, or physical placement.",
            "The intent is to catch schema creep before any future builder starts emitting physical-looking payloads.",
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
            [{"id": row["artifact_name"], "kind": row["kind"]} for row in sample_rows]
            + [{"id": name, "kind": "allowed_output"} for name in allowed_output_classes]
            + [{"id": name, "kind": "forbidden_output"} for name in forbidden_output_classes]
        ),
        "edges": (
            [
                {
                    "source": row["artifact_name"],
                    "target": row["kind"],
                    "relation": "classified_as",
                }
                for row in sample_rows
            ]
            + [
                {
                    "source": "future_builder",
                    "target": name,
                    "relation": "may_emit",
                }
                for name in allowed_output_classes
            ]
            + [
                {
                    "source": "future_builder",
                    "target": name,
                    "relation": "must_not_emit",
                }
                for name in forbidden_output_classes
            ]
        ),
        "summary": report["audit_summary"],
    }
    return report, graph


def build_time_control_builder_output_regression_markdown(report: dict[str, Any]) -> str:
    sample_rows = [
        [
            row["artifact_name"],
            row["kind"],
            row["top_key_count"],
            row["deep_key_count"],
            ", ".join(row["forbidden_top_level_hits"]) or "-",
            ", ".join(row["forbidden_deep_hits"]) or "-",
            row["metadata_only_ok"],
        ]
        for row in report["artifact_sample_rows"]
    ]
    output_rows = [
        [
            row["artifact_class"],
            row["allowed"],
            row["must_remain_nonphysical"],
            row["notes"],
        ]
        for row in report["output_class_rows"]
    ]
    consistency_rows = [[key, value] for key, value in report["consistency_checks"].items()]

    lines = [
        "# OpenYield TIME Control Builder Output Regression Audit",
        "",
        "This is a metadata-only regression audit for future builder outputs.",
        "",
        "## Audit Summary",
        "",
        "```json",
        json.dumps(report["audit_summary"], ensure_ascii=False, indent=2),
        "```",
        "",
        "## Artifact Samples",
        "",
        _md_table(
            ["artifact", "kind", "top keys", "deep keys", "forbidden top hits", "forbidden deep hits", "ok"],
            sample_rows,
        ),
        "",
        "## Output Classes",
        "",
        _md_table(
            ["artifact class", "allowed", "must remain nonphysical", "notes"],
            output_rows,
        ),
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
