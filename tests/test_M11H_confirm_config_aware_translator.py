from __future__ import annotations

import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from sram_layoutgen.openyield_adapter.M11H_confirm_config_aware_translator import (  # noqa: E402
    run_m11h_confirm_config_aware_translator,
)


def main() -> int:
    out_dir = REPO_ROOT / "outputs/M11H_confirm_config_aware_translator/current_supported_config"
    out_json = REPO_ROOT / "docs/M11H_confirm_config_aware_translator_report.json"
    out_report = REPO_ROOT / "docs/M11H_confirm_config_aware_translator_report.md"
    report = run_m11h_confirm_config_aware_translator(
        repo_root=REPO_ROOT,
        status_md=REPO_ROOT / "PROJECT_LAYOUTGEN_OPENYIELD_STATUS.md",
        status_json=REPO_ROOT / "PROJECT_LAYOUTGEN_OPENYIELD_STATUS.json",
        goal_md=REPO_ROOT / "PROJECT_NETLIST_TO_LAYOUT_GOAL.md",
        progress_md=REPO_ROOT / "PROJECT_NETLIST_TO_LAYOUT_PROGRESS.md",
        m11_report=REPO_ROOT / "docs/M11_openyield_config_variation_report.json",
        m12_report=REPO_ROOT / "docs/M12_ten_asset_audit_report.json",
        m12_assets=REPO_ROOT / "docs/mapping/M12_ten_required_assets_matrix.csv",
        m12_backlog=REPO_ROOT / "docs/mapping/M12_missing_asset_backlog.csv",
        m11_dir=REPO_ROOT / "outputs/M11_openyield_config_variation/current_supported_config",
        out_dir=out_dir,
        out_json=out_json,
        out_report=out_report,
    )
    assert report["status_file_read"] is True
    assert report["status_file_updated"] is True
    assert report["goal_file_updated"] is True
    assert report["progress_file_updated"] is True
    assert report["m11_clean_gds_user_review_passed"] is True
    assert report["m11_config_aware_translator_v3_confirmed"] is True
    assert report["can_claim_config_aware_translator_v3"] is True
    assert report["can_claim_full_raw_netlist_compiler"] is False
    assert report["capacity_config_fallback_used_after_M11"] is True
    assert report["fallback_eliminated_by_M11"] is False
    assert report["variation_support_added"] is True
    assert report["reference_vs_m11_geometry_match"] == "EXACT_MATCH"
    assert report["remaining_M11_blockers_before_count"] == 3
    assert report["remaining_M11_blockers_after_count"] == 0
    assert report["m12_recommended_next_stage_before"] == "M11H"
    assert report["m12_recommended_next_stage_after"] == "M11A_MODULE_GDS_QUALIFICATION"
    assert report["next_stage_allowed"] == "M11A_MODULE_GDS_QUALIFICATION"
    assert report["can_enter_M11A_after_this_gate"] is True
    assert report["can_enter_next_stage_without_human_review"] is False
    for name in [
        "M11H_gate_clearance_report.json",
        "M11H_gate_clearance_report.md",
        "review_gds_manifest.json",
        "review_gds_manifest.md",
    ]:
        assert (out_dir / name).exists(), name
    for name in [
        "docs/M11H_confirm_config_aware_translator_report.json",
        "docs/M11H_confirm_config_aware_translator_report.md",
        "docs/evidence/M11H_confirm_config_aware_translator_summary.md",
    ]:
        assert (REPO_ROOT / name).exists(), name
    status = json.loads((REPO_ROOT / "PROJECT_LAYOUTGEN_OPENYIELD_STATUS.json").read_text(encoding="utf-8"))
    assert status["m11_clean_gds_user_review_passed"] is True
    assert status["m11_config_aware_translator_v3_confirmed"] is True
    assert status["can_claim_config_aware_translator_v3"] is True
    assert status["next_stage_allowed"] == "M11A_MODULE_GDS_QUALIFICATION"
    print("M11H_confirm_config_aware_translator_ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
