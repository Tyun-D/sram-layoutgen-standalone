from __future__ import annotations

import csv
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))


def main() -> int:
    report = json.loads((REPO_ROOT / "docs/M12C4_composite_control_cell_generation_plan_report.json").read_text())
    csv_path = REPO_ROOT / "docs/mapping/M12C4_composite_implementation_wave_plan.csv"
    with csv_path.open("r", encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    assert rows
    assert report["implementation_wave_plan_locked"] is True
    assert report["first_implementation_wave"] == "Wave1"
    assert report["first_implementation_module"] == "DFF"
    assert any(row["module"] == "DFF" for row in rows)
    print("M12C4_wave_plan_ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
