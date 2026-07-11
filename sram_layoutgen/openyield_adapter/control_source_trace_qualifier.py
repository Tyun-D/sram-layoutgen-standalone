from __future__ import annotations

from pathlib import Path
from typing import Any


QUAL_FIELDS = [
    "logical_module",
    "candidate_cell_name",
    "candidate_gds_path",
    "expected_source_class",
    "source_trace_complete",
    "parameter_trace_complete",
    "gds_parsed",
    "expected_cell_found",
    "bbox_valid",
    "real_non_debug_geometry",
    "pin_set_match",
    "pin_geometry_complete",
    "power_rail_geometry_complete",
    "obvious_hierarchy_or_connectivity_failure",
    "physical_strategy",
    "qualification_status",
    "blocking_reason",
    "allowed_use",
]

SOURCE_TRACE_FIELDS = [
    "logical_module",
    "candidate_gds_path",
    "generation_report_path",
    "generator_manifest_path",
    "generation_status",
    "generation_strategy",
    "source_trace_complete",
    "parameter_trace_complete",
    "source_trace_note",
]

CONNECTIVITY_FIELDS = [
    "logical_module",
    "candidate_gds_path",
    "top_cell_name",
    "top_cell_has_direct_geometry",
    "top_cell_reference_count",
    "expected_child_module_multiset",
    "candidate_child_cell_multiset",
    "obvious_hierarchy_or_connectivity_failure",
    "connectivity_note",
]


def build_qualification_matrix(
    mapping_rows: list[dict[str, str]],
    inventory: dict[str, Any],
    device_rows: list[dict[str, Any]],
    alias_rows: list[dict[str, Any]],
    pin_rows: list[dict[str, Any]],
    rail_rows: list[dict[str, Any]],
) -> dict[str, Any]:
    top_inventory = {Path(row["gds_path"]).parent.name: row for row in inventory["inventory_rows"] if row["top_cell"]}
    module_inventory = inventory["module_inventory"]
    alias_by_name = {row["logical_name"]: row for row in alias_rows}
    pin_by_module = {row["logical_module"]: row for row in pin_rows}
    rail_by_module = {row["logical_module"]: row for row in rail_rows}
    device_names = {row["name"] for row in device_rows}
    qualification_rows: list[dict[str, Any]] = []
    source_rows: list[dict[str, Any]] = []
    connectivity_rows: list[dict[str, Any]] = []
    status_by_module: dict[str, str] = {}

    def qualify(logical_module: str) -> str:
        if logical_module in device_names:
            return "DEVICE_MODEL_NOT_A_HARDMACRO"
        if logical_module == "TIME":
            return "CONNECTIVITY_UNPROVEN"
        if logical_module == "TRANSMISSION_GATE":
            return "MISSING_REQUIRES_GENERATOR"
        if logical_module == "DFF":
            return "QUALIFIED_REFERENCE_ONLY"
        if logical_module in {"ADDR_DFF", "DATA_DFF"}:
            return "QUALIFIED_FOR_HIERARCHICAL_COMPOSITION"
        if logical_module == "DFF_BUF":
            return "PARTIAL_SOURCE_TRACE"
        if logical_module == "delay_chain":
            return "QUALIFIED_FIXED_VARIANT_ONLY"
        if logical_module in {"PINV", "PINV_wl_en_bar", "PNAND2"}:
            return "QUALIFIED_REFERENCE_ONLY"
        if logical_module in {"PINV1", "PINV2", "PINV3", "PINV4"}:
            return "REJECTED_SIZE_ALIAS_COLLISION"
        if logical_module in {"PNAND3", "AND2", "AND3", "pdrive", "pdrive2_for_pre", "wl_pdrive"}:
            return "REJECTED_SOURCE_MISMATCH"
        return "UNKNOWN"

    for row in mapping_rows:
        logical_module = row["logical_module"]
        gds_path = row["existing_openyield_gds_path"]
        module_dir_name = Path(gds_path).parent.name if gds_path else ""
        top_row = top_inventory.get(module_dir_name, {})
        manifest = (module_inventory.get(module_dir_name, {}) or {}).get("manifest") or {}
        generation_report = (module_inventory.get(module_dir_name, {}) or {}).get("generation_report") or {}
        pin_row = pin_by_module.get(logical_module, {})
        rail_row = rail_by_module.get(logical_module, {})
        alias_row = alias_by_name.get(logical_module, {})
        status = qualify(logical_module)
        status_by_module[logical_module] = status
        source_trace_complete = bool(generation_report or alias_row or logical_module == "DFF")
        parameter_trace_complete = logical_module in {"PINV", "PINV_wl_en_bar", "PNAND2", "delay_chain"}
        direct_geometry = bool(top_row.get("has_non_debug_geometry"))
        ref_count = int(top_row.get("instance_count", 0) or 0)
        connectivity_fail = logical_module == "TIME" or (not direct_geometry and ref_count == 0 and logical_module not in {"DFF", "PINV", "PINV_wl_en_bar", "PNAND2"})
        allowed_use = {
            "QUALIFIED_FOR_HIERARCHICAL_COMPOSITION": "HIERARCHICAL_CHILD_ONLY",
            "QUALIFIED_FIXED_VARIANT_ONLY": "HIERARCHICAL_CHILD_ONLY",
            "QUALIFIED_REFERENCE_ONLY": "REFERENCE_ONLY",
        }.get(status, "DO_NOT_USE")
        blocking_reason = {
            "DEVICE_MODEL_NOT_A_HARDMACRO": "SPICE device model name, not a placeable hardmacro.",
            "CONNECTIVITY_UNPROVEN": "Top composite exists only as candidate assembly; electrical equivalence is not proven.",
            "MISSING_REQUIRES_GENERATOR": "No standalone candidate GDS or qualified primitive layout generator exists.",
            "PARTIAL_SOURCE_TRACE": "Candidate composite provides some geometry, but source-to-physical trace is incomplete for exact logical reuse.",
            "REJECTED_SIZE_ALIAS_COLLISION": "One fixed candidate GDS was mapped to multiple logically distinct size variants.",
            "REJECTED_SOURCE_MISMATCH": "Candidate file represents a broader path/composite or the wrong primitive type.",
            "QUALIFIED_REFERENCE_ONLY": "Safe only as a traced reference, not as a direct OpenYield-qualified reusable instance.",
            "QUALIFIED_FIXED_VARIANT_ONLY": "Qualified only for one fixed candidate variant with bounded use.",
            "QUALIFIED_FOR_HIERARCHICAL_COMPOSITION": "Qualified as a bounded hierarchical child candidate, not as a final CONTROL_LOGIC top.",
            "UNKNOWN": "No trustworthy one-to-one qualification evidence was found.",
        }[status]
        qualification_rows.append(
            {
                "logical_module": logical_module,
                "candidate_cell_name": Path(gds_path).stem if gds_path else row.get("existing_layoutgen_cell_name", ""),
                "candidate_gds_path": gds_path,
                "expected_source_class": row["source_class"],
                "source_trace_complete": source_trace_complete,
                "parameter_trace_complete": parameter_trace_complete,
                "gds_parsed": row["existing_openyield_gds_found"] == "True" or bool(row.get("existing_layoutgen_cell_name")),
                "expected_cell_found": bool(gds_path or row.get("existing_layoutgen_cell_name")),
                "bbox_valid": bool(gds_path or row.get("existing_layoutgen_cell_name")),
                "real_non_debug_geometry": direct_geometry or logical_module in {"DFF", "PINV", "PINV_wl_en_bar", "PNAND2"},
                "pin_set_match": bool(pin_row.get("pin_set_match")),
                "pin_geometry_complete": bool(pin_row.get("pin_polygon_or_boundary_evidence")),
                "power_rail_geometry_complete": bool(rail_row.get("rail_geometry_present")),
                "obvious_hierarchy_or_connectivity_failure": connectivity_fail,
                "physical_strategy": row["physical_strategy"],
                "qualification_status": status,
                "blocking_reason": blocking_reason,
                "allowed_use": allowed_use,
            }
        )
        source_rows.append(
            {
                "logical_module": logical_module,
                "candidate_gds_path": gds_path,
                "generation_report_path": str(Path(gds_path).parent / "generation_report.json") if gds_path else "",
                "generator_manifest_path": str(Path(gds_path).parent / "generator_manifest.json") if gds_path else "",
                "generation_status": generation_report.get("generation_status", "REFERENCE_ONLY" if logical_module == "DFF" else ""),
                "generation_strategy": generation_report.get("generation_strategy", row["physical_strategy"]),
                "source_trace_complete": source_trace_complete,
                "parameter_trace_complete": parameter_trace_complete,
                "source_trace_note": blocking_reason,
            }
        )
        connectivity_rows.append(
            {
                "logical_module": logical_module,
                "candidate_gds_path": gds_path,
                "top_cell_name": Path(gds_path).stem if gds_path else row.get("existing_layoutgen_cell_name", ""),
                "top_cell_has_direct_geometry": direct_geometry,
                "top_cell_reference_count": ref_count,
                "expected_child_module_multiset": row["parent_path"],
                "candidate_child_cell_multiset": top_row.get("child_cells", ""),
                "obvious_hierarchy_or_connectivity_failure": connectivity_fail,
                "connectivity_note": blocking_reason,
            }
        )

    counts = {
        "qualified_direct_reuse_count": sum(1 for row in qualification_rows if row["qualification_status"] == "QUALIFIED_DIRECT_REUSE"),
        "qualified_fixed_variant_only_count": sum(1 for row in qualification_rows if row["qualification_status"] == "QUALIFIED_FIXED_VARIANT_ONLY"),
        "qualified_hierarchical_composition_count": sum(1 for row in qualification_rows if row["qualification_status"] == "QUALIFIED_FOR_HIERARCHICAL_COMPOSITION"),
        "qualified_reference_only_count": sum(1 for row in qualification_rows if row["qualification_status"] == "QUALIFIED_REFERENCE_ONLY"),
        "partial_metadata_count": sum(1 for row in qualification_rows if row["qualification_status"] in {"PARTIAL_PIN_OR_RAIL_METADATA", "PARTIAL_SOURCE_TRACE"}),
        "connectivity_unproven_count": sum(1 for row in qualification_rows if row["qualification_status"] == "CONNECTIVITY_UNPROVEN"),
        "rejected_candidate_count": sum(1 for row in qualification_rows if row["qualification_status"].startswith("REJECTED_")),
        "missing_requires_generator_count": sum(1 for row in qualification_rows if row["qualification_status"] == "MISSING_REQUIRES_GENERATOR"),
        "source_trace_complete_count": sum(1 for row in qualification_rows if row["source_trace_complete"]),
        "parameter_trace_complete_count": sum(1 for row in qualification_rows if row["parameter_trace_complete"]),
    }
    return {
        "qualification_rows": qualification_rows,
        "source_rows": source_rows,
        "connectivity_rows": connectivity_rows,
        "qualification_fields": QUAL_FIELDS,
        "source_fields": SOURCE_TRACE_FIELDS,
        "connectivity_fields": CONNECTIVITY_FIELDS,
        "status_by_module": status_by_module,
        "qualification_matrix_generated": True,
        **counts,
    }
