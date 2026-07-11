from __future__ import annotations

import json
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.M12N2R_correct_time_role import EXPECTED_SHA, run_m12n2r  # noqa: E402


def main() -> int:
    out_dir = REPO_ROOT / "outputs/M12N2R_correct_time_role/current_supported_config"
    out_json = REPO_ROOT / "docs/M12N2R_correct_time_role_report.json"
    out_report = REPO_ROOT / "docs/M12N2R_correct_time_role_report.md"
    report = run_m12n2r(
        repo_root=REPO_ROOT,
        openyield_root=Path("/data1/qujh/work/external/OpenYield"),
        status_md=REPO_ROOT / "PROJECT_LAYOUTGEN_OPENYIELD_STATUS.md",
        status_json=REPO_ROOT / "PROJECT_LAYOUTGEN_OPENYIELD_STATUS.json",
        goal_md=REPO_ROOT / "PROJECT_NETLIST_TO_LAYOUT_GOAL.md",
        progress_md=REPO_ROOT / "PROJECT_NETLIST_TO_LAYOUT_PROGRESS.md",
        m12n2_report_json=REPO_ROOT / "docs/M12N2_clean_openyield_sram_top_report.json",
        m12n2_report_md=REPO_ROOT / "docs/M12N2_clean_openyield_sram_top_report.md",
        m12n2_control_evidence=REPO_ROOT / "docs/mapping/M12N2_control_logic_role_evidence.csv",
        m12n2_blockers=REPO_ROOT / "docs/mapping/M12N2_external_dependency_blockers.csv",
        m12n2_next_stage=REPO_ROOT / "docs/mapping/M12N2_next_stage_decision.csv",
        out_dir=out_dir,
        out_json=out_json,
        out_report=out_report,
    )

    assert report["status_file_read"] is True
    assert report["status_file_updated"] is True
    assert report["goal_file_read"] is True
    assert report["goal_file_updated"] is True
    assert report["progress_file_updated"] is True
    assert report["m12n2_report_loaded"] is True
    assert report["openyield_local_sha"] == EXPECTED_SHA
    assert report["openyield_expected_sha"] == EXPECTED_SHA
    assert report["openyield_version_match"] is True
    assert report["openyield_worktree_clean"] is True
    assert report["readme_subcircuits_role_confirmed"] is True
    assert report["readme_testbenches_role_confirmed"] is True
    assert report["time_source_file_loaded"] is True
    assert report["time_inherits_base_subcircuit"] is True
    assert report["time_contains_physical_gate_transistor_subcircuits"] is True
    assert report["time_contains_address_dff"] is True
    assert report["time_contains_data_dff"] is True
    assert report["time_contains_clock_buffer"] is True
    assert report["time_contains_gated_clock"] is True
    assert report["time_contains_replica_delay_chain"] is True
    assert report["time_generates_wl_en"] is True
    assert report["time_generates_s_en"] is True
    assert report["time_generates_w_en"] is True
    assert report["time_generates_pre"] is True
    assert report["time_factory_source_loaded"] is True
    assert report["time_testbench_callsite_loaded"] is True
    assert report["time_is_testbench_stimulus"] is False
    assert report["time_is_design_subcircuit"] is True
    assert report["time_is_instantiated_in_sram_design_graph"] is True
    assert report["time_outputs_consumed_by_sram_periphery"] is True
    assert report["time_control_role_status_before"] == "AMBIGUOUS_REQUIRES_TEAM_CONFIRMATION"
    assert report["time_control_role_status_after"] == "ON_CHIP_CONTROL_LOGIC"
    assert report["time_role_requires_team_confirmation_before"] is True
    assert report["time_role_requires_team_confirmation_after"] is False
    assert report["openyield_control_logic_netlist_source_locked"] is True
    assert report["openyield_control_logic_physical_implementation_ready"] is False
    assert report["can_claim_openyield_authoritative_netlist_locked"] is True
    assert report["can_claim_parameterized_netlist_v1"] is True
    assert report["can_claim_control_logic_source_locked"] is True
    assert report["can_claim_control_logic_mapping_ready"] is False
    assert report["can_claim_control_logic_physical_ready"] is False
    assert report["can_claim_custom_netlist_driven_layout_generation"] is False
    assert report["blocker_count_before"] == 6
    assert report["blocker_count_after"] == 5
    assert report["resolved_blockers"] == ["M12N2-B01"]
    assert report["remaining_blockers"] == ["M12N2-B02", "M12N2-B03", "M12N2-B04", "M12N2-B05", "M12N2-B07"]
    assert report["recommended_next_stage"] == "M12C_CONTROL_LOGIC_GAP_DEFINITION"
    assert report["next_stage_allowed"] == "M12C_CONTROL_LOGIC_GAP_DEFINITION"
    assert report["can_enter_M12C_after_this_gate"] is True
    assert report["human_review_required"] is False
    assert report["can_enter_next_stage_before_human_review"] is True

    for name in [
        "M12N2R_time_role_correction_report.json",
        "M12N2R_time_role_correction_report.md",
        "M12N2R_time_source_evidence.csv",
        "M12N2R_time_call_chain.csv",
        "M12N2R_corrected_blockers.csv",
        "M12N2R_M12C_entry_gate.json",
        "M12N2R_M12C_entry_gate.md",
    ]:
        assert (out_dir / name).exists(), name

    for path in [
        REPO_ROOT / "docs/M12N2R_correct_time_role_report.json",
        REPO_ROOT / "docs/M12N2R_correct_time_role_report.md",
        REPO_ROOT / "docs/evidence/M12N2R_correct_time_role_summary.md",
        REPO_ROOT / "docs/mapping/M12N2R_time_source_evidence.csv",
        REPO_ROOT / "docs/mapping/M12N2R_time_call_chain.csv",
        REPO_ROOT / "docs/mapping/M12N2R_corrected_external_dependency_blockers.csv",
        REPO_ROOT / "docs/mapping/M12N2R_M12C_entry_gate.csv",
    ]:
        assert path.exists(), path

    status = json.loads((REPO_ROOT / "PROJECT_LAYOUTGEN_OPENYIELD_STATUS.json").read_text(encoding="utf-8"))
    assert status["current_stage"] == "M12N2R"
    assert status["next_stage"] == "M12C_CONTROL_LOGIC_GAP_DEFINITION"
    assert status["can_enter_next_stage_without_human_review"] is True
    assert status["time_control_role_status"] == "ON_CHIP_CONTROL_LOGIC"
    assert status["time_role_requires_team_confirmation"] is False
    print("M12N2R_correct_time_role_ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
