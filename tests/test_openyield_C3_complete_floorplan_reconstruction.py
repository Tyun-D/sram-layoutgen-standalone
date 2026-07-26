from __future__ import annotations

import json
from pathlib import Path


def main() -> None:
    root = Path("/data1/qujh/work/sram_layoutgen_step45_clean")
    out_dir = root / "outputs/openyield_complete_floorplan/current_supported_config"
    report_json = root / "docs/openyield_C3_complete_floorplan_reconstruction_report.json"
    report_md = root / "docs/openyield_C3_complete_floorplan_reconstruction_report.md"
    placement_csv = root / "docs/mapping/openyield_C3_complete_placement_matrix.csv"
    placement_md = root / "docs/mapping/openyield_C3_complete_placement_matrix.md"

    required = [
        report_json,
        report_md,
        placement_csv,
        placement_md,
        root / "docs/evidence/C3_complete_floorplan_reconstruction_summary.md",
        out_dir / "openyield_complete_floorplan_sram.gds",
        out_dir / "complete_sram_floorplan.json",
        out_dir / "complete_sram_floorplan.md",
        out_dir / "complete_sram_placement.json",
        out_dir / "complete_sram_placement.csv",
        out_dir / "complete_sram_placement.md",
        out_dir / "complete_sram_region_plan.json",
        out_dir / "complete_sram_region_plan.md",
        out_dir / "complete_array_region_report.json",
        out_dir / "complete_array_region_report.md",
        out_dir / "complete_row_path_region_report.json",
        out_dir / "complete_row_path_region_report.md",
        out_dir / "complete_column_path_region_report.json",
        out_dir / "complete_column_path_region_report.md",
        out_dir / "complete_control_region_report.json",
        out_dir / "complete_control_region_report.md",
        out_dir / "complete_routing_channel_plan.json",
        out_dir / "complete_routing_channel_plan.md",
        out_dir / "complete_power_strap_region_plan.json",
        out_dir / "complete_power_strap_region_plan.md",
        out_dir / "pitch_exact_alignment_report.json",
        out_dir / "pitch_exact_alignment_report.md",
        out_dir / "layoutgen_reference_reuse_decision.json",
        out_dir / "layoutgen_reference_reuse_decision.md",
        out_dir / "complete_floorplan_gds_sanity_report.json",
        out_dir / "complete_floorplan_generator_manifest.json",
        out_dir / "complete_floorplan_generation_report.json",
        out_dir / "complete_floorplan_generation_report.md",
    ]
    for path in required:
        assert path.exists(), f"missing required artifact: {path}"

    report = json.loads(report_json.read_text(encoding="utf-8"))
    assert report["floorplan_gds_generated"] is True
    assert report["floorplan_gds_sanity_status"] == "PASSED"
    assert report["top_cell_name"] == "openyield_complete_floorplan_sram"
    assert report["required_module_count"] == 20
    assert report["required_module_placed_count"] == 20
    assert report["required_modules_missing"] == []
    assert report["array_region_exists"] is True
    assert report["row_path_region_exists"] is True
    assert report["column_path_region_exists"] is True
    assert report["control_region_exists"] is True
    assert report["routing_channel_plan_exists"] is True
    assert report["power_strap_region_plan_exists"] is True
    assert report["row_alignment_blocked_count"] == 0
    assert report["column_alignment_blocked_count"] == 0
    assert report["control_access_blocked_count"] == 0
    assert report["power_access_blocked_count"] == 0
    assert report["placeholder_overlay_removed_or_isolated"] is True
    assert report["layoutgen_reference_used"] is True
    assert report["remaining_C3_blockers_count"] == 0
    assert report["can_claim_C3_complete_floorplan_reconstructed_now"] is True
    assert report["can_claim_complete_gds_now"] is False
    assert report["can_enter_C4_signal_routing_geometry"] is True
    print("OpenYield C3 complete floorplan reconstruction tests passed.")


if __name__ == "__main__":
    main()
