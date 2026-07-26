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

from sram_layoutgen.openyield_adapter.candidate_spice_generation import (  # noqa: E402
    build_candidate_spice_generation_report,
    format_candidate_spice_generation_markdown,
)


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate candidate SPICE templates and search FreePDK45 device models.")
    parser.add_argument("--repo-root", default=".")
    parser.add_argument("--openram-tech-dir", required=True)
    parser.add_argument("--local-tech-dir", default="technology/freepdk45")
    parser.add_argument("--gen-delay-inv-recovery", default="docs/openyield_gen_delay_inv_netlist_recovery_report.json")
    parser.add_argument("--four-load-plan", default="docs/openyield_four_load_inverter_stage_model_report.json")
    parser.add_argument("--delay-chain-plan", default="docs/openyield_delay_chain_testbench_plan_report.json")
    parser.add_argument("--out-json", default="docs/openyield_candidate_spice_generation_and_pdk_search_report.json")
    parser.add_argument("--out-md", default="docs/openyield_candidate_spice_generation_and_pdk_search_report.md")
    parser.add_argument("--out-graph", default="docs/openyield_candidate_spice_generation_and_pdk_search_graph.json")
    parser.add_argument("--out-dir", default="docs/candidate_spice")
    args = parser.parse_args()

    payload = build_candidate_spice_generation_report(
        resolve_input(args.repo_root),
        Path(args.openram_tech_dir),
        resolve_input(args.local_tech_dir),
        resolve_input(args.gen_delay_inv_recovery),
        resolve_input(args.four_load_plan),
        resolve_input(args.delay_chain_plan),
        resolve_output(args.out_dir),
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
    out_md.write_text(format_candidate_spice_generation_markdown(report), encoding="utf-8", newline="\n")
    out_graph.write_text(json.dumps(graph, ensure_ascii=False, indent=2), encoding="utf-8", newline="\n")
    smoke_assertions(report)
    print(f"Wrote {out_json}")
    print(f"Wrote {out_md}")
    print(f"Wrote {out_graph}")
    print(f"device_model_include_found={report['audit_summary']['device_model_include_found']}")
    print(f"gen_delay_inv_candidate_spice_emitted={report['audit_summary']['gen_delay_inv_candidate_spice_emitted']}")
    return 0


def smoke_assertions(report: dict) -> None:
    s = report["audit_summary"]
    assert s["pdk_model_search_completed"] is True
    assert s["candidate_spice_generation_available"] is True
    assert s["gen_delay_inv_candidate_spice_emitted"] is True
    assert s["delay_chain_symbolic_tb_emitted"] is True
    assert s["device_model_include_found"] is True
    assert s["nmos_vtg_bound"] is True
    assert s["pmos_vtg_bound"] is True
    assert s["needs_model_alias_mapping"] is False
    assert s["can_run_candidate_spice_now"] is False
    assert s["can_run_delay_chain_testbench_now"] is False
    assert s["can_claim_delay_proof_now"] is False
    assert s["can_claim_timing_closure_now"] is False
    assert s["needs_teacher_or_project_provider"] is False
    assert s["can_enter_candidate_spice_syntax_check"] is True
    assert s["can_enter_pvt_corner_definition"] is True
    assert s["can_enter_delay_chain_smoke_simulation"] is False
    assert s["can_enter_physical_timing_closure_now"] is False
    assert s["can_enter_physical_routing_now"] is False
    assert s["can_enter_physical_placement_now"] is False
    assert s["can_generate_time_control_gds_now"] is False
    assert s["can_modify_standalone_now"] is False
    binding = report["device_model_binding_decision"]
    assert binding["can_bind_openyield_model_names_directly"] is True
    assert binding["needs_model_alias_mapping"] is False
    files = {Path(row["path"]).name: row for row in report["generated_candidate_files"]["files"]}
    for name in [
        "gen_delay_inv_candidate.sp",
        "delay_chain_symbolic_tb.sp",
        "delay_chain_measure.inc",
        "delay_chain_corner_placeholder.inc",
        "README.md",
    ]:
        assert files[name]["exists"] is True


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
