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

from sram_layoutgen.openyield_adapter.gen_delay_inv_netlist_recovery import (  # noqa: E402
    build_gen_delay_inv_netlist_recovery_report,
    format_gen_delay_inv_netlist_recovery_markdown,
)


def main() -> int:
    parser = argparse.ArgumentParser(description="Readonly gen_delay_inv transistor netlist recovery planning audit.")
    parser.add_argument("--repo-root", default=".")
    parser.add_argument("--tech-dir", default="technology/freepdk45")
    parser.add_argument("--delay-chain-plan", default="docs/openyield_delay_chain_testbench_plan_report.json")
    parser.add_argument("--model-recovery", default="docs/openyield_generated_logic_model_recovery_report.json")
    parser.add_argument("--leaf-inventory", default="docs/openyield_time_control_leaf_inventory_report.json")
    parser.add_argument("--out-json", default="docs/openyield_gen_delay_inv_netlist_recovery_report.json")
    parser.add_argument("--out-md", default="docs/openyield_gen_delay_inv_netlist_recovery_report.md")
    parser.add_argument("--out-graph", default="docs/openyield_gen_delay_inv_netlist_recovery_graph.json")
    args = parser.parse_args()

    payload = build_gen_delay_inv_netlist_recovery_report(
        resolve_input(args.repo_root),
        resolve_input(args.tech_dir),
        resolve_input(args.delay_chain_plan),
        resolve_input(args.model_recovery),
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
    out_md.write_text(format_gen_delay_inv_netlist_recovery_markdown(report), encoding="utf-8", newline="\n")
    out_graph.write_text(json.dumps(graph, ensure_ascii=False, indent=2), encoding="utf-8", newline="\n")
    smoke_assertions(report)
    print(f"Wrote {out_json}")
    print(f"Wrote {out_md}")
    print(f"Wrote {out_graph}")
    print(f"can_emit_candidate_subckt_template_now={report['audit_summary']['can_emit_candidate_subckt_template_now']}")
    return 0


def smoke_assertions(report: dict) -> None:
    s = report["audit_summary"]
    assert s["gen_delay_inv_transistor_netlist_recovery_plan_available"] is True
    assert s["source_evidence_found"] is True
    assert s["gds_pin_evidence_found"] is True
    assert s["candidate_subckt_contract_available"] is True
    assert s["candidate_pin_order_available"] is True
    assert s["candidate_pin_order_validated_by_spice"] is False
    assert s["transistor_sizing_known"] is False
    assert s["pdk_device_model_bound"] is False
    assert s["can_emit_candidate_subckt_template_now"] is True
    assert s["can_emit_validated_spice_now"] is False
    assert s["can_enter_four_load_inverter_stage_model_plan"] is True
    assert s["can_enter_delay_chain_testbench_template_contract"] is True
    assert s["can_run_delay_chain_testbench_now"] is False
    assert s["can_claim_delay_proof_now"] is False
    assert s["can_claim_timing_closure_now"] is False
    assert s["can_enter_physical_timing_closure_now"] is False
    assert s["can_enter_physical_routing_now"] is False
    assert s["can_enter_physical_placement_now"] is False
    assert s["can_generate_time_control_gds_now"] is False
    assert s["can_modify_standalone_now"] is False
    gds = report["gds_leaf_evidence"]
    assert gds["recommended_gds_variant"] == "openram_replacements"
    assert gds["candidate_pin_order"] == ["A", "Z", "vdd", "gnd"]
    assert gds["candidate_pin_order_validated_by_spice"] is False
    assert gds["safe_for_validated_spice_generation"] is False
    contract = report["candidate_subckt_contract"]
    assert contract["subckt_name"] == "gen_delay_inv"
    assert contract["candidate_pin_order"] == ["A", "Z", "vdd", "gnd"]
    assert contract["logical_function"] == "inverter / delay inverter"
    assert contract["usable_for_testbench_template"] is True
    assert contract["usable_for_spice_simulation_now"] is False
    assert contract["usable_for_timing_proof_now"] is False
    decision = report["recovery_decision"]
    assert decision["recovery_decision"] == "recoverable_from_generator_source_but_requires_manual_netlist_materialization"
    assert decision["can_emit_candidate_subckt_template_now"] is True
    assert decision["can_emit_validated_spice_now"] is False
    assert decision["can_enter_four_load_inverter_stage_model_plan"] is True
    assert decision["can_enter_delay_chain_testbench_template_contract"] is True
    assert decision["can_run_delay_chain_testbench_now"] is False
    assert decision["can_claim_delay_proof_now"] is False
    assert report["next_recommended_proof_task"] == "four_load_inverter_stage_model_plan"


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
