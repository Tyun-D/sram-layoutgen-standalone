from __future__ import annotations

import csv
import json
import shutil
from collections import Counter
from pathlib import Path
from typing import Any

import gdstk

from sram_layoutgen.gds_util import inspect_gds_hierarchy, inspect_gds_layers, inspect_gds_text_records, measure_gds_bbox
from sram_layoutgen.openyield_adapter.gds_row_abutment_audit import audit_gds_row_abutment, render_markdown as render_gds_row_abutment_markdown
from sram_layoutgen.openyield_adapter.layout_prototype import generate_layout_prototype


REVIEW_TEXT = """M6 human review failed:
- Generated GDS still looks like previous non-overlap result.
- Power rails are not visibly overlapped/stiched.
- MUX is not visibly generated/placed as expected.
- Report fields power_rail_overlap_restored=True, column_mux_present=True, reference_comparison_match=True are not trusted.
- Must reference and reproduce hybrid_openyield_rail_overlap.complete.gds exactly."""


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


def _collect_geometry_report(path: Path) -> dict[str, Any]:
    low = inspect_gds_hierarchy(path)
    layers = inspect_gds_layers(path)
    bbox = measure_gds_bbox(path)
    high = _gdstk_stats(path)
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
        "low_level_reference_counts": low["reference_counts"],
    }


def _geometry_diff_rows(lhs_name: str, lhs: dict[str, Any], rhs_name: str, rhs: dict[str, Any]) -> list[dict[str, Any]]:
    rows = []
    scalar_keys = [
        "file_size_bytes",
        "top_cell",
        "cell_count",
        "sref_count",
        "boundary_count",
        "path_count",
        "text_count",
        "bbox",
        "layer_datatype_summary",
        "per_layer_shape_count",
        "instance_count_by_cell_name",
        "gen_col_mux_hierarchy_presence",
        "tri_gate_hierarchy_presence",
    ]
    for key in scalar_keys:
        rows.append(
            {
                "metric": key,
                lhs_name: lhs.get(key),
                rhs_name: rhs.get(key),
                "match": lhs.get(key) == rhs.get(key),
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
            "- current_stage: `M6R`",
            "- next_stage: `WAIT_HUMAN_KLAYOUT_REVIEW`",
            "- human_klayout_review_required_every_stage: `True`",
            "- can_enter_next_stage_without_human_review: `False`",
            "",
            "## 3. Latest Human Review",
            "",
            *[f"- {line[2:] if line.startswith('- ') else line}" for line in REVIEW_TEXT.splitlines()[1:]],
            "",
            "## 4. M6R Result",
            "",
            f"- reference_copy_for_review_gds: `{report['reference_copy_for_review_gds_path']}`",
            f"- m6_previous_output_for_review_gds: `{report['m6_previous_output_for_review_gds_path']}`",
            f"- reproduced_review_gds: `{report['layoutgen_hybrid_reproduced_M6R_gds_path']}`",
            f"- reproduced_clean_review_gds: `{report['layoutgen_hybrid_reproduced_M6R_clean_review_gds_path']}`",
            f"- m6_previous_matches_reference: `{report['m6_previous_matches_reference']}`",
            f"- reproduced_matches_reference: `{report['reproduced_matches_reference']}`",
            "",
            "## 5. Next Immediate Task",
            "",
            f"等待人工 KLayout review `{report['layoutgen_hybrid_reproduced_M6R_clean_review_gds_path']}` 与 `{report['reference_copy_for_review_gds_path']}` 的对照结果；在此之前不进入下一阶段。",
            "",
        ]
    )


def _update_status_json(status: dict[str, Any], report: dict[str, Any]) -> dict[str, Any]:
    updated = dict(status)
    updated["current_stage"] = "M6R"
    updated["next_stage"] = "WAIT_HUMAN_KLAYOUT_REVIEW"
    updated["can_enter_next_stage_without_human_review"] = False
    updated["next_task_summary"] = (
        f"Human KLayout review of {report['layoutgen_hybrid_reproduced_M6R_clean_review_gds_path']} against {report['reference_copy_for_review_gds_path']} is required before any next-stage work."
    )
    updated["last_human_review"] = REVIEW_TEXT
    updated["last_M6R_report"] = {
        "reference_copy_for_review_gds_path": report["reference_copy_for_review_gds_path"],
        "m6_previous_output_for_review_gds_path": report["m6_previous_output_for_review_gds_path"],
        "layoutgen_hybrid_reproduced_M6R_gds_path": report["layoutgen_hybrid_reproduced_M6R_gds_path"],
        "m6_previous_matches_reference": report["m6_previous_matches_reference"],
        "reproduced_matches_reference": report["reproduced_matches_reference"],
        "true_generation_entry_identified": report["true_generation_entry_identified"],
        "human_klayout_review_required": report["human_klayout_review_required"],
        "can_enter_next_stage_before_human_review": report["can_enter_next_stage_before_human_review"],
    }
    return updated


def _build_failure_reason(m6_prev_vs_ref: list[dict[str, Any]], reproduced_vs_ref: list[dict[str, Any]]) -> str:
    mismatch_metrics = [row["metric"] for row in m6_prev_vs_ref if not row["match"]]
    reproduced_mismatch = [row["metric"] for row in reproduced_vs_ref if not row["match"]]
    lines = [
        "# M6R Failure Reason Report",
        "",
        "## Root Cause",
        "",
        "- M6 compared and shipped the wrong artifact class for visual review.",
        "- The fixed reference is `hybrid_openyield_rail_overlap.complete.gds`, but M6's main review artifact was `layoutgen_optimized_reproduced_sram.gds`.",
        "- `layoutgen_optimized_reproduced_sram.gds` has the same macro bbox and many of the same hierarchy statistics as the reference, but it has fewer geometry shapes because it is the primary `.gds`, not the `complete.gds` visual-routing export.",
        "- M6 therefore reported success from the regenerated backend metrics while the user was visually inspecting a different export artifact.",
        "",
        "## Evidence",
        "",
        f"- M6 previous vs reference mismatches: `{', '.join(mismatch_metrics) if mismatch_metrics else 'none'}`",
        f"- Reproduced true-entry output vs reference mismatches: `{', '.join(reproduced_mismatch) if reproduced_mismatch else 'none'}`",
        "- The true reference-locked rerun uses `generate_layout_prototype(..., mode='hybrid_openyield_prototype', enable_openyield_gate_row_packing=True, enable_openyield_rail_to_rail_abutment=True, enable_openyield_power_rail_overlap_packing=True, exclude_dff_vertical_overlap=True)` and then inspects the resulting `complete.gds` artifact.",
        "",
    ]
    return "\n".join(lines)


def run_m6r_reference_locked_reproduce(
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
        raise FileNotFoundError("PROJECT_LAYOUTGEN_OPENYIELD_STATUS.md/json must exist before M6R.")

    status = _read_json(status_json)
    reference_complete_gds = repo_root / "outputs/layout_prototype/hybrid_openyield_rail_overlap/hybrid_openyield_rail_overlap.complete.gds"
    reference_proto = repo_root / "outputs/layout_prototype/hybrid_openyield_rail_overlap/prototype_result.json"
    m6_prev_gds = repo_root / "outputs/M6_layoutgen_spec_reproduce/current_supported_config/layoutgen_optimized_reproduced_sram.gds"
    m6_prev_layout_json = repo_root / "outputs/M6_layoutgen_spec_reproduce/current_supported_config/layoutgen_optimized_reproduced_sram.layout.json"
    if not reference_complete_gds.exists() or not reference_proto.exists() or not m6_prev_gds.exists():
        raise FileNotFoundError("M6R required reference or previous M6 artifacts are missing.")

    ref_payload = _read_json(reference_proto)
    spec = ref_payload["spec"]
    out_dir.mkdir(parents=True, exist_ok=True)

    reference_copy = out_dir / "reference_copy_for_review.gds"
    m6_prev_copy = out_dir / "m6_previous_output_for_review.gds"
    _copy(reference_complete_gds, reference_copy)
    _copy(m6_prev_gds, m6_prev_copy)

    true_entry_result = generate_layout_prototype(
        repo_root=repo_root,
        mode=ref_payload["mode"],
        out_dir=out_dir,
        metadata_dir=repo_root / "docs",
        word_size=int(spec["word_size"]),
        num_words=int(spec["num_words"]),
        words_per_row=int(spec["words_per_row"]),
        enable_openyield_gate_row_packing=bool(spec["enable_openyield_gate_row_packing"]),
        enable_openyield_gate_row_vertical_abutment=bool(spec["enable_openyield_gate_row_vertical_abutment"]),
        enable_openyield_rail_to_rail_abutment=bool(spec["enable_openyield_rail_to_rail_abutment"]),
        enable_openyield_power_rail_overlap_packing=bool(spec["enable_openyield_power_rail_overlap_packing"]),
        enable_openyield_dff_row_packing=bool(spec["enable_openyield_dff_row_packing"]),
        exclude_dff_vertical_overlap=bool(spec["exclude_dff_vertical_overlap"]),
    )
    regenerated_complete = Path(true_entry_result["metrics"]["complete_gds"]).resolve()
    regenerated_layout_json = Path(true_entry_result["metrics"]["layout_json"]).resolve()
    reproduced_review_gds = out_dir / "layoutgen_hybrid_reproduced_M6R.gds"
    _copy(regenerated_complete, reproduced_review_gds)
    clean_review_info = _strip_all_text(reproduced_review_gds, out_dir / "layoutgen_hybrid_reproduced_M6R_clean_review.gds")

    ref_report = _collect_geometry_report(reference_complete_gds)
    m6_prev_report = _collect_geometry_report(m6_prev_gds)
    reproduced_report = _collect_geometry_report(reproduced_review_gds)

    m6_prev_vs_ref = _geometry_diff_rows("m6_previous", m6_prev_report, "reference", ref_report)
    reproduced_vs_ref = _geometry_diff_rows("reproduced", reproduced_report, "reference", ref_report)
    geom_report = {
        "reference_path": str(reference_complete_gds),
        "m6_previous_path": str(m6_prev_gds),
        "reproduced_path": str(reproduced_review_gds),
        "m6_previous_vs_reference": m6_prev_vs_ref,
        "reproduced_vs_reference": reproduced_vs_ref,
    }
    _json_dump(out_dir / "M6R_reference_geometry_diff_report.json", geom_report)
    _write_text(
        out_dir / "M6R_reference_geometry_diff_report.md",
        "# M6R Reference Geometry Diff Report\n\n## M6 Previous vs Reference\n\n"
        + _md_table(["metric", "m6_previous", "reference", "match"], m6_prev_vs_ref)
        + "\n## Reproduced vs Reference\n\n"
        + _md_table(["metric", "reproduced", "reference", "match"], reproduced_vs_ref),
    )

    true_entry_report = {
        "reference_config_path": str(reference_proto),
        "reference_complete_gds_path": str(reference_complete_gds),
        "true_generation_entry_identified": True,
        "generator_entry_script": str(repo_root / "scripts/openyield_generate_layout_prototype.py"),
        "generator_function": "sram_layoutgen.openyield_adapter.layout_prototype.generate_layout_prototype",
        "mode": ref_payload["mode"],
        "arguments": {
            "word_size": int(spec["word_size"]),
            "num_words": int(spec["num_words"]),
            "words_per_row": int(spec["words_per_row"]),
            "enable_openyield_gate_row_packing": bool(spec["enable_openyield_gate_row_packing"]),
            "enable_openyield_gate_row_vertical_abutment": bool(spec["enable_openyield_gate_row_vertical_abutment"]),
            "enable_openyield_rail_to_rail_abutment": bool(spec["enable_openyield_rail_to_rail_abutment"]),
            "enable_openyield_power_rail_overlap_packing": bool(spec["enable_openyield_power_rail_overlap_packing"]),
            "enable_openyield_dff_row_packing": bool(spec["enable_openyield_dff_row_packing"]),
            "exclude_dff_vertical_overlap": bool(spec["exclude_dff_vertical_overlap"]),
        },
        "generated_complete_gds_path": str(regenerated_complete),
        "generated_review_gds_path": str(reproduced_review_gds),
        "byte_identical_to_reference_complete_gds": reference_complete_gds.read_bytes() == regenerated_complete.read_bytes(),
        "m6_wrong_artifact_reason": "M6 reported against regenerated metrics and compared/handed off the primary .gds artifact instead of the reference-locked .complete.gds visual-routing artifact.",
    }
    _json_dump(out_dir / "M6R_true_generation_entry_report.json", true_entry_report)
    _write_text(
        out_dir / "M6R_true_generation_entry_report.md",
        "# M6R True Generation Entry Report\n\n"
        + "\n".join(f"- {key}: `{value}`" for key, value in true_entry_report.items() if key != "arguments")
        + "\n\n## Arguments\n\n"
        + "\n".join(f"- {key}: `{value}`" for key, value in true_entry_report["arguments"].items())
        + "\n",
    )

    ref_power = audit_gds_row_abutment(reference_complete_gds, layout_json=Path(ref_payload["metrics"]["layout_json"]))
    m6_prev_power = audit_gds_row_abutment(m6_prev_gds, layout_json=m6_prev_layout_json)
    reproduced_power = audit_gds_row_abutment(reproduced_review_gds, layout_json=regenerated_layout_json)
    power_report = {
        "reference_positive_overlap_count": ref_power.get("positive_overlap_count"),
        "reference_same_net_power_overlap_pass": ref_power.get("same_net_power_overlap_pass"),
        "m6_previous_positive_overlap_count": m6_prev_power.get("positive_overlap_count"),
        "m6_previous_same_net_power_overlap_pass": m6_prev_power.get("same_net_power_overlap_pass"),
        "reproduced_positive_overlap_count": reproduced_power.get("positive_overlap_count"),
        "reproduced_same_net_power_overlap_pass": reproduced_power.get("same_net_power_overlap_pass"),
        "notes": "M6 previous primary .gds already had overlap evidence in geometry audit, but it still did not match the fixed reference artifact class the user requested. M6R therefore locks to complete.gds reproduction.",
    }
    _json_dump(out_dir / "M6R_power_rail_overlap_real_check.json", power_report)
    _write_text(
        out_dir / "M6R_power_rail_overlap_real_check.md",
        "# M6R Power Rail Overlap Real Check\n\n"
        + "\n".join(f"- {key}: `{value}`" for key, value in power_report.items() if key != "notes")
        + "\n\n"
        + power_report["notes"]
        + "\n",
    )

    column_report = {
        "reference_gen_col_mux": ref_report["gen_col_mux_hierarchy_presence"],
        "reference_tri_gate": ref_report["tri_gate_hierarchy_presence"],
        "m6_previous_gen_col_mux": m6_prev_report["gen_col_mux_hierarchy_presence"],
        "m6_previous_tri_gate": m6_prev_report["tri_gate_hierarchy_presence"],
        "reproduced_gen_col_mux": reproduced_report["gen_col_mux_hierarchy_presence"],
        "reproduced_tri_gate": reproduced_report["tri_gate_hierarchy_presence"],
        "reference_column_mux_instance_count_by_cell_name": ref_report["instance_count_by_cell_name"].get("column_mux__gen_col_mux", 0),
        "m6_previous_column_mux_instance_count_by_cell_name": m6_prev_report["instance_count_by_cell_name"].get("column_mux__gen_col_mux", 0),
        "reproduced_column_mux_instance_count_by_cell_name": reproduced_report["instance_count_by_cell_name"].get("column_mux__gen_col_mux", 0),
    }
    _json_dump(out_dir / "M6R_column_mux_real_check.json", column_report)
    _write_text(
        out_dir / "M6R_column_mux_real_check.md",
        "# M6R Column Mux Real Check\n\n" + "\n".join(f"- {key}: `{value}`" for key, value in column_report.items()) + "\n",
    )

    failure_reason_md = _build_failure_reason(m6_prev_vs_ref, reproduced_vs_ref)
    _write_text(out_dir / "M6R_failure_reason_report.md", failure_reason_md)

    final_report = {
        "status_file_read": True,
        "status_file_updated": True,
        "reference_copy_for_review_gds_path": str(reference_copy),
        "m6_previous_output_for_review_gds_path": str(m6_prev_copy),
        "layoutgen_hybrid_reproduced_M6R_gds_path": str(reproduced_review_gds),
        "layoutgen_hybrid_reproduced_M6R_clean_review_gds_path": clean_review_info["clean_review_gds_path"],
        "true_generation_entry_identified": True,
        "m6_previous_matches_reference": all(bool(row["match"]) for row in m6_prev_vs_ref),
        "reproduced_matches_reference": all(bool(row["match"]) for row in reproduced_vs_ref),
        "byte_identical_reference_vs_reproduced_complete": true_entry_report["byte_identical_to_reference_complete_gds"],
        "human_klayout_review_required": True,
        "can_enter_next_stage_before_human_review": False,
    }
    updated_status = _update_status_json(status, final_report)
    _write_text(status_md, _render_status_md(final_report))
    _json_dump(status_json, updated_status)
    _json_dump(out_json, final_report)
    _write_text(
        out_report,
        "# M6R Reference Locked Reproduce Report\n\n"
        + "\n".join(f"- {key}: `{value}`" for key, value in final_report.items())
        + "\n",
    )
    _write_text(
        repo_root / "docs/evidence/M6R_reference_locked_reproduce_summary.md",
        "# M6R Reference Locked Reproduce Summary\n\n"
        + f"- reference_copy_for_review.gds: `{reference_copy}`\n"
        + f"- m6_previous_output_for_review.gds: `{m6_prev_copy}`\n"
        + f"- layoutgen_hybrid_reproduced_M6R.gds: `{reproduced_review_gds}`\n"
        + f"- reproduced_matches_reference: `{final_report['reproduced_matches_reference']}`\n"
        + f"- m6_previous_matches_reference: `{final_report['m6_previous_matches_reference']}`\n",
    )
    return final_report
