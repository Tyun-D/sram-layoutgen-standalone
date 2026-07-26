from __future__ import annotations

import json
from pathlib import Path
import sys

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from sram_layoutgen.openyield_adapter.composite_concrete_expander import build_concrete_binding_report


def _contract() -> dict:
    return json.loads(
        (
            REPO_ROOT
            / "outputs/M12C3A4R_review_atlas_state_normalization/current_supported_config/M12C3A4R_primitive_composition_input_contract.json"
        ).read_text(encoding="utf-8")
    )


def main() -> None:
    contract = _contract()
    cfg16 = {"num_rows": 16, "num_cols": 16, "num_words": 16, "word_size": 16, "words_per_row": 1, "mux_ratio": 1, "choose_columnmux": False, "operation": "read&write", "tech": "FreePDK45"}
    cfg64 = {"num_rows": 64, "num_cols": 8, "num_words": 64, "word_size": 8, "words_per_row": 1, "mux_ratio": 1, "choose_columnmux": False, "operation": "read&write", "tech": "FreePDK45"}
    res16 = build_concrete_binding_report(
        config=cfg16,
        resolution_json=REPO_ROOT / "outputs/M12C3A_parameterized_device_gate_generator/current_supported_config/M12C3A_concrete_parameter_resolution_16x16.json",
        contract=contract,
    )
    res64 = build_concrete_binding_report(
        config=cfg64,
        resolution_json=REPO_ROOT / "outputs/M12C3A_parameterized_device_gate_generator/current_supported_config/M12C3A_concrete_parameter_resolution_64x8.json",
        contract=contract,
    )
    assert res16["concrete_expanded_instance_count"] == 12
    assert res64["concrete_expanded_instance_count"] == 12
    assert res16["DFF_total_count"] == 22
    assert res64["DFF_total_count"] == 16
    leaf_rows = [*res16["leaf_rows"], *res64["leaf_rows"]]
    failure_rows = [*res16["failure_rows"], *res64["failure_rows"]]
    assert len(leaf_rows) == 38
    assert all(row["binding_status"] == "APPROVED_PRIMITIVE_BINDING" for row in leaf_rows)
    assert sum(1 for row in failure_rows if row["failure_class"] == "NEW_PRIMITIVE_REQUIRED") == 4
    assert sum(1 for row in failure_rows if row["failure_class"] == "COMPOSITE_CHILD_NOT_YET_GENERATED") > 0


if __name__ == "__main__":
    main()
