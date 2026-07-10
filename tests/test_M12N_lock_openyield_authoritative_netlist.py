from __future__ import annotations

import json
from pathlib import Path


REPO_ROOT = Path("/data1/qujh/work/sram_layoutgen_step45_clean")
REPORT_PATH = REPO_ROOT / "docs" / "M12N_lock_openyield_authoritative_netlist_report.json"


def _load_report() -> dict:
    return json.loads(REPORT_PATH.read_text(encoding="utf-8"))


def test_m12n_report_exists() -> None:
    assert REPORT_PATH.exists(), f"missing report: {REPORT_PATH}"


def test_m12n_required_status_flags() -> None:
    report = _load_report()
    assert report["status_file_read"] is True
    assert report["status_file_updated"] is True
    assert report["goal_file_read"] is True
    assert report["goal_file_updated"] is True
    assert report["progress_file_updated"] is True
    assert report["m12o_report_loaded"] is True
    assert report["openyield_root_found"] is True
    assert report["openyield_candidate_files_loaded"] is True
    assert report["file_role_classification_completed"] is True
    assert report["entrypoint_callgraph_generated"] is True
    assert report["parameter_interface_extracted"] is True
    assert report["sram_top_coverage_matrix_generated"] is True
    assert report["control_logic_source_matrix_generated"] is True


def test_m12n_authority_decision() -> None:
    report = _load_report()
    assert report["authoritative_netlist_lock_status"] == "PARTIAL_SUBCIRCUIT_LIBRARY_ONLY"
    assert report["authoritative_netlist_type"] == "TESTBENCH_BACKED_PARAMETERIZED_SPICE_GENERATOR"
    assert report["authoritative_entrypoint"] == "sram_compiler/testbenches/sram_6t_core_testbench.py"
    assert report["authoritative_top_class_or_function"] == "Sram6TCoreTestbench.create_testbench"
    assert report["authoritative_output_format"] == "PySpice Circuit rendered to SPICE testbench netlist (.sp)"
    assert report["openyield_single_authoritative_netlist_proven"] is False
    assert report["openyield_parameterized_netlist_generator_proven"] is True
    assert report["openyield_complete_sram_top_proven"] is False
    assert report["openyield_control_logic_source_locked"] is True


def test_m12n_sample_netlist_generation() -> None:
    report = _load_report()
    assert report["sample_netlist_generation_attempted"] is True
    assert report["sample_netlist_generation_passed"] is True
    sample_path = REPO_ROOT / report["sample_netlist_path"]
    assert sample_path.exists(), f"missing sample netlist: {sample_path}"
    text = sample_path.read_text(encoding="utf-8")
    assert ".title SRAM_6T_CORE_" in text
    assert ".subckt TIME" in text
    assert "WORDLINEDRIVER" in text


def test_m12n_parameterization_and_claims() -> None:
    report = _load_report()
    assert report["parameterization_supported"] is True
    for key in ["num_rows", "num_cols", "choose_columnmux", "corner", "temperature", "sram_cell_type", "control_timing_parameters"]:
        assert key in report["supported_parameters"]
    for key in ["word_size", "num_words", "mux_ratio", "tech"]:
        assert key in report["partial_parameters"]
    assert "words_per_row" in report["unknown_parameters"]
    assert report["custom_netlist_driven_generation_readiness"] == "NOT_READY_TESTBENCH_GENERATOR_ONLY"
    assert report["external_dependency_blockers_count"] >= 4
    assert report["can_claim_openyield_authoritative_netlist_locked"] is False
    assert report["can_claim_custom_netlist_driven_layout_generation"] is False
    assert report["can_claim_drc_clean"] is False
    assert report["can_claim_lvs_clean"] is False
    assert report["can_claim_signoff_ready"] is False


def test_m12n_next_stage() -> None:
    report = _load_report()
    assert report["recommended_next_stage"] == "M12C_CONTROL_LOGIC_GAP_DEFINITION"
    assert "control logic" in report["recommended_next_stage_reason"].lower()
    assert report["remaining_M12N_blockers_count"] == 4
    assert report["human_review_required"] is False
    assert report["can_enter_next_stage_before_human_review"] is True


def main() -> None:
    test_m12n_report_exists()
    test_m12n_required_status_flags()
    test_m12n_authority_decision()
    test_m12n_sample_netlist_generation()
    test_m12n_parameterization_and_claims()
    test_m12n_next_stage()


if __name__ == "__main__":
    main()
