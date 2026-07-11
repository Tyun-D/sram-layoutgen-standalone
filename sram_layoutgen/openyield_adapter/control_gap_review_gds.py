from __future__ import annotations

from pathlib import Path
from typing import Any

import gdstk


DEBUG_TEXT_LAYER = 296
DEBUG_BOX_LAYER = 297
REVIEW_BOX_LAYER = 298


def build_control_gap_review_gds(
    *,
    layoutgen_golden: Path,
    openram_reference_gds: Path,
    openyield_module_gds_dir: Path,
    out_review_gds: Path,
    out_clean_gds: Path,
    out_debug_gds: Path,
    floorplan_plan: dict[str, Any],
) -> dict[str, Any]:
    openram_lib = gdstk.read_gds(openram_reference_gds)
    golden_lib = gdstk.read_gds(layoutgen_golden)
    candidate_names = [
        "CONTROL_LOGIC",
        "DFF_ROW",
        "DELAY_CHAIN",
        "GATED_CLOCK_PATH",
        "PRECHARGE_ENABLE_PATH",
        "SENSE_ENABLE_PATH",
        "WORDLINE_ENABLE_PATH",
        "WRITE_ENABLE_PATH",
    ]
    candidate_libs = []
    for name in candidate_names:
        path = openyield_module_gds_dir / name / f"{name}.gds"
        if path.exists():
            candidate_libs.append((name, gdstk.read_gds(path)))

    review_lib = gdstk.Library(unit=golden_lib.unit, precision=golden_lib.precision)
    top = review_lib.new_cell("M12C_control_logic_gap_review")
    clean = review_lib.new_cell("M12C_control_logic_gap_clean")
    debug = review_lib.new_cell("M12C_control_logic_gap_debug")

    cursor_x = 0.0
    cursor_y = 0.0
    spacing = 80.0
    cursor_x = _place_library(review_lib, top, clean, debug, openram_lib, "OPENRAM_REF", cursor_x, cursor_y, add_labels=True)
    cursor_x += spacing
    cursor_x = _place_library(review_lib, top, clean, debug, golden_lib, "LAYOUTGEN_GOLDEN", cursor_x, cursor_y, add_labels=True)
    cursor_x += spacing

    cluster_x = cursor_x
    cluster_y = cursor_y
    for index, (name, lib) in enumerate(candidate_libs):
        dx = cluster_x + (index % 2) * 25.0
        dy = cluster_y - (index // 2) * 25.0
        _place_library(review_lib, top, clean, debug, lib, f"OPENYIELD_{name}", dx, dy, add_labels=True)

    _add_candidate_region_boxes(top, clean, debug, floorplan_plan, cluster_x, cursor_y)
    out_review_gds.parent.mkdir(parents=True, exist_ok=True)
    review_lib.write_gds(out_review_gds)

    clean_lib = gdstk.read_gds(out_review_gds)
    _strip_text(clean_lib)
    clean_lib.write_gds(out_clean_gds)

    debug_lib = gdstk.read_gds(out_review_gds)
    debug_lib.write_gds(out_debug_gds)

    return {
        "review_gds_generated": True,
        "review_gds_parsed": _gds_parsed(out_review_gds) and _gds_parsed(out_clean_gds) and _gds_parsed(out_debug_gds),
        "review_gds_path": str(out_review_gds),
        "clean_review_gds_path": str(out_clean_gds),
        "annotated_debug_gds_path": str(out_debug_gds),
    }


def _place_library(
    review_lib: gdstk.Library,
    top: gdstk.Cell,
    clean: gdstk.Cell,
    debug: gdstk.Cell,
    source_lib: gdstk.Library,
    prefix: str,
    dx: float,
    dy: float,
    add_labels: bool,
) -> float:
    cell_map: dict[str, gdstk.Cell] = {}
    for cell in source_lib.cells:
        new_name = f"{prefix}__{cell.name}"
        cloned = gdstk.Cell(new_name)
        for polygon in cell.polygons:
            cloned.add(polygon.copy())
        for path in cell.paths:
            cloned.add(path.copy())
        for label in cell.labels:
            cloned.add(label.copy())
        review_lib.add(cloned)
        cell_map[cell.name] = cloned
    for cell in source_lib.cells:
        cloned = cell_map[cell.name]
        for ref in cell.references:
            target = cell_map.get(ref.cell_name)
            if target is None:
                continue
            cloned.add(
                gdstk.Reference(
                    target,
                    origin=tuple(ref.origin),
                    rotation=ref.rotation,
                    magnification=ref.magnification,
                    x_reflection=ref.x_reflection,
                )
            )
    source_top = source_lib.top_level()[0]
    top_cell = cell_map[source_top.name]
    top.add(gdstk.Reference(top_cell, origin=(dx, dy)))
    clean.add(gdstk.Reference(top_cell, origin=(dx, dy)))
    debug.add(gdstk.Reference(top_cell, origin=(dx, dy)))
    bbox = top_cell.bounding_box()
    if bbox is not None:
        top.add(gdstk.rectangle((bbox[0][0] + dx, bbox[0][1] + dy), (bbox[1][0] + dx, bbox[1][1] + dy), layer=REVIEW_BOX_LAYER, datatype=0))
        clean.add(gdstk.rectangle((bbox[0][0] + dx, bbox[0][1] + dy), (bbox[1][0] + dx, bbox[1][1] + dy), layer=REVIEW_BOX_LAYER, datatype=0))
        if add_labels:
            debug.add(gdstk.Label(prefix, ((bbox[0][0] + bbox[1][0]) / 2 + dx, bbox[1][1] + dy + 5.0), layer=DEBUG_TEXT_LAYER, texttype=0))
            top.add(gdstk.Label(prefix, ((bbox[0][0] + bbox[1][0]) / 2 + dx, bbox[1][1] + dy + 5.0), layer=DEBUG_TEXT_LAYER, texttype=0))
    return dx + ((bbox[1][0] - bbox[0][0]) if bbox is not None else 0.0)


def _add_candidate_region_boxes(
    top: gdstk.Cell,
    clean: gdstk.Cell,
    debug: gdstk.Cell,
    floorplan_plan: dict[str, Any],
    anchor_x: float,
    anchor_y: float,
) -> None:
    top.add(gdstk.rectangle((anchor_x - 10, anchor_y - 70), (anchor_x + 70, anchor_y + 15), layer=DEBUG_BOX_LAYER, datatype=0))
    clean.add(gdstk.rectangle((anchor_x - 10, anchor_y - 70), (anchor_x + 70, anchor_y + 15), layer=DEBUG_BOX_LAYER, datatype=0))
    debug.add(gdstk.rectangle((anchor_x - 10, anchor_y - 70), (anchor_x + 70, anchor_y + 15), layer=DEBUG_BOX_LAYER, datatype=0))
    debug.add(gdstk.Label("CANDIDATE_CONTROL_REGION", (anchor_x + 30, anchor_y + 20), layer=DEBUG_TEXT_LAYER, texttype=0))
    debug.add(gdstk.Label("OPENRAM region is reference only", (anchor_x - 60, anchor_y + 35), layer=DEBUG_TEXT_LAYER, texttype=0))
    debug.add(gdstk.Label("Layoutgen control gap placeholder", (anchor_x + 30, anchor_y - 75), layer=DEBUG_TEXT_LAYER, texttype=0))
    for index, row in enumerate(floorplan_plan["interface_nets"][:8]):
        debug.add(gdstk.Label(f"{row['net_name']} -> {row['adjacent_module']}", (anchor_x + 80, anchor_y - index * 6), layer=DEBUG_TEXT_LAYER, texttype=0))


def _strip_text(lib: gdstk.Library) -> None:
    clean_lib = gdstk.Library(unit=lib.unit, precision=lib.precision)
    cell_map: dict[str, gdstk.Cell] = {}
    for cell in lib.cells:
        cloned = gdstk.Cell(cell.name)
        for polygon in cell.polygons:
            cloned.add(polygon.copy())
        for path in cell.paths:
            cloned.add(path.copy())
        clean_lib.add(cloned)
        cell_map[cell.name] = cloned
    for cell in lib.cells:
        cloned = cell_map[cell.name]
        for ref in cell.references:
            target = cell_map.get(ref.cell_name)
            if target is None:
                continue
            cloned.add(
                gdstk.Reference(
                    target,
                    origin=tuple(ref.origin),
                    rotation=ref.rotation,
                    magnification=ref.magnification,
                    x_reflection=ref.x_reflection,
                )
            )
    lib.cells.clear()
    for cell in clean_lib.cells:
        lib.add(cell)


def _gds_parsed(path: Path) -> bool:
    try:
        gdstk.read_gds(path)
    except Exception:
        return False
    return True
