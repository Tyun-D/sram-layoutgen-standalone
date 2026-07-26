from __future__ import annotations

import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from sram_layoutgen.openyield_adapter.M12_ten_asset_audit import run_m12_ten_asset_audit  # noqa: E402


def main() -> int:
    out_dir = REPO_ROOT / "outputs/M12_ten_asset_audit/current_supported_config"
    out_json = REPO_ROOT / "docs/M12_ten_asset_audit_report.json"
    out_report = REPO_ROOT / "docs/M12_ten_asset_audit_report.md"
    report = run_m12_ten_asset_audit(
        repo_root=REPO_ROOT,
        status_md=REPO_ROOT / "PROJECT_LAYOUTGEN_OPENYIELD_STATUS.md",
        status_json=REPO_ROOT / "PROJECT_LAYOUTGEN_OPENYIELD_STATUS.json",
        openyield_root=Path("/data1/qujh/work/external/OpenYield"),
        out_dir=out_dir,
        out_json=out_json,
        out_report=out_report,
    )
    assert report["status_file_read"] is True
    assert report["status_file_updated"] is True
    assert report["ten_required_assets_added_to_goal"] is True
    assert report["ten_required_assets_added_to_progress"] is True
    assert report["workdir_scan_completed"] is True
    assert report["asset_count_total"] == 10
    assert report["asset_complete_count"] >= 1
    assert report["asset_partial_count"] >= 1
    assert report["blocking_asset_count"] >= 1
    assert report["can_claim_source_backed_translator_v2"] is True
    assert report["can_claim_full_raw_openyield_netlist_compiler"] is False
    assert report["can_claim_openyield_module_gds_hardmacro_substitution"] is False
    assert report["can_claim_drc_clean"] is False
    assert report["can_claim_lvs_clean"] is False
    assert report["can_claim_signoff_ready"] is False
    assert report["human_klayout_review_required"] is True
    assert report["can_enter_next_stage_before_human_review"] is False
    assert report["recommended_next_stage"] in {"M11H", "M11A"}
    for name in [
        "M12_ten_required_assets_status.json",
        "M12_ten_required_assets_status.md",
        "M12_ten_required_assets_matrix.csv",
        "M12_ten_required_assets_matrix.md",
        "M12_workdir_asset_evidence_inventory.csv",
        "M12_workdir_asset_evidence_inventory.md",
        "M12_missing_asset_backlog.csv",
        "M12_missing_asset_backlog.md",
        "M12_next_fill_plan.md",
        "M12_reused_previous_artifacts.md",
        "M12_deprecated_artifacts.md",
    ]:
        assert (out_dir / name).exists(), name
    for name in [
        "PROJECT_NETLIST_TO_LAYOUT_GOAL.md",
        "PROJECT_NETLIST_TO_LAYOUT_PROGRESS.md",
        "docs/M12_ten_asset_audit_report.json",
        "docs/M12_ten_asset_audit_report.md",
        "docs/evidence/M12_ten_asset_audit_summary.md",
        "docs/mapping/M12_ten_required_assets_matrix.csv",
        "docs/mapping/M12_workdir_asset_evidence_inventory.csv",
        "docs/mapping/M12_missing_asset_backlog.csv",
        "docs/mapping/M12_next_fill_plan.csv",
    ]:
        assert (REPO_ROOT / name).exists(), name
    status = json.loads((REPO_ROOT / "PROJECT_LAYOUTGEN_OPENYIELD_STATUS.json").read_text(encoding="utf-8"))
    assert status["current_stage"] == "M12"
    assert status["can_enter_next_stage_without_human_review"] is False
    assert len(status["ten_required_assets_for_netlist_to_layout"]) == 10
    assert status["current_claim_boundary"]["can_claim_source_backed_translator_v2"] is True
    print("M12_ten_asset_audit_ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
