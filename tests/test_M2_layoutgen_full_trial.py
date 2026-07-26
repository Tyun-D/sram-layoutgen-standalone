from __future__ import annotations

import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from sram_layoutgen.openyield_adapter.M2_layoutgen_full_trial import run_m2_full_trial  # noqa: E402


def main() -> int:
    out_dir = REPO_ROOT / "outputs/test_M2_layoutgen_full_trial/current_supported_config"
    out_json = REPO_ROOT / "docs/test_M2_layoutgen_full_trial_report.json"
    out_report = REPO_ROOT / "docs/test_M2_layoutgen_full_trial_report.md"
    report = run_m2_full_trial(
        repo_root=REPO_ROOT,
        status_md=REPO_ROOT / "PROJECT_LAYOUTGEN_OPENYIELD_STATUS.md",
        status_json=REPO_ROOT / "PROJECT_LAYOUTGEN_OPENYIELD_STATUS.json",
        m1_binding=REPO_ROOT / "docs/mapping/M1_openyield_to_layoutgen_binding.csv",
        m1_net_binding=REPO_ROOT / "docs/mapping/M1_openyield_net_to_layoutgen_pin_binding.csv",
        openyield_module_gds_dir=REPO_ROOT / "outputs/openyield_module_gds",
        layoutgen_reference_gds=REPO_ROOT / "outputs/layout_prototype/baseline_legacy/sram_8x64_wpr4_fd45.complete.gds",
        out_dir=out_dir,
        out_json=out_json,
        out_report=out_report,
    )
    assert report["full_sram_review_gds_generated"] is True
    assert report["top_cell_name"] == "openyield_layoutgen_full_trial_sram"
    assert report["gds_sanity_status"] == "GDS_PARSED_SANITY_PASSED"
    assert report["bitcell_array_present"] is True
    assert report["row_path_present"] is True
    assert report["column_path_present"] is True
    assert report["access_module_as_primary_count"] == 0
    assert report["floorplan_proxy_count"] == 0
    assert report["remaining_M2_blockers_count"] == 0
    assert report["temporary_wrapper_count"] > 0
    assert Path(report["full_sram_review_gds_path"]).exists()
    usage = (REPO_ROOT / "docs/mapping/M2_openyield_module_to_real_gds_usage.csv").read_text(encoding="utf-8")
    assert "TEMP_WRAPPER_FOR_M2_REVIEW" not in usage
    manifest = json.loads((out_dir / "review_gds_manifest.json").read_text(encoding="utf-8"))
    assert manifest["top_cell_name"] == "openyield_layoutgen_full_trial_sram"
    print("M2_layoutgen_full_trial_ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
