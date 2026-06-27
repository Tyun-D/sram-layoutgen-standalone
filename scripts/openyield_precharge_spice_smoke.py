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

from sram_layoutgen.openyield_adapter.precharge_spice_smoke import (  # noqa: E402
    build_precharge_smoke_report,
    format_precharge_smoke_report_markdown,
    parse_precharge_log,
    parse_precharge_source,
    run_precharge_smoke,
    update_precharge_status,
    write_precharge_candidate_ngspice,
    write_precharge_smoke_deck,
)


def main() -> int:
    parser = argparse.ArgumentParser(description="Run source-linked ngspice smoke for the OpenYield PRECHARGE candidate.")
    parser.add_argument("--repo-root", default=".")
    parser.add_argument("--openyield-root", required=True)
    parser.add_argument("--candidate-dir", required=True)
    parser.add_argument("--out-json", required=True)
    parser.add_argument("--out-md", required=True)
    args = parser.parse_args()

    repo_root = resolve_input(args.repo_root)
    openyield_root = resolve_input(args.openyield_root)
    candidate_dir = resolve_input(args.candidate_dir)
    out_json = resolve_output(args.out_json)
    out_md = resolve_output(args.out_md)

    source_info = parse_precharge_source(openyield_root)
    candidate_spice = write_precharge_candidate_ngspice(candidate_dir / "precharge_candidate_ngspice.sp", source_info)
    deck = write_precharge_smoke_deck(
        candidate_dir / "precharge_smoke_ngspice.sp",
        repo_root / "docs/candidate_spice/local_model_include_nom_server.inc",
        candidate_spice,
        active_low=source_info["enb_polarity"] == "active_low",
    )
    log = candidate_dir / "precharge_smoke_ngspice.log"
    run_precharge_smoke(deck, log, repo_root)
    parsed = parse_precharge_log(log, active_low=source_info["enb_polarity"] == "active_low")
    pre_report = build_precharge_smoke_report(repo_root, openyield_root, source_info, candidate_spice, deck, log, parsed)
    update_precharge_status(repo_root, pre_report)
    pre_report = build_precharge_smoke_report(repo_root, openyield_root, source_info, candidate_spice, deck, log, parsed)

    out_json.parent.mkdir(parents=True, exist_ok=True)
    out_md.parent.mkdir(parents=True, exist_ok=True)
    out_json.write_text(json.dumps(pre_report, ensure_ascii=False, indent=2), encoding="utf-8", newline="\n")
    out_md.write_text(format_precharge_smoke_report_markdown(pre_report), encoding="utf-8", newline="\n")
    smoke_assertions(pre_report)

    print(f"Wrote {out_json}")
    print(f"Wrote {out_md}")
    for key, value in pre_report["gates"].items():
        print(f"{key}={value}")
    return 0


def smoke_assertions(report: dict) -> None:
    gates = report["gates"]
    assert gates["selected_control_path_spice_smoke_precharge_available"] is True
    assert gates["precharge_source_found"] is True
    assert gates["precharge_ports_recorded"] is True
    assert gates["precharge_enb_polarity_inferred"] is True
    assert gates["precharge_candidate_spice_generated"] is True
    assert gates["precharge_ngspice_deck_generated"] is True
    assert gates["precharge_ngspice_run_attempted"] is True
    assert gates["precharge_ngspice_run_pass"] is True
    assert gates["precharge_bl_observed"] is True
    assert gates["precharge_blb_observed"] is True
    assert gates["precharge_behavior_plausible"] is True
    assert gates["precharge_contract_status_updated"] is True
    assert gates["metadata_consumer_precharge_status_updated"] is True
    assert gates["can_enter_precharge_enable_path_smoke"] is True
    assert gates["can_enter_next_control_path_spice_smoke"] is True
    assert gates["can_enter_guarded_adapter_registry"] is True
    assert gates["can_modify_standalone_now"] is False
    assert gates["can_generate_time_control_gds_now"] is False
    assert gates["can_claim_openyield_full_integration_now"] is False
    assert gates["can_claim_timing_closure_now"] is False


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
