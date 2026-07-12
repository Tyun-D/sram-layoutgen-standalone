from __future__ import annotations

from typing import Any


def snap_coordinate(value: float, grid: float) -> float:
    return round(round(float(value) / grid) * grid, 6)


def snap_via_center(value: float, grid: float) -> float:
    return snap_coordinate(value, grid)


def snap_bbox(bbox: dict[str, float], grid: float) -> dict[str, float]:
    return {
        "lx": snap_coordinate(bbox["lx"], grid),
        "by": snap_coordinate(bbox["by"], grid),
        "rx": snap_coordinate(bbox["rx"], grid),
        "uy": snap_coordinate(bbox["uy"], grid),
    }


def snap_rect_with_legal_width(
    *,
    cx: float | None = None,
    cy: float | None = None,
    lx: float | None = None,
    by: float | None = None,
    rx: float | None = None,
    uy: float | None = None,
    width: float,
    height: float,
    grid: float,
) -> dict[str, float]:
    snapped_width = snap_coordinate(width, grid)
    snapped_height = snap_coordinate(height, grid)
    if cx is not None and cy is not None:
        half_w = snapped_width * 0.5
        half_h = snapped_height * 0.5
        return snap_bbox(
            {
                "lx": float(cx) - half_w,
                "by": float(cy) - half_h,
                "rx": float(cx) + half_w,
                "uy": float(cy) + half_h,
            },
            grid,
        )
    assert lx is not None and by is not None and rx is not None and uy is not None
    return snap_bbox({"lx": lx, "by": by, "rx": rx, "uy": uy}, grid)


def bbox_center(bbox: dict[str, float], grid: float | None = None) -> tuple[float, float]:
    cx = (float(bbox["lx"]) + float(bbox["rx"])) * 0.5
    cy = (float(bbox["by"]) + float(bbox["uy"])) * 0.5
    if grid is None:
        return (round(cx, 6), round(cy, 6))
    return (snap_coordinate(cx, grid), snap_coordinate(cy, grid))


def expand_bbox(bbox: dict[str, float], delta: float, grid: float | None = None) -> dict[str, float]:
    expanded = {
        "lx": float(bbox["lx"]) - delta,
        "by": float(bbox["by"]) - delta,
        "rx": float(bbox["rx"]) + delta,
        "uy": float(bbox["uy"]) + delta,
    }
    return snap_bbox(expanded, grid) if grid is not None else expanded


def bbox_overlaps(left: dict[str, float], right: dict[str, float], epsilon: float = 1e-6) -> bool:
    return not (
        float(left["rx"]) < float(right["lx"]) - epsilon
        or float(right["rx"]) < float(left["lx"]) - epsilon
        or float(left["uy"]) < float(right["by"]) - epsilon
        or float(right["uy"]) < float(left["by"]) - epsilon
    )


def bbox_to_list(bbox: dict[str, float]) -> list[float]:
    return [round(float(bbox["lx"]), 6), round(float(bbox["by"]), 6), round(float(bbox["rx"]), 6), round(float(bbox["uy"]), 6)]


def rect_from_segment(
    start: tuple[float, float],
    end: tuple[float, float],
    width: float,
    grid: float,
) -> dict[str, float]:
    start_x = snap_coordinate(start[0], grid)
    start_y = snap_coordinate(start[1], grid)
    end_x = snap_coordinate(end[0], grid)
    end_y = snap_coordinate(end[1], grid)
    half = snap_coordinate(width * 0.5, grid)
    if abs(start_x - end_x) <= 1e-6:
        return snap_bbox(
            {
                "lx": start_x - half,
                "by": min(start_y, end_y),
                "rx": start_x + half,
                "uy": max(start_y, end_y),
            },
            grid,
        )
    return snap_bbox(
        {
            "lx": min(start_x, end_x),
            "by": start_y - half,
            "rx": max(start_x, end_x),
            "uy": start_y + half,
        },
        grid,
    )


def bbox_contains(container: dict[str, float], inner: dict[str, float], epsilon: float = 1e-6) -> bool:
    return (
        float(container["lx"]) <= float(inner["lx"]) + epsilon
        and float(container["by"]) <= float(inner["by"]) + epsilon
        and float(container["rx"]) >= float(inner["rx"]) - epsilon
        and float(container["uy"]) >= float(inner["uy"]) - epsilon
    )


def count_off_grid_vertices(bboxes: list[dict[str, float]], grid: float) -> int:
    count = 0
    for bbox in bboxes:
        for key in ("lx", "by", "rx", "uy"):
            value = float(bbox[key])
            if abs(value - snap_coordinate(value, grid)) > 1e-9:
                count += 1
    return count

