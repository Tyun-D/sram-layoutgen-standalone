from __future__ import annotations

import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))


def main() -> int:
    graph = json.loads((REPO_ROOT / "outputs/M12C4_composite_control_cell_generation_plan/current_supported_config/M12C4_composite_dependency_graph.json").read_text())
    report = json.loads((REPO_ROOT / "docs/M12C4_composite_control_cell_generation_plan_report.json").read_text())
    assert report["dependency_graph_acyclic"] is True
    assert report["dependency_graph_cycle_count"] == 0
    assert report["dependency_graph_node_count"] == len(graph["nodes"])
    assert report["dependency_graph_edge_count"] == len(graph["edges"])
    assert any(edge["from"] == "DFF" and edge["to"] in {"Pinv", "PINV", "TransmissionGate"} for edge in graph["edges"])
    print("M12C4_dependency_graph_ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
