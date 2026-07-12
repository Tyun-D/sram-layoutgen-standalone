from __future__ import annotations

import csv
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))


def main() -> int:
    csv_path = REPO_ROOT / "docs/mapping/M12C4_approved_child_binding_matrix.csv"
    with csv_path.open("r", encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    dff_rows = [row for row in rows if row["parent_composite_module"] == "DFF" and row["resolved_physical_cell_name"]]
    assert dff_rows
    assert all(row["binding_status"] == "APPROVED_EXACT_BINDING" for row in dff_rows)
    assert any(row["resolved_physical_cell_name"] == "PINV_NW250_PW500_L50" for row in dff_rows)
    assert any(row["resolved_physical_cell_name"] == "TRANSMISSION_GATE_NW250_PW500_L50" for row in dff_rows)
    assert any(row["binding_status"] == "NEW_PRIMITIVE_GENERATOR_REQUIRED" for row in rows if row["child_logical_alias"] in {"PNAND2", "PNAND3"})
    print("M12C4_child_binding_ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
