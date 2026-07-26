from __future__ import annotations

import csv
from pathlib import Path
import sys

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))


def main() -> None:
    rows = list(csv.DictReader((REPO_ROOT / "outputs/M12C4R2_dff_source_binding_gate/current_supported_config/M12C4R2_dff_instance_binding_matrix.csv").open()))
    assert len(rows) == 11
    assert sum(1 for row in rows if row["binding_status"] == "APPROVED_EXACT_BINDING") == 11
    assert sum(1 for row in rows if row["child_logical_module"] == "PINV") == 7
    assert sum(1 for row in rows if row["child_logical_module"] == "TRANSMISSION_GATE") == 4
    assert sum(1 for row in rows if row["forbidden_source_root_used"] == "True") == 0
    assert all(row["resolved_physical_cell_name"] == "PINV_NW250_PW500_L50" for row in rows if row["child_logical_module"] == "PINV")
    assert all(row["resolved_physical_cell_name"] == "TRANSMISSION_GATE_NW250_PW500_L50" for row in rows if row["child_logical_module"] == "TRANSMISSION_GATE")
    assert all(row["parent_net_connections"] != "[]" for row in rows)


if __name__ == "__main__":
    main()
