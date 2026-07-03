from __future__ import annotations

import json
from pathlib import Path


def main() -> None:
    root = Path("/data1/qujh/work/sram_layoutgen_step45_clean")
    out_dir = root / "outputs/openyield_complete_gds_rule_extraction/current_supported_config"
    report_json = root / "docs/openyield_C1_sram_physical_rule_extraction_report.json"
    report_md = root / "docs/openyield_C1_sram_physical_rule_extraction_report.md"
    matrix_csv = root / "docs/mapping/openyield_C1_physical_rule_matrix.csv"
    matrix_md = root / "docs/mapping/openyield_C1_physical_rule_matrix.md"

    required = [
        report_json,
        report_md,
        matrix_csv,
        matrix_md,
        root / "docs/evidence/C1_sram_physical_rule_extraction_summary.md",
        out_dir / "sram_baseline_physical_rulebook.json",
        out_dir / "sram_baseline_physical_rulebook.md",
        out_dir / "openram_source_rule_inventory.csv",
        out_dir / "openram_source_rule_inventory.md",
        out_dir / "reference_gds_physical_observation.json",
        out_dir / "reference_gds_physical_observation.md",
        out_dir / "array_physical_rules.json",
        out_dir / "array_physical_rules.md",
        out_dir / "row_path_physical_rules.json",
        out_dir / "row_path_physical_rules.md",
        out_dir / "column_path_physical_rules.json",
        out_dir / "column_path_physical_rules.md",
        out_dir / "control_io_physical_rules.json",
        out_dir / "control_io_physical_rules.md",
        out_dir / "power_physical_rules.json",
        out_dir / "power_physical_rules.md",
        out_dir / "pin_label_layer_rules.json",
        out_dir / "pin_label_layer_rules.md",
        out_dir / "openram_vs_openyield_layout_gap_matrix.csv",
        out_dir / "openram_vs_openyield_layout_gap_matrix.md",
        out_dir / "complete_gds_physical_requirements.json",
        out_dir / "complete_gds_physical_requirements.md",
        out_dir / "c0_blocker_to_c2_c6_fix_plan.csv",
        out_dir / "c0_blocker_to_c2_c6_fix_plan.md",
    ]
    for path in required:
        assert path.exists(), f"missing required artifact: {path}"

    report = json.loads(report_json.read_text(encoding="utf-8"))
    c0_report = json.loads((root / "docs/openyield_C0_complete_gds_gap_audit_report.json").read_text(encoding="utf-8"))
    assert report["C1_physical_rule_extraction_available"] is True
    assert report["openram_source_rule_count"] >= 30
    assert report["array_rule_count"] > 0
    assert report["row_path_rule_count"] > 0
    assert report["column_path_rule_count"] > 0
    assert report["control_io_rule_count"] > 0
    assert report["power_rule_count"] > 0
    assert report["pin_label_rule_count"] > 0
    assert report["c0_blocker_fix_plan_count"] == c0_report["complete_gds_blocker_count"]
    assert report["remaining_C1_blockers_count"] == 0
    assert report["can_claim_C1_physical_rules_extracted_now"] is True
    assert report["can_claim_complete_gds_now"] is False
    assert report["can_enter_C2_pin_geometry_access_repair"] is True

    print("OpenYield C1 SRAM physical rule extraction tests passed.")


if __name__ == "__main__":
    main()
