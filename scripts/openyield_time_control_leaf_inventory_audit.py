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

from sram_layoutgen.openyield_adapter.time_control_leaf_inventory import (  # noqa: E402
    build_time_control_leaf_inventory_report,
    format_time_control_leaf_inventory_markdown,
)


def main() -> int:
    parser = argparse.ArgumentParser(description="Readonly TIME/control leaf geometry inventory.")
    parser.add_argument("--repo-root", default=".")
    parser.add_argument("--tech-dir", default="technology/freepdk45")
    parser.add_argument("--asset-inventory", default="docs/openyield_repo_physical_asset_inventory_report.json")
    parser.add_argument("--power-rail-audit", default="docs/openyield_hardcell_power_rail_continuity_report.json")
    parser.add_argument("--out-json", default="docs/openyield_time_control_leaf_inventory_report.json")
    parser.add_argument("--out-md", default="docs/openyield_time_control_leaf_inventory_report.md")
    parser.add_argument("--out-graph", default="docs/openyield_time_control_leaf_inventory_graph.json")
    args = parser.parse_args()

    repo_root = resolve_input(args.repo_root)
    tech_dir = resolve_input(args.tech_dir)
    asset_inventory = resolve_input(args.asset_inventory)
    power_rail_audit = resolve_input(args.power_rail_audit)
    out_json = resolve_output(args.out_json)
    out_md = resolve_output(args.out_md)
    out_graph = resolve_output(args.out_graph)

    payload = build_time_control_leaf_inventory_report(repo_root, tech_dir, asset_inventory, power_rail_audit)
    report = payload["report"]
    graph = payload["graph"]

    out_json.parent.mkdir(parents=True, exist_ok=True)
    out_md.parent.mkdir(parents=True, exist_ok=True)
    out_graph.parent.mkdir(parents=True, exist_ok=True)
    out_json.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8", newline="\n")
    out_md.write_text(format_time_control_leaf_inventory_markdown(report), encoding="utf-8", newline="\n")
    out_graph.write_text(json.dumps(graph, ensure_ascii=False, indent=2), encoding="utf-8", newline="\n")
    smoke_assertions(report)
    print(f"Wrote {out_json}")
    print(f"Wrote {out_md}")
    print(f"Wrote {out_graph}")
    print(f"can_enter_composite_internal_placement_feasibility_audit={report['audit_summary']['can_enter_composite_internal_placement_feasibility_audit']}")
    return 0


def smoke_assertions(report: dict) -> None:
    s = report["audit_summary"]
    assert s["time_control_leaf_bbox_pin_side_inventory_available"] is True
    assert s["can_enter_composite_internal_placement_feasibility_audit"] is True
    assert s["can_enter_legal_placement_readonly_audit"] is True
    assert s["can_enter_physical_placement_now"] is False
    assert s["can_generate_time_control_gds_now"] is False
    assert s["can_modify_standalone_now"] is False
    assert report["precharge_special_section"]["precharge_safe_for_physical_placement"] is False


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
