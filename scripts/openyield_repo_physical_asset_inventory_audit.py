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

from sram_layoutgen.openyield_adapter.repo_physical_asset_inventory import (  # noqa: E402
    build_repo_physical_asset_inventory,
    format_repo_physical_asset_inventory_markdown,
)


def main() -> int:
    parser = argparse.ArgumentParser(description="Readonly repository physical asset inventory for OpenYield/OpenRAM evidence collection.")
    parser.add_argument("--repo-root", default=".")
    parser.add_argument("--out-json", default="docs/openyield_repo_physical_asset_inventory_report.json")
    parser.add_argument("--out-md", default="docs/openyield_repo_physical_asset_inventory_report.md")
    parser.add_argument("--out-graph", default="docs/openyield_repo_physical_asset_inventory_graph.json")
    args = parser.parse_args()

    repo_root = resolve_input(args.repo_root)
    out_json = resolve_output(args.out_json)
    out_md = resolve_output(args.out_md)
    out_graph = resolve_output(args.out_graph)

    payload = build_repo_physical_asset_inventory(repo_root)
    report = payload["report"]
    graph = payload["graph"]

    out_json.parent.mkdir(parents=True, exist_ok=True)
    out_md.parent.mkdir(parents=True, exist_ok=True)
    out_graph.parent.mkdir(parents=True, exist_ok=True)

    out_json.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8", newline="\n")
    out_md.write_text(format_repo_physical_asset_inventory_markdown(report), encoding="utf-8", newline="\n")
    out_graph.write_text(json.dumps(graph, ensure_ascii=False, indent=2), encoding="utf-8", newline="\n")

    smoke_assertions(report, graph)
    print(f"Wrote {out_json}")
    print(f"Wrote {out_md}")
    print(f"Wrote {out_graph}")
    print(f"recommended_next_goal={report['recommended_next_goal']}")
    return 0


def smoke_assertions(report: dict, graph: dict) -> None:
    flags = report["decision_flags"]
    assert flags["repo_physical_asset_inventory_available"] is True
    assert flags["can_modify_standalone_now"] is False
    assert flags["can_generate_time_control_gds_now"] is False
    assert flags["can_enter_physical_placement_now"] is False
    assert any(item["component"] == "standalone" for item in report["layout_writer_routing_standalone_readonly_inventory"]["items"])
    assert any(item["tool_or_deck"] == "drc_deck" for item in report["drc_klayout_verification_inventory"]["items"])
    assert graph["nodes"] and graph["edges"]


def resolve_input(value: str) -> Path:
    path = Path(value)
    if path.is_absolute():
        return path
    candidates = [Path.cwd() / value, STANDALONE_ROOT / value, REPO_ROOT / value]
    for candidate in candidates:
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
