from __future__ import annotations

import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from sram_layoutgen.openyield_adapter.M11A_module_gds_qualification import run_m11a_module_gds_qualification  # noqa: E402


def main() -> int:
    out_dir = REPO_ROOT / "outputs/M11A_module_gds_qualification/current_supported_config"
    out_json = REPO_ROOT / "docs/M11A_module_gds_qualification_report.json"
    out_report = REPO_ROOT / "docs/M11A_module_gds_qualification_report.md"
    report = run_m11a_module_gds_qualification(
        repo_root=REPO_ROOT,
        status_md=REPO_ROOT / "PROJECT_LAYOUTGEN_OPENYIELD_STATUS.md",
        status_json=REPO_ROOT / "PROJECT_LAYOUTGEN_OPENYIELD_STATUS.json",
        goal_md=REPO_ROOT / "PROJECT_NETLIST_TO_LAYOUT_GOAL.md",
        progress_md=REPO_ROOT / "PROJECT_NETLIST_TO_LAYOUT_PROGRESS.md",
        module_gds_dir=REPO_ROOT / "outputs/openyield_module_gds",
        golden_reference=REPO_ROOT / "outputs/M7_correct_golden_reference/current_supported_config/golden_reference.gds",
        m10_module_trace=REPO_ROOT / "docs/mapping/M10_source_backed_module_trace.csv",
        m10_net_trace=REPO_ROOT / "docs/mapping/M10_source_backed_net_trace.csv",
        m9_module_binding=REPO_ROOT / "outputs/M9_openyield_netlist_translator/current_supported_config/M9_module_binding_matrix.csv",
        m9_net_binding=REPO_ROOT / "outputs/M9_openyield_netlist_translator/current_supported_config/M9_net_binding_matrix.csv",
        m12_assets=REPO_ROOT / "docs/mapping/M12_ten_required_assets_matrix.csv",
        m12_backlog=REPO_ROOT / "docs/mapping/M12_missing_asset_backlog.csv",
        out_dir=out_dir,
        out_json=out_json,
        out_report=out_report,
    )
    assert report["status_file_read"] is True
    assert report["status_file_updated"] is True
    assert report["progress_file_updated"] is True
    assert report["module_gds_dir_found"] is True
    assert report["module_gds_count"] == 20
    assert report["expected_openyield_module_count"] == 20
    assert report["all_expected_modules_have_gds"] is True
    assert report["bbox_metadata_count"] == 20
    assert report["pin_metadata_count"] == 20
    assert report["rail_metadata_count"] == 20
    assert report["generation_report_count"] == 20
    assert report["direct_hardmacro_replace_count"] == 4
    assert report["constraint_extraction_only_count"] == 4
    assert report["semantic_reference_only_count"] == 12
    assert report["rejected_count"] == 0
    assert report["first_substitution_candidates"] == ["column_mux", "sense_amp", "wordline_driver", "write_driver"] or report["first_substitution_candidates"] == ["column_mux", "sense_amp", "write_driver", "wordline_driver"]
    assert report["safe_to_attempt_selective_substitution"] is True
    assert report["must_run_M11B_before_substitution"] is True
    assert report["review_gds_generated"] is True
    assert report["review_gds_sanity_status"] == "GDS_PARSED_SANITY_PASSED"
    assert report["can_claim_openyield_module_gds_hardmacro_substitution"] is False
    assert report["human_klayout_review_required"] is True
    assert report["can_enter_next_stage_before_human_review"] is False
    for name in [
        "M11A_module_gds_inventory.csv",
        "M11A_module_gds_inventory.md",
        "M11A_module_vs_golden_leaf_comparison.csv",
        "M11A_module_vs_golden_leaf_comparison.md",
        "M11A_hardmacro_substitution_decision.csv",
        "M11A_hardmacro_substitution_decision.md",
        "M11A_pin_bbox_rail_metadata.csv",
        "M11A_pin_bbox_rail_metadata.json",
        "M11A_next_substitution_plan.md",
        "M11A_review_gds_manifest.json",
        "M11A_review_gds_manifest.md",
        "module_gds_qualification_review.gds",
        "module_gds_qualification_clean_review.gds",
        "module_gds_qualification_annotated_debug.gds",
    ]:
        assert (out_dir / name).exists(), name
    for name in [
        "docs/M11A_module_gds_qualification_report.json",
        "docs/M11A_module_gds_qualification_report.md",
        "docs/evidence/M11A_module_gds_qualification_summary.md",
        "docs/mapping/M11A_module_gds_inventory.csv",
        "docs/mapping/M11A_module_vs_golden_leaf_comparison.csv",
        "docs/mapping/M11A_hardmacro_substitution_decision.csv",
        "docs/mapping/M11A_pin_bbox_rail_metadata.csv",
        "docs/mapping/M11A_next_substitution_plan.csv",
    ]:
        assert (REPO_ROOT / name).exists(), name
    status = json.loads((REPO_ROOT / "PROJECT_LAYOUTGEN_OPENYIELD_STATUS.json").read_text(encoding="utf-8"))
    assert status["current_stage"] == "M11A"
    assert status["next_stage_allowed"] == "M11B_PIN_BBOX_RAIL_METADATA_EXTRACTION"
    assert status["can_claim_openyield_module_gds_hardmacro_substitution"] is False
    print("M11A_module_gds_qualification_ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
