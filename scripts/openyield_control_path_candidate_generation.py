from __future__ import annotations

import argparse
import csv
import json
import sys
from dataclasses import asdict
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
STANDALONE_ROOT = SCRIPT_DIR.parent
REPO_ROOT = STANDALONE_ROOT.parents[1]
if str(STANDALONE_ROOT) not in sys.path:
    sys.path.insert(0, str(STANDALONE_ROOT))

from sram_layoutgen.openyield_adapter.control_path_candidate_generation import (  # noqa: E402
    build_wave1_generation,
    format_contracts_markdown,
    format_wave1_report_markdown,
)


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate OpenYield control path candidate contracts wave1.")
    parser.add_argument("--repo-root", default=".")
    parser.add_argument("--openyield-root", required=True)
    parser.add_argument("--out-json", required=True)
    parser.add_argument("--out-md", required=True)
    parser.add_argument("--contracts-csv", required=True)
    parser.add_argument("--contracts-md", required=True)
    args = parser.parse_args()

    repo_root = resolve_input(args.repo_root)
    openyield_root = resolve_input(args.openyield_root)
    out_json = resolve_output(args.out_json)
    out_md = resolve_output(args.out_md)
    contracts_csv = resolve_output(args.contracts_csv)
    contracts_md = resolve_output(args.contracts_md)

    generated = build_wave1_generation(repo_root, openyield_root)
    report = generated["report"]
    contracts = generated["contracts"]

    write_json(out_json, report)
    write_text(out_md, format_wave1_report_markdown(report))
    write_contracts_csv(contracts_csv, contracts)
    write_text(contracts_md, format_contracts_markdown(contracts))
    smoke_assertions(report, contracts)

    print(f"Wrote {out_json}")
    print(f"Wrote {out_md}")
    print(f"Wrote {contracts_csv}")
    print(f"Wrote {contracts_md}")
    for key, value in report["gates"].items():
        print(f"{key}={value}")
    return 0


def smoke_assertions(report: dict, contracts: list) -> None:
    gates = report["gates"]
    assert gates["control_path_candidate_generation_wave1_available"] is True
    assert gates["control_source_scan_completed"] is True
    assert gates["candidate_contracts_generated"] is True
    assert gates["candidate_contracts_table_available"] is True
    assert gates["precharge_source_found"] is True
    assert gates["precharge_candidate_contract_available"] is True
    assert gates["precharge_enable_candidate_contract_available"] is True
    assert gates["sense_enable_candidate_contract_available"] is True
    assert gates["write_enable_candidate_contract_available"] is True
    assert gates["wordline_enable_candidate_contract_available"] is True
    assert gates["gated_clock_candidate_contract_available"] is True
    assert gates["dff_row_candidate_contract_available"] is True
    assert gates["all_blocked_objects_have_next_action"] is True
    assert gates["metadata_consumer_contract_link_available"] is True
    assert gates["can_enter_guarded_adapter_registry"] is True
    assert gates["can_modify_standalone_now"] is False
    assert gates["can_generate_time_control_gds_now"] is False
    assert gates["can_claim_openyield_full_integration_now"] is False
    assert gates["can_claim_timing_closure_now"] is False
    assert len(contracts) == 7


def write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8", newline="\n")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8", newline="\n")


def write_contracts_csv(path: Path, contracts: list) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    rows = [asdict(row) for row in contracts]
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


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
