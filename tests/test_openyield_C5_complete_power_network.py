from __future__ import annotations

import json
from pathlib import Path


def main() -> None:
    repo_root = Path(__file__).resolve().parents[1]
    report = json.loads((repo_root / "docs/openyield_C5_complete_power_network_report.json").read_text(encoding="utf-8"))

    assert (repo_root / "docs/openyield_C5_complete_power_network_report.json").exists()
    assert (repo_root / "docs/openyield_C5_complete_power_network_report.md").exists()
    assert (repo_root / "outputs/openyield_complete_power_network/current_supported_config/openyield_complete_power_stitched_sram.gds").exists()
    assert report["power_stitched_gds_sanity_status"] == "PASSED"
    assert report["top_cell_name"] == "openyield_complete_power_stitched_sram"
    assert report["required_modules_found_in_recursive_gds_count"] == 20
    assert report["required_modules_missing_from_recursive_gds"] == []
    assert report["access_view_module_reference_count"] == 20
    assert report["floorplan_proxy_reference_count"] == 0
    assert report["signal_route_shape_preserved_count"] > 0
    assert report["module_power_connected_count"] == 20
    assert report["module_vdd_connected_count"] == 20
    assert report["module_gnd_connected_count"] == 20
    assert report["blocked_module_power_connection_count"] == 0
    assert report["contract_module_power_connection_count"] == 0
    assert report["vdd_graph_connected"] is True
    assert report["gnd_graph_connected"] is True
    assert report["power_graph_blocked_edge_count"] == 0
    assert report["power_graph_contract_edge_count"] == 0
    assert report["contract_rail_based_stitch_count"] == 0
    assert report["approximate_power_geometry_count"] == 0
    assert report["placeholder_power_overlay_count"] == 0
    assert report["power_net_to_shape_entry_count"] > 0
    assert report["shape_verified_power_entry_count"] == report["power_net_to_shape_entry_count"]
    assert report["top_vdd_pin_exported"] is True
    assert report["top_gnd_pin_exported"] is True
    assert report["blocked_top_power_pin_count"] == 0
    assert report["contract_top_power_pin_count"] == 0
    assert report["remaining_C5_blockers_count"] == 0
    assert report["can_claim_C5_power_network_stitched_now"] is True
    assert report["can_claim_complete_gds_now"] is False
    assert report["can_enter_C6_complete_gds_validation"] is True
    print("OpenYield C5 complete power network tests passed.")


if __name__ == "__main__":
    main()
