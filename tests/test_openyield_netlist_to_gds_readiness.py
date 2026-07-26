from __future__ import annotations

import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from sram_layoutgen.openyield_adapter.netlist_to_gds_readiness import build_readiness_report  # noqa: E402


def main() -> int:
    report = build_readiness_report(
        repo_root=REPO_ROOT,
        openyield_root=REPO_ROOT.parent / "external" / "OpenYield",
        module_coverage_path=REPO_ROOT / "outputs/layout_prototype/hybrid_openyield/module_coverage.json",
    )
    rows = report["matrix_rows"]
    by_module = {row["module"]: row for row in rows}

    assert len(rows) == 25
    assert report["gates"]["netlist_to_gds_readiness_matrix_available"] is True
    assert report["gates"]["module_readiness_rows_count"] == 25
    assert report["gates"]["current_hybrid_gds_available"] is True
    assert by_module["bitcell_array"]["readiness_level"] == "READY_FOR_CURRENT_HYBRID_GDS"
    assert by_module["sense_amp"]["readiness_level"] == "READY_FOR_CURRENT_HYBRID_GDS"
    assert by_module["DELAY_CHAIN"]["readiness_level"] == "READY_FOR_METADATA_CONSUMPTION"
    assert by_module["PRECHARGE"]["readiness_level"] == "CANDIDATE_CONTRACT_ONLY"
    assert by_module["DFF_ROW"]["readiness_level"] == "CANDIDATE_CONTRACT_ONLY"
    assert by_module["decoder"]["readiness_level"] == "PHYSICAL_CELL_EXISTS_NEEDS_PLACEMENT"
    assert by_module["decoder_gate_cells"]["readiness_level"] == "PHYSICAL_PLACED_NEEDS_RAIL_STITCH"
    assert by_module["routing"]["readiness_level"] == "BLOCKED"
    assert report["gates"]["can_claim_full_openyield_gds_now"] is False
    assert report["gates"]["can_claim_drc_clean_now"] is False
    assert report["gates"]["can_claim_lvs_clean_now"] is False
    assert report["gates"]["can_claim_timing_closure_now"] is False
    assert report["gates"]["ready_for_current_hybrid_modules"] == [
        "bitcell_array",
        "dummy_array",
        "replica_array",
        "sense_amp",
        "write_driver",
        "column_mux",
        "wordline_driver",
    ]
    assert report["gates"]["metadata_only_modules"] == ["DELAY_CHAIN"]
    assert report["gates"]["candidate_contract_only_modules"] == [
        "PRECHARGE",
        "PRECHARGE_ENABLE_PATH",
        "SENSE_ENABLE_PATH",
        "WRITE_ENABLE_PATH",
        "WORDLINE_ENABLE_PATH",
        "GATED_CLOCK_PATH",
        "DFF_ROW",
    ]
    assert report["gates"]["missing_physical_implementation_modules"] == []
    assert len(report["blocking_gaps_for_full_openyield_gds"]) >= 7
    assert report["next_action_priority"][0]["target_module"] == "decoder_gate_cells"
    print(json.dumps(report["gates"], ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
