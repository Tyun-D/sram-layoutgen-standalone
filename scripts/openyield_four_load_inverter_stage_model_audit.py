from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


SCRIPT_DIR = Path(__file__).resolve().parent
STANDALONE_ROOT = SCRIPT_DIR.parent
REPO_ROOT = STANDALONE_ROOT.parents[1]
if str(STANDALONE_ROOT) not in sys.path:
    sys.path.insert(0, str(STANDALONE_ROOT))

from sram_layoutgen.openyield_adapter.four_load_inverter_stage_model import (  # noqa: E402
    build_four_load_inverter_stage_model_report,
    format_four_load_inverter_stage_model_markdown,
)


def main() -> int:
    parser = argparse.ArgumentParser(description="Readonly DELAY_CHAIN four-load inverter stage model planning audit.")
    parser.add_argument("--repo-root", default=".")
    parser.add_argument("--tech-dir", default="technology/freepdk45")
    parser.add_argument("--gen-delay-inv-recovery", default="docs/openyield_gen_delay_inv_netlist_recovery_report.json")
    parser.add_argument("--delay-chain-plan", default="docs/openyield_delay_chain_testbench_plan_report.json")
    parser.add_argument("--leaf-inventory", default="docs/openyield_time_control_leaf_inventory_report.json")
    parser.add_argument("--out-json", default="docs/openyield_four_load_inverter_stage_model_report.json")
    parser.add_argument("--out-md", default="docs/openyield_four_load_inverter_stage_model_report.md")
    parser.add_argument("--out-graph", default="docs/openyield_four_load_inverter_stage_model_graph.json")
    args = parser.parse_args()

    payload = build_four_load_inverter_stage_model_report(
        resolve_input(args.repo_root),
        resolve_input(args.tech_dir),
        resolve_input(args.gen_delay_inv_recovery),
        resolve_input(args.delay_chain_plan),
        resolve_input(args.leaf_inventory),
    )
    report = payload["report"]
    graph = payload["graph"]

    out_json = resolve_output(args.out_json)
    out_md = resolve_output(args.out_md)
    out_graph = resolve_output(args.out_graph)
    out_json.parent.mkdir(parents=True, exist_ok=True)
    out_md.parent.mkdir(parents=True, exist_ok=True)
    out_graph.parent.mkdir(parents=True, exist_ok=True)
    out_json.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8", newline="\n")
    out_md.write_text(format_four_load_inverter_stage_model_markdown(report), encoding="utf-8", newline="\n")
    out_graph.write_text(json.dumps(graph, ensure_ascii=False, indent=2), encoding="utf-8", newline="\n")
    smoke_assertions(report)
    print(f"Wrote {out_json}")
    print(f"Wrote {out_md}")
    print(f"Wrote {out_graph}")
    print(f"can_emit_symbolic_load_testbench_template_now={report['audit_summary']['can_emit_symbolic_load_testbench_template_now']}")
    print(f"can_run_delay_chain_testbench_now={report['audit_summary']['can_run_delay_chain_testbench_now']}")
    return 0


def smoke_assertions(report: dict) -> None:
    s = report["audit_summary"]
    assert s["four_load_inverter_stage_model_plan_available"] is True
    assert s["source_four_load_pattern_found"] is True
    assert s["load_count_per_stage_confirmed"] is True
    assert s["all_stage_load_contracts_available"] is True
    assert s["load_inverter_binding_decision_available"] is True
    assert s["load_capacitance_quantified"] is False
    assert s["load_pin_order_validated_by_spice"] is False
    assert s["can_emit_symbolic_load_testbench_template_now"] is True
    assert s["can_run_delay_chain_testbench_now"] is False
    assert s["can_claim_delay_proof_now"] is False
    assert s["can_claim_timing_closure_now"] is False
    assert s["can_enter_delay_chain_testbench_template_contract"] is True
    assert s["can_enter_pvt_corner_definition_plan"] is True
    assert s["can_enter_replica_load_calibration_plan"] is True
    assert s["can_enter_wen_delay_chain_conditional_testbench_plan"] is True
    assert s["can_enter_physical_timing_closure_now"] is False
    assert s["can_enter_physical_routing_now"] is False
    assert s["can_enter_physical_placement_now"] is False
    assert s["can_generate_time_control_gds_now"] is False
    assert s["can_modify_standalone_now"] is False
    assert report["load_inverter_same_as_delay_stage_source"] is True
    assert report["load_count_source_confirmed"] is True
    assert report["load_capacitance_quantified"] is False
    assert report["four_load_count_known"] is True
    assert report["four_load_capacitance_value_known"] is False
    assert report["requires_characterization_or_cap_estimation"] is True
    candidates = {row["candidate_name"]: row for row in report["load_inverter_candidate_binding_comparison"]}
    assert candidates["same_source_Pinv_as_delay_stage"]["recommended_for_planning"] is True
    assert candidates["same_source_Pinv_as_delay_stage"]["recommended_for_simulation_now"] is False
    assert candidates["symbolic_inverter_load_only"]["recommended_for_planning"] is True
    assert candidates["symbolic_inverter_load_only"]["recommended_for_simulation_now"] is False
    assert candidates["gen_inv_openram_replacement"]["recommended_for_planning"] is False
    assert len(report["per_stage_load_model_contract"]) == 9
    for row in report["per_stage_load_model_contract"]:
        assert row["load_instance_count"] == 4
        assert row["load_model_type"] == "four_parallel_inverter_gate_loads"
        assert row["load_capacitance_known"] is False
        assert row["safe_for_testbench_template"] is True
        assert row["safe_for_simulation_now"] is False
    spice = report["spice_template_implication"]
    assert spice["can_emit_template_with_symbolic_loads"] is True
    assert spice["can_run_template_now"] is False
    assert spice["floating_load_outputs_allowed"] is True
    assert report["next_recommended_proof_task"] == "delay_chain_testbench_template_contract"


def resolve_input(value: str) -> Path:
    path = Path(value)
    if path.is_absolute():
        return path
    for base in (Path.cwd(), STANDALONE_ROOT, REPO_ROOT):
        candidate = base / value
        if candidate.exists():
            return candidate
    return Path.cwd() / value


def resolve_output(value: str) -> Path:
    path = Path(value)
    if path.is_absolute():
        return path
    if Path.cwd().resolve() == REPO_ROOT.resolve():
        return STANDALONE_ROOT / value
    return Path.cwd() / value


if __name__ == "__main__":
    raise SystemExit(main())
