from __future__ import annotations

import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))


def main() -> int:
    human_review = json.loads((REPO_ROOT / "docs/evidence/M12C3AH_human_visual_review_result.json").read_text())
    current_state = json.loads((REPO_ROOT / "docs/evidence/M12C3A4R_current_qualified_primitive_state.json").read_text())

    assert human_review["schema_version"] == "M12C3A4R_HUMAN_REVIEW_STATE_V1"
    assert human_review["current_stage"] == "M12C3A4R"
    assert "history" in human_review
    assert "current_qualified_state" in human_review
    assert "transmission_gate_in_connected_to_vdd" not in human_review
    assert "transmission_gate_in_connected_to_vss" not in human_review
    assert "duplicate_label_cleanup_required_before_composite_generation" not in human_review

    assert current_state["pinv_human_review_passed"] is True
    assert current_state["transmission_gate_human_review_passed"] is True
    assert current_state["transmission_gate_in_connected_to_vdd"] is False
    assert current_state["transmission_gate_in_connected_to_vss"] is False
    assert current_state["transmission_gate_out_connected_to_vdd"] is False
    assert current_state["transmission_gate_out_connected_to_vss"] is False
    assert current_state["transmission_gate_vdd_vss_short_present"] is False
    assert current_state["transmission_gate_in_out_direct_short_present"] is False
    assert current_state["transmission_gate_ctr_p_metal_accessible"] is True
    assert current_state["transmission_gate_ctr_n_metal_accessible"] is True
    assert current_state["duplicate_label_cleanup_required_before_composite_generation"] is False
    assert current_state["p0_primitives_reusable_for_composition"] is True

    report = json.loads((REPO_ROOT / "docs/M12C3A4R_review_atlas_state_normalization_report.json").read_text())
    assert report["human_review_required"] is False

    print("M12C3A4R_current_state_normalization_ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
