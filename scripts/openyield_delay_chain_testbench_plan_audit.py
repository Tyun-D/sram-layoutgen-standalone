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

from sram_layoutgen.openyield_adapter.delay_chain_testbench_plan import (  # noqa: E402
    build_delay_chain_testbench_plan_report,
    format_delay_chain_testbench_plan_markdown,
)


def main() -> int:
    parser = argparse.ArgumentParser(description="Readonly DELAY_CHAIN SPICE testbench planning audit.")
    parser.add_argument("--repo-root", default=".")
    parser.add_argument("--tech-dir", default="technology/freepdk45")
    parser.add_argument("--model-recovery", default="docs/openyield_generated_logic_model_recovery_report.json")
    parser.add_argument("--timing-proof-plan", default="docs/openyield_time_control_timing_proof_plan_report.json")
    parser.add_argument("--timing-metadata", default="docs/openyield_time_control_timing_metadata_report.json")
    parser.add_argument("--out-json", default="docs/openyield_delay_chain_testbench_plan_report.json")
    parser.add_argument("--out-md", default="docs/openyield_delay_chain_testbench_plan_report.md")
    parser.add_argument("--out-graph", default="docs/openyield_delay_chain_testbench_plan_graph.json")
    args = parser.parse_args()

    payload = build_delay_chain_testbench_plan_report(
        resolve_input(args.repo_root),
        resolve_input(args.tech_dir),
        resolve_input(args.model_recovery),
        resolve_input(args.timing_proof_plan),
        resolve_input(args.timing_metadata),
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
    out_md.write_text(format_delay_chain_testbench_plan_markdown(report), encoding="utf-8", newline="\n")
    out_graph.write_text(json.dumps(graph, ensure_ascii=False, indent=2), encoding="utf-8", newline="\n")
    smoke_assertions(report)
    print(f"Wrote {out_json}")
    print(f"Wrote {out_md}")
    print(f"Wrote {out_graph}")
    print(f"can_emit_testbench_template_now={report['audit_summary']['can_emit_testbench_template_now']}")
    print(f"can_run_testbench_now={report['audit_summary']['can_run_testbench_now']}")
    return 0


def smoke_assertions(report: dict) -> None:
    s = report["audit_summary"]
    assert s["delay_chain_spice_testbench_plan_available"] is True
    assert s["delay_chain_structure_captured"] is True
    assert s["stage_count_confirmed"] is True
    assert s["four_load_inverter_policy_captured"] is True
    assert s["model_dependencies_identified"] is True
    assert s["measurement_plan_available"] is True
    assert s["corner_plan_available"] is True
    assert s["artifact_contract_available"] is True
    assert s["can_emit_testbench_template_now"] is True
    assert s["can_run_testbench_now"] is False
    assert s["can_claim_delay_proof_now"] is False
    assert s["can_claim_timing_closure_now"] is False
    assert s["can_enter_gen_delay_inv_transistor_netlist_recovery_plan"] is True
    assert s["can_enter_four_load_inverter_stage_model_plan"] is True
    assert s["can_enter_wen_delay_chain_conditional_testbench_plan"] is True
    assert s["can_enter_physical_timing_closure_now"] is False
    assert s["can_enter_physical_routing_now"] is False
    assert s["can_enter_physical_placement_now"] is False
    assert s["can_generate_time_control_gds_now"] is False
    assert s["can_modify_standalone_now"] is False
    structure = report["delay_chain_structure_plan"]
    assert structure["timing_object"] == "DELAY_CHAIN"
    assert structure["stage_count"] == 9
    assert structure["leaf"] == "gen_delay_inv"
    assert structure["load_model_source"] == "source_confirmed_four_load_inverters_per_stage"
    assert structure["requires_replica_path_calibration"] is True
    assert structure["requires_parasitic_estimate"] is True
    assert structure["requires_waveform_check"] is True
    tb = report["spice_testbench_plan"]
    assert tb["leaf_macro"] == "gen_delay_inv"
    assert tb["required_pin_order"] == ["A", "Z", "vdd", "gnd"]
    assert tb["four_load_inverters_per_stage_encoded"] is True
    assert tb["can_emit_testbench_template_now"] is True
    assert tb["can_run_testbench_now"] is False
    assert tb["can_claim_delay_proof_now"] is False
    assert tb["can_claim_timing_closure_now"] is False
    assert report["corner_definition_available"] is False
    assert len(report["per_stage_load_plan"]) == 9
    assert report["next_recommended_proof_task"] == "gen_delay_inv_transistor_netlist_recovery_plan"


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
