"""Global floorplan occupancy analysis for SRAM layout compaction."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

from .geometry import LayoutDB, Rect


@dataclass(frozen=True)
class OccupancyRegion:
    kind: str
    name: str
    role: str
    rect: Rect

    @property
    def area(self) -> float:
        return self.rect.area


def analyze_floorplan_occupancy(
    layout: LayoutDB,
    *,
    coarse_columns: int = 48,
    max_empty_regions: int = 16,
) -> dict[str, object]:
    """Return a global "what fills where" occupancy model.

    Placement objects are used as physical occupancy. Module overlays are used
    only to label the coarse map, because they can intentionally nest.
    """

    boundary = _placement_boundary(layout)
    placement_regions = _collect_placement_regions(layout, boundary)
    module_regions = _collect_module_regions(layout, boundary)

    cells = _atomic_cells(boundary, [region.rect for region in placement_regions])
    role_primary_area: dict[str, float] = {}
    kind_primary_area: dict[str, float] = {}
    free_cells: set[tuple[int, int]] = set()
    occupied_area = 0.0

    for ix, iy, cell in cells:
        covers = [region for region in placement_regions if _contains_center(region.rect, cell)]
        if not covers:
            free_cells.add((ix, iy))
            continue
        occupied_area += cell.area
        primary = min(covers, key=lambda region: (region.area, region.kind, region.name))
        role_primary_area[primary.role] = role_primary_area.get(primary.role, 0.0) + cell.area
        kind_primary_area[primary.kind] = kind_primary_area.get(primary.kind, 0.0) + cell.area

    all_empty_regions = _merge_empty_cells(cells, free_cells)
    empty_regions = all_empty_regions[:max_empty_regions]
    macro_area = boundary.area
    empty_area = max(0.0, macro_area - occupied_area)
    edge_empty_area = _edge_empty_area(all_empty_regions, boundary)
    largest_empty = all_empty_regions[0] if all_empty_regions else None

    coarse = _coarse_role_map(boundary, placement_regions, module_regions, coarse_columns)
    optimization_targets = _optimization_targets(empty_regions, placement_regions, boundary)

    return {
        "method": (
            "Exact rectangle decomposition over top-level physical placement objects "
            "with module overlays used as semantic labels for a coarse floorplan map."
        ),
        "boundary": _rect_dict(boundary),
        "macro_area_um2": round(macro_area, 6),
        "occupied_area_um2": round(occupied_area, 6),
        "empty_area_um2": round(empty_area, 6),
        "occupancy_ratio": occupied_area / macro_area if macro_area else 0.0,
        "empty_ratio": empty_area / macro_area if macro_area else 0.0,
        "edge_empty_area_um2": round(edge_empty_area, 6),
        "largest_empty_area_um2": round(largest_empty["area_um2"], 6) if largest_empty else 0.0,
        "empty_region_count": len(all_empty_regions),
        "empty_regions": empty_regions,
        "optimization_targets": optimization_targets,
        "role_primary_area_um2": _round_area_map(role_primary_area),
        "kind_primary_area_um2": _round_area_map(kind_primary_area),
        "placement_region_count": len(placement_regions),
        "module_region_count": len(module_regions),
        "module_regions": [
            {
                "name": region.name,
                "role": region.role,
                "area_um2": round(region.area, 6),
                "rect": _rect_dict(region.rect),
            }
            for region in sorted(module_regions, key=lambda item: (item.rect.y0, item.rect.x0, item.name))
        ],
        "coarse_map": coarse,
    }


def write_occupancy_svg(path: Path, analysis: dict[str, object]) -> None:
    """Write a lightweight visual view of occupied modules and largest voids."""

    boundary = _rect_from_dict(analysis["boundary"])
    modules = analysis.get("module_regions", [])
    empty_regions = analysis.get("empty_regions", [])
    width_px = 1200.0
    scale = width_px / max(boundary.width, 1e-9)
    height_px = max(1.0, boundary.height * scale)
    palette = [
        "#4c78a8",
        "#f58518",
        "#54a24b",
        "#e45756",
        "#72b7b2",
        "#b279a2",
        "#ff9da6",
        "#9d755d",
        "#bab0ac",
        "#59a14f",
        "#edc948",
        "#af7aa1",
    ]

    def sx(x: float) -> float:
        return (x - boundary.x0) * scale

    def sy(y: float) -> float:
        return height_px - (y - boundary.y0) * scale

    lines = [
        '<svg xmlns="http://www.w3.org/2000/svg" '
        f'width="{width_px:.1f}" height="{height_px:.1f}" viewBox="0 0 {width_px:.1f} {height_px:.1f}">',
        '<rect width="100%" height="100%" fill="#fbfbf8"/>',
        f'<rect x="0" y="0" width="{width_px:.1f}" height="{height_px:.1f}" '
        'fill="none" stroke="#222" stroke-width="2"/>',
    ]
    for index, module in enumerate(modules):
        rect = _rect_from_dict(module["rect"])
        color = palette[index % len(palette)]
        lines.append(
            f'<rect x="{sx(rect.x0):.2f}" y="{sy(rect.y1):.2f}" '
            f'width="{rect.width * scale:.2f}" height="{rect.height * scale:.2f}" '
            f'fill="{color}" fill-opacity="0.34" stroke="{color}" stroke-width="1.2"/>'
        )
        if rect.width * scale > 55 and rect.height * scale > 16:
            lines.append(
                f'<text x="{sx(rect.x0) + 4:.2f}" y="{sy(rect.y1) + 13:.2f}" '
                'font-family="monospace" font-size="12" fill="#202020">'
                f'{_escape_svg(str(module.get("name", "")))}</text>'
            )
    for index, item in enumerate(empty_regions[:12]):
        rect = _rect_from_dict(item["rect"])
        opacity = 0.30 if index == 0 else 0.18
        lines.append(
            f'<rect x="{sx(rect.x0):.2f}" y="{sy(rect.y1):.2f}" '
            f'width="{rect.width * scale:.2f}" height="{rect.height * scale:.2f}" '
            f'fill="#d62728" fill-opacity="{opacity:.2f}" stroke="#8c1d18" '
            'stroke-dasharray="5 3" stroke-width="1"/>'
        )
    lines.append("</svg>")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


def _placement_boundary(layout: LayoutDB) -> Rect:
    return next(
        (shape.rect for shape in layout.shapes if shape.purpose == "boundary" and shape.name == "prBoundary"),
        layout.bounds,
    )


def _collect_placement_regions(layout: LayoutDB, boundary: Rect) -> list[OccupancyRegion]:
    regions: list[OccupancyRegion] = []
    for array in layout.cell_arrays:
        clipped = _clip_rect(array.rect, boundary)
        if clipped is not None:
            regions.append(OccupancyRegion("cell_array", array.name, array.role or array.cell, clipped))
    for instance in layout.instances:
        clipped = _clip_rect(instance.rect, boundary)
        if clipped is not None:
            regions.append(OccupancyRegion("instance", instance.name, instance.role or instance.cell, clipped))
    return regions


def _collect_module_regions(layout: LayoutDB, boundary: Rect) -> list[OccupancyRegion]:
    regions: list[OccupancyRegion] = []
    for shape in layout.shapes:
        if shape.purpose != "module" or not shape.name:
            continue
        clipped = _clip_rect(shape.rect, boundary)
        if clipped is not None:
            regions.append(OccupancyRegion("module", shape.name, shape.name, clipped))
    return regions


def _atomic_cells(boundary: Rect, rects: Iterable[Rect]) -> list[tuple[int, int, Rect]]:
    xs = {boundary.x0, boundary.x1}
    ys = {boundary.y0, boundary.y1}
    for rect in rects:
        xs.update((max(boundary.x0, rect.x0), min(boundary.x1, rect.x1)))
        ys.update((max(boundary.y0, rect.y0), min(boundary.y1, rect.y1)))
    x_values = sorted(xs)
    y_values = sorted(ys)
    cells: list[tuple[int, int, Rect]] = []
    for ix, (x0, x1) in enumerate(zip(x_values, x_values[1:])):
        if x1 <= x0:
            continue
        for iy, (y0, y1) in enumerate(zip(y_values, y_values[1:])):
            if y1 <= y0:
                continue
            cells.append((ix, iy, Rect(x0, y0, x1, y1)))
    return cells


def _merge_empty_cells(
    cells: list[tuple[int, int, Rect]],
    free_cells: set[tuple[int, int]],
) -> list[dict[str, object]]:
    by_y: dict[int, list[tuple[int, Rect]]] = {}
    for ix, iy, cell in cells:
        if (ix, iy) in free_cells:
            by_y.setdefault(iy, []).append((ix, cell))

    merged: list[tuple[float, float, float, float]] = []
    active: dict[tuple[float, float], tuple[float, float, float, float]] = {}
    all_y = sorted({iy for _, iy, _ in cells})
    for iy in all_y:
        row_runs: dict[tuple[float, float], tuple[float, float, float, float]] = {}
        row = sorted(by_y.get(iy, []), key=lambda item: item[0])
        run_start: Rect | None = None
        run_end: Rect | None = None
        previous_ix: int | None = None
        for ix, cell in row:
            if run_start is None or previous_ix is None or ix != previous_ix + 1:
                if run_start is not None and run_end is not None:
                    row_runs[(run_start.x0, run_end.x1)] = (run_start.x0, run_start.y0, run_end.x1, run_end.y1)
                run_start = cell
            run_end = cell
            previous_ix = ix
        if run_start is not None and run_end is not None:
            row_runs[(run_start.x0, run_end.x1)] = (run_start.x0, run_start.y0, run_end.x1, run_end.y1)

        next_active: dict[tuple[float, float], tuple[float, float, float, float]] = {}
        for key, rect_tuple in row_runs.items():
            if key in active and abs(active[key][3] - rect_tuple[1]) <= 1e-9:
                old = active[key]
                next_active[key] = (old[0], old[1], old[2], rect_tuple[3])
            else:
                next_active[key] = rect_tuple
        for key, rect_tuple in active.items():
            if key not in row_runs:
                merged.append(rect_tuple)
        active = next_active
    merged.extend(active.values())

    regions = []
    for x0, y0, x1, y1 in merged:
        rect = Rect(x0, y0, x1, y1)
        if rect.area <= 1e-9:
            continue
        regions.append({"area_um2": round(rect.area, 6), "rect": _rect_dict(rect)})
    regions.sort(key=lambda item: float(item["area_um2"]), reverse=True)
    return regions


def _coarse_role_map(
    boundary: Rect,
    placement_regions: list[OccupancyRegion],
    module_regions: list[OccupancyRegion],
    coarse_columns: int,
) -> dict[str, object]:
    columns = max(8, coarse_columns)
    rows = max(6, min(32, round(columns * boundary.height / max(boundary.width, 1e-9))))
    chars = "123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz"
    legend: dict[str, str] = {}
    reverse_legend: dict[str, str] = {}

    def symbol(label: str) -> str:
        if label in reverse_legend:
            return reverse_legend[label]
        char = chars[len(reverse_legend)] if len(reverse_legend) < len(chars) else "#"
        reverse_legend[label] = char
        legend[char] = label
        return char

    map_rows: list[str] = []
    dx = boundary.width / columns
    dy = boundary.height / rows
    for row in reversed(range(rows)):
        text = []
        y = boundary.y0 + (row + 0.5) * dy
        for col in range(columns):
            x = boundary.x0 + (col + 0.5) * dx
            point_cell = Rect(x, y, x, y)
            placement_hits = [region for region in placement_regions if _contains_center(region.rect, point_cell)]
            if not placement_hits:
                text.append(".")
                continue
            module_hits = [region for region in module_regions if _contains_center(region.rect, point_cell)]
            if module_hits:
                label = min(module_hits, key=lambda region: (region.area, region.name)).name
            else:
                label = min(placement_hits, key=lambda region: (region.area, region.role)).role
            text.append(symbol(label))
        map_rows.append("".join(text))
    return {
        "origin": "top_left",
        "columns": columns,
        "rows": rows,
        "empty_symbol": ".",
        "legend": legend,
        "rows_text": map_rows,
    }


def _optimization_targets(
    empty_regions: list[dict[str, object]],
    placement_regions: list[OccupancyRegion],
    boundary: Rect,
) -> list[dict[str, object]]:
    targets: list[dict[str, object]] = []
    for item in empty_regions[:8]:
        rect = _rect_from_dict(item["rect"])
        nearest = sorted(
            (
                (max(0.0, rect.spacing_to(region.rect)), region.role, region.name)
                for region in placement_regions
            ),
            key=lambda entry: (entry[0], entry[1], entry[2]),
        )[:4]
        edge_flags = _edge_flags(rect, boundary)
        targets.append({
            "area_um2": item["area_um2"],
            "rect": item["rect"],
            "touches_boundary": edge_flags,
            "nearest_filled_regions": [
                {"spacing_um": round(spacing, 6), "role": role, "name": name}
                for spacing, role, name in nearest
            ],
        })
    return targets


def _edge_empty_area(empty_regions: list[dict[str, object]], boundary: Rect) -> float:
    area = 0.0
    for item in empty_regions:
        rect = _rect_from_dict(item["rect"])
        if any(_edge_flags(rect, boundary).values()):
            area += rect.area
    return area


def _edge_flags(rect: Rect, boundary: Rect) -> dict[str, bool]:
    return {
        "left": abs(rect.x0 - boundary.x0) <= 1e-9,
        "right": abs(rect.x1 - boundary.x1) <= 1e-9,
        "bottom": abs(rect.y0 - boundary.y0) <= 1e-9,
        "top": abs(rect.y1 - boundary.y1) <= 1e-9,
    }


def _contains_center(rect: Rect, cell: Rect) -> bool:
    point = cell.center
    return rect.x0 <= point.x <= rect.x1 and rect.y0 <= point.y <= rect.y1


def _clip_rect(rect: Rect, boundary: Rect) -> Rect | None:
    x0 = max(rect.x0, boundary.x0)
    y0 = max(rect.y0, boundary.y0)
    x1 = min(rect.x1, boundary.x1)
    y1 = min(rect.y1, boundary.y1)
    if x1 <= x0 or y1 <= y0:
        return None
    return Rect(x0, y0, x1, y1)


def _rect_dict(rect: Rect) -> dict[str, float]:
    return {
        "x0": round(rect.x0, 6),
        "y0": round(rect.y0, 6),
        "x1": round(rect.x1, 6),
        "y1": round(rect.y1, 6),
        "width": round(rect.width, 6),
        "height": round(rect.height, 6),
    }


def _rect_from_dict(data: object) -> Rect:
    rect = data if isinstance(data, dict) else {}
    return Rect(
        float(rect.get("x0", 0.0)),
        float(rect.get("y0", 0.0)),
        float(rect.get("x1", 0.0)),
        float(rect.get("y1", 0.0)),
    )


def _round_area_map(values: dict[str, float]) -> dict[str, float]:
    return {key: round(value, 6) for key, value in sorted(values.items())}


def _escape_svg(text: str) -> str:
    return (
        text.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )
