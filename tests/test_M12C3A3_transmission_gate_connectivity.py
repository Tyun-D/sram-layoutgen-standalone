from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from sram_layoutgen.openyield_adapter.transmission_gate_connectivity_verifier import verify_transmission_gate_connectivity


def main() -> int:
    gds_path = REPO_ROOT / "outputs/M12C3A3_transmission_gate_adapter_repair/current_supported_config/TRANSMISSION_GATE_NW250_PW500_L50/TRANSMISSION_GATE_NW250_PW500_L50.gds"
    graph, report = verify_transmission_gate_connectivity(gds_path, "TRANSMISSION_GATE_NW250_PW500_L50")
    assert report["physical_connectivity_verification_passed"] is True
    assert report["in_connected_to_vdd_after_repair"] is False
    assert report["in_connected_to_vss_after_repair"] is False
    assert report["out_connected_to_vdd_after_repair"] is False
    assert report["out_connected_to_vss_after_repair"] is False
    assert report["vdd_connected_to_vss_after_repair"] is False
    assert report["in_directly_connected_to_out_after_repair"] is False
    assert report["pin_components"]["IN"] == report["pmos_terminal_components"]["left"] == report["nmos_terminal_components"]["left"]
    assert report["pin_components"]["OUT"] == report["pmos_terminal_components"]["right"] == report["nmos_terminal_components"]["right"]
    assert report["pin_components"]["VDD"] == report["nwell_tap_component"]
    assert report["pin_components"]["VSS"] == report["pwell_tap_component"]
    assert report["connectivity_assertion_failure_count"] == 0
    print("M12C3A3_transmission_gate_connectivity_ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
