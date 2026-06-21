"""Deterministic metadata-consumption audit for future TIME/control prototype builders.

This stays strictly at the metadata-consumption layer. It checks whether a
future default-off prototype builder can consume the existing payload and
prototype-plan artifacts without hidden identifier, ordering, or endpoint
guesswork. It does not authorize standalone integration, routing, placement,
or GDS generation.
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


def _duplicates(items: list[str]) -> list[str]:
    seen: set[str] = set()
    dupes: set[str] = set()
    for item in items:
        if item in seen:
            dupes.add(item)
        seen.add(item)
    return sorted(dupes)


def build_time_control_payload_consumption_contract_report(
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
    packing_report = _load_json("docs/openyield_time_control_packing_invariant_report.json")
    experimental_contract = _load_json("docs/openyield_time_control_experimental_contract_report.json")
    prototype_plan = _load_json("docs/openyield_time_control_opt_in_prototype_plan_report.json")
    signal_report = _load_json("docs/openyield_time_control_signal_binding_report.json")
    consumer_report = _load_json("docs/openyield_time_control_consumer_contract_report.json")
    readiness_report = _load_json("docs/openyield_time_control_placement_readiness_report.json")

    payload = payload_report["payload"]
    region_names = [item["region_name"] for item in payload["regions"]]
    subblock_names = [item["subblock_name"] for item in payload["subblocks"]]
    handoff_names = [item["interface_name"] for item in payload["handoffs"]]

    region_dupes = _duplicates(region_names)
    subblock_dupes = _duplicates(subblock_names)
    handoff_dupes = _duplicates(handoff_names)
    identifier_uniqueness_clean = not (region_dupes or subblock_dupes or handoff_dupes)

    known_regions = set(region_names)
    signal_bindings = signal_report["signal_binding_contracts"]
    consumer_contracts = {
        item["consumer_macro"]: item["contract_name"] for item in consumer_report["consumer_side_contract_list"]
    }
    canonical_signals = {
        item["signal_name"]: item["contract_name"] for item in signal_bindings
    }
    alias_signals = {
        alias: item["contract_name"] for item in signal_bindings for alias in item["aliases"]
    }
    dependency_targets = {
        edge["target"] for edge in signal_report["dependency_graph"]["edges"] if edge.get("dependency_confirmed")
    }
    secondary_signal_bindings: dict[str, list[str]] = {}
    for item in signal_bindings:
        searchable_text = " ".join(
            [item["producer_expression_or_dependency"], *item.get("consumer_pins", []), *item.get("notes", [])]
        )
        for target in dependency_targets:
            if target in canonical_signals or target in alias_signals:
                continue
            if target in searchable_text:
                secondary_signal_bindings.setdefault(target, []).append(item["contract_name"])

    region_reference_rows = []
    region_reference_violations: list[str] = []
    for item in payload["regions"]:
        bad_neighbors = [name for name in item["preferred_neighbor_regions"] if name not in known_regions]
        row = {
            "region_name": item["region_name"],
            "bad_preferred_neighbors": bad_neighbors,
            "neighbors_all_known": not bad_neighbors,
        }
        region_reference_rows.append(row)
        if bad_neighbors:
            region_reference_violations.append(item["region_name"])

    subblock_rows = []
    subblock_region_violations: list[str] = []
    subblock_blocker_violations: list[str] = []
    subblock_plan_alignment_violations: list[str] = []
    experimental_subplans = {
        item["subblock_name"]: item for item in experimental_contract["prototype_subplans"]
    }
    candidate_interfaces = {item["name"]: item for item in prototype_plan["candidate_interfaces"]}
    packing_rows = {item["subblock_name"]: item for item in packing_report["group_sequence_rows"]}
    for item in payload["subblocks"]:
        assigned_region = item["assigned_region"]
        region_exists = assigned_region in known_regions
        blockers_explicit = bool(item.get("blocked_by"))
        experimental_match = experimental_subplans.get(item["subblock_name"])
        candidate_match = candidate_interfaces.get(item["subblock_name"])
        packing_match = packing_rows.get(item["subblock_name"])
        experimental_plan_aligned = bool(
            experimental_match
            and packing_match
            and experimental_match["region_name"] == assigned_region
            and packing_match["assigned_region"] == assigned_region
        )
        candidate_interface_aligned = (
            None
            if candidate_match is None
            else candidate_match["future_plan_kind"] == item["plan_kind"]
        )
        subblock_rows.append(
            {
                "subblock_name": item["subblock_name"],
                "assigned_region": assigned_region,
                "region_exists": region_exists,
                "blocked_by_explicit": blockers_explicit,
                "relative_order_group": item["relative_order_group"],
                "group_rank": packing_match["group_rank"] if packing_match else None,
                "consumer_target": item.get("consumer_target"),
                "experimental_plan_aligned": experimental_plan_aligned,
                "candidate_interface_aligned": candidate_interface_aligned,
            }
        )
        if not region_exists:
            subblock_region_violations.append(item["subblock_name"])
        if not blockers_explicit:
            subblock_blocker_violations.append(item["subblock_name"])
        if not experimental_plan_aligned:
            subblock_plan_alignment_violations.append(item["subblock_name"])
        if candidate_interface_aligned is False:
            subblock_plan_alignment_violations.append(f"{item['subblock_name']}:candidate_interface")

    handoff_rows = []
    handoff_region_violations: list[str] = []
    handoff_signal_violations: list[str] = []
    handoff_consumer_violations: list[str] = []
    partial_precharge_preserved = True
    payload_subblock_targets = {
        item["subblock_name"]: item.get("consumer_target") for item in payload["subblocks"]
    }
    for item in payload["handoffs"]:
        bad_regions = [name for name in item["source_regions"] if name not in known_regions]
        binding_contracts = []
        unresolved_signals = []
        for signal in item["control_signals"]:
            binding = canonical_signals.get(signal) or alias_signals.get(signal)
            if binding:
                binding_contracts.append(binding)
                continue
            secondary_bindings = secondary_signal_bindings.get(signal, [])
            if secondary_bindings:
                binding_contracts.extend(
                    [f"{name}:derived_secondary_signal" for name in secondary_bindings]
                )
            else:
                unresolved_signals.append(signal)
        matching_subblock = next(
            (
                subblock_name
                for subblock_name, consumer_target in payload_subblock_targets.items()
                if consumer_target == item["target_macro"]
            ),
            None,
        )
        consumer_contract = consumer_contracts.get(item["target_macro"])
        consumer_explicit = matching_subblock is not None and consumer_contract is not None
        if item["interface_name"] == "TIME_CONTROL_TO_PRECHARGE_INTERFACE":
            partial_precharge_preserved = partial_precharge_preserved and item["metadata_ready"] == "partial"
        handoff_rows.append(
            {
                "interface_name": item["interface_name"],
                "target_macro": item["target_macro"],
                "source_regions_all_known": not bad_regions,
                "binding_contracts": binding_contracts,
                "unresolved_signals": unresolved_signals,
                "matching_subblock": matching_subblock,
                "consumer_contract": consumer_contract,
                "metadata_ready": item["metadata_ready"],
                "blocked_by_explicit": bool(item.get("blocked_by")),
                "consumer_explicit": consumer_explicit,
            }
        )
        if bad_regions:
            handoff_region_violations.append(item["interface_name"])
        if unresolved_signals:
            handoff_signal_violations.append(item["interface_name"])
        if not consumer_explicit:
            handoff_consumer_violations.append(item["interface_name"])
        if not item.get("blocked_by"):
            handoff_consumer_violations.append(f"{item['interface_name']}:missing_blocked_by")

    group_rows = []
    group_order_violations: list[str] = []
    groups_seen: dict[str, set[int]] = {}
    for row in packing_report["group_sequence_rows"]:
        groups_seen.setdefault(row["group"], set()).add(row["group_rank"])
    for group, ranks in sorted(groups_seen.items()):
        deterministic = len(ranks) == 1
        rank = sorted(ranks)[0] if ranks else None
        group_rows.append(
            {
                "relative_order_group": group,
                "group_rank_values": sorted(ranks),
                "deterministic_rank": deterministic,
                "rank": rank,
            }
        )
        if not deterministic:
            group_order_violations.append(group)

    future_default_off_builder_can_consume_metadata = (
        completeness_report["consistency_checks"]["consumption_contract_complete_for_metadata"]
        and identifier_uniqueness_clean
        and not region_reference_violations
        and not subblock_region_violations
        and not subblock_blocker_violations
        and not subblock_plan_alignment_violations
        and not handoff_region_violations
        and not handoff_signal_violations
        and not handoff_consumer_violations
        and not group_order_violations
        and partial_precharge_preserved
        and not payload["default_enabled"]
        and payload["legacy_path_unchanged"]
        and not payload["standalone_py_modified"]
        and not payload["routing_modified"]
        and not payload["gds_writer_modified"]
        and not payload["physical_gds_generated"]
    )

    report = {
        "scope": "step6_35_openyield_time_control_payload_consumption_contract_audit",
        "openyield_root": str(openyield_root.resolve()),
        "contracts_path": str(contracts_path.resolve()),
        "tech_dir": str(tech_dir.resolve()),
        "identifier_audit": {
            "region_duplicates": region_dupes,
            "subblock_duplicates": subblock_dupes,
            "handoff_duplicates": handoff_dupes,
        },
        "region_reference_rows": region_reference_rows,
        "subblock_rows": subblock_rows,
        "handoff_rows": handoff_rows,
        "group_order_rows": group_rows,
        "violations": {
            "region_reference_violations": region_reference_violations,
            "subblock_region_violations": subblock_region_violations,
            "subblock_blocker_violations": subblock_blocker_violations,
            "subblock_plan_alignment_violations": subblock_plan_alignment_violations,
            "handoff_region_violations": handoff_region_violations,
            "handoff_signal_violations": handoff_signal_violations,
            "handoff_consumer_violations": handoff_consumer_violations,
            "group_order_violations": group_order_violations,
        },
        "source_reports": {
            "payload": payload_report["scope"],
            "payload_completeness": completeness_report["scope"],
            "packing_invariants": packing_report["scope"],
            "experimental_contract": experimental_contract["scope"],
            "prototype_plan": prototype_plan["scope"],
            "placement_readiness": readiness_report["scope"],
            "signal_bindings": signal_report["scope"],
            "consumer_contracts": consumer_report["scope"],
        },
        "consistency_checks": {
            "payload_consumption_contract_available": True,
            "consumption_contract_complete_for_metadata": completeness_report["consistency_checks"][
                "consumption_contract_complete_for_metadata"
            ],
            "identifier_uniqueness_clean": identifier_uniqueness_clean,
            "region_reference_clean": not region_reference_violations,
            "subblock_region_assignment_clean": not subblock_region_violations,
            "subblock_blockers_explicit": not subblock_blocker_violations,
            "subblock_plan_alignment_clean": not subblock_plan_alignment_violations,
            "handoff_region_reference_clean": not handoff_region_violations,
            "handoff_signal_binding_clean": not handoff_signal_violations,
            "handoff_consumer_endpoint_explicit": not handoff_consumer_violations,
            "group_order_materializable": not group_order_violations,
            "partial_precharge_preserved": partial_precharge_preserved,
            "default_off_still_preserved": not payload["default_enabled"],
            "legacy_path_unchanged": payload["legacy_path_unchanged"],
            "standalone_still_unmodified": not payload["standalone_py_modified"],
            "routing_still_unmodified": not payload["routing_modified"],
            "gds_writer_still_unmodified": not payload["gds_writer_modified"],
            "physical_gds_still_not_generated": not payload["physical_gds_generated"],
            "future_default_off_builder_can_consume_metadata": future_default_off_builder_can_consume_metadata,
            "can_modify_standalone_now": False,
            "can_generate_time_control_gds_now": False,
            "can_enter_physical_placement_now": False,
        },
        "audit_summary": {
            "payload_consumption_contract_available": True,
            "identifier_uniqueness_clean": identifier_uniqueness_clean,
            "group_order_materializable": not group_order_violations,
            "partial_precharge_preserved": partial_precharge_preserved,
            "future_default_off_builder_can_consume_metadata": future_default_off_builder_can_consume_metadata,
            "can_modify_standalone_now": False,
            "can_generate_time_control_gds_now": False,
            "can_enter_physical_placement_now": False,
        },
        "notes": [
            "This audit checks whether a future default-off prototype builder can consume the current payload deterministically without hidden identifier, region, or endpoint assumptions.",
            "Passing this audit still does not prove legal placement, legal routing, timing closure, DRC, or LVS.",
            "PRECHARGE may remain partial, but that partial status must stay explicit and must not be silently upgraded.",
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
            [{"id": item["region_name"], "kind": "region"} for item in payload["regions"]]
            + [{"id": item["subblock_name"], "kind": "subblock"} for item in payload["subblocks"]]
            + [{"id": item["interface_name"], "kind": "handoff"} for item in payload["handoffs"]]
        ),
        "edges": (
            [
                {
                    "source": item["subblock_name"],
                    "target": item["assigned_region"],
                    "relation": "assigned_region",
                }
                for item in payload["subblocks"]
            ]
            + [
                {
                    "source": item["interface_name"],
                    "target": region,
                    "relation": "source_region",
                }
                for item in payload["handoffs"]
                for region in item["source_regions"]
            ]
            + [
                {
                    "source": item["interface_name"],
                    "target": item["target_macro"],
                    "relation": "consumer_target_macro",
                }
                for item in payload["handoffs"]
            ]
        ),
        "summary": report["audit_summary"],
    }
    return report, graph


def build_time_control_payload_consumption_contract_markdown(report: dict[str, Any]) -> str:
    region_rows = [
        [item["region_name"], ", ".join(item["bad_preferred_neighbors"]), item["neighbors_all_known"]]
        for item in report["region_reference_rows"]
    ]
    subblock_rows = [
        [
            item["subblock_name"],
            item["assigned_region"],
            item["region_exists"],
            item["relative_order_group"],
            item["group_rank"],
            item["consumer_target"] or "-",
            item["blocked_by_explicit"],
            item["experimental_plan_aligned"],
            item["candidate_interface_aligned"],
        ]
        for item in report["subblock_rows"]
    ]
    handoff_rows = [
        [
            item["interface_name"],
            item["target_macro"],
            ", ".join(item["binding_contracts"]),
            ", ".join(item["unresolved_signals"]),
            item["matching_subblock"] or "-",
            item["consumer_contract"] or "-",
            item["metadata_ready"],
            item["consumer_explicit"],
        ]
        for item in report["handoff_rows"]
    ]
    group_rows = [
        [
            item["relative_order_group"],
            item["group_rank_values"],
            item["deterministic_rank"],
            item["rank"],
        ]
        for item in report["group_order_rows"]
    ]
    consistency_rows = [[key, value] for key, value in report["consistency_checks"].items()]

    lines = [
        "# OpenYield TIME Control Payload Consumption Contract Audit",
        "",
        "This is a metadata-only determinism audit for future default-off prototype builders.",
        "",
        "## Audit Summary",
        "",
        "```json",
        json.dumps(report["audit_summary"], ensure_ascii=False, indent=2),
        "```",
        "",
        "## Region Reference Audit",
        "",
        _md_table(["region", "bad preferred neighbors", "neighbors all known"], region_rows),
        "",
        "## Subblock Consumption Rows",
        "",
        _md_table(
            [
                "subblock",
                "assigned region",
                "region exists",
                "group",
                "group rank",
                "consumer target",
                "blocked_by explicit",
                "experimental aligned",
                "candidate aligned",
            ],
            subblock_rows,
        ),
        "",
        "## Handoff Consumption Rows",
        "",
        _md_table(
            [
                "handoff",
                "target macro",
                "binding contracts",
                "unresolved signals",
                "matching subblock",
                "consumer contract",
                "metadata ready",
                "consumer explicit",
            ],
            handoff_rows,
        ),
        "",
        "## Group Ordering",
        "",
        _md_table(["group", "rank values", "deterministic rank", "rank"], group_rows),
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
