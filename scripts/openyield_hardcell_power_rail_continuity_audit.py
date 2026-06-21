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

from sram_layoutgen.openyield_adapter.hardcell_power_rail_continuity import (  # noqa: E402
    build_hardcell_power_rail_continuity_report,
    format_hardcell_power_rail_continuity_markdown,
)


def main() -> int:
    parser = argparse.ArgumentParser(description="Readonly hardcell power rail continuity audit.")
    parser.add_argument("--repo-root", default=".")
    parser.add_argument("--tech-dir", default="technology/freepdk45")
    parser.add_argument("--inventory", default="docs/openyield_repo_physical_asset_inventory_report.json")
    parser.add_argument("--out-json", default="docs/openyield_hardcell_power_rail_continuity_report.json")
    parser.add_argument("--out-md", default="docs/openyield_hardcell_power_rail_continuity_report.md")
    parser.add_argument("--out-graph", default="docs/openyield_hardcell_power_rail_continuity_graph.json")
    args = parser.parse_args()

    repo_root = resolve_input(args.repo_root)
    tech_dir = resolve_input(args.tech_dir)
    inventory = resolve_input(args.inventory)
    out_json = resolve_output(args.out_json)
    out_md = resolve_output(args.out_md)
    out_graph = resolve_output(args.out_graph)

    payload = build_hardcell_power_rail_continuity_report(repo_root, tech_dir, inventory)
    report = payload["report"]
    graph = payload["graph"]

    out_json.parent.mkdir(parents=True, exist_ok=True)
    out_md.parent.mkdir(parents=True, exist_ok=True)
    out_graph.parent.mkdir(parents=True, exist_ok=True)
    out_json.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8", newline="\n")
    out_md.write_text(format_hardcell_power_rail_continuity_markdown(report), encoding="utf-8", newline="\n")
    out_graph.write_text(json.dumps(graph, ensure_ascii=False, indent=2), encoding="utf-8", newline="\n")
    smoke_assertions(report)
    print(f"Wrote {out_json}")
    print(f"Wrote {out_md}")
    print(f"Wrote {out_graph}")
    print(f"can_enter_legal_placement_readonly_audit={report['rail_continuity_decision']['can_enter_legal_placement_readonly_audit']}")
    return 0


def smoke_assertions(report: dict) -> None:
    decision = report["rail_continuity_decision"]
    assert decision["hardcell_power_rail_continuity_readonly_audit_available"] is True
    assert decision["can_enter_legal_placement_readonly_audit"] is True
    assert decision["can_enter_physical_placement_now"] is False
    assert decision["can_generate_time_control_gds_now"] is False
    assert decision["can_modify_standalone_now"] is False
    assert any(row["macro_name"] == "gen_precharge" for row in report["gds_power_rail_label_audit"])
    assert any(row["precharge_power_status"] for row in report["precharge_special_decision"])


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
