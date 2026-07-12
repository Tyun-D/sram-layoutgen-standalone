from __future__ import annotations

import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))


def main() -> int:
    out_root = REPO_ROOT / "outputs/M12C4_composite_control_cell_generation_plan/current_supported_config"
    assert not list(out_root.rglob("*.gds"))
    report = json.loads((REPO_ROOT / "docs/M12C4_composite_control_cell_generation_plan_report.json").read_text())
    assert report["gds_generated_in_M12C4"] is False
    assert report["can_claim_composite_control_cell_generated"] is False
    print("M12C4_no_gds_generated_ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
