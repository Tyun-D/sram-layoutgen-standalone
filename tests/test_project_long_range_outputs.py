from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))


def main() -> int:
    subprocess.check_call([sys.executable, "scripts/project_long_range_closure.py"], cwd=REPO_ROOT)

    required = [
        REPO_ROOT / "docs/P0_003_OWNER_CONFIRMATION_RESOLUTION.json",
        REPO_ROOT / "docs/LONG_RANGE_GAP_EXECUTION_MATRIX.csv",
        REPO_ROOT / "docs/FORMAL_SRAM_CONFIG_INVENTORY.csv",
        REPO_ROOT / "docs/PROJECT_CLAIM_POLICY.json",
        REPO_ROOT / "docs/DECODER_PHYSICAL_CLOSURE_AUDIT.json",
        REPO_ROOT / "docs/MULTIBANK_PHYSICAL_FLOW_AUDIT.json",
        REPO_ROOT / "docs/FINAL_FIGURE_AND_TABLE_INDEX.csv",
        REPO_ROOT / "docs/PROJECT_FUTURE_ROADMAP.json",
        REPO_ROOT / "docs/PROJECT_FINAL_TECHNICAL_DRAFT.json",
        REPO_ROOT / "docs/PROJECT_LONG_RANGE_CLOSURE_GATE.json",
    ]
    for path in required:
        assert path.exists(), path

    resolution = json.loads((REPO_ROOT / "docs/P0_003_OWNER_CONFIRMATION_RESOLUTION.json").read_text(encoding="utf-8"))
    assert resolution["status"] == "BLOCKED_EXTERNAL"

    gate = json.loads((REPO_ROOT / "docs/PROJECT_LONG_RANGE_CLOSURE_GATE.json").read_text(encoding="utf-8"))
    assert gate["p1_total"] == 4
    assert gate["p2_total"] == 2
    assert gate["p3_total"] == 1
    assert gate["claim_policy_passed"] is True
    assert gate["no_unapproved_other_team_merge"] is True

    status = json.loads((REPO_ROOT / "docs/PROJECT_CURRENT_STATUS.json").read_text(encoding="utf-8"))
    assert status["p0_003_resolution"] == "BLOCKED_EXTERNAL"
    assert status["claim_policy_passed"] is True
    assert status["decoder_status"] == "BLOCKED_TECHNICAL"

    print("project_long_range_outputs_ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
