from __future__ import annotations

import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))


def main() -> int:
    report = json.loads((REPO_ROOT / "docs/M12C4_composite_control_cell_generation_plan_report.json").read_text())
    contract = json.loads(
        (
            REPO_ROOT
            / "outputs/M12C3A4R_review_atlas_state_normalization/current_supported_config/M12C3A4R_primitive_composition_input_contract.json"
        ).read_text()
    )
    current_state = json.loads((REPO_ROOT / "docs/evidence/M12C3A4R_current_qualified_primitive_state.json").read_text())

    assert report["m12c3a4r_gate_passed"] is True
    assert report["composition_input_contract_locked"] is True
    assert report["approved_reusable_cell_count"] == 10
    assert report["approved_pinv_count"] == 9
    assert report["approved_transmission_gate_count"] == 1
    assert contract["review_atlas_is_evidence_only"] is True
    assert contract["review_atlas_cells_must_not_be_composed"] is True
    assert current_state["p0_primitives_reusable_for_composition"] is True
    assert current_state["transmission_gate_vdd_vss_short_present"] is False
    assert current_state["duplicate_label_cleanup_required_before_composite_generation"] is False

    print("M12C4_entry_gate_ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
