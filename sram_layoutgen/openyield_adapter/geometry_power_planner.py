from __future__ import annotations

from typing import Any

from sram_layoutgen.openyield_adapter.power_shape_index import rect_bbox


POWER_LAYER_VDD = 41
POWER_LAYER_GND = 42
TOP_POWER_PIN_LAYER = 43


def region_power_rail_bbox(region_bbox: dict[str, float], net_name: str) -> dict[str, float]:
    height = min(0.18, max(0.08, float(region_bbox["height"]) * 0.04))
    margin = min(0.12, max(0.04, float(region_bbox["height"]) * 0.01))
    if net_name == "VDD":
        y1 = float(region_bbox["y1"]) - margin
        y0 = y1 - height
    else:
        y0 = float(region_bbox["y0"]) + margin
        y1 = y0 + height
    return rect_bbox(float(region_bbox["x0"]), y0, float(region_bbox["x1"]), y1)


def top_power_pin_bbox(strap_bbox: dict[str, float], side: str) -> dict[str, float]:
    width = 1.6
    margin = 0.4
    if side == "left":
        x0 = float(strap_bbox["x0"]) + margin
    else:
        x0 = float(strap_bbox["x1"]) - margin - width
    return rect_bbox(x0, float(strap_bbox["y0"]), x0 + width, float(strap_bbox["y1"]))


def stitch_rect_between(source_bbox: dict[str, float], target_bbox: dict[str, float]) -> dict[str, float]:
    sx = (float(source_bbox["x0"]) + float(source_bbox["x1"])) / 2.0
    tx = (float(target_bbox["x0"]) + float(target_bbox["x1"])) / 2.0
    x0 = min(sx, tx) - 0.05
    x1 = max(sx, tx) + 0.05
    sy = (float(source_bbox["y0"]) + float(source_bbox["y1"])) / 2.0
    ty = (float(target_bbox["y0"]) + float(target_bbox["y1"])) / 2.0
    y0 = min(sy, ty)
    y1 = max(sy, ty)
    if abs(y1 - y0) < 0.08:
        y0 -= 0.04
        y1 += 0.04
    return rect_bbox(x0, y0, x1, y1)


def nearest_anchor_rect(source_bbox: dict[str, float], anchor_y: float) -> dict[str, float]:
    sx = (float(source_bbox["x0"]) + float(source_bbox["x1"])) / 2.0
    return rect_bbox(sx - 0.05, min(float(source_bbox["y0"]), anchor_y), sx + 0.05, max(float(source_bbox["y1"]), anchor_y))


def region_name_for_module(placement_row: dict[str, Any]) -> str:
    region = placement_row["region"]
    if region in {"ARRAY_CORE_REGION", "ARRAY_BOUNDARY_REGION"}:
        return "ARRAY"
    if region == "ROW_PATH_REGION":
        return "ROW"
    if region == "COLUMN_PATH_REGION":
        return "COLUMN"
    return "CONTROL"
