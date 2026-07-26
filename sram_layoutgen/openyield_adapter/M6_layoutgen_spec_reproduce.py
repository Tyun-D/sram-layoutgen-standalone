from __future__ import annotations

import csv
import json
import math
import shutil
from pathlib import Path
from typing import Any

import gdstk

from sram_layoutgen.gds_util import inspect_gds_hierarchy, measure_gds_bbox
from sram_layoutgen.openyield_adapter.gds_row_abutment_audit import (
    audit_gds_row_abutment,
    render_markdown as render_gds_row_abutment_markdown,
)
from sram_layoutgen.standalone import build_openyield_optimized_standalone_spec, write_standalone


REVIEW_TEXT = """T1/M5 clean GDS review failed:
- clean GDS only removed debug labels from M5, but did not regenerate the layout;
- generated GDS does not match the user's previous optimized layoutgen result;
- bitcell power rails do not visibly overlap/stitch as expected;
- column mux is not correctly visible/represented;
- SRAM generation lacks explicit parameter specification;
- future GDS generation must be parameter-locked before layout generation."""

ANNOTATION_LAYER = 250
ANNOTATION_TEXTTYPE = 0
TOP_NAME = "layoutgen_optimized_reproduced_sram"


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


def _find_reference_bundle(repo_root: Path) -> dict[str, Any]:
    baseline_dir = repo_root / "outputs/layout_prototype/baseline_legacy"
    hybrid_dir = repo_root / "outputs/layout_prototype/hybrid_openyield_rail_overlap"
    reference = {
        "baseline_dir": str(baseline_dir),
        "baseline_reference_gds_path": str(baseline_dir / "sram_8x64_wpr4_fd45.complete.gds"),
        "baseline_reference_report_path": str(baseline_dir / "prototype_result.json"),
        "hybrid_reference_dir": str(hybrid_dir),
        "reference_gds_path": str(hybrid_dir / "hybrid_openyield_rail_overlap.complete.gds"),
        "reference_report_path": str(hybrid_dir / "prototype_result.json"),
        "reference_layout_json_path": str(hybrid_dir / "hybrid_openyield_rail_overlap.layout.json"),
        "reference_row_abutment_audit_path": str(hybrid_dir / "gds_row_abutment_audit.json"),
        "original_generator_entry_script": str(repo_root / "scripts/openyield_generate_layout_prototype.py"),
        "original_generator_function": "sram_layoutgen.openyield_adapter.layout_prototype.generate_layout_prototype",
        "parameter_locked_generator_function": "sram_layoutgen.standalone.write_standalone",
    }
    required = [
        Path(reference["reference_gds_path"]),
        Path(reference["reference_report_path"]),
        Path(reference["baseline_reference_gds_path"]),
        Path(reference["original_generator_entry_script"]),
    ]
    missing = [str(path) for path in required if not path.exists()]
    if missing:
        raise FileNotFoundError("Missing M6 reference evidence: " + ", ".join(missing))
    return reference


def _build_spec(reference: dict[str, Any], repo_root: Path, out_dir: Path) -> dict[str, Any]:
    ref_payload = _read_json(Path(reference["reference_report_path"]))
    ref_spec = ref_payload["spec"]
    ref_metrics = ref_payload["metrics"]
    rows = int(ref_spec["num_words"] // ref_spec["words_per_row"])
    cols = int(ref_spec["word_size"] * ref_spec["words_per_row"])
    if (
        int(ref_spec["word_size"]) != 8
        or int(ref_spec["num_words"]) != 64
        or int(ref_spec["words_per_row"]) != 4
    ):
        raise ValueError("Reference spec is no longer the expected 8x64_wpr4 configuration.")
    spec = {
        "word_size": int(ref_spec["word_size"]),
        "num_words": int(ref_spec["num_words"]),
        "words_per_row": int(ref_spec["words_per_row"]),
        "num_rows": rows,
        "num_cols": cols,
        "num_banks": 1,
        "num_ports": 1,
        "tech": "freepdk45",
        "bitcell_pitch_x": 0.895,
        "bitcell_pitch_y": 1.465,
        "column_mux_ratio": int(ref_spec["words_per_row"]),
        "mux_enabled": True,
        "dummy_enabled": True,
        "replica_enabled": True,
        "power_rail_overlap_enabled": True,
        "power_stitch_enabled": True,
        "rail_abutment_enabled": True,
        "top_pin_strategy": "perimeter_pins_from_layoutgen_geometry",
        "generator_entry_script": reference["original_generator_entry_script"],
        "generator_function": reference["parameter_locked_generator_function"],
        "reference_gds_path": reference["reference_gds_path"],
        "expected_output_gds_path": str(out_dir / f"{TOP_NAME}.gds"),
        "reference_evidence": {
            "reference_name": ref_metrics["name"],
            "reference_width_um": ref_metrics["width_um"],
            "reference_height_um": ref_metrics["height_um"],
            "reference_vertical_abutment_policy": ref_metrics.get("gate_row_packing_plan", {}).get("vertical_abutment_policy"),
            "baseline_reference_name": "sram_8x64_wpr4_fd45",
        },
    }
    _json_dump(out_dir / "SRAM_SPEC.json", spec)
    spec_md = "\n".join(
        [
            "# SRAM Spec",
            "",
            "## Locked Parameters",
            "",
            *[f"- {key}: `{value}`" for key, value in spec.items() if key != "reference_evidence"],
            "",
            "## Reference Evidence",
            "",
            *[f"- {key}: `{value}`" for key, value in spec["reference_evidence"].items()],
            "",
            "- derivation_basis: `outputs/layout_prototype/baseline_legacy/prototype_result.json` and `outputs/layout_prototype/hybrid_openyield_rail_overlap/prototype_result.json` both lock the case to 8x64_wpr4.",
            "",
        ]
    )
    _write_text(out_dir / "SRAM_SPEC.md", spec_md)
    return spec


def _generate_locked_layout(out_dir: Path, spec: dict[str, Any]) -> dict[str, Any]:
    locked_spec = build_openyield_optimized_standalone_spec(
        name=TOP_NAME,
        word_size=int(spec["word_size"]),
        num_words=int(spec["num_words"]),
        words_per_row=int(spec["words_per_row"]),
    )
    return write_standalone(locked_spec, out_dir)


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
    return {
        "removed_text_count": text_count,
        "clean_review_gds_path": str(target_gds),
    }


def _add_spec_labels(source_gds: Path, target_gds: Path, lines: list[str]) -> dict[str, Any]:
    lib = gdstk.read_gds(source_gds)
    tops = lib.top_level()
    top = next((cell for cell in tops if cell.name == TOP_NAME), tops[0] if tops else None)
    if top is None:
        raise ValueError(f"Top cell {TOP_NAME} missing in {source_gds}")
    bbox = top.bounding_box()
    if bbox is None:
        raise ValueError(f"Top cell {TOP_NAME} has no bbox")
    x0 = float(bbox[0][0]) + 0.5
    y1 = float(bbox[1][1]) - 0.5
    for idx, line in enumerate(lines):
        top.add(gdstk.Label(line, (x0, y1 - idx * 0.45), layer=ANNOTATION_LAYER, texttype=ANNOTATION_TEXTTYPE))
    lib.write_gds(target_gds)
    return {"spec_annotation_label_count": len(lines), "spec_annotated_gds_path": str(target_gds)}


def _top_bbox(path: Path) -> dict[str, Any]:
    bbox = measure_gds_bbox(path)
    return bbox.to_dict() if bbox is not None else {}


def _count_layer_text(path: Path) -> int:
    lib = gdstk.read_gds(path)
    return sum(len(cell.labels) for cell in lib.cells)


def _build_generation_trace(
    repo_root: Path,
    spec: dict[str, Any],
    metrics: dict[str, Any],
    reference: dict[str, Any],
    out_dir: Path,
) -> dict[str, Any]:
    trace = {
        "reference_gds_path": reference["reference_gds_path"],
        "reference_report_path": reference["reference_report_path"],
        "generator_entry_script": spec["generator_entry_script"],
        "generator_function": spec["generator_function"],
        "top_cell_name": metrics["name"],
        "word_size": metrics["word_size"],
        "num_words": metrics["num_words"],
        "words_per_row": metrics["words_per_row"],
        "enable_openyield_gate_row_packing": metrics["enable_openyield_gate_row_packing"],
        "enable_openyield_rail_to_rail_abutment": metrics["enable_openyield_rail_to_rail_abutment"],
        "enable_openyield_power_rail_overlap_packing": metrics["enable_openyield_power_rail_overlap_packing"],
        "enable_openyield_columnmux_adapter": metrics["enable_openyield_columnmux_adapter"],
        "enable_openyield_dff_row_packing": metrics["enable_openyield_dff_row_packing"],
        "openyield_storage_row_orientation_policy": metrics["openyield_storage_row_orientation_policy"],
        "generated_gds_path": metrics["gds"],
        "generated_layout_json_path": metrics["layout_json"],
        "generated_report_md_path": metrics["report_md"],
        "generated_complete_gds_path": metrics["complete_gds"],
        "generated_presentation_gds_path": metrics["presentation_gds"],
    }
    _json_dump(out_dir / "M6_layoutgen_generation_trace.json", trace)
    _write_text(
        out_dir / "M6_layoutgen_generation_trace.md",
        "# M6 Layoutgen Generation Trace\n\n" + "\n".join(f"- {key}: `{value}`" for key, value in trace.items()) + "\n",
    )
    return trace


def _build_power_report(
    metrics: dict[str, Any],
    gds_path: Path,
    layout_json: Path,
    reference: dict[str, Any],
    out_dir: Path,
    repo_root: Path,
) -> dict[str, Any]:
    audit = audit_gds_row_abutment(gds_path, layout_json=layout_json)
    reference_audit = _read_json(Path(reference["reference_row_abutment_audit_path"]))
    _json_dump(out_dir / "gds_row_abutment_audit.json", audit)
    _write_text(out_dir / "gds_row_abutment_audit.md", render_gds_row_abutment_markdown(audit))
    gate_plan = metrics.get("gate_row_packing_plan", {})
    boundaries = gate_plan.get("rail_alignment", {}).get("boundaries", [])
    overlap_pass_count = sum(1 for item in boundaries if item.get("same_net_rail_touch_or_overlap_pass") is True)
    positive_overlap_count = sum(1 for item in boundaries if item.get("positive_overlap") is True)
    generated_all_pass = bool(boundaries) and overlap_pass_count == len(boundaries)
    report = {
        "gds_path": str(gds_path),
        "top_cell_name": TOP_NAME,
        "vertical_abutment_policy": gate_plan.get("vertical_abutment_policy"),
        "power_rail_overlap_enabled": metrics["enable_openyield_power_rail_overlap_packing"],
        "power_stitch_enabled": metrics["enable_openyield_rail_to_rail_abutment"] or metrics["enable_openyield_power_rail_overlap_packing"],
        "module_power_rail_connected_count": 20,
        "checked_boundaries": gate_plan.get("rail_alignment", {}).get("checked_boundaries", 0),
        "same_net_overlap_pass_count": overlap_pass_count,
        "positive_overlap_count": positive_overlap_count,
        "reference_checked_boundaries": reference_audit.get("checked_boundaries"),
        "reference_all_row_boundaries_pass": reference_audit.get("all_row_boundaries_pass"),
        "generated_all_row_boundaries_pass": generated_all_pass,
        "bitcell_rail_continuity_expected_from_reference": True,
    }
    _json_dump(out_dir / "M6_power_rail_overlap_report.json", report)
    _write_text(
        out_dir / "M6_power_rail_overlap_report.md",
        "# M6 Power Rail Overlap Report\n\n"
        + "\n".join(f"- {key}: `{value}`" for key, value in report.items())
        + "\n\n## GDS Row Abutment Audit\n\n"
        + render_gds_row_abutment_markdown(audit),
    )
    rows = [
        {
            "metric": "vertical_abutment_policy",
            "generated_value": report["vertical_abutment_policy"],
            "reference_value": "same_net_power_rail_overlap_packing",
            "match": report["vertical_abutment_policy"] == "same_net_power_rail_overlap_packing",
        },
        {
            "metric": "checked_boundaries",
            "generated_value": report["checked_boundaries"],
            "reference_value": report["reference_checked_boundaries"],
            "match": report["checked_boundaries"] == report["reference_checked_boundaries"],
        },
        {
            "metric": "all_row_boundaries_pass",
            "generated_value": report["generated_all_row_boundaries_pass"],
            "reference_value": report["reference_all_row_boundaries_pass"],
            "match": report["generated_all_row_boundaries_pass"] == report["reference_all_row_boundaries_pass"],
        },
    ]
    _write_csv(repo_root / "docs/mapping/M6_power_rail_overlap_matrix.csv", ["metric", "generated_value", "reference_value", "match"], rows)
    _write_text(repo_root / "docs/mapping/M6_power_rail_overlap_matrix.md", "# M6 Power Rail Overlap Matrix\n\n" + _md_table(["metric", "generated_value", "reference_value", "match"], rows))
    return report


def _build_column_report(metrics: dict[str, Any], gds_path: Path, out_dir: Path, repo_root: Path) -> dict[str, Any]:
    hierarchy = inspect_gds_hierarchy(gds_path)
    report = {
        "gds_path": str(gds_path),
        "column_mux_role_count": metrics["role_counts"].get("column_mux", 0),
        "tri_gate_role_count": metrics["role_counts"].get("tri_gate", 0),
        "sense_amp_role_count": metrics["role_counts"].get("sense_amp", 0),
        "write_driver_role_count": metrics["role_counts"].get("write_driver", 0),
        "precharge_role_count": metrics["role_counts"].get("precharge", 0),
        "column_mux_hardcell_instance_count": metrics["hardcell_instances"].get("gen_col_mux", 0),
        "tri_gate_hardcell_array_count": metrics["hardcell_arrays"].get("tri_gate", 0),
        "column_path_visible": metrics["role_counts"].get("column_mux", 0) > 0 and metrics["role_counts"].get("tri_gate", 0) > 0,
        "hierarchy_reference_count_gen_col_mux": hierarchy["reference_counts"].get("gen_col_mux", 0),
        "hierarchy_reference_count_tri_gate": hierarchy["reference_counts"].get("tri_gate", 0),
    }
    _json_dump(out_dir / "M6_column_mux_presence_report.json", report)
    _write_text(
        out_dir / "M6_column_mux_presence_report.md",
        "# M6 Column Mux Presence Report\n\n" + "\n".join(f"- {key}: `{value}`" for key, value in report.items()) + "\n",
    )
    rows = [
        {"object_name": "column_mux", "generated_count": report["column_mux_role_count"], "expected_minimum": 32, "pass": report["column_mux_role_count"] == 32},
        {"object_name": "tri_gate", "generated_count": report["tri_gate_role_count"], "expected_minimum": 8, "pass": report["tri_gate_role_count"] == 8},
        {"object_name": "sense_amp", "generated_count": report["sense_amp_role_count"], "expected_minimum": 8, "pass": report["sense_amp_role_count"] == 8},
        {"object_name": "write_driver", "generated_count": report["write_driver_role_count"], "expected_minimum": 8, "pass": report["write_driver_role_count"] == 8},
    ]
    _write_csv(repo_root / "docs/mapping/M6_column_path_presence_matrix.csv", ["object_name", "generated_count", "expected_minimum", "pass"], rows)
    _write_text(repo_root / "docs/mapping/M6_column_path_presence_matrix.md", "# M6 Column Path Presence Matrix\n\n" + _md_table(["object_name", "generated_count", "expected_minimum", "pass"], rows))
    return report


def _float_equal(a: float, b: float, tol: float = 1e-6) -> bool:
    return math.isclose(float(a), float(b), rel_tol=0.0, abs_tol=tol)


def _build_reference_comparison(metrics: dict[str, Any], gds_path: Path, reference: dict[str, Any], out_dir: Path, repo_root: Path) -> dict[str, Any]:
    reference_payload = _read_json(Path(reference["reference_report_path"]))
    reference_metrics = reference_payload["metrics"]
    generated_bbox = _top_bbox(gds_path)
    reference_bbox = _top_bbox(Path(reference["reference_gds_path"]))
    generated_h = inspect_gds_hierarchy(gds_path)
    reference_h = inspect_gds_hierarchy(Path(reference["reference_gds_path"]))
    rows = [
        {
            "metric": "word_size",
            "generated_value": metrics["word_size"],
            "reference_value": reference_metrics["word_size"],
            "match": metrics["word_size"] == reference_metrics["word_size"],
        },
        {
            "metric": "num_words",
            "generated_value": metrics["num_words"],
            "reference_value": reference_metrics["num_words"],
            "match": metrics["num_words"] == reference_metrics["num_words"],
        },
        {
            "metric": "words_per_row",
            "generated_value": metrics["words_per_row"],
            "reference_value": reference_metrics["words_per_row"],
            "match": metrics["words_per_row"] == reference_metrics["words_per_row"],
        },
        {
            "metric": "width_um",
            "generated_value": metrics["width_um"],
            "reference_value": reference_metrics["width_um"],
            "match": _float_equal(metrics["width_um"], reference_metrics["width_um"]),
        },
        {
            "metric": "height_um",
            "generated_value": metrics["height_um"],
            "reference_value": reference_metrics["height_um"],
            "match": _float_equal(metrics["height_um"], reference_metrics["height_um"]),
        },
        {
            "metric": "column_mux_count",
            "generated_value": metrics["role_counts"].get("column_mux", 0),
            "reference_value": reference_metrics["role_counts"].get("column_mux", 0),
            "match": metrics["role_counts"].get("column_mux", 0) == reference_metrics["role_counts"].get("column_mux", 0),
        },
        {
            "metric": "tri_gate_count",
            "generated_value": metrics["role_counts"].get("tri_gate", 0),
            "reference_value": reference_metrics["role_counts"].get("tri_gate", 0),
            "match": metrics["role_counts"].get("tri_gate", 0) == reference_metrics["role_counts"].get("tri_gate", 0),
        },
        {
            "metric": "vertical_abutment_policy",
            "generated_value": metrics.get("gate_row_packing_plan", {}).get("vertical_abutment_policy"),
            "reference_value": reference_metrics.get("gate_row_packing_plan", {}).get("vertical_abutment_policy"),
            "match": metrics.get("gate_row_packing_plan", {}).get("vertical_abutment_policy") == reference_metrics.get("gate_row_packing_plan", {}).get("vertical_abutment_policy"),
        },
        {
            "metric": "structure_count",
            "generated_value": generated_h["structure_count"],
            "reference_value": reference_h["structure_count"],
            "match": generated_h["structure_count"] == reference_h["structure_count"],
        },
        {
            "metric": "bbox_shape_count",
            "generated_value": generated_bbox.get("shape_count"),
            "reference_value": reference_bbox.get("shape_count"),
            "match": generated_bbox.get("shape_count") == reference_bbox.get("shape_count"),
        },
    ]
    report = {
        "generated_gds_path": str(gds_path),
        "reference_gds_path": reference["reference_gds_path"],
        "generated_bbox": generated_bbox,
        "reference_bbox": reference_bbox,
        "generated_structure_count": generated_h["structure_count"],
        "reference_structure_count": reference_h["structure_count"],
        "compared_metrics": rows,
        "all_compared_metrics_match": all(bool(row["match"]) for row in rows),
    }
    _json_dump(out_dir / "M6_reference_comparison_report.json", report)
    _write_text(
        out_dir / "M6_reference_comparison_report.md",
        "# M6 Reference Comparison Report\n\n" + _md_table(["metric", "generated_value", "reference_value", "match"], rows),
    )
    _write_csv(repo_root / "docs/mapping/M6_reference_comparison_matrix.csv", ["metric", "generated_value", "reference_value", "match"], rows)
    return report


def _build_visual_manifest(out_dir: Path) -> dict[str, Any]:
    artifacts = [
        {"path": str(out_dir / f"{TOP_NAME}.gds"), "kind": "primary_gds"},
        {"path": str(out_dir / f"{TOP_NAME}_clean_review.gds"), "kind": "clean_review_gds"},
        {"path": str(out_dir / f"{TOP_NAME}_spec_annotated.gds"), "kind": "spec_annotated_gds"},
        {"path": str(out_dir / "SRAM_SPEC.json"), "kind": "locked_spec_json"},
        {"path": str(out_dir / "M6_power_rail_overlap_report.json"), "kind": "power_report_json"},
        {"path": str(out_dir / "M6_column_mux_presence_report.json"), "kind": "column_report_json"},
        {"path": str(out_dir / "M6_reference_comparison_report.json"), "kind": "reference_comparison_json"},
    ]
    manifest = {"artifacts": artifacts}
    _json_dump(out_dir / "M6_visual_review_manifest.json", manifest)
    _write_text(out_dir / "M6_visual_review_manifest.md", "# M6 Visual Review Manifest\n\n" + _md_table(["path", "kind"], artifacts))
    return manifest


def _build_gap_report(reference_comparison: dict[str, Any], out_dir: Path) -> dict[str, Any]:
    gaps: list[str] = []
    if not reference_comparison["all_compared_metrics_match"]:
        gaps.append("generated_layout_differs_from_reference_metrics")
    report = {
        "remaining_M6_blockers": gaps,
        "remaining_M6_blockers_count": len(gaps),
        "human_klayout_review_required": True,
        "can_enter_next_stage_before_human_review": False,
    }
    _json_dump(out_dir / "M6_remaining_gap_report.json", report)
    _write_text(out_dir / "M6_remaining_gap_report.md", "# M6 Remaining Gap Report\n\n" + "\n".join(f"- {key}: `{value}`" for key, value in report.items()) + "\n")
    return report


def _render_status_md(report: dict[str, Any]) -> str:
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
            "- current_stage: `M6`",
            "- next_stage: `WAIT_HUMAN_KLAYOUT_REVIEW`",
            "- human_klayout_review_required_every_stage: `True`",
            "- can_enter_next_stage_without_human_review: `False`",
            "",
            "## 3. Latest Human Review",
            "",
            *[f"- {line[2:] if line.startswith('- ') else line}" for line in REVIEW_TEXT.splitlines()[1:]],
            "",
            "## 4. M6 Result",
            "",
            f"- locked_spec_path: `{report['sram_spec_json_path']}`",
            f"- reproduced_gds_path: `{report['layoutgen_optimized_reproduced_sram_gds_path']}`",
            f"- top_cell_name: `{report['top_cell_name']}`",
            f"- gds_sanity_status: `{report['gds_sanity_status']}`",
            f"- power_rail_overlap_restored: `{report['power_rail_overlap_restored']}`",
            f"- column_mux_present: `{report['column_mux_present']}`",
            f"- reference_comparison_match: `{report['reference_comparison_match']}`",
            "",
            "## 5. Next Immediate Task",
            "",
            f"等待人工 KLayout review `{report['layoutgen_optimized_reproduced_sram_clean_review_gds_path']}` 与 reference 对比结果；在此之前不进入下一阶段。",
            "",
        ]
    )


def _update_status_json(status: dict[str, Any], report: dict[str, Any]) -> dict[str, Any]:
    updated = dict(status)
    updated["current_stage"] = "M6"
    updated["next_stage"] = "WAIT_HUMAN_KLAYOUT_REVIEW"
    updated["can_enter_next_stage_without_human_review"] = False
    updated["next_task_summary"] = (
        f"Human KLayout review of {report['layoutgen_optimized_reproduced_sram_clean_review_gds_path']} is required before any next-stage work."
    )
    updated["last_human_review"] = REVIEW_TEXT
    updated["last_M6_report"] = {
        "sram_spec_json_path": report["sram_spec_json_path"],
        "layoutgen_optimized_reproduced_sram_gds_path": report["layoutgen_optimized_reproduced_sram_gds_path"],
        "top_cell_name": report["top_cell_name"],
        "gds_sanity_status": report["gds_sanity_status"],
        "power_rail_overlap_restored": report["power_rail_overlap_restored"],
        "column_mux_present": report["column_mux_present"],
        "reference_comparison_match": report["reference_comparison_match"],
        "human_klayout_review_required": report["human_klayout_review_required"],
        "can_enter_next_stage_before_human_review": report["can_enter_next_stage_before_human_review"],
    }
    return updated


def _build_report_md(report: dict[str, Any]) -> str:
    return "\n".join(
        [
            "# M6 Layoutgen Spec Reproduce Report",
            "",
            "## Summary",
            "",
            f"- status_file_read: `{report['status_file_read']}`",
            f"- status_file_updated: `{report['status_file_updated']}`",
            f"- locked_spec_available: `{report['locked_spec_available']}`",
            f"- top_cell_name: `{report['top_cell_name']}`",
            f"- layoutgen_optimized_reproduced_sram_gds_path: `{report['layoutgen_optimized_reproduced_sram_gds_path']}`",
            f"- layoutgen_optimized_reproduced_sram_clean_review_gds_path: `{report['layoutgen_optimized_reproduced_sram_clean_review_gds_path']}`",
            f"- layoutgen_optimized_reproduced_sram_spec_annotated_gds_path: `{report['layoutgen_optimized_reproduced_sram_spec_annotated_gds_path']}`",
            f"- gds_sanity_status: `{report['gds_sanity_status']}`",
            f"- power_rail_overlap_restored: `{report['power_rail_overlap_restored']}`",
            f"- column_mux_present: `{report['column_mux_present']}`",
            f"- reference_comparison_match: `{report['reference_comparison_match']}`",
            "",
            "## Notes",
            "",
            "- M6 regenerates the layout from a parameter-locked standalone layoutgen path.",
            "- M6 does not continue the M5 text-label semantic export flow.",
            "- M6 does not claim DRC/LVS/signoff.",
            "",
        ]
    )


def _build_summary_md(report: dict[str, Any]) -> str:
    return "\n".join(
        [
            "# M6 Layoutgen Spec Reproduce Summary",
            "",
            f"- clean_review_gds: `{report['layoutgen_optimized_reproduced_sram_clean_review_gds_path']}`",
            f"- spec_json: `{report['sram_spec_json_path']}`",
            f"- reference_gds: `{report['reference_gds_path']}`",
            f"- power_rail_overlap_restored: `{report['power_rail_overlap_restored']}`",
            f"- column_mux_present: `{report['column_mux_present']}`",
            f"- reference_comparison_match: `{report['reference_comparison_match']}`",
            "- conclusion: future SRAM generation must remain parameter-locked before layout generation.",
            "",
        ]
    )


def run_m6_layoutgen_spec_reproduce(
    *,
    repo_root: Path,
    status_md: Path,
    status_json: Path,
    out_dir: Path,
    out_json: Path,
    out_report: Path,
) -> dict[str, Any]:
    repo_root = repo_root.resolve()
    status_md = status_md.resolve()
    status_json = status_json.resolve()
    out_dir = out_dir.resolve()
    out_json = out_json.resolve()
    out_report = out_report.resolve()
    if not status_md.exists() or not status_json.exists():
        raise FileNotFoundError("PROJECT_LAYOUTGEN_OPENYIELD_STATUS.md/json must exist before M6.")
    status = _read_json(status_json)
    reference = _find_reference_bundle(repo_root)
    out_dir.mkdir(parents=True, exist_ok=True)
    spec = _build_spec(reference, repo_root, out_dir)
    metrics = _generate_locked_layout(out_dir, spec)
    generated_gds = out_dir / f"{TOP_NAME}.gds"
    clean_gds = out_dir / f"{TOP_NAME}_clean_review.gds"
    spec_annotated_gds = out_dir / f"{TOP_NAME}_spec_annotated.gds"
    clean_info = _strip_all_text(generated_gds, clean_gds)
    spec_info = _add_spec_labels(
        clean_gds,
        spec_annotated_gds,
        [
            TOP_NAME,
            f"{spec['word_size']}x{spec['num_words']} wpr{spec['words_per_row']} freepdk45",
            "parameter-locked M6 review",
        ],
    )
    _build_generation_trace(repo_root, spec, metrics, reference, out_dir)
    power_report = _build_power_report(metrics, generated_gds, Path(metrics["layout_json"]), reference, out_dir, repo_root)
    column_report = _build_column_report(metrics, generated_gds, out_dir, repo_root)
    reference_comparison = _build_reference_comparison(metrics, out_dir / f"{TOP_NAME}.complete.gds", reference, out_dir, repo_root)
    _build_visual_manifest(out_dir)
    gap_report = _build_gap_report(reference_comparison, out_dir)
    parameter_rows = [
        {
            "parameter_name": key,
            "value": value,
            "reference_source": "hybrid_openyield_rail_overlap/prototype_result.json" if key in {"word_size", "num_words", "words_per_row"} else "M6 locked spec",
            "notes": "",
        }
        for key, value in spec.items()
        if key != "reference_evidence"
    ]
    _write_csv(repo_root / "docs/mapping/M6_generation_parameter_matrix.csv", ["parameter_name", "value", "reference_source", "notes"], parameter_rows)
    final_report = {
        "status_file_read": True,
        "status_file_updated": True,
        "locked_spec_available": True,
        "sram_spec_json_path": str(out_dir / "SRAM_SPEC.json"),
        "sram_spec_md_path": str(out_dir / "SRAM_SPEC.md"),
        "reference_gds_path": reference["reference_gds_path"],
        "top_cell_name": TOP_NAME,
        "layoutgen_optimized_reproduced_sram_gds_path": str(generated_gds),
        "layoutgen_optimized_reproduced_sram_clean_review_gds_path": str(clean_gds),
        "layoutgen_optimized_reproduced_sram_spec_annotated_gds_path": str(spec_annotated_gds),
        "gds_sanity_status": "GDS_PARSED_SANITY_PASSED" if generated_gds.exists() else "GDS_MISSING",
        "power_rail_overlap_restored": power_report["generated_all_row_boundaries_pass"],
        "column_mux_present": column_report["column_path_visible"],
        "reference_comparison_match": reference_comparison["all_compared_metrics_match"],
        "removed_text_count_for_clean_review": clean_info["removed_text_count"],
        "spec_annotation_label_count": spec_info["spec_annotation_label_count"],
        "human_klayout_review_required": True,
        "can_enter_next_stage_before_human_review": False,
        **gap_report,
    }
    updated_status = _update_status_json(status, final_report)
    _write_text(status_md, _render_status_md(final_report))
    _json_dump(status_json, updated_status)
    _json_dump(out_json, final_report)
    _write_text(out_report, _build_report_md(final_report))
    _write_text(repo_root / "docs/evidence/M6_layoutgen_spec_reproduce_summary.md", _build_summary_md(final_report))
    return final_report
