"""Metadata-only packing-order and adjacency invariant audit for TIME/control payloads."""

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


GROUP_ORDER = {
    "front_end_registers": 0,
    "timing_generation": 1,
    "generated_logic_core": 2,
    "consumer_handoff_boundary": 3,
    "decoder_boundary": 4,
}


def _bfs_path(
    start: str | None,
    goal: str | None,
    adjacency_pairs: set[tuple[str, str]],
    region_names: set[str],
) -> list[str] | None:
    if start is None or goal is None:
        return None
    if start == goal:
        return [start]
    visited = {start}
    queue: list[list[str]] = [[start]]
    while queue:
        path = queue.pop(0)
        node = path[-1]
        for neighbor in sorted(dst for src, dst in adjacency_pairs if src == node and dst in region_names):
            if neighbor in visited:
                continue
            next_path = path + [neighbor]
            if neighbor == goal:
                return next_path
            visited.add(neighbor)
            queue.append(next_path)
    return None


def build_time_control_packing_invariant_report(
    *,
    openyield_root: str | Path,
    contracts_path: str | Path,
    tech_dir: str | Path,
) -> tuple[dict[str, Any], dict[str, Any]]:
    openyield_root = Path(openyield_root)
    contracts_path = Path(contracts_path)
    tech_dir = Path(tech_dir)

    payload_report = _load_json("docs/openyield_time_control_abstract_floorplan_payload_report.json")
    region_refinement = _load_json("docs/openyield_time_control_region_refinement_report.json")
    contract_report = _load_json("docs/openyield_time_control_experimental_contract_report.json")

    payload = payload_report["payload"]
    regions = {item["region_name"]: item for item in payload["regions"]}
    subblocks = {item["subblock_name"]: item for item in payload["subblocks"]}
    handoffs = {item["interface_name"]: item for item in payload["handoffs"]}

    adjacency_pairs = set()
    for item in region_refinement["region_adjacency_handoff_planning"]:
        source = item["source_region"]
        target = item["target_region"]
        adjacency_pairs.add((source, target))
        adjacency_pairs.add((target, source))
    for name, item in regions.items():
        adjacency_pairs.add((name, name))
        for neighbor in item["preferred_neighbor_regions"]:
            adjacency_pairs.add((name, neighbor))

    group_presence = {group: False for group in GROUP_ORDER}
    group_sequence_rows: list[dict[str, Any]] = []
    group_order_violation_items: list[str] = []
    for item in payload["subblocks"]:
        group = item["relative_order_group"]
        group_presence[group] = True
        group_sequence_rows.append(
            {
                "subblock_name": item["subblock_name"],
                "group": group,
                "group_rank": GROUP_ORDER.get(group, 999),
                "assigned_region": item["assigned_region"],
            }
        )
        if group not in GROUP_ORDER:
            group_order_violation_items.append(f"unknown_group:{item['subblock_name']}:{group}")

    required_groups_present = all(group_presence.values())

    region_assignment_checks = []
    missing_region_assignments: list[str] = []
    for item in payload["subblocks"]:
        assigned_region = item["assigned_region"]
        ok = assigned_region in regions if assigned_region is not None else item["plan_kind"] == "decoder_boundary_reservation_only"
        region_assignment_checks.append(
            {
                "subblock_name": item["subblock_name"],
                "assigned_region": assigned_region,
                "region_exists": ok,
            }
        )
        if not ok:
            missing_region_assignments.append(item["subblock_name"])

    expected_handoff_map = {
        "PRECHARGE_HANDOFF": "TIME_CONTROL_TO_PRECHARGE_INTERFACE",
        "SENSEAMP_HANDOFF": "TIME_CONTROL_TO_SENSEAMP_INTERFACE",
        "WRITEDRIVER_HANDOFF": "TIME_CONTROL_TO_WRITEDRIVER_INTERFACE",
        "WORDLINEDRIVER_HANDOFF": "TIME_CONTROL_TO_WORDLINEDRIVER_INTERFACE",
    }
    handoff_alignment = []
    misaligned_handoffs: list[str] = []
    for subblock_name, interface_name in expected_handoff_map.items():
        subblock = subblocks[subblock_name]
        handoff = handoffs[interface_name]
        assigned_region = subblock["assigned_region"]
        aligned = assigned_region in handoff["source_regions"]
        handoff_alignment.append(
            {
                "subblock_name": subblock_name,
                "interface_name": interface_name,
                "assigned_region": assigned_region,
                "source_regions": handoff["source_regions"],
                "aligned": aligned,
            }
        )
        if not aligned:
            misaligned_handoffs.append(subblock_name)

    adjacency_invariants = []
    adjacency_violations: list[str] = []
    required_edges = [
        ("DELAY_CHAIN_CLUSTER", "GENERATED_LOGIC_CLUSTER"),
        ("PDRIVE_CLUSTER", "GENERATED_LOGIC_CLUSTER"),
        ("GENERATED_LOGIC_CLUSTER", "DECODER_INTERFACE"),
        ("GENERATED_LOGIC_CLUSTER", "PRECHARGE_HANDOFF"),
        ("GENERATED_LOGIC_CLUSTER", "WORDLINEDRIVER_HANDOFF"),
        ("SENSEAMP_HANDOFF", "WRITEDRIVER_HANDOFF"),
    ]
    for left_name, right_name in required_edges:
        left_region = subblocks[left_name]["assigned_region"]
        right_region = subblocks[right_name]["assigned_region"]
        path = _bfs_path(left_region, right_region, adjacency_pairs, set(regions))
        adjacent = path is not None
        adjacency_invariants.append(
            {
                "left": left_name,
                "right": right_name,
                "left_region": left_region,
                "right_region": right_region,
                "adjacent_or_reachable": adjacent,
                "metadata_path": path,
            }
        )
        if not adjacent:
            adjacency_violations.append(f"{left_name}->{right_name}")

    channel_margin_rows = []
    low_margin_regions: list[str] = []
    for item in payload["regions"]:
        margin = float(item["budget_margin"])
        channel_margin_rows.append(
            {
                "region_name": item["region_name"],
                "budget_margin": margin,
                "risk_level": item["risk_level"],
                "usable_for_metadata_ordering": margin >= 0,
            }
        )
        if margin < 0:
            low_margin_regions.append(item["region_name"])

    gate_consistency = {
        "default_enabled": payload["default_enabled"] is False and contract_report["config_surface"]["default_enabled"] is False,
        "legacy_path_unchanged": payload["legacy_path_unchanged"] is True and contract_report["config_surface"]["legacy_path_unchanged"] is True,
        "standalone_still_blocked": payload_report["can_modify_standalone_now"] is False and contract_report["can_modify_standalone_now"] is False,
        "gds_still_blocked": payload_report["can_generate_time_control_gds_now"] is False and contract_report["can_generate_time_control_gds_now"] is False,
        "physical_placement_still_blocked": payload_report["can_enter_physical_placement_now"] is False and contract_report["can_enter_physical_placement_now"] is False,
    }

    invariants_clean = (
        required_groups_present
        and not group_order_violation_items
        and not missing_region_assignments
        and not misaligned_handoffs
        and not adjacency_violations
        and not low_margin_regions
        and all(gate_consistency.values())
    )

    report = {
        "scope": "step6_33_openyield_time_control_packing_invariant_audit",
        "openyield_root": str(openyield_root.resolve()),
        "contracts_path": str(contracts_path.resolve()),
        "tech_dir": str(tech_dir.resolve()),
        "packing_group_presence": group_presence,
        "group_sequence_rows": group_sequence_rows,
        "region_assignment_checks": region_assignment_checks,
        "handoff_alignment": handoff_alignment,
        "adjacency_invariants": adjacency_invariants,
        "channel_margin_rows": channel_margin_rows,
        "gate_consistency": gate_consistency,
        "violations": {
            "group_order_violation_items": group_order_violation_items,
            "missing_region_assignments": missing_region_assignments,
            "misaligned_handoffs": misaligned_handoffs,
            "adjacency_violations": adjacency_violations,
            "negative_margin_regions": low_margin_regions,
        },
        "consistency_checks": {
            "packing_invariant_audit_available": True,
            "required_groups_present": required_groups_present,
            "all_subblocks_have_known_region_or_allowed_decoder_boundary": not missing_region_assignments,
            "consumer_handoff_regions_aligned": not misaligned_handoffs,
            "required_adjacency_invariants_hold": not adjacency_violations,
            "all_region_channel_margins_non_negative": not low_margin_regions,
            "default_enabled_still_false": gate_consistency["default_enabled"],
            "legacy_path_unchanged": gate_consistency["legacy_path_unchanged"],
            "standalone_still_blocked": gate_consistency["standalone_still_blocked"],
            "gds_still_blocked": gate_consistency["gds_still_blocked"],
            "physical_placement_still_blocked": gate_consistency["physical_placement_still_blocked"],
            "invariants_clean": invariants_clean,
        },
        "audit_summary": {
            "packing_invariant_audit_available": True,
            "required_groups_present": required_groups_present,
            "consumer_handoff_regions_aligned": not misaligned_handoffs,
            "required_adjacency_invariants_hold": not adjacency_violations,
            "all_region_channel_margins_non_negative": not low_margin_regions,
            "invariants_clean": invariants_clean,
            "can_modify_standalone_now": False,
            "can_generate_time_control_gds_now": False,
            "can_enter_physical_placement_now": False,
        },
        "notes": [
            "This audit checks internal consistency of the metadata payload only.",
            "Passing invariants does not prove legal placement, legal routing, timing closure, DRC, or LVS.",
            "The audit is intended to reduce future prototype ambiguity, not to reopen the physical gate.",
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
            [{"id": row["subblock_name"], "kind": "subblock"} for row in group_sequence_rows]
            + [{"id": item["region_name"], "kind": "region"} for item in payload["regions"]]
            + [{"id": item["interface_name"], "kind": "handoff"} for item in handoff_alignment]
        ),
        "edges": (
            [
                {
                    "source": row["subblock_name"],
                    "target": row["assigned_region"],
                    "relation": "assigned_region",
                }
                for row in group_sequence_rows
                if row["assigned_region"] is not None
            ]
            + [
                {
                    "source": item["subblock_name"],
                    "target": item["interface_name"],
                    "relation": "handoff_alignment",
                }
                for item in handoff_alignment
            ]
            + [
                {
                    "source": item["left"],
                    "target": item["right"],
                    "relation": "adjacency_invariant",
                }
                for item in adjacency_invariants
            ]
        ),
        "summary": report["audit_summary"],
    }
    return report, graph


def build_time_control_packing_invariant_markdown(report: dict[str, Any]) -> str:
    group_rows = [
        [group, present] for group, present in report["packing_group_presence"].items()
    ]
    region_rows = [
        [item["subblock_name"], item["assigned_region"], item["region_exists"]]
        for item in report["region_assignment_checks"]
    ]
    handoff_rows = [
        [
            item["subblock_name"],
            item["interface_name"],
            item["assigned_region"],
            ", ".join(item["source_regions"]),
            item["aligned"],
        ]
        for item in report["handoff_alignment"]
    ]
    adjacency_rows = [
        [
            item["left"],
            item["right"],
            item["left_region"],
            item["right_region"],
            " -> ".join(item["metadata_path"]) if item["metadata_path"] else "-",
            item["adjacent_or_reachable"],
        ]
        for item in report["adjacency_invariants"]
    ]
    margin_rows = [
        [item["region_name"], item["budget_margin"], item["risk_level"], item["usable_for_metadata_ordering"]]
        for item in report["channel_margin_rows"]
    ]
    consistency_rows = [[key, value] for key, value in report["consistency_checks"].items()]

    lines = [
        "# OpenYield TIME Control Packing Invariant Audit",
        "",
        "This is a metadata-only invariant audit over the Stage 6.32 payload. It does not prove legal placement, legal routing, timing closure, DRC, or LVS.",
        "",
        "## Audit Summary",
        "",
        "```json",
        json.dumps(report["audit_summary"], ensure_ascii=False, indent=2),
        "```",
        "",
        "## Packing Groups",
        "",
        _md_table(["group", "present"], group_rows),
        "",
        "## Region Assignment Checks",
        "",
        _md_table(["subblock", "assigned region", "region exists"], region_rows),
        "",
        "## Handoff Alignment",
        "",
        _md_table(["subblock", "interface", "assigned region", "source regions", "aligned"], handoff_rows),
        "",
        "## Adjacency Invariants",
        "",
        _md_table(["left", "right", "left region", "right region", "metadata path", "adjacent or reachable"], adjacency_rows),
        "",
        "## Channel Margins",
        "",
        _md_table(["region", "budget margin", "risk", "usable for metadata ordering"], margin_rows),
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
