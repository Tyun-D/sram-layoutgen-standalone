from __future__ import annotations

import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from sram_layoutgen.openyield_adapter.timing_metadata_consumer import (  # noqa: E402
    emit_consumer_summary,
    get_control_object_status,
    load_candidate_contracts,
)


def main() -> int:
    repo_root = REPO_ROOT
    contracts_csv = repo_root / "docs/mapping/openyield_control_path_candidate_contracts.csv"
    timing_json = repo_root / "docs/openyield_delay_chain_timing_metadata_report.json"
    source_json = repo_root / "docs/openyield_source_provenance_linking_report.json"
    audit_json = repo_root / "docs/openyield_source_linked_timing_metadata_audit_report.json"
    mapping_csv = repo_root / "docs/mapping/openyield_control_timing_mapping.csv"

    contracts = load_candidate_contracts(contracts_csv)
    assert len(contracts) == 7

    contract_by_object = {row.control_object: row for row in contracts}
    assert contract_by_object["PRECHARGE"].candidate_artifact.endswith("precharge_candidate_ngspice.sp")
    assert contract_by_object["PRECHARGE_ENABLE_PATH"].candidate_artifact.endswith("precharge_enable_candidate_tb.sp")
    assert bool(contract_by_object["PRECHARGE"].next_required_action)
    assert bool(contract_by_object["PRECHARGE_ENABLE_PATH"].next_required_action)
    assert all(bool(row.next_required_action) for row in contracts)

    precharge_status = get_control_object_status(
        mapping_csv,
        contracts_csv,
        "PRECHARGE",
    )
    assert precharge_status["mapping_evidence_status"] == "source_linked_candidate_spice_smoke_available"
    assert precharge_status["ready_for_physical_integration"] is False

    summary = emit_consumer_summary(timing_json, source_json, audit_json, mapping_csv)
    assert summary.delay_chain_consumable is True
    assert abs(summary.delay_chain_worst_smoke_delay_s - 2.15738e-10) < 1e-18
    assert summary.gates["can_modify_standalone_now"] is False

    blocked = {
        "PRECHARGE",
        "PRECHARGE_ENABLE_PATH",
        "SENSE_ENABLE_PATH",
        "WRITE_ENABLE_PATH",
        "WORDLINE_ENABLE_PATH",
        "GATED_CLOCK_PATH",
        "DFF_ROW",
    }
    for row in contracts:
        assert row.integration_readiness != "physical_ready"
        assert "no_physical_integration" in row.forbidden_claims
    assert blocked.issubset(contract_by_object.keys())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
