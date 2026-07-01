from __future__ import annotations

import csv
import json
from pathlib import Path


REPO_ROOT = Path("/data1/qujh/work/sram_layoutgen_step45_clean")


def _load_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def test_L2_outputs_exist() -> None:
    required = [
        REPO_ROOT / "docs/mapping/openyield_placement_rule_matrix.csv",
        REPO_ROOT / "docs/mapping/openyield_placement_rule_matrix.md",
        REPO_ROOT / "docs/mapping/openyield_abutment_rule_matrix.csv",
        REPO_ROOT / "docs/mapping/openyield_abutment_rule_matrix.md",
        REPO_ROOT / "docs/mapping/openyield_rail_rule_matrix.csv",
        REPO_ROOT / "docs/mapping/openyield_rail_rule_matrix.md",
        REPO_ROOT / "docs/mapping/openyield_orientation_policy_matrix.csv",
        REPO_ROOT / "docs/mapping/openyield_orientation_policy_matrix.md",
        REPO_ROOT / "docs/mapping/openyield_pin_access_rule_matrix.csv",
        REPO_ROOT / "docs/mapping/openyield_pin_access_rule_matrix.md",
        REPO_ROOT / "docs/mapping/openyield_module_handoff_rule_matrix.csv",
        REPO_ROOT / "docs/mapping/openyield_module_handoff_rule_matrix.md",
        REPO_ROOT / "technology/freepdk45/openyield_L2_placement_abutment_rule_library.json",
        REPO_ROOT / "docs/openyield_L2_placement_abutment_rule_closure_report.json",
        REPO_ROOT / "docs/openyield_L2_placement_abutment_rule_closure_report.md",
    ]
    missing = [str(path) for path in required if not path.exists()]
    assert not missing, f"Missing L2 outputs: {missing}"


def test_every_L1_required_primitive_has_placement_rule() -> None:
    leaf_rows = _load_csv(REPO_ROOT / "docs/mapping/openyield_leaf_physical_readiness_matrix.csv")
    placement_rows = _load_csv(REPO_ROOT / "docs/mapping/openyield_placement_rule_matrix.csv")
    placement_by_name = {row["object_name"]: row for row in placement_rows if row["object_type"] == "primitive"}
    missing = [row["primitive_name"] for row in leaf_rows if row["primitive_name"] not in placement_by_name]
    assert not missing, f"Missing primitive placement rules: {missing}"


def test_every_row_or_array_object_has_abutment_and_rail_rules() -> None:
    abutment_rows = {row["object_name"]: row for row in _load_csv(REPO_ROOT / "docs/mapping/openyield_abutment_rule_matrix.csv")}
    rail_rows = {row["object_name"]: row for row in _load_csv(REPO_ROOT / "docs/mapping/openyield_rail_rule_matrix.csv")}
    required = [
        "bitcell",
        "dummy_cell",
        "replica_cell",
        "inv",
        "delay_inv",
        "nand2",
        "nand3",
        "and2",
        "and3",
        "buffer",
        "decoder_leaf_gate",
        "wordline_decoder_leaf_gate",
        "wordline_driver_leaf_gate",
        "enable_path_leaf_gate",
        "gated_clock_leaf_gate",
        "control_logic_leaf_gate",
        "precharge_cell",
        "sense_amp",
        "write_driver",
        "column_mux",
        "wordline_driver",
        "dff_cell",
    ]
    assert all(name in abutment_rows for name in required)
    assert all(name in rail_rows for name in required)


def test_precharge_pin_access_rule_closed() -> None:
    pin_rows = {row["object_name"]: row for row in _load_csv(REPO_ROOT / "docs/mapping/openyield_pin_access_rule_matrix.csv")}
    precharge = pin_rows["precharge_cell"]
    assert precharge["pin_access_rule_status"] == "PIN_ACCESS_RULE_CLOSED"
    assert precharge["pin_geometry_known"] == "True"


def test_storage_orientation_policy_contains_alternating_mx_r0() -> None:
    rows = {row["object_name"]: row for row in _load_csv(REPO_ROOT / "docs/mapping/openyield_orientation_policy_matrix.csv")}
    for name in ["bitcell", "dummy_cell", "replica_cell"]:
        assert "alternating_MX_R0" in rows[name]["recommended_policy"]


def test_gate_row_policy_contains_same_row_abut() -> None:
    placement_rows = {row["object_name"]: row for row in _load_csv(REPO_ROOT / "docs/mapping/openyield_placement_rule_matrix.csv")}
    for name in ["inv", "nand2", "delay_inv", "decoder_leaf_gate", "enable_path_leaf_gate"]:
        assert "same_row_abut" in placement_rows[name]["placement_strategy"]


def test_module_handoff_covers_all_L3_targets() -> None:
    handoff_rows = {row["module"]: row for row in _load_csv(REPO_ROOT / "docs/mapping/openyield_module_handoff_rule_matrix.csv")}
    required = [
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
        "SRAM_TOP",
        "BANK",
    ]
    missing = [name for name in required if name not in handoff_rows]
    assert not missing, f"Missing module handoff rows: {missing}"


def test_report_gates_exist_and_signoff_claims_remain_false() -> None:
    report = json.loads((REPO_ROOT / "docs/openyield_L2_placement_abutment_rule_closure_report.json").read_text(encoding="utf-8"))
    required_keys = [
        "L2_placement_abutment_rule_closure_available",
        "placement_rule_matrix_available",
        "abutment_rule_matrix_available",
        "rail_rule_matrix_available",
        "orientation_policy_matrix_available",
        "pin_access_rule_matrix_available",
        "module_handoff_rule_matrix_available",
        "L2_rule_library_available",
        "placement_rule_rows_count",
        "abutment_rule_rows_count",
        "rail_rule_rows_count",
        "orientation_policy_rows_count",
        "pin_access_rule_rows_count",
        "module_handoff_rows_count",
        "objects_with_closed_placement_rules",
        "objects_with_closed_abutment_rules",
        "objects_with_closed_rail_rules",
        "objects_with_closed_orientation_policies",
        "objects_with_closed_pin_access_rules",
        "modules_can_enter_L3_standalone_module_gds",
        "modules_blocked_from_L3_standalone_module_gds",
        "remaining_L2_blockers",
        "remaining_L2_blockers_count",
        "can_claim_L2_placement_abutment_rules_closed_now",
        "can_enter_L3_module_gds_generation",
        "can_enter_L4_top_level_assembly",
        "can_claim_full_openyield_gds_now",
        "can_claim_drc_clean_now",
        "can_claim_lvs_clean_now",
        "can_claim_timing_closure_now",
    ]
    for key in required_keys:
        assert key in report, f"Missing report key: {key}"
    assert report["can_claim_full_openyield_gds_now"] is False
    assert report["can_claim_drc_clean_now"] is False
    assert report["can_claim_lvs_clean_now"] is False
