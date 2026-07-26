from __future__ import annotations

import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from sram_layoutgen.openyield_adapter.M11_openyield_config_variation import run_m11_openyield_config_variation  # noqa: E402


def main() -> int:
    out_dir = REPO_ROOT / "outputs/M11_openyield_config_variation/current_supported_config"
    out_json = REPO_ROOT / "docs/M11_openyield_config_variation_report.json"
    out_report = REPO_ROOT / "docs/M11_openyield_config_variation_report.md"
    report = run_m11_openyield_config_variation(
        repo_root=REPO_ROOT,
        status_md=REPO_ROOT / "PROJECT_LAYOUTGEN_OPENYIELD_STATUS.md",
        status_json=REPO_ROOT / "PROJECT_LAYOUTGEN_OPENYIELD_STATUS.json",
        m10h_report=REPO_ROOT / "docs/M10H_confirm_source_backed_translator_report.json",
        m10_report=REPO_ROOT / "docs/M10_harden_raw_openyield_trace_report.json",
        m10_dir=REPO_ROOT / "outputs/M10_raw_openyield_trace/current_supported_config",
        golden_reference=REPO_ROOT / "outputs/M7_correct_golden_reference/current_supported_config/golden_reference.gds",
        openyield_root=Path("/data1/qujh/work/external/OpenYield"),
        t1_inventory=REPO_ROOT / "outputs/T1_openyield_file_inventory/current_supported_config/openyield_full_file_inventory.csv",
        out_dir=out_dir,
        out_json=out_json,
        out_report=out_report,
    )
    assert report["status_file_read"] is True
    assert report["status_file_updated"] is True
    assert report["m10h_gate_loaded"] is True
    assert report["m10_source_backed_translator_v2_confirmed"] is True
    assert report["config_candidate_count"] >= 20
    assert report["openyield_capacity_config_found"] is True
    assert report["word_size_source_backed"] is False
    assert report["num_words_source_backed"] is False
    assert report["words_per_row_source_backed"] is False
    assert report["num_rows_source_backed"] is True
    assert report["num_cols_source_backed"] is True
    assert report["capacity_config_fallback_used_before_M11"] is True
    assert report["capacity_config_fallback_used_after_M11"] is True
    assert report["fallback_reduced_by_M11"] is True
    assert report["fallback_eliminated_by_M11"] is False
    assert report["variation_support_added"] is True
    assert "8x64_wpr4" in report["supported_variations"]
    assert "4x32_wpr2" in report["supported_variations"]
    assert report["layoutgen_golden_flow_used"] is True
    assert report["reference_file_copied_as_output"] is False
    assert report["gds_generated"] is True
    assert report["gds_sanity_status"] == "GDS_PARSED_SANITY_PASSED"
    assert report["reference_vs_m11_geometry_match"] in {"EXACT_MATCH", "NEAR_MATCH"}
    assert report["can_claim_config_aware_translator_v3"] is True
    assert report["can_claim_full_raw_netlist_compiler"] is False
    assert report["human_klayout_review_required"] is True
    assert report["can_enter_next_stage_before_human_review"] is False
    for name in [
        "openyield_config_derived_sram.gds",
        "openyield_config_derived_sram_clean_review.gds",
        "openyield_config_derived_sram_annotated_debug.gds",
        "golden_reference_copy_for_comparison.gds",
        "M11_OPENYIELD_CONFIG_DERIVED_SRAM_SPEC.json",
        "M11_config_extraction_trace.json",
        "M11_config_candidate_inventory.csv",
        "M11_spec_field_source_matrix.csv",
        "M11_variation_support_report.json",
        "M11_vs_golden_geometry_diff_report.json",
        "M11_remaining_gap_report.json",
        "review_gds_manifest.json",
    ]:
        assert (out_dir / name).exists(), name
    status = json.loads((REPO_ROOT / "PROJECT_LAYOUTGEN_OPENYIELD_STATUS.json").read_text(encoding="utf-8"))
    assert status["current_stage"] == "M11"
    assert status["next_stage"] == "WAIT_HUMAN_KLAYOUT_REVIEW"
    assert status["can_enter_next_stage_without_human_review"] is False
    print("M11_openyield_config_variation_ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
