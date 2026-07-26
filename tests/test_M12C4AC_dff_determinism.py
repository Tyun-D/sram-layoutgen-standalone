from __future__ import annotations

import json
from pathlib import Path
import sys

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))


def main() -> None:
    report = json.loads((REPO_ROOT / "outputs/M12C4AC_dff_connectivity_repair/current_supported_config/M12C4AC_deterministic_regeneration_report.json").read_text())
    assert report["deterministic_regeneration_verified"] is True
    assert len(report["canonical_topology_hash"]) == 12


if __name__ == "__main__":
    main()

