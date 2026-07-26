"""Materialization-boundary audit for future default-off TIME/control builders.

This audit stays at the metadata-contract layer. It asks whether a future
default-off prototype builder can turn the existing payload into a deterministic
abstract materialization plan without inventing hidden tie-breakers, anchor
rules, or blocker-propagation rules. It does not authorize placement, routing,
standalone integration, or GDS generation.
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


def build_time_control_payload_materialization_boundary_report(
    *,
    openyield_root: str | Path,
    contracts_path: str | Path,
    tech_dir: str | Path,
) -> tuple[dict[str, Any], dict[str, Any]]:
    openyield_root = Path(openyield_root)
    contracts_path = Path(contracts_path)
    tech_dir = Path(tech_dir)

    payload_report = _load_json("docs/openyield_time_control_abstract_floorplan_payload_report.json")
    completeness_report = _load_json("docs/openyield_time_control_payload_completeness_report.json")
    consumption_report = _load_json("docs/openyield_time_control_payload_consumption_contract_report.json")
    packing_report = _load_json("docs/openyield_time_control_packing_invariant_report.json")
    readiness_report = _load_json("docs/openyield_time_control_placement_readiness_report.json")
    experimental_contract = _load_json("docs/openyield_time_control_experimental_contract_report.json")
    prototype_plan = _load_json("docs/openyield_time_control_opt_in_prototype_plan_report.json")

    payload = payload_report["payload"]
    subblocks = payload["subblocks"]
    regions = {item["region_name"]: item for item in payload["regions"]}
    handoffs = {item["interface_name"]: item for item in payload["handoffs"]}
    packing_rows = {item["subblock_name"]: item for item in packing_report["group_sequence_rows"]}
    experimental_rows = {item["subblock_name"]: item for item in experimental_contract["prototype_subplans"]}

    payload_order_index = {item["subblock_name"]: index for index, item in enumerate(subblocks)}
    group_materialization_rows = []
    group_materialization_violations: list[str] = []
    group_members: dict[str, list[dict[str, Any]]] = {}
    for item in subblocks:
        group_members.setdefault(item["relative_order_group"], []).append(item)

    for group_name, members in group_members.items():
        materialized_members = sorted(members, key=lambda item: payload_order_index[item["subblock_name"]])
        packing_rank = {packing_rows[item["subblock_name"]]["group_rank"] for item in members}
        rank_consistent = len(packing_rank) == 1
        row = {
            "group_name": group_name,
            "group_rank": sorted(packing_rank)[0] if packing_rank else None,
            "payload_order_sequence": [item["subblock_name"] for item in materialized_members],
            "member_count": len(materialized_members),
            "materializable_via_payload_order": True,
            "packing_rank_consistent": rank_consistent,
        }
        group_materialization_rows.append(row)
        if not rank_consistent:
            group_materialization_violations.append(group_name)

    region_anchor_rows = []
    region_anchor_violations: list[str] = []
    for name, item in regions.items():
        anchor_explicit = bool(item["preferred_neighbor_regions"]) and item["required_channel_width"] <= item["reserved_channel_width"]
        region_anchor_rows.append(
            {
                "region_name": name,
                "preferred_neighbor_regions": item["preferred_neighbor_regions"],
                "required_channel_width": item["required_channel_width"],
                "reserved_channel_width": item["reserved_channel_width"],
                "anchor_explicit": anchor_explicit,
            }
        )
        if not anchor_explicit:
            region_anchor_violations.append(name)

    handoff_anchor_rows = []
    handoff_anchor_violations: list[str] = []
    for interface_name, handoff in handoffs.items():
        matching_subblocks = [
            item for item in subblocks if item.get("consumer_target") == handoff["target_macro"]
        ]
        anchor_explicit = bool(
            matching_subblocks
            and handoff["source_regions"]
            and handoff.get("blocked_by")
        )
        handoff_anchor_rows.append(
            {
                "interface_name": interface_name,
                "target_macro": handoff["target_macro"],
                "source_regions": handoff["source_regions"],
                "matching_subblocks": [item["subblock_name"] for item in matching_subblocks],
                "metadata_ready": handoff["metadata_ready"],
                "anchor_explicit": anchor_explicit,
            }
        )
        if not anchor_explicit:
            handoff_anchor_violations.append(interface_name)

    blocker_rows = []
    blocker_violations: list[str] = []
    for item in subblocks:
        subblock_name = item["subblock_name"]
        experimental_match = experimental_rows.get(subblock_name)
        blocked_by = item.get("blocked_by", [])
        propagated = bool(
            blocked_by
            and experimental_match
            and experimental_match.get("blocked_by")
            and set(blocked_by).issubset(set(experimental_match["blocked_by"]))
        )
        blocker_rows.append(
            {
                "subblock_name": subblock_name,
                "payload_blocked_by": blocked_by,
                "experimental_blocked_by": experimental_match.get("blocked_by") if experimental_match else [],
                "propagation_explicit": propagated,
            }
        )
        if not propagated:
            blocker_violations.append(subblock_name)

    partial_precharge_propagation = bool(
        any(item["interface_name"] == "TIME_CONTROL_TO_PRECHARGE_INTERFACE" and item["metadata_ready"] == "partial" for item in payload["handoffs"])
        and any(item["interface_name"] == "TIME_CONTROL_TO_PRECHARGE_INTERFACE" and item["metadata_ready"] == "partial" for item in completeness_report["handoff_checks"])
        and consumption_report["consistency_checks"]["partial_precharge_preserved"]
    )

    prototype_guardrails = prototype_plan["prototype_contract"]
    builder_guardrails_explicit = bool(
        prototype_guardrails["allows_only_metadata_prototype"]
        and prototype_guardrails["default_enabled"] is False
        and prototype_guardrails["legacy_path_unchanged"] is True
        and prototype_guardrails["standalone_py_modified"] is False
        and prototype_guardrails["routing_modified"] is False
        and prototype_guardrails["gds_writer_modified"] is False
        and prototype_guardrails["physical_gds_generated"] is False
    )

    future_default_off_builder_can_materialize_metadata_plan = (
        completeness_report["consistency_checks"]["consumption_contract_complete_for_metadata"]
        and consumption_report["consistency_checks"]["future_default_off_builder_can_consume_metadata"]
        and not group_materialization_violations
        and not region_anchor_violations
        and not handoff_anchor_violations
        and not blocker_violations
        and partial_precharge_propagation
        and builder_guardrails_explicit
        and readiness_report["can_create_experimental_opt_in_placement_plan"]
    )

    report = {
        "scope": "step6_36_openyield_time_control_payload_materialization_boundary_audit",
        "openyield_root": str(openyield_root.resolve()),
        "contracts_path": str(contracts_path.resolve()),
        "tech_dir": str(tech_dir.resolve()),
        "group_materialization_rows": group_materialization_rows,
        "region_anchor_rows": region_anchor_rows,
        "handoff_anchor_rows": handoff_anchor_rows,
        "blocker_rows": blocker_rows,
        "source_reports": {
            "payload": payload_report["scope"],
            "payload_completeness": completeness_report["scope"],
            "payload_consumption_contract": consumption_report["scope"],
            "packing_invariants": packing_report["scope"],
            "placement_readiness": readiness_report["scope"],
            "experimental_contract": experimental_contract["scope"],
            "prototype_plan": prototype_plan["scope"],
        },
        "violations": {
            "group_materialization_violations": group_materialization_violations,
            "region_anchor_violations": region_anchor_violations,
            "handoff_anchor_violations": handoff_anchor_violations,
            "blocker_propagation_violations": blocker_violations,
        },
        "consistency_checks": {
            "payload_materialization_boundary_audit_available": True,
            "group_rank_deterministic": not group_materialization_violations,
            "intra_group_order_materialized": not group_materialization_violations,
            "region_anchor_rules_explicit": not region_anchor_violations,
            "handoff_anchor_rules_explicit": not handoff_anchor_violations,
            "partial_precharge_propagation_explicit": partial_precharge_propagation,
            "blocker_propagation_explicit": not blocker_violations,
            "builder_guardrails_explicit": builder_guardrails_explicit,
            "future_default_off_builder_can_materialize_metadata_plan": future_default_off_builder_can_materialize_metadata_plan,
            "can_modify_standalone_now": False,
            "can_generate_time_control_gds_now": False,
            "can_enter_physical_placement_now": False,
        },
        "audit_summary": {
            "payload_materialization_boundary_audit_available": True,
            "group_rank_deterministic": not group_materialization_violations,
            "region_anchor_rules_explicit": not region_anchor_violations,
            "handoff_anchor_rules_explicit": not handoff_anchor_violations,
            "partial_precharge_propagation_explicit": partial_precharge_propagation,
            "future_default_off_builder_can_materialize_metadata_plan": future_default_off_builder_can_materialize_metadata_plan,
            "can_modify_standalone_now": False,
            "can_generate_time_control_gds_now": False,
            "can_enter_physical_placement_now": False,
        },
        "notes": [
            "This audit asks whether a future default-off prototype builder can turn the current payload into a deterministic abstract materialization plan without inventing hidden tie-breakers or anchor rules.",
            "Passing this audit still does not prove legal placement, legal routing, timing closure, DRC, or LVS.",
            "Payload-order materialization is an abstract builder rule only and must not be misread as physical legalization.",
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
            [{"id": row["group_name"], "kind": "group"} for row in group_materialization_rows]
            + [{"id": row["region_name"], "kind": "region"} for row in region_anchor_rows]
            + [{"id": row["interface_name"], "kind": "handoff"} for row in handoff_anchor_rows]
        ),
        "edges": (
            [
                {
                    "source": item["relative_order_group"],
                    "target": item["subblock_name"],
                    "relation": "payload_order_member",
                    "payload_index": payload_order_index[item["subblock_name"]],
                }
                for item in subblocks
            ]
            + [
                {
                    "source": row["interface_name"],
                    "target": region_name,
                    "relation": "handoff_source_region",
                }
                for row in handoff_anchor_rows
                for region_name in row["source_regions"]
            ]
        ),
        "summary": report["audit_summary"],
    }
    return report, graph


def build_time_control_payload_materialization_boundary_markdown(report: dict[str, Any]) -> str:
    group_rows = [
        [
            row["group_name"],
            row["group_rank"],
            row["member_count"],
            row["payload_order_sequence"],
            row["materializable_via_payload_order"],
            row["packing_rank_consistent"],
        ]
        for row in report["group_materialization_rows"]
    ]
    region_rows = [
        [
            row["region_name"],
            row["preferred_neighbor_regions"],
            row["required_channel_width"],
            row["reserved_channel_width"],
            row["anchor_explicit"],
        ]
        for row in report["region_anchor_rows"]
    ]
    handoff_rows = [
        [
            row["interface_name"],
            row["target_macro"],
            row["source_regions"],
            row["matching_subblocks"],
            row["metadata_ready"],
            row["anchor_explicit"],
        ]
        for row in report["handoff_anchor_rows"]
    ]
    blocker_rows = [
        [
            row["subblock_name"],
            row["payload_blocked_by"],
            row["experimental_blocked_by"],
            row["propagation_explicit"],
        ]
        for row in report["blocker_rows"]
    ]
    consistency_rows = [[key, value] for key, value in report["consistency_checks"].items()]

    lines = [
        "# OpenYield TIME Control Payload Materialization Boundary Audit",
        "",
        "This is a metadata-only audit for future default-off prototype builders.",
        "",
        "## Audit Summary",
        "",
        "```json",
        json.dumps(report["audit_summary"], ensure_ascii=False, indent=2),
        "```",
        "",
        "## Group Materialization",
        "",
        _md_table(
            ["group", "group rank", "member count", "payload order sequence", "materializable", "rank consistent"],
            group_rows,
        ),
        "",
        "## Region Anchor Rules",
        "",
        _md_table(
            ["region", "preferred neighbors", "required width", "reserved width", "anchor explicit"],
            region_rows,
        ),
        "",
        "## Handoff Anchor Rules",
        "",
        _md_table(
            ["handoff", "target macro", "source regions", "matching subblocks", "metadata ready", "anchor explicit"],
            handoff_rows,
        ),
        "",
        "## Blocker Propagation",
        "",
        _md_table(
            ["subblock", "payload blocked_by", "experimental blocked_by", "propagation explicit"],
            blocker_rows,
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
