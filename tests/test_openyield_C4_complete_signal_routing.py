from __future__ import annotations

import json
from pathlib import Path


def main() -> None:
    root = Path("/data1/qujh/work/sram_layoutgen_step45_clean")
    out_dir = root / "outputs/openyield_complete_signal_routing/current_supported_config"
    report_json = root / "docs/openyield_C4_complete_signal_routing_report.json"
    report_md = root / "docs/openyield_C4_complete_signal_routing_report.md"
    required = [
        report_json,
        report_md,
        root / "docs/mapping/openyield_C4_signal_net_to_shape_matrix.csv",
        root / "docs/mapping/openyield_C4_signal_net_to_shape_matrix.md",
        root / "docs/mapping/openyield_C4_signal_routing_matrix.csv",
        root / "docs/mapping/openyield_C4_signal_routing_matrix.md",
        root / "docs/evidence/C4_complete_signal_routing_summary.md",
        out_dir / "openyield_complete_signal_routed_sram.gds",
        out_dir / "complete_wordline_routing_report.json",
        out_dir / "complete_bitline_routing_report.json",
        out_dir / "complete_column_path_routing_report.json",
        out_dir / "complete_control_routing_report.json",
        out_dir / "complete_top_io_routing_report.json",
        out_dir / "complete_signal_net_to_shape_map.json",
        out_dir / "complete_signal_route_shape_index.json",
        out_dir / "complete_signal_routing_gds_sanity_report.json",
    ]
    for path in required:
        assert path.exists(), f"missing required artifact: {path}"

    report = json.loads(report_json.read_text(encoding="utf-8"))
    assert report["signal_routed_gds_sanity_status"] == "PASSED"
    assert report["top_cell_name"] == "openyield_complete_signal_routed_sram"
    assert report["required_modules_found_in_recursive_gds_count"] == 20
    assert report["required_modules_missing_from_recursive_gds"] == []
    assert report["access_view_module_reference_count"] == 20
    assert report["wordline_route_count"] >= 4
    assert report["geometry_wordline_route_count"] >= 4
    assert report["contract_wordline_route_count"] == 0
    assert report["blocked_wordline_route_count"] == 0
    assert report["bitline_connection_count"] >= 32
    assert report["geometry_bitline_connection_count"] >= 32
    assert report["contract_bitline_route_count"] == 0
    assert report["blocked_bitline_route_count"] == 0
    assert report["control_route_count"] >= 6
    assert report["geometry_control_route_count"] >= 6
    assert report["contract_control_route_count"] == 0
    assert report["blocked_control_route_count"] == 0
    assert report["top_signal_io_route_count"] > 0
    assert report["contract_top_io_route_count"] == 0
    assert report["blocked_top_io_route_count"] == 0
    assert report["placeholder_signal_overlay_count"] == 0
    assert report["signal_net_to_shape_entry_count"] > 0
    assert report["shape_verified_signal_route_count"] == report["signal_net_to_shape_entry_count"]
    assert report["remaining_C4_blockers_count"] == 0
    assert report["can_claim_C4_signal_geometry_routing_completed_now"] is True
    assert report["can_claim_complete_gds_now"] is False
    assert report["can_enter_C5_power_network_stitching"] is True
    print("OpenYield C4 complete signal routing tests passed.")


if __name__ == "__main__":
    main()
