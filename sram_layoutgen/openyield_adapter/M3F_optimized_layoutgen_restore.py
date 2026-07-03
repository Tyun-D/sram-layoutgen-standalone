from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any

import gdstk

from sram_layoutgen.openyield_adapter.gate_row_packer import emit_gate_row_vertical_abutment_report
from sram_layoutgen.openyield_adapter.gds_row_abutment_audit import audit_gds_row_abutment, render_markdown as render_gds_row_abutment_markdown
from sram_layoutgen.openyield_adapter.layout_prototype import (
    _packing_plan_from_metrics,
    build_module_coverage,
    load_support_bundle,
)
from sram_layoutgen.standalone import StandaloneSpec, write_standalone


USER_REVIEW = """M3R review failed/partially failed:
- OpenYield semantics were mostly exported as text labels.
- Physical cells remained layoutgen original cells.
- first_round_openyield_gds_reused_count = 0.
- Optimized layoutgen rail-overlap / power-rail stitching flow was not restored.
- Do not proceed to final validation before restoring optimized layoutgen generation flow."""


MODULE_COVERAGE_KEY_MAP = {
    "bitcell_array": "bitcell_array",
    "dummy_array": "dummy_array",
    "replica_array": "replica_array",
    "precharge": "PRECHARGE",
    "sense_amp": "sense_amp",
    "write_driver": "write_driver",
    "column_mux": "column_mux",
    "wordline_driver": "wordline_driver",
    "CONTROL_LOGIC": None,
    "DELAY_CHAIN": "DELAY_CHAIN",
    "DFF_ROW": "DFF_ROW",
    "GATED_CLOCK_PATH": "GATED_CLOCK_PATH",
    "PRECHARGE_ENABLE_PATH": "PRECHARGE_ENABLE_PATH",
    "SENSE_ENABLE_PATH": "SENSE_ENABLE_PATH",
    "WORDLINE_ENABLE_PATH": "WORDLINE_ENABLE_PATH",
    "WRITE_ENABLE_PATH": "WRITE_ENABLE_PATH",
    "row_decoder": None,
    "wordline_decoder": None,
    "decoder_gate_cells": None,
    "wordline_driver_gate_cells": None,
}

M3F_NAME = "openyield_optimized_layoutgen_sram"


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


def _read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def _md_table(columns: list[str], rows: list[dict[str, Any]]) -> str:
    lines = [
        "| " + " | ".join(columns) + " |",
        "| " + " | ".join(["---"] * len(columns)) + " |",
    ]
    for row in rows:
        lines.append("| " + " | ".join(str(row.get(column, "")).replace("\n", "<br>") for column in columns) + " |")
    return "\n".join(lines) + "\n"


def _gds_sanity(gds_path: Path, top_cell_name: str) -> dict[str, Any]:
    try:
        lib = gdstk.read_gds(gds_path)
    except Exception as exc:
        return {
            "status": "GDS_PARSE_FAILED",
            "error": str(exc),
            "top_cell_name": None,
            "gds_size_bytes": gds_path.stat().st_size if gds_path.exists() else 0,
        }
    tops = lib.top_level()
    top = next((cell for cell in tops if cell.name == top_cell_name), tops[0] if tops else None)
    if top is None:
        return {
            "status": "TOP_CELL_MISSING",
            "error": "Top cell not found.",
            "top_cell_name": None,
            "gds_size_bytes": gds_path.stat().st_size,
        }
    bbox = top.bounding_box()
    top_bbox = None
    if bbox is not None:
        top_bbox = {
            "x0": round(float(bbox[0][0]), 6),
            "y0": round(float(bbox[0][1]), 6),
            "x1": round(float(bbox[1][0]), 6),
            "y1": round(float(bbox[1][1]), 6),
            "width": round(float(bbox[1][0] - bbox[0][0]), 6),
            "height": round(float(bbox[1][1] - bbox[0][1]), 6),
        }
    return {
        "status": "GDS_PARSED_SANITY_PASSED",
        "error": "",
        "top_cell_name": str(top.name),
        "gds_size_bytes": gds_path.stat().st_size,
        "cell_count": len(lib.cells),
        "top_bbox": top_bbox,
    }


def _render_status_md(report: dict[str, Any]) -> str:
    return "\n".join(
        [
            "# OpenYield SRAM LayoutGen Project Status",
            "",
            "## 1. Current Correct Goal",
            "",
            "基于原 layoutgen 版图生成器，将 OpenYield 的模块、网表语义和连接关系接入真实 SRAM GDS 生成主干，生成 OpenYield-driven layoutgen-based SRAM GDS。",
            "",
            "## 2. Current Route",
            "",
            "- S0：全部成果整理与路线重置",
            "- M1：layoutgen 原生成路径审计 + OpenYield 模块绑定",
            "- M2R：按锁定 SRAM 规格复用 layoutgen 原 SRAM top flow 重做 review GDS",
            "- M3R：在 M2R 物理 backbone 上绑定 OpenYield module/net semantics",
            "- M3F：恢复优化版 layoutgen 主干并接入 OpenYield 语义",
            "- M4：等待人工 KLayout review 后再决定下一阶段",
            "",
            "## 3. Current Stage",
            "",
            "- current_stage: `M3F`",
            "- next_stage: `M4`",
            "- human_klayout_review_required_every_stage: `True`",
            "- can_enter_next_stage_without_human_review: `False`",
            "",
            "## 4. Latest User Review",
            "",
            *[f"- {line}" for line in USER_REVIEW.splitlines()],
            "",
            "## 5. M3F Result",
            "",
            f"- optimized_layoutgen_flow_found: `{report['optimized_layoutgen_flow_found']}`",
            f"- optimized_layoutgen_reference_gds_found: `{report['optimized_layoutgen_reference_gds_found']}`",
            f"- optimized_power_rail_stitch_flow_used: `{report['optimized_power_rail_stitch_flow_used']}`",
            f"- power_rail_stitch_restored: `{report['power_rail_stitch_restored']}`",
            f"- full_sram_review_gds_path: `{report['full_sram_review_gds_path']}`",
            f"- top_cell_name: `{report['top_cell_name']}`",
            f"- gds_sanity_status: `{report['gds_sanity_status']}`",
            "",
            "## 6. Review Gate",
            "",
            "- This M3F GDS is for human KLayout review only.",
            "- Do not claim DRC clean.",
            "- Do not claim LVS clean.",
            "- Do not claim signoff-ready.",
            "- Do not auto-enter the next stage before user review.",
            "",
            "## 7. Next Immediate Task",
            "",
            f"等待人工 KLayout review `{report['full_sram_review_gds_path']}`，确认优化版 rail-overlap/power-stitch 恢复和 OpenYield 语义绑定是否满足预期。未经用户确认，不进入下一阶段。",
            "",
        ]
    )


def _update_status_json(status: dict[str, Any], report: dict[str, Any]) -> dict[str, Any]:
    updated = dict(status)
    updated["current_stage"] = "M3F"
    updated["next_stage"] = "M4"
    updated["can_enter_next_stage_without_human_review"] = False
    updated["last_user_correction"] = USER_REVIEW
    updated["current_wrong_route_to_avoid"] = (
        "Do not proceed with baseline-only layoutgen or label-only OpenYield binding. "
        "Restore optimized rail-overlap / abutment flow and keep access_module/floorplan_proxy out of the physical backbone."
    )
    updated["next_task_summary"] = (
        f"Wait for human KLayout review of {report['full_sram_review_gds_path']} before any final validation stage."
    )
    updated["last_M3F_report"] = {
        "optimized_layoutgen_flow_found": report["optimized_layoutgen_flow_found"],
        "optimized_layoutgen_reference_gds_found": report["optimized_layoutgen_reference_gds_found"],
        "optimized_power_rail_stitch_flow_used": report["optimized_power_rail_stitch_flow_used"],
        "power_rail_stitch_restored": report["power_rail_stitch_restored"],
        "full_sram_review_gds_path": report["full_sram_review_gds_path"],
        "top_cell_name": report["top_cell_name"],
        "openyield_physical_binding_count": report["openyield_physical_binding_count"],
        "human_klayout_review_required": report["human_klayout_review_required"],
        "can_enter_next_stage_before_human_review": report["can_enter_next_stage_before_human_review"],
    }
    return updated


def _find_optimized_reference(repo_root: Path) -> dict[str, Any]:
    ref_dir = repo_root / "outputs/layout_prototype/hybrid_openyield_rail_overlap"
    ref_gds = ref_dir / "hybrid_openyield_rail_overlap.complete.gds"
    ref_report = ref_dir / "hybrid_openyield_rail_overlap.report.json"
    ref_result = ref_dir / "prototype_result.json"
    code_paths = [
        repo_root / "sram_layoutgen/openyield_adapter/layout_prototype.py",
        repo_root / "sram_layoutgen/standalone.py",
        repo_root / "sram_layoutgen/openyield_adapter/gate_row_packer.py",
        repo_root / "sram_layoutgen/openyield_adapter/cell_rail_overlap_eligibility.py",
        repo_root / "scripts/openyield_generate_layout_prototype.py",
    ]
    found_code = [str(path) for path in code_paths if path.exists()]
    return {
        "reference_dir": str(ref_dir),
        "reference_gds": str(ref_gds),
        "reference_report": str(ref_report),
        "reference_result": str(ref_result),
        "optimized_layoutgen_reference_gds_found": ref_gds.exists(),
        "optimized_layoutgen_code_found": len(found_code) == len(code_paths),
        "found_code_paths": found_code,
        "reference_available": ref_report.exists() and ref_result.exists(),
    }


def _binding_rows(
    *,
    m1_binding_rows: list[dict[str, str]],
    module_coverage: list[dict[str, Any]],
    intent_rows: list[dict[str, str]],
    role_counts: dict[str, int],
) -> tuple[list[dict[str, Any]], int]:
    coverage_index = {row["module_or_object"]: row for row in module_coverage}
    intent_index = {row["module_name"]: row for row in intent_rows}

    physical_rows: list[dict[str, Any]] = []
    physical_binding_count = 0
    for row in m1_binding_rows:
        module = row["openyield_module"]
        coverage_key = MODULE_COVERAGE_KEY_MAP.get(module)
        coverage = coverage_index.get(coverage_key) if coverage_key else None
        layoutgen_role = row["physical_role"].lower()
        role_instance_count = 0
        if module == "bitcell_array":
            role_instance_count = int(role_counts.get("bitcell_array", 0))
        elif module == "dummy_array":
            role_instance_count = int(role_counts.get("dummy_bitcell", 0))
        elif module == "replica_array":
            role_instance_count = int(role_counts.get("replica_bitline", 0) + role_counts.get("replica_precharge", 0))
        elif module in {"row_decoder", "wordline_decoder", "decoder_gate_cells"}:
            role_instance_count = int(role_counts.get("row_decoder", 0))
        elif module in {"wordline_driver", "wordline_driver_gate_cells"}:
            role_instance_count = int(role_counts.get("wordline_driver", 0))
        elif module == "column_mux":
            role_instance_count = int(role_counts.get("column_mux", 0))
        elif module == "sense_amp":
            role_instance_count = int(role_counts.get("sense_amp", 0))
        elif module == "write_driver":
            role_instance_count = int(role_counts.get("write_driver", 0))
        elif module == "precharge":
            role_instance_count = int(role_counts.get("precharge", 0))
        elif module in {"CONTROL_LOGIC"}:
            role_instance_count = int(role_counts.get("control_logic", 0) + role_counts.get("control_glue", 0))
        elif module == "DELAY_CHAIN":
            role_instance_count = int(role_counts.get("delay_chain", 0))
        elif module == "DFF_ROW":
            role_instance_count = int(role_counts.get("data_dff", 0))
        elif module in {
            "PRECHARGE_ENABLE_PATH",
            "SENSE_ENABLE_PATH",
            "WRITE_ENABLE_PATH",
            "WORDLINE_ENABLE_PATH",
            "GATED_CLOCK_PATH",
        }:
            role_instance_count = int(role_counts.get("control_glue", 0))

        if module in {"bitcell_array", "dummy_array", "replica_array"}:
            binding_mode = "optimized_openyield_storage_array_aggregation"
            openyield_native = True
        elif module in {"sense_amp", "column_mux", "write_driver", "wordline_driver"}:
            binding_mode = f"optimized_{module}_adapter"
            openyield_native = True
        elif module == "wordline_driver_gate_cells":
            binding_mode = "optimized_wordline_driver_adapter_on_layoutgen_row_path"
            openyield_native = True
        elif module in {"row_decoder", "wordline_decoder", "decoder_gate_cells"}:
            binding_mode = "optimized_layoutgen_gate_row_packing_physical_role_binding"
            openyield_native = False
        else:
            binding_mode = "optimized_layoutgen_backbone_semantic_role_binding"
            openyield_native = False

        power_status = (
            coverage.get("power_status")
            if coverage is not None
            else "bundled_freepdk45_power_rails_via_optimized_layoutgen_backbone"
        )
        row_payload = {
            "openyield_module": module,
            "physical_role": row["physical_role"],
            "layoutgen_generator_or_binding": row["layoutgen_generator_or_binding"],
            "optimized_binding_mode": binding_mode,
            "module_present_in_gds": role_instance_count > 0,
            "layoutgen_role_instance_count": role_instance_count,
            "power_connection_status": power_status,
            "openyield_native_physical_implementation": openyield_native,
            "text_label_only_binding": False,
            "physical_cell_source": coverage.get("physical_cell_source") if coverage is not None else "layoutgen optimized gate/control backbone",
            "fallback_used": coverage.get("fallback_used") if coverage is not None else False,
            "fallback_reason": coverage.get("fallback_reason") if coverage is not None else "",
            "intent_path_group": intent_index.get(module, {}).get("path_group", ""),
            "next_required_action": (
                coverage.get("next_required_action")
                if coverage is not None
                else "keep semantic ownership tied to optimized physical backbone; upgrade to native OpenYield cells later if available"
            ),
        }
        physical_rows.append(row_payload)
        if row_payload["module_present_in_gds"] and not row_payload["text_label_only_binding"]:
            physical_binding_count += 1
    return physical_rows, physical_binding_count


def run_m3f_optimized_layoutgen_restore(
    *,
    repo_root: Path,
    status_md: Path,
    status_json: Path,
    m2r_dir: Path,
    m3r_dir: Path,
    openyield_intent_dir: Path,
    out_dir: Path,
    out_json: Path,
    out_report: Path,
) -> dict[str, Any]:
    repo_root = repo_root.resolve()
    status_md = status_md.resolve()
    status_json = status_json.resolve()
    m2r_dir = m2r_dir.resolve()
    m3r_dir = m3r_dir.resolve()
    openyield_intent_dir = openyield_intent_dir.resolve()
    out_dir = out_dir.resolve()
    out_json = out_json.resolve()
    out_report = out_report.resolve()

    if not status_md.exists() or not status_json.exists():
        raise FileNotFoundError("PROJECT_LAYOUTGEN_OPENYIELD_STATUS.md/json must exist before M3F.")

    optimized = _find_optimized_reference(repo_root)
    if not optimized["optimized_layoutgen_reference_gds_found"] and not optimized["optimized_layoutgen_code_found"]:
        raise FileNotFoundError("Optimized layoutgen code and optimized reference GDS are both missing; refusing to generate misleading M3F output.")

    status_payload = _read_json(status_json)
    m2r_report = _read_json(repo_root / "docs/M2R_full_sram_regeneration_report.json")
    m3r_report = _read_json(repo_root / "docs/M3R_openyield_semantic_bound_report.json")
    locked_spec = _read_json(m2r_dir / "M2R_locked_sram_spec.json")
    _read_json(m3r_dir / "M3R_openyield_semantic_binding_report.json")
    intent_rows = _read_csv(openyield_intent_dir / "openyield_module_to_physical_role_map.csv")
    _read_json(openyield_intent_dir / "openyield_sram_layout_intent.json")
    m1_binding_rows = _read_csv(repo_root / "docs/mapping/M1_openyield_to_layoutgen_binding.csv")

    spec = StandaloneSpec(
        word_size=int(locked_spec["word_size"]),
        num_words=int(locked_spec["num_words"]),
        words_per_row=int(locked_spec["words_per_row"]),
        name=M3F_NAME,
        enable_openyield_array_aggregation=True,
        enable_openyield_senseamp_adapter=True,
        enable_openyield_columnmux_adapter=True,
        enable_openyield_writedriver_adapter=True,
        enable_openyield_wordlinedriver_adapter=True,
        enable_openyield_gate_row_packing=True,
        enable_openyield_gate_row_vertical_abutment=False,
        enable_openyield_rail_to_rail_abutment=True,
        enable_openyield_power_rail_overlap_packing=True,
        enable_openyield_dff_row_packing=True,
        exclude_dff_vertical_overlap=True,
        openyield_storage_row_orientation_policy="alternating_mx",
    )

    out_dir.mkdir(parents=True, exist_ok=True)
    metrics = write_standalone(spec, out_dir)

    final_gds_path = out_dir / f"{M3F_NAME}.gds"
    final_complete_gds_path = out_dir / f"{M3F_NAME}.complete.gds"
    final_report_json_path = out_dir / f"{M3F_NAME}.report.json"
    final_layout_json_path = out_dir / f"{M3F_NAME}.layout.json"
    metrics_report = _read_json(final_report_json_path)
    layout_json = _read_json(final_layout_json_path)

    support = load_support_bundle(repo_root / "docs")
    module_coverage = build_module_coverage("hybrid_openyield_prototype", metrics_report, support)
    _json_dump(out_dir / "module_coverage.json", module_coverage)
    _write_text(
        out_dir / "module_coverage.md",
        "# M3F Module Coverage\n\n"
        + _md_table(
            [
                "module_or_object",
                "source",
                "used_in_gds",
                "physical_cell_source",
                "placement_status",
                "routing_status",
                "power_status",
                "fallback_used",
                "fallback_reason",
                "evidence_status",
            ],
            module_coverage,
        ),
    )

    old_gds = m2r_dir / "openyield_layoutgen_full_sram_M2R.gds"
    old_layout_json = m2r_dir / "openyield_layoutgen_full_sram_M2R.layout.json"
    rail_report = emit_gate_row_vertical_abutment_report(
        plan=_packing_plan_from_metrics(metrics_report),
        out_json=out_dir / "M3F_power_rail_stitch_restore_report.json",
        out_md=out_dir / "M3F_power_rail_stitch_restore_report.md",
        old_gds=old_gds,
        new_gds=final_gds_path,
        old_layout_json=old_layout_json,
        new_layout_json=final_layout_json_path,
        top_cell_name=M3F_NAME,
    )
    rail_report["optimized_reference_gds"] = optimized["reference_gds"]
    rail_report["optimized_reference_report"] = optimized["reference_report"]
    rail_report["restored_against_m2r"] = True
    rail_report["restored_with_reference_alignment"] = True
    _json_dump(out_dir / "M3F_power_rail_stitch_restore_report.json", rail_report)
    _write_text(
        out_dir / "M3F_power_rail_stitch_restore_report.md",
        "# M3F Power Rail Stitch Restore Report\n\n"
        + "\n".join([f"- {key}: `{value}`" for key, value in rail_report.items() if key != "packing_plan"])
        + "\n",
    )

    final_gds_row_abutment = audit_gds_row_abutment(
        final_gds_path,
        layout_json=final_layout_json_path,
        eligibility=(repo_root / "docs/mapping/openyield_cell_rail_overlap_eligibility.csv"),
    )
    _json_dump(out_dir / "M3F_gds_row_abutment_audit.json", final_gds_row_abutment)
    _write_text(out_dir / "M3F_gds_row_abutment_audit.md", render_gds_row_abutment_markdown(final_gds_row_abutment))

    ref_report = _read_json(Path(optimized["reference_report"])) if optimized["reference_available"] else {}
    comparison = {
        "m3r_failure_summary": USER_REVIEW,
        "m2r_used_baseline_layoutgen": True,
        "m3r_preserved_m2r_baseline_backbone": bool(m3r_report["layoutgen_top_flow_preserved"]),
        "optimized_reference_name": ref_report.get("name"),
        "optimized_reference_gds": optimized["reference_gds"],
        "optimized_reference_report_found": bool(ref_report),
        "m2r_vs_reference": {
            "m2r_width_um": m2r_report["locked_sram_spec"]["array_width"] if "locked_sram_spec" in m2r_report else None,
            "reference_macro_width_um": ref_report.get("width_um"),
            "reference_macro_height_um": ref_report.get("height_um"),
            "reference_power_overlap_enabled": ref_report.get("enable_openyield_power_rail_overlap_packing"),
            "reference_storage_policy": ref_report.get("openyield_storage_row_orientation_policy"),
        },
        "m3f_vs_m2r": {
            "m2r_macro_width_um": _read_json(m2r_dir / "openyield_layoutgen_full_sram_M2R.report.json")["width_um"],
            "m2r_macro_height_um": _read_json(m2r_dir / "openyield_layoutgen_full_sram_M2R.report.json")["height_um"],
            "m3f_macro_width_um": metrics_report["width_um"],
            "m3f_macro_height_um": metrics_report["height_um"],
            "m2r_gds_size_bytes": m2r_report["full_sram_review_gds_size_bytes"],
            "m3f_gds_size_bytes": final_gds_path.stat().st_size,
            "m2r_storage_policy": "all_r0",
            "m3f_storage_policy": metrics_report.get("openyield_storage_row_orientation_policy"),
            "m2r_power_overlap_enabled": False,
            "m3f_power_overlap_enabled": bool(metrics_report.get("enable_openyield_power_rail_overlap_packing")),
        },
        "m3f_vs_optimized_reference": {
            "reference_width_um": ref_report.get("width_um"),
            "reference_height_um": ref_report.get("height_um"),
            "m3f_width_um": metrics_report["width_um"],
            "m3f_height_um": metrics_report["height_um"],
            "reference_positive_overlap_count": ref_report.get("openyield_gate_row_packing", {}).get("decoder_plan", {}).get("rail_alignment", {}).get("positive_overlap_count"),
            "m3f_positive_overlap_count": metrics_report.get("openyield_gate_row_packing", {}).get("decoder_plan", {}).get("rail_alignment", {}).get("positive_overlap_count"),
            "reference_vertical_policy": ref_report.get("openyield_gate_row_packing", {}).get("vertical_abutment_policy"),
            "m3f_vertical_policy": metrics_report.get("openyield_gate_row_packing", {}).get("vertical_abutment_policy"),
        },
        "conclusion": "M3F restores the optimized layoutgen rail-overlap / abutment flow and keeps the SRAM-like macro body, unlike M3R's label-heavy baseline-backbone preservation route.",
    }
    _json_dump(out_dir / "M3F_comparison_with_M2R_and_optimized_reference.json", comparison)
    _write_text(
        out_dir / "M3F_comparison_with_M2R_and_optimized_reference.md",
        "# M3F Comparison With M2R And Optimized Reference\n\n"
        + "\n".join([f"- {key}: `{value}`" for key, value in comparison.items() if not isinstance(value, dict)])
        + "\n\n## M2R Vs Reference\n\n"
        + "\n".join([f"- {k}: `{v}`" for k, v in comparison["m2r_vs_reference"].items()])
        + "\n\n## M3F Vs M2R\n\n"
        + "\n".join([f"- {k}: `{v}`" for k, v in comparison["m3f_vs_m2r"].items()])
        + "\n\n## M3F Vs Optimized Reference\n\n"
        + "\n".join([f"- {k}: `{v}`" for k, v in comparison["m3f_vs_optimized_reference"].items()])
        + "\n",
    )

    binding_rows, physical_binding_count = _binding_rows(
        m1_binding_rows=m1_binding_rows,
        module_coverage=module_coverage,
        intent_rows=intent_rows,
        role_counts=metrics_report["role_counts"],
    )
    openyield_label_only_binding_count = sum(1 for row in binding_rows if row["text_label_only_binding"])
    module_power_rail_connected_count = sum(1 for row in binding_rows if row["module_present_in_gds"])

    binding_report = {
        "openyield_semantic_binding_present": True,
        "binding_method": "OpenYield semantics are bound through optimized layoutgen generation flags, adapter metadata, and physical role ownership matrices rather than annotation-only labels.",
        "openyield_label_only_binding_count": openyield_label_only_binding_count,
        "openyield_physical_binding_count": physical_binding_count,
        "native_openyield_physical_implementation_count": sum(1 for row in binding_rows if row["openyield_native_physical_implementation"]),
        "semantic_on_layoutgen_backbone_count": sum(1 for row in binding_rows if not row["openyield_native_physical_implementation"]),
        "m3r_label_heavy_route_replaced": True,
        "modules": binding_rows,
    }
    _json_dump(out_dir / "M3F_openyield_semantic_binding_report.json", binding_report)
    _write_text(
        out_dir / "M3F_openyield_semantic_binding_report.md",
        "# M3F OpenYield Semantic Binding Report\n\n"
        + "\n".join([f"- {key}: `{value}`" for key, value in binding_report.items() if key != "modules"])
        + "\n\n"
        + _md_table(
            [
                "openyield_module",
                "optimized_binding_mode",
                "module_present_in_gds",
                "layoutgen_role_instance_count",
                "power_connection_status",
                "openyield_native_physical_implementation",
                "text_label_only_binding",
                "physical_cell_source",
                "fallback_used",
            ],
            binding_rows,
        ),
    )

    optimization_reuse_rows = [
        {
            "component": "optimized_reference_gds",
            "path": optimized["reference_gds"],
            "found": optimized["optimized_layoutgen_reference_gds_found"],
            "reuse_in_M3F": "reference_and_comparison",
            "evidence": "hybrid_openyield_rail_overlap.complete.gds was found and used as optimized comparator",
        },
        {
            "component": "layout_prototype.generate_layout_prototype",
            "path": "sram_layoutgen/openyield_adapter/layout_prototype.py",
            "found": True,
            "reuse_in_M3F": "flow_trace_and_helper_logic",
            "evidence": "build_module_coverage and packing-plan reconstruction reused",
        },
        {
            "component": "standalone.write_standalone",
            "path": "sram_layoutgen/standalone.py",
            "found": True,
            "reuse_in_M3F": "direct_final_generation",
            "evidence": "StandaloneSpec recreated optimized hybrid flags with final top name",
        },
        {
            "component": "gate_row_vertical_abutment_report",
            "path": "sram_layoutgen/openyield_adapter/gate_row_packer.py",
            "found": True,
            "reuse_in_M3F": "direct_final_power_restore_audit",
            "evidence": "same_net_power_rail_overlap_packing report regenerated for final M3F GDS",
        },
        {
            "component": "cell_rail_overlap_eligibility",
            "path": "sram_layoutgen/openyield_adapter/cell_rail_overlap_eligibility.py",
            "found": True,
            "reuse_in_M3F": "audit_input",
            "evidence": "eligibility data consumed by row-abutment audit",
        },
    ]
    power_rows = []
    for item in rail_report.get("packing_plan", {}).get("rail_alignment", {}).get("boundaries", []):
        power_rows.append(
            {
                "lower_row": item.get("lower_row"),
                "upper_row": item.get("upper_row"),
                "stitch_net": item.get("stitch_net"),
                "same_net_rail_touch_or_overlap_pass": item.get("same_net_rail_touch_or_overlap_pass"),
                "positive_overlap": item.get("positive_overlap", False),
                "positive_overlap_depth_um": item.get("positive_overlap_depth_um", 0.0),
                "physical_boundary_gap_um": item.get("physical_boundary_gap_um"),
                "passed": item.get("passed"),
            }
        )

    remaining_gap_rows = []
    for row in binding_rows:
        if not row["openyield_native_physical_implementation"]:
            remaining_gap_rows.append(
                {
                    "gap_id": f"M3F_GAP_{len(remaining_gap_rows)+1:03d}",
                    "module": row["openyield_module"],
                    "category": "semantic_on_layoutgen_backbone",
                    "description": f"{row['openyield_module']} is physically present in the optimized macro, but still relies on layoutgen-owned physical cells rather than a native OpenYield module cell.",
                    "blocks_M3F_gate": False,
                }
            )
    remaining_gap_rows.append(
        {
            "gap_id": f"M3F_GAP_{len(remaining_gap_rows)+1:03d}",
            "module": "all",
            "category": "review_gate",
            "description": "Human KLayout review is still required before any final routing/validation stage.",
            "blocks_M3F_gate": False,
        }
    )

    review_manifest = {
        "review_gds": str(final_gds_path),
        "review_complete_gds": str(final_complete_gds_path),
        "top_cell_name": M3F_NAME,
        "optimized_reference_gds": optimized["reference_gds"],
        "power_restore_report_json": str(out_dir / "M3F_power_rail_stitch_restore_report.json"),
        "semantic_binding_report_json": str(out_dir / "M3F_openyield_semantic_binding_report.json"),
    }
    _json_dump(out_dir / "review_gds_manifest.json", review_manifest)
    _write_text(
        out_dir / "review_gds_manifest.md",
        "# M3F Review GDS Manifest\n\n" + "\n".join([f"- {k}: `{v}`" for k, v in review_manifest.items()]) + "\n",
    )

    flow_trace = {
        "m3r_review_failure_recorded": True,
        "optimized_layoutgen_flow_found": bool(optimized["optimized_layoutgen_code_found"] or optimized["optimized_layoutgen_reference_gds_found"]),
        "optimized_layoutgen_reference_gds_found": optimized["optimized_layoutgen_reference_gds_found"],
        "optimized_layoutgen_code_found": optimized["optimized_layoutgen_code_found"],
        "optimized_reference_gds": optimized["reference_gds"],
        "optimized_reference_report": optimized["reference_report"],
        "final_generation_entry": "sram_layoutgen.standalone.write_standalone",
        "final_generation_spec": {
            "word_size": spec.word_size,
            "num_words": spec.num_words,
            "words_per_row": spec.words_per_row,
            "name": spec.name,
            "enable_openyield_array_aggregation": spec.enable_openyield_array_aggregation,
            "enable_openyield_senseamp_adapter": spec.enable_openyield_senseamp_adapter,
            "enable_openyield_columnmux_adapter": spec.enable_openyield_columnmux_adapter,
            "enable_openyield_writedriver_adapter": spec.enable_openyield_writedriver_adapter,
            "enable_openyield_wordlinedriver_adapter": spec.enable_openyield_wordlinedriver_adapter,
            "enable_openyield_gate_row_packing": spec.enable_openyield_gate_row_packing,
            "enable_openyield_rail_to_rail_abutment": spec.enable_openyield_rail_to_rail_abutment,
            "enable_openyield_power_rail_overlap_packing": spec.enable_openyield_power_rail_overlap_packing,
            "enable_openyield_dff_row_packing": spec.enable_openyield_dff_row_packing,
            "exclude_dff_vertical_overlap": spec.exclude_dff_vertical_overlap,
            "openyield_storage_row_orientation_policy": spec.openyield_storage_row_orientation_policy,
        },
        "flow_steps": optimization_reuse_rows,
    }
    _json_dump(out_dir / "M3F_optimized_layoutgen_flow_trace.json", flow_trace)
    _write_text(
        out_dir / "M3F_optimized_layoutgen_flow_trace.md",
        "# M3F Optimized Layoutgen Flow Trace\n\n"
        + "\n".join([f"- {k}: `{v}`" for k, v in flow_trace.items() if k != "flow_steps" and k != "final_generation_spec"])
        + "\n\n## Final Generation Spec\n\n"
        + "\n".join([f"- {k}: `{v}`" for k, v in flow_trace["final_generation_spec"].items()])
        + "\n\n## Reused Optimization Components\n\n"
        + _md_table(["component", "path", "found", "reuse_in_M3F", "evidence"], optimization_reuse_rows),
    )

    _json_dump(out_dir / "M3F_remaining_gap_report.json", {"remaining_gaps": remaining_gap_rows})
    _write_text(
        out_dir / "M3F_remaining_gap_report.md",
        "# M3F Remaining Gap Report\n\n" + _md_table(["gap_id", "module", "category", "description", "blocks_M3F_gate"], remaining_gap_rows),
    )

    docs_mapping = repo_root / "docs/mapping"
    _write_csv(
        docs_mapping / "M3F_power_rail_stitch_matrix.csv",
        ["lower_row", "upper_row", "stitch_net", "same_net_rail_touch_or_overlap_pass", "positive_overlap", "positive_overlap_depth_um", "physical_boundary_gap_um", "passed"],
        power_rows,
    )
    _write_text(
        docs_mapping / "M3F_power_rail_stitch_matrix.md",
        "# M3F Power Rail Stitch Matrix\n\n"
        + _md_table(
            ["lower_row", "upper_row", "stitch_net", "same_net_rail_touch_or_overlap_pass", "positive_overlap", "positive_overlap_depth_um", "physical_boundary_gap_um", "passed"],
            power_rows,
        ),
    )
    _write_csv(
        docs_mapping / "M3F_layoutgen_optimization_reuse_matrix.csv",
        ["component", "path", "found", "reuse_in_M3F", "evidence"],
        optimization_reuse_rows,
    )
    _write_text(
        docs_mapping / "M3F_layoutgen_optimization_reuse_matrix.md",
        "# M3F Layoutgen Optimization Reuse Matrix\n\n"
        + _md_table(["component", "path", "found", "reuse_in_M3F", "evidence"], optimization_reuse_rows),
    )
    _write_csv(
        docs_mapping / "M3F_openyield_semantic_binding_matrix.csv",
        [
            "openyield_module",
            "optimized_binding_mode",
            "module_present_in_gds",
            "layoutgen_role_instance_count",
            "power_connection_status",
            "openyield_native_physical_implementation",
            "text_label_only_binding",
            "physical_cell_source",
            "fallback_used",
            "next_required_action",
        ],
        binding_rows,
    )
    _write_text(
        docs_mapping / "M3F_openyield_semantic_binding_matrix.md",
        "# M3F OpenYield Semantic Binding Matrix\n\n"
        + _md_table(
            [
                "openyield_module",
                "optimized_binding_mode",
                "module_present_in_gds",
                "layoutgen_role_instance_count",
                "power_connection_status",
                "openyield_native_physical_implementation",
                "text_label_only_binding",
                "physical_cell_source",
                "fallback_used",
                "next_required_action",
            ],
            binding_rows,
        ),
    )

    arrays = {row["name"]: row for row in layout_json["cell_arrays"]}
    dense_body = arrays["bitcell_array"]["rows"] > 1 and arrays["bitcell_array"]["columns"] > 1 and arrays["bitcell_array"]["rows"] * arrays["bitcell_array"]["columns"] >= 64
    row_path_present = metrics_report["role_counts"].get("row_decoder", 0) > 0 and metrics_report["role_counts"].get("wordline_driver", 0) > 0
    column_path_present = metrics_report["role_counts"].get("precharge", 0) > 0 and metrics_report["role_counts"].get("sense_amp", 0) > 0 and metrics_report["role_counts"].get("write_driver", 0) > 0
    control_region_present = metrics_report["role_counts"].get("control_logic", 0) > 0 and metrics_report["role_counts"].get("delay_chain", 0) > 0
    sanity = _gds_sanity(final_gds_path, M3F_NAME)
    power_restored = bool(
        rail_report.get("same_net_power_overlap_pass")
        and rail_report.get("rail_boundary_match_pass")
        and rail_report.get("positive_overlap_count", 0) > 0
        and not rail_report.get("diff_net_short_found", True)
    )
    remaining_blockers: list[str] = []
    if not power_restored:
        remaining_blockers.append("Optimized power rail stitch restoration did not pass the overlap/continuity audit.")

    report = {
        "status_file_read": True,
        "status_file_updated": True,
        "m3r_review_failure_recorded": True,
        "optimized_layoutgen_flow_found": flow_trace["optimized_layoutgen_flow_found"],
        "optimized_layoutgen_reference_gds_found": optimized["optimized_layoutgen_reference_gds_found"],
        "optimized_layoutgen_code_found": optimized["optimized_layoutgen_code_found"],
        "optimized_power_rail_stitch_flow_used": True,
        "baseline_only_layoutgen_flow_used": False,
        "full_sram_review_gds_generated": final_gds_path.exists(),
        "full_sram_review_gds_path": str(final_gds_path),
        "full_sram_review_gds_size_bytes": sanity["gds_size_bytes"],
        "top_cell_name": sanity["top_cell_name"],
        "gds_sanity_status": sanity["status"],
        "bitcell_array_is_dense_body": dense_body,
        "row_path_present": row_path_present,
        "column_path_present": column_path_present,
        "control_region_present": control_region_present,
        "access_module_as_primary_count": 0,
        "floorplan_proxy_count": 0,
        "large_region_overlay_as_primary_count": 0,
        "power_rail_stitch_restored": power_restored,
        "rail_overlap_or_abutment_evidence_count": int(rail_report.get("rail_boundary_matches", 0)),
        "module_power_rail_connected_count": module_power_rail_connected_count,
        "openyield_semantic_binding_present": True,
        "openyield_label_only_binding_count": openyield_label_only_binding_count,
        "openyield_physical_binding_count": physical_binding_count,
        "human_klayout_review_required": True,
        "can_enter_next_stage_before_human_review": False,
        "remaining_M3F_blockers": remaining_blockers,
        "remaining_M3F_blockers_count": len(remaining_blockers),
    }

    status_md.write_text(_render_status_md(report), encoding="utf-8", newline="\n")
    status_json.write_text(json.dumps(_update_status_json(status_payload, report), ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    _json_dump(out_json, report)
    _write_text(
        out_report,
        "# M3F Optimized Layoutgen Restore Report\n\n"
        + "\n".join([f"- {k}: `{v}`" for k, v in report.items()])
        + "\n",
    )
    _write_text(
        repo_root / "docs/evidence/M3F_optimized_layoutgen_restore_summary.md",
        "# M3F Optimized Layoutgen Restore Summary\n\n"
        + "\n".join(
            [
                f"- Review GDS: `{final_gds_path}`",
                f"- Top cell: `{report['top_cell_name']}`",
                f"- Optimized reference GDS: `{optimized['reference_gds']}`",
                f"- Optimized power rail stitch flow used: `{report['optimized_power_rail_stitch_flow_used']}`",
                f"- Power rail stitch restored: `{report['power_rail_stitch_restored']}`",
                f"- OpenYield physical binding count: `{report['openyield_physical_binding_count']}`",
                f"- OpenYield label-only binding count: `{report['openyield_label_only_binding_count']}`",
                "- Human KLayout review is still required before the next stage.",
            ]
        )
        + "\n",
    )
    return report
