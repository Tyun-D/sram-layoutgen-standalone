from __future__ import annotations

import csv
import json
from pathlib import Path
import sys

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))


def main() -> None:
    report = json.loads((REPO_ROOT / "outputs/M12C4AC_dff_connectivity_repair/current_supported_config/M12C4AC_failed_attempt_root_cause_report.json").read_text())
    rows = list(csv.DictReader((REPO_ROOT / "outputs/M12C4AC_dff_connectivity_repair/current_supported_config/M12C4AC_failed_drc_category_matrix.csv").open()))
    assert report["failed_signal_supernet_component_id"] == "via1_172"
    assert report["failed_route_segment_count"] == 44
    assert report["failed_m2_route_count"] == 44
    assert report["failed_via1_count"] == 33
    counts = {row["category"]: int(row["count"]) for row in rows}
    assert counts["TOTAL"] == 88
    assert counts["METAL2.1"] == 42
    assert counts["METAL1.2"] == 20


if __name__ == "__main__":
    main()

