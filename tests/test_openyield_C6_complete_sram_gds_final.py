from __future__ import annotations

import json
from pathlib import Path


def main() -> None:
    repo_root = Path(__file__).resolve().parents[1]
    report = json.loads((repo_root / "docs/openyield_C6_complete_sram_gds_final_report.json").read_text(encoding="utf-8"))

    assert (repo_root / "docs/openyield_C6_complete_sram_gds_final_report.json").exists()
    assert (repo_root / "docs/openyield_C6_complete_sram_gds_final_report.md").exists()
    assert (repo_root / "outputs/openyield_complete_sram/current_supported_config/openyield_complete_sram.gds").exists()
    assert report["final_complete_gds_sanity_status"] == "PASSED"
    assert report["top_cell_name"] == "openyield_complete_sram"
    assert report["required_modules_found_in_recursive_gds_count"] == 20
    assert report["required_modules_missing_from_recursive_gds"] == []
    assert report["access_view_module_reference_count"] == 20
    assert report["floorplan_proxy_reference_count"] == 0
    assert report["geometry_wordline_route_count"] >= 4
    assert report["contract_wordline_route_count"] == 0
    assert report["geometry_bitline_connection_count"] >= 32
    assert report["contract_bitline_route_count"] == 0
    assert report["geometry_control_route_count"] >= 6
    assert report["contract_control_route_count"] == 0
    assert report["top_signal_io_route_count"] > 0
    assert report["contract_top_io_route_count"] == 0
    assert report["signal_net_to_shape_entry_count"] >= 62
    assert report["shape_verified_signal_route_count"] == report["signal_net_to_shape_entry_count"]
    assert report["module_power_connected_count"] == 20
    assert report["module_vdd_connected_count"] == 20
    assert report["module_gnd_connected_count"] == 20
    assert report["vdd_graph_connected"] is True
    assert report["gnd_graph_connected"] is True
    assert report["power_net_to_shape_entry_count"] >= 58
    assert report["shape_verified_power_entry_count"] == report["power_net_to_shape_entry_count"]
    assert report["contract_rail_based_stitch_count"] == 0
    assert report["approximate_power_geometry_count"] == 0
    assert report["top_vdd_pin_exported"] is True
    assert report["top_gnd_pin_exported"] is True
    assert report["final_contract_route_entry_count"] == 0
    assert report["final_bbox_only_route_entry_count"] == 0
    assert report["final_approximate_geometry_entry_count"] == 0
    assert report["final_placeholder_entry_count"] == 0
    assert report["final_risk_register_available"] is True
    assert report["final_delivery_checklist_available"] is True
    assert report["can_claim_C6_complete_sram_gds_generated_now"] is True
    assert report["can_claim_complete_gds_for_current_supported_config_now"] is True
    assert report["can_claim_timing_closure_now"] is False
    assert report["can_claim_signoff_ready_now"] is False
    assert report["can_claim_tapeout_ready_now"] is False
    assert report["remaining_C6_blockers_count"] == 0
    assert report["drc_smoke_status"] in ["DRC_SMOKE_CLEAN", "DRC_SMOKE_RAN_WITH_MARKERS", "DRC_NOT_RUN_WITH_REASON"]
    assert report["lvs_feasibility_status"] in ["LVS_FEASIBLE_WITH_GAPS", "LVS_FEASIBLE_READY_FOR_RUN", "LVS_NOT_FEASIBLE_WITH_REASON"]
    assert report["lvs_run_status"] in ["LVS_PASSED", "LVS_FAILED", "NOT_RUN_WITH_REASON"]
    print("OpenYield C6 complete SRAM GDS final tests passed.")


if __name__ == "__main__":
    main()
