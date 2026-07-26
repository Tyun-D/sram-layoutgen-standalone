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

from sram_layoutgen.openyield_adapter.candidate_spice_syntax_check import (  # noqa: E402
    build_candidate_spice_syntax_check_report,
    format_candidate_spice_syntax_check_markdown,
)


def main() -> int:
    parser = argparse.ArgumentParser(description="Check candidate SPICE static syntax and simulator binding.")
    parser.add_argument("--repo-root", default=".")
    parser.add_argument("--candidate-dir", default="docs/candidate_spice")
    parser.add_argument("--openram-tech-dir", required=True)
    parser.add_argument("--pdk-model-dir", required=True)
    parser.add_argument("--out-json", default="docs/openyield_candidate_spice_syntax_check_report.json")
    parser.add_argument("--out-md", default="docs/openyield_candidate_spice_syntax_check_report.md")
    parser.add_argument("--out-graph", default="docs/openyield_candidate_spice_syntax_check_graph.json")
    args = parser.parse_args()

    payload = build_candidate_spice_syntax_check_report(
        resolve_input(args.repo_root),
        resolve_input(args.candidate_dir),
        Path(args.openram_tech_dir),
        Path(args.pdk_model_dir),
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
    out_md.write_text(format_candidate_spice_syntax_check_markdown(report), encoding="utf-8", newline="\n")
    out_graph.write_text(json.dumps(graph, ensure_ascii=False, indent=2), encoding="utf-8", newline="\n")
    smoke_assertions(report)
    print(f"Wrote {out_json}")
    print(f"Wrote {out_md}")
    print(f"Wrote {out_graph}")
    print(f"simulator_found={report['audit_summary']['simulator_found']}")
    print(f"static_spice_check_pass={report['audit_summary']['static_spice_check_pass']}")
    return 0


def smoke_assertions(report: dict) -> None:
    s = report["audit_summary"]
    assert s["candidate_spice_syntax_check_available"] is True
    assert s["pdk_include_binding_available"] is True
    assert s["local_model_include_emitted"] is True
    assert s["static_spice_check_pass"] is True
    assert s["can_claim_delay_proof_now"] is False
    assert s["can_claim_timing_closure_now"] is False
    assert s["can_enter_physical_timing_closure_now"] is False
    assert s["can_enter_physical_routing_now"] is False
    assert s["can_enter_physical_placement_now"] is False
    assert s["can_generate_time_control_gds_now"] is False
    assert s["can_modify_standalone_now"] is False
    if not s["simulator_found"]:
        assert s["syntax_smoke_attempted"] is False
        assert s["can_run_candidate_spice_now"] is False
        assert s["needs_user_simulator_install"] is True


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
