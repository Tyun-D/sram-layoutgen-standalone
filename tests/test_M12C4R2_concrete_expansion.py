from __future__ import annotations

import json
from pathlib import Path
import sys

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from sram_layoutgen.openyield_adapter.composite_concrete_expander import build_source_derived_concrete_expansion
from sram_layoutgen.openyield_adapter.composite_source_topology_extractor import extract_source_exact_composite_topology
from sram_layoutgen.openyield_adapter.config_branch_evaluator import REFERENCE_CONFIGS


def main() -> None:
    payload = extract_source_exact_composite_topology("/data1/qujh/work/external/OpenYield")
    contract = json.loads((REPO_ROOT / "outputs/M12C3A4R_review_atlas_state_normalization/current_supported_config/M12C3A4R_primitive_composition_input_contract.json").read_text(encoding="utf-8"))
    res16 = build_source_derived_concrete_expansion(
        config=REFERENCE_CONFIGS["16x16"],
        child_rows=payload["child_rows"],
        registry=payload["registry"],
        contract=contract,
        resolution_json=REPO_ROOT / "outputs/M12C3A_parameterized_device_gate_generator/current_supported_config/M12C3A_concrete_parameter_resolution_16x16.json",
    )
    res64 = build_source_derived_concrete_expansion(
        config=REFERENCE_CONFIGS["64x8"],
        child_rows=payload["child_rows"],
        registry=payload["registry"],
        contract=contract,
        resolution_json=REPO_ROOT / "outputs/M12C3A_parameterized_device_gate_generator/current_supported_config/M12C3A_concrete_parameter_resolution_64x8.json",
    )
    assert res16["unresolved_concrete_instance_count"] == 0
    assert res64["unresolved_concrete_instance_count"] == 0
    assert res16["active_leaf_parent_net_connections_complete"] is True
    assert res64["active_leaf_parent_net_connections_complete"] is True
    assert any(row["instance_classification"] == "NEW_PRIMITIVE_REQUIRED" for row in res16["instances"])
    assert all(row["parent_net_connections"] != "[]" for row in res16["instances"] if row["instance_classification"] == "APPROVED_LEAF_PRIMITIVE")
    script_text = (REPO_ROOT / "scripts/M12C4R2_dff_source_binding_gate.py").read_text(encoding="utf-8")
    assert "unresolved_parameter_expression_count = 0" not in script_text


if __name__ == "__main__":
    main()
