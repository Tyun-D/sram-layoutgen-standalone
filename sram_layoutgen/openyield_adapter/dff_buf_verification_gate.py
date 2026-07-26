from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from sram_layoutgen.openyield_adapter.primitive_geometry_verifier import non_text_geometry_fingerprint


def compute_source_topology_hash_match(
    *,
    canonical_extracted_topology_hash: str,
    requested_source_topology_hash: str,
) -> bool:
    if not canonical_extracted_topology_hash or not isinstance(canonical_extracted_topology_hash, str):
        raise ValueError("canonical_extracted_topology_hash must be a non-empty string")
    if not requested_source_topology_hash or not isinstance(requested_source_topology_hash, str):
        raise ValueError("requested_source_topology_hash must be a non-empty string")
    return canonical_extracted_topology_hash == requested_source_topology_hash


def compute_child_geometry_immutability(records: list[dict[str, Any]]) -> dict[str, Any]:
    rows: list[dict[str, Any]] = []
    modified_count = 0
    for record in records:
        approved_digest = non_text_geometry_fingerprint(
            Path(record["approved_path"]),
            record["approved_top_name"],
        )["digest"]
        cloned_digest = non_text_geometry_fingerprint(
            Path(record["cloned_path"]),
            record["cloned_top_name"],
        )["digest"]
        hierarchy_digest = non_text_geometry_fingerprint(
            Path(record["hierarchy_path"]),
            record["hierarchy_top_name"],
        )["digest"]
        match = approved_digest == cloned_digest == hierarchy_digest
        if not match:
            modified_count += 1
        rows.append(
            {
                "instance": record["instance"],
                "approved_digest": approved_digest,
                "cloned_digest": cloned_digest,
                "hierarchy_digest": hierarchy_digest,
                "match": match,
            }
        )
    return {
        "rows": rows,
        "child_geometry_modified_count": modified_count,
    }


def compute_source_level_polarity_audit(instance_rows: list[dict[str, str]]) -> dict[str, Any]:
    pin_to_net = {(row["instance"], row["child_pin"]): row["parent_net"] for row in instance_rows}
    inverter_edges = []
    for row in instance_rows:
        if row["type"] == "PINV" and row["child_pin"] == "A":
            instance = row["instance"]
            src = row["parent_net"]
            dst = pin_to_net[(instance, "Z")]
            inverter_edges.append({"instance": instance, "input_net": src, "output_net": dst})
    edge_by_input = {edge["input_net"]: edge for edge in inverter_edges}
    path = []
    current = "qint"
    visited_inputs: set[str] = set()
    cycle_detected = False
    while current in edge_by_input:
        if current in visited_inputs:
            cycle_detected = True
            break
        visited_inputs.add(current)
        edge = edge_by_input[current]
        path.append(edge)
        current = edge["output_net"]
    qint_to_qb = len([edge for edge in path if edge["output_net"] == "QB"])
    qb_to_q = 1 if any(edge["input_net"] == "QB" and edge["output_net"] == "Q" for edge in path) else 0
    qint_to_q = len(path) if path and path[-1]["output_net"] == "Q" else None
    d_extra = any(edge["input_net"] == "D" for edge in inverter_edges)
    clk_extra = any(edge["input_net"] == "CLK" for edge in inverter_edges)
    passed = (
        qint_to_qb == 1
        and qb_to_q == 1
        and qint_to_q == 2
        and not d_extra
        and not clk_extra
        and len(path) == 2
        and path[0]["output_net"] == "QB"
        and path[1]["output_net"] == "Q"
        and not cycle_detected
    )
    return {
        "inverter_edges": inverter_edges,
        "path_from_qint": path,
        "cycle_detected": cycle_detected,
        "qint_to_qb_inverter_count": qint_to_qb,
        "qb_to_q_inverter_count": qb_to_q,
        "qint_to_q_inverter_count": qint_to_q,
        "final_q_same_polarity_as_dff_q": qint_to_q == 2,
        "final_qb_inverted_from_dff_q": qint_to_qb == 1,
        "d_has_no_parent_level_inverter": not d_extra,
        "clk_has_no_parent_level_inverter": not clk_extra,
        "source_level_functional_polarity_audit_passed": passed,
    }


def compute_logical_physical_structural_match(
    *,
    source_topology_hash_match: bool,
    exact_child_binding_count: int,
    non_exact_child_binding_count: int,
    child_geometry_modified_count: int,
    binding_rows: list[dict[str, Any]],
    expected_instance_order: list[str],
    expected_child_types: dict[str, str],
    connectivity: dict[str, Any],
    namespace_report: dict[str, Any],
    hierarchy_report: dict[str, Any],
) -> bool:
    instance_order_matches = [row["instance_name"] for row in binding_rows] == expected_instance_order
    instance_types_match = all(row["child_logical_module"] == expected_child_types[row["instance_name"]] for row in binding_rows)
    return (
        source_topology_hash_match
        and instance_order_matches
        and instance_types_match
        and exact_child_binding_count == len(expected_instance_order)
        and non_exact_child_binding_count == 0
        and child_geometry_modified_count == 0
        and connectivity["physical_connectivity_verification_passed"]
        and connectivity["unexpected_net_merge_count"] == 0
        and connectivity["missing_expected_endpoint_count"] == 0
        and connectivity["unexpected_endpoint_count"] == 0
        and namespace_report["top_canonical_label_set_exact"]
        and namespace_report["internal_child_label_leakage_count"] == 0
        and hierarchy_report["reference_closure_passed"]
        and hierarchy_report["missing_reference_target_count"] == 0
        and hierarchy_report["reference_cycle_count"] == 0
    )


def compute_machine_pass(gate_inputs: dict[str, Any]) -> bool:
    return (
        gate_inputs["source_commit_match"]
        and gate_inputs["source_topology_extraction_passed"]
        and gate_inputs["source_topology_hash_match"]
        and gate_inputs["exact_child_binding_count"] == 3
        and gate_inputs["non_exact_child_binding_count"] == 0
        and gate_inputs["child_geometry_modified_count"] == 0
        and gate_inputs["pin_access_planning_passed"]
        and gate_inputs["routing_architecture_has_no_same_layer_crossovers"]
        and gate_inputs["signal_routing_completed"]
        and gate_inputs["physical_connectivity_verification_passed"]
        and gate_inputs["logical_physical_structural_match"]
        and gate_inputs["top_canonical_label_set_exact"]
        and gate_inputs["child_label_leakage_count"] == 0
        and gate_inputs["hierarchy_closure_passed"]
        and gate_inputs["missing_reference_target_count"] == 0
        and gate_inputs["reference_cycle_count"] == 0
        and gate_inputs["drc_marker_count"] == 0
        and gate_inputs["deterministic_regeneration_verified"]
        and gate_inputs["source_level_functional_polarity_audit_passed"]
    )


def compute_machine_gate_outcome(machine_pass: bool) -> dict[str, Any]:
    if machine_pass:
        return {
            "human_review_required": True,
            "can_enter_next_stage_before_human_review": False,
            "recommended_next_stage": "Wave3 / DFF_BUF human visual review",
            "recommended_next_stage_reason": "Machine verification hardened successfully. The candidate now requires focused human visual review before any reusable or higher-wave claim.",
            "stage_status": "MACHINE_VERIFIED_CANDIDATE_PENDING_HUMAN_REVIEW",
            "can_claim_dff_buf_machine_verified": True,
            "can_claim_dff_buf_human_verified": False,
            "can_claim_dff_buf_reusable": False,
        }
    return {
        "human_review_required": False,
        "can_enter_next_stage_before_human_review": False,
        "recommended_next_stage": "Wave3 / DFF_BUF verification repair",
        "recommended_next_stage_reason": "Machine verification did not fully pass; repair is required before any human review or higher-wave progression.",
        "stage_status": "QUALIFICATION_FAILED_MACHINE",
        "can_claim_dff_buf_machine_verified": False,
        "can_claim_dff_buf_human_verified": False,
        "can_claim_dff_buf_reusable": False,
    }
