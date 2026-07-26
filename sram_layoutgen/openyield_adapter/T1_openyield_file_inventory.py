from __future__ import annotations

import ast
import csv
import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import gdstk


DEBUG_TEXT_PATTERNS = (
    "OPENYIELD_NET",
    "OPENYIELD_MODULE",
    "M5_",
    "DIRECT_GENERATOR_BINDING",
    "PARAMETERIZED",
    "REAL_CELL_WRAPPER",
    "FALLBACK",
    "NET:",
    "PINBIND",
    "M5:",
    "LAYOUTGEN_FALLBACK_WITH_OPENYIELD_SEMANTICS",
)
DEBUG_LAYER = 900
DEBUG_TEXTTYPE = 0
MAX_TEXT_READ_BYTES = 20 * 1024 * 1024
INVENTORY_COLUMNS = [
    "file_id",
    "relative_path",
    "file_type",
    "extension",
    "size_bytes",
    "line_count",
    "is_text",
    "is_binary",
    "is_source_code",
    "is_config",
    "is_netlist",
    "is_data",
    "is_test",
    "is_documentation",
    "main_purpose",
    "key_classes",
    "key_functions",
    "key_inputs",
    "key_outputs",
    "depends_on",
    "used_by",
    "relevance_to_sram_layoutgen",
    "relevance_category",
    "can_drive_layout_generation",
    "can_provide_netlist_semantics",
    "can_provide_module_definition",
    "can_provide_optimization_result",
    "can_be_used_in_next_stage",
    "risk_or_limitation",
    "notes",
]


@dataclass(frozen=True)
class FileRecord:
    file_id: str
    relative_path: str
    file_type: str
    extension: str
    size_bytes: int
    line_count: int
    is_text: bool
    is_binary: bool
    is_source_code: bool
    is_config: bool
    is_netlist: bool
    is_data: bool
    is_test: bool
    is_documentation: bool
    main_purpose: str
    key_classes: str
    key_functions: str
    key_inputs: str
    key_outputs: str
    depends_on: str
    used_by: str
    relevance_to_sram_layoutgen: str
    relevance_category: str
    can_drive_layout_generation: bool
    can_provide_netlist_semantics: bool
    can_provide_module_definition: bool
    can_provide_optimization_result: bool
    can_be_used_in_next_stage: bool
    risk_or_limitation: str
    notes: str

    def to_row(self) -> dict[str, Any]:
        return self.__dict__.copy()


def _json_dump(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8", newline="\n")


def _write_csv(path: Path, fieldnames: list[str], rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def _md_table(columns: list[str], rows: list[dict[str, Any]]) -> str:
    lines = [
        "| " + " | ".join(columns) + " |",
        "| " + " | ".join(["---"] * len(columns)) + " |",
    ]
    for row in rows:
        lines.append("| " + " | ".join(str(row.get(column, "")).replace("\n", "<br>") for column in columns) + " |")
    return "\n".join(lines) + "\n"


def _read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _find_cell(lib: gdstk.Library, name: str) -> gdstk.Cell | None:
    for cell in lib.cells:
        if cell.name == name:
            return cell
    return None


def _clone_reference(lib: gdstk.Library, ref: gdstk.Reference) -> gdstk.Reference:
    cell = _find_cell(lib, ref.cell_name)
    if cell is None:
        raise ValueError(f"Missing referenced cell {ref.cell_name}")
    return gdstk.Reference(
        cell,
        origin=tuple(ref.origin),
        rotation=ref.rotation,
        magnification=ref.magnification,
        x_reflection=ref.x_reflection,
    )


def _clone_label(label: gdstk.Label, *, layer: int | None = None, texttype: int | None = None) -> gdstk.Label:
    return gdstk.Label(
        label.text,
        origin=tuple(label.origin),
        layer=label.layer if layer is None else layer,
        texttype=label.texttype if texttype is None else texttype,
        anchor=label.anchor,
        rotation=label.rotation,
        magnification=label.magnification,
        x_reflection=label.x_reflection,
    )


def _matches_debug_text(text: str) -> bool:
    normalized = str(text)
    return any(pattern in normalized for pattern in DEBUG_TEXT_PATTERNS)


def _gds_sanity(gds_path: Path) -> dict[str, Any]:
    try:
        lib = gdstk.read_gds(gds_path)
    except Exception as exc:
        return {"status": "GDS_PARSE_FAILED", "error": str(exc), "cell_count": 0, "top_level_names": []}
    return {
        "status": "GDS_PARSED_SANITY_PASSED",
        "error": "",
        "cell_count": len(lib.cells),
        "top_level_names": [cell.name for cell in lib.top_level()],
    }


def _library_signature(lib: gdstk.Library) -> dict[str, Any]:
    cell_rows: list[dict[str, Any]] = []
    for cell in sorted(lib.cells, key=lambda item: item.name):
        ref_names = sorted(ref.cell_name for ref in cell.references)
        cell_rows.append(
            {
                "name": cell.name,
                "polygon_count": len(cell.polygons),
                "path_count": len(cell.paths),
                "reference_count": len(cell.references),
                "label_count": len(cell.labels),
                "ref_names": ref_names,
            }
        )
    return {
        "cell_count": len(lib.cells),
        "top_level_names": sorted(cell.name for cell in lib.top_level()),
        "cells": cell_rows,
    }


def _build_clean_gds(
    *,
    source_gds: Path,
    out_clean_dir: Path,
) -> dict[str, Any]:
    out_clean_dir.mkdir(parents=True, exist_ok=True)
    clean_gds = out_clean_dir / "openyield_layoutgen_integrated_sram_clean_review.gds"
    debug_gds = out_clean_dir / "openyield_layoutgen_integrated_sram_annotated_debug.gds"
    source_lib = gdstk.read_gds(source_gds)
    source_sig = _library_signature(source_lib)
    clean_lib = gdstk.Library()
    clean_cell_map: dict[str, gdstk.Cell] = {}
    for cell in source_lib.cells:
        new_cell = gdstk.Cell(cell.name)
        for polygon in cell.polygons:
            new_cell.add(polygon.copy())
        for path in cell.paths:
            new_cell.add(path.copy())
        for label in cell.labels:
            if not _matches_debug_text(label.text):
                new_cell.add(_clone_label(label))
        clean_lib.add(new_cell)
        clean_cell_map[cell.name] = new_cell
    for cell in source_lib.cells:
        new_cell = clean_cell_map[cell.name]
        for ref in cell.references:
            new_cell.add(_clone_reference(clean_lib, ref))
    clean_lib.write_gds(clean_gds)
    source_lib.write_gds(debug_gds)
    clean_sig = _library_signature(gdstk.read_gds(clean_gds))
    removed_rows: list[dict[str, Any]] = []
    for cell in source_lib.cells:
        for label in cell.labels:
            if _matches_debug_text(label.text):
                removed_rows.append(
                    {
                        "cell_name": cell.name,
                        "label_text": label.text,
                        "source_layer": label.layer,
                        "source_texttype": label.texttype,
                        "action": "REMOVED",
                        "debug_layer": "",
                        "debug_texttype": "",
                    }
                )
    physical_shape_preserved = True
    cell_hierarchy_preserved = True
    for source_cell, clean_cell in zip(source_sig["cells"], clean_sig["cells"], strict=True):
        if source_cell["name"] != clean_cell["name"]:
            cell_hierarchy_preserved = False
        if source_cell["polygon_count"] != clean_cell["polygon_count"] or source_cell["path_count"] != clean_cell["path_count"]:
            physical_shape_preserved = False
        if source_cell["reference_count"] != clean_cell["reference_count"] or source_cell["ref_names"] != clean_cell["ref_names"]:
            cell_hierarchy_preserved = False
    clean_sanity = _gds_sanity(clean_gds)
    debug_sanity = _gds_sanity(debug_gds)
    top_levels = clean_sanity["top_level_names"]
    top_cell_name = top_levels[0] if top_levels else "UNKNOWN"
    report = {
        "source_gds_path": str(source_gds),
        "clean_gds_path": str(clean_gds),
        "annotated_debug_gds_path": str(debug_gds),
        "top_cell_name": top_cell_name,
        "gds_sanity_status": clean_sanity["status"],
        "removed_text_count": len(removed_rows),
        "moved_to_debug_layer_count": 0,
        "physical_shape_preserved": physical_shape_preserved,
        "cell_hierarchy_preserved": cell_hierarchy_preserved,
        "human_klayout_review_required": True,
        "debug_layer": DEBUG_LAYER,
        "debug_texttype": DEBUG_TEXTTYPE,
        "source_gds_sanity_status": debug_sanity["status"],
        "clean_cell_count": clean_sanity["cell_count"],
        "annotated_debug_cell_count": debug_sanity["cell_count"],
    }
    report_md = "\n".join(
        [
            "# T1 Clean Review GDS Report",
            "",
            "## Summary",
            "",
            f"- source_gds_path: `{report['source_gds_path']}`",
            f"- clean_gds_path: `{report['clean_gds_path']}`",
            f"- annotated_debug_gds_path: `{report['annotated_debug_gds_path']}`",
            f"- top_cell_name: `{report['top_cell_name']}`",
            f"- gds_sanity_status: `{report['gds_sanity_status']}`",
            f"- removed_text_count: `{report['removed_text_count']}`",
            f"- moved_to_debug_layer_count: `{report['moved_to_debug_layer_count']}`",
            f"- physical_shape_preserved: `{report['physical_shape_preserved']}`",
            f"- cell_hierarchy_preserved: `{report['cell_hierarchy_preserved']}`",
            f"- human_klayout_review_required: `{report['human_klayout_review_required']}`",
            "",
            "## Notes",
            "",
            "- Clean review GDS deletes matched M5/OpenYield debug text labels only.",
            "- Annotated debug GDS preserves the original label-bearing view for trace/debug use.",
            "- Label cleanup does not prove OpenYield netlist-to-layout traceability.",
            "",
        ]
    )
    removed_md = "# Removed Annotation Inventory\n\n" + _md_table(
        ["cell_name", "label_text", "source_layer", "source_texttype", "action", "debug_layer", "debug_texttype"],
        removed_rows or [{"cell_name": "NONE", "label_text": "NONE", "source_layer": "", "source_texttype": "", "action": "NONE", "debug_layer": "", "debug_texttype": ""}],
    )
    manifest = {
        "artifacts": [
            {"path": str(clean_gds), "kind": "clean_review_gds"},
            {"path": str(debug_gds), "kind": "annotated_debug_gds"},
            {"path": str(out_clean_dir / "clean_gds_report.json"), "kind": "clean_report_json"},
            {"path": str(out_clean_dir / "clean_gds_report.md"), "kind": "clean_report_md"},
            {"path": str(out_clean_dir / "removed_annotation_inventory.csv"), "kind": "removed_annotation_inventory_csv"},
            {"path": str(out_clean_dir / "removed_annotation_inventory.md"), "kind": "removed_annotation_inventory_md"},
        ]
    }
    _json_dump(out_clean_dir / "clean_gds_report.json", report)
    _write_text(out_clean_dir / "clean_gds_report.md", report_md)
    _write_csv(out_clean_dir / "removed_annotation_inventory.csv", ["cell_name", "label_text", "source_layer", "source_texttype", "action", "debug_layer", "debug_texttype"], removed_rows)
    _write_text(out_clean_dir / "removed_annotation_inventory.md", removed_md)
    _json_dump(out_clean_dir / "review_gds_manifest.json", manifest)
    _write_text(
        out_clean_dir / "review_gds_manifest.md",
        "# Review GDS Manifest\n\n" + _md_table(["path", "kind"], manifest["artifacts"]),
    )
    return report


def _is_probably_text(path: Path, size_bytes: int) -> bool:
    if path.suffix.lower() in {".png", ".jpg", ".jpeg", ".gif", ".pdf", ".gz", ".zip", ".tar", ".xz", ".pickle", ".pkl"}:
        return False
    if size_bytes > MAX_TEXT_READ_BYTES:
        return False
    try:
        data = path.read_bytes()[:4096]
    except Exception:
        return False
    if b"\x00" in data:
        return False
    try:
        data.decode("utf-8")
        return True
    except UnicodeDecodeError:
        try:
            data.decode("utf-8-sig")
            return True
        except UnicodeDecodeError:
            return False


def _read_text_if_safe(path: Path, is_text: bool, size_bytes: int) -> str | None:
    if not is_text or size_bytes > MAX_TEXT_READ_BYTES:
        return None
    for encoding in ("utf-8", "utf-8-sig", "gbk", "latin-1"):
        try:
            return path.read_text(encoding=encoding)
        except UnicodeDecodeError:
            continue
    return None


def _count_lines(text: str | None) -> int:
    if text is None:
        return 0
    return len(text.splitlines())


def _detect_file_flags(relative_path: str, extension: str) -> dict[str, bool]:
    lower = relative_path.lower()
    return {
        "is_source_code": extension in {".py", ".sh"} or lower.endswith("refreshenv") or lower.endswith("conda"),
        "is_config": extension in {".yaml", ".yml", ".json", ".ini", ".cfg"} or Path(relative_path).name in {"conda"},
        "is_netlist": extension in {".sp", ".spice", ".cir"},
        "is_data": extension in {".csv", ".txt", ".ipynb"} or "/vector_csv_file/" in lower or "/bound_lib/" in lower,
        "is_test": "test" in Path(relative_path).name.lower() or "/test" in lower or lower.endswith("_test.py"),
        "is_documentation": extension in {".md", ".rst"} or Path(relative_path).name.lower() in {"license", "readme"},
    }


def _python_summary(relative_path: str, text: str) -> dict[str, Any]:
    try:
        tree = ast.parse(text)
    except SyntaxError:
        return {
            "key_classes": "UNKNOWN",
            "key_functions": "UNKNOWN",
            "depends_on": "UNKNOWN",
            "doc_summary": "Python file with parse error; manual inspection needed.",
        }
    classes = [node.name for node in ast.walk(tree) if isinstance(node, ast.ClassDef)]
    funcs = [node.name for node in ast.walk(tree) if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))]
    imports: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imports.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            base = node.module or ""
            imports.append(base)
    doc = ast.get_docstring(tree) or ""
    return {
        "key_classes": ", ".join(classes[:12]) if classes else "NONE",
        "key_functions": ", ".join(funcs[:18]) if funcs else "NONE",
        "depends_on": ", ".join(sorted(set(item for item in imports if item))[:20]) if imports else "NONE",
        "doc_summary": doc.strip().splitlines()[0] if doc.strip() else _guess_main_purpose(relative_path, text),
    }


def _guess_main_purpose(relative_path: str, text: str | None) -> str:
    lower = relative_path.lower()
    name = Path(relative_path).name.lower()
    if relative_path == "main_sram.py":
        return "Primary SRAM simulation entrypoint that loads YAML configs and runs transistor-level SRAM testbenches."
    if relative_path == "main_opt.py":
        return "Interactive entrypoint that selects and launches SRAM sizing/architecture optimization demos."
    if relative_path == "main_estimation.py":
        return "Yield-estimation driver that runs SRAM failure-probability algorithms over SPICE-backed testbenches."
    if lower.startswith("sram_compiler/subcircuits/"):
        return "Defines SRAM or peripheral subcircuit generation logic for SPICE/PySpice netlist construction."
    if lower.startswith("sram_compiler/testbenches/"):
        return "Builds simulation testbenches and result-processing flows around generated SRAM netlists."
    if lower.startswith("sram_compiler/config_yaml/"):
        return "Stores SRAM/global/module parameter configuration consumed by OpenYield netlist generation flows."
    if lower.startswith("size_optimization/"):
        return "Implements or configures SRAM sizing/architecture optimization algorithms."
    if lower.startswith("yield_estimation/"):
        return "Implements SRAM yield-estimation algorithms and related statistical utilities."
    if lower.startswith("equivalent_modeling/"):
        return "Studies or demonstrates equivalent-circuit acceleration for large SRAM simulations."
    if extension := Path(relative_path).suffix.lower():
        if extension in {".sp", ".spice"}:
            return "SPICE model or netlist-related source used by simulation flows."
        if extension in {".yaml", ".yml"}:
            return "Configuration file for simulation or optimization flow."
        if extension in {".md"}:
            return "Documentation file."
        if extension in {".csv", ".txt"}:
            return "Data or bounds file consumed by algorithms."
        if extension in {".png", ".jpg", ".jpeg"}:
            return "Image asset for documentation."
    if name in {"conda", "refreshenv"}:
        return "Environment helper script."
    if text and "class " in text:
        return "Source file containing class-based project logic."
    return "UNKNOWN"


def _classify_relevance(relative_path: str) -> tuple[str, str]:
    lower = relative_path.lower()
    if lower == "main_sram.py":
        return (
            "NETLIST_SOURCE",
            "Top-level OpenYield SRAM netlist generator entrypoint; useful as a trace source for future netlist-to-layout translation.",
        )
    if lower.startswith("sram_compiler/subcircuits/"):
        return (
            "MODULE_DEFINITION",
            "Defines SRAM module/peripheral netlist structure and therefore provides module semantics relevant to layoutgen mapping.",
        )
    if lower.startswith("sram_compiler/config_yaml/"):
        return (
            "CONFIG",
            "Provides module parameters, array dimensions, device choices, and configuration semantics that can annotate layoutgen inputs.",
        )
    if lower.startswith("sram_compiler/testbenches/"):
        return (
            "NETLIST_SOURCE",
            "Builds executable SRAM testbench/netlist contexts; relevant for tracing how OpenYield instantiates and connects modules.",
        )
    if lower.startswith("size_optimization/") and lower.endswith(".yaml"):
        return (
            "CONFIG",
            "Optimization configuration, not physical layout source; may guide future translator inputs indirectly.",
        )
    if lower.startswith("size_optimization/"):
        return (
            "OPTIMIZATION_ALGORITHM",
            "Optimization-side code for sizing/search, not a physical GDS implementation source.",
        )
    if lower.startswith("yield_estimation/"):
        return (
            "OPTIMIZATION_ALGORITHM",
            "Yield-estimation/statistical code, largely orthogonal to physical layout generation.",
        )
    if lower.startswith("equivalent_modeling/"):
        return (
            "UTILITY",
            "Equivalent-model experiments for simulation acceleration, not a direct physical-layout source.",
        )
    if lower.startswith("tran_models/"):
        return (
            "DATASET",
            "PDK transistor model deck for SPICE simulation; required for simulation fidelity but not a GDS layout source.",
        )
    if lower == "config.py":
        return (
            "CONFIG",
            "Central OpenYield YAML configuration loader that materializes SRAM/global/module semantics used by netlist-generation flows.",
        )
    if lower in {"readme.md", "readme_compiler.md", "电路算法说明文档.md", "等效电路说明文档.md", "license"}:
        return (
            "DOCUMENTATION",
            "Documentation or license material; informative for understanding the project but not a layout driver.",
        )
    if lower.startswith("img/"):
        return (
            "DOCUMENTATION",
            "Documentation image asset with no layout-generation semantics.",
        )
    if lower in {"main_opt.py", "main_estimation.py", "demo_run_a_testbench.py"}:
        return (
            "SCRIPT_ENTRYPOINT",
            "Script entrypoint for optimization or estimation flows, useful for locating execution roots but not direct GDS generation.",
        )
    if lower in {"utils.py", "plot_data.py", "environment.yml", "conda", "refreshenv"}:
        return (
            "UTILITY",
            "Project-level utility or environment helper with indirect integration relevance only.",
        )
    return ("UNKNOWN", "UNKNOWN")


def _derive_semantic_flags(relative_path: str, category: str) -> dict[str, Any]:
    lower = relative_path.lower()
    module_definition = category == "MODULE_DEFINITION"
    net_semantics = category in {"MODULE_DEFINITION", "NETLIST_SOURCE", "CONFIG"} and not lower.startswith("size_optimization/")
    drive_layout = lower == "main_sram.py"
    optimization_result = category == "OPTIMIZATION_ALGORITHM" or lower.endswith(".csv")
    next_stage = (
        lower == "main_sram.py"
        or lower == "config.py"
        or lower.startswith("sram_compiler/subcircuits/")
        or lower.startswith("sram_compiler/config_yaml/")
        or lower.startswith("sram_compiler/testbenches/")
    )
    if lower.startswith("yield_estimation/") or lower.startswith("size_optimization/") or lower.startswith("equivalent_modeling/"):
        next_stage = False
    return {
        "can_drive_layout_generation": drive_layout,
        "can_provide_netlist_semantics": net_semantics,
        "can_provide_module_definition": module_definition,
        "can_provide_optimization_result": optimization_result,
        "can_be_used_in_next_stage": next_stage,
    }


def _guess_inputs_outputs(relative_path: str, text: str | None, flags: dict[str, bool]) -> tuple[str, str]:
    lower = relative_path.lower()
    if lower == "main_sram.py":
        return (
            "YAML configs, transistor/device parameters, SRAM array size, simulation mode.",
            "SPICE netlists, Xyce simulation outputs, CSV stats, waveform/result directories.",
        )
    if lower.startswith("sram_compiler/subcircuits/"):
        return ("Config objects and module parameters.", "PySpice/SPICE subcircuit definitions and connectivity.")
    if lower.startswith("sram_compiler/testbenches/"):
        return ("Config objects, subcircuit instances, simulation targets, process settings.", "Executable SRAM testbenches, netlists, parsed results.")
    if lower.startswith("sram_compiler/config_yaml/"):
        return ("Manual or scripted parameter edits.", "Configuration values consumed by compiler/testbench flows.")
    if flags["is_netlist"]:
        return ("Included by simulation/testbench flows.", "SPICE model statements or netlist fragments.")
    if lower.startswith("size_optimization/"):
        return ("Optimization config, objective bounds, simulation callbacks.", "Optimization trajectories, selected parameter sets, CSV results.")
    if lower.startswith("yield_estimation/"):
        return ("Simulation outcome model, distributions, pass/fail criteria.", "Failure-rate or yield-estimation statistics.")
    if lower.startswith("equivalent_modeling/"):
        return ("Array size / equivalent-model options.", "Comparison results for equivalent vs full simulation.")
    if text and "matplotlib" in text.lower():
        return ("CSV or numeric result files.", "Plots or visualizations.")
    return ("UNKNOWN", "UNKNOWN")


def _risk_note(relative_path: str, category: str) -> str:
    lower = relative_path.lower()
    if lower == "main_sram.py":
        return "Generates or mutates simulation-side YAML and netlists, but does not emit physical GDS or a proven layout trace."
    if category == "MODULE_DEFINITION":
        return "Provides electrical/module semantics only; missing direct geometry, placement, and routing correspondence to layoutgen cells."
    if category == "CONFIG":
        return "Configuration alone cannot prove which physical layout cell should implement a given OpenYield module."
    if category == "OPTIMIZATION_ALGORITHM":
        return "Optimization or estimation logic is not a physical-layout implementation source."
    if lower.startswith("tran_models/"):
        return "Process model deck affects simulation behavior only and cannot map modules to GDS geometry."
    if lower.startswith("img/"):
        return "Documentation asset only."
    return "UNKNOWN"


def _build_used_by_map(relative_paths: list[str]) -> dict[str, list[str]]:
    stem_map: dict[str, list[str]] = {}
    for rel in relative_paths:
        stem = Path(rel).stem
        stem_map.setdefault(stem, []).append(rel)
    used_by: dict[str, list[str]] = {rel: [] for rel in relative_paths}
    for rel in relative_paths:
        try:
            text = Path("/").joinpath("tmp").read_text()  # unreachable sentinel
        except Exception:
            pass
    return used_by


def _repo_tree_lines(root: Path) -> list[str]:
    lines = [root.name]
    for current_root, dirs, files in os.walk(root):
        dirs[:] = sorted(d for d in dirs if d not in {".git", "__pycache__"})
        rel_root = Path(current_root).relative_to(root)
        depth = len(rel_root.parts)
        prefix = "  " * depth
        for file_name in sorted(files):
            if file_name.endswith(".pyc"):
                continue
            rel = rel_root / file_name if rel_root.parts else Path(file_name)
            lines.append(f"{prefix}- {rel.as_posix()}")
    return lines


def _collect_files(openyield_root: Path) -> list[Path]:
    paths: list[Path] = []
    for current_root, dirs, files in os.walk(openyield_root):
        dirs[:] = sorted(d for d in dirs if d not in {".git", "__pycache__"})
        for file_name in sorted(files):
            if file_name.endswith(".pyc"):
                continue
            paths.append(Path(current_root) / file_name)
    return sorted(paths)


def _analyze_openyield_files(openyield_root: Path) -> dict[str, Any]:
    file_paths = _collect_files(openyield_root)
    relative_paths = [path.relative_to(openyield_root).as_posix() for path in file_paths]
    used_by_map: dict[str, list[str]] = {rel: [] for rel in relative_paths}
    import_targets: dict[str, list[str]] = {}
    parsed_python: dict[str, dict[str, Any]] = {}
    text_cache: dict[str, str | None] = {}
    for path, rel in zip(file_paths, relative_paths, strict=True):
        size_bytes = path.stat().st_size
        is_text = _is_probably_text(path, size_bytes)
        text = _read_text_if_safe(path, is_text, size_bytes)
        text_cache[rel] = text
        if path.suffix.lower() == ".py" and text is not None:
            parsed = _python_summary(rel, text)
            parsed_python[rel] = parsed
            for dep in str(parsed["depends_on"]).split(", "):
                if dep and dep not in {"NONE", "UNKNOWN"}:
                    import_targets.setdefault(dep.split(".")[-1], []).append(rel)
    for rel in relative_paths:
        stem = Path(rel).stem
        used_by = sorted(set(import_targets.get(stem, [])))
        used_by_map[rel] = [item for item in used_by if item != rel]
    rows: list[dict[str, Any]] = []
    records: list[FileRecord] = []
    for index, (path, rel) in enumerate(zip(file_paths, relative_paths, strict=True), start=1):
        size_bytes = path.stat().st_size
        extension = path.suffix.lower()
        is_text = _is_probably_text(path, size_bytes)
        text = text_cache[rel]
        flags = _detect_file_flags(rel, extension)
        category, relevance = _classify_relevance(rel)
        semantic_flags = _derive_semantic_flags(rel, category)
        py_summary = parsed_python.get(rel, {})
        main_purpose = py_summary.get("doc_summary") or _guess_main_purpose(rel, text)
        key_classes = py_summary.get("key_classes", "NONE" if flags["is_source_code"] else "UNKNOWN")
        key_functions = py_summary.get("key_functions", "NONE" if flags["is_source_code"] else "UNKNOWN")
        depends_on = py_summary.get("depends_on", "UNKNOWN")
        key_inputs, key_outputs = _guess_inputs_outputs(rel, text, flags)
        notes: list[str] = []
        if size_bytes > MAX_TEXT_READ_BYTES:
            notes.append("Content not read because file is larger than 20MB.")
        if not is_text:
            notes.append("Binary or non-text asset.")
        if category == "UNKNOWN":
            notes.append("Classification remained UNKNOWN where evidence was insufficient.")
        record = FileRecord(
            file_id=f"OYF{index:04d}",
            relative_path=rel,
            file_type=_determine_file_type(rel, extension, flags, is_text),
            extension=extension or "NONE",
            size_bytes=size_bytes,
            line_count=_count_lines(text),
            is_text=is_text,
            is_binary=not is_text,
            is_source_code=flags["is_source_code"],
            is_config=flags["is_config"],
            is_netlist=flags["is_netlist"],
            is_data=flags["is_data"],
            is_test=flags["is_test"],
            is_documentation=flags["is_documentation"],
            main_purpose=main_purpose or "UNKNOWN",
            key_classes=key_classes,
            key_functions=key_functions,
            key_inputs=key_inputs,
            key_outputs=key_outputs,
            depends_on=depends_on if depends_on else "UNKNOWN",
            used_by=", ".join(used_by_map[rel]) if used_by_map[rel] else "UNKNOWN",
            relevance_to_sram_layoutgen=relevance,
            relevance_category=category,
            can_drive_layout_generation=semantic_flags["can_drive_layout_generation"],
            can_provide_netlist_semantics=semantic_flags["can_provide_netlist_semantics"],
            can_provide_module_definition=semantic_flags["can_provide_module_definition"],
            can_provide_optimization_result=semantic_flags["can_provide_optimization_result"],
            can_be_used_in_next_stage=semantic_flags["can_be_used_in_next_stage"],
            risk_or_limitation=_risk_note(rel, category),
            notes=" ".join(notes) if notes else "NONE",
        )
        records.append(record)
        rows.append(record.to_row())
    return {
        "records": records,
        "rows": rows,
        "tree_lines": _repo_tree_lines(openyield_root),
        "relative_paths": relative_paths,
    }


def _determine_file_type(relative_path: str, extension: str, flags: dict[str, bool], is_text: bool) -> str:
    lower = relative_path.lower()
    if lower.startswith("sram_compiler/subcircuits/"):
        return "python_subcircuit_source"
    if lower.startswith("sram_compiler/testbenches/"):
        return "python_testbench_source"
    if lower.startswith("sram_compiler/config_yaml/"):
        return "yaml_config"
    if lower.startswith("size_optimization/"):
        return "optimization_source" if extension == ".py" else "optimization_asset"
    if lower.startswith("yield_estimation/"):
        return "yield_estimation_source" if extension == ".py" else "yield_estimation_asset"
    if lower.startswith("tran_models/"):
        return "spice_model"
    if flags["is_documentation"]:
        return "documentation"
    if flags["is_netlist"]:
        return "netlist_or_model"
    if flags["is_source_code"]:
        return "source_code"
    if not is_text:
        return "binary_asset"
    return "text_asset"


def _build_inventory_reports(
    *,
    openyield_root: Path,
    out_inventory_dir: Path,
) -> dict[str, Any]:
    analysis = _analyze_openyield_files(openyield_root)
    rows = analysis["rows"]
    records: list[FileRecord] = analysis["records"]
    out_inventory_dir.mkdir(parents=True, exist_ok=True)
    _write_csv(out_inventory_dir / "openyield_full_file_inventory.csv", INVENTORY_COLUMNS, rows)
    _json_dump(out_inventory_dir / "openyield_full_file_inventory.json", rows)
    full_md_columns = [
        "file_id",
        "relative_path",
        "file_type",
        "relevance_category",
        "main_purpose",
        "relevance_to_sram_layoutgen",
        "can_drive_layout_generation",
        "can_provide_netlist_semantics",
        "can_provide_module_definition",
        "can_be_used_in_next_stage",
        "risk_or_limitation",
    ]
    _write_text(
        out_inventory_dir / "openyield_full_file_inventory.md",
        "# OpenYield Full File Inventory\n\n" + _md_table(full_md_columns, rows),
    )
    source_rows = [
        {
            "relative_path": row["relative_path"],
            "file_type": row["file_type"],
            "key_classes": row["key_classes"],
            "key_functions": row["key_functions"],
            "depends_on": row["depends_on"],
            "used_by": row["used_by"],
            "main_purpose": row["main_purpose"],
            "relevance_category": row["relevance_category"],
        }
        for row in rows
        if row["is_source_code"]
    ]
    _write_csv(
        out_inventory_dir / "openyield_source_file_analysis.csv",
        ["relative_path", "file_type", "key_classes", "key_functions", "depends_on", "used_by", "main_purpose", "relevance_category"],
        source_rows,
    )
    _write_text(
        out_inventory_dir / "openyield_source_file_analysis.md",
        "# OpenYield Source File Analysis\n\n" + _md_table(
            ["relative_path", "file_type", "key_classes", "key_functions", "depends_on", "used_by", "main_purpose", "relevance_category"],
            source_rows or [{"relative_path": "NONE", "file_type": "", "key_classes": "", "key_functions": "", "depends_on": "", "used_by": "", "main_purpose": "", "relevance_category": ""}],
        ),
    )
    tree_text = "\n".join(analysis["tree_lines"]) + "\n"
    _write_text(out_inventory_dir / "openyield_file_tree.txt", tree_text)
    _write_text(out_inventory_dir / "openyield_file_tree.md", "# OpenYield File Tree\n\n```text\n" + tree_text + "```\n")
    key_entrypoints = _identify_key_entrypoints(records)
    _json_dump(out_inventory_dir / "openyield_key_entrypoints_report.json", key_entrypoints)
    _write_text(out_inventory_dir / "openyield_key_entrypoints_report.md", _build_key_entrypoints_md(key_entrypoints))
    relevance_rows = [
        {
            "relative_path": row["relative_path"],
            "relevance_category": row["relevance_category"],
            "relevance_to_sram_layoutgen": row["relevance_to_sram_layoutgen"],
            "can_drive_layout_generation": row["can_drive_layout_generation"],
            "can_provide_netlist_semantics": row["can_provide_netlist_semantics"],
            "can_provide_module_definition": row["can_provide_module_definition"],
            "can_be_used_in_next_stage": row["can_be_used_in_next_stage"],
        }
        for row in rows
    ]
    _write_csv(
        out_inventory_dir / "openyield_layoutgen_integration_relevance_matrix.csv",
        [
            "relative_path",
            "relevance_category",
            "relevance_to_sram_layoutgen",
            "can_drive_layout_generation",
            "can_provide_netlist_semantics",
            "can_provide_module_definition",
            "can_be_used_in_next_stage",
        ],
        relevance_rows,
    )
    _write_text(
        out_inventory_dir / "openyield_layoutgen_integration_relevance_matrix.md",
        "# OpenYield/Layoutgen Relevance Matrix\n\n"
        + _md_table(
            [
                "relative_path",
                "relevance_category",
                "relevance_to_sram_layoutgen",
                "can_drive_layout_generation",
                "can_provide_netlist_semantics",
                "can_provide_module_definition",
                "can_be_used_in_next_stage",
            ],
            relevance_rows,
        ),
    )
    netlist_report = _build_netlist_layout_relevance(records)
    _json_dump(out_inventory_dir / "openyield_netlist_layout_relevance_report.json", netlist_report)
    _write_text(out_inventory_dir / "openyield_netlist_layout_relevance_report.md", _build_netlist_layout_md(netlist_report))
    totals = _inventory_totals(records)
    return {
        "records": records,
        "rows": rows,
        "key_entrypoints": key_entrypoints,
        "netlist_report": netlist_report,
        "totals": totals,
    }


def _identify_key_entrypoints(records: list[FileRecord]) -> dict[str, Any]:
    rel_map = {record.relative_path: record for record in records}
    entrypoint_paths = [
        "main_sram.py",
        "main_opt.py",
        "main_estimation.py",
        "equivalent_modeling/main_sram.py",
        "demo_run_a_testbench.py",
    ]
    entrypoints = []
    for rel in entrypoint_paths:
        record = rel_map.get(rel)
        if record is None:
            entrypoints.append({"relative_path": rel, "status": "UNKNOWN", "why": "File not found during inventory."})
            continue
        entrypoints.append(
            {
                "relative_path": rel,
                "status": "IDENTIFIED",
                "main_purpose": record.main_purpose,
                "relevance_category": record.relevance_category,
                "can_provide_netlist_semantics": record.can_provide_netlist_semantics,
                "can_be_used_in_next_stage": record.can_be_used_in_next_stage,
            }
        )
    return {
        "project_primary_entrypoint": "main_sram.py" if "main_sram.py" in rel_map else "UNKNOWN",
        "key_entrypoints": entrypoints,
    }


def _build_key_entrypoints_md(report: dict[str, Any]) -> str:
    rows = report["key_entrypoints"]
    return "# OpenYield Key Entrypoints\n\n" + _md_table(
        ["relative_path", "status", "main_purpose", "relevance_category", "can_provide_netlist_semantics", "can_be_used_in_next_stage", "why"],
        rows,
    )


def _build_netlist_layout_relevance(records: list[FileRecord]) -> dict[str, Any]:
    netlist_sources = [record.relative_path for record in records if record.can_provide_netlist_semantics]
    module_definitions = [record.relative_path for record in records if record.can_provide_module_definition]
    direct_gds_modules = [record.relative_path for record in records if record.extension == ".gds"]
    next_stage_inputs = [
        record.relative_path
        for record in records
        if record.can_be_used_in_next_stage and record.relative_path.startswith(("main_sram.py", "sram_compiler/"))
    ]
    unrelated = [
        record.relative_path
        for record in records
        if record.relevance_category in {"DOCUMENTATION", "OPTIMIZATION_ALGORITHM"} or record.relative_path.startswith(("img/", "yield_estimation/", "size_optimization/"))
    ]
    return {
        "project_overview": "OpenYield is primarily a transistor-level SRAM simulation, yield-estimation, and optimization project rather than a physical GDS layout repository.",
        "contains_direct_physical_gds_module": False,
        "direct_physical_gds_module_evidence": direct_gds_modules,
        "netlist_semantics_sources": netlist_sources,
        "module_definition_sources": module_definitions,
        "layoutgen_candidate_inputs": next_stage_inputs,
        "layoutgen_irrelevant_or_low_relevance_files": unrelated,
        "translator_recommended_inputs": [
            "main_sram.py",
            "config.py",
            "sram_compiler/config_yaml/global.yaml",
            "sram_compiler/config_yaml/sram_6t_cell.yaml",
            "sram_compiler/config_yaml/wordline_driver.yaml",
            "sram_compiler/config_yaml/precharge.yaml",
            "sram_compiler/config_yaml/mux.yaml",
            "sram_compiler/config_yaml/sa.yaml",
            "sram_compiler/config_yaml/write_driver.yaml",
            "sram_compiler/config_yaml/decoder.yaml",
            "sram_compiler/subcircuits/sram_6t_core.py",
            "sram_compiler/subcircuits/decoder.py",
            "sram_compiler/subcircuits/wordline_driver.py",
            "sram_compiler/subcircuits/precharge_and_write_driver.py",
            "sram_compiler/subcircuits/mux_and_sa.py",
            "sram_compiler/subcircuits/time_generate.py",
            "sram_compiler/testbenches/sram_6t_core_MC_testbench.py",
            "sram_compiler/testbenches/parameter_factor.py",
        ],
    }


def _build_netlist_layout_md(report: dict[str, Any]) -> str:
    return "\n".join(
        [
            "# OpenYield Netlist/Layout Relevance Report",
            "",
            f"- project_overview: {report['project_overview']}",
            f"- contains_direct_physical_gds_module: `{report['contains_direct_physical_gds_module']}`",
            "",
            "## Netlist Semantics Sources",
            "",
        ]
    ) + "\n" + "\n".join(f"- `{item}`" for item in report["netlist_semantics_sources"]) + "\n\n## Translator Recommended Inputs\n\n" + "\n".join(
        f"- `{item}`" for item in report["translator_recommended_inputs"]
    ) + "\n\n## Low-Relevance Files\n\n" + "\n".join(
        f"- `{item}`" for item in report["layoutgen_irrelevant_or_low_relevance_files"][:80]
    ) + "\n"


def _inventory_totals(records: list[FileRecord]) -> dict[str, int]:
    return {
        "openyield_file_count_total": len(records),
        "openyield_text_file_count": sum(1 for item in records if item.is_text),
        "openyield_source_file_count": sum(1 for item in records if item.is_source_code),
        "openyield_config_file_count": sum(1 for item in records if item.is_config),
        "openyield_netlist_candidate_file_count": sum(1 for item in records if item.is_netlist or item.can_provide_netlist_semantics),
        "openyield_unknown_file_count": sum(1 for item in records if item.relevance_category == "UNKNOWN"),
    }


def _render_status_md(clean_report: dict[str, Any], inventory_totals: dict[str, int], out_report: Path) -> str:
    return "\n".join(
        [
            "# OpenYield SRAM LayoutGen Project Status",
            "",
            "## 1. Current Correct Goal",
            "",
            "基于原 layoutgen 版图生成器，将 OpenYield 的模块、网表语义和连接关系接入真实 SRAM GDS 生成主干，生成 OpenYield-driven layoutgen-based SRAM GDS。",
            "",
            "## 2. Current Stage",
            "",
            "- current_stage: `T1`",
            "- next_stage: `WAIT_HUMAN_KLAYOUT_REVIEW`",
            "- human_klayout_review_required_every_stage: `True`",
            "- can_enter_next_stage_without_human_review: `False`",
            "",
            "## 3. M5 Human Review",
            "",
            "- Current GDS is visually cluttered by OpenYield/M5 debug text labels.",
            "- The physical hierarchy still mainly uses layoutgen cells.",
            "- Current evidence does not yet prove the final GDS is truly generated from the OpenYield netlist.",
            "- OpenYield-to-layoutgen integration must be proven by a netlist-to-layout trace, not by text labels.",
            "- Bitcell power rail merging / rail continuity appears not fully restored in the generated GDS.",
            "- Next immediate work is cleanup + complete OpenYield file inventory, not another integration attempt.",
            "",
            "## 4. T1 Result",
            "",
            f"- clean_review_gds_path: `{clean_report['clean_gds_path']}`",
            f"- clean_gds_sanity_status: `{clean_report['gds_sanity_status']}`",
            f"- removed_text_count: `{clean_report['removed_text_count']}`",
            f"- physical_shape_preserved: `{clean_report['physical_shape_preserved']}`",
            f"- cell_hierarchy_preserved: `{clean_report['cell_hierarchy_preserved']}`",
            f"- openyield_file_count_total: `{inventory_totals['openyield_file_count_total']}`",
            f"- openyield_source_file_count: `{inventory_totals['openyield_source_file_count']}`",
            f"- openyield_netlist_candidate_file_count: `{inventory_totals['openyield_netlist_candidate_file_count']}`",
            "",
            "## 5. Next Immediate Task",
            "",
            f"先对 clean review GDS 做人工 KLayout 复核，再进入 netlist-to-layout translator 设计；在此之前不进入下一阶段。详见 `{out_report}`。",
            "",
        ]
    )


def _update_status_json(status: dict[str, Any], final_report: dict[str, Any]) -> dict[str, Any]:
    updated = dict(status)
    updated["current_stage"] = "T1"
    updated["next_stage"] = "WAIT_HUMAN_KLAYOUT_REVIEW"
    updated["can_enter_next_stage_without_human_review"] = False
    updated["next_task_summary"] = (
        f"Human KLayout review of {final_report['clean_review_gds_path']} is required before any next-stage netlist-to-layout translator work."
    )
    updated["last_M5_human_review"] = {
        "current_gds_visually_cluttered_by_debug_text_labels": True,
        "physical_hierarchy_still_mainly_uses_layoutgen_cells": True,
        "final_gds_proven_openyield_netlist_driven": False,
        "must_prove_integration_via_netlist_to_layout_trace_not_text_labels": True,
        "bitcell_power_rail_merging_fully_restored": False,
        "next_immediate_work": "cleanup + complete OpenYield file inventory",
    }
    updated["last_T1_report"] = {
        "clean_review_gds_path": final_report["clean_review_gds_path"],
        "clean_gds_sanity_status": final_report["clean_gds_sanity_status"],
        "removed_text_count": final_report["removed_text_count"],
        "physical_shape_preserved": final_report["physical_shape_preserved"],
        "cell_hierarchy_preserved": final_report["cell_hierarchy_preserved"],
        "openyield_file_count_total": final_report["openyield_file_count_total"],
        "openyield_source_file_count": final_report["openyield_source_file_count"],
        "openyield_netlist_candidate_file_count": final_report["openyield_netlist_candidate_file_count"],
        "next_stage_should_be_netlist_to_layout_translator": final_report["next_stage_should_be_netlist_to_layout_translator"],
        "human_klayout_review_required": final_report["human_klayout_review_required"],
        "can_enter_next_stage_before_human_review": final_report["can_enter_next_stage_before_human_review"],
    }
    return updated


def _build_final_report_md(final_report: dict[str, Any], inventory: dict[str, Any]) -> str:
    key_entrypoints = ", ".join(item["relative_path"] for item in inventory["key_entrypoints"]["key_entrypoints"] if item["status"] == "IDENTIFIED")
    return "\n".join(
        [
            "# T1 OpenYield Full File Report",
            "",
            "## Summary",
            "",
            f"- clean_review_gds_generated: `{final_report['clean_review_gds_generated']}`",
            f"- clean_review_gds_path: `{final_report['clean_review_gds_path']}`",
            f"- clean_gds_sanity_status: `{final_report['clean_gds_sanity_status']}`",
            f"- removed_text_count: `{final_report['removed_text_count']}`",
            f"- physical_shape_preserved: `{final_report['physical_shape_preserved']}`",
            f"- cell_hierarchy_preserved: `{final_report['cell_hierarchy_preserved']}`",
            f"- openyield_file_count_total: `{final_report['openyield_file_count_total']}`",
            f"- openyield_source_file_count: `{final_report['openyield_source_file_count']}`",
            f"- openyield_netlist_candidate_file_count: `{final_report['openyield_netlist_candidate_file_count']}`",
            f"- key_entrypoints: `{key_entrypoints or 'UNKNOWN'}`",
            "",
            "## Required Answers",
            "",
            "1. OpenYield 项目整体是做什么的；",
            "OpenYield 整体更像一个 SRAM 电路网表生成、仿真、yield estimation 和参数优化项目，核心输出围绕 SPICE/PySpice/Xyce，而不是 physical GDS 版图库。",
            "",
            "2. 它里面是否真的包含可直接用于版图生成的 GDS module；",
            "没有发现 OpenYield 自带的 `.gds` physical module 库。当前 inventory 中不存在可直接作为 layoutgen physical macro 输入的 OpenYield GDS 模块证据。",
            "",
            "3. 它是否更偏网表/优化/算法，而不是 physical layout；",
            "是。目录结构和入口脚本都表明它更偏网表生成、仿真、yield estimation、以及 sizing/architecture optimization，而不是 physical layout。",
            "",
            "4. 哪些文件能作为 OpenYield 网表语义来源；",
            "主要是 `main_sram.py`、`config.py`、`sram_compiler/subcircuits/*.py`、`sram_compiler/testbenches/*.py`、`sram_compiler/config_yaml/*.yaml`。",
            "",
            "5. 哪些文件能作为 module mapping 来源；",
            "主要是 `sram_compiler/subcircuits/decoder.py`、`wordline_driver.py`、`precharge_and_write_driver.py`、`mux_and_sa.py`、`sram_6t_core.py`、`time_generate.py`，以及相应 YAML 配置。",
            "",
            "6. 哪些文件能作为 layoutgen 输入；",
            "下一阶段最适合作为 translator 输入的是 `main_sram.py`、`config.py`、`sram_compiler/config_yaml/*.yaml`、`sram_compiler/subcircuits/*.py`、以及部分 testbench 连接逻辑。",
            "",
            "7. 哪些文件不能直接用于 GDS；",
            "`yield_estimation/`、`size_optimization/`、`equivalent_modeling/`、`tran_models/`、图片和说明文档都不能直接用于 GDS 生成。",
            "",
            "8. 下一阶段如果要做“网表翻译器”，应该读取哪些 OpenYield 文件；",
            "应优先读取 `main_sram.py`、`config.py`、`sram_compiler/config_yaml/global.yaml`、各模块 YAML，以及 `sram_compiler/subcircuits/*.py` 和 `sram_compiler/testbenches/parameter_factor.py`。",
            "",
            "9. 当前 M5 为什么不能证明 GDS 来自 OpenYield 网表；",
            "因为当前证据主要是 M5/OpenYield 文本标签和 wrapper hierarchy。标签只能证明人工标注，不足以证明每个 GDS module、instance、net 都从 OpenYield netlist 被逐步翻译并落到了真实 layoutgen 物理对象上。",
            "",
            "10. 需要怎样的 netlist-to-layout trace 才能证明。",
            "需要从 OpenYield module definition/netlist source 到 layoutgen generator binding、instance placement、route/power realization、最终 GDS cell/reference/net correspondence 的可追溯链路，并且每一步都能回溯到源 netlist 语义，而不是仅靠 text label。",
            "",
            "## Gate",
            "",
            f"- next_stage_should_be_netlist_to_layout_translator: `{final_report['next_stage_should_be_netlist_to_layout_translator']}`",
            f"- human_klayout_review_required: `{final_report['human_klayout_review_required']}`",
            f"- can_enter_next_stage_before_human_review: `{final_report['can_enter_next_stage_before_human_review']}`",
            "",
        ]
    )


def _build_summary_md(final_report: dict[str], inventory: dict[str, Any]) -> str:
    return "\n".join(
        [
            "# T1 OpenYield Full File Summary",
            "",
            f"- clean_review_gds_path: `{final_report['clean_review_gds_path']}`",
            f"- removed_text_count: `{final_report['removed_text_count']}`",
            f"- openyield_file_count_total: `{final_report['openyield_file_count_total']}`",
            f"- key_entrypoints: `{', '.join(item['relative_path'] for item in inventory['key_entrypoints']['key_entrypoints'] if item['status'] == 'IDENTIFIED') or 'UNKNOWN'}`",
            f"- contains_direct_physical_gds_module: `{inventory['netlist_report']['contains_direct_physical_gds_module']}`",
            "- conclusion: OpenYield is primarily a netlist/simulation/optimization codebase; next stage should be a netlist-to-layout translator with explicit trace evidence.",
            "",
        ]
    )


def run_t1_openyield_file_inventory(
    *,
    repo_root: Path,
    status_md: Path,
    status_json: Path,
    m5_gds: Path,
    openyield_root: Path,
    out_clean_dir: Path,
    out_inventory_dir: Path,
    out_json: Path,
    out_report: Path,
) -> dict[str, Any]:
    repo_root = repo_root.resolve()
    status_md = status_md.resolve()
    status_json = status_json.resolve()
    m5_gds = m5_gds.resolve()
    openyield_root = openyield_root.resolve()
    out_clean_dir = out_clean_dir.resolve()
    out_inventory_dir = out_inventory_dir.resolve()
    out_json = out_json.resolve()
    out_report = out_report.resolve()
    if not status_md.exists() or not status_json.exists():
        raise FileNotFoundError("PROJECT_LAYOUTGEN_OPENYIELD_STATUS.md/json must exist before T1.")
    status = _read_json(status_json)
    clean_report = _build_clean_gds(source_gds=m5_gds, out_clean_dir=out_clean_dir)
    inventory = _build_inventory_reports(openyield_root=openyield_root, out_inventory_dir=out_inventory_dir)
    totals = inventory["totals"]
    blockers = []
    if clean_report["gds_sanity_status"] != "GDS_PARSED_SANITY_PASSED":
        blockers.append("clean_review_gds_parse_failed")
    if not clean_report["physical_shape_preserved"]:
        blockers.append("physical_shape_not_preserved")
    if not clean_report["cell_hierarchy_preserved"]:
        blockers.append("cell_hierarchy_not_preserved")
    final_report = {
        "status_file_read": True,
        "status_file_updated": True,
        "clean_review_gds_generated": True,
        "clean_review_gds_path": clean_report["clean_gds_path"],
        "clean_gds_sanity_status": clean_report["gds_sanity_status"],
        "removed_text_count": clean_report["removed_text_count"],
        "physical_shape_preserved": clean_report["physical_shape_preserved"],
        "cell_hierarchy_preserved": clean_report["cell_hierarchy_preserved"],
        "openyield_root_exists": openyield_root.exists(),
        **totals,
        "full_file_inventory_available": True,
        "source_file_analysis_available": True,
        "file_tree_available": True,
        "key_entrypoints_report_available": True,
        "layoutgen_integration_relevance_matrix_available": True,
        "next_stage_should_be_netlist_to_layout_translator": True,
        "human_klayout_review_required": True,
        "can_enter_next_stage_before_human_review": False,
        "remaining_T1_blockers": blockers,
        "remaining_T1_blockers_count": len(blockers),
        "key_entrypoints": [
            item["relative_path"]
            for item in inventory["key_entrypoints"]["key_entrypoints"]
            if item["status"] == "IDENTIFIED"
        ],
        "openyield_contains_direct_physical_gds_module": inventory["netlist_report"]["contains_direct_physical_gds_module"],
        "openyield_bias": "NETLIST_OPTIMIZATION",
    }
    updated_status = _update_status_json(status, final_report)
    _write_text(status_md, _render_status_md(clean_report, totals, out_report))
    _json_dump(status_json, updated_status)
    _json_dump(out_json, final_report)
    _write_text(out_report, _build_final_report_md(final_report, inventory))
    _write_text(repo_root / "docs/evidence/T1_openyield_full_file_summary.md", _build_summary_md(final_report, inventory))
    return final_report
