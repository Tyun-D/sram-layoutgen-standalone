from __future__ import annotations

import csv
import json
from pathlib import Path


REPO_ROOT = Path("/data1/qujh/work/sram_layoutgen_step45_clean")
L3_TARGETS = [
    "bitcell_array",
    "dummy_array",
    "replica_array",
    "row_decoder",
    "wordline_decoder",
    "decoder_gate_cells",
    "wordline_driver",
    "wordline_driver_gate_cells",
    "column_mux",
    "sense_amp",
    "write_driver",
    "precharge",
    "DELAY_CHAIN",
    "PRECHARGE_ENABLE_PATH",
    "SENSE_ENABLE_PATH",
    "WRITE_ENABLE_PATH",
    "WORDLINE_ENABLE_PATH",
    "GATED_CLOCK_PATH",
    "DFF_ROW",
    "CONTROL_LOGIC",
]
DEFERRED = ["SRAM_TOP", "BANK", "routing_semantics", "power_semantics", "timing_semantics"]


def _load_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def test_no_L3_target_remains_sanity_failed() -> None:
    rows = {row["module"]: row for row in _load_csv(REPO_ROOT / "docs/mapping/openyield_module_gds_inventory.csv")}
    for module in L3_TARGETS:
        assert rows[module]["sanity_check_status"] != "SANITY_FAILED"


def test_every_L3_target_has_at_least_basic_sanity() -> None:
    rows = {row["module"]: row for row in _load_csv(REPO_ROOT / "docs/mapping/openyield_module_gds_inventory.csv")}
    for module in L3_TARGETS:
        assert rows[module]["sanity_check_status"] in {"GDS_BASIC_SANITY_PASSED", "GDS_PARSED_SANITY_PASSED"}


def test_deferred_objects_do_not_block_L3_sanity() -> None:
    rows = {row["module"]: row for row in _load_csv(REPO_ROOT / "docs/mapping/openyield_module_gds_inventory.csv")}
    for module in DEFERRED:
        assert rows[module]["sanity_check_status"] == "NOT_REQUIRED_FOR_CURRENT_SCOPE"


def test_report_gates_and_signoff_claims() -> None:
    report = json.loads((REPO_ROOT / "docs/openyield_L3_module_generator_gds_generation_report.json").read_text(encoding="utf-8"))
    assert report["module_gds_sanity_failed_count"] == 0
    assert set(L3_TARGETS).issubset(set(report["module_gds_basic_sanity_passed_modules"]))
    assert report["can_enter_L4_top_level_assembly"] is True
    assert report["can_claim_full_openyield_gds_now"] is False
    assert report["can_claim_drc_clean_now"] is False
    assert report["can_claim_lvs_clean_now"] is False
    assert report["can_claim_timing_closure_now"] is False
