from __future__ import annotations

from pathlib import Path
import sys

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from sram_layoutgen.openyield_adapter.openram_device_adapter import build_backend_context
from sram_layoutgen.openyield_adapter.openram_pnand2_adapter import generate_pnand2_cell


def test_pnand2_adapter_exact_match() -> None:
    with build_backend_context(Path("/data1/qujh/OpenRAM")) as ctx:
        result = generate_pnand2_cell(
            ctx,
            cell_name="PNAND2_NW180_PW270_L50_FPDK45_TEST",
            requested_nmos_width_nm=180,
            requested_pmos_width_nm=270,
            requested_length_nm=50,
            source_instance_paths=["AND2.nand_gate"],
            reference_configs=["AND2"],
        )
    assert result.parameter_mapping["mapping_status"] == "EXACT_MATCH"
    assert list(result.pin_map) == ["VDD", "VSS", "A", "B", "Z"]
    assert len(result.device_layout) == 4
