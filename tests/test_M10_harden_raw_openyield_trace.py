from __future__ import annotations

import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from sram_layoutgen.openyield_adapter.M10_harden_raw_openyield_trace import run_m10_harden_raw_openyield_trace  # noqa: E402


def main() -> int:
    out_dir = REPO_ROOT / "outputs/M10_raw_openyield_trace/current_supported_config"
    out_json = REPO_ROOT / "docs/M10_harden_raw_openyield_trace_report.json"
    out_report = REPO_ROOT / "docs/M10_harden_raw_openyield_trace_report.md"
    report = run_m10_harden_raw_openyield_trace(
        repo_root=REPO_ROOT,
        status_md=REPO_ROOT / "PROJECT_LAYOUTGEN_OPENYIELD_STATUS.md",
        status_json=REPO_ROOT / "PROJECT_LAYOUTGEN_OPENYIELD_STATUS.json",
        m9h_report=REPO_ROOT / "docs/M9H_confirm_translator_review_report.json",
        m9_report=REPO_ROOT / "docs/M9_openyield_netlist_translator_report.json",
        m9_dir=REPO_ROOT / "outputs/M9_openyield_netlist_translator/current_supported_config",
        golden_reference=REPO_ROOT / "outputs/M7_correct_golden_reference/current_supported_config/golden_reference.gds",
        openyield_root=Path("/data1/qujh/work/external/OpenYield"),
        openyield_intent_dir=REPO_ROOT / "outputs/openyield_layout_intent/current_supported_config",
        t1_inventory=REPO_ROOT / "outputs/T1_openyield_file_inventory/current_supported_config/openyield_full_file_inventory.csv",
        out_dir=out_dir,
        out_json=out_json,
        out_report=out_report,
    )
    assert report["status_file_read"] is True
    assert report["status_file_updated"] is True
    assert report["m9h_gate_loaded"] is True
    assert report["openyield_root_found"] is True
    assert report["raw_source_trace_generated"] is True
    assert report["module_source_trace_available"] is True
    assert report["net_source_trace_available"] is True
    assert report["instance_source_trace_available"] is True
    assert report["config_source_trace_available"] is True
    assert report["openyield_module_count"] == 20
    assert report["source_backed_module_count"] >= 12
    assert report["unknown_module_source_count"] == 0
    assert report["openyield_net_count"] == 34
    assert report["source_backed_net_count"] == 34
    assert report["unknown_net_source_count"] == 0
    assert report["capacity_config_fallback_used"] is True
    assert report["generated_from_raw_openyield_source_trace"] is True
    assert report["full_raw_openyield_netlist_compiler"] is False
    assert report["layoutgen_golden_flow_used"] is True
    assert report["reference_file_copied_as_output"] is False
    assert report["gds_sanity_status"] == "GDS_PARSED_SANITY_PASSED"
    assert report["reference_vs_m10_geometry_match"] in {"EXACT_MATCH", "NEAR_MATCH"}
    assert report["can_claim_source_backed_translator_v2"] is True
    assert report["can_claim_full_raw_netlist_compiler"] is False
    assert report["human_klayout_review_required"] is True
    assert report["can_enter_next_stage_before_human_review"] is False
    for name in [
        "openyield_source_backed_translated_sram.gds",
        "openyield_source_backed_translated_sram_clean_review.gds",
        "openyield_source_backed_translated_sram_annotated_debug.gds",
        "M10_OPENYIELD_SOURCE_BACKED_SRAM_SPEC.json",
        "M10_raw_openyield_source_trace.json",
        "M10_source_backed_module_trace.csv",
        "M10_source_backed_net_trace.csv",
        "M10_source_backed_instance_trace.csv",
        "M10_config_source_trace.json",
        "M10_translator_generation_report.json",
        "M10_vs_golden_geometry_diff_report.json",
        "M10_remaining_gap_report.json",
        "review_gds_manifest.json",
    ]:
        assert (out_dir / name).exists(), name
    status = json.loads((REPO_ROOT / "PROJECT_LAYOUTGEN_OPENYIELD_STATUS.json").read_text(encoding="utf-8"))
    assert status["current_stage"] == "M10"
    assert status["next_stage"] == "WAIT_HUMAN_KLAYOUT_REVIEW"
    assert status["can_enter_next_stage_without_human_review"] is False
    print("M10_harden_raw_openyield_trace_ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
