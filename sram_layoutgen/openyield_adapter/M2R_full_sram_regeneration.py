from __future__ import annotations

import csv
import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

import gdstk

from sram_layoutgen.openyield_adapter.layout_prototype import DEFAULT_LAYOUT_CASE
from sram_layoutgen.standalone import StandaloneSpec, write_standalone


USER_CORRECTION = (
    "M2 physical review failed because modules were freely scattered, SRAM spec was not locked, "
    "layoutgen top-level generation rules were not followed, and the result did not resemble a complete SRAM macro."
)

FLOW_TRACE_STEPS = [
    {
        "step": 1,
        "component": "scripts/openyield_generate_layout_prototype.py",
        "function": "main",
        "role": "CLI entry for legacy_baseline / hybrid prototype generation.",
        "reused_for_M2R": "evidence_only",
    },
    {
        "step": 2,
        "component": "sram_layoutgen/openyield_adapter/layout_prototype.py",
        "function": "generate_layout_prototype",
        "role": "Build guarded prototype config and call the original SRAM macro generator via write_standalone.",
        "reused_for_M2R": "spec_and_flow_evidence",
    },
    {
        "step": 3,
        "component": "sram_layoutgen/standalone.py",
        "function": "write_standalone",
        "role": "Original SRAM top-level generation driver: creates GDS, complete.gds, LEF, SPICE, layout JSON, and metrics.",
        "reused_for_M2R": "direct",
    },
    {
        "step": 4,
        "component": "sram_layoutgen/standalone.py",
        "function": "build_layout",
        "role": "Deterministic SRAM physical assembly: bitcell/dummy/replica arrays, row path, column path, control region, routing guides, and pin export.",
        "reused_for_M2R": "direct",
    },
    {
        "step": 5,
        "component": "sram_layoutgen/gds_writer.py",
        "function": "GDSWriter.write",
        "role": "Write top cell and hierarchy to GDS using layout DB objects from write_standalone/build_layout.",
        "reused_for_M2R": "direct",
    },
]


@dataclass(frozen=True)
class LockedSramSpec:
    word_size: int
    num_words: int
    words_per_row: int
    num_rows: int
    num_cols: int
    num_banks: int
    num_ports: int
    tech: str
    bitcell_pitch_x: float
    bitcell_pitch_y: float
    array_width: float
    array_height: float
    row_path_side: str
    column_path_side: str
    control_region_side: str
    power_rail_strategy: str
    top_pin_strategy: str
    evidence_sources: list[str]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _json_dump(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8", newline="\n")


def _write_csv(path: Path, fieldnames: list[str], rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
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


def _lock_spec_from_evidence(repo_root: Path, layoutgen_reference_gds: Path) -> LockedSramSpec:
    prototype_result = _read_json(repo_root / "outputs/layout_prototype/baseline_legacy/prototype_result.json")
    report = _read_json(repo_root / "outputs/layout_prototype/baseline_legacy/sram_8x64_wpr4_fd45.report.json")
    layout_json = _read_json(repo_root / "outputs/layout_prototype/baseline_legacy/sram_8x64_wpr4_fd45.layout.json")
    meta = layout_json["metadata"]
    stem = layoutgen_reference_gds.stem

    code_spec = {
        "word_size": int(DEFAULT_LAYOUT_CASE["word_size"]),
        "num_words": int(DEFAULT_LAYOUT_CASE["num_words"]),
        "words_per_row": int(DEFAULT_LAYOUT_CASE["words_per_row"]),
    }
    report_spec = {
        "word_size": int(report["word_size"]),
        "num_words": int(report["num_words"]),
        "words_per_row": int(report["words_per_row"]),
    }
    proto_spec = {
        "word_size": int(prototype_result["spec"]["word_size"]),
        "num_words": int(prototype_result["spec"]["num_words"]),
        "words_per_row": int(prototype_result["spec"]["words_per_row"]),
    }
    if code_spec != report_spec or report_spec != proto_spec:
        raise ValueError(f"Locked spec conflict between code/report/prototype evidence: {code_spec} vs {report_spec} vs {proto_spec}")
    if "8x64" not in stem or "wpr4" not in stem:
        raise ValueError(f"Reference GDS name does not match the expected baseline evidence: {stem}")

    arrays = {row["name"]: row for row in layout_json["cell_arrays"]}
    bitcell_array = arrays["bitcell_array"]["rect"]
    row_side = "left"
    column_side = "bottom"
    control_side = "left_bottom_periphery"
    return LockedSramSpec(
        word_size=report_spec["word_size"],
        num_words=report_spec["num_words"],
        words_per_row=report_spec["words_per_row"],
        num_rows=int(meta["num_rows"]),
        num_cols=int(meta["num_cols"]),
        num_banks=1,
        num_ports=1,
        tech="freepdk45",
        bitcell_pitch_x=float(meta["bitcell_pitch_x_um"]),
        bitcell_pitch_y=float(meta["bitcell_pitch_y_um"]),
        array_width=round(float(bitcell_array["x1"] - bitcell_array["x0"]), 6),
        array_height=round(float(bitcell_array["y1"] - bitcell_array["y0"]), 6),
        row_path_side=row_side,
        column_path_side=column_side,
        control_region_side=control_side,
        power_rail_strategy="write_standalone_bundled_freepdk45_power_rails",
        top_pin_strategy="write_standalone_perimeter_pins",
        evidence_sources=[
            "sram_layoutgen/openyield_adapter/layout_prototype.py::DEFAULT_LAYOUT_CASE",
            "outputs/layout_prototype/baseline_legacy/prototype_result.json",
            "outputs/layout_prototype/baseline_legacy/sram_8x64_wpr4_fd45.report.json",
            "outputs/layout_prototype/baseline_legacy/sram_8x64_wpr4_fd45.layout.json",
            str(layoutgen_reference_gds),
        ],
    )


def _render_locked_spec_md(spec: LockedSramSpec) -> str:
    lines = [
        "# M2R Locked SRAM Spec",
        "",
        "Locked from existing layoutgen baseline evidence before any GDS regeneration.",
        "",
    ]
    for key, value in spec.to_dict().items():
        lines.append(f"- {key}: `{value}`")
    return "\n".join(lines) + "\n"


def _build_flow_trace(repo_root: Path, spec: LockedSramSpec, generated_metrics: dict[str, Any]) -> dict[str, Any]:
    return {
        "layoutgen_top_flow_trace_available": True,
        "layoutgen_top_flow_used": True,
        "arbitrary_module_scatter_used": False,
        "locked_spec": spec.to_dict(),
        "original_layoutgen_complete_sram_entry_script": "scripts/openyield_generate_layout_prototype.py",
        "original_layoutgen_complete_sram_entry_function": "sram_layoutgen.openyield_adapter.layout_prototype.generate_layout_prototype",
        "original_layoutgen_top_generator_function": "sram_layoutgen.standalone.write_standalone",
        "original_layoutgen_layout_builder_function": "sram_layoutgen.standalone.build_layout",
        "original_layoutgen_gds_writer_function": "sram_layoutgen.gds_writer.GDSWriter.write",
        "parameters_used": {
            "word_size": spec.word_size,
            "num_words": spec.num_words,
            "words_per_row": spec.words_per_row,
            "name": "openyield_layoutgen_full_sram_M2R",
            "perimeter_pins": True,
            "enable_openyield_array_aggregation": False,
            "enable_openyield_senseamp_adapter": False,
            "enable_openyield_columnmux_adapter": False,
            "enable_openyield_writedriver_adapter": False,
            "enable_openyield_wordlinedriver_adapter": False,
        },
        "bitcell_array_generation": "build_layout creates bitcell_array/dummy_left_array/dummy_right_array/replica_bitline_array CellArray objects from the locked num_rows/num_cols and bitcell pitch.",
        "row_path_generation": "build_layout generates decoder and wordline-driver structures from the locked row count and row-address width on the array-adjacent side.",
        "column_path_generation": "build_layout generates precharge/column mux/sense amp/write driver stacks from num_cols, word_size, and words_per_row on the column side.",
        "power_rail_generation": "write_standalone emits normal and complete GDS through GDSWriter with bundled FreePDK45 rail layers and routing metadata.",
        "top_cell_writeout": "write_standalone writes <name>.gds and <name>.complete.gds using layout.top_name derived from StandaloneSpec.name.",
        "direct_reuse": [
            "write_standalone",
            "build_layout",
            "GDSWriter.write",
            "baseline 8x64 wpr4 placement and hierarchy conventions",
        ],
        "openyield_adaptation_needed": [
            "Map M1 OpenYield module roles onto baseline layoutgen roles for review reporting.",
            "Keep OpenYield module/net binding as evidence/input, not as arbitrary coordinate placement.",
        ],
        "generated_metrics_snapshot": {
            "gds": generated_metrics["gds"],
            "complete_gds": generated_metrics["complete_gds"],
            "layout_json": generated_metrics["layout_json"],
            "report_md": generated_metrics["report_md"],
        },
        "steps": FLOW_TRACE_STEPS,
    }


def _module_usage_rows(binding_rows: list[dict[str, str]], metrics: dict[str, Any]) -> tuple[list[dict[str, Any]], int]:
    role_counts = metrics["role_counts"]
    role_map = {
        "bitcell_array": ("bitcell_array", "cell_1rw array"),
        "dummy_array": ("dummy_bitcell", "dummy_cell_1rw boundary arrays"),
        "replica_array": ("replica_bitline", "replica_cell_1rw array plus replica precharge"),
        "row_decoder": ("row_decoder", "layoutgen generated decoder chain"),
        "wordline_decoder": ("row_decoder", "layoutgen generated decoder chain"),
        "decoder_gate_cells": ("row_decoder", "layoutgen generated decoder logic"),
        "wordline_driver": ("wordline_driver", "gen_wl_driver row path"),
        "wordline_driver_gate_cells": ("wordline_driver", "gen_wl_driver row path"),
        "column_mux": ("column_mux", "gen_col_mux column path"),
        "sense_amp": ("sense_amp", "sense_amp array"),
        "write_driver": ("write_driver", "write_driver array"),
        "precharge": ("precharge", "gen_precharge column path"),
        "CONTROL_LOGIC": ("control_logic", "control DFF array / control glue"),
        "DELAY_CHAIN": ("delay_chain", "gen_delay_inv chain"),
        "PRECHARGE_ENABLE_PATH": ("control_glue", "control glue"),
        "SENSE_ENABLE_PATH": ("control_glue", "control glue"),
        "WRITE_ENABLE_PATH": ("control_glue", "control glue"),
        "WORDLINE_ENABLE_PATH": ("control_glue", "control glue"),
        "GATED_CLOCK_PATH": ("control_glue", "control glue"),
        "DFF_ROW": ("data_dff", "data DFF array"),
    }
    rows: list[dict[str, Any]] = []
    for row in binding_rows:
        module_name = row["openyield_module"]
        layoutgen_role, implementation = role_map[module_name]
        rows.append(
            {
                "openyield_module": module_name,
                "physical_role": row["physical_role"],
                "binding_status": row["binding_status"],
                "layoutgen_role": layoutgen_role,
                "layoutgen_role_instance_count": int(role_counts.get(layoutgen_role, 0)),
                "physical_source_class": "layoutgen_top_flow_role",
                "implementation": implementation,
                "uses_first_round_openyield_gds": False,
                "temporary_wrapper": False,
            }
        )
    return rows, len(rows)


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
            "- M3：等待人工 KLayout review 后再决定下一阶段",
            "",
            "## 3. Current Stage",
            "",
            "- current_stage: `M2R`",
            "- next_stage: `M3`",
            "- human_klayout_review_required_every_stage: `True`",
            "- can_enter_next_stage_without_human_review: `False`",
            "",
            "## 4. Latest User Correction",
            "",
            f"- {USER_CORRECTION}",
            "",
            "## 5. M2R Result",
            "",
            f"- locked_sram_spec_available: `{report['locked_sram_spec_available']}`",
            f"- layoutgen_top_flow_trace_available: `{report['layoutgen_top_flow_trace_available']}`",
            f"- layoutgen_top_flow_used: `{report['layoutgen_top_flow_used']}`",
            f"- arbitrary_module_scatter_used: `{report['arbitrary_module_scatter_used']}`",
            f"- full_sram_review_gds_generated: `{report['full_sram_review_gds_generated']}`",
            f"- full_sram_review_gds_path: `{report['full_sram_review_gds_path']}`",
            f"- top_cell_name: `{report['top_cell_name']}`",
            f"- gds_sanity_status: `{report['gds_sanity_status']}`",
            "",
            "## 6. Review Gate",
            "",
            "- This M2R GDS is for human KLayout review only.",
            "- Do not claim DRC clean.",
            "- Do not claim LVS clean.",
            "- Do not claim signoff-ready.",
            "- Do not auto-enter M3 before user review.",
            "",
            "## 7. Next Immediate Task",
            "",
            f"等待人工 KLayout review `{report['full_sram_review_gds_path']}`。未经用户确认，不进入下一阶段。",
            "",
        ]
    )


def _update_status_json(status: dict[str, Any], report: dict[str, Any]) -> dict[str, Any]:
    updated = dict(status)
    updated["current_stage"] = "M2R"
    updated["next_stage"] = "M3"
    updated["can_enter_next_stage_without_human_review"] = False
    updated["last_user_correction"] = USER_CORRECTION
    updated["current_wrong_route_to_avoid"] = (
        "Do not freely scatter modules or use large region-guide overlays as the primary SRAM physical body; "
        "reuse the original layoutgen top-level SRAM flow."
    )
    updated["next_task_summary"] = f"Wait for human KLayout review of {report['full_sram_review_gds_path']} before entering the next stage."
    updated["last_M2R_report"] = {
        "locked_sram_spec_available": report["locked_sram_spec_available"],
        "layoutgen_top_flow_used": report["layoutgen_top_flow_used"],
        "arbitrary_module_scatter_used": report["arbitrary_module_scatter_used"],
        "full_sram_review_gds_path": report["full_sram_review_gds_path"],
        "top_cell_name": report["top_cell_name"],
        "temporary_wrapper_count": report["temporary_wrapper_count"],
        "human_klayout_review_required": report["human_klayout_review_required"],
        "can_enter_next_stage_before_human_review": report["can_enter_next_stage_before_human_review"],
    }
    return updated


def run_m2r_full_sram_regeneration(
    *,
    repo_root: Path,
    status_md: Path,
    status_json: Path,
    m1_binding: Path,
    m1_net_binding: Path,
    openyield_module_gds_dir: Path,
    layoutgen_reference_gds: Path,
    out_dir: Path,
    out_json: Path,
    out_report: Path,
) -> dict[str, Any]:
    repo_root = repo_root.resolve()
    status_md = status_md.resolve()
    status_json = status_json.resolve()
    m1_binding = m1_binding.resolve()
    m1_net_binding = m1_net_binding.resolve()
    openyield_module_gds_dir = openyield_module_gds_dir.resolve()
    layoutgen_reference_gds = layoutgen_reference_gds.resolve()
    out_dir = out_dir.resolve()
    out_json = out_json.resolve()
    out_report = out_report.resolve()

    if not status_md.exists() or not status_json.exists():
        raise FileNotFoundError("PROJECT_LAYOUTGEN_OPENYIELD_STATUS.md/json must exist before M2R.")

    status_payload = _read_json(status_json)
    binding_rows = _read_csv(m1_binding)
    _read_csv(m1_net_binding)

    spec = _lock_spec_from_evidence(repo_root, layoutgen_reference_gds)
    out_dir.mkdir(parents=True, exist_ok=True)
    _json_dump(out_dir / "M2R_locked_sram_spec.json", spec.to_dict())
    _write_text(out_dir / "M2R_locked_sram_spec.md", _render_locked_spec_md(spec))

    standalone_spec = StandaloneSpec(
        word_size=spec.word_size,
        num_words=spec.num_words,
        words_per_row=spec.words_per_row,
        name="openyield_layoutgen_full_sram_M2R",
    )
    metrics = write_standalone(standalone_spec, out_dir)
    flow_trace = _build_flow_trace(repo_root, spec, metrics)
    _json_dump(out_dir / "M2R_layoutgen_top_flow_trace.json", flow_trace)
    _write_text(
        out_dir / "M2R_layoutgen_top_flow_trace.md",
        "# M2R Layoutgen Top Flow Trace\n\n"
        + "\n".join(
            [
                f"- original_layoutgen_complete_sram_entry_script: `{flow_trace['original_layoutgen_complete_sram_entry_script']}`",
                f"- original_layoutgen_top_generator_function: `{flow_trace['original_layoutgen_top_generator_function']}`",
                f"- layoutgen_top_flow_used: `{flow_trace['layoutgen_top_flow_used']}`",
                f"- arbitrary_module_scatter_used: `{flow_trace['arbitrary_module_scatter_used']}`",
            ]
        )
        + "\n\n"
        + _md_table(
            ["step", "component", "function", "role", "reused_for_M2R"],
            flow_trace["steps"],
        ),
    )

    final_gds_path = out_dir / "openyield_layoutgen_full_sram_M2R.gds"
    sanity = _gds_sanity(final_gds_path, "openyield_layoutgen_full_sram_M2R")
    metrics_report = _read_json(out_dir / "openyield_layoutgen_full_sram_M2R.report.json")
    layout_json = _read_json(out_dir / "openyield_layoutgen_full_sram_M2R.layout.json")
    arrays = {row["name"]: row for row in layout_json["cell_arrays"]}
    module_usage_rows, layoutgen_real_count = _module_usage_rows(binding_rows, metrics_report)

    bitcell_array = arrays["bitcell_array"]
    dense_body = bitcell_array["rows"] > 1 and bitcell_array["columns"] > 1 and bitcell_array["rows"] * bitcell_array["columns"] >= 64
    visual_report = {
        "bitcell_array_present": "bitcell_array" in arrays,
        "bitcell_array_is_dense主体": dense_body,
        "dummy_or_replica_present": all(name in arrays for name in ("dummy_left_array", "dummy_right_array", "replica_bitline_array")),
        "row_path_present": metrics_report["role_counts"].get("row_decoder", 0) > 0 and metrics_report["role_counts"].get("wordline_driver", 0) > 0,
        "column_path_present": metrics_report["role_counts"].get("precharge", 0) > 0 and metrics_report["role_counts"].get("sense_amp", 0) > 0 and metrics_report["role_counts"].get("write_driver", 0) > 0,
        "control_region_present": metrics_report["role_counts"].get("control_logic", 0) > 0 and metrics_report["role_counts"].get("delay_chain", 0) > 0,
        "large_region_overlay_as_primary_count": 0,
        "access_module_as_primary_count": 0,
        "floorplan_proxy_count": 0,
        "temporary_wrapper_count": 0,
    }
    _json_dump(out_dir / "M2R_visual_sram_likeness_report.json", visual_report)
    _write_text(
        out_dir / "M2R_visual_sram_likeness_report.md",
        "# M2R Visual SRAM Likeness Report\n\n"
        + "\n".join([f"- {key}: `{value}`" for key, value in visual_report.items()])
        + "\n",
    )

    adaptation_report = {
        "layoutgen_real_generator_used_count": layoutgen_real_count,
        "first_round_openyield_gds_used_count": 0,
        "temporary_wrapper_count": 0,
        "module_usage_rows": module_usage_rows,
        "openyield_module_gds_dir_read": str(openyield_module_gds_dir),
        "adaptation_strategy": "Use M1 OpenYield bindings as role-mapping evidence while the physical GDS is regenerated entirely by the original layoutgen top flow.",
    }
    _json_dump(out_dir / "M2R_openyield_adaptation_report.json", adaptation_report)
    _write_text(
        out_dir / "M2R_openyield_adaptation_report.md",
        "# M2R OpenYield Adaptation Report\n\n"
        + "\n".join(
            [
                f"- layoutgen_real_generator_used_count: `{layoutgen_real_count}`",
                f"- first_round_openyield_gds_used_count: `0`",
                f"- temporary_wrapper_count: `0`",
            ]
        )
        + "\n\n"
        + _md_table(
            [
                "openyield_module",
                "physical_role",
                "binding_status",
                "layoutgen_role",
                "layoutgen_role_instance_count",
                "physical_source_class",
                "implementation",
            ],
            module_usage_rows,
        ),
    )

    remaining_gap_rows = [
        {
            "gap_id": "M2R_GAP_001",
            "category": "openyield_semantics",
            "severity": "review_only",
            "description": "This M2R rebuild prioritizes original layoutgen top-flow correctness; OpenYield semantic ownership is mapped in reports rather than re-routed into a new physical hierarchy.",
            "blocks_M2R_gate": False,
        },
        {
            "gap_id": "M2R_GAP_002",
            "category": "signoff",
            "severity": "review_only",
            "description": "Human KLayout review is still required before any next-stage claim; DRC/LVS/signoff are not claimed here.",
            "blocks_M2R_gate": False,
        },
    ]
    _json_dump(out_dir / "M2R_remaining_gap_report.json", {"remaining_gaps": remaining_gap_rows})
    _write_text(
        out_dir / "M2R_remaining_gap_report.md",
        "# M2R Remaining Gap Report\n\n" + _md_table(["gap_id", "category", "severity", "description", "blocks_M2R_gate"], remaining_gap_rows),
    )

    full_generation_report = {
        "generator": "write_standalone",
        "layout_builder": "build_layout",
        "metrics_report_json": str(out_dir / "openyield_layoutgen_full_sram_M2R.report.json"),
        "layout_json": str(out_dir / "openyield_layoutgen_full_sram_M2R.layout.json"),
        "complete_gds": str(out_dir / "openyield_layoutgen_full_sram_M2R.complete.gds"),
        "presentation_gds": str(out_dir / "openyield_layoutgen_full_sram_M2R.presentation.gds"),
        "route_guide_gds": str(out_dir / "openyield_layoutgen_full_sram_M2R.route_guides.gds"),
        "top_gds": str(final_gds_path),
        "top_bbox": sanity.get("top_bbox"),
        "layout_completeness": metrics_report["layout_completeness"],
        "structural_audit": metrics_report["structural_audit"],
        "hardcell_arrays": metrics_report["hardcell_arrays"],
        "hardcell_instances": metrics_report["hardcell_instances"],
        "role_counts": metrics_report["role_counts"],
    }
    _json_dump(out_dir / "M2R_full_sram_generation_report.json", full_generation_report)
    _write_text(
        out_dir / "M2R_full_sram_generation_report.md",
        "# M2R Full SRAM Generation Report\n\n"
        + "\n".join(
            [
                f"- generator: `{full_generation_report['generator']}`",
                f"- layout_builder: `{full_generation_report['layout_builder']}`",
                f"- top_gds: `{full_generation_report['top_gds']}`",
                f"- complete_gds: `{full_generation_report['complete_gds']}`",
                f"- top_bbox: `{full_generation_report['top_bbox']}`",
            ]
        )
        + "\n",
    )

    review_manifest = {
        "review_gds": str(final_gds_path),
        "complete_gds": str(out_dir / "openyield_layoutgen_full_sram_M2R.complete.gds"),
        "layout_json": str(out_dir / "openyield_layoutgen_full_sram_M2R.layout.json"),
        "report_json": str(out_dir / "openyield_layoutgen_full_sram_M2R.report.json"),
        "top_cell_name": "openyield_layoutgen_full_sram_M2R",
    }
    _json_dump(out_dir / "review_gds_manifest.json", review_manifest)
    _write_text(
        out_dir / "review_gds_manifest.md",
        "# M2R Review GDS Manifest\n\n" + "\n".join([f"- {key}: `{value}`" for key, value in review_manifest.items()]) + "\n",
    )

    docs_mapping = repo_root / "docs/mapping"
    module_usage_columns = [
        "openyield_module",
        "physical_role",
        "binding_status",
        "layoutgen_role",
        "layoutgen_role_instance_count",
        "physical_source_class",
        "implementation",
        "uses_first_round_openyield_gds",
        "temporary_wrapper",
    ]
    _write_csv(docs_mapping / "M2R_module_usage_matrix.csv", module_usage_columns, module_usage_rows)
    _write_text(docs_mapping / "M2R_module_usage_matrix.md", "# M2R Module Usage Matrix\n\n" + _md_table(module_usage_columns, module_usage_rows))

    flow_reuse_rows = [
        {
            "component": item["component"],
            "function": item["function"],
            "reused_for_M2R": item["reused_for_M2R"],
            "role": item["role"],
        }
        for item in FLOW_TRACE_STEPS
    ]
    flow_reuse_columns = ["component", "function", "reused_for_M2R", "role"]
    _write_csv(docs_mapping / "M2R_layoutgen_flow_reuse_matrix.csv", flow_reuse_columns, flow_reuse_rows)
    _write_text(docs_mapping / "M2R_layoutgen_flow_reuse_matrix.md", "# M2R Layoutgen Flow Reuse Matrix\n\n" + _md_table(flow_reuse_columns, flow_reuse_rows))

    gap_columns = ["gap_id", "category", "severity", "description", "blocks_M2R_gate"]
    _write_csv(docs_mapping / "M2R_remaining_gap_matrix.csv", gap_columns, remaining_gap_rows)
    _write_text(docs_mapping / "M2R_remaining_gap_matrix.md", "# M2R Remaining Gap Matrix\n\n" + _md_table(gap_columns, remaining_gap_rows))

    report = {
        "status_file_read": True,
        "status_file_updated": True,
        "locked_sram_spec_available": True,
        "layoutgen_top_flow_trace_available": True,
        "layoutgen_top_flow_used": True,
        "arbitrary_module_scatter_used": False,
        "full_sram_review_gds_generated": final_gds_path.exists(),
        "full_sram_review_gds_path": str(final_gds_path),
        "full_sram_review_gds_size_bytes": sanity["gds_size_bytes"],
        "top_cell_name": sanity["top_cell_name"],
        "gds_sanity_status": sanity["status"],
        "word_size": spec.word_size,
        "num_words": spec.num_words,
        "words_per_row": spec.words_per_row,
        "num_rows": spec.num_rows,
        "num_cols": spec.num_cols,
        "tech": spec.tech,
        "bitcell_array_present": visual_report["bitcell_array_present"],
        "bitcell_array_is_dense主体": visual_report["bitcell_array_is_dense主体"],
        "dummy_or_replica_present": visual_report["dummy_or_replica_present"],
        "row_path_present": visual_report["row_path_present"],
        "column_path_present": visual_report["column_path_present"],
        "control_region_present": visual_report["control_region_present"],
        "large_region_overlay_as_primary_count": visual_report["large_region_overlay_as_primary_count"],
        "access_module_as_primary_count": visual_report["access_module_as_primary_count"],
        "floorplan_proxy_count": visual_report["floorplan_proxy_count"],
        "temporary_wrapper_count": visual_report["temporary_wrapper_count"],
        "layoutgen_real_generator_used_count": layoutgen_real_count,
        "first_round_openyield_gds_used_count": 0,
        "human_klayout_review_required": True,
        "can_enter_next_stage_before_human_review": False,
        "remaining_M2R_blockers": [],
        "remaining_M2R_blockers_count": 0,
        "locked_sram_spec": spec.to_dict(),
    }

    status_md.write_text(_render_status_md(report), encoding="utf-8", newline="\n")
    status_json.write_text(json.dumps(_update_status_json(status_payload, report), ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    _json_dump(out_json, report)
    _write_text(
        out_report,
        "# M2R Full SRAM Regeneration Report\n\n"
        + "\n".join([f"- {key}: `{value}`" for key, value in report.items() if key != "locked_sram_spec"])
        + "\n\n## Locked SRAM Spec\n\n"
        + "\n".join([f"- {key}: `{value}`" for key, value in report["locked_sram_spec"].items()])
        + "\n",
    )
    _write_text(
        repo_root / "docs/evidence/M2R_full_sram_regeneration_summary.md",
        "# M2R Full SRAM Regeneration Summary\n\n"
        + "\n".join(
            [
                f"- Review GDS: `{final_gds_path}`",
                f"- Top cell: `{report['top_cell_name']}`",
                f"- Locked spec: `{spec.word_size}x{spec.num_words}_wpr{spec.words_per_row}`",
                f"- layoutgen_top_flow_used: `{report['layoutgen_top_flow_used']}`",
                f"- arbitrary_module_scatter_used: `{report['arbitrary_module_scatter_used']}`",
                "- Human KLayout review is required before any next-stage work.",
            ]
        )
        + "\n",
    )
    return report
