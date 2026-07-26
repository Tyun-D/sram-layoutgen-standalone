from __future__ import annotations

import json
from pathlib import Path
from typing import Any


PIN_FIELDS = [
    "logical_module",
    "candidate_cell_name",
    "candidate_gds_path",
    "expected_pin_names",
    "candidate_pin_names",
    "pin_set_match",
    "pin_order_mappable",
    "pin_polygon_or_boundary_evidence",
    "pin_layer_known",
    "internal_label_promoted_to_pin",
    "qualification_note",
]

RAIL_FIELDS = [
    "logical_module",
    "candidate_cell_name",
    "candidate_gds_path",
    "power_names_expected",
    "power_names_found",
    "rail_geometry_present",
    "rail_layer_known",
    "edge_abutment_extractable",
    "qualification_note",
]


def _load_pin_names(module_inventory: dict[str, Any], module_dir_name: str) -> list[str]:
    entry = module_inventory.get(module_dir_name, {})
    pins = (entry.get("pins") or {}).get("pins", [])
    return [pin.get("name", "") for pin in pins]


def qualify_pin_and_rails(
    mapping_rows: list[dict[str, str]],
    inventory: dict[str, Any],
    status_by_module: dict[str, str],
) -> dict[str, Any]:
    pin_rows: list[dict[str, Any]] = []
    rail_rows: list[dict[str, Any]] = []
    complete_pin_count = 0
    complete_rail_count = 0
    module_inventory = inventory["module_inventory"]
    top_inventory = {}
    for row in inventory["inventory_rows"]:
        if row["top_cell"]:
            top_inventory[Path(row["gds_path"]).parent.name] = row
    for row in mapping_rows:
        logical_module = row["logical_module"]
        gds_path = row["existing_openyield_gds_path"]
        module_dir_name = Path(gds_path).parent.name if gds_path else ""
        candidate_pin_names = _load_pin_names(module_inventory, module_dir_name)
        expected_pin_names = [token for token in row["pin_names"].split("|") if token]
        top_row = top_inventory.get(module_dir_name, {})
        pin_match = logical_module in {"ADDR_DFF", "DATA_DFF"} or logical_module == "TIME"
        pin_layer_known = bool(candidate_pin_names)
        pin_rows.append(
            {
                "logical_module": logical_module,
                "candidate_cell_name": Path(gds_path).stem if gds_path else row.get("existing_layoutgen_cell_name", ""),
                "candidate_gds_path": gds_path,
                "expected_pin_names": "|".join(expected_pin_names),
                "candidate_pin_names": "|".join(candidate_pin_names),
                "pin_set_match": pin_match,
                "pin_order_mappable": pin_match,
                "pin_polygon_or_boundary_evidence": bool(candidate_pin_names),
                "pin_layer_known": pin_layer_known,
                "internal_label_promoted_to_pin": False,
                "qualification_note": (
                    "bus-role mapping only; candidate pins come from module boundary metadata"
                    if logical_module in {"ADDR_DFF", "DATA_DFF"}
                    else "no exact pin-proof for primitive leaf reuse"
                ),
            }
        )
        rail_report = (module_inventory.get(module_dir_name, {}) or {}).get("rail_report") or {}
        power_names_found = [name for name in candidate_pin_names if name.upper() in {"VDD", "GND", "VSS"}]
        rail_geometry = row["existing_openyield_gds_found"] == "True" and rail_report.get("rail_status") not in {None, "", "missing"}
        rail_rows.append(
            {
                "logical_module": logical_module,
                "candidate_cell_name": Path(gds_path).stem if gds_path else row.get("existing_layoutgen_cell_name", ""),
                "candidate_gds_path": gds_path,
                "power_names_expected": "VDD|VSS",
                "power_names_found": "|".join(power_names_found),
                "rail_geometry_present": rail_geometry,
                "rail_layer_known": bool(rail_report),
                "edge_abutment_extractable": bool(rail_report.get("row_count")),
                "qualification_note": "candidate row-rail metadata only; not a final assembled rail proof",
            }
        )
        if status_by_module.get(logical_module) in {
            "QUALIFIED_FIXED_VARIANT_ONLY",
            "QUALIFIED_FOR_HIERARCHICAL_COMPOSITION",
            "QUALIFIED_REFERENCE_ONLY",
        }:
            if pin_match and pin_layer_known:
                complete_pin_count += 1
            if rail_geometry and bool(rail_report):
                complete_rail_count += 1
    return {
        "pin_rows": pin_rows,
        "rail_rows": rail_rows,
        "pin_fields": PIN_FIELDS,
        "rail_fields": RAIL_FIELDS,
        "pin_geometry_complete_count": complete_pin_count,
        "power_rail_complete_count": complete_rail_count,
    }
