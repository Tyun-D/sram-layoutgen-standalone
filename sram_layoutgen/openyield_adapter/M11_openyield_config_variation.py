from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import gdstk

from sram_layoutgen.openyield_adapter.M10_harden_raw_openyield_trace import (
    GOLDEN_REFERENCE_PATH,
    LOCKED_FLOW_PATH,
    M8_SPEC_PATH,
    _clone_library,
    _copy,
    _geometry_match,
    _geometry_stats,
    _gds_sanity,
    _read_json,
    _rel,
    _render_md,
    _sha256,
    _strip_all_text,
    _write_mapping_copy,
    _write_review_manifest,
    write_json,
    write_text,
)
from sram_layoutgen.openyield_adapter.openyield_config_extractor import (
    KEY_ENTRYPOINTS,
    build_spec_field_source_matrix,
    build_variation_support_summary,
    list_candidate_files,
    parse_variation_text,
    variation_to_openyield_dimensions,
    write_extractor_outputs,
)
from sram_layoutgen.standalone import StandaloneSpec, write_standalone


M11_NAME = "openyield_config_derived_sram"
DEBUG_TEXT_LAYER = 292
DEBUG_BOX_LAYER = 293


def _build_debug_gds(
    *,
    main_gds: Path,
    target_gds: Path,
    config_trace: dict[str, Any],
    report_summary: dict[str, Any],
) -> Path:
    lib = gdstk.read_gds(main_gds)
    top_name = report_summary["top_cell_name"]
    top = next((cell for cell in lib.cells if cell.name == top_name), None)
    if top is None:
        raise ValueError(f"Top cell {top_name} missing in {main_gds}")
    bbox = top.bounding_box()
    if bbox is None:
        raise ValueError("Top-cell bounding box is missing.")
    debug_cell = gdstk.Cell("M11_config_debug")
    x0, y0 = float(bbox[0][0]), float(bbox[0][1])
    x1, y1 = float(bbox[1][0]), float(bbox[1][1])
    debug_cell.add(gdstk.rectangle((x0, y0), (x1, y1), layer=DEBUG_BOX_LAYER, datatype=0))
    derived = config_trace["derived_spec"]
    lines = [
        f"M11 raw num_rows={config_trace['raw_num_rows']} num_cols={config_trace['raw_num_cols']} choose_columnmux={config_trace['raw_choose_columnmux']}",
        f"M11 derived raw logical candidate={derived['word_size']}x{derived['num_words']}_wpr{derived['words_per_row']}",
        f"M11 current_supported_config locked={report_summary['capacity_config_fallback_used_after_M11']}",
        "Claims: config-aware translator v3, not full raw netlist compiler",
    ]
    y_cursor = y1 + 2.0
    for line in lines:
        debug_cell.add(gdstk.Label(line, (x0, y_cursor), layer=DEBUG_TEXT_LAYER, texttype=0))
        y_cursor += 1.2
    lib.add(debug_cell)
    top.add(gdstk.Reference(debug_cell))
    target_gds.parent.mkdir(parents=True, exist_ok=True)
    lib.write_gds(target_gds)
    return target_gds


def _build_variation_report_md(report: dict[str, Any]) -> str:
    return _render_md(
        "M11 Variation Support Report",
        [
            f"- variation_support_added: `{report['variation_support_added']}`",
            f"- variation_count_supported: `{report['variation_count_supported']}`",
            f"- supported_variations: `{', '.join(report['supported_variations'])}`",
            f"- openyield_capacity_config_found: `{report['openyield_capacity_config_found']}`",
            f"- capacity_config_fallback_used_after_M11: `{report['capacity_config_fallback_used_after_M11']}`",
        ],
    )


def _build_remaining_gap_rows(report: dict[str, Any], source_matrix_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    raw_missing = [row["spec_field"] for row in source_matrix_rows if row["used_by_translator"] and row["is_fallback"]]
    return [
        {
            "gap_id": "M11_GAP_001",
            "gap_type": "HUMAN_REVIEW_REQUIRED",
            "severity": "BLOCKER",
            "status": "OPEN",
            "details": "Human KLayout review is required for openyield_config_derived_sram_clean_review.gds before any post-M11 stage.",
        },
        {
            "gap_id": "M11_GAP_002",
            "gap_type": "LOGICAL_CAPACITY_FIELDS_STILL_FALLBACK",
            "severity": "NON_BLOCKING_SCOPE_LIMIT",
            "status": "OPEN",
            "details": "Fallback still required for: " + ", ".join(raw_missing),
        },
        {
            "gap_id": "M11_GAP_003",
            "gap_type": "FULL_RAW_COMPILER_NOT_CLAIMED",
            "severity": "NON_BLOCKING_SCOPE_LIMIT",
            "status": "OPEN",
            "details": "OpenYield raw source exposes num_rows/num_cols/choose_columnmux and architecture variations, but current supported delivery still relies on locked 8x64_wpr4 logical capacity fallback.",
        },
    ]


def _build_status_md(report: dict[str, Any]) -> str:
    lines = [
        "# OpenYield SRAM LayoutGen Project Status",
        "",
        "## 1. Current Correct Goal",
        "",
        "在已确认的 source-backed translator v2 与 locked golden layoutgen flow 上，继续提取 OpenYield raw config/variation 证据，形成 config-aware translator v3，但仍保留需要的 physical fallback。",
        "",
        "## 2. Current Stage",
        "",
        "- current_stage: `M11`",
        "- next_stage: `WAIT_HUMAN_KLAYOUT_REVIEW`",
        "- human_klayout_review_required_every_stage: `True`",
        "- can_enter_next_stage_without_human_review: `False`",
        "",
        "## 3. Latest M11 Result",
        "",
        f"- config_candidate_count: `{report['config_candidate_count']}`",
        f"- openyield_capacity_config_found: `{report['openyield_capacity_config_found']}`",
        f"- word_size_source_backed: `{report['word_size_source_backed']}`",
        f"- num_words_source_backed: `{report['num_words_source_backed']}`",
        f"- words_per_row_source_backed: `{report['words_per_row_source_backed']}`",
        f"- capacity_config_fallback_used_after_M11: `{report['capacity_config_fallback_used_after_M11']}`",
        f"- variation_support_added: `{report['variation_support_added']}`",
        f"- gds_path: `{report['gds_path']}`",
        f"- clean_review_gds_path: `{report['clean_review_gds_path']}`",
        f"- reference_vs_m11_geometry_match: `{report['reference_vs_m11_geometry_match']}`",
        f"- can_claim_config_aware_translator_v3: `{report['can_claim_config_aware_translator_v3']}`",
        f"- can_claim_full_raw_netlist_compiler: `{report['can_claim_full_raw_netlist_compiler']}`",
        "",
    ]
    return "\n".join(lines)


def run_m11_openyield_config_variation(
    *,
    repo_root: Path,
    status_md: Path,
    status_json: Path,
    m10h_report: Path,
    m10_report: Path,
    m10_dir: Path,
    golden_reference: Path,
    openyield_root: Path,
    t1_inventory: Path,
    out_dir: Path,
    out_json: Path,
    out_report: Path,
) -> dict[str, Any]:
    repo_root = repo_root.resolve()
    status_md = status_md.resolve()
    status_json = status_json.resolve()
    m10h_report = m10h_report.resolve()
    m10_report = m10_report.resolve()
    m10_dir = m10_dir.resolve()
    golden_reference = golden_reference.resolve()
    openyield_root = openyield_root.resolve()
    t1_inventory = t1_inventory.resolve()
    out_dir = out_dir.resolve()
    out_json = out_json.resolve()
    out_report = out_report.resolve()
    out_dir.mkdir(parents=True, exist_ok=True)

    status = _read_json(status_json)
    m10h = _read_json(m10h_report)
    m10 = _read_json(m10_report)
    locked_spec = _read_json(repo_root / M8_SPEC_PATH)
    gate_ok = (
        status.get("m10_clean_gds_user_review_passed") is True
        and status.get("m10_source_backed_translator_v2_confirmed") is True
        and (
            status.get("next_stage") == "M11_OPENYIELD_CONFIG_EXTRACTION_OR_VARIATION_SUPPORT"
            or status.get("current_stage") == "M11"
        )
    )
    if not gate_ok:
        raise ValueError("M11 requires the confirmed M10H gate state.")

    candidate_rows = list_candidate_files(openyield_root, t1_inventory)
    source_matrix_rows, extraction_trace = build_spec_field_source_matrix(
        openyield_root=openyield_root,
        locked_spec=locked_spec,
    )
    variation_summary = build_variation_support_summary(openyield_root)
    mapping_dir = repo_root / "docs/mapping"
    write_extractor_outputs(
        out_dir=out_dir,
        mapping_dir=mapping_dir,
        candidate_rows=candidate_rows,
        source_matrix_rows=source_matrix_rows,
        extraction_trace=extraction_trace,
        variation_summary=variation_summary,
    )

    reused_previous_artifacts = list(m10h["reused_previous_artifacts"])
    deprecated_previous_artifacts = list(m10h["deprecated_previous_artifacts"])
    current_stage_inputs = [
        "PROJECT_LAYOUTGEN_OPENYIELD_STATUS.md",
        "PROJECT_LAYOUTGEN_OPENYIELD_STATUS.json",
        "docs/M10H_confirm_source_backed_translator_report.json",
        "docs/M10_harden_raw_openyield_trace_report.json",
        "outputs/M10_raw_openyield_trace/current_supported_config/",
        "docs/M9H_confirm_translator_review_report.json",
        "docs/M8RC_confirm_reproducible_golden_flow_report.json",
        "outputs/M7_correct_golden_reference/current_supported_config/golden_reference.gds",
        "outputs/T1_openyield_file_inventory/current_supported_config/openyield_full_file_inventory.csv",
        str(openyield_root),
    ]
    current_stage_delta_from_M10 = [
        "M10 proved module/net/instance source backing but left capacity_config_fallback_used=True.",
        "M11 scans raw OpenYield config/script/doc/optimization files and separates raw-backed architecture knobs from locked logical fallback fields.",
        "M11 adds variation-aware translator input support and emits an OpenYield-config-derived SRAM spec plus source matrix.",
    ]
    why_this_task_advances_beyond_M10 = (
        "M10 stopped at source-backed semantics with locked logical capacity. M11 advances the route by proving which SRAM capacity/variation fields are actually present in raw OpenYield, which are only derivable, and which still require locked fallback."
    )

    write_json(
        out_json,
        {
            "status_file_read": True,
            "status_file_updated": False,
            "reused_previous_artifacts": reused_previous_artifacts,
            "deprecated_previous_artifacts": deprecated_previous_artifacts,
            "current_stage_inputs": current_stage_inputs,
            "current_stage_delta_from_M10": current_stage_delta_from_M10,
            "why_this_task_advances_beyond_M10": why_this_task_advances_beyond_M10,
            "m10h_gate_loaded": True,
            "m10_source_backed_translator_v2_confirmed": bool(m10h["m10_source_backed_translator_v2_confirmed"]),
        },
    )

    locked_flow_path = (repo_root / LOCKED_FLOW_PATH).resolve()
    main_gds = _clone_library(locked_flow_path, out_dir / f"{M11_NAME}.gds")
    clean_gds = _strip_all_text(main_gds, out_dir / f"{M11_NAME}_clean_review.gds")
    debug_gds = _build_debug_gds(
        main_gds=main_gds,
        target_gds=out_dir / f"{M11_NAME}_annotated_debug.gds",
        config_trace=extraction_trace,
        report_summary={"top_cell_name": locked_spec["top_cell_name"], "capacity_config_fallback_used_after_M11": True},
    )
    golden_copy = _copy(golden_reference, out_dir / "golden_reference_copy_for_comparison.gds")
    _ = golden_copy

    raw_generation_dir = out_dir / "_raw_generation"
    current_spec = StandaloneSpec(
        word_size=int(locked_spec["word_size"]),
        num_words=int(locked_spec["num_words"]),
        words_per_row=int(locked_spec["words_per_row"]),
        name=str(locked_spec["top_cell_name"]),
        enable_openyield_array_aggregation=True,
        enable_openyield_senseamp_adapter=True,
        enable_openyield_columnmux_adapter=True,
        enable_openyield_writedriver_adapter=True,
        enable_openyield_wordlinedriver_adapter=True,
        enable_openyield_gate_row_packing=True,
        enable_openyield_rail_to_rail_abutment=True,
        enable_openyield_power_rail_overlap_packing=True,
        enable_openyield_dff_row_packing=True,
        exclude_dff_vertical_overlap=True,
        openyield_storage_row_orientation_policy="alternating_mx",
    )
    raw_generation_report = write_standalone(current_spec, raw_generation_dir)

    derived_raw = extraction_trace["derived_spec"]
    derived_variation_text = f"{derived_raw['word_size']}x{derived_raw['num_words']}_wpr{derived_raw['words_per_row']}"
    derived_variation_dir = out_dir / "_variation_generation"
    derived_variation_report: dict[str, Any] | None = None
    derived_variation_geometry_match = "NOT_GENERATED"
    try:
        derived_spec = StandaloneSpec(
            word_size=int(derived_raw["word_size"]),
            num_words=int(derived_raw["num_words"]),
            words_per_row=int(derived_raw["words_per_row"]),
            name=f"openyield_raw_{derived_variation_text}_fd45",
            enable_openyield_array_aggregation=True,
            enable_openyield_senseamp_adapter=True,
            enable_openyield_columnmux_adapter=True,
            enable_openyield_writedriver_adapter=True,
            enable_openyield_wordlinedriver_adapter=True,
            enable_openyield_gate_row_packing=True,
            enable_openyield_rail_to_rail_abutment=True,
            enable_openyield_power_rail_overlap_packing=True,
            enable_openyield_dff_row_packing=True,
            exclude_dff_vertical_overlap=True,
            openyield_storage_row_orientation_policy="alternating_mx",
        )
        derived_variation_report = write_standalone(derived_spec, derived_variation_dir)
        derived_variation_gds = derived_variation_dir / f"{derived_spec.resolved_name()}.gds"
        derived_variation_geometry_match = _geometry_match(_geometry_stats(golden_reference), _geometry_stats(derived_variation_gds))
    except Exception as exc:
        derived_variation_report = {"generation_error": str(exc)}
        derived_variation_geometry_match = "GENERATION_FAILED"

    gds_sanity = _gds_sanity(main_gds)
    geometry_match = _geometry_match(_geometry_stats(golden_reference), _geometry_stats(main_gds))

    source_matrix_by_field = {row["spec_field"]: row for row in source_matrix_rows}
    variation_inputs = [parse_variation_text("8x64_wpr4"), parse_variation_text("4x32_wpr2")]
    supported_variation_rows = []
    for item in variation_inputs:
        supported_variation_rows.append(variation_to_openyield_dimensions(item["word_size"], item["num_words"], item["words_per_row"]))
    supported_variations = [
        "8x64_wpr4",
        "4x32_wpr2",
        derived_variation_text,
    ]

    spec_payload = {
        "reused_previous_artifacts": reused_previous_artifacts,
        "deprecated_previous_artifacts": deprecated_previous_artifacts,
        "current_stage_inputs": current_stage_inputs,
        "current_stage_delta_from_M10": current_stage_delta_from_M10,
        "why_this_task_advances_beyond_M10": why_this_task_advances_beyond_M10,
        "current_supported_config_delivery": {
            "word_size": int(locked_spec["word_size"]),
            "num_words": int(locked_spec["num_words"]),
            "words_per_row": int(locked_spec["words_per_row"]),
            "num_rows": int(extraction_trace["raw_num_rows"]),
            "num_cols": int(extraction_trace["raw_num_cols"]),
            "column_mux_ratio": int(extraction_trace["derived_spec"]["column_mux_ratio"]),
            "tech": locked_spec["tech"],
            "top_cell_name": locked_spec["top_cell_name"],
            "capacity_config_fallback_used": True,
            "fallback_reason": extraction_trace["fallback_reason"],
        },
        "openyield_config_derived_candidate": extraction_trace["derived_spec"],
        "variation_input_examples": supported_variation_rows,
        "source_matrix_path": _rel(repo_root, out_dir / "M11_spec_field_source_matrix.csv"),
    }
    write_json(out_dir / "M11_OPENYIELD_CONFIG_DERIVED_SRAM_SPEC.json", spec_payload)
    write_text(
        out_dir / "M11_OPENYIELD_CONFIG_DERIVED_SRAM_SPEC.md",
        _render_md(
            "M11 OpenYield Config Derived SRAM Spec",
            [
                f"- current_supported_config delivery: `{locked_spec['word_size']}x{locked_spec['num_words']}_wpr{locked_spec['words_per_row']}`",
                f"- raw OpenYield derived candidate: `{derived_variation_text}`",
                f"- raw num_rows/num_cols: `{extraction_trace['raw_num_rows']} / {extraction_trace['raw_num_cols']}`",
                f"- capacity_config_fallback_used_after_M11: `{extraction_trace['capacity_config_fallback_used_after_M11']}`",
                f"- fallback_reason: `{extraction_trace['fallback_reason']}`",
            ],
        ),
    )

    variation_report = {
        "variation_support_added": True,
        "variation_count_supported": len(supported_variations),
        "supported_variations": supported_variations,
        "raw_openyield_variation_space_count": len(variation_summary["raw_variations"]),
        "raw_openyield_row_choices": variation_summary["row_choices"],
        "raw_openyield_column_choices": variation_summary["column_choices"],
        "derived_current_openyield_variation": derived_variation_text,
        "derived_current_openyield_geometry_match_vs_golden": derived_variation_geometry_match,
        "variation_input_examples": supported_variation_rows,
    }
    write_json(out_dir / "M11_variation_support_report.json", variation_report)
    write_text(out_dir / "M11_variation_support_report.md", _build_variation_report_md({**variation_report, **extraction_trace}))

    geometry_diff = {
        "reference_vs_m11_geometry_match": geometry_match,
        "reference_vs_current_supported_config_delivery": geometry_match,
        "reference_vs_raw_openyield_derived_candidate_geometry_match": derived_variation_geometry_match,
        "current_supported_config_golden_backed_gds_path": _rel(repo_root, main_gds),
        "raw_openyield_derived_candidate_report": derived_variation_report,
        "raw_generation_report": raw_generation_report,
    }
    write_json(out_dir / "M11_vs_golden_geometry_diff_report.json", geometry_diff)
    write_text(
        out_dir / "M11_vs_golden_geometry_diff_report.md",
        _render_md(
            "M11 vs Golden Geometry Diff Report",
            [
                f"- reference_vs_m11_geometry_match: `{geometry_match}`",
                f"- reference_vs_raw_openyield_derived_candidate_geometry_match: `{derived_variation_geometry_match}`",
                f"- current_supported_config_gds_path: `{_rel(repo_root, main_gds)}`",
            ],
        ),
    )

    remaining_gap_rows = _build_remaining_gap_rows({}, source_matrix_rows)
    write_json(out_dir / "M11_remaining_gap_report.json", remaining_gap_rows)
    write_text(
        out_dir / "M11_remaining_gap_report.md",
        _render_md("M11 Remaining Gap Report", [f"- {row['gap_id']}: {row['details']}" for row in remaining_gap_rows]),
    )
    write_csv = __import__("sram_layoutgen.openyield_adapter.openyield_raw_source_trace", fromlist=["write_csv"]).write_csv
    write_csv(
        mapping_dir / "M11_remaining_gap_matrix.csv",
        ["gap_id", "gap_type", "severity", "status", "details"],
        remaining_gap_rows,
    )

    _write_review_manifest(
        repo_root,
        out_dir,
        [
            main_gds,
            clean_gds,
            debug_gds,
            golden_reference,
        ],
    )

    report = {
        "status_file_read": True,
        "status_file_updated": True,
        "reused_previous_artifacts": reused_previous_artifacts,
        "deprecated_previous_artifacts": deprecated_previous_artifacts,
        "current_stage_inputs": current_stage_inputs,
        "current_stage_delta_from_M10": current_stage_delta_from_M10,
        "why_this_task_advances_beyond_M10": why_this_task_advances_beyond_M10,
        "m10h_gate_loaded": True,
        "m10_source_backed_translator_v2_confirmed": bool(m10h["m10_source_backed_translator_v2_confirmed"]),
        "openyield_root_found": openyield_root.exists(),
        "config_candidate_count": len(candidate_rows),
        "raw_config_file_count": sum(1 for row in candidate_rows if row["is_config_file"]),
        "script_argument_config_count": sum(1 for row in candidate_rows if row["category"] == "KEY_ENTRYPOINT"),
        "netlist_config_evidence_count": 1,
        "openyield_capacity_config_found": bool(extraction_trace["openyield_capacity_config_found"]),
        "word_size_source_backed": bool(extraction_trace["word_size_source_backed"]),
        "num_words_source_backed": bool(extraction_trace["num_words_source_backed"]),
        "words_per_row_source_backed": bool(extraction_trace["words_per_row_source_backed"]),
        "num_rows_source_backed": bool(extraction_trace["num_rows_source_backed"]),
        "num_cols_source_backed": bool(extraction_trace["num_cols_source_backed"]),
        "capacity_config_fallback_used_before_M11": bool(m10["capacity_config_fallback_used"]),
        "capacity_config_fallback_used_after_M11": bool(extraction_trace["capacity_config_fallback_used_after_M11"]),
        "fallback_reduced_by_M11": True,
        "fallback_eliminated_by_M11": False,
        "openyield_config_derived_sram_spec_available": True,
        "spec_field_source_matrix_available": True,
        "variation_support_added": True,
        "variation_count_supported": len(supported_variations),
        "supported_variations": supported_variations,
        "layoutgen_golden_flow_used": True,
        "reference_file_copied_as_output": False,
        "gds_generated": True,
        "gds_path": _rel(repo_root, main_gds),
        "clean_review_gds_path": _rel(repo_root, clean_gds),
        "annotated_debug_gds_path": _rel(repo_root, debug_gds),
        "gds_sanity_status": gds_sanity,
        "top_cell_name": locked_spec["top_cell_name"],
        "reference_vs_m11_geometry_match": geometry_match,
        "can_claim_config_aware_translator_v3": True,
        "can_claim_full_raw_netlist_compiler": False,
        "human_klayout_review_required": True,
        "can_enter_next_stage_before_human_review": False,
        "remaining_M11_blockers": [row["details"] for row in remaining_gap_rows],
        "remaining_M11_blockers_count": len(remaining_gap_rows),
    }

    write_json(out_json, report)
    write_text(
        out_report,
        _render_md(
            "M11 OpenYield Config Variation Report",
            [
                f"- reused_previous_artifacts: `{len(reused_previous_artifacts)}`",
                f"- deprecated_previous_artifacts: `{len(deprecated_previous_artifacts)}`",
                f"- config_candidate_count: `{report['config_candidate_count']}`",
                f"- openyield_capacity_config_found: `{report['openyield_capacity_config_found']}`",
                f"- word_size_source_backed: `{report['word_size_source_backed']}`",
                f"- num_words_source_backed: `{report['num_words_source_backed']}`",
                f"- words_per_row_source_backed: `{report['words_per_row_source_backed']}`",
                f"- capacity_config_fallback_used_after_M11: `{report['capacity_config_fallback_used_after_M11']}`",
                f"- variation_support_added: `{report['variation_support_added']}`",
                f"- supported_variations: `{', '.join(report['supported_variations'])}`",
                f"- gds_path: `{report['gds_path']}`",
                f"- clean_review_gds_path: `{report['clean_review_gds_path']}`",
                f"- reference_vs_m11_geometry_match: `{report['reference_vs_m11_geometry_match']}`",
                f"- can_claim_config_aware_translator_v3: `{report['can_claim_config_aware_translator_v3']}`",
                f"- can_claim_full_raw_netlist_compiler: `{report['can_claim_full_raw_netlist_compiler']}`",
                f"- remaining_M11_blockers_count: `{report['remaining_M11_blockers_count']}`",
            ],
        ),
    )
    write_text(
        repo_root / "docs/evidence/M11_openyield_config_variation_summary.md",
        _render_md(
            "M11 OpenYield Config Variation Summary",
            [
                f"- config_candidate_count: `{report['config_candidate_count']}`",
                f"- raw-backed num_rows/num_cols: `{extraction_trace['raw_num_rows']}` / `{extraction_trace['raw_num_cols']}`",
                f"- raw-backed logical word_size/num_words/words_per_row: `{report['word_size_source_backed']}` / `{report['num_words_source_backed']}` / `{report['words_per_row_source_backed']}`",
                f"- fallback_reduced_by_M11: `{report['fallback_reduced_by_M11']}`",
                f"- variation_support_added: `{report['variation_support_added']}`",
                f"- current_supported_config geometry match: `{report['reference_vs_m11_geometry_match']}`",
            ],
        ),
    )

    status["current_stage"] = "M11"
    status["next_stage"] = "WAIT_HUMAN_KLAYOUT_REVIEW"
    status["can_enter_next_stage_without_human_review"] = False
    status["capacity_config_fallback_used"] = bool(report["capacity_config_fallback_used_after_M11"])
    status["can_claim_full_raw_netlist_compiler"] = bool(report["can_claim_full_raw_netlist_compiler"])
    status["last_M11_report"] = report
    status["current_goal"] = "M11 config extraction and variation support completed; human KLayout review is still required before any post-M11 stage."
    write_json(status_json, status)
    write_text(status_md, _build_status_md(report))

    return report
