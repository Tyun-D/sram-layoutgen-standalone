from __future__ import annotations

import json
from pathlib import Path
import sys


REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))


def main() -> None:
    report = json.loads((REPO_ROOT / "docs/M12C4R_source_interface_routing_correction_report.json").read_text(encoding="utf-8"))
    assert report["dff_source_topology_locked"] is True
    assert report["dff_child_dependencies_complete"] is True
    assert report["dff_concrete_binding_complete"] is True
    assert report["dff_interface_ready"] is True
    assert report["dff_routing_ready"] is True
    assert report["dff_ready_for_smoke_generation"] is True
    assert report["recommended_next_stage"] == "M12C4A_DFF_COMPOSITE_GENERATION"


if __name__ == "__main__":
    main()
