from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from sram_layoutgen.openyield_adapter.T1_openyield_file_inventory import (  # noqa: E402
    run_t1_openyield_file_inventory,
)


def main() -> int:
    report = run_t1_openyield_file_inventory(
        repo_root=REPO_ROOT,
        status_md=REPO_ROOT / "PROJECT_LAYOUTGEN_OPENYIELD_STATUS.md",
        status_json=REPO_ROOT / "PROJECT_LAYOUTGEN_OPENYIELD_STATUS.json",
        m5_gds=REPO_ROOT / "outputs/M5_openyield_layoutgen_integration/current_supported_config/openyield_layoutgen_integrated_sram.gds",
        openyield_root=Path("/data1/qujh/work/external/OpenYield"),
        out_clean_dir=REPO_ROOT / "outputs/T1_clean_m5_review/current_supported_config",
        out_inventory_dir=REPO_ROOT / "outputs/T1_openyield_file_inventory/current_supported_config",
        out_json=REPO_ROOT / "docs/T1_openyield_full_file_report.json",
        out_report=REPO_ROOT / "docs/T1_openyield_full_file_report.md",
    )
    assert report["status_file_read"] is True
    assert report["status_file_updated"] is True
    assert report["clean_review_gds_generated"] is True
    assert report["clean_gds_sanity_status"] == "GDS_PARSED_SANITY_PASSED"
    assert report["removed_text_count"] > 0
    assert report["physical_shape_preserved"] is True
    assert report["cell_hierarchy_preserved"] is True
    assert report["openyield_root_exists"] is True
    assert report["openyield_file_count_total"] > 0
    assert report["openyield_source_file_count"] > 0
    assert report["openyield_netlist_candidate_file_count"] > 0
    assert report["full_file_inventory_available"] is True
    assert report["source_file_analysis_available"] is True
    assert report["file_tree_available"] is True
    assert report["key_entrypoints_report_available"] is True
    assert report["layoutgen_integration_relevance_matrix_available"] is True
    assert report["next_stage_should_be_netlist_to_layout_translator"] is True
    assert report["human_klayout_review_required"] is True
    assert report["can_enter_next_stage_before_human_review"] is False
    assert (REPO_ROOT / "outputs/T1_clean_m5_review/current_supported_config/openyield_layoutgen_integrated_sram_clean_review.gds").exists()
    assert (REPO_ROOT / "outputs/T1_openyield_file_inventory/current_supported_config/openyield_full_file_inventory.csv").exists()
    assert (REPO_ROOT / "outputs/T1_openyield_file_inventory/current_supported_config/openyield_key_entrypoints_report.json").exists()
    assert "main_sram.py" in report["key_entrypoints"]
    print("T1_openyield_file_inventory_ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
