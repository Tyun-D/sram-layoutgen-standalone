"""Metadata-only payload completeness and consumption-contract audit for TIME/control.

This audit checks whether the current abstract payload is explicit enough for a
future default-off prototype builder to consume without guessing hidden fields.
It does not authorize physical placement, routing, or GDS generation.
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


def _missing_fields(item: dict[str, Any], required: list[str]) -> list[str]:
    missing: list[str] = []
    for field in required:
        if field not in item:
            missing.append(field)
            continue
        value = item[field]
        if value is None:
            missing.append(field)
        elif isinstance(value, (list, tuple, dict)) and len(value) == 0:
            missing.append(field)
        elif isinstance(value, str) and value == "":
            missing.append(field)
    return missing


def build_time_control_payload_completeness_report(
    *,
    openyield_root: str | Path,
    contracts_path: str | Path,
    tech_dir: str | Path,
) -> tuple[dict[str, Any], dict[str, Any]]:
    openyield_root = Path(openyield_root)
    contracts_path = Path(contracts_path)
    tech_dir = Path(tech_dir)

    payload_report = _load_json("docs/openyield_time_control_abstract_floorplan_payload_report.json")
    contract_report = _load_json("docs/openyield_time_control_experimental_contract_report.json")
    packing_report = _load_json("docs/openyield_time_control_packing_invariant_report.json")
    signal_report = _load_json("docs/openyield_time_control_signal_binding_report.json")
    consumer_report = _load_json("docs/openyield_time_control_consumer_contract_report.json")
    generated_logic_report = _load_json("docs/openyield_time_control_generated_logic_contract_report.json")

    payload = payload_report["payload"]
    signal_contracts = {item["contract_name"]: item for item in signal_report["signal_binding_contracts"]}
    consumer_contracts = {item["contract_name"]: item for item in consumer_report["consumer_side_contract_list"]}
    generated_logic_contracts = {
        item["contract_name"]: item for item in generated_logic_report["generated_logic_contract_list"]
    }

    config_required = [
        "flag_name",
        "default_enabled",
        "legacy_path_unchanged",
        "standalone_py_modified",
        "routing_modified",
        "gds_writer_modified",
        "physical_gds_generated",
    ]
    config_missing = _missing_fields(payload, config_required)

    region_required = [
        "region_name",
        "preferred_neighbor_regions",
        "required_channel_width",
        "reserved_channel_width",
        "budget_margin",
        "risk_level",
        "metadata_only",
        "legal_physical_placement",
    ]
    region_checks = []
    region_missing: dict[str, list[str]] = {}
    for item in payload["regions"]:
        missing = _missing_fields(item, region_required)
        region_checks.append(
            {
                "region_name": item["region_name"],
                "missing_fields": missing,
                "complete_for_metadata_consumer": not missing,
            }
        )
        if missing:
            region_missing[item["region_name"]] = missing

    subblock_required = [
        "subblock_name",
        "plan_kind",
        "assigned_region",
        "relative_order_group",
        "metadata_ready",
        "physical_ready",
        "requires_opt_in",
        "blocked_by",
    ]
    subblock_checks = []
    subblock_missing: dict[str, list[str]] = {}
    consumer_required_subblocks = {
        "PRECHARGE_HANDOFF",
        "SENSEAMP_HANDOFF",
        "WRITEDRIVER_HANDOFF",
        "WORDLINEDRIVER_HANDOFF",
        "DECODER_INTERFACE",
    }
    for item in payload["subblocks"]:
        missing = _missing_fields(item, subblock_required)
        if item["subblock_name"] in consumer_required_subblocks and item.get("consumer_target") in (None, ""):
            missing = missing + ["consumer_target"]
        subblock_checks.append(
            {
                "subblock_name": item["subblock_name"],
                "missing_fields": missing,
                "complete_for_metadata_consumer": not missing,
                "metadata_ready": item["metadata_ready"],
            }
        )
        if missing:
            subblock_missing[item["subblock_name"]] = missing

    handoff_required = [
        "interface_name",
        "source_regions",
        "target_macro",
        "control_signals",
        "metadata_ready",
        "physical_ready",
        "blocked_by",
    ]
    handoff_checks = []
    handoff_missing: dict[str, list[str]] = {}
    partial_handoffs: list[str] = []
    for item in payload["handoffs"]:
        missing = _missing_fields(item, handoff_required)
        handoff_checks.append(
            {
                "interface_name": item["interface_name"],
                "missing_fields": missing,
                "complete_for_metadata_consumer": not missing,
                "metadata_ready": item["metadata_ready"],
            }
        )
        if item["metadata_ready"] != True:
            partial_handoffs.append(item["interface_name"])
        if missing:
            handoff_missing[item["interface_name"]] = missing

    handoff_to_consumer_contract = {
        "TIME_CONTROL_TO_WRITEDRIVER_INTERFACE": "WRITE_ENABLE_CONSUMER_CONTRACT",
        "TIME_CONTROL_TO_SENSEAMP_INTERFACE": "SENSE_ENABLE_CONSUMER_CONTRACT",
        "TIME_CONTROL_TO_PRECHARGE_INTERFACE": "PRECHARGE_ENB_CONSUMER_CONTRACT",
        "TIME_CONTROL_TO_WORDLINEDRIVER_INTERFACE": "WORDLINE_ENABLE_CONSUMER_CONTRACT",
    }
    signal_name_to_binding = {
        item["signal_name"]: item["contract_name"] for item in signal_report["signal_binding_contracts"]
    }
    alias_to_binding = {
        alias: item["contract_name"]
        for item in signal_report["signal_binding_contracts"]
        for alias in item["aliases"]
    }

    handoff_traceability = []
    missing_handoff_traceability: list[str] = []
    for item in payload["handoffs"]:
        consumer_contract_name = handoff_to_consumer_contract.get(item["interface_name"])
        consumer_contract = consumer_contracts.get(consumer_contract_name) if consumer_contract_name else None
        binding_contracts = []
        generated_contract_refs = []
        for signal in item["control_signals"]:
            binding_name = signal_name_to_binding.get(signal) or alias_to_binding.get(signal)
            if binding_name:
                binding_contracts.append(binding_name)
                generated_contract_refs.extend(signal_contracts[binding_name]["candidate_generated_cells"])
        traceable = bool(consumer_contract_name and consumer_contract and binding_contracts)
        handoff_traceability.append(
            {
                "interface_name": item["interface_name"],
                "consumer_contract": consumer_contract_name,
                "binding_contracts": binding_contracts,
                "consumer_contract_found": consumer_contract is not None,
                "traceable": traceable,
            }
        )
        if not traceable:
            missing_handoff_traceability.append(item["interface_name"])

    subblock_to_generated_contracts = {
        "DELAY_CHAIN_CLUSTER": ["DELAY_CHAIN_GENERATED_LOGIC_CONTRACT"],
        "WEN_DELAY_CHAIN_CLUSTER": ["WEN_DELAY_CHAIN_CONDITIONAL_GENERATED_LOGIC_CONTRACT"],
        "PDRIVE_CLUSTER": [
            "PDRIVE_CHAIN_GENERATED_LOGIC_CONTRACT",
            "PDRIVE2_FOR_PRE_CHAIN_GENERATED_LOGIC_CONTRACT",
            "WL_PDRIVE_CHAIN_GENERATED_LOGIC_CONTRACT",
        ],
        "GENERATED_LOGIC_CLUSTER": [
            "PINV_GENERATED_LOGIC_CONTRACT",
            "AND2_GENERATED_LOGIC_CONTRACT",
            "AND3_COMPOSITE_GENERATED_LOGIC_CONTRACT",
            "PNAND3_COMPOSITE_GENERATED_LOGIC_CONTRACT",
        ],
    }
    subblock_traceability = []
    missing_subblock_traceability: list[str] = []
    for item in payload["subblocks"]:
        generated_refs = subblock_to_generated_contracts.get(item["subblock_name"], [])
        consumer_target = item.get("consumer_target")
        consumer_match = None
        if consumer_target:
            for contract in consumer_contracts.values():
                if contract["consumer_macro"] == consumer_target:
                    consumer_match = contract["contract_name"]
                    break
        traceable = bool(
            generated_refs
            or item["subblock_name"] in {"ADDR_DFF_ROW", "DATA_DFF_ROW", "DECODER_INTERFACE"}
            or consumer_match is not None
        )
        subblock_traceability.append(
            {
                "subblock_name": item["subblock_name"],
                "generated_logic_contracts": generated_refs,
                "consumer_contract": consumer_match,
                "traceable": traceable,
            }
        )
        if not traceable:
            missing_subblock_traceability.append(item["subblock_name"])

    generated_contract_presence = {
        name: name in generated_logic_contracts for names in subblock_to_generated_contracts.values() for name in names
    }
    consumer_contract_presence = {
        name: name in consumer_contracts for name in handoff_to_consumer_contract.values()
    }

    partial_status_explicit = all(
        item["metadata_ready"] != "partial" or "PRECHARGE" in item["interface_name"]
        for item in payload["handoffs"]
    )

    consumption_contract_complete_for_metadata = (
        not config_missing
        and not region_missing
        and not subblock_missing
        and not handoff_missing
        and not missing_handoff_traceability
        and not missing_subblock_traceability
        and all(generated_contract_presence.values())
        and all(consumer_contract_presence.values())
        and packing_report["consistency_checks"]["invariants_clean"]
        and partial_status_explicit
    )

    report = {
        "scope": "step6_34_openyield_time_control_payload_completeness_audit",
        "openyield_root": str(openyield_root.resolve()),
        "contracts_path": str(contracts_path.resolve()),
        "tech_dir": str(tech_dir.resolve()),
        "config_missing_fields": config_missing,
        "region_checks": region_checks,
        "subblock_checks": subblock_checks,
        "handoff_checks": handoff_checks,
        "handoff_traceability": handoff_traceability,
        "subblock_traceability": subblock_traceability,
        "generated_contract_presence": generated_contract_presence,
        "consumer_contract_presence": consumer_contract_presence,
        "partial_items": {
            "handoffs_marked_partial": partial_handoffs,
        },
        "violations": {
            "region_missing_fields": region_missing,
            "subblock_missing_fields": subblock_missing,
            "handoff_missing_fields": handoff_missing,
            "missing_handoff_traceability": missing_handoff_traceability,
            "missing_subblock_traceability": missing_subblock_traceability,
            "missing_generated_contracts": [name for name, present in generated_contract_presence.items() if not present],
            "missing_consumer_contracts": [name for name, present in consumer_contract_presence.items() if not present],
            "partial_status_not_explicit": not partial_status_explicit,
        },
        "consistency_checks": {
            "payload_completeness_audit_available": True,
            "config_surface_complete": not config_missing,
            "all_regions_complete_for_metadata_consumer": not region_missing,
            "all_subblocks_complete_for_metadata_consumer": not subblock_missing,
            "all_handoffs_complete_for_metadata_consumer": not handoff_missing,
            "handoff_traceability_complete": not missing_handoff_traceability,
            "subblock_traceability_complete": not missing_subblock_traceability,
            "generated_contract_references_present": all(generated_contract_presence.values()),
            "consumer_contract_references_present": all(consumer_contract_presence.values()),
            "packing_invariants_clean": packing_report["consistency_checks"]["invariants_clean"],
            "partial_status_explicit": partial_status_explicit,
            "consumption_contract_complete_for_metadata": consumption_contract_complete_for_metadata,
            "can_modify_standalone_now": False,
            "can_generate_time_control_gds_now": False,
            "can_enter_physical_placement_now": False,
        },
        "audit_summary": {
            "payload_completeness_audit_available": True,
            "config_surface_complete": not config_missing,
            "handoff_traceability_complete": not missing_handoff_traceability,
            "subblock_traceability_complete": not missing_subblock_traceability,
            "consumption_contract_complete_for_metadata": consumption_contract_complete_for_metadata,
            "partial_handoff_count": len(partial_handoffs),
            "can_modify_standalone_now": False,
            "can_generate_time_control_gds_now": False,
            "can_enter_physical_placement_now": False,
        },
        "notes": [
            "This audit checks whether a future default-off prototype builder would have enough explicit metadata to consume the payload without guessing.",
            "A complete metadata consumption contract does not imply legal placement, legal routing, timing closure, DRC, or LVS.",
            "Partial PRECHARGE status is allowed only when it is explicit and preserved as blocked metadata.",
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
            [{"id": item["subblock_name"], "kind": "subblock"} for item in subblock_traceability]
            + [{"id": item["interface_name"], "kind": "handoff"} for item in handoff_traceability]
            + [{"id": name, "kind": "consumer_contract"} for name in handoff_to_consumer_contract.values()]
        ),
        "edges": (
            [
                {
                    "source": item["interface_name"],
                    "target": item["consumer_contract"],
                    "relation": "consumes_via_contract",
                }
                for item in handoff_traceability
                if item["consumer_contract"]
            ]
            + [
                {
                    "source": item["subblock_name"],
                    "target": item["consumer_contract"],
                    "relation": "traceable_consumer",
                }
                for item in subblock_traceability
                if item["consumer_contract"]
            ]
        ),
        "summary": report["audit_summary"],
    }
    return report, graph


def build_time_control_payload_completeness_markdown(report: dict[str, Any]) -> str:
    region_rows = [
        [item["region_name"], ", ".join(item["missing_fields"]), item["complete_for_metadata_consumer"]]
        for item in report["region_checks"]
    ]
    subblock_rows = [
        [item["subblock_name"], ", ".join(item["missing_fields"]), item["metadata_ready"], item["complete_for_metadata_consumer"]]
        for item in report["subblock_checks"]
    ]
    handoff_rows = [
        [item["interface_name"], ", ".join(item["missing_fields"]), item["metadata_ready"], item["complete_for_metadata_consumer"]]
        for item in report["handoff_checks"]
    ]
    handoff_trace_rows = [
        [
            item["interface_name"],
            item["consumer_contract"] or "-",
            ", ".join(item["binding_contracts"]),
            item["consumer_contract_found"],
            item["traceable"],
        ]
        for item in report["handoff_traceability"]
    ]
    subblock_trace_rows = [
        [
            item["subblock_name"],
            ", ".join(item["generated_logic_contracts"]),
            item["consumer_contract"] or "-",
            item["traceable"],
        ]
        for item in report["subblock_traceability"]
    ]
    consistency_rows = [[key, value] for key, value in report["consistency_checks"].items()]

    lines = [
        "# OpenYield TIME Control Payload Completeness Audit",
        "",
        "This is a metadata-only consumption-contract audit. It checks whether the current payload is explicit enough for a future default-off prototype builder to consume without hidden assumptions.",
        "",
        "## Audit Summary",
        "",
        "```json",
        json.dumps(report["audit_summary"], ensure_ascii=False, indent=2),
        "```",
        "",
        "## Region Completeness",
        "",
        _md_table(["region", "missing fields", "complete"], region_rows),
        "",
        "## Subblock Completeness",
        "",
        _md_table(["subblock", "missing fields", "metadata ready", "complete"], subblock_rows),
        "",
        "## Handoff Completeness",
        "",
        _md_table(["handoff", "missing fields", "metadata ready", "complete"], handoff_rows),
        "",
        "## Handoff Traceability",
        "",
        _md_table(["handoff", "consumer contract", "binding contracts", "consumer found", "traceable"], handoff_trace_rows),
        "",
        "## Subblock Traceability",
        "",
        _md_table(["subblock", "generated logic contracts", "consumer contract", "traceable"], subblock_trace_rows),
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
