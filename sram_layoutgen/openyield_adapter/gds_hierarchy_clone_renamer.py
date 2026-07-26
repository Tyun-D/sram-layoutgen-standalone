from __future__ import annotations

from pathlib import Path

import gdstk


def _reachable_cells(root: gdstk.Cell) -> dict[str, gdstk.Cell]:
    reachable: dict[str, gdstk.Cell] = {}

    def visit(cell: gdstk.Cell) -> None:
        if cell.name in reachable:
            return
        reachable[cell.name] = cell
        for reference in cell.references:
            visit(reference.cell)

    visit(root)
    return reachable


def clone_hierarchy_with_renamed_cells(
    *,
    source_gds: Path,
    root_cell_name: str,
    namespace_prefix: str,
) -> tuple[gdstk.Library, str, dict[str, str]]:
    source_lib = gdstk.read_gds(source_gds)
    root = next(cell for cell in source_lib.cells if cell.name == root_cell_name)
    reachable = _reachable_cells(root)
    cloned_lib = gdstk.Library(unit=source_lib.unit, precision=source_lib.precision)
    name_map = {name: f"{namespace_prefix}__{root_cell_name}__{name}" for name in sorted(reachable)}
    cloned_cells: dict[str, gdstk.Cell] = {}

    for original_name, cell in reachable.items():
        cloned_cells[original_name] = cell.copy(name_map[original_name], deep_copy=True)

    for original_name, cloned in cloned_cells.items():
        for reference in cloned.references:
            target_name = reference.cell_name or reference.cell.name
            reference.cell = cloned_cells[target_name]
        cloned_lib.add(cloned)

    return cloned_lib, name_map[root_cell_name], name_map


def merge_unique_cells(target_lib: gdstk.Library, source_lib: gdstk.Library) -> None:
    existing = {cell.name for cell in target_lib.cells}
    for cell in source_lib.cells:
        if cell.name in existing:
            raise ValueError(f"duplicate structure name detected during merge: {cell.name}")
        target_lib.add(cell)
        existing.add(cell.name)
