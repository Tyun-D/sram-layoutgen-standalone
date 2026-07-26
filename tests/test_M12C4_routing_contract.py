from __future__ import annotations

import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))


def main() -> int:
    contract = json.loads((REPO_ROOT / "outputs/M12C4_composite_control_cell_generation_plan/current_supported_config/M12C4_composite_routing_contract.json").read_text())
    report = json.loads((REPO_ROOT / "docs/M12C4_composite_control_cell_generation_plan_report.json").read_text())
    assert contract["local_pin_escape_layer"] == "m1"
    assert contract["primary_intercell_signal_layer"] == "m2"
    assert contract["via_stack"] == "m1_via1_m2"
    assert report["m1_pin_escape_supported"] is True
    assert report["m2_intercell_routing_supported"] is True
    assert report["via1_supported"] is True
    assert report["power_stitch_supported"] is True
    print("M12C4_routing_contract_ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
