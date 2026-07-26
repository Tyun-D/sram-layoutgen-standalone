from __future__ import annotations

import sys
import tempfile
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from sram_layoutgen.openyield_adapter.openram_device_adapter import build_backend_context
from sram_layoutgen.openyield_adapter.openram_pinv_adapter import generate_pinv_cell
from sram_layoutgen.openyield_adapter.primitive_geometry_verifier import geometry_fingerprint


def main() -> int:
    with build_backend_context(Path("/data1/qujh/OpenRAM")) as ctx:
        r1 = generate_pinv_cell(ctx, cell_name="PINV_NW90_PW270_L50", requested_nmos_width_nm=90, requested_pmos_width_nm=270, requested_length_nm=50, source_instance_paths=["TIME.inv_clk_bar"], reference_configs=["16x16"])
        assert r1.parameter_mapping["parameter_match"] is True
        assert set(r1.pin_map) == {"VDD", "VSS", "A", "Z"}
        r2 = generate_pinv_cell(ctx, cell_name="PINV_NW250_PW500_L50", requested_nmos_width_nm=250, requested_pmos_width_nm=500, requested_length_nm=50, source_instance_paths=["dff.inv_dff"], reference_configs=["16x16"])
        assert r2.parameter_mapping["actual_nmos_width_nm"] == 250
        assert r2.parameter_mapping["actual_pmos_width_nm"] == 500
        assert r1.parameter_mapping["calculated_openram_size"] != r2.parameter_mapping["calculated_openram_size"]
    print("M12C3A_pinv_adapter_ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

