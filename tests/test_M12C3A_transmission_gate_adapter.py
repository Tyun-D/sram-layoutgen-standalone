from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from sram_layoutgen.openyield_adapter.openram_device_adapter import build_backend_context
from sram_layoutgen.openyield_adapter.openram_transmission_gate_adapter import generate_transmission_gate_cell


def main() -> int:
    with build_backend_context(Path("/data1/qujh/OpenRAM")) as ctx:
        result = generate_transmission_gate_cell(ctx, cell_name="TRANSMISSION_GATE_NW250_PW500_L50", nmos_width_nm=250, pmos_width_nm=500, channel_length_nm=50, source_instance_paths=["TransmissionGate"], reference_configs=["16x16"])
        assert result.connectivity_contract["transmission_gate_parameter_match"] is True
        assert set(result.pin_map) == {"VDD", "VSS", "IN", "OUT", "CTR_P", "CTR_N"}
        assert result.connectivity_contract["nmos_logical_device_count"] == 1
        assert result.connectivity_contract["pmos_logical_device_count"] == 1
    print("M12C3A_transmission_gate_adapter_ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

