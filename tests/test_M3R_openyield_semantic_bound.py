from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from sram_layoutgen.openyield_adapter.M3R_openyield_semantic_bound import run_m3r_openyield_semantic_bound  # noqa: E402


def main() -> int:
    out_dir = REPO_ROOT / "outputs/M3R_openyield_semantic_bound/current_supported_config"
    out_json = REPO_ROOT / "docs/M3R_openyield_semantic_bound_report.json"
    out_report = REPO_ROOT / "docs/M3R_openyield_semantic_bound_report.md"
    report = run_m3r_openyield_semantic_bound(
        repo_root=REPO_ROOT,
        status_md=REPO_ROOT / "PROJECT_LAYOUTGEN_OPENYIELD_STATUS.md",
        status_json=REPO_ROOT / "PROJECT_LAYOUTGEN_OPENYIELD_STATUS.json",
        m2r_dir=REPO_ROOT / "outputs/M2R_full_sram_regen/current_supported_config",
        m1_binding=REPO_ROOT / "docs/mapping/M1_openyield_to_layoutgen_binding.csv",
        m1_net_binding=REPO_ROOT / "docs/mapping/M1_openyield_net_to_layoutgen_pin_binding.csv",
        openyield_module_gds_dir=REPO_ROOT / "outputs/openyield_module_gds",
        openyield_intent_dir=REPO_ROOT / "outputs/openyield_layout_intent/current_supported_config",
        out_dir=out_dir,
        out_json=out_json,
        out_report=out_report,
    )
    assert report["semantic_bound_gds_generated"] is True
    assert report["top_cell_name"] == "openyield_semantic_bound_full_sram"
    assert report["gds_sanity_status"] == "GDS_PARSED_SANITY_PASSED"
    assert report["m2r_physical_backbone_preserved"] is True
    assert report["layoutgen_top_flow_preserved"] is True
    assert report["arbitrary_module_scatter_used"] is False
    assert report["bitcell_array_is_dense主体"] is True
    assert report["openyield_required_module_count"] == 20
    assert report["openyield_modules_bound_count"] == 20
    assert report["openyield_modules_unbound_count"] == 0
    assert report["openyield_net_binding_count"] == 34
    assert report["openyield_net_bound_count"] == 34
    assert report["openyield_net_unbound_count"] == 0
    assert report["first_round_openyield_gds_evaluated_count"] == 20
    assert report["first_round_openyield_gds_reused_count"] == 0
    assert report["first_round_openyield_gds_rejected_count"] == 20
    assert report["semantic_wrapper_or_label_count"] > 0
    assert report["access_module_as_primary_count"] == 0
    assert report["floorplan_proxy_count"] == 0
    assert report["temporary_empty_wrapper_count"] == 0
    assert report["remaining_M3R_blockers_count"] == 0
    assert Path(report["semantic_bound_gds_path"]).exists()
    print("M3R_openyield_semantic_bound_ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
