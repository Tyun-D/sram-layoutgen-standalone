from __future__ import annotations

import json
from pathlib import Path


def main() -> None:
    root = Path("/data1/qujh/work/sram_layoutgen_step45_clean")
    out_dir = root / "outputs/openyield_pin_access_repair/current_supported_config"
    report_json = root / "docs/openyield_C2_pin_geometry_access_repair_report.json"
    report_md = root / "docs/openyield_C2_pin_geometry_access_repair_report.md"
    matrix_csv = root / "docs/mapping/openyield_C2_pin_access_matrix.csv"
    matrix_md = root / "docs/mapping/openyield_C2_pin_access_matrix.md"

    required = [
        report_json,
        report_md,
        matrix_csv,
        matrix_md,
        root / "docs/evidence/C2_pin_geometry_access_repair_summary.md",
        out_dir / "normalized_pin_access_database.json",
        out_dir / "normalized_pin_access_database.csv",
        out_dir / "normalized_pin_access_database.md",
        out_dir / "module_pin_geometry_report.json",
        out_dir / "module_pin_geometry_report.md",
        out_dir / "pin_access_gap_summary.json",
        out_dir / "pin_access_gap_summary.md",
        out_dir / "pin_access_repair_plan.csv",
        out_dir / "pin_access_repair_plan.md",
        out_dir / "module_access_view_manifest.json",
        out_dir / "module_access_view_manifest.md",
        out_dir / "critical_net_pin_access_report.json",
        out_dir / "critical_net_pin_access_report.md",
        out_dir / "power_pin_access_report.json",
        out_dir / "power_pin_access_report.md",
        out_dir / "top_io_pin_access_report.json",
        out_dir / "top_io_pin_access_report.md",
        out_dir / "c2_blocker_resolution_matrix.csv",
        out_dir / "c2_blocker_resolution_matrix.md",
        out_dir / "layoutgen_reference_pin_access_audit.json",
        out_dir / "layoutgen_reference_pin_access_audit.md",
    ]
    for path in required:
        assert path.exists(), f"missing required artifact: {path}"

    report = json.loads(report_json.read_text(encoding="utf-8"))
    assert report["C2_pin_geometry_access_repair_available"] is True
    assert report["required_module_count"] == 20
    assert report["module_with_pin_access_count"] == 20
    assert report["module_access_view_count"] == 20
    assert report["total_pin_access_entry_count"] > 0
    assert report["critical_signal_pin_ready"] is True
    assert report["power_pin_ready"] is True
    assert report["top_io_access_ready"] is True
    assert report["blocking_missing_pin_count"] == 0
    assert report["unknown_pin_status_count"] == 0
    assert report["c2_related_blocker_unresolved_count"] == 0
    assert report["remaining_C2_blockers_count"] == 0
    assert report["can_claim_C2_pin_geometry_access_repaired_now"] is True
    assert report["can_claim_complete_gds_now"] is False
    assert report["can_enter_C3_floorplan_reconstruction"] is True
    assert report["layoutgen_reference_used"] is True
    assert report["layoutgen_reference_audit_available"] is True
    print("OpenYield C2 pin geometry access repair tests passed.")


if __name__ == "__main__":
    main()
