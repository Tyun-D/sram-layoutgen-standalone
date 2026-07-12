from __future__ import annotations

import csv
from pathlib import Path
import sys

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from sram_layoutgen.openyield_adapter.composite_concrete_expander import build_active_template_rows
from sram_layoutgen.openyield_adapter.composite_source_topology_extractor import extract_source_exact_composite_topology
from sram_layoutgen.openyield_adapter.config_branch_evaluator import REFERENCE_CONFIGS


def main() -> None:
    payload = extract_source_exact_composite_topology("/data1/qujh/work/external/OpenYield")
    res16 = build_active_template_rows(child_rows=payload["child_rows"], registry=payload["registry"], config=REFERENCE_CONFIGS["16x16"])
    res64 = build_active_template_rows(child_rows=payload["child_rows"], registry=payload["registry"], config=REFERENCE_CONFIGS["64x8"])
    assert len(res16["active_child_rows"]) == 50
    assert res16["active_net_connection_count"] == 248
    assert len(res64["active_child_rows"]) == 50
    assert res64["active_net_connection_count"] == 248
    assert any(row["module_name"] == "TIME" and str(row["instance_name_expression"]).strip("'\"") == "dff_buf_data" and row["active_for_config"] for row in res16["active_rows"])
    assert any(row["module_name"] == "DATA_DFF" and row["active_for_config"] for row in res16["active_rows"])
    assert any(row["module_name"] == "TIME" and str(row["instance_name_expression"]).strip("'\"") == "wen_delaychain" and not row["active_for_config"] for row in res16["active_rows"])
    out16 = list(csv.DictReader((REPO_ROOT / "outputs/M12C4R2_dff_source_binding_gate/current_supported_config/M12C4R2_config_active_net_connection_matrix_16x16.csv").open()))
    out64 = list(csv.DictReader((REPO_ROOT / "outputs/M12C4R2_dff_source_binding_gate/current_supported_config/M12C4R2_config_active_net_connection_matrix_64x8.csv").open()))
    assert sum(1 for row in out16 if row["active_for_config"] == "True") == 248
    assert sum(1 for row in out64 if row["active_for_config"] == "True") == 248


if __name__ == "__main__":
    main()
