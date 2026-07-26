from __future__ import annotations

import json
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.M12N2_clean_openyield_sram_top import run_m12n2  # noqa: E402


def main() -> int:
    out_dir = REPO_ROOT / "outputs/M12N2_clean_openyield_sram_top/current_supported_config"
    out_json = REPO_ROOT / "docs/M12N2_clean_openyield_sram_top_report.json"
    out_report = REPO_ROOT / "docs/M12N2_clean_openyield_sram_top_report.md"
    report = run_m12n2(
        repo_root=REPO_ROOT,
        openyield_root=Path("/data1/qujh/work/external/OpenYield"),
        status_md=REPO_ROOT / "PROJECT_LAYOUTGEN_OPENYIELD_STATUS.md",
        status_json=REPO_ROOT / "PROJECT_LAYOUTGEN_OPENYIELD_STATUS.json",
        goal_md=REPO_ROOT / "PROJECT_NETLIST_TO_LAYOUT_GOAL.md",
        progress_md=REPO_ROOT / "PROJECT_NETLIST_TO_LAYOUT_PROGRESS.md",
        m12n_report=REPO_ROOT / "docs/M12N_lock_openyield_authoritative_netlist_report.json",
        sample_testbench_netlist=REPO_ROOT / "outputs/M12N_lock_openyield_authoritative_netlist/current_supported_config/sample_openyield_sram_netlist.sp",
        out_dir=out_dir,
        out_json=out_json,
        out_report=out_report,
    )
    assert report["status_file_read"] is True
    assert report["status_file_updated"] is True
    assert report["goal_file_read"] is True
    assert report["goal_file_updated"] is True
    assert report["progress_file_updated"] is True
    assert report["m12n_report_loaded"] is True
    assert report["main_sram_import_passed_after_fix"] is True
    assert report["equivalent_main_sram_import_passed_after_fix"] is True
    assert report["torch_required_for_core_netlist_export"] is False
    assert report["clean_top_extraction_passed"] is True
    assert report["clean_top_contains_independent_stimulus"] is False
    assert report["clean_top_contains_pulse"] is False
    assert report["clean_top_contains_pwl"] is False
    assert report["clean_top_contains_tran"] is False
    assert report["clean_top_contains_measure"] is False
    assert report["all_instance_subcircuits_resolved"] is True
    assert report["all_instance_port_counts_match"] is True
    assert report["graph_spice_instance_count_match"] is True
    assert report["graph_spice_module_count_match"] is True
    assert report["graph_spice_net_count_match"] is True
    assert report["parameter_contract_v1_locked"] is True
    assert report["sample_16x16_generated"] is True
    assert report["sample_64x8_generated"] is True
    assert report["parameter_scaling_verified"] is True
    assert report["time_control_role_status"] == "AMBIGUOUS_REQUIRES_TEAM_CONFIRMATION"
    assert report["time_role_requires_team_confirmation"] is True
    assert report["can_claim_openyield_clean_layout_facing_top_locked"] is True
    assert report["can_claim_parameterized_netlist_v1"] is True
    assert report["can_claim_custom_netlist_driven_layout_generation"] is False
    assert report["recommended_next_stage"] == "M12N2H_REQUEST_TIME_ROLE_CONFIRMATION"
    assert report["can_enter_next_stage_before_human_review"] is False
    for name in [
        "openyield_sram_top_v1.sp",
        "openyield_sram_top_v1_graph.json",
        "openyield_sram_top_v1_modules.csv",
        "openyield_sram_top_v1_instances.csv",
        "openyield_sram_top_v1_nets.csv",
        "openyield_sram_top_v1_pins.csv",
        "openyield_sram_top_v1_16x16.sp",
        "openyield_sram_top_v1_16x16_graph.json",
        "openyield_sram_top_v1_64x8.sp",
        "openyield_sram_top_v1_64x8_graph.json",
        "OPENYIELD_SRAM_SPEC_V1.schema.json",
        "OPENYIELD_SRAM_SPEC_V1.example_16x16.json",
        "OPENYIELD_SRAM_SPEC_V1.example_64x8.json",
        "OPENYIELD_SRAM_SPEC_V1.md",
        "M12N2_testbench_element_classification.csv",
        "M12N2_clean_top_extraction_report.json",
        "M12N2_clean_top_extraction_report.md",
        "M12N2_parameter_scaling_report.json",
        "M12N2_parameter_scaling_report.md",
        "M12N2_control_logic_role_report.json",
        "M12N2_control_logic_role_report.md",
        "M12N2_external_dependency_blockers.md",
        "M12N2_next_stage_decision.json",
        "M12N2_next_stage_decision.md",
        "M12N2_machine_verification_report.json",
        "M12N2_machine_verification_report.md",
    ]:
        assert (out_dir / name).exists(), name
    graph = json.loads((out_dir / "openyield_sram_top_v1_graph.json").read_text(encoding="utf-8"))
    assert graph["top_module"] == "OPENYIELD_SRAM_TOP_V1"
    assert len(graph["pins"]) >= 10
    status = json.loads((REPO_ROOT / "PROJECT_LAYOUTGEN_OPENYIELD_STATUS.json").read_text(encoding="utf-8"))
    assert status["current_stage"] == "M12N2"
    assert status["next_stage"] == "M12N2H_REQUEST_TIME_ROLE_CONFIRMATION"
    assert status["can_enter_next_stage_without_human_review"] is False
    print("M12N2_clean_openyield_sram_top_ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
