from __future__ import annotations

import json
from pathlib import Path
import sys

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))


def main() -> None:
    report = json.loads((REPO_ROOT / "docs/M12C4AC_dff_connectivity_repair_report.json").read_text())
    assert report["physical_connectivity_verification_passed"] is True
    assert report["d_q_direct_short_present"] is False
    assert report["power_signal_short_count"] == 0
    assert report["vdd_vss_short_present"] is False


if __name__ == "__main__":
    main()

