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
    assert report["primitive_interface_audit_completed"] is True
    assert report["all_vdd_rails_align"] is True
    assert report["all_vss_rails_align"] is True
    csv_path = REPO_ROOT / "docs/mapping/M12C4_primitive_interface_compatibility_matrix.csv"
    with csv_path.open("r", encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    assert len(rows) == 10
    assert any(row["cell_name"] == "TRANSMISSION_GATE_NW250_PW500_L50" for row in rows)
    print("M12C4_primitive_interface_ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
