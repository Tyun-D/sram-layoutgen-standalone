from __future__ import annotations

import csv
import json
import xml.etree.ElementTree as ET
from pathlib import Path
import sys

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))


def main() -> None:
    report = json.loads((REPO_ROOT / "outputs/M12C4AC_dff_connectivity_repair/current_supported_config/M12C4AC_dff_drc_report.json").read_text())
    lyrdb = REPO_ROOT / "outputs/M12C4AC_dff_connectivity_repair/current_supported_config/M12C4AC_dff_drc.lyrdb"
    items = ET.parse(lyrdb).getroot().findall(".//item")
    rows = list(csv.DictReader((REPO_ROOT / "outputs/M12C4AC_dff_connectivity_repair/current_supported_config/M12C4AC_dff_drc_category_matrix.csv").open()))
    assert report["dff_drc_marker_count"] == 0
    assert report["dff_drc_passed"] is True
    assert len(items) == 0
    assert all(int(row["count"]) == 0 for row in rows)


if __name__ == "__main__":
    main()

