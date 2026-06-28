from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from sram_layoutgen.openyield_adapter.cell_rail_overlap_eligibility import (  # noqa: E402
    audit_cell_rail_overlap_eligibility,
    classify_cell_rail_overlap,
)


def main() -> int:
    inv = classify_cell_rail_overlap(REPO_ROOT, "gen_inv")
    assert inv.overlap_eligible is True
    assert inv.eligibility_class == "eligible_standard_gate_rail_overlap"
    assert inv.candidate_overlap_depth_um > 0.0

    dff = classify_cell_rail_overlap(REPO_ROOT, "dff")
    assert dff.eligibility_class == "excluded_dff_pending_manual_review"
    assert dff.overlap_eligible is False
    assert dff.unusual_power_related_shapes

    col_mux = classify_cell_rail_overlap(REPO_ROOT, "gen_col_mux")
    assert col_mux.overlap_eligible is False
    assert col_mux.eligibility_class.startswith("blocked")

    report = audit_cell_rail_overlap_eligibility(REPO_ROOT, ["gen_inv", "dff", "gen_col_mux"])
    assert report["cell_rail_overlap_eligibility_audit_available"] is True
    assert report["all_used_cells_classified"] is True
    assert report["dff_excluded_from_vertical_overlap"] is True
    print("openyield_cell_rail_overlap_eligibility_ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
