from __future__ import annotations

import json
from pathlib import Path


def main() -> None:
    root = Path("/data1/qujh/work/sram_layoutgen_step45_clean")
    out_dir = root / "outputs/openyield_complete_gds_gap_audit/current_supported_config"
    report_json = root / "docs/openyield_C0_complete_gds_gap_audit_report.json"
    report_md = root / "docs/openyield_C0_complete_gds_gap_audit_report.md"
    matrix_csv = root / "docs/mapping/openyield_C0_complete_gds_gap_matrix.csv"
    matrix_md = root / "docs/mapping/openyield_C0_complete_gds_gap_matrix.md"

    required = [
        report_json,
        report_md,
        matrix_csv,
        matrix_md,
        root / "docs/evidence/C0_complete_gds_gap_summary.md",
        out_dir / "complete_gds_gap_audit_report.json",
        out_dir / "complete_gds_gap_audit_report.md",
        out_dir / "contract_connection_inventory.csv",
        out_dir / "contract_connection_inventory.md",
        out_dir / "approximate_geometry_inventory.csv",
        out_dir / "approximate_geometry_inventory.md",
        out_dir / "contract_power_inventory.csv",
        out_dir / "contract_power_inventory.md",
        out_dir / "missing_pin_geometry_inventory.csv",
        out_dir / "missing_pin_geometry_inventory.md",
        out_dir / "real_geometry_inventory.csv",
        out_dir / "real_geometry_inventory.md",
        out_dir / "geometry_connection_gap_summary.json",
        out_dir / "geometry_connection_gap_summary.md",
        out_dir / "complete_gds_blocker_matrix.csv",
        out_dir / "complete_gds_blocker_matrix.md",
    ]
    for path in required:
        assert path.exists(), f"missing required artifact: {path}"

    report = json.loads(report_json.read_text(encoding="utf-8"))
    assert report["C0_complete_gds_gap_audit_available"] is True
    assert report["contract_connection_inventory_available"] is True
    assert report["approximate_geometry_inventory_available"] is True
    assert report["contract_power_inventory_available"] is True
    assert report["missing_pin_geometry_inventory_available"] is True
    assert report["real_geometry_inventory_available"] is True
    assert report["geometry_connection_gap_summary_available"] is True
    assert report["complete_gds_blocker_matrix_available"] is True
    assert report["gds_parse_success"] is True
    assert report["complete_gds_blocker_count"] > 0
    assert report["can_claim_C0_gap_audit_completed_now"] is True
    assert report["can_claim_complete_gds_now"] is False
    assert report["can_enter_C1_physical_rule_extraction"] is True
    assert report["remaining_C0_blockers_count"] == 0

    print("OpenYield C0 complete GDS gap audit tests passed.")


if __name__ == "__main__":
    main()
