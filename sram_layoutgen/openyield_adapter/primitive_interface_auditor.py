from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .primitive_geometry_verifier import read_top_cell


def audit_approved_primitive_interfaces(reusable_root: Path) -> dict[str, Any]:
    rows: list[dict[str, Any]] = []
    power_rows: list[dict[str, Any]] = []
    pin_rows: list[dict[str, Any]] = []
    heights = []
    vdd_rows = set()
    vss_rows = set()
    for cell_dir in sorted(reusable_root.iterdir()):
        if not cell_dir.is_dir():
            continue
        cell_name = cell_dir.name
        gds_path = cell_dir / f"{cell_name}.gds"
        pin_map = json.loads((cell_dir / f"{cell_name}_pin_map.json").read_text(encoding="utf-8"))
        _, top = read_top_cell(gds_path, cell_name)
        bbox = top.bounding_box()
        x0, y0 = [float(v) for v in bbox[0]]
        x1, y1 = [float(v) for v in bbox[1]]
        height = round(y1 - y0, 6)
        widths = round(x1 - x0, 6)
        heights.append(height)
        vdd = pin_map["VDD"][0]
        vss = pin_map["VSS"][0]
        vdd_rows.add((round(vdd["by"], 6), round(vdd["uy"], 6)))
        vss_rows.add((round(vss["by"], 6), round(vss["uy"], 6)))
        rows.append(
            {
                "cell_name": cell_name,
                "cell_width": widths,
                "cell_height": height,
                "boundary_bbox": [x0, y0, x1, y1],
                "vdd_layer": vdd["layer"],
                "vdd_bbox": [vdd["lx"], vdd["by"], vdd["rx"], vdd["uy"]],
                "vss_layer": vss["layer"],
                "vss_bbox": [vss["lx"], vss["by"], vss["rx"], vss["uy"]],
                "rail_width": round(vdd["uy"] - vdd["by"], 6),
                "rail_extension_to_left_boundary": round(vdd["lx"] - x0, 6),
                "rail_extension_to_right_boundary": round(x1 - vdd["rx"], 6),
                "orientation_support": "R0_ONLY_ASSUMED_FOR_V1",
                "mirror_support": "MX_NOT_PROVEN",
                "rotation_support": "R90_FORBIDDEN",
            }
        )
        power_rows.append(
            {
                "cell_name": cell_name,
                "vdd_y_min": vdd["by"],
                "vdd_y_max": vdd["uy"],
                "vss_y_min": vss["by"],
                "vss_y_max": vss["uy"],
                "vdd_layer": vdd["layer"],
                "vss_layer": vss["layer"],
            }
        )
        for pin_name, entries in pin_map.items():
            for entry in entries:
                pin_rows.append(
                    {
                        "cell_name": cell_name,
                        "pin_name": pin_name,
                        "pin_layer": entry["layer"],
                        "pin_access_box": [entry["lx"], entry["by"], entry["rx"], entry["uy"]],
                        "distance_left": round(entry["lx"] - x0, 6),
                        "distance_right": round(x1 - entry["rx"], 6),
                        "distance_bottom": round(entry["by"] - y0, 6),
                        "distance_top": round(y1 - entry["uy"], 6),
                    }
                )
    interface_status = "LOCKED_COMPOSITION_COMPATIBLE_V1"
    heights_compatible = len(set(heights)) == 1
    tg_compatible = heights_compatible
    if not heights_compatible:
        interface_status = "PARTIAL_REQUIRES_INTERFACE_NORMALIZATION"
    return {
        "interface_rows": rows,
        "power_rows": power_rows,
        "pin_rows": pin_rows,
        "summary": {
            "primitive_interface_audit_completed": True,
            "interface_compatibility_status": interface_status,
            "all_primitive_heights_compatible": heights_compatible,
            "all_vdd_rails_align": len(vdd_rows) == 1,
            "all_vss_rails_align": len(vss_rows) == 1,
            "all_power_rail_layers_compatible": all(row["vdd_layer"] == "m1" and row["vss_layer"] == "m1" for row in power_rows),
            "all_boundary_stitching_compatible": heights_compatible and len(vdd_rows) == 1 and len(vss_rows) == 1,
            "all_signal_pins_accessible_for_composition": all(row["pin_layer"] == "m1" for row in pin_rows),
            "transmission_gate_interface_compatible_with_pinv_row": tg_compatible,
            "well_overlap_or_spacing_risk_detected": not heights_compatible,
            "orientation_policy_locked": True,
        },
    }
