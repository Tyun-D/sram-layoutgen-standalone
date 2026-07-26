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

from sram_layoutgen.openyield_adapter.time_control_routing_obstacle import (  # noqa: E402
    build_time_control_routing_obstacle_report,
    format_time_control_routing_obstacle_markdown,
)


def main() -> int:
    parser = argparse.ArgumentParser(description="Readonly TIME/control routing obstacle audit.")
    parser.add_argument("--repo-root", default=".")
    parser.add_argument("--tech-dir", default="technology/freepdk45")
    parser.add_argument("--legal-placement-readonly", default="docs/openyield_time_control_legal_placement_readonly_report.json")
    parser.add_argument("--composite-feasibility", default="docs/openyield_time_control_composite_feasibility_report.json")
    parser.add_argument("--leaf-inventory", default="docs/openyield_time_control_leaf_inventory_report.json")
    parser.add_argument("--region-refinement", default="docs/openyield_time_control_region_refinement_report.json")
    parser.add_argument("--metadata-closure", default="docs/openyield_time_control_metadata_closure_report.json")
    parser.add_argument("--out-json", default="docs/openyield_time_control_routing_obstacle_report.json")
    parser.add_argument("--out-md", default="docs/openyield_time_control_routing_obstacle_report.md")
    parser.add_argument("--out-graph", default="docs/openyield_time_control_routing_obstacle_graph.json")
    args = parser.parse_args()

    repo_root = resolve_input(args.repo_root)
    tech_dir = resolve_input(args.tech_dir)
    legal_placement_readonly = resolve_input(args.legal_placement_readonly)
    composite_feasibility = resolve_input(args.composite_feasibility)
    leaf_inventory = resolve_input(args.leaf_inventory)
    region_refinement = resolve_input(args.region_refinement)
    metadata_closure = resolve_input(args.metadata_closure)
    out_json = resolve_output(args.out_json)
    out_md = resolve_output(args.out_md)
    out_graph = resolve_output(args.out_graph)

    payload = build_time_control_routing_obstacle_report(
        repo_root,
        tech_dir,
        legal_placement_readonly,
        composite_feasibility,
        leaf_inventory,
        region_refinement,
        metadata_closure,
    )
    report = payload["report"]
    graph = payload["graph"]

    out_json.parent.mkdir(parents=True, exist_ok=True)
    out_md.parent.mkdir(parents=True, exist_ok=True)
    out_graph.parent.mkdir(parents=True, exist_ok=True)
    out_json.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8", newline="\n")
    out_md.write_text(format_time_control_routing_obstacle_markdown(report), encoding="utf-8", newline="\n")
    out_graph.write_text(json.dumps(graph, ensure_ascii=False, indent=2), encoding="utf-8", newline="\n")
    smoke_assertions(report)
    print(f"Wrote {out_json}")
    print(f"Wrote {out_md}")
    print(f"Wrote {out_graph}")
    print(f"routing_proof_available_now={report['audit_summary']['routing_proof_available_now']}")
    return 0


def smoke_assertions(report: dict) -> None:
    s = report["audit_summary"]
    assert s["time_control_routing_obstacle_readonly_audit_available"] is True
    assert s["routing_obstacle_readonly_candidate_available"] is True
    assert s["routing_proof_available_now"] is False
    assert s["can_enter_timing_metadata_inventory"] is True
    assert s["can_enter_routing_proof_planning"] is True
    assert s["can_enter_physical_routing_now"] is False
    assert s["can_enter_physical_placement_now"] is False
    assert s["can_generate_time_control_gds_now"] is False
    assert s["can_modify_standalone_now"] is False
    edge = next(row for row in report["region_crossing_adjacency_audit"] if row["edge_name"] == "GATED_CLK_BAR_TO_WL_EN")
    assert edge["adjacency_known"] is True
    assert edge["routing_proof_available"] is False
    assert report["precharge_routing_exception_audit"]["precharge_rail_continuity_proven"] is False


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
