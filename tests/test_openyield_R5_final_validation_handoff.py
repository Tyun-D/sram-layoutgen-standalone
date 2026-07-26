from __future__ import annotations

import json
from pathlib import Path


def main() -> None:
    root = Path("/data1/qujh/work/sram_layoutgen_step45_clean")
    out_dir = root / "outputs/openyield_final_validation/current_supported_config"
    report_json = root / "docs/openyield_R5_final_validation_handoff_report.json"
    report_md = root / "docs/openyield_R5_final_validation_handoff_report.md"
    matrix_csv = root / "docs/mapping/openyield_R5_final_validation_matrix.csv"
    matrix_md = root / "docs/mapping/openyield_R5_final_validation_matrix.md"

    required = [
        report_json,
        report_md,
        matrix_csv,
        matrix_md,
        root / "docs/evidence/R5_final_validation_handoff_summary.md",
        out_dir / "final_gds_sanity_report.json",
        out_dir / "final_gds_sanity_report.md",
        out_dir / "final_hierarchy_validation_report.json",
        out_dir / "final_hierarchy_validation_report.md",
        out_dir / "final_topology_validation_report.json",
        out_dir / "final_topology_validation_report.md",
        out_dir / "final_routing_completeness_audit.json",
        out_dir / "final_routing_completeness_audit.md",
        out_dir / "final_power_continuity_audit.json",
        out_dir / "final_power_continuity_audit.md",
        out_dir / "final_pin_export_audit.json",
        out_dir / "final_pin_export_audit.md",
        out_dir / "final_net_mapping_audit.json",
        out_dir / "final_net_mapping_audit.md",
        out_dir / "final_gds_comparison_report.json",
        out_dir / "final_gds_comparison_report.md",
        out_dir / "final_risk_register.json",
        out_dir / "final_risk_register.md",
        out_dir / "final_project_summary.json",
        out_dir / "final_project_summary.md",
        out_dir / "final_one_page_summary.md",
        out_dir / "final_delivery_checklist.json",
        out_dir / "final_delivery_checklist.md",
    ]
    for path in required:
        assert path.exists(), f"missing required artifact: {path}"

    report = json.loads(report_json.read_text(encoding="utf-8"))
    assert report["final_gds_sanity_status"] == "PASSED"
    assert report["required_modules_missing_from_recursive_gds"] == []
    assert report["topology_validation_status"] == "PASSED"
    assert report["routing_completeness_audit_status"] == "PASSED"
    assert report["power_continuity_audit_status"] == "PASSED"
    assert report["pin_export_audit_status"] == "PASSED"
    assert report["net_mapping_audit_status"] == "PASSED"
    assert report["remaining_R5_blockers_count"] == 0
    assert report["can_claim_openyield_oriented_structure_complete_sram_gds_prototype_now"] is True
    assert report["can_claim_routing_power_pin_mapping_evidence_now"] is True
    assert report["can_claim_final_handoff_completed_now"] is True
    assert report["can_claim_detailed_routing_complete_now"] is False
    assert report["can_claim_power_network_signoff_now"] is False
    assert report["can_claim_drc_clean_now"] is False
    assert report["can_claim_lvs_clean_now"] is False
    assert report["can_claim_timing_closure_now"] is False
    assert report["can_claim_signoff_ready_now"] is False

    print("OpenYield R5 final validation handoff tests passed.")


if __name__ == "__main__":
    main()
