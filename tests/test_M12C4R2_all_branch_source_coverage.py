from __future__ import annotations

import csv
from pathlib import Path
import sys

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from sram_layoutgen.openyield_adapter.composite_source_topology_extractor import extract_source_exact_composite_topology


def main() -> None:
    payload = extract_source_exact_composite_topology("/data1/qujh/work/external/OpenYield")
    assert len(payload["child_rows"]) == 53
    assert sum(int(row["connection_count"]) for row in payload["child_rows"]) == 260
    assert len(payload["all_branch_net_rows"]) == 260
    assert len(payload["default_active_net_rows"]) == 237
    assert sum(1 for row in payload["all_branch_net_rows"] if row["parent_module"] == "DATA_DFF") == 5
    assert sum(1 for row in payload["all_branch_net_rows"] if row["parent_module"] == "TIME" and str(row["instance_name_expression"]).strip("'\"") == "dff_buf_data") == 19
    assert sum(1 for row in payload["all_branch_net_rows"] if row["parent_module"] == "TIME" and str(row["instance_name_expression"]).strip("'\"") == "wen_delaychain") == 4
    out_rows = list(csv.DictReader((REPO_ROOT / "outputs/M12C4R2_dff_source_binding_gate/current_supported_config/M12C4R2_all_branch_source_net_connection_matrix.csv").open()))
    assert len(out_rows) == 260


if __name__ == "__main__":
    main()
