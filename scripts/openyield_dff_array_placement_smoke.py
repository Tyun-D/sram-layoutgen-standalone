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

from sram_layoutgen.openyield_adapter.dff_array_adapter import build_dff_array_adapter_report  # noqa: E402
from sram_layoutgen.openyield_adapter.dff_array_placement import build_dff_array_metadata_plan  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate a metadata-only DFF array placement plan.")
    parser.add_argument("--openyield-root", default="third_party/OpenYield")
    parser.add_argument("--contracts", default="docs/openyield_module_contracts.json")
    parser.add_argument("--tech-dir", default="technology/freepdk45")
    parser.add_argument("--addr-width", type=int, required=True)
    parser.add_argument("--data-width", type=int, required=True)
    parser.add_argument("--origin-x", type=float, default=0.0)
    parser.add_argument("--origin-y", type=float, default=0.0)
    parser.add_argument("--pitch-x", type=float, default=1.0)
    parser.add_argument("--row-gap", type=float, default=1.0)
    parser.add_argument("--out-json", default="docs/openyield_dff_array_placement_report.json")
    parser.add_argument("--out-md", default="docs/openyield_dff_array_placement_report.md")
    args = parser.parse_args()

    adapter_report = build_dff_array_adapter_report(
        resolve_input(args.openyield_root),
        resolve_input(args.contracts),
        resolve_input(args.tech_dir),
    )
    bbox = adapter_report["local_dff_gds_bbox"] or {}
    width = float(bbox.get("x1", 0.0)) - float(bbox.get("x0", 0.0))
    height = float(bbox.get("y1", 0.0)) - float(bbox.get("y0", 0.0))
    plan = build_dff_array_metadata_plan(
        addr_width=args.addr_width,
        data_width=args.data_width,
        origin_x=args.origin_x,
        origin_y=args.origin_y,
        pitch_x=args.pitch_x,
        row_gap=args.row_gap,
        dff_width=width,
        dff_height=height,
    )
    report = {
        "scope": "step6_2_dff_array_metadata_placement_plan",
        "input_args": {
            "addr_width": args.addr_width,
            "data_width": args.data_width,
            "origin_x": args.origin_x,
            "origin_y": args.origin_y,
            "pitch_x": args.pitch_x,
            "row_gap": args.row_gap,
        },
        "adapter_safe_for_metadata_plan": adapter_report["dff_adapter_safe_for_metadata_plan"],
        "safe_for_physical_mapping": adapter_report["safe_for_physical_mapping"],
        "safe_for_shared_rail": False,
        "row_placement_ready": plan["row_placement_readiness"],
        "dff_array_can_enter_metadata_placement": adapter_report["dff_array_can_enter_metadata_placement"],
        "dff_array_can_enter_standalone_placement": False,
        "standalone_modified": False,
        "routing_modified": False,
        "gds_writer_modified": False,
        "address_dff_count": plan["address_dff_count"],
        "data_dff_count": plan["data_dff_count"],
        "placement_count": plan["placement_count"],
        "local_dff_gds_path": adapter_report["local_dff_gds_path"],
        "local_dff_spice_path": adapter_report["local_dff_spice_path"],
        "local_dff_gds_bbox": adapter_report["local_dff_gds_bbox"],
        "placements": plan["placements"],
        "bbox_estimate": plan["bbox_estimate"],
        "pitch_x_legal_for_bbox": plan["pitch_x_legal_for_bbox"],
        "overlap_risk_if_physically_placed": plan["overlap_risk_if_physically_placed"],
        "example_placements": plan["placements"][: min(6, len(plan["placements"]))],
        "notes": [
            "This report is metadata-only and does not connect the plan to standalone placement.",
            "No routing, clock tree, shared rail, or row abutment proof is performed here.",
            "A supplied pitch_x smaller than the DFF bbox width is still reported, but flagged as a physical overlap risk.",
        ],
        "step_6_3_recommendation": (
            "Proceed to control-row floorplan metadata and clock-domain planning without enabling standalone placement."
            if adapter_report["dff_adapter_safe_for_metadata_plan"]
            else "Stop before Step 6.3 because the DFF adapter audit is not safe enough."
        ),
    }

    out_json = resolve_output(args.out_json)
    out_md = resolve_output(args.out_md)
    out_json.parent.mkdir(parents=True, exist_ok=True)
    out_md.parent.mkdir(parents=True, exist_ok=True)
    out_json.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    out_md.write_text(format_markdown(report), encoding="utf-8")
    print(f"Wrote {out_json}")
    print(f"Wrote {out_md}")
    print(
        "placements="
        f"{report['placement_count']} "
        f"metadata_placement={report['dff_array_can_enter_metadata_placement']} "
        f"standalone_placement={report['dff_array_can_enter_standalone_placement']}"
    )
    return 0


def format_markdown(report: dict[str, object]) -> str:
    placements = report["placements"]
    return "\n".join(
        [
            "# OpenYield DFF Array Placement Report",
            "",
            "This is a metadata-only placement plan. It does not change standalone.py, routing, or the GDS writer.",
            "",
            "## Summary",
            "",
            f"- address DFF count: `{report['address_dff_count']}`",
            f"- data DFF count: `{report['data_dff_count']}`",
            f"- placement count: `{report['placement_count']}`",
            f"- safe_for_physical_mapping: `{report['safe_for_physical_mapping']}`",
            f"- safe_for_shared_rail: `{report['safe_for_shared_rail']}`",
            f"- row_placement_ready: `{report['row_placement_ready']}`",
            f"- dff_array_can_enter_metadata_placement: `{report['dff_array_can_enter_metadata_placement']}`",
            f"- dff_array_can_enter_standalone_placement: `{report['dff_array_can_enter_standalone_placement']}`",
            f"- pitch_x_legal_for_bbox: `{report['pitch_x_legal_for_bbox']}`",
            f"- overlap_risk_if_physically_placed: `{report['overlap_risk_if_physically_placed']}`",
            "",
            "## BBox Estimate",
            "",
            f"- local DFF bbox: `{json.dumps(report['local_dff_gds_bbox'], ensure_ascii=False)}`",
            f"- plan bbox: `{json.dumps(report['bbox_estimate'], ensure_ascii=False)}`",
            "",
            "## Example Placements",
            "",
            table(
                ["instance", "array", "bit", "x", "y", "orientation", "d", "clk", "q", "consumer"],
                [
                    [
                        item["instance_name"],
                        item["array_type"],
                        item["bit_index"],
                        item["x"],
                        item["y"],
                        item["orientation"],
                        item["nets"]["d"],
                        item["nets"]["clk"],
                        item["nets"]["q"],
                        item["downstream_consumer"],
                    ]
                    for item in report["example_placements"]
                ],
            ),
            "",
            "## Notes",
            "",
            *[f"- {item}" for item in report["notes"]],
            "",
        ]
    )


def table(headers: list[str], rows: list[list[object]]) -> str:
    lines = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join("---" for _ in headers) + " |",
    ]
    for row in rows:
        lines.append("| " + " | ".join(str(item).replace("|", "\\|").replace("\n", "<br>") for item in row) + " |")
    return "\n".join(lines)


def resolve_input(value: str) -> Path:
    path = Path(value)
    if path.exists():
        return path
    for base in (Path.cwd(), STANDALONE_ROOT, REPO_ROOT):
        candidate = base / value
        if candidate.exists():
            return candidate
    return path


def resolve_output(value: str) -> Path:
    path = Path(value)
    return path if path.is_absolute() else STANDALONE_ROOT / path


if __name__ == "__main__":
    raise SystemExit(main())
