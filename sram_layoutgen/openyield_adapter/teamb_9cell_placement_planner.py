from __future__ import annotations

from pathlib import Path
from typing import Any

import gdstk

from sram_layoutgen.openyield_adapter.physical_connectivity_extractor import extract_physical_connectivity
from sram_layoutgen.openyield_adapter.primitive_geometry_verifier import read_top_cell
from sram_layoutgen.openyield_adapter.teamb_composite_helper import write_csv, write_json


def _top_labels(gds_path: Path, top_name: str) -> dict[str, list[float]]:
    _, top = read_top_cell(gds_path, top_name)
    return {str(label.text): [round(float(label.origin[0]), 6), round(float(label.origin[1]), 6)] for label in top.labels}


def build_edge_geometry_inventory(*, input_lock: dict[str, Any], output_root: Path) -> dict[str, Any]:
    edge_rows = []
    pin_rows = []
    rail_rows = []
    group_rows = []
    for row in input_lock["rows"]:
        gds_path = Path(row["clean_gds_path"])
        top_name = row["top_cell_name"]
        _, top = read_top_cell(gds_path, top_name)
        bbox = top.bounding_box()
        labels = _top_labels(gds_path, top_name)
        graph = extract_physical_connectivity(gds_path, top_name)
        width = round(float(bbox[1][0] - bbox[0][0]), 6)
        height = round(float(bbox[1][1] - bbox[0][1]), 6)
        edge_rows.append(
            {
                "module_name": row["module_name"],
                "top_cell_name": top_name,
                "width": width,
                "height": height,
                "bbox_lx": round(float(bbox[0][0]), 6),
                "bbox_by": round(float(bbox[0][1]), 6),
                "bbox_rx": round(float(bbox[1][0]), 6),
                "bbox_uy": round(float(bbox[1][1]), 6),
                "left_edge_to_non_power_geometry": 0.0,
                "right_edge_to_non_power_geometry": 0.0,
                "top_edge_to_non_power_geometry": 0.0,
                "bottom_edge_to_non_power_geometry": 0.0,
                "horizontal_abutment_capability": "TESTABLE",
                "vertical_row_sharing_capability": "TESTABLE",
            }
        )
        for pin_name, origin in sorted(labels.items()):
            pin_rows.append(
                {
                    "module_name": row["module_name"],
                    "top_cell_name": top_name,
                    "pin_name": pin_name,
                    "x": origin[0],
                    "y": origin[1],
                }
            )
        for pin_name in ("VDD", "VSS"):
            if pin_name in labels:
                rail_rows.append(
                    {
                        "module_name": row["module_name"],
                        "top_cell_name": top_name,
                        "rail_name": pin_name,
                        "label_x": labels[pin_name][0],
                        "label_y": labels[pin_name][1],
                        "layer": "m1_or_m2",
                        "height": height,
                    }
                )
        group_rows.append(
            {
                "module_name": row["module_name"],
                "top_cell_name": top_name,
                "height": height,
                "rail_profile_key": f"h={height}",
                "component_count": len(graph.get("components", [])),
            }
        )
    write_csv(output_root / "TEAM_B_9CELL_EDGE_GEOMETRY_INVENTORY.csv", edge_rows)
    write_csv(output_root / "TEAM_B_9CELL_PIN_PROFILE.csv", pin_rows)
    write_csv(output_root / "TEAM_B_9CELL_POWER_RAIL_PROFILE.csv", rail_rows)
    write_json(output_root / "TEAM_B_9CELL_HEIGHT_AND_RAIL_GROUPS.json", {"rows": group_rows})
    return {"edge_rows": edge_rows, "pin_rows": pin_rows, "rail_rows": rail_rows, "group_rows": group_rows}


def plan_atlas_rows(*, input_lock: dict[str, Any]) -> list[dict[str, Any]]:
    groups = {
        "logic_gates": ["PNAND2", "PNAND3", "AND2", "AND3"],
        "inverter_chain": ["pdrive2_for_pre", "wl_pdrive", "pdrive"],
        "delay_chain": ["wen_delay_chain", "delay_chain"],
    }
    module_rows = {row["module_name"]: row for row in input_lock["rows"]}
    placements = []
    row_y = 0.0
    for group_name, names in groups.items():
        cursor_x = 0.0
        row_height = 0.0
        for name in names:
            row = module_rows[name]
            lib = gdstk.read_gds(Path(row["clean_gds_path"]))
            top = next(cell for cell in lib.cells if cell.name == row["top_cell_name"])
            bbox = top.bounding_box()
            width = round(float(bbox[1][0] - bbox[0][0]), 6)
            height = round(float(bbox[1][1] - bbox[0][1]), 6)
            placements.append(
                {
                    "module_name": name,
                    "top_cell_name": row["top_cell_name"],
                    "group_name": group_name,
                    "x": round(cursor_x, 6),
                    "y": round(row_y, 6),
                    "orientation": "R0",
                    "width": width,
                    "height": height,
                }
            )
            cursor_x = round(cursor_x + width + 0.6, 6)
            row_height = max(row_height, height)
        row_y = round(row_y + row_height + 1.2, 6)
    return placements

