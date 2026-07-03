from __future__ import annotations

import json
from pathlib import Path


def main() -> None:
    root = Path("/data1/qujh/work/sram_layoutgen_step45_clean")
    out_dir = root / "outputs/openyield_routing_power_pin/current_supported_config"
    report_json = root / "docs/openyield_R4_routing_power_pin_report.json"
    report_md = root / "docs/openyield_R4_routing_power_pin_report.md"
    matrix_csv = root / "docs/mapping/openyield_R4_routing_power_pin_matrix.csv"
    matrix_md = root / "docs/mapping/openyield_R4_routing_power_pin_matrix.md"
    net_csv = root / "docs/mapping/openyield_R4_net_to_shape_matrix.csv"
    net_md = root / "docs/mapping/openyield_R4_net_to_shape_matrix.md"

    required = [
        report_json,
        report_md,
        matrix_csv,
        matrix_md,
        net_csv,
        net_md,
        root / "docs/evidence/R4_routing_power_pin_gap_summary.md",
        out_dir / "openyield_routed_power_pin_sram.gds",
        out_dir / "routing_power_pin_config.json",
        out_dir / "wordline_routing_report.json",
        out_dir / "wordline_routing_report.md",
        out_dir / "bitline_routing_report.json",
        out_dir / "bitline_routing_report.md",
        out_dir / "control_routing_report.json",
        out_dir / "control_routing_report.md",
        out_dir / "power_routing_report.json",
        out_dir / "power_routing_report.md",
        out_dir / "top_pin_export_report.json",
        out_dir / "top_pin_export_report.md",
        out_dir / "net_to_shape_map.json",
        out_dir / "net_to_shape_map.csv",
        out_dir / "net_to_shape_map.md",
        out_dir / "instance_mapping.json",
        out_dir / "instance_mapping.csv",
        out_dir / "instance_mapping.md",
        out_dir / "routing_power_pin_gds_sanity_report.json",
        out_dir / "routing_power_pin_generator_manifest.json",
        out_dir / "routing_power_pin_generation_report.json",
        out_dir / "routing_power_pin_generation_report.md",
    ]
    for path in required:
        assert path.exists(), f"missing required artifact: {path}"

    report = json.loads(report_json.read_text(encoding="utf-8"))
    assert report["routed_power_pin_gds_generated"] is True
    assert report["routed_power_pin_gds_sanity_status"] == "PASSED"
    assert report["wl_route_count"] >= 4
    assert report["bitline_route_count"] >= 8
    assert report["control_route_count"] >= 5
    assert report["power_route_count"] >= 2
    assert report["top_pin_count"] > 0
    assert report["net_to_shape_entry_count"] > 0
    assert report["instance_mapping_count"] == 20
    assert report["blocked_wordline_route_count"] == 0
    assert report["blocked_bitline_route_count"] == 0
    assert report["blocked_control_route_count"] == 0
    assert report["blocked_power_route_count"] == 0
    assert report["blocked_pin_export_count"] == 0
    assert report["remaining_R4_blockers_count"] == 0
    assert report["can_claim_R4_routing_power_pin_mapping_completed_now"] is True
    assert report["can_enter_R5_validation_comparison_final_handoff"] is True
    assert report["can_claim_detailed_routing_complete_now"] is False
    assert report["can_claim_power_network_signoff_now"] is False
    assert report["can_claim_drc_clean_now"] is False
    assert report["can_claim_lvs_clean_now"] is False
    assert report["can_claim_timing_closure_now"] is False
    assert report["can_claim_signoff_ready_now"] is False

    sanity = json.loads((out_dir / "routing_power_pin_gds_sanity_report.json").read_text(encoding="utf-8"))
    assert sanity["routing_power_pin_gds_sanity_status"] == "PASSED"
    assert sanity["top_cell_name"] == "openyield_routed_power_pin_sram"

    instance_mapping = json.loads((out_dir / "instance_mapping.json").read_text(encoding="utf-8"))
    assert len(instance_mapping["entries"]) == 20

    print("OpenYield R4 routing/power/pin tests passed.")


if __name__ == "__main__":
    main()
