from __future__ import annotations

import json
from pathlib import Path


def main() -> None:
    root = Path("/data1/qujh/work/sram_layoutgen_step45_clean")
    out_dir = root / "outputs/openyield_structure_complete_gds/current_supported_config"
    report_json = root / "docs/openyield_R3_structure_complete_gds_report.json"
    report_md = root / "docs/openyield_R3_structure_complete_gds_report.md"
    matrix_csv = root / "docs/mapping/openyield_R3_structure_complete_placement_matrix.csv"
    matrix_md = root / "docs/mapping/openyield_R3_structure_complete_placement_matrix.md"

    required = [
        report_json,
        report_md,
        matrix_csv,
        matrix_md,
        root / "docs/evidence/R3_structure_complete_gds_gap_summary.md",
        out_dir / "openyield_structure_complete_sram.gds",
        out_dir / "structure_complete_config.json",
        out_dir / "sram_physical_floorplan.json",
        out_dir / "sram_region_plan.json",
        out_dir / "sram_structure_placement.json",
        out_dir / "pitch_alignment_report.json",
        out_dir / "structure_gds_sanity_report.json",
        out_dir / "structure_generator_manifest.json",
        out_dir / "structure_generation_report.json",
        out_dir / "structure_generation_report.md",
        out_dir / "array_region_report.json",
        out_dir / "row_periphery_report.json",
        out_dir / "column_periphery_report.json",
        out_dir / "control_periphery_report.json",
    ]
    for path in required:
        assert path.exists(), f"missing required artifact: {path}"

    report = json.loads(report_json.read_text(encoding="utf-8"))
    assert report["top_cell_name"] == "openyield_structure_complete_sram"
    assert report["structure_gds_sanity_status"] == "PASSED"
    assert report["required_module_count"] == 20
    assert report["required_module_placed_count"] == 20
    assert report["required_modules_missing"] == []
    assert report["array_region_exists"] is True
    assert report["row_periphery_region_exists"] is True
    assert report["column_periphery_region_exists"] is True
    assert report["control_periphery_region_exists"] is True
    assert report["blocked_alignment_count"] == 0
    assert report["remaining_R3_blockers_count"] == 0
    assert report["can_claim_R3_structure_complete_sram_gds_prototype_now"] is True
    assert report["can_enter_R4_routing_power_pin_mapping"] is True
    assert report["can_claim_detailed_routing_complete_now"] is False
    assert report["can_claim_power_network_signoff_now"] is False
    assert report["can_claim_drc_clean_now"] is False
    assert report["can_claim_lvs_clean_now"] is False
    assert report["can_claim_timing_closure_now"] is False
    assert report["can_claim_signoff_ready_now"] is False

    sanity = json.loads((out_dir / "structure_gds_sanity_report.json").read_text(encoding="utf-8"))
    assert sanity["top_cell_name"] == "openyield_structure_complete_sram"
    assert sanity["structure_gds_sanity_status"] == "PASSED"
    assert len(sanity["required_modules_in_placement"]) == 20

    print("OpenYield R3 structure-complete GDS tests passed.")


if __name__ == "__main__":
    main()
