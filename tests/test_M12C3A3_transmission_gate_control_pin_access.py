from __future__ import annotations

import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from sram_layoutgen.openyield_adapter.transmission_gate_connectivity_verifier import verify_transmission_gate_connectivity


def main() -> int:
    gds_path = REPO_ROOT / "outputs/M12C3A3_transmission_gate_adapter_repair/current_supported_config/TRANSMISSION_GATE_NW250_PW500_L50/TRANSMISSION_GATE_NW250_PW500_L50.gds"
    _, report = verify_transmission_gate_connectivity(gds_path, "TRANSMISSION_GATE_NW250_PW500_L50")
    pin_map = json.loads((REPO_ROOT / "outputs/M12C3A3_transmission_gate_adapter_repair/current_supported_config/TRANSMISSION_GATE_NW250_PW500_L50/TRANSMISSION_GATE_NW250_PW500_L50_pin_map.json").read_text())
    assert all(pin_map[name][0]["layer"] == "m1" for name in ("VDD", "VSS", "IN", "OUT", "CTR_P", "CTR_N"))
    assert report["ctr_p_metal1_pin_added"] is True
    assert report["ctr_n_metal1_pin_added"] is True
    assert report["ctr_p_poly_contact_added"] is True
    assert report["ctr_n_poly_contact_added"] is True
    assert report["all_six_pins_metal_accessible"] is True
    assert report["pin_components"]["CTR_P"] != report["pin_components"]["CTR_N"]
    assert report["pin_components"]["CTR_P"] != report["pin_components"]["IN"]
    assert report["pin_components"]["CTR_N"] != report["pin_components"]["OUT"]
    print("M12C3A3_transmission_gate_control_pin_access_ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
