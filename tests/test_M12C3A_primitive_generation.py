from __future__ import annotations

import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from sram_layoutgen.openyield_adapter.primitive_geometry_verifier import geometry_fingerprint, read_top_cell


def main() -> int:
    report = json.loads((REPO_ROOT / "docs/M12C3A_parameterized_device_gate_generator_report.json").read_text(encoding="utf-8"))
    assert report["primitive_generation_passed"] is True
    assert report["generated_pinv_variant_count"] > 0
    assert report["generated_transmission_gate_count"] == 1
    pinv = REPO_ROOT / "outputs/M12C3A_parameterized_device_gate_generator/current_supported_config/cells/PINV_NW90_PW270_L50/PINV_NW90_PW270_L50.gds"
    tg = REPO_ROOT / "outputs/M12C3A_parameterized_device_gate_generator/current_supported_config/cells/TRANSMISSION_GATE_NW250_PW500_L50/TRANSMISSION_GATE_NW250_PW500_L50.gds"
    _, pinv_top = read_top_cell(pinv, "PINV_NW90_PW270_L50")
    _, tg_top = read_top_cell(tg, "TRANSMISSION_GATE_NW250_PW500_L50")
    assert pinv_top.name == "PINV_NW90_PW270_L50"
    assert tg_top.name == "TRANSMISSION_GATE_NW250_PW500_L50"
    assert geometry_fingerprint(pinv, "PINV_NW90_PW270_L50")["digest"] != geometry_fingerprint(tg, "TRANSMISSION_GATE_NW250_PW500_L50")["digest"]
    print("M12C3A_primitive_generation_ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

