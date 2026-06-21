"""Read-only OpenYield TIME control metadata closure report."""

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


def build_time_control_metadata_closure_report(
    *,
    openyield_root: str | Path,
    contracts_path: str | Path,
    tech_dir: str | Path,
) -> tuple[dict[str, Any], dict[str, Any]]:
    openyield_root = Path(openyield_root)
    contracts_path = Path(contracts_path)
    tech_dir = Path(tech_dir)

    decomposition = _load_json("docs/openyield_time_control_decomposition_report.json")
    signal_bindings = _load_json("docs/openyield_time_control_signal_binding_report.json")
    generated_logic = _load_json("docs/openyield_time_control_generated_logic_contract_report.json")
    consumer_contracts = _load_json("docs/openyield_time_control_consumer_contract_report.json")
    fast_bundle = _load_json("docs/openyield_time_control_fast_bundle_report.json")
    precharge_constraints = _load_json("docs/openyield_time_control_precharge_constraints_bundle_report.json")
    region_refinement = _load_json("docs/openyield_time_control_region_refinement_report.json")
    closure_unblock = _load_json("docs/openyield_time_control_closure_unblock_report.json")

    decomposition_closed = bool(
        decomposition.get("time_decomposition_success")
        or decomposition.get("conclusions", {}).get("time_decomposition_success")
        or decomposition.get("can_enter_control_subblock_adapter_planning")
    )

    precharge_ground_class = closure_unblock["precharge_ground_semantics"]["precharge_ground_semantics_classification"]
    precharge_closure_status = (
        "intentional_no_local_gnd_metadata_exception"
        if precharge_ground_class == "intentional_no_local_gnd_metadata_exception"
        else "metadata_power_closed_rail_unproven"
        if precharge_ground_class == "explicit_gnd_found_power_metadata_closed_rail_unproven"
        else "retained_partial_blocker"
    )
    precharge_blocker_retained_if_any = (
        None
        if precharge_closure_status != "retained_partial_blocker"
        else "PRECHARGE local GND evidence remains unresolved"
    )

    time_control_metadata_closure_available = bool(
        closure_unblock["can_enter_time_control_metadata_closure"]
    )
    control_region_crossing_coverage_complete = bool(
        closure_unblock["crossing_coverage_summary"]["all_required_crossings_have_adjacency"]
        and closure_unblock["crossing_coverage_summary"]["all_required_crossings_have_handoff_or_reservation"]
        and closure_unblock["crossing_coverage_summary"]["all_crossing_budgets_pass"]
    )
    time_control_metadata_chain_complete = all(
        [
            decomposition_closed,
            signal_bindings.get("time_control_signal_binding_available", False),
            generated_logic.get("time_control_generated_logic_contract_available", False),
            consumer_contracts.get("time_control_consumer_contract_available", False),
            fast_bundle.get("consistency_checks", {}).get("time_control_fast_bundle_available", False),
            precharge_constraints.get("consistency_checks", {}).get("time_control_precharge_constraints_bundle_available", False),
            region_refinement.get("consistency_checks", {}).get("time_control_region_refinement_available", False),
            closure_unblock.get("closure_unblock_bundle_available", False),
        ]
    )
    can_enter_very_limited_abstract_to_placement_readiness = (
        time_control_metadata_closure_available
        and control_region_crossing_coverage_complete
        and precharge_ground_class != "conflicting_ground_metadata"
    )

    consistency_checks = {
        "time_control_metadata_closure_available": time_control_metadata_closure_available,
        "time_control_metadata_chain_complete": time_control_metadata_chain_complete,
        "time_control_decomposition_closed": decomposition_closed,
        "time_control_signal_bindings_closed": bool(signal_bindings.get("time_control_signal_binding_available", False)),
        "time_control_generated_logic_contracts_closed": bool(generated_logic.get("time_control_generated_logic_contract_available", False)),
        "time_control_consumer_contracts_closed": bool(consumer_contracts.get("time_control_consumer_contract_available", False)),
        "time_control_fast_bundle_closed": bool(fast_bundle.get("consistency_checks", {}).get("time_control_fast_bundle_available", False)),
        "time_control_precharge_constraints_closed": bool(precharge_constraints.get("consistency_checks", {}).get("time_control_precharge_constraints_bundle_available", False)),
        "time_control_region_refinement_closed": bool(region_refinement.get("consistency_checks", {}).get("time_control_region_refinement_available", False)),
        "time_control_closure_unblock_closed": bool(closure_unblock.get("closure_unblock_bundle_available", False)),
        "precharge_closure_status": precharge_closure_status,
        "control_region_crossing_coverage_complete": control_region_crossing_coverage_complete,
        "all_required_crossings_have_adjacency": bool(closure_unblock["crossing_coverage_summary"]["all_required_crossings_have_adjacency"]),
        "all_required_crossings_have_handoff_or_reservation": bool(closure_unblock["crossing_coverage_summary"]["all_required_crossings_have_handoff_or_reservation"]),
        "all_crossing_budgets_pass": bool(closure_unblock["crossing_coverage_summary"]["all_crossing_budgets_pass"]),
        "can_enter_very_limited_abstract_to_placement_readiness": can_enter_very_limited_abstract_to_placement_readiness,
        "can_enter_time_control_physical_placement": False,
        "can_enter_standalone_control_placement": False,
        "safe_for_metadata_planning": time_control_metadata_closure_available,
        "safe_for_physical_placement": False,
    }

    unresolved_items = [
        "PRECHARGE may still carry a retained metadata-only exception or power blocker.",
        "rail continuity proof is missing.",
        "routing proof is missing.",
        "delay timing proof is missing.",
        "wen-delay timing proof is missing.",
        "region refinement is not legal placement.",
        "crossing coverage is not legal routing.",
        "shared rail is disabled.",
        "no DRC/LVS proof exists.",
        "standalone integration remains blocked.",
    ]

    report = {
        "scope": "stage_b_openyield_time_control_metadata_closure",
        "openyield_root": str(openyield_root.resolve()),
        "contracts_path": str(contracts_path.resolve()),
        "tech_dir": str(tech_dir.resolve()),
        "source_reports": {
            "time_control_decomposition": decomposition.get("scope"),
            "time_control_signal_binding": signal_bindings.get("scope"),
            "time_control_generated_logic_contract": generated_logic.get("scope"),
            "time_control_consumer_contract": consumer_contracts.get("scope"),
            "time_control_fast_bundle": fast_bundle.get("scope"),
            "time_control_precharge_constraints": precharge_constraints.get("scope"),
            "time_control_region_refinement": region_refinement.get("scope"),
            "time_control_closure_unblock": closure_unblock.get("scope"),
        },
        "precharge_closure_status": precharge_closure_status,
        "precharge_blocker_retained_if_any": precharge_blocker_retained_if_any,
        "consistency_checks": consistency_checks,
        "unresolved_items": unresolved_items,
        "audit_summary": {
            "time_control_metadata_closure_available": time_control_metadata_closure_available,
            "time_control_metadata_chain_complete": time_control_metadata_chain_complete,
            "precharge_closure_status": precharge_closure_status,
            "control_region_crossing_coverage_complete": control_region_crossing_coverage_complete,
            "can_enter_very_limited_abstract_to_placement_readiness": can_enter_very_limited_abstract_to_placement_readiness,
            "can_enter_time_control_physical_placement": False,
            "can_enter_standalone_control_placement": False,
        },
        "can_enter_very_limited_abstract_to_placement_readiness": can_enter_very_limited_abstract_to_placement_readiness,
        "can_enter_time_control_physical_placement": False,
        "can_enter_standalone_control_placement": False,
        "standalone_modified": False,
        "routing_modified": False,
        "gds_writer_modified": False,
    }

    graph = {
        "scope": report["scope"],
        "nodes": [
            {"id": "TIME_CONTROL_DECOMPOSITION", "kind": "closure_input"},
            {"id": "TIME_CONTROL_SIGNAL_BINDINGS", "kind": "closure_input"},
            {"id": "TIME_CONTROL_GENERATED_LOGIC", "kind": "closure_input"},
            {"id": "TIME_CONTROL_CONSUMER_CONTRACTS", "kind": "closure_input"},
            {"id": "TIME_CONTROL_FAST_BUNDLE", "kind": "closure_input"},
            {"id": "TIME_CONTROL_PRECHARGE_CONSTRAINTS", "kind": "closure_input"},
            {"id": "TIME_CONTROL_REGION_REFINEMENT", "kind": "closure_input"},
            {"id": "TIME_CONTROL_CLOSURE_UNBLOCK", "kind": "closure_input"},
            {"id": "TIME_CONTROL_METADATA_CLOSURE", "kind": "closure_output"},
        ],
        "edges": [
            {"source": "TIME_CONTROL_DECOMPOSITION", "target": "TIME_CONTROL_METADATA_CLOSURE", "relation": "feeds"},
            {"source": "TIME_CONTROL_SIGNAL_BINDINGS", "target": "TIME_CONTROL_METADATA_CLOSURE", "relation": "feeds"},
            {"source": "TIME_CONTROL_GENERATED_LOGIC", "target": "TIME_CONTROL_METADATA_CLOSURE", "relation": "feeds"},
            {"source": "TIME_CONTROL_CONSUMER_CONTRACTS", "target": "TIME_CONTROL_METADATA_CLOSURE", "relation": "feeds"},
            {"source": "TIME_CONTROL_FAST_BUNDLE", "target": "TIME_CONTROL_METADATA_CLOSURE", "relation": "feeds"},
            {"source": "TIME_CONTROL_PRECHARGE_CONSTRAINTS", "target": "TIME_CONTROL_METADATA_CLOSURE", "relation": "feeds"},
            {"source": "TIME_CONTROL_REGION_REFINEMENT", "target": "TIME_CONTROL_METADATA_CLOSURE", "relation": "feeds"},
            {"source": "TIME_CONTROL_CLOSURE_UNBLOCK", "target": "TIME_CONTROL_METADATA_CLOSURE", "relation": "feeds"},
        ],
        "summary": report["audit_summary"],
    }
    return report, graph


def build_time_control_metadata_closure_markdown(report: dict[str, Any]) -> str:
    consistency_rows = [[key, value] for key, value in report["consistency_checks"].items()]
    lines = [
        "# OpenYield TIME Control Metadata Closure Report",
        "",
        "This is a metadata-planning closure report only. It does not prove legal routing, legal placement, timing closure, DRC, LVS, or physical readiness.",
        "",
        "## Audit Summary",
        "",
        "```json",
        json.dumps(report["audit_summary"], ensure_ascii=False, indent=2),
        "```",
        "",
        "## Closure State",
        "",
        "```json",
        json.dumps(
            {
                "precharge_closure_status": report["precharge_closure_status"],
                "precharge_blocker_retained_if_any": report["precharge_blocker_retained_if_any"],
            },
            ensure_ascii=False,
            indent=2,
        ),
        "```",
        "",
        "## Consistency Checks",
        "",
        _md_table(["check", "value"], consistency_rows),
        "",
        "## Unresolved Items",
        "",
    ]
    lines.extend(f"- {item}" for item in report["unresolved_items"])
    lines.extend(
        [
            "",
            "## Entry Decisions",
            "",
            f"- can_enter_very_limited_abstract_to_placement_readiness: `{report['can_enter_very_limited_abstract_to_placement_readiness']}`",
            f"- can_enter_time_control_physical_placement: `{report['can_enter_time_control_physical_placement']}`",
            f"- can_enter_standalone_control_placement: `{report['can_enter_standalone_control_placement']}`",
            "",
        ]
    )
    return "\n".join(lines)
