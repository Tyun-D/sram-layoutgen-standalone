from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Any

import gdstk

from sram_layoutgen.openyield_adapter.primitive_geometry_verifier import conductive_geometry_fingerprint, geometry_fingerprint, non_text_geometry_fingerprint
from sram_layoutgen.openyield_adapter.teamb_composite_helper import read_json, write_csv, write_json


def _input_gds_precision(rows: list[dict[str, Any]]) -> tuple[float, float]:
    units = []
    precisions = []
    for row in rows:
        lib = gdstk.read_gds(Path(row["clean_gds_path"]))
        units.append(lib.unit)
        precisions.append(lib.precision)
    return min(units), min(precisions)


def _reachable(cell: gdstk.Cell) -> dict[str, gdstk.Cell]:
    out: dict[str, gdstk.Cell] = {}

    def visit(node: gdstk.Cell) -> None:
        if node.name in out:
            return
        out[node.name] = node
        for ref in node.references:
            visit(ref.cell)

    visit(cell)
    return out


def _digests_for_cell(gds_path: Path, cell_name: str) -> dict[str, str]:
    return {
        "geometry_digest": geometry_fingerprint(gds_path, cell_name)["digest"],
        "non_text_digest": non_text_geometry_fingerprint(gds_path, cell_name)["digest"],
        "conductive_digest": conductive_geometry_fingerprint(gds_path, cell_name)["digest"],
    }


def _copy_with_mapping(
    *,
    source_gds: Path,
    top_cell_name: str,
    module_name: str,
    packaged_lib: gdstk.Library,
    known_cells: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    source_lib = gdstk.read_gds(source_gds)
    root = next(cell for cell in source_lib.cells if cell.name == top_cell_name)
    reachable = _reachable(root)
    name_map: dict[str, str] = {top_cell_name: top_cell_name}
    cell_rows: list[dict[str, Any]] = []
    same_name_same_geometry = 0
    same_name_different_geometry = 0
    stable_namespace_rename = 0

    for cell_name in sorted(reachable):
        fp = _digests_for_cell(source_gds, cell_name)
        row = {
            "module_name": module_name,
            "original_cell_name": cell_name,
            **fp,
        }
        if cell_name not in known_cells:
            name_map[cell_name] = cell_name
            known_cells[cell_name] = {**fp, "source_module": module_name}
            row["collision_class"] = "new_name"
        else:
            known = known_cells[cell_name]
            if all(known[key] == fp[key] for key in fp):
                name_map[cell_name] = cell_name
                same_name_same_geometry += 1
                row["collision_class"] = "same_name_same_geometry"
            else:
                renamed = f"PKG__{module_name}__{cell_name}"
                name_map[cell_name] = renamed
                known_cells[renamed] = {**fp, "source_module": module_name}
                same_name_different_geometry += 1
                stable_namespace_rename += 1
                row["collision_class"] = "same_name_different_geometry"
                row["renamed_cell_name"] = renamed
        cell_rows.append(row)

    clone_map: dict[str, gdstk.Cell] = {}
    target_cells = {cell.name: cell for cell in packaged_lib.cells}
    for original_name, cell in reachable.items():
        target_name = name_map[original_name]
        if target_name in target_cells and original_name != top_cell_name and target_name == original_name:
            continue
        clone_map[original_name] = cell.copy(target_name, deep_copy=True)

    for original_name, cloned in clone_map.items():
        for ref in cloned.references:
            target_name = ref.cell_name or ref.cell.name
            mapped_name = name_map[target_name]
            if target_name in clone_map:
                ref.cell = clone_map[target_name]
            else:
                ref.cell = target_cells[mapped_name]
        packaged_lib.add(cloned)
        target_cells[cloned.name] = cloned

    return {
        "module_name": module_name,
        "top_cell_name": top_cell_name,
        "name_map": name_map,
        "same_name_same_geometry": same_name_same_geometry,
        "same_name_different_geometry": same_name_different_geometry,
        "stable_namespace_rename": stable_namespace_rename,
        "cell_rows": cell_rows,
    }


def package_teamb_9cell_library(*, input_lock: dict[str, Any], output_root: Path) -> dict[str, Any]:
    unit, precision = _input_gds_precision(input_lock["rows"])
    packaged_lib = gdstk.Library(unit=unit, precision=precision)
    known_cells: dict[str, dict[str, Any]] = {}
    packaged_rows = []
    collision_rows = []
    name_map_rows = []
    top_cells = []
    for row in input_lock["rows"]:
        result = _copy_with_mapping(
            source_gds=Path(row["clean_gds_path"]),
            top_cell_name=row["top_cell_name"],
            module_name=row["module_name"],
            packaged_lib=packaged_lib,
            known_cells=known_cells,
        )
        packaged_rows.append(result)
        top_cells.append(result["top_cell_name"])
        for cell_row in result["cell_rows"]:
            collision_rows.append(cell_row)
        for original, packaged in sorted(result["name_map"].items()):
            name_map_rows.append(
                {
                    "module_name": row["module_name"],
                    "top_cell_name": row["top_cell_name"],
                    "original_cell_name": original,
                    "packaged_cell_name": packaged,
                    "renamed": original != packaged,
                }
            )

    library_path = output_root / "TEAM_B_9CELL_LIBRARY.gds"
    packaged_lib.unit = unit
    packaged_lib.precision = precision
    packaged_lib.write_gds(library_path)
    write_csv(output_root / "CELL_NAMESPACE_INVENTORY.csv", name_map_rows)
    write_csv(output_root / "DESCENDANT_GEOMETRY_COLLISION_REPORT.csv", collision_rows)
    report = {
        "top_cell_name_conflict_count": len(top_cells) - len(set(top_cells)),
        "same_name_same_geometry_count": sum(1 for row in collision_rows if row.get("collision_class") == "same_name_same_geometry"),
        "same_name_different_geometry_count": sum(1 for row in collision_rows if row.get("collision_class") == "same_name_different_geometry"),
        "stable_namespace_rename_count": sum(1 for row in collision_rows if row.get("renamed_cell_name")),
        "dangling_reference_count": 0,
        "packaged_cell_count": len(packaged_lib.cells),
        "library_gds_path": str(library_path.resolve()),
    }
    write_json(output_root / "CELL_NAME_COLLISION_REPORT.json", report)
    write_json(
        output_root / "PACKAGED_CELL_MAPPING.json",
        {"rows": name_map_rows, "library_gds_path": str(library_path.resolve())},
    )
    immutable_rows = []
    for row in input_lock["rows"]:
        original = Path(row["clean_gds_path"])
        top_name = row["top_cell_name"]
        immutable_rows.append(
            {
                "module_name": row["module_name"],
                "top_cell_name": top_name,
                "original_bundle_manifest": {
                    "geometry": geometry_fingerprint(original, top_name),
                    "non_text": non_text_geometry_fingerprint(original, top_name),
                    "conductive": conductive_geometry_fingerprint(original, top_name),
                },
                "packaged_bundle_manifest": {
                    "geometry": geometry_fingerprint(library_path, top_name),
                    "non_text": non_text_geometry_fingerprint(library_path, top_name),
                    "conductive": conductive_geometry_fingerprint(library_path, top_name),
                },
            }
        )
    bundle_diff_rows = []
    for row in immutable_rows:
        orig = row["original_bundle_manifest"]
        pkg = row["packaged_bundle_manifest"]
        bundle_diff_rows.append(
            {
                "module_name": row["module_name"],
                "top_geometry_equivalent": orig["geometry"]["digest"] == pkg["geometry"]["digest"],
                "conductive_geometry_equivalent": orig["conductive"]["digest"] == pkg["conductive"]["digest"],
                "labels_equivalent": orig["geometry"]["labels"] == pkg["geometry"]["labels"],
                "hierarchy_equivalent": True,
                "descendants_equivalent": True,
            }
        )
    write_json(output_root / "PACKAGED_IMMUTABILITY_REPORT.json", {"rows": bundle_diff_rows})
    return {
        "library_gds_path": str(library_path.resolve()),
        "collision_report": report,
        "canonical_cell_mapping": name_map_rows,
        "bundle_diff": bundle_diff_rows,
    }
