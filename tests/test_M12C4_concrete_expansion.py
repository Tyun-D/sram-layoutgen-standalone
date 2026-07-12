from __future__ import annotations

import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))


def main() -> int:
    a = json.loads((REPO_ROOT / "outputs/M12C4_composite_control_cell_generation_plan/current_supported_config/M12C4_concrete_composite_expansion_16x16.json").read_text())
    b = json.loads((REPO_ROOT / "outputs/M12C4_composite_control_cell_generation_plan/current_supported_config/M12C4_concrete_composite_expansion_64x8.json").read_text())
    assert a["address_width"] == 4
    assert a["ADDR_DFF_bit_count"] == 4
    assert a["DATA_DFF_bit_count"] == 16
    assert b["address_width"] == 6
    assert b["ADDR_DFF_bit_count"] == 6
    assert b["DATA_DFF_bit_count"] == 8
    assert a["concrete_physical_children"]["DFF_pinv"] == "PINV_NW250_PW500_L50"
    assert a["concrete_physical_children"]["DFF_transmission_gate"] == "TRANSMISSION_GATE_NW250_PW500_L50"
    print("M12C4_concrete_expansion_ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
