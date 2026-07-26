from __future__ import annotations

import json
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from sram_layoutgen.openyield_adapter.timing_metadata_consumer import get_control_object_status  # noqa: E402


def main() -> int:
    repo_root = REPO_ROOT
    report_path = repo_root / "docs/openyield_precharge_spice_smoke_report.json"
    mapping_csv = repo_root / "docs/mapping/openyield_control_timing_mapping.csv"
    contracts_csv = repo_root / "docs/mapping/openyield_control_path_candidate_contracts.csv"

    report = json.loads(report_path.read_text(encoding="utf-8"))
    gates = report["gates"]
    assert gates["precharge_source_found"] is True
    assert gates["precharge_enb_polarity_inferred"] is True
    assert gates["precharge_candidate_spice_generated"] is True
    assert gates["precharge_ngspice_run_pass"] is True
    assert gates["precharge_bl_observed"] is True
    assert gates["precharge_blb_observed"] is True
    assert gates["precharge_behavior_plausible"] is True
    assert gates["precharge_contract_status_updated"] is True
    assert gates["metadata_consumer_precharge_status_updated"] is True
    assert gates["can_enter_precharge_enable_path_smoke"] is True
    assert gates["can_enter_next_control_path_spice_smoke"] is True
    assert gates["can_modify_standalone_now"] is False

    parse_result = report["parse_result"]
    assert parse_result["bl_final_voltage"] is not None
    assert parse_result["blb_final_voltage"] is not None
    assert parse_result["active_window_end_bl"] > 0.8
    assert parse_result["active_window_end_blb"] > 0.8

    precharge_status = get_control_object_status(mapping_csv, contracts_csv, "PRECHARGE")
    assert precharge_status["mapping_evidence_status"] == "source_linked_candidate_spice_smoke_available"
    assert precharge_status["contract_evidence_status"] == "source_linked_candidate_spice_smoke_available"
    assert precharge_status["ready_for_physical_integration"] is False
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
