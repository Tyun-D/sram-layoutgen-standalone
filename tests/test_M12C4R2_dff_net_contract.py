from __future__ import annotations

import json
from pathlib import Path
import sys

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))


def main() -> None:
    contract = json.loads((REPO_ROOT / "outputs/M12C4R2_dff_source_binding_gate/current_supported_config/M12C4R2_dff_net_contract.json").read_text(encoding="utf-8"))
    assert contract["dff_top_pin_count"] == 5
    assert contract["dff_internal_net_count"] == 8
    assert contract["dff_unknown_net_count"] == 0
    assert contract["dff_unconnected_required_child_pin_count"] == 0
    assert contract["dff_duplicate_instance_name_count"] == 0
    clkb = contract["internal_nets"]["CLKB"]
    assert clkb["drivers_or_output_terminals"] == ["inv1_clk.Z"]
    assert clkb["loads_or_input_terminals"] == ["tg1.CTR_N", "tg2.CTR_P", "tg3.CTR_P", "tg4.CTR_N"]
    clk = contract["top_pin_contracts"]["CLK"]
    assert "inv1_clk.A" in clk["loads_or_input_terminals"]
    assert "tg1.CTR_P" in clk["loads_or_input_terminals"]
    assert "tg2.CTR_N" in clk["loads_or_input_terminals"]
    assert "tg3.CTR_N" in clk["loads_or_input_terminals"]
    assert "tg4.CTR_P" in clk["loads_or_input_terminals"]


if __name__ == "__main__":
    main()
