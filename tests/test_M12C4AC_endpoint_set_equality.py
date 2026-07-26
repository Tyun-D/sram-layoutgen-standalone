from __future__ import annotations

import json
from pathlib import Path
import sys

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))


def main() -> None:
    report = json.loads((REPO_ROOT / "outputs/M12C4AC_dff_connectivity_repair/current_supported_config/M12C4AC_dff_physical_connectivity_report.json").read_text())
    assert report["expected_net_count"] == 13
    assert report["actual_net_component_count"] == 13
    assert report["unexpected_net_merge_count"] == 0
    assert report["missing_expected_endpoint_count"] == 0
    assert report["unexpected_endpoint_count"] == 0
    assert all(row["net_match_status"] == "MATCH" for row in report["per_net"])


if __name__ == "__main__":
    main()

