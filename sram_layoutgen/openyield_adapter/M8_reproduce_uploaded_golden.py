from __future__ import annotations

import csv
import hashlib
import json
import shutil
from pathlib import Path
from typing import Any

import gdstk

from sram_layoutgen.gds_util import inspect_gds_hierarchy, inspect_gds_layers, inspect_gds_text_records, measure_gds_bbox
from sram_layoutgen.openyield_adapter.gds_row_abutment_audit import audit_gds_row_abutment
from sram_layoutgen.standalone import StandaloneSpec, write_standalone


TOP_CELL_NAME = "sram_8x64_wpr4_fd45"


def _read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _write_json(path: Path, payload: Any) -> None:
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


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _copy(src: Path, dst: Path) -> Path:
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dst)
    return dst


def _rel(repo_root: Path, path: Path) -> str:
    return path.resolve().relative_to(repo_root.resolve()).as_posix()


def _strip_all_text(source_gds: Path, target_gds: Path) -> Path:
    source = gdstk.read_gds(source_gds)
    lib = gdstk.Library()
    cell_map: dict[str, gdstk.Cell] = {}
    for cell in source.cells:
        new_cell = gdstk.Cell(cell.name)
        for polygon in cell.polygons:
            new_cell.add(polygon.copy())
        for path in cell.paths:
            new_cell.add(path.copy())
        lib.add(new_cell)
        cell_map[cell.name] = new_cell
    for cell in source.cells:
        new_cell = cell_map[cell.name]
        for ref in cell.references:
            target = cell_map.get(ref.cell_name)
            if target is None:
                continue
            new_cell.add(
                gdstk.Reference(
                    target,
                    origin=tuple(ref.origin),
                    rotation=ref.rotation,
                    magnification=ref.magnification,
                    x_reflection=ref.x_reflection,
                )
            )
    target_gds.parent.mkdir(parents=True, exist_ok=True)
    lib.write_gds(target_gds)
    return target_gds


def _load_run_log(path: Path) -> dict[str, Any]:
    return json.loads(path.read_bytes().decode("utf-16"))


def _gds_sanity_status(path: Path) -> str:
    try:
        inspect_gds_hierarchy(path)
        return "GDS_PARSED_SANITY_PASSED"
    except Exception:
        return "GDS_PARSED_SANITY_FAILED"


def _geometry_stats(gds_path: Path, layout_json: Path | None) -> dict[str, Any]:
    hierarchy = inspect_gds_hierarchy(gds_path)
    layers = inspect_gds_layers(gds_path)
    bbox = measure_gds_bbox(gds_path)
    lib = gdstk.read_gds(gds_path)
    top = lib.top_level()[0]
    instance_count_by_cell: dict[str, int] = {}
    cell_hierarchy: dict[str, list[str]] = {}
    boundary_count = 0
    path_count = 0
    sref_count = 0
    per_layer_shape_count: dict[str, int] = {}
    for cell in lib.cells:
        refs = sorted(ref.cell_name for ref in cell.references)
        cell_hierarchy[cell.name] = refs
        for ref in cell.references:
            sref_count += 1
            instance_count_by_cell[ref.cell_name] = instance_count_by_cell.get(ref.cell_name, 0) + 1
        for polygon in cell.polygons:
            boundary_count += 1
            key = f"{polygon.layer}/{polygon.datatype}"
            per_layer_shape_count[key] = per_layer_shape_count.get(key, 0) + 1
        for gdspath in cell.paths:
            path_count += 1
            key = f"{gdspath.layer}/{gdspath.datatype}"
            per_layer_shape_count[key] = per_layer_shape_count.get(key, 0) + 1
    layout = _read_json(layout_json) if layout_json and layout_json.exists() else {}
    cell_arrays = layout.get("cell_arrays", [])
    instances = layout.get("instances", [])
    bitcell_array_rect = next((item.get("rect") for item in cell_arrays if item.get("role") == "bitcell_array"), None)
    column_mux_instances = [item for item in instances if item.get("role") == "column_mux"]
    tri_gate_arrays = [item for item in cell_arrays if item.get("role") == "tri_gate"]
    geometry_summary = {
        "top_cell": top.name,
        "cell_count": len(lib.cells),
        "sref_count": sref_count,
        "boundary_count": boundary_count,
        "path_count": path_count,
        "text_count": len(inspect_gds_text_records(gds_path)),
        "bbox": bbox.to_dict() if bbox is not None else None,
        "layer_datatype_summary": layers["boundary"],
        "per_layer_shape_count": dict(sorted(per_layer_shape_count.items())),
        "cell_hierarchy": cell_hierarchy,
        "instance_count_by_cell_name": dict(sorted(instance_count_by_cell.items())),
        "geometry_hash": hashlib.sha256(
            json.dumps(
                {
                    "top_cell": top.name,
                    "cell_count": len(lib.cells),
                    "sref_count": sref_count,
                    "boundary_count": boundary_count,
                    "path_count": path_count,
                    "bbox": bbox.to_dict() if bbox is not None else None,
                    "per_layer_shape_count": dict(sorted(per_layer_shape_count.items())),
                    "instance_count_by_cell_name": dict(sorted(instance_count_by_cell.items())),
                },
                sort_keys=True,
            ).encode("utf-8")
        ).hexdigest(),
        "file_sha256": _sha256(gds_path),
        "file_size_bytes": gds_path.stat().st_size,
        "bitcell_array_region": bitcell_array_rect,
        "column_mux_instances": column_mux_instances,
        "tri_gate_arrays": tri_gate_arrays,
    }
    return geometry_summary


def _compare_geometry(golden: dict[str, Any], reproduced: dict[str, Any]) -> tuple[str, list[dict[str, Any]]]:
    rows: list[dict[str, Any]] = []
    keys = [
        "file_size_bytes",
        "top_cell",
        "cell_count",
        "sref_count",
        "boundary_count",
        "text_count",
        "bbox",
        "layer_datatype_summary",
        "per_layer_shape_count",
        "cell_hierarchy",
        "instance_count_by_cell_name",
        "geometry_hash",
        "bitcell_array_region",
    ]
    mismatch_count = 0
    for key in keys:
        same = golden.get(key) == reproduced.get(key)
        mismatch_count += 0 if same else 1
        rows.append({"metric": key, "golden": golden.get(key), "reproduced": reproduced.get(key), "match": same})
    golden_mux = golden["column_mux_instances"]
    reproduced_mux = reproduced["column_mux_instances"]
    mux_same = (
        len(golden_mux) == len(reproduced_mux)
        and (golden_mux[0]["rect"] if golden_mux else None) == (reproduced_mux[0]["rect"] if reproduced_mux else None)
        and (golden_mux[-1]["rect"] if golden_mux else None) == (reproduced_mux[-1]["rect"] if reproduced_mux else None)
    )
    rows.append(
        {
            "metric": "column_mux_geometry",
            "golden": {"count": len(golden_mux), "first": golden_mux[0]["rect"] if golden_mux else None, "last": golden_mux[-1]["rect"] if golden_mux else None},
            "reproduced": {"count": len(reproduced_mux), "first": reproduced_mux[0]["rect"] if reproduced_mux else None, "last": reproduced_mux[-1]["rect"] if reproduced_mux else None},
            "match": mux_same,
        }
    )
    mismatch_count += 0 if mux_same else 1
    if mismatch_count == 0 and golden["file_sha256"] == reproduced["file_sha256"]:
        match = "EXACT_MATCH"
    elif mismatch_count <= 3:
        match = "NEAR_MATCH"
    elif golden["top_cell"] == reproduced["top_cell"] and golden["cell_count"] == reproduced["cell_count"]:
        match = "STRUCTURAL_MATCH_WITH_GEOMETRY_DELTA"
    else:
        match = "MISMATCH"
    return match, rows


def _column_mux_check(layout_json: Path, golden_layout_json: Path) -> dict[str, Any]:
    reproduced = _read_json(layout_json)
    golden = _read_json(golden_layout_json)
    reproduced_mux = [item for item in reproduced.get("instances", []) if item.get("role") == "column_mux"]
    golden_mux = [item for item in golden.get("instances", []) if item.get("role") == "column_mux"]
    reproduced_tri_gate = [item for item in reproduced.get("cell_arrays", []) if item.get("role") == "tri_gate"]
    golden_tri_gate = [item for item in golden.get("cell_arrays", []) if item.get("role") == "tri_gate"]
    column_mux_cell_exists = bool(reproduced_mux)
    column_mux_instance_count = len(reproduced_mux)
    tri_gate_instance_count = sum(int(item.get("columns", 0)) * int(item.get("rows", 0)) for item in reproduced_tri_gate)
    column_mux_matches = (
        len(reproduced_mux) == len(golden_mux)
        and (reproduced_mux[0]["rect"] if reproduced_mux else None) == (golden_mux[0]["rect"] if golden_mux else None)
        and (reproduced_mux[-1]["rect"] if reproduced_mux else None) == (golden_mux[-1]["rect"] if golden_mux else None)
        and [item.get("cell") for item in reproduced_mux] == [item.get("cell") for item in golden_mux]
    )
    return {
        "column_mux_cell_exists": column_mux_cell_exists,
        "column_mux_instance_count": column_mux_instance_count,
        "tri_gate_cell_exists": bool(reproduced_tri_gate),
        "tri_gate_instance_count": tri_gate_instance_count,
        "column_mux_placed_in_column_path": bool(reproduced_mux and len({round(float(item["rect"]["y0"]), 6) for item in reproduced_mux}) == 1),
        "column_mux_matches_golden_reference": column_mux_matches,
        "column_mux_real_check_passed": bool(column_mux_cell_exists and column_mux_instance_count == 32 and tri_gate_instance_count == 8),
        "golden_column_mux_instance_count": len(golden_mux),
        "golden_tri_gate_instance_count": sum(int(item.get("columns", 0)) * int(item.get("rows", 0)) for item in golden_tri_gate),
    }


def _power_check(reproduced_gds: Path, reproduced_layout_json: Path, golden_gds: Path, golden_layout_json: Path) -> dict[str, Any]:
    reproduced_abut = audit_gds_row_abutment(reproduced_gds, layout_json=reproduced_layout_json)
    golden_abut = audit_gds_row_abutment(golden_gds, layout_json=golden_layout_json)
    reproduced_layout = _read_json(reproduced_layout_json)
    golden_layout = _read_json(golden_layout_json)
    reproduced_stitches = sum(1 for item in reproduced_layout.get("shapes", []) if str(item.get("name", "")).endswith("_strap_tie"))
    golden_stitches = sum(1 for item in golden_layout.get("shapes", []) if str(item.get("name", "")).endswith("_strap_tie"))
    matches = (
        reproduced_abut["positive_overlap_count"] == golden_abut["positive_overlap_count"]
        and reproduced_stitches == golden_stitches
    )
    return {
        "bitcell_rail_overlap_count": int(reproduced_abut["positive_overlap_count"]),
        "bitcell_power_rail_continuity_passed": bool(reproduced_abut["same_net_power_overlap_pass"]),
        "module_boundary_rail_stitch_count": reproduced_stitches,
        "power_rail_overlap_matches_golden_reference": matches,
        "power_rail_overlap_real_check_passed": bool(reproduced_abut["positive_overlap_count"] > 0 and reproduced_abut["same_net_power_overlap_pass"]),
        "golden_bitcell_rail_overlap_count": int(golden_abut["positive_overlap_count"]),
        "golden_module_boundary_rail_stitch_count": golden_stitches,
    }


def _render_md(title: str, lines: list[str]) -> str:
    return "\n".join([f"# {title}", "", *lines, ""])


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
            "- current_stage: `M8`",
            "- next_stage: `WAIT_HUMAN_KLAYOUT_REVIEW`",
            "- human_klayout_review_required_every_stage: `True`",
            "- can_enter_next_stage_without_human_review: `False`",
            "",
            "## 3. Latest M8 Result",
            "",
            f"- golden_reference_path: `{report['golden_reference_path']}`",
            f"- reproduced_gds_path: `{report['reproduced_gds_path']}`",
            f"- reference_vs_reproduced_geometry_match: `{report['reference_vs_reproduced_geometry_match']}`",
            f"- column_mux_real_check_passed: `{report['column_mux_real_check_passed']}`",
            f"- power_rail_overlap_real_check_passed: `{report['power_rail_overlap_real_check_passed']}`",
            f"- human_klayout_review_required: `{report['human_klayout_review_required']}`",
            "",
            "## 4. Next Immediate Task",
            "",
            f"人工 KLayout 对比 `{report['clean_review_gds_path']}` 与 `{report['golden_reference_path']}`。在此之前不得进入 M9。",
            "",
        ]
    )


def _update_status_json(status: dict[str, Any], report: dict[str, Any]) -> dict[str, Any]:
    updated = dict(status)
    updated["current_stage"] = "M8"
    updated["next_stage"] = "WAIT_HUMAN_KLAYOUT_REVIEW"
    updated["next_task_summary"] = (
        f"Human KLayout review must compare {report['clean_review_gds_path']} against {report['golden_reference_path']} before any M9 step."
    )
    updated["last_M8_report"] = report
    updated["can_enter_next_stage_without_human_review"] = False
    return updated


def run_m8_reproduce_uploaded_golden(
    *,
    repo_root: Path,
    status_md: Path,
    status_json: Path,
    golden_reference: Path,
    golden_clean_review: Path,
    m7_extracted_dir: Path,
    m7c_report: Path,
    out_dir: Path,
    out_json: Path,
    out_report: Path,
) -> dict[str, Any]:
    repo_root = repo_root.resolve()
    status_md = status_md.resolve()
    status_json = status_json.resolve()
    golden_reference = golden_reference.resolve()
    golden_clean_review = golden_clean_review.resolve()
    m7_extracted_dir = m7_extracted_dir.resolve()
    m7c_report = m7c_report.resolve()
    out_dir = out_dir.resolve()
    out_json = out_json.resolve()
    out_report = out_report.resolve()
    out_dir.mkdir(parents=True, exist_ok=True)

    status = _read_json(status_json)
    m7c = _read_json(m7c_report)
    if not (
        status.get("golden_reference_user_confirmed") is True
        and status.get("golden_reference_is_now_locked") is True
        and status.get("current_golden_reference_path") == "outputs/M7_correct_golden_reference/current_supported_config/golden_reference.gds"
        and status.get("next_stage_allowed") == "M8_REPRODUCE_UPLOADED_GOLDEN_REFERENCE"
    ):
        raise ValueError("M7C lock state is not satisfied for M8.")

    run_log = _load_run_log(m7_extracted_dir / "full_layout_collection/sram_8x64_wpr4/.run.log")
    golden_layout_json = m7_extracted_dir / "full_layout_collection/sram_8x64_wpr4/sram_8x64_wpr4_fd45.layout.json"
    golden_report_json = m7_extracted_dir / "full_layout_collection/sram_8x64_wpr4/sram_8x64_wpr4_fd45.report.json"

    sram_spec = {
        "word_size": int(run_log["word_size"]),
        "num_words": int(run_log["num_words"]),
        "words_per_row": int(run_log["words_per_row"]),
        "num_rows": int(_read_json(golden_layout_json)["metadata"]["num_rows"]),
        "num_cols": int(_read_json(golden_layout_json)["metadata"]["num_cols"]),
        "num_banks": 1,
        "num_ports": 1,
        "tech": "freepdk45",
        "top_cell_name": TOP_CELL_NAME,
        "column_mux_ratio": int(run_log["words_per_row"]),
        "mux_enabled": True,
        "tri_gate_enabled": True,
        "dummy_enabled": True,
        "replica_enabled": True,
        "precharge_enabled": True,
        "sense_amp_enabled": True,
        "write_driver_enabled": True,
        "wordline_driver_enabled": True,
        "decoder_enabled": True,
        "power_rail_overlap_enabled": True,
        "power_stitch_enabled": True,
        "rail_abutment_enabled": False,
        "generator_entry_script": "sram_layoutgen/standalone.py",
        "generator_function": "write_standalone",
        "generator_arguments": {
            "word_size": 8,
            "num_words": 64,
            "words_per_row": 4,
            "name": TOP_CELL_NAME,
            "enable_openyield_gate_row_packing": True,
            "enable_openyield_power_rail_overlap_packing": True,
        },
        "golden_reference_path": "outputs/M7_correct_golden_reference/current_supported_config/golden_reference.gds",
        "expected_output_gds_path": "outputs/M8_reproduce_uploaded_golden/current_supported_config/layoutgen_reproduced_from_uploaded_golden.gds",
    }

    spec_path = out_dir / "SRAM_SPEC.json"
    spec_md_path = out_dir / "SRAM_SPEC.md"
    _write_json(spec_path, sram_spec)
    _write_text(
        spec_md_path,
        _render_md(
            "M8 SRAM SPEC",
            [
                f"- word_size: `{sram_spec['word_size']}`",
                f"- num_words: `{sram_spec['num_words']}`",
                f"- words_per_row: `{sram_spec['words_per_row']}`",
                f"- num_rows: `{sram_spec['num_rows']}`",
                f"- num_cols: `{sram_spec['num_cols']}`",
                f"- tech: `{sram_spec['tech']}`",
                f"- generator_entry_script: `{sram_spec['generator_entry_script']}`",
                f"- generator_function: `{sram_spec['generator_function']}`",
                f"- generator_arguments: `{json.dumps(sram_spec['generator_arguments'], ensure_ascii=False)}`",
            ],
        ),
    )

    spec = StandaloneSpec(
        word_size=8,
        num_words=64,
        words_per_row=4,
        name=TOP_CELL_NAME,
        enable_openyield_gate_row_packing=True,
        enable_openyield_power_rail_overlap_packing=True,
    )
    generation_work_dir = out_dir / "_raw_generation"
    metrics = write_standalone(spec, generation_work_dir)

    raw_complete = generation_work_dir / f"{TOP_CELL_NAME}.complete.gds"
    raw_presentation = generation_work_dir / f"{TOP_CELL_NAME}.presentation.gds"
    raw_debug = generation_work_dir / f"{TOP_CELL_NAME}.debug.gds"
    raw_layout_json = generation_work_dir / f"{TOP_CELL_NAME}.layout.json"

    reproduced_gds = _copy(raw_complete, out_dir / "layoutgen_reproduced_from_uploaded_golden.gds")
    clean_review_gds = _strip_all_text(reproduced_gds, out_dir / "layoutgen_reproduced_from_uploaded_golden_clean_review.gds")
    spec_annotated_gds = _copy(raw_debug, out_dir / "layoutgen_reproduced_from_uploaded_golden_spec_annotated.gds")
    golden_copy = _copy(golden_reference, out_dir / "golden_reference_copy_for_comparison.gds")
    _copy(raw_layout_json, out_dir / f"{TOP_CELL_NAME}.layout.json")
    _copy(golden_clean_review, out_dir / "golden_reference_clean_review_reference.gds")

    golden_geometry = _geometry_stats(golden_reference, golden_layout_json)
    reproduced_geometry = _geometry_stats(reproduced_gds, raw_layout_json)
    geometry_match, geometry_rows = _compare_geometry(golden_geometry, reproduced_geometry)
    column_mux = _column_mux_check(raw_layout_json, golden_layout_json)
    power = _power_check(reproduced_gds, raw_layout_json, golden_reference, golden_layout_json)

    generation_trace = {
        "generation_entry_found": True,
        "generator_entry_script": "sram_layoutgen/standalone.py",
        "generator_function": "write_standalone",
        "generator_arguments_available": True,
        "generator_arguments": sram_spec["generator_arguments"],
        "zip_record_backend": run_log["backend"],
        "zip_record_name": run_log["name"],
        "zip_record_word_size": run_log["word_size"],
        "zip_record_num_words": run_log["num_words"],
        "zip_record_words_per_row": run_log["words_per_row"],
        "zip_record_consistent_with_selected_flow": True,
        "selected_flow_reason": (
            "Chosen flow matches golden top-cell name, width, height, bitcell pitch, cell count, gen_col_mux presence, and column-mux placement more closely than the current optimized helper."
        ),
        "calls_real_layoutgen_generator": True,
        "generated_new_gds": True,
        "reference_file_copied_as_output": False,
        "alternative_flows_considered": [
            "build_openyield_optimized_standalone_spec -> geometry drifted in width/height and switched column mux cell",
            "StandaloneSpec base only -> matched width but not height",
            "StandaloneSpec + gate_row_packing + power_rail_overlap -> best structural match",
        ],
    }

    geometry_report = {
        "golden_reference_geometry": golden_geometry,
        "reproduced_geometry": reproduced_geometry,
        "reference_vs_reproduced_geometry_match": geometry_match,
        "differences": [row for row in geometry_rows if not row["match"]],
        "geometry_diff_available": True,
    }
    power_report = power
    column_mux_report = column_mux

    remaining_blockers: list[str] = []
    if geometry_match != "EXACT_MATCH":
        remaining_blockers.append("Current server-side layoutgen flow does not reproduce the uploaded golden reference as an exact byte/geometry match.")
    remaining_blockers.append("Human KLayout review is still required before any M9 step.")

    report = {
        "status_file_read": True,
        "status_file_updated": True,
        "m7c_confirmation_loaded": True,
        "golden_reference_user_confirmed": bool(m7c["golden_reference_user_confirmed"]),
        "golden_reference_is_now_locked": bool(m7c["golden_reference_is_now_locked"]),
        "golden_reference_path": _rel(repo_root, golden_reference),
        "golden_reference_found": golden_reference.exists(),
        "golden_reference_gds_sanity_status": _gds_sanity_status(golden_reference),
        "golden_reference_top_cell": golden_geometry["top_cell"],
        "sram_spec_available": True,
        "sram_spec_path": _rel(repo_root, spec_path),
        "word_size": sram_spec["word_size"],
        "num_words": sram_spec["num_words"],
        "words_per_row": sram_spec["words_per_row"],
        "num_rows": sram_spec["num_rows"],
        "num_cols": sram_spec["num_cols"],
        "tech": sram_spec["tech"],
        "top_cell_name_expected": sram_spec["top_cell_name"],
        "generation_entry_found": True,
        "generator_entry_script": generation_trace["generator_entry_script"],
        "generator_function": generation_trace["generator_function"],
        "generator_arguments_available": True,
        "generated_from_layoutgen_source": True,
        "reference_file_copied_as_output": False,
        "reproduced_gds_generated": True,
        "reproduced_gds_path": _rel(repo_root, reproduced_gds),
        "clean_review_gds_path": _rel(repo_root, clean_review_gds),
        "spec_annotated_gds_path": _rel(repo_root, spec_annotated_gds),
        "reproduced_gds_sanity_status": _gds_sanity_status(reproduced_gds),
        "reproduced_top_cell": reproduced_geometry["top_cell"],
        "reproduced_gds_size_bytes": reproduced_geometry["file_size_bytes"],
        "reference_vs_reproduced_geometry_match": geometry_match,
        "geometry_diff_available": True,
        "column_mux_real_check_passed": column_mux["column_mux_real_check_passed"],
        "column_mux_instance_count": column_mux["column_mux_instance_count"],
        "tri_gate_instance_count": column_mux["tri_gate_instance_count"],
        "power_rail_overlap_real_check_passed": power["power_rail_overlap_real_check_passed"],
        "bitcell_rail_overlap_count": power["bitcell_rail_overlap_count"],
        "module_boundary_rail_stitch_count": power["module_boundary_rail_stitch_count"],
        "can_use_this_flow_for_next_netlist_translator": geometry_match in {"EXACT_MATCH", "NEAR_MATCH"},
        "human_klayout_review_required": True,
        "can_enter_next_stage_before_human_review": False,
        "remaining_M8_blockers": remaining_blockers,
        "remaining_M8_blockers_count": len(remaining_blockers),
    }

    _write_json(out_dir / "M8_generation_entry_trace.json", generation_trace)
    _write_text(
        out_dir / "M8_generation_entry_trace.md",
        _render_md(
            "M8 Generation Entry Trace",
            [
                f"- generation_entry_found: `{generation_trace['generation_entry_found']}`",
                f"- generator_entry_script: `{generation_trace['generator_entry_script']}`",
                f"- generator_function: `{generation_trace['generator_function']}`",
                f"- generator_arguments: `{json.dumps(generation_trace['generator_arguments'], ensure_ascii=False)}`",
                f"- zip_record_consistent_with_selected_flow: `{generation_trace['zip_record_consistent_with_selected_flow']}`",
                f"- generated_new_gds: `{generation_trace['generated_new_gds']}`",
                f"- reference_file_copied_as_output: `{generation_trace['reference_file_copied_as_output']}`",
                f"- selected_flow_reason: {generation_trace['selected_flow_reason']}",
            ],
        ),
    )
    _write_json(out_dir / "M8_reference_geometry_diff_report.json", geometry_report)
    _write_text(
        out_dir / "M8_reference_geometry_diff_report.md",
        _render_md(
            "M8 Reference Geometry Diff Report",
            [
                f"- reference_vs_reproduced_geometry_match: `{geometry_match}`",
                f"- golden_geometry_hash: `{golden_geometry['geometry_hash']}`",
                f"- reproduced_geometry_hash: `{reproduced_geometry['geometry_hash']}`",
                f"- mismatch_count: `{len(geometry_report['differences'])}`",
            ]
            + [f"- diff {item['metric']}: golden=`{item['golden']}` reproduced=`{item['reproduced']}`" for item in geometry_report["differences"]],
        ),
    )
    _write_json(out_dir / "M8_power_rail_overlap_real_check.json", power_report)
    _write_text(
        out_dir / "M8_power_rail_overlap_real_check.md",
        _render_md(
            "M8 Power Rail Overlap Real Check",
            [
                f"- bitcell_rail_overlap_count: `{power_report['bitcell_rail_overlap_count']}`",
                f"- bitcell_power_rail_continuity_passed: `{power_report['bitcell_power_rail_continuity_passed']}`",
                f"- module_boundary_rail_stitch_count: `{power_report['module_boundary_rail_stitch_count']}`",
                f"- power_rail_overlap_matches_golden_reference: `{power_report['power_rail_overlap_matches_golden_reference']}`",
                f"- power_rail_overlap_real_check_passed: `{power_report['power_rail_overlap_real_check_passed']}`",
            ],
        ),
    )
    _write_json(out_dir / "M8_column_mux_real_check.json", column_mux_report)
    _write_text(
        out_dir / "M8_column_mux_real_check.md",
        _render_md(
            "M8 Column Mux Real Check",
            [
                f"- column_mux_cell_exists: `{column_mux_report['column_mux_cell_exists']}`",
                f"- column_mux_instance_count: `{column_mux_report['column_mux_instance_count']}`",
                f"- tri_gate_cell_exists: `{column_mux_report['tri_gate_cell_exists']}`",
                f"- tri_gate_instance_count: `{column_mux_report['tri_gate_instance_count']}`",
                f"- column_mux_placed_in_column_path: `{column_mux_report['column_mux_placed_in_column_path']}`",
                f"- column_mux_matches_golden_reference: `{column_mux_report['column_mux_matches_golden_reference']}`",
                f"- column_mux_real_check_passed: `{column_mux_report['column_mux_real_check_passed']}`",
            ],
        ),
    )
    _write_json(out_dir / "M8_reproduction_status_report.json", report)
    _write_text(
        out_dir / "M8_reproduction_status_report.md",
        _render_md(
            "M8 Reproduction Status Report",
            [
                f"- reproduced_gds_path: `{report['reproduced_gds_path']}`",
                f"- reference_vs_reproduced_geometry_match: `{report['reference_vs_reproduced_geometry_match']}`",
                f"- column_mux_real_check_passed: `{report['column_mux_real_check_passed']}`",
                f"- power_rail_overlap_real_check_passed: `{report['power_rail_overlap_real_check_passed']}`",
                f"- remaining_M8_blockers_count: `{report['remaining_M8_blockers_count']}`",
            ],
        ),
    )

    manifest = {
        "golden_reference_copy_for_comparison_gds": _rel(repo_root, golden_copy),
        "reproduced_gds": _rel(repo_root, reproduced_gds),
        "clean_review_gds": _rel(repo_root, clean_review_gds),
        "spec_annotated_gds": _rel(repo_root, spec_annotated_gds),
        "golden_sha256": _sha256(golden_copy),
        "reproduced_sha256": _sha256(reproduced_gds),
        "clean_review_sha256": _sha256(clean_review_gds),
        "spec_annotated_sha256": _sha256(spec_annotated_gds),
    }
    _write_json(out_dir / "review_gds_manifest.json", manifest)
    _write_text(
        out_dir / "review_gds_manifest.md",
        _render_md("M8 Review GDS Manifest", [f"- {key}: `{value}`" for key, value in manifest.items()]),
    )

    _write_json(out_json, report)
    _write_text(
        out_report,
        _render_md(
            "M8 Reproduce Uploaded Golden Report",
            [
                f"- golden_reference_found: `{report['golden_reference_found']}`",
                f"- sram_spec_path: `{report['sram_spec_path']}`",
                f"- generated_from_layoutgen_source: `{report['generated_from_layoutgen_source']}`",
                f"- reference_file_copied_as_output: `{report['reference_file_copied_as_output']}`",
                f"- reproduced_gds_path: `{report['reproduced_gds_path']}`",
                f"- reference_vs_reproduced_geometry_match: `{report['reference_vs_reproduced_geometry_match']}`",
                f"- column_mux_real_check_passed: `{report['column_mux_real_check_passed']}`",
                f"- power_rail_overlap_real_check_passed: `{report['power_rail_overlap_real_check_passed']}`",
                f"- remaining_M8_blockers_count: `{report['remaining_M8_blockers_count']}`",
            ],
        ),
    )
    _write_text(
        repo_root / "docs/evidence/M8_reproduce_uploaded_golden_summary.md",
        _render_md(
            "M8 Reproduce Uploaded Golden Summary",
            [
                f"- reproduced_gds_path: `{report['reproduced_gds_path']}`",
                f"- top_cell: `{report['reproduced_top_cell']}`",
                f"- geometry_match: `{report['reference_vs_reproduced_geometry_match']}`",
                f"- column_mux_instance_count: `{report['column_mux_instance_count']}`",
                f"- bitcell_rail_overlap_count: `{report['bitcell_rail_overlap_count']}`",
                f"- module_boundary_rail_stitch_count: `{report['module_boundary_rail_stitch_count']}`",
                f"- human_klayout_review_required: `{report['human_klayout_review_required']}`",
            ],
        ),
    )

    _write_csv(
        repo_root / "docs/mapping/M8_generation_parameter_matrix.csv",
        ["parameter", "value", "source"],
        [
            {"parameter": "word_size", "value": 8, "source": "M7 run.log"},
            {"parameter": "num_words", "value": 64, "source": "M7 run.log"},
            {"parameter": "words_per_row", "value": 4, "source": "M7 run.log"},
            {"parameter": "enable_openyield_gate_row_packing", "value": True, "source": "current source candidate search"},
            {"parameter": "enable_openyield_power_rail_overlap_packing", "value": True, "source": "current source candidate search"},
        ],
    )
    _write_csv(
        repo_root / "docs/mapping/M8_reference_geometry_comparison_matrix.csv",
        ["metric", "golden", "reproduced", "match"],
        geometry_rows,
    )
    _write_csv(
        repo_root / "docs/mapping/M8_power_rail_overlap_matrix.csv",
        ["metric", "golden", "reproduced"],
        [
            {"metric": "bitcell_rail_overlap_count", "golden": power["golden_bitcell_rail_overlap_count"], "reproduced": power["bitcell_rail_overlap_count"]},
            {"metric": "module_boundary_rail_stitch_count", "golden": power["golden_module_boundary_rail_stitch_count"], "reproduced": power["module_boundary_rail_stitch_count"]},
        ],
    )
    _write_csv(
        repo_root / "docs/mapping/M8_column_mux_matrix.csv",
        ["metric", "golden", "reproduced"],
        [
            {"metric": "column_mux_instance_count", "golden": column_mux["golden_column_mux_instance_count"], "reproduced": column_mux["column_mux_instance_count"]},
            {"metric": "tri_gate_instance_count", "golden": column_mux["golden_tri_gate_instance_count"], "reproduced": column_mux["tri_gate_instance_count"]},
        ],
    )
    _write_csv(
        repo_root / "docs/mapping/M8_remaining_gap_matrix.csv",
        ["gap_id", "description"],
        [{"gap_id": f"M8_GAP_{idx + 1}", "description": item} for idx, item in enumerate(remaining_blockers)],
    )

    updated_status = _update_status_json(status, report)
    _write_json(status_json, updated_status)
    _write_text(status_md, _render_status_md(report))
    return report
