from __future__ import annotations

from pathlib import Path
from typing import Any

import gdstk


DEBUG_TEXT_LAYER = 296
DEBUG_BOX_LAYER = 297
REF_TEXT_LAYER = 298


def _copy_without_text(lib: gdstk.Library) -> gdstk.Library:
    new_lib = gdstk.Library(unit=lib.unit, precision=lib.precision)
    cell_map: dict[str, gdstk.Cell] = {}
    for cell in lib.cells:
        cloned = gdstk.Cell(cell.name)
        for polygon in cell.polygons:
            cloned.add(polygon.copy())
        for path in cell.paths:
            cloned.add(path.copy())
        new_lib.add(cloned)
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
    return new_lib


def build_control_library_qualification_review_gds(
    *,
    qualification_rows: list[dict[str, Any]],
    out_atlas_gds: Path,
    out_clean_gds: Path,
    out_annotated_gds: Path,
) -> dict[str, Any]:
    atlas = gdstk.Library()
    top = atlas.new_cell("M12C2_control_library_qualification_atlas")
    clean = atlas.new_cell("M12C2_control_library_qualification_clean")
    annotated = atlas.new_cell("M12C2_control_library_qualification_annotated")
    x = 0.0
    y = 0.0
    pitch_x = 16.0
    pitch_y = 12.0
    for index, row in enumerate(qualification_rows):
        gx = x + (index % 4) * pitch_x
        gy = y - (index // 4) * pitch_y
        bbox = ((gx, gy), (gx + 10.0, gy + 8.0))
        top.add(gdstk.rectangle(bbox[0], bbox[1], layer=DEBUG_BOX_LAYER, datatype=0))
        clean.add(gdstk.rectangle(bbox[0], bbox[1], layer=DEBUG_BOX_LAYER, datatype=0))
        annotated.add(gdstk.rectangle(bbox[0], bbox[1], layer=DEBUG_BOX_LAYER, datatype=0))
        clean.add(gdstk.Label(row["logical_module"], (gx + 0.5, gy + 7.2), layer=REF_TEXT_LAYER, texttype=0))
        annotated.add(gdstk.Label(row["logical_module"], (gx + 0.5, gy + 7.2), layer=DEBUG_TEXT_LAYER, texttype=0))
        annotated.add(gdstk.Label(row["candidate_cell_name"] or "NO_CELL", (gx + 0.5, gy + 6.1), layer=DEBUG_TEXT_LAYER, texttype=0))
        annotated.add(gdstk.Label(row["qualification_status"], (gx + 0.5, gy + 5.0), layer=DEBUG_TEXT_LAYER, texttype=0))
        annotated.add(gdstk.Label(f"use={row['allowed_use']}", (gx + 0.5, gy + 3.9), layer=DEBUG_TEXT_LAYER, texttype=0))
        annotated.add(gdstk.Label(row["blocking_reason"][:70], (gx + 0.5, gy + 2.8), layer=DEBUG_TEXT_LAYER, texttype=0))
    out_atlas_gds.parent.mkdir(parents=True, exist_ok=True)
    atlas.write_gds(out_atlas_gds)
    clean_lib = _copy_without_text(gdstk.read_gds(out_atlas_gds))
    clean_lib.write_gds(out_clean_gds)
    atlas.write_gds(out_annotated_gds)
    parsed = True
    for path in [out_atlas_gds, out_clean_gds, out_annotated_gds]:
        try:
            gdstk.read_gds(path)
        except Exception:
            parsed = False
    return {
        "review_gds_generated": True,
        "review_gds_parsed": parsed,
        "qualification_atlas_gds_path": str(out_atlas_gds),
        "qualification_clean_gds_path": str(out_clean_gds),
        "qualification_annotated_gds_path": str(out_annotated_gds),
    }
