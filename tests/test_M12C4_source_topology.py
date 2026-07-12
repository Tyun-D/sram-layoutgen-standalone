from __future__ import annotations

import csv
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from sram_layoutgen.openyield_adapter.composite_source_topology_extractor import extract_source_exact_composite_topology


def main() -> int:
    extracted = extract_source_exact_composite_topology(Path("/data1/qujh/work/external/OpenYield"))
    assert extracted["summary"]["source_topology_extraction_completed"] is True
    assert extracted["summary"]["unresolved_source_topology_count"] == 0
    modules = {row["module_name"] for row in extracted["inventory_rows"]}
    for name in ["DFF", "DFF_BUF", "ADDR_DFF", "DATA_DFF", "AND2", "AND3", "PNAND2", "PNAND3", "pdrive", "pdrive2_for_pre", "wl_pdrive", "delay_chain", "TIME"]:
        assert name in modules
    assert "wen_delay_chain" in modules or "WenDelayChain" in modules
    csv_path = REPO_ROOT / "docs/mapping/M12C4_source_exact_composite_module_inventory.csv"
    with csv_path.open("r", encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    assert len(rows) == extracted["summary"]["source_composite_module_count"]
    print("M12C4_source_topology_ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
