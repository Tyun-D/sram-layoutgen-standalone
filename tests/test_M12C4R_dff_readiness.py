from __future__ import annotations

import json
from pathlib import Path
import sys


REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))


def main() -> None:
    coverage = json.loads(
        (
            REPO_ROOT
            / "outputs/M12C4R_source_interface_routing_correction/current_supported_config/M12C4R_source_exact_connection_coverage_report.json"
        ).read_text(encoding="utf-8")
    )
    routing = json.loads(
        (
            REPO_ROOT
            / "outputs/M12C4R_source_interface_routing_correction/current_supported_config/M12C4R_routing_backend_execution_report.json"
        ).read_text(encoding="utf-8")
    )
    interface = json.loads(
        (
            REPO_ROOT
            / "outputs/M12C4R_source_interface_routing_correction/current_supported_config/M12C4R_interface_candidate_drc_report.json"
        ).read_text(encoding="utf-8")
    )
    readiness = json.loads(
        (
            REPO_ROOT
            / "outputs/M12C4R_source_interface_routing_correction/current_supported_config/M12C4R_dff_readiness_report.json"
        ).read_text(encoding="utf-8")
    )
    assert coverage["dff_child_instance_call_count"] == 11
    assert coverage["dff_net_connection_row_count"] == 52
    assert coverage["dff_pinv_instance_count"] == 7
    assert coverage["dff_transmission_gate_instance_count"] == 4
    assert interface["direct_abutment_drc_passed"] is True
    assert routing["route_drc_marker_count"] == 0
    assert routing["routing_backend_execution_test_passed"] is True
    assert readiness["dff_source_topology_locked"] is True
    assert readiness["dff_child_dependencies_complete"] is True
    assert readiness["dff_interface_ready"] is True
    assert readiness["dff_routing_ready"] is True


if __name__ == "__main__":
    main()
