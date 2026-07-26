from __future__ import annotations

from typing import Any


def build_manifest(
    qualification_rows: list[dict[str, Any]],
    source_rows: list[dict[str, Any]],
    pin_rows: list[dict[str, Any]],
    rail_rows: list[dict[str, Any]],
) -> dict[str, Any]:
    source_by_module = {row["logical_module"]: row for row in source_rows}
    pin_by_module = {row["logical_module"]: row for row in pin_rows}
    rail_by_module = {row["logical_module"]: row for row in rail_rows}
    manifest_rows: list[dict[str, Any]] = []
    quarantined_rows: list[dict[str, Any]] = []
    for row in qualification_rows:
        logical_module = row["logical_module"]
        pin_row = pin_by_module.get(logical_module, {})
        rail_row = rail_by_module.get(logical_module, {})
        source_row = source_by_module.get(logical_module, {})
        entry = {
            "logical_module": logical_module,
            "physical_cell_name": row["candidate_cell_name"],
            "gds_path": row["candidate_gds_path"],
            "qualification_status": row["qualification_status"],
            "supported_parameters": "fixed reference config only" if row["qualification_status"] != "QUALIFIED_FOR_HIERARCHICAL_COMPOSITION" else "fixed candidate bus-role mapping only",
            "supported_configurations": "read&write canonical topology reference config",
            "fixed_or_parameterized": "FIXED_ONLY",
            "bbox": "candidate bbox metadata available" if row["candidate_gds_path"] else "reference-only",
            "pin_map": pin_row.get("candidate_pin_names", ""),
            "pin_geometry": pin_row.get("pin_polygon_or_boundary_evidence", False),
            "power_rails": rail_row.get("power_names_found", ""),
            "layer_map": "candidate FreePDK45 layers only",
            "orientation_constraints": "respect original candidate orientation until later floorplan qualification",
            "abutment_constraints": "row-rail abutment is not yet globally proven",
            "source_trace": source_row.get("source_trace_note", ""),
            "geometry_fingerprint": row["candidate_gds_path"],
            "known_limitations": row["blocking_reason"],
            "allowed_use": row["allowed_use"],
        }
        if row["qualification_status"] in {
            "QUALIFIED_DIRECT_REUSE",
            "QUALIFIED_FIXED_VARIANT_ONLY",
            "QUALIFIED_FOR_HIERARCHICAL_COMPOSITION",
            "QUALIFIED_REFERENCE_ONLY",
        }:
            manifest_rows.append(entry)
        else:
            quarantined_rows.append(entry)
    return {
        "manifest": manifest_rows,
        "quarantined": quarantined_rows,
        "qualified_manifest_generated": True,
        "qualified_manifest_entry_count": len(manifest_rows),
        "quarantined_candidate_count": len(quarantined_rows),
    }
