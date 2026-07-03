from __future__ import annotations

from pathlib import Path
from typing import Any

import gdstk

from sram_layoutgen.gds_util import inspect_gds_hierarchy, inspect_gds_layers, measure_gds_bbox


def normalize_reference_name(ref_name: str, required_modules: set[str]) -> str:
    text = str(ref_name)
    if text in required_modules:
        return text
    for module in required_modules:
        if text == f"{module}__{module}" or text.startswith(f"{module}__"):
            return module
    return text


def validate_structure_gds(
    gds_path: Path,
    required_modules: list[str],
) -> dict[str, Any]:
    lib = gdstk.read_gds(gds_path)
    cells = list(lib.cells)
    top = next((cell for cell in cells if str(cell.name) == "openyield_structure_complete_sram"), cells[0] if cells else None)
    hierarchy = inspect_gds_hierarchy(gds_path)
    layers = inspect_gds_layers(gds_path)
    bbox = measure_gds_bbox(gds_path)
    top_bbox = None
    if top is not None:
        bounds = top.bounding_box()
        if bounds is not None:
            top_bbox = {
                "x0": round(float(bounds[0][0]), 6),
                "y0": round(float(bounds[0][1]), 6),
                "x1": round(float(bounds[1][0]), 6),
                "y1": round(float(bounds[1][1]), 6),
                "width": round(float(bounds[1][0] - bounds[0][0]), 6),
                "height": round(float(bounds[1][1] - bounds[0][1]), 6),
            }
    if top_bbox is None and bbox is not None:
        top_bbox = bbox.to_dict()
    cell_names = {str(cell.name) for cell in cells}
    refs_by_cell = {str(cell.name): [str(ref.cell_name) for ref in cell.references] for cell in cells}
    self_refs = sorted(name for name, refs in refs_by_cell.items() if name in refs)
    missing_refs = sorted({ref for refs in refs_by_cell.values() for ref in refs if ref not in cell_names})
    top_refs = [str(ref.cell_name) for ref in top.references] if top is not None else []
    normalized_top_refs = sorted({normalize_reference_name(name, set(required_modules)) for name in top_refs})
    cycles: list[str] = []
    visited: set[str] = set()
    stack: list[str] = []

    def dfs(name: str) -> None:
        if name in stack:
            cycles.append(" -> ".join(stack + [name]))
            return
        if name in visited:
            return
        visited.add(name)
        stack.append(name)
        for child in refs_by_cell.get(name, []):
            if child in refs_by_cell:
                dfs(child)
        stack.pop()

    for name in sorted(refs_by_cell):
        dfs(name)

    return {
        "gds_exists": gds_path.exists(),
        "gds_path": str(gds_path),
        "gds_size_bytes": gds_path.stat().st_size if gds_path.exists() else 0,
        "parser_success": True,
        "top_cell_name": str(top.name) if top is not None else None,
        "top_bbox": top_bbox,
        "cell_count": len(cells),
        "instance_count": len(top.references) if top is not None else 0,
        "top_direct_references": top_refs,
        "normalized_top_references": normalized_top_refs,
        "missing_references": missing_refs,
        "self_references": self_refs,
        "reference_cycles": sorted(set(cycles)),
        "hierarchy_summary": hierarchy,
        "layer_summary": layers,
    }
