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

from sram_layoutgen.openyield_adapter.generated_logic_model_recovery import (  # noqa: E402
    build_generated_logic_model_recovery_report,
    format_generated_logic_model_recovery_markdown,
)


def main() -> int:
    parser = argparse.ArgumentParser(description="Readonly generated-logic timing model recovery inventory.")
    parser.add_argument("--repo-root", default=".")
    parser.add_argument("--tech-dir", default="technology/freepdk45")
    parser.add_argument("--timing-proof-plan", default="docs/openyield_time_control_timing_proof_plan_report.json")
    parser.add_argument("--timing-metadata", default="docs/openyield_time_control_timing_metadata_report.json")
    parser.add_argument("--asset-inventory", default="docs/openyield_repo_physical_asset_inventory_report.json")
    parser.add_argument("--out-json", default="docs/openyield_generated_logic_model_recovery_report.json")
    parser.add_argument("--out-md", default="docs/openyield_generated_logic_model_recovery_report.md")
    parser.add_argument("--out-graph", default="docs/openyield_generated_logic_model_recovery_graph.json")
    args = parser.parse_args()

    payload = build_generated_logic_model_recovery_report(
        resolve_input(args.repo_root),
        resolve_input(args.tech_dir),
        resolve_input(args.timing_proof_plan),
        resolve_input(args.timing_metadata),
        resolve_input(args.asset_inventory),
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
    out_md.write_text(format_generated_logic_model_recovery_markdown(report), encoding="utf-8", newline="\n")
    out_graph.write_text(json.dumps(graph, ensure_ascii=False, indent=2), encoding="utf-8", newline="\n")
    smoke_assertions(report)
    print(f"Wrote {out_json}")
    print(f"Wrote {out_md}")
    print(f"Wrote {out_graph}")
    print(
        "can_enter_model_characterization_plan="
        f"{report['audit_summary']['can_enter_model_characterization_plan']} "
        "can_enter_delay_chain_testbench_plan="
        f"{report['audit_summary']['can_enter_delay_chain_testbench_plan']}"
    )
    return 0


def smoke_assertions(report: dict) -> None:
    s = report["audit_summary"]
    assert s["generated_logic_model_recovery_inventory_available"] is True
    assert s["all_p0_macros_analyzed"] is True
    assert s["all_repo_model_sources_searched"] is True
    assert s["can_enter_model_characterization_plan"] is True
    assert s["can_enter_timing_proof_now"] is False
    assert s["can_enter_physical_timing_closure_now"] is False
    assert s["can_enter_physical_routing_now"] is False
    assert s["can_enter_physical_placement_now"] is False
    assert s["can_generate_time_control_gds_now"] is False
    assert s["can_modify_standalone_now"] is False
    p0 = {row["macro_name"]: row for row in report["p0_generated_logic_model_inventory"]}
    assert "gen_inv" in p0 and "gen_nand2" in p0 and "gen_delay_inv" in p0
    assert p0["gen_inv"]["gds_exists"] is True
    assert p0["gen_nand2"]["gds_exists"] is True
    assert p0["gen_delay_inv"]["gds_exists"] is True
    assert p0["gen_inv"]["has_usable_spice_now"] is False
    assert p0["gen_nand2"]["has_usable_spice_now"] is False
    assert p0["gen_delay_inv"]["can_claim_timing_proof_now"] is False


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
