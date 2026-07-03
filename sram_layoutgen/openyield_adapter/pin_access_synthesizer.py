from __future__ import annotations

import re
from typing import Any

from sram_layoutgen.openyield_adapter.module_pin_extractor import parse_layer_number


def infer_edge_from_point(bbox: dict[str, float], x: float, y: float) -> str:
    distances = {
        "left": abs(x - float(bbox["x0"])),
        "right": abs(x - float(bbox["x1"])),
        "bottom": abs(y - float(bbox["y0"])),
        "top": abs(y - float(bbox["y1"])),
    }
    return min(distances, key=distances.get)


def bbox_center(bbox: dict[str, float]) -> dict[str, float]:
    return {
        "x": round((float(bbox["x0"]) + float(bbox["x1"])) / 2.0, 6),
        "y": round((float(bbox["y0"]) + float(bbox["y1"])) / 2.0, 6),
    }


def _layer_for_pin(raw_pin: dict[str, Any] | None, pin_category: str) -> int:
    layer = parse_layer_number((raw_pin or {}).get("layer"))
    if layer is not None:
        return layer
    if pin_category in {"POWER", "GROUND", "CLOCK"}:
        return 11
    return 13


def _rect(x0: float, y0: float, x1: float, y1: float) -> dict[str, float]:
    return {
        "x0": round(min(x0, x1), 6),
        "y0": round(min(y0, y1), 6),
        "x1": round(max(x0, x1), 6),
        "y1": round(max(y0, y1), 6),
        "width": round(abs(x1 - x0), 6),
        "height": round(abs(y1 - y0), 6),
    }


def _index(pin_name: str) -> int | None:
    match = re.search(r"\[(\d+)\]", str(pin_name))
    return int(match.group(1)) if match else None


def synthesize_pin_access(
    module_name: str,
    physical_role: str,
    pin_name: str,
    pin_category: str,
    module_bbox: dict[str, float],
    raw_pin: dict[str, Any] | None,
    supported_counts: dict[str, int],
    source_evidence: list[str] | None = None,
) -> dict[str, Any]:
    x0 = float(module_bbox["x0"])
    y0 = float(module_bbox["y0"])
    x1 = float(module_bbox["x1"])
    y1 = float(module_bbox["y1"])
    width = float(module_bbox["width"])
    height = float(module_bbox["height"])
    x = float((raw_pin or {}).get("x", x0) or x0)
    y = float((raw_pin or {}).get("y", y0) or y0)
    layer = _layer_for_pin(raw_pin, pin_category)
    edge = infer_edge_from_point(module_bbox, x, y)

    rows = max(1, int(supported_counts.get("rows", 1) or 1))
    cols = max(1, int(supported_counts.get("cols", 1) or 1))
    row_pitch = height / rows
    col_pitch = width / cols
    idx = _index(pin_name)

    synthesis_rule = "C2_EDGE_ACCESS_NEAREST_BOUNDARY"
    direction = "edge_access"
    if module_name in {"bitcell_array", "dummy_array", "replica_array"} and idx is not None and pin_name.startswith("BL["):
        synthesis_rule = "C2_ARRAY_COLUMN_PITCH_BL_ACCESS"
        xc = x0 + col_pitch * (idx + 0.25)
        half = max(col_pitch * 0.08, 0.04)
        bbox = _rect(xc - half, y0, xc + half, y1)
        edge = "top_bottom_span"
        direction = "vertical_column_access"
    elif module_name in {"bitcell_array", "dummy_array", "replica_array"} and idx is not None and pin_name.startswith("BR["):
        synthesis_rule = "C2_ARRAY_COLUMN_PITCH_BR_ACCESS"
        xc = x0 + col_pitch * (idx + 0.75)
        half = max(col_pitch * 0.08, 0.04)
        bbox = _rect(xc - half, y0, xc + half, y1)
        edge = "top_bottom_span"
        direction = "vertical_column_access"
    elif module_name in {"bitcell_array", "dummy_array", "replica_array"} and idx is not None and pin_name.startswith("WL["):
        synthesis_rule = "C2_ARRAY_ROW_PITCH_WL_ACCESS"
        yc = y0 + row_pitch * (idx + 0.5)
        half = max(row_pitch * 0.08, 0.04)
        bbox = _rect(x0, yc - half, x1, yc + half)
        edge = "left_right_span"
        direction = "horizontal_row_access"
    elif module_name == "replica_array" and pin_name.upper() == "RBL":
        synthesis_rule = "C2_REPLICA_ARRAY_RBL_EDGE_ACCESS"
        half = max(col_pitch * 0.12, 0.05)
        bbox = _rect(x1 - 2 * half, y0, x1 - half, y1)
        edge = "right"
        direction = "vertical_column_access"
    elif pin_name.upper() == "VDD":
        synthesis_rule = "C2_POWER_RAIL_SYNTHESIS"
        rail_h = max(height * 0.06, 0.08)
        bbox = _rect(x0, y1 - rail_h, x1, y1)
        edge = "top"
        direction = "horizontal_rail_access"
    elif pin_name.upper() == "GND":
        synthesis_rule = "C2_POWER_RAIL_SYNTHESIS"
        rail_h = max(height * 0.06, 0.08)
        bbox = _rect(x0, y0, x1, y0 + rail_h)
        edge = "bottom"
        direction = "horizontal_rail_access"
    else:
        pad_w = max(width * 0.08, 0.08)
        pad_h = max(height * 0.08, 0.08)
        if edge == "left":
            bbox = _rect(x0, max(y0, y - pad_h / 2), x0 + pad_w, min(y1, y + pad_h / 2))
            direction = "west_edge_access"
        elif edge == "right":
            bbox = _rect(x1 - pad_w, max(y0, y - pad_h / 2), x1, min(y1, y + pad_h / 2))
            direction = "east_edge_access"
        elif edge == "top":
            bbox = _rect(max(x0, x - pad_w / 2), y1 - pad_h, min(x1, x + pad_w / 2), y1)
            direction = "north_edge_access"
        else:
            bbox = _rect(max(x0, x - pad_w / 2), y0, min(x1, x + pad_w / 2), y0 + pad_h)
            direction = "south_edge_access"

    return {
        "bbox": bbox,
        "layer": layer,
        "edge": edge,
        "direction": direction,
        "status": "SYNTHESIZED_PIN_FOR_CURRENT_GENERATOR",
        "synthesis_rule": synthesis_rule,
        "source_evidence": ";".join(source_evidence or []),
    }
