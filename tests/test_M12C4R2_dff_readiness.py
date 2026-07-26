from __future__ import annotations

import csv
import json
from pathlib import Path
import sys

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))


def main() -> None:
    report = json.loads((REPO_ROOT / "docs/M12C4R2_dff_source_binding_gate_report.json").read_text(encoding="utf-8"))
    binding_rows = list(csv.DictReader((REPO_ROOT / "outputs/M12C4R2_dff_source_binding_gate/current_supported_config/M12C4R2_dff_instance_binding_matrix.csv").open()))
    diag = json.loads((REPO_ROOT / "outputs/M12C4R2_dff_source_binding_gate/current_supported_config/M12C4R2_diagnostic_evidence_immutability_report.json").read_text(encoding="utf-8"))
    assert len(binding_rows) == 11
    assert sum(1 for row in binding_rows if row["binding_status"] == "APPROVED_EXACT_BINDING") == 11
    assert diag["direct_abutment_drc_marker_count"] == 0
    assert diag["routing_diagnostic_drc_marker_count"] == 0
    assert diag["routing_diagnostic_connectivity_passed"] is True
    assert report["dff_source_topology_locked"] is True
    assert report["dff_child_dependencies_complete"] is True
    assert report["dff_concrete_binding_complete"] is True
    assert report["dff_interface_ready"] is True
    assert report["dff_routing_ready"] is True
    assert report["dff_ready_for_smoke_generation"] is True
    script_text = (REPO_ROOT / "scripts/M12C4R_source_interface_routing_correction.py").read_text(encoding="utf-8")
    assert "dff_concrete_binding_complete = True" not in script_text


if __name__ == "__main__":
    main()
