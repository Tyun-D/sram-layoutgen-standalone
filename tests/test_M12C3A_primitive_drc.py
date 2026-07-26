from __future__ import annotations

import csv
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))


def main() -> int:
    report = json.loads((REPO_ROOT / "docs/M12C3A_parameterized_device_gate_generator_report.json").read_text(encoding="utf-8"))
    with (REPO_ROOT / "docs/mapping/M12C3A_primitive_cell_drc_matrix.csv").open("r", encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    assert report["primitive_cell_drc_run"] is True
    assert report["primitive_cell_drc_fail_count"] == 0
    assert report["primitive_smoke_total_drc_marker_count"] == 0
    assert all(int(row["marker_count"]) == 0 for row in rows)
    print("M12C3A_primitive_drc_ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
