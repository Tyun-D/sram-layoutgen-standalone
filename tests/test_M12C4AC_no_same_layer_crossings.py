from __future__ import annotations

import csv
from pathlib import Path
import sys

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))


def main() -> None:
    rows = list(csv.DictReader((REPO_ROOT / "outputs/M12C4AC_dff_connectivity_repair/current_supported_config/M12C4AC_dff_route_segment_matrix.csv").open()))
    assert all(float(row["start"].strip("[]").split(",")[1]) == float(row["end"].strip("[]").split(",")[1]) for row in rows if row["layer"] == "m1")
    assert all(float(row["start"].strip("[]").split(",")[0]) == float(row["end"].strip("[]").split(",")[0]) for row in rows if row["layer"] == "m2")
    assert sum(1 for row in rows if row["layer"] == "m1") == 11
    assert sum(1 for row in rows if row["layer"] == "m2") == 30


if __name__ == "__main__":
    main()

