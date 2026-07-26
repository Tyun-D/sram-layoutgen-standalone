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
    child_rows = [row for row in payload["child_rows"] if row["module_name"] == "DFF"]
    net_rows = [row for row in payload["net_rows"] if row["parent_module"] == "DFF"]
    assert len(child_rows) == 11
    assert len(net_rows) == 52
    assert all(row["child_pin_order"] for row in child_rows)
    assert all(row["pin_connection_count_match"] for row in child_rows)
    assert {row["child_logical_module"] for row in child_rows} == {"PINV", "TRANSMISSION_GATE"}
    templates = {row["instance_name_expression"] for row in child_rows}
    assert "'inv1_clk'" in templates
    assert "'inv7'" in templates
    assert "'tg1'" in templates
    assert "'tg4'" in templates
    assert all(row["normalized_parent_net"] for row in net_rows)


if __name__ == "__main__":
    main()
