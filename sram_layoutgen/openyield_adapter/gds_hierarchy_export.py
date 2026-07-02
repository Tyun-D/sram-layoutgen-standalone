from __future__ import annotations

import json
from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import gdstk


def _json_dump(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8", newline="\n")


@dataclass(frozen=True)
class SourceCell:
    path: Path
    cell_name: str
    cell: gdstk.Cell


@dataclass(frozen=True)
class TopCellImportPlan:
    module_name: str
    module_gds_path: Path
    root_cell_name: str
    instance_name: str
    origin_x: float
    origin_y: float
    orientation: str


def read_gds_cells(path: Path) -> list[gdstk.Cell]:
    lib = gdstk.read_gds(path)
    return list(lib.cells)


def build_source_registry(paths: list[Path]) -> dict[str, list[SourceCell]]:
    registry: dict[str, list[SourceCell]] = defaultdict(list)
    seen_paths: set[Path] = set()
    for raw_path in paths:
        path = raw_path.resolve()
        if path in seen_paths or not path.exists() or path.suffix.lower() != ".gds":
            continue
        seen_paths.add(path)
        try:
            cells = read_gds_cells(path)
        except Exception:
            continue
        for cell in cells:
            registry[str(cell.name)].append(SourceCell(path=path, cell_name=str(cell.name), cell=cell))
    return dict(registry)


def collect_search_paths(module_gds_paths: list[Path], technology_gds_root: Path) -> list[Path]:
    paths = [path.resolve() for path in module_gds_paths if path.exists()]
    if technology_gds_root.exists():
        paths.extend(sorted(path.resolve() for path in technology_gds_root.rglob("*.gds")))
    return paths


def build_top_level_library(
    import_plans: list[TopCellImportPlan],
    search_paths: list[Path],
    top_cell_name: str = "openyield_top_level_candidate",
) -> tuple[gdstk.Library, dict[str, Any]]:
    registry = build_source_registry(search_paths)
    library = gdstk.Library()
    top = library.new_cell(top_cell_name)
    imported: dict[tuple[str, Path, str], gdstk.Cell] = {}
    import_state: dict[tuple[str, Path, str], str] = {}
    used_target_names: set[str] = {top_cell_name}
    manifest: dict[str, Any] = {
        "hierarchy_export_strategy": "complete_hierarchy_prefixed_import",
        "flattened_module_wrappers": False,
        "cell_renaming_map": {},
        "module_top_cell_map": {},
        "unresolved_references": [],
        "self_reference_redirects": [],
        "cycle_errors": [],
        "registry_source_files": sorted(str(path) for path in search_paths),
    }
    for plan in import_plans:
        root_candidates = registry.get(plan.root_cell_name, [])
        root_origin = next((item for item in root_candidates if item.path.resolve() == plan.module_gds_path.resolve()), None)
        if root_origin is None:
            raise ValueError(f"Could not resolve root cell {plan.root_cell_name} from {plan.module_gds_path}")
        imported_root = _import_cell_hierarchy(
            module_prefix=plan.module_name,
            origin=root_origin,
            registry=registry,
            library=library,
            imported=imported,
            import_state=import_state,
            used_target_names=used_target_names,
            manifest=manifest,
        )
        manifest["module_top_cell_map"][plan.module_name] = imported_root.name
        top.add(gdstk.Reference(imported_root, origin=(plan.origin_x, plan.origin_y)))
    return library, manifest


def diagnose_gds_hierarchy(
    gds_path: Path,
    module_gds_paths: dict[str, Path],
    technology_gds_root: Path,
    module_gds_inventory_rows: list[dict[str, str]] | None = None,
) -> dict[str, Any]:
    lib = gdstk.read_gds(gds_path)
    cells = list(lib.cells)
    cell_names = {str(cell.name) for cell in cells}
    refs_by_cell: dict[str, list[str]] = {}
    missing_refs: set[str] = set()
    self_refs: list[str] = []
    incoming: dict[str, set[str]] = defaultdict(set)
    layer_summary: Counter[str] = Counter()
    for cell in cells:
        refs = [str(ref.cell_name) for ref in cell.references]
        refs_by_cell[str(cell.name)] = refs
        for ref_name in refs:
            incoming[ref_name].add(str(cell.name))
            if ref_name == str(cell.name):
                self_refs.append(str(cell.name))
            if ref_name not in cell_names:
                missing_refs.add(ref_name)
        for polygon in cell.polygons:
            layer_summary[f"{polygon.layer}/{polygon.datatype}"] += 1
    cycles = _find_cycles(refs_by_cell, cell_names)
    registry = build_source_registry(collect_search_paths(list(module_gds_paths.values()), technology_gds_root))
    missing_candidates = {
        ref_name: [str(item.path) for item in registry.get(ref_name, [])]
        for ref_name in sorted(missing_refs)
    }
    missing_by_module = {}
    top = next((cell for cell in cells if str(cell.name) == "openyield_top_level_candidate"), cells[0] if cells else None)
    if top is not None:
        for ref in top.references:
            module_name = str(ref.cell_name)
            module_missing = sorted(_collect_missing_from_root(module_name, refs_by_cell, cell_names))
            if module_missing:
                missing_by_module[module_name] = module_missing
    module_sanity = {}
    if module_gds_inventory_rows:
        module_sanity = {
            row["module"]: {
                "parser_sanity_status": row.get("parser_sanity_status"),
                "sanity_check_status": row.get("sanity_check_status"),
                "gds_generated": row.get("gds_generated"),
                "gds_path": row.get("gds_path"),
            }
            for row in module_gds_inventory_rows
            if row.get("module")
        }
    return {
        "gds_path": str(gds_path),
        "cell_count": len(cells),
        "top_cell_name": str(top.name) if top is not None else None,
        "cell_names": sorted(cell_names),
        "refs_by_cell": {name: refs_by_cell[name] for name in sorted(refs_by_cell)},
        "missing_referenced_cells": sorted(missing_refs),
        "missing_reference_candidate_sources": missing_candidates,
        "missing_references_by_top_module": missing_by_module,
        "self_references": sorted(set(self_refs)),
        "cycles": cycles,
        "layer_summary": dict(sorted(layer_summary.items())),
        "module_gds_sanity": module_sanity,
    }


def write_hierarchy_diagnosis(report: dict[str, Any], out_json: Path, out_md: Path) -> None:
    _json_dump(out_json, report)
    lines = [
        "# Top GDS Hierarchy Diagnosis",
        "",
        f"- gds_path: `{report['gds_path']}`",
        f"- cell_count: `{report['cell_count']}`",
        f"- top_cell_name: `{report['top_cell_name']}`",
        f"- missing_referenced_cells_count: `{len(report['missing_referenced_cells'])}`",
        f"- self_reference_count: `{len(report['self_references'])}`",
        f"- cycle_count: `{len(report['cycles'])}`",
        "",
        "## Missing Referenced Cells",
        "",
    ]
    for name in report["missing_referenced_cells"]:
        candidates = report["missing_reference_candidate_sources"].get(name, [])
        lines.append(f"- `{name}`")
        if candidates:
            lines.append(f"  candidate_sources: `{candidates}`")
    lines.extend(["", "## Self References", ""])
    lines.extend(f"- `{name}`" for name in report["self_references"])
    lines.extend(["", "## Cycles", ""])
    if report["cycles"]:
        lines.extend(f"- `{cycle}`" for cycle in report["cycles"])
    else:
        lines.append("- none")
    lines.extend(["", "## Missing References By Top Module", ""])
    for module, missing in sorted(report["missing_references_by_top_module"].items()):
        lines.append(f"- `{module}`: `{missing}`")
    _write_text(out_md, "\n".join(lines) + "\n")


def _import_cell_hierarchy(
    module_prefix: str,
    origin: SourceCell,
    registry: dict[str, list[SourceCell]],
    library: gdstk.Library,
    imported: dict[tuple[str, Path, str], gdstk.Cell],
    import_state: dict[tuple[str, Path, str], str],
    used_target_names: set[str],
    manifest: dict[str, Any],
) -> gdstk.Cell:
    key = (module_prefix, origin.path.resolve(), origin.cell_name)
    existing = imported.get(key)
    if existing is not None:
        return existing
    state = import_state.get(key)
    if state == "visiting":
        cycle = {"module_prefix": module_prefix, "path": str(origin.path), "cell_name": origin.cell_name}
        manifest["cycle_errors"].append(cycle)
        raise ValueError(f"Cyclic reference detected while importing {origin.cell_name} from {origin.path}")
    import_state[key] = "visiting"
    target_name = _allocate_target_name(module_prefix, origin, used_target_names)
    cell = gdstk.Cell(target_name)
    imported[key] = cell
    manifest["cell_renaming_map"][f"{origin.path}:{origin.cell_name}"] = target_name
    for polygon in origin.cell.polygons:
        cell.add(polygon.copy())
    for path in origin.cell.paths:
        cell.add(path.copy())
    for label in origin.cell.labels:
        cell.add(label.copy())
    for reference in origin.cell.references:
        ref_name = str(reference.cell_name)
        resolved = _resolve_reference_target(module_prefix, origin, ref_name, registry)
        if resolved is None:
            manifest["unresolved_references"].append(
                {
                    "module_prefix": module_prefix,
                    "from_path": str(origin.path),
                    "from_cell": origin.cell_name,
                    "reference_name": ref_name,
                }
            )
            continue
        if resolved.path.resolve() == origin.path.resolve() and resolved.cell_name == origin.cell_name:
            manifest["cycle_errors"].append(
                {
                    "module_prefix": module_prefix,
                    "from_path": str(origin.path),
                    "from_cell": origin.cell_name,
                    "reference_name": ref_name,
                }
            )
            raise ValueError(f"Unresolved self-reference for {origin.cell_name} in {origin.path}")
        target_cell = _import_cell_hierarchy(module_prefix, resolved, registry, library, imported, import_state, used_target_names, manifest)
        new_reference = reference.copy()
        new_reference.cell = target_cell
        cell.add(new_reference)
        if ref_name == origin.cell_name and (resolved.path.resolve() != origin.path.resolve() or resolved.cell_name != origin.cell_name):
            manifest["self_reference_redirects"].append(
                {
                    "module_prefix": module_prefix,
                    "from_path": str(origin.path),
                    "from_cell": origin.cell_name,
                    "reference_name": ref_name,
                    "redirected_to_path": str(resolved.path),
                    "redirected_to_cell": resolved.cell_name,
                }
            )
    library.add(cell)
    import_state[key] = "done"
    return cell


def _resolve_reference_target(module_prefix: str, origin: SourceCell, ref_name: str, registry: dict[str, list[SourceCell]]) -> SourceCell | None:
    candidates = registry.get(ref_name, [])
    if not candidates:
        return None
    same_file = [item for item in candidates if item.path.resolve() == origin.path.resolve()]
    non_self_same_file = [item for item in same_file if item.cell_name != origin.cell_name]
    if non_self_same_file:
        return non_self_same_file[0]
    if same_file and ref_name != origin.cell_name:
        return same_file[0]
    non_module_outputs = [item for item in candidates if "outputs/openyield_module_gds" not in str(item.path)]
    non_self_external = [item for item in non_module_outputs if not (item.path.resolve() == origin.path.resolve() and item.cell_name == origin.cell_name)]
    if non_self_external:
        return non_self_external[0]
    non_self = [item for item in candidates if not (item.path.resolve() == origin.path.resolve() and item.cell_name == origin.cell_name)]
    if non_self:
        return non_self[0]
    return same_file[0] if same_file else candidates[0]


def _allocate_target_name(module_prefix: str, origin: SourceCell, used_target_names: set[str]) -> str:
    base = f"{module_prefix}__{origin.cell_name}"
    if base not in used_target_names:
        used_target_names.add(base)
        return base
    stem = origin.path.stem.replace(".", "_").replace("-", "_")
    candidate = f"{base}__{stem}"
    if candidate not in used_target_names:
        used_target_names.add(candidate)
        return candidate
    index = 2
    while True:
        candidate = f"{base}__{stem}_{index}"
        if candidate not in used_target_names:
            used_target_names.add(candidate)
            return candidate
        index += 1


def _find_cycles(refs_by_cell: dict[str, list[str]], cell_names: set[str]) -> list[list[str]]:
    visited: dict[str, int] = {}
    stack: list[str] = []
    cycles: list[list[str]] = []

    def dfs(node: str) -> None:
        visited[node] = 1
        stack.append(node)
        for ref_name in refs_by_cell.get(node, []):
            if ref_name not in cell_names:
                continue
            state = visited.get(ref_name, 0)
            if state == 1:
                index = stack.index(ref_name)
                cycles.append(stack[index:] + [ref_name])
            elif state == 0:
                dfs(ref_name)
        stack.pop()
        visited[node] = 2

    for cell_name in sorted(cell_names):
        if visited.get(cell_name, 0) == 0:
            dfs(cell_name)
    unique: list[list[str]] = []
    seen: set[tuple[str, ...]] = set()
    for cycle in cycles:
        key = tuple(cycle)
        if key not in seen:
            seen.add(key)
            unique.append(cycle)
    return unique


def _collect_missing_from_root(root_name: str, refs_by_cell: dict[str, list[str]], cell_names: set[str]) -> set[str]:
    seen: set[str] = set()
    missing: set[str] = set()

    def dfs(name: str) -> None:
        if name in seen or name not in cell_names:
            return
        seen.add(name)
        for ref_name in refs_by_cell.get(name, []):
            if ref_name not in cell_names:
                missing.add(ref_name)
            else:
                dfs(ref_name)

    dfs(root_name)
    return missing
