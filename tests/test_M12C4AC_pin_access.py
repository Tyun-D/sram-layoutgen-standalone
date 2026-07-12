from __future__ import annotations

import csv
from pathlib import Path
import sys

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))


def main() -> None:
    rows = list(csv.DictReader((REPO_ROOT / "outputs/M12C4AC_dff_connectivity_repair/current_supported_config/M12C4AC_pin_access_decision_matrix.csv").open()))
    assert len(rows) == 30
    assert all(row["access_status"] == "PLANNED" for row in rows)
    assert all(row["grid_aligned"] == "True" for row in rows)


if __name__ == "__main__":
    main()

