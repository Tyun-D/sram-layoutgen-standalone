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

from sram_layoutgen.openyield_adapter.timing_metadata_consumer import (  # noqa: E402
    emit_consumer_summary,
    summary_to_dict,
)


def main() -> int:
    parser = argparse.ArgumentParser(description="Run smoke validation for the OpenYield timing metadata consumer adapter.")
    parser.add_argument("--repo-root", default=".")
    parser.add_argument("--timing-json", required=True)
    parser.add_argument("--source-json", required=True)
    parser.add_argument("--mapping-csv", required=True)
    parser.add_argument("--out-json", required=True)
    parser.add_argument("--out-md", required=True)
    args = parser.parse_args()

    timing_json = resolve_input(args.timing_json)
    source_json = resolve_input(args.source_json)
    mapping_csv = resolve_input(args.mapping_csv)
    audit_json = resolve_input("docs/openyield_source_linked_timing_metadata_audit_report.json")
    out_json = resolve_output(args.out_json)
    out_md = resolve_output(args.out_md)

    summary = emit_consumer_summary(timing_json, source_json, audit_json, mapping_csv)
    payload = summary_to_dict(summary)
    write_json(out_json, payload)
    write_text(out_md, format_markdown(payload))
    smoke_assertions(payload)

    print(f"Wrote {out_json}")
    print(f"Wrote {out_md}")
    for key, value in payload["gates"].items():
        print(f"{key}={value}")
    print(f"ready_objects={','.join(payload['ready_objects'])}")
    print(f"blocked_objects={','.join(payload['blocked_objects'])}")
    return 0


def format_markdown(payload: dict) -> str:
    return "\n".join([
        "# OpenYield Timing Metadata Consumer Smoke Report",
        "",
        "## Ready Objects",
        "",
        "```json",
        json.dumps(payload["ready_objects"], ensure_ascii=False, indent=2),
        "```",
        "",
        "## Blocked Objects",
        "",
        "```json",
        json.dumps(payload["blocked_objects"], ensure_ascii=False, indent=2),
        "```",
        "",
        "## Delay Chain Summary",
        "",
        "```json",
        json.dumps({
            "delay_chain_consumable": payload["delay_chain_consumable"],
            "delay_chain_worst_smoke_delay_s": payload["delay_chain_worst_smoke_delay_s"],
            "delay_chain_worst_corner": payload["delay_chain_worst_corner"],
            "delay_chain_corner_table": payload["delay_chain_corner_table"],
            "metadata_consumer_api_available": payload["metadata_consumer_api_available"],
            "next_adapter_action": payload["next_adapter_action"],
            "forbidden_actions": payload["forbidden_actions"],
        }, ensure_ascii=False, indent=2),
        "```",
        "",
        "## Gates",
        "",
        "```json",
        json.dumps(payload["gates"], ensure_ascii=False, indent=2),
        "```",
    ])


def smoke_assertions(payload: dict) -> None:
    gates = payload["gates"]
    assert gates["metadata_consumer_adapter_available"] is True
    assert gates["metadata_consumer_smoke_pass"] is True
    assert gates["delay_chain_metadata_loaded"] is True
    assert gates["delay_chain_source_linked"] is True
    assert gates["delay_chain_ready_for_metadata_consumption"] is True
    assert gates["delay_chain_ready_for_physical_integration"] is False
    assert gates["blocked_control_objects_recorded"] is True
    assert gates["control_mapping_loaded"] is True
    assert gates["consumer_api_ready"] is True
    assert gates["can_enter_control_path_candidate_generation"] is True
    assert gates["can_enter_guarded_adapter_integration"] is True
    assert gates["can_modify_standalone_now"] is False
    assert gates["can_generate_time_control_gds_now"] is False
    assert gates["can_claim_openyield_full_integration_now"] is False
    assert gates["can_claim_timing_closure_now"] is False
    assert abs(payload["delay_chain_worst_smoke_delay_s"] - 2.15738e-10) < 1e-18
    assert payload["delay_chain_worst_corner"] == "ss"


def write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8", newline="\n")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8", newline="\n")


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
