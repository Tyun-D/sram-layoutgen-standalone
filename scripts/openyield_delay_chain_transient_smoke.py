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

from sram_layoutgen.openyield_adapter.delay_chain_transient_smoke import (  # noqa: E402
    build_delay_chain_transient_smoke_report,
    format_delay_chain_transient_smoke_markdown,
)


def main() -> int:
    parser = argparse.ArgumentParser(description="Build a delay-chain ngspice transient smoke report for the candidate SPICE.")
    parser.add_argument("--repo-root", default=".")
    parser.add_argument("--candidate-dir", default="docs/candidate_spice")
    parser.add_argument("--out-json", default="docs/openyield_delay_chain_transient_smoke_report.json")
    parser.add_argument("--out-md", default="docs/openyield_delay_chain_transient_smoke_report.md")
    args = parser.parse_args()

    report = build_delay_chain_transient_smoke_report(resolve_input(args.repo_root), resolve_input(args.candidate_dir))
    out_json = resolve_output(args.out_json)
    out_md = resolve_output(args.out_md)
    out_json.parent.mkdir(parents=True, exist_ok=True)
    out_md.parent.mkdir(parents=True, exist_ok=True)
    out_json.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8", newline="\n")
    out_md.write_text(format_delay_chain_transient_smoke_markdown(report), encoding="utf-8", newline="\n")
    smoke_assertions(report)
    print(f"Wrote {out_json}")
    print(f"Wrote {out_md}")
    for key, value in report["audit_summary"].items():
        print(f"{key}={value}")
    return 0


def smoke_assertions(report: dict) -> None:
    s = report["audit_summary"]
    assert s["delay_chain_transient_smoke_available"] is True
    assert s["ngspice_found"] is True
    assert s["model_include_available"] is True
    assert s["transient_deck_generated"] is True
    assert s["transient_attempted"] is True
    assert s["can_claim_delay_proof_now"] is False
    assert s["can_claim_timing_closure_now"] is False
    assert s["can_enter_physical_timing_closure_now"] is False
    assert s["can_enter_physical_routing_now"] is False
    assert s["can_enter_physical_placement_now"] is False
    assert s["can_generate_time_control_gds_now"] is False
    assert s["can_modify_standalone_now"] is False
    if s["transient_run_pass"] and s["rbl_delay_observed"]:
        assert s["can_enter_delay_measurement_refinement"] is True
    else:
        assert s["can_enter_delay_measurement_refinement"] is False


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
