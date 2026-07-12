from __future__ import annotations

from pathlib import Path
import sys

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from sram_layoutgen.openyield_adapter.composite_source_topology_extractor import extract_source_exact_composite_topology

OPENYIELD_ROOT = Path("/data1/qujh/work/external/OpenYield")


def main() -> None:
    payload = extract_source_exact_composite_topology(OPENYIELD_ROOT)
    child_rows = payload["child_rows"]
    net_rows = payload["net_rows"]
    assert len(child_rows) == 53
    assert len(net_rows) == 232
    assert sum(1 for row in child_rows if row["child_logical_module"] and not row["child_pin_order"]) == 0
    assert sum(1 for row in child_rows if not row["pin_connection_count_match"]) == 0
    assert sum(1 for row in child_rows if row["module_name"] == "DFF") == 11
    dff_net_rows = [row for row in net_rows if row["parent_module"] == "DFF"]
    assert len(dff_net_rows) == 52
    assert sum(1 for row in child_rows if row["module_name"] == "DFF" and row["child_logical_module"] == "PINV") == 7
    assert sum(1 for row in child_rows if row["module_name"] == "DFF" and row["child_logical_module"] == "TRANSMISSION_GATE") == 4


if __name__ == "__main__":
    main()
