from __future__ import annotations

import json
from pathlib import Path
import sys

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))


def main() -> None:
    report = json.loads((REPO_ROOT / "docs/M12C4AC_dff_connectivity_repair_report.json").read_text())
    assert report["can_claim_dff_composite_generated"] is True
    assert report["can_claim_dff_machine_connectivity_verified"] is True
    assert report["can_claim_dff_drc_clean"] is True
    assert report["can_claim_dff_human_verified"] is False
    assert report["can_claim_dff_reusable_for_higher_composition"] is False
    assert report["human_review_required"] is True
    assert report["recommended_next_stage"] == "M12C4ACH_DFF_REPAIRED_VISUAL_REVIEW"


if __name__ == "__main__":
    main()
