from __future__ import annotations

import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from sram_layoutgen.signoff import count_klayout_items


def main() -> int:
    report = json.loads((REPO_ROOT / "outputs/M12C3A3_transmission_gate_adapter_repair/current_supported_config/M12C3A3_transmission_gate_drc_report.json").read_text())
    lyrdb = REPO_ROOT / "outputs/M12C3A3_transmission_gate_adapter_repair/current_supported_config/M12C3A3_transmission_gate_drc.lyrdb"
    assert report["drc_run"] is True
    assert report["drc_parse_passed"] is True
    assert count_klayout_items(lyrdb) == 0
    assert report["marker_count"] == 0
    assert report["drc_passed"] is True
    print("M12C3A3_transmission_gate_drc_ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
