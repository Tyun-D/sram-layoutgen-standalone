from __future__ import annotations

import csv
from pathlib import Path
import sys

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))


def main() -> None:
    rows = list(csv.DictReader((REPO_ROOT / "outputs/M12C4AC_dff_connectivity_repair/current_supported_config/M12C4AC_floorplan_route_trial_matrix.csv").open()))
    assert len(rows) == 3
    archs = {row["architecture"] for row in rows}
    assert {"SINGLE_ROW_SOURCE_ORDER", "TWO_ROW_MASTER_SLAVE_MICRO_FLOORPLAN", "THREE_ZONE_CLOCK_MASTER_SLAVE"} == archs


if __name__ == "__main__":
    main()

