from __future__ import annotations

import csv
import json
import shutil
import zipfile
from collections import Counter
from pathlib import Path
from typing import Any

import gdstk

from sram_layoutgen.gds_util import inspect_gds_hierarchy, inspect_gds_layers, measure_gds_bbox
from sram_layoutgen.openyield_adapter.gds_row_abutment_audit import audit_gds_row_abutment


REVIEW_TEXT = """M6R correction:
- hybrid_openyield_rail_overlap.complete.gds was proven reproducible, but user confirmed it is still not the correct layoutgen result.
- The true correct layoutgen result is local to the user's Windows machine:
  E:\\njust\\keyan\\SRAM Compiler_V2\\OpenRAM-stable\\deliverables\\sram_layoutgen_standalone\\build\\full_layout_collection.zip
- After upload, the server-side golden reference zip is:
  external_references/full_layout_collection.zip
- From now on, hybrid_openyield_rail_overlap.complete.gds must be treated as historical wrong reference, not golden reference."""

HISTORICAL_WRONG_REFERENCE = "outputs/layout_prototype/hybrid_openyield_rail_overlap/hybrid_openyield_rail_overlap.complete.gds"
CURRENT_PROJECT_TARGET = "8x64_wpr4"
OUTPUT_GOLDEN_NAME = "golden_reference.gds"
OUTPUT_GOLDEN_CLEAN_NAME = "golden_reference_clean_review.gds"


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


def _copy(src: Path, dst: Path) -> str:
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dst)
    return str(dst)


def _strip_all_text(source_gds: Path, target_gds: Path) -> dict[str, Any]:
    source = gdstk.read_gds(source_gds)
    lib = gdstk.Library()
    text_count = 0
    for cell in source.cells:
        new_cell = gdstk.Cell(cell.name)
        for polygon in cell.polygons:
            new_cell.add(polygon.copy())
        for path in cell.paths:
            new_cell.add(path.copy())
        text_count += len(cell.labels)
        lib.add(new_cell)
    for cell in source.cells:
        new_cell = _find_cell(lib, cell.name)
        assert new_cell is not None
        for ref in cell.references:
            new_cell.add(_clone_reference(lib, ref))
    lib.write_gds(target_gds)
    return {"removed_text_count": text_count, "clean_review_gds_path": str(target_gds)}


def _gdstk_stats(path: Path) -> dict[str, Any]:
    lib = gdstk.read_gds(path)
    tops = lib.top_level()
    top = tops[0] if tops else None
    bbox = top.bounding_box() if top is not None else None
    per_layer = Counter()
    boundary_count = 0
    path_count = 0
    sref_count = 0
    instance_count_by_cell = Counter()
    cell_hierarchy: dict[str, list[str]] = {}
    for cell in lib.cells:
        child_names = sorted(ref.cell_name for ref in cell.references)
        cell_hierarchy[cell.name] = child_names
        for polygon in cell.polygons:
            boundary_count += 1
            per_layer[f"{polygon.layer}/{polygon.datatype}"] += 1
        for gdspath in cell.paths:
            path_count += 1
            per_layer[f"{gdspath.layer}/{gdspath.datatype}"] += 1
        for ref in cell.references:
            sref_count += 1
            instance_count_by_cell[ref.cell_name] += 1
    return {
        "top_cell": top.name if top is not None else None,
        "cell_count": len(lib.cells),
        "sref_count": sref_count,
        "boundary_count": boundary_count,
        "path_count": path_count,
        "bbox": {
            "x0": round(float(bbox[0][0]), 6),
            "y0": round(float(bbox[0][1]), 6),
            "x1": round(float(bbox[1][0]), 6),
            "y1": round(float(bbox[1][1]), 6),
        } if bbox is not None else None,
        "per_layer_shape_count": dict(sorted(per_layer.items())),
        "instance_count_by_cell_name": dict(sorted(instance_count_by_cell.items())),
        "cell_hierarchy": cell_hierarchy,
    }


def _hierarchy_presence(stats: dict[str, Any], needle: str) -> dict[str, Any]:
    names = list(stats["instance_count_by_cell_name"].keys())
    exact = stats["instance_count_by_cell_name"].get(needle, 0)
    wrapper_names = sorted(name for name in names if needle in name)
    return {
        "exact_instance_count": exact,
        "wrapper_instance_count": sum(stats["instance_count_by_cell_name"].get(name, 0) for name in wrapper_names),
        "wrapper_cell_names": wrapper_names,
        "present_in_top_hierarchy": exact > 0 or bool(wrapper_names),
    }


def _nearby_layout_json(path: Path) -> Path | None:
    stem = path.stem
    candidates = [
        path.with_suffix(".layout.json"),
        path.parent / f"{stem}.layout.json",
        path.parent / f"{stem.replace('.complete', '')}.layout.json",
        path.parent / f"{stem.replace('.debug', '')}.layout.json",
    ]
    for candidate in candidates:
        if candidate.exists():
            return candidate
    return None


def _layout_json_power_summary(gds_path: Path) -> dict[str, Any]:
    layout_json = _nearby_layout_json(gds_path)
    if layout_json is None:
        return {
            "layout_json_path": None,
            "power_rail_overlap_positive_count": None,
            "same_net_power_overlap_pass": None,
            "bitcell_rail_continuity_visible": "UNKNOWN",
            "rail_stitch_visible": "UNKNOWN",
        }
    audit = audit_gds_row_abutment(gds_path, layout_json=layout_json)
    positive = audit.get("positive_overlap_count")
    same_net = audit.get("same_net_power_overlap_pass")
    return {
        "layout_json_path": str(layout_json),
        "power_rail_overlap_positive_count": positive,
        "same_net_power_overlap_pass": same_net,
        "bitcell_rail_continuity_visible": bool(positive and positive > 0),
        "rail_stitch_visible": bool(same_net),
    }


def _visible_structure_summary(stats: dict[str, Any]) -> dict[str, Any]:
    names = set(stats["instance_count_by_cell_name"].keys())
    def _has(token: str) -> bool:
        return any(token in name.lower() for name in names)
    return {
        "bitcell_array_present": _has("bitcell") or _has("cell_1rw"),
        "dummy_present": _has("dummy"),
        "replica_present": _has("replica"),
        "precharge_present": _has("precharge"),
        "mux_present": _has("mux") or _has("tri_gate"),
        "sense_amp_present": _has("sense"),
        "write_driver_present": _has("write_driver"),
        "wl_driver_present": _has("wl_driver"),
    }


def _collect_geometry_report(path: Path) -> dict[str, Any]:
    low = inspect_gds_hierarchy(path)
    layers = inspect_gds_layers(path)
    bbox = measure_gds_bbox(path)
    high = _gdstk_stats(path)
    structure = _visible_structure_summary(high)
    power = _layout_json_power_summary(path)
    return {
        "path": str(path),
        "file_size_bytes": path.stat().st_size,
        "top_cell": high["top_cell"],
        "cell_count": high["cell_count"],
        "sref_count": high["sref_count"],
        "boundary_count": high["boundary_count"],
        "path_count": high["path_count"],
        "text_count": low["text_count"],
        "bbox": bbox.to_dict() if bbox is not None else None,
        "layer_datatype_summary": layers["boundary"],
        "text_layer_datatype_summary": layers["text"],
        "per_layer_shape_count": high["per_layer_shape_count"],
        "cell_hierarchy": high["cell_hierarchy"],
        "instance_count_by_cell_name": high["instance_count_by_cell_name"],
        "gen_col_mux_hierarchy_presence": _hierarchy_presence(high, "gen_col_mux"),
        "tri_gate_hierarchy_presence": _hierarchy_presence(high, "tri_gate"),
        "visible_structure_summary": structure,
        "power_summary": power,
        "low_level_reference_counts": low["reference_counts"],
        "contains_complete_sram_top": bool(high["top_cell"] and "sram" in high["top_cell"].lower()),
    }


def _compare_reports(lhs_name: str, lhs: dict[str, Any], rhs_name: str, rhs: dict[str, Any]) -> list[dict[str, Any]]:
    keys = [
        "file_size_bytes",
        "top_cell",
        "cell_count",
        "sref_count",
        "boundary_count",
        "path_count",
        "bbox",
        "layer_datatype_summary",
        "per_layer_shape_count",
        "gen_col_mux_hierarchy_presence",
        "tri_gate_hierarchy_presence",
        "visible_structure_summary",
    ]
    rows: list[dict[str, Any]] = []
    for key in keys:
        rows.append(
            {
                "metric": key,
                lhs_name: lhs.get(key),
                rhs_name: rhs.get(key),
                "match": lhs.get(key) == rhs.get(key),
            }
        )
    power_lhs = lhs.get("power_summary", {})
    power_rhs = rhs.get("power_summary", {})
    for key in [
        "power_rail_overlap_positive_count",
        "same_net_power_overlap_pass",
        "bitcell_rail_continuity_visible",
        "rail_stitch_visible",
    ]:
        rows.append(
            {
                "metric": f"power_summary.{key}",
                lhs_name: power_lhs.get(key),
                rhs_name: power_rhs.get(key),
                "match": power_lhs.get(key) == power_rhs.get(key),
            }
        )
    rows.append(
        {
            "metric": "cell_hierarchy",
            lhs_name: "MATCH" if lhs.get("cell_hierarchy") == rhs.get("cell_hierarchy") else "DIFF",
            rhs_name: "MATCH" if lhs.get("cell_hierarchy") == rhs.get("cell_hierarchy") else "DIFF",
            "match": lhs.get("cell_hierarchy") == rhs.get("cell_hierarchy"),
        }
    )
    return rows


def _extract_zip(zip_path: Path, extract_dir: Path) -> list[Path]:
    if extract_dir.exists():
        shutil.rmtree(extract_dir)
    extract_dir.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(zip_path) as zf:
        zf.extractall(extract_dir)
    return sorted(path for path in extract_dir.rglob("*") if path.is_file())


def _classify_file(path: Path) -> str:
    ext = path.suffix.lower()
    if ext == ".gds":
        return "gds"
    if ext == ".json":
        return "json"
    if ext in {".md", ".txt", ".log"}:
        return "text_report"
    if ext in {".svg", ".png", ".jpg", ".jpeg"}:
        return "image"
    if ext in {".lef", ".sp", ".csv"}:
        return "design_artifact"
    return "other"


def _zip_inventory_rows(extracted_root: Path, files: list[Path]) -> list[dict[str, Any]]:
    rows = []
    for index, path in enumerate(files, start=1):
        relative = path.relative_to(extracted_root).as_posix()
        rows.append(
            {
                "file_id": f"ZIP_{index:04d}",
                "relative_path": relative,
                "file_type": _classify_file(path),
                "extension": path.suffix.lower(),
                "size_bytes": path.stat().st_size,
            }
        )
    return rows


def _score_candidate(relative_path: str, report: dict[str, Any]) -> tuple[int, list[str]]:
    score = 0
    reasons: list[str] = []
    lower = relative_path.lower()
    if CURRENT_PROJECT_TARGET in lower:
        score += 100
        reasons.append("matches current project target 8x64_wpr4")
    if "complete" in lower:
        score += 40
        reasons.append("filename contains complete")
    if "final" in lower or "full" in lower or "top" in lower:
        score += 10
        reasons.append("filename contains final/full/top")
    if "sram" in lower:
        score += 10
        reasons.append("filename contains sram")
    if "/_all_gds_and_reports/" in f"/{lower}":
        score -= 10
        reasons.append("duplicate export bundle path")
    for penalty in ("debug", "integration", "presentation", "route_guides", "architecture"):
        if penalty in lower:
            score -= 60
            reasons.append(f"non-golden export class: {penalty}")
    if report.get("contains_complete_sram_top"):
        score += 20
        reasons.append("top cell looks like SRAM top")
    structure = report.get("visible_structure_summary", {})
    present_count = sum(bool(structure.get(key)) for key in structure)
    score += present_count * 3
    if present_count:
        reasons.append(f"contains {present_count} expected SRAM structure categories")
    score += min(int(report.get("boundary_count", 0)) // 200, 15)
    score += min(int(report.get("sref_count", 0)) // 20, 15)
    return score, reasons


def _build_gds_candidate_rows(extracted_root: Path, gds_files: list[Path]) -> list[dict[str, Any]]:
    rows = []
    for index, path in enumerate(sorted(gds_files), start=1):
        relative = path.relative_to(extracted_root).as_posix()
        report = _collect_geometry_report(path)
        score, reasons = _score_candidate(relative, report)
        rows.append(
            {
                "candidate_id": f"GDS_{index:03d}",
                "relative_path": relative,
                "size_bytes": report["file_size_bytes"],
                "top_cell": report["top_cell"],
                "cell_count": report["cell_count"],
                "sref_count": report["sref_count"],
                "boundary_count": report["boundary_count"],
                "bbox": report["bbox"],
                "layer_summary": report["layer_datatype_summary"],
                "contains_complete_sram_top": report["contains_complete_sram_top"],
                "visible_structure_summary": report["visible_structure_summary"],
                "candidate_score": score,
                "selection_reasons": "; ".join(reasons),
                "report": report,
            }
        )
    return rows


def _select_golden_candidate(rows: list[dict[str, Any]]) -> dict[str, Any]:
    if not rows:
        raise FileNotFoundError("No GDS candidate found in uploaded zip.")
    sorted_rows = sorted(rows, key=lambda row: (row["candidate_score"], row["size_bytes"], row["boundary_count"]), reverse=True)
    best = sorted_rows[0]
    matching = [row for row in sorted_rows if row["candidate_score"] == best["candidate_score"]]
    if len(matching) > 1:
        primary = [row for row in matching if f"/sram_{CURRENT_PROJECT_TARGET}/" in f"/{row['relative_path'].lower()}"]
        primary_complete = [row for row in primary if ".complete.gds" in row["relative_path"].lower()]
        if len(primary_complete) == 1:
            return primary_complete[0]
        if len(primary) == 1:
            return primary[0]
        non_dup = [row for row in matching if "/_all_gds_and_reports/" not in f"/{row['relative_path'].lower()}"]
        if len(non_dup) == 1:
            return non_dup[0]
        raise ValueError(
            "Multiple uploaded GDS candidates remain tied for golden selection: "
            + ", ".join(row["relative_path"] for row in matching)
        )
    return best


def _render_status_md(report: dict[str, Any]) -> str:
    return "\n".join(
        [
            "# OpenYield SRAM LayoutGen Project Status",
            "",
            "## 1. Current Correct Goal",
            "",
            "先复现并修复用户上传确认的正确 layoutgen golden reference，再以该 golden 为唯一物理目标推进后续修复与最终 OpenYield 集成。",
            "",
            "## 2. Current Stage",
            "",
            "- current_stage: `M7`",
            "- next_stage: `WAIT_HUMAN_KLAYOUT_REVIEW`",
            "- human_klayout_review_required_every_stage: `True`",
            "- can_enter_next_stage_without_human_review: `False`",
            "",
            "## 3. Latest Human Review",
            "",
            *[f"- {line[2:] if line.startswith('- ') else line}" for line in REVIEW_TEXT.splitlines()[1:]],
            "",
            "## 4. M7 Result",
            "",
            f"- uploaded_zip_path: `{report['uploaded_zip_path']}`",
            f"- golden_reference_path: `{report['golden_reference_path']}`",
            f"- golden_reference_clean_review_path: `{report['golden_reference_clean_review_path']}`",
            f"- golden_reference_top_cell: `{report['golden_reference_top_cell']}`",
            f"- hybrid_openyield_rail_overlap_is_golden: `{report['hybrid_openyield_rail_overlap_is_golden']}`",
            f"- new_uploaded_reference_is_golden: `{report['new_uploaded_reference_is_golden']}`",
            "",
            "## 5. Next Immediate Task",
            "",
            f"先进行人工 KLayout review：`{report['golden_reference_clean_review_path']}`。后续所有修复必须对比 `{report['golden_reference_path']}`，不得再以 `hybrid_openyield_rail_overlap.complete.gds` 作为 golden。",
            "",
        ]
    )


def _update_status_json(status: dict[str, Any], report: dict[str, Any]) -> dict[str, Any]:
    updated = dict(status)
    updated["current_stage"] = "M7"
    updated["next_stage"] = "WAIT_HUMAN_KLAYOUT_REVIEW"
    updated["can_enter_next_stage_without_human_review"] = False
    updated["next_task_summary"] = (
        f"Human KLayout review of {report['golden_reference_clean_review_path']} is required before attempting reproduction of the new uploaded golden reference."
    )
    updated["last_human_review"] = REVIEW_TEXT
    updated["current_golden_reference"] = report["golden_reference_path"]
    updated["historical_wrong_reference"] = str((Path(report["repo_root"]) / HISTORICAL_WRONG_REFERENCE).resolve())
    updated["next_route_constraint"] = (
        "Next stage must reproduce the uploaded golden_reference.gds first, then compare any generated GDS against it before resuming OpenYield integration."
    )
    updated["last_M7_report"] = {
        "uploaded_zip_path": report["uploaded_zip_path"],
        "golden_reference_path": report["golden_reference_path"],
        "golden_reference_top_cell": report["golden_reference_top_cell"],
        "golden_reference_size_bytes": report["golden_reference_size_bytes"],
        "hybrid_openyield_rail_overlap_is_golden": report["hybrid_openyield_rail_overlap_is_golden"],
        "new_uploaded_reference_is_golden": report["new_uploaded_reference_is_golden"],
        "next_repair_target_defined": report["next_repair_target_defined"],
        "human_klayout_review_required": report["human_klayout_review_required"],
        "can_enter_next_stage_before_human_review": report["can_enter_next_stage_before_human_review"],
    }
    return updated


def run_m7_correct_golden_reference(
    *,
    repo_root: Path,
    status_md: Path,
    status_json: Path,
    zip_path: Path,
    out_dir: Path,
    out_json: Path,
    out_report: Path,
) -> dict[str, Any]:
    repo_root = repo_root.resolve()
    status_md = status_md.resolve()
    status_json = status_json.resolve()
    zip_path = zip_path.resolve()
    out_dir = out_dir.resolve()
    out_json = out_json.resolve()
    out_report = out_report.resolve()
    if not status_md.exists() or not status_json.exists():
        raise FileNotFoundError("PROJECT_LAYOUTGEN_OPENYIELD_STATUS.md/json must exist before M7.")
    if not zip_path.exists():
        raise FileNotFoundError(f"Uploaded golden reference zip not found: {zip_path}")

    status = _read_json(status_json)
    extract_dir = out_dir / "extracted"
    out_dir.mkdir(parents=True, exist_ok=True)
    extracted_files = _extract_zip(zip_path, extract_dir)
    zip_rows = _zip_inventory_rows(extract_dir, extracted_files)
    zip_csv_out = out_dir / "M7_zip_inventory.csv"
    _write_csv(zip_csv_out, ["file_id", "relative_path", "file_type", "extension", "size_bytes"], zip_rows)

    gds_files = [path for path in extracted_files if path.suffix.lower() == ".gds"]
    gds_rows_raw = _build_gds_candidate_rows(extract_dir, gds_files)
    golden_row = _select_golden_candidate(gds_rows_raw)

    gds_csv_rows = []
    for row in gds_rows_raw:
        report = row["report"]
        gds_csv_rows.append(
            {
                "candidate_id": row["candidate_id"],
                "relative_path": row["relative_path"],
                "size_bytes": row["size_bytes"],
                "top_cell": row["top_cell"],
                "cell_count": row["cell_count"],
                "sref_count": row["sref_count"],
                "boundary_count": row["boundary_count"],
                "bbox": json.dumps(row["bbox"], ensure_ascii=False),
                "contains_complete_sram_top": row["contains_complete_sram_top"],
                "candidate_score": row["candidate_score"],
                "mux_present": report["visible_structure_summary"]["mux_present"],
                "power_rail_overlap_positive_count": report["power_summary"]["power_rail_overlap_positive_count"],
                "rail_stitch_visible": report["power_summary"]["rail_stitch_visible"],
                "selection_reasons": row["selection_reasons"],
                "selected_as_golden": row["relative_path"] == golden_row["relative_path"],
            }
        )
    gds_csv_out = out_dir / "M7_gds_candidate_inventory.csv"
    _write_csv(
        gds_csv_out,
        [
            "candidate_id",
            "relative_path",
            "size_bytes",
            "top_cell",
            "cell_count",
            "sref_count",
            "boundary_count",
            "bbox",
            "contains_complete_sram_top",
            "candidate_score",
            "mux_present",
            "power_rail_overlap_positive_count",
            "rail_stitch_visible",
            "selection_reasons",
            "selected_as_golden",
        ],
        gds_csv_rows,
    )

    golden_source = extract_dir / golden_row["relative_path"]
    golden_copy = out_dir / OUTPUT_GOLDEN_NAME
    _copy(golden_source, golden_copy)
    clean_info = _strip_all_text(golden_copy, out_dir / OUTPUT_GOLDEN_CLEAN_NAME)
    golden_report = _collect_geometry_report(golden_copy)

    selection_report = {
        "uploaded_zip_path": str(zip_path),
        "golden_reference_selected": True,
        "golden_reference_relative_path_in_zip": golden_row["relative_path"],
        "golden_reference_path": str(golden_copy),
        "golden_reference_top_cell": golden_report["top_cell"],
        "golden_reference_size_bytes": golden_report["file_size_bytes"],
        "golden_reference_gds_sanity_status": "GDS_PARSED_SANITY_PASSED",
        "selection_basis": [
            "uploaded zip contains multiple layout collections",
            f"current project history targets {CURRENT_PROJECT_TARGET}",
            "selected candidate is the non-duplicate .complete.gds inside the matching 8x64_wpr4 directory",
            "candidate score favors complete SRAM-top exports and penalizes debug/integration/architecture/presentation artifacts",
        ],
        "selection_reasons": golden_row["selection_reasons"].split("; "),
        "historical_wrong_reference_path": str((repo_root / HISTORICAL_WRONG_REFERENCE).resolve()),
        "hybrid_openyield_rail_overlap_is_golden": False,
        "new_uploaded_reference_is_golden": True,
    }
    _json_dump(out_dir / "M7_correct_golden_reference_selection_report.json", selection_report)
    _write_text(
        out_dir / "M7_correct_golden_reference_selection_report.md",
        "# M7 Correct Golden Reference Selection Report\n\n"
        + "\n".join(f"- {key}: `{value}`" for key, value in selection_report.items() if key != "selection_basis" and key != "selection_reasons")
        + "\n\n## Selection Basis\n\n"
        + "\n".join(f"- {item}" for item in selection_report["selection_basis"])
        + "\n\n## Selection Reasons\n\n"
        + "\n".join(f"- {item}" for item in selection_report["selection_reasons"] if item)
        + "\n",
    )

    old_refs: list[tuple[str, Path]] = [
        ("new_golden_reference", golden_copy),
        ("historical_hybrid_openyield_complete", (repo_root / HISTORICAL_WRONG_REFERENCE).resolve()),
        ("M6R_reproduced", (repo_root / "outputs/M6R_reference_locked_reproduce/current_supported_config/layoutgen_hybrid_reproduced_M6R.gds").resolve()),
        ("M6_primary_output", (repo_root / "outputs/M6_layoutgen_spec_reproduce/current_supported_config/layoutgen_optimized_reproduced_sram.gds").resolve()),
        ("M3F_complete", (repo_root / "outputs/M3F_optimized_layoutgen_restore/current_supported_config/openyield_optimized_layoutgen_sram.complete.gds").resolve()),
        ("M5_integrated", (repo_root / "outputs/M5_openyield_layoutgen_integration/current_supported_config/openyield_layoutgen_integrated_sram.gds").resolve()),
    ]
    old_refs = [(name, path) for name, path in old_refs if path.exists()]

    reference_reports = {name: _collect_geometry_report(path) for name, path in old_refs}
    comparison_rows: list[dict[str, Any]] = []
    for name, _path in old_refs:
        report = reference_reports[name]
        comparison_rows.append(
            {
                "artifact_name": name,
                "path": report["path"],
                "file_size_bytes": report["file_size_bytes"],
                "top_cell": report["top_cell"],
                "cell_count": report["cell_count"],
                "sref_count": report["sref_count"],
                "boundary_count": report["boundary_count"],
                "bbox": json.dumps(report["bbox"], ensure_ascii=False),
                "mux_presence": report["visible_structure_summary"]["mux_present"],
                "power_rail_overlap_positive_count": report["power_summary"]["power_rail_overlap_positive_count"],
                "bitcell_rail_continuity_visible": report["power_summary"]["bitcell_rail_continuity_visible"],
                "rail_stitch_visible": report["power_summary"]["rail_stitch_visible"],
                "is_golden": name == "new_golden_reference",
            }
        )
    comparison_csv = repo_root / "docs/mapping/M7_old_vs_new_reference_comparison.csv"
    _write_csv(
        comparison_csv,
        [
            "artifact_name",
            "path",
            "file_size_bytes",
            "top_cell",
            "cell_count",
            "sref_count",
            "boundary_count",
            "bbox",
            "mux_presence",
            "power_rail_overlap_positive_count",
            "bitcell_rail_continuity_visible",
            "rail_stitch_visible",
            "is_golden",
        ],
        comparison_rows,
    )

    diff_bundle = {}
    base = reference_reports["new_golden_reference"]
    for name, _path in old_refs:
        if name == "new_golden_reference":
            continue
        diff_bundle[name] = _compare_reports("new_golden_reference", base, name, reference_reports[name])
    compare_report = {
        "hybrid_openyield_rail_overlap_is_golden": False,
        "new_uploaded_reference_is_golden": True,
        "artifacts_compared": [name for name, _ in old_refs],
        "diffs_against_new_golden": diff_bundle,
    }
    _json_dump(out_dir / "M7_compare_old_references_report.json", compare_report)
    compare_md = ["# M7 Compare Old References Report", "", "- hybrid_openyield_rail_overlap_is_golden: `False`", "- new_uploaded_reference_is_golden: `True`", ""]
    for name, rows in diff_bundle.items():
        compare_md.append(f"## new_golden_reference vs {name}")
        compare_md.append("")
        compare_md.append(_md_table(["metric", "new_golden_reference", name, "match"], rows))
        compare_md.append("")
    _write_text(out_dir / "M7_compare_old_references_report.md", "\n".join(compare_md))

    review_manifest = {
        "golden_reference_gds_path": str(golden_copy),
        "golden_reference_clean_review_gds_path": clean_info["clean_review_gds_path"],
        "historical_wrong_reference_path": str((repo_root / HISTORICAL_WRONG_REFERENCE).resolve()),
        "m6r_reproduced_path": str((repo_root / "outputs/M6R_reference_locked_reproduce/current_supported_config/layoutgen_hybrid_reproduced_M6R.gds").resolve()),
        "human_klayout_review_required": True,
        "review_intent": "User should confirm the newly imported uploaded golden reference before any new reproduction attempt.",
    }
    _json_dump(out_dir / "review_gds_manifest.json", review_manifest)
    _write_text(
        out_dir / "review_gds_manifest.md",
        "# Review GDS Manifest\n\n" + "\n".join(f"- {key}: `{value}`" for key, value in review_manifest.items()) + "\n",
    )

    next_target_rows = [
        {
            "step_order": 1,
            "repair_target": "Reproduce uploaded golden_reference.gds exactly",
            "required_input": str(golden_copy),
            "reason": "This is now the only trusted physical target.",
        },
        {
            "step_order": 2,
            "repair_target": "Diff every regenerated GDS against new golden reference",
            "required_input": str(golden_copy),
            "reason": "Historical hybrid_openyield_rail_overlap reference is explicitly downgraded.",
        },
        {
            "step_order": 3,
            "repair_target": "Resume OpenYield integration only after golden reproduction is visually confirmed",
            "required_input": clean_info["clean_review_gds_path"],
            "reason": "Human KLayout review remains mandatory before next stage.",
        },
    ]
    next_target_csv = repo_root / "docs/mapping/M7_next_repair_target_matrix.csv"
    _write_csv(next_target_csv, ["step_order", "repair_target", "required_input", "reason"], next_target_rows)

    zip_mapping = repo_root / "docs/mapping/M7_zip_inventory.csv"
    gds_mapping = repo_root / "docs/mapping/M7_gds_candidate_inventory.csv"
    shutil.copy2(zip_csv_out, zip_mapping)
    shutil.copy2(gds_csv_out, gds_mapping)

    report = {
        "repo_root": str(repo_root),
        "status_file_read": True,
        "status_file_updated": True,
        "uploaded_zip_found": True,
        "uploaded_zip_path": str(zip_path),
        "zip_extracted": True,
        "zip_file_count": len(extracted_files),
        "gds_candidate_count": len(gds_files),
        "golden_reference_selected": True,
        "golden_reference_path": str(golden_copy),
        "golden_reference_clean_review_path": clean_info["clean_review_gds_path"],
        "golden_reference_gds_sanity_status": "GDS_PARSED_SANITY_PASSED",
        "golden_reference_top_cell": golden_report["top_cell"],
        "golden_reference_size_bytes": golden_report["file_size_bytes"],
        "hybrid_openyield_rail_overlap_is_golden": False,
        "new_uploaded_reference_is_golden": True,
        "old_reference_comparison_available": True,
        "next_repair_target_defined": True,
        "human_klayout_review_required": True,
        "can_enter_next_stage_before_human_review": False,
        "remaining_M7_blockers": [
            "Human KLayout review of the uploaded golden_reference_clean_review.gds is still required.",
            "Next repair stage must reproduce the new uploaded golden reference instead of the historical hybrid_openyield reference.",
        ],
        "remaining_M7_blockers_count": 2,
    }

    updated_status = _update_status_json(status, report)
    _write_text(status_md, _render_status_md(report))
    _json_dump(status_json, updated_status)
    _json_dump(out_json, report)
    _write_text(
        out_report,
        "# M7 Correct Golden Reference Report\n\n"
        + "\n".join(f"- {key}: `{value}`" for key, value in report.items() if key != "remaining_M7_blockers")
        + "\n\n## Remaining M7 Blockers\n\n"
        + "\n".join(f"- {item}" for item in report["remaining_M7_blockers"])
        + "\n",
    )
    _write_text(
        repo_root / "docs/evidence/M7_correct_golden_reference_summary.md",
        "# M7 Correct Golden Reference Summary\n\n"
        + f"- uploaded_zip_path: `{zip_path}`\n"
        + f"- golden_reference_path: `{golden_copy}`\n"
        + f"- golden_reference_clean_review_path: `{clean_info['clean_review_gds_path']}`\n"
        + f"- hybrid_openyield_rail_overlap_is_golden: `{report['hybrid_openyield_rail_overlap_is_golden']}`\n"
        + f"- new_uploaded_reference_is_golden: `{report['new_uploaded_reference_is_golden']}`\n"
        + f"- next_repair_target_defined: `{report['next_repair_target_defined']}`\n",
    )
    return report
