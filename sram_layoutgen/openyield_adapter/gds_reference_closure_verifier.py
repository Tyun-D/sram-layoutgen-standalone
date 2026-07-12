from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any

import gdstk


def verify_gds_reference_closure(gds_path: Path, expected_top_name: str | None = None) -> dict[str, Any]:
    lib = gdstk.read_gds(gds_path)
    structure_names = [cell.name for cell in lib.cells]
    structure_name_set = set(structure_names)
    duplicate_names = sorted(name for name in structure_name_set if structure_names.count(name) > 1)
    reference_rows: list[dict[str, Any]] = []
    referenced_targets: set[str] = set()
    missing_sref_targets: list[str] = []
    missing_aref_targets: list[str] = []

    adjacency: dict[str, list[str]] = {cell.name: [] for cell in lib.cells}
    for cell in lib.cells:
        for index, reference in enumerate(cell.references):
            target = reference.cell_name or reference.cell.name
            repetition = getattr(reference, "repetition", None)
            columns = int(getattr(repetition, "columns", 1) or 1)
            rows = int(getattr(repetition, "rows", 1) or 1)
            reference_type = "AREF" if columns > 1 or rows > 1 else "SREF"
            target_exists = target in structure_name_set
            reference_rows.append(
                {
                    "source_cell": cell.name,
                    "reference_index": index,
                    "reference_type": reference_type,
                    "target_cell": target,
                    "target_exists": target_exists,
                    "columns": columns,
                    "rows": rows,
                }
            )
            referenced_targets.add(target)
            if target_exists:
                adjacency[cell.name].append(target)
            elif reference_type == "AREF":
                missing_aref_targets.append(target)
            else:
                missing_sref_targets.append(target)

    top_level_cells = sorted(name for name in structure_names if name not in referenced_targets)
    if expected_top_name is not None and expected_top_name not in top_level_cells and expected_top_name in structure_name_set:
        top_level_cells = [expected_top_name]

    visited: set[str] = set()
    cycle_count = 0
    max_depth = 0

    def dfs(node: str, stack: set[str], depth: int) -> None:
        nonlocal cycle_count, max_depth
        visited.add(node)
        max_depth = max(max_depth, depth)
        stack.add(node)
        for child in adjacency.get(node, []):
            if child in stack:
                cycle_count += 1
                continue
            if child not in visited:
                dfs(child, stack, depth + 1)
        stack.remove(node)

    for top in top_level_cells:
        if top in structure_name_set and top not in visited:
            dfs(top, set(), 0)

    unreachable_cells = sorted(name for name in structure_names if name not in visited)
    before_after_root_mapping: dict[str, dict[str, str]] = {}
    for row in reference_rows:
        target = row["target_cell"]
        if target.startswith("DEBUG_BEFORE__") or target.startswith("REUSABLE_AFTER__"):
            parts = target.split("__", 2)
            if len(parts) == 3:
                side, root_cell, _ = parts
                entry = before_after_root_mapping.setdefault(root_cell, {})
                entry["before_root_name" if side == "DEBUG_BEFORE" else "after_root_name"] = target

    report = {
        "gds_path": str(gds_path),
        "library_structure_names": structure_names,
        "duplicate_structure_names": duplicate_names,
        "duplicate_structure_name_count": len(duplicate_names),
        "all_sref_targets": sorted(row["target_cell"] for row in reference_rows if row["reference_type"] == "SREF"),
        "all_aref_targets": sorted(row["target_cell"] for row in reference_rows if row["reference_type"] == "AREF"),
        "missing_sref_targets": sorted(missing_sref_targets),
        "missing_aref_targets": sorted(missing_aref_targets),
        "missing_sref_target_count": len(missing_sref_targets),
        "missing_aref_target_count": len(missing_aref_targets),
        "missing_reference_target_count": len(missing_sref_targets) + len(missing_aref_targets),
        "reference_count": len(reference_rows),
        "structure_count": len(structure_names),
        "top_level_cells": top_level_cells,
        "top_level_cell_count": len(top_level_cells),
        "top_level_cell_name": top_level_cells[0] if len(top_level_cells) == 1 else None,
        "unreachable_cells": unreachable_cells,
        "reference_cycle_count": cycle_count,
        "reference_depth": max_depth,
        "before_after_root_mapping": before_after_root_mapping,
        "reference_closure_passed": len(duplicate_names) == 0 and len(missing_sref_targets) == 0 and len(missing_aref_targets) == 0,
        "reference_matrix": reference_rows,
    }
    return report


def write_reference_closure_outputs(
    *,
    report: dict[str, Any],
    json_path: Path,
    md_path: Path,
    structure_csv_path: Path,
    reference_csv_path: Path,
) -> None:
    json_path.parent.mkdir(parents=True, exist_ok=True)
    json_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    md_path.write_text(
        "\n".join(
            [
                "# M12C3A4R Review Atlas Reference Closure",
                "",
                f"- structure_count: `{report['structure_count']}`",
                f"- reference_count: `{report['reference_count']}`",
                f"- missing_reference_target_count: `{report['missing_reference_target_count']}`",
                f"- duplicate_structure_name_count: `{report['duplicate_structure_name_count']}`",
                f"- top_level_cell_name: `{report['top_level_cell_name']}`",
                f"- reference_closure_passed: `{report['reference_closure_passed']}`",
                "",
            ]
        ),
        encoding="utf-8",
    )
    with structure_csv_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=["structure_name", "is_top_level", "is_unreachable"])
        writer.writeheader()
        for name in report["library_structure_names"]:
            writer.writerow(
                {
                    "structure_name": name,
                    "is_top_level": name in report["top_level_cells"],
                    "is_unreachable": name in report["unreachable_cells"],
                }
            )
    with reference_csv_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=["source_cell", "reference_index", "reference_type", "target_cell", "target_exists", "columns", "rows"],
        )
        writer.writeheader()
        writer.writerows(report["reference_matrix"])
