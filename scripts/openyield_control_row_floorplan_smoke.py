from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


SCRIPT_DIR = Path(__file__).resolve().parent
STANDALONE_ROOT = SCRIPT_DIR.parent
REPO_ROOT = STANDALONE_ROOT.parents[1]
if str(STANDALONE_ROOT) not in sys.path:
    sys.path.insert(0, str(STANDALONE_ROOT))

from sram_layoutgen.openyield_adapter.control_row_floorplan import build_control_row_floorplan  # noqa: E402
from sram_layoutgen.openyield_adapter.dff_array_adapter import build_dff_array_adapter_report  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate a metadata-only OpenYield control-row floorplan report.")
    parser.add_argument("--openyield-root", default="third_party/OpenYield")
    parser.add_argument("--contracts", default="docs/openyield_module_contracts.json")
    parser.add_argument("--tech-dir", default="technology/freepdk45")
    parser.add_argument("--addr-width", type=int, required=True)
    parser.add_argument("--data-width", type=int, required=True)
    parser.add_argument("--origin-x", type=float, default=0.0)
    parser.add_argument("--origin-y", type=float, default=0.0)
    parser.add_argument("--pitch-policy", choices=("input_pitch", "bbox_width", "bbox_width_plus_margin"), default="bbox_width")
    parser.add_argument("--pitch-x", type=float)
    parser.add_argument("--pitch-margin", type=float, default=0.0)
    parser.add_argument("--row-gap-policy", choices=("bbox_height", "bbox_height_plus_margin", "explicit_gap"), default="bbox_height")
    parser.add_argument("--row-gap", type=float)
    parser.add_argument("--row-gap-margin", type=float, default=0.0)
    parser.add_argument("--out-json", default="docs/openyield_control_row_floorplan_report.json")
    parser.add_argument("--out-md", default="docs/openyield_control_row_floorplan_report.md")
    args = parser.parse_args()

    adapter = build_dff_array_adapter_report(
        resolve_input(args.openyield_root),
        resolve_input(args.contracts),
        resolve_input(args.tech_dir),
    )
    bbox = adapter["local_dff_gds_bbox"]
    dff_width = float(bbox["x1"]) - float(bbox["x0"])
    dff_height = float(bbox["y1"]) - float(bbox["y0"])

    floorplan = build_control_row_floorplan(
        addr_width=args.addr_width,
        data_width=args.data_width,
        origin_x=args.origin_x,
        origin_y=args.origin_y,
        dff_width=dff_width,
        dff_height=dff_height,
        pitch_policy=args.pitch_policy,
        row_gap_policy=args.row_gap_policy,
        input_pitch_x=args.pitch_x,
        explicit_row_gap=args.row_gap,
        pitch_margin=args.pitch_margin,
        row_gap_margin=args.row_gap_margin,
    )
    pitch1_check = build_control_row_floorplan(
        addr_width=args.addr_width,
        data_width=args.data_width,
        origin_x=args.origin_x,
        origin_y=args.origin_y,
        dff_width=dff_width,
        dff_height=dff_height,
        pitch_policy="input_pitch",
        row_gap_policy="bbox_height",
        input_pitch_x=1.0,
    )
    flattened_placements = flatten_placements(
        floorplan["placement_plan"]["placements"],
        physical_pitch_legal=floorplan["pitch_x_legal_for_bbox"],
    )

    report = {
        "scope": "step6_3_openyield_control_row_floorplan",
        "standalone_modified": False,
        "routing_modified": False,
        "gds_writer_modified": False,
        "addr_width": args.addr_width,
        "data_width": args.data_width,
        "local_dff_bbox": bbox,
        "local_dff_bbox_dimensions": {
            "width": dff_width,
            "height": dff_height,
        },
        "recommended_pitch_x": floorplan["recommended_pitch_x"],
        "recommended_row_height": floorplan["recommended_row_height"],
        "recommended_row_gap": floorplan["recommended_row_gap"],
        "recommended_pitch_avoids_bbox_overlap": floorplan["recommended_pitch_avoids_bbox_overlap"],
        "selected_pitch_policy": args.pitch_policy,
        "selected_row_gap_policy": args.row_gap_policy,
        "selected_pitch_x": floorplan["chosen_pitch_x"],
        "selected_row_gap": floorplan["chosen_row_gap"],
        "row_summaries": [floorplan["addr_row"], floorplan["data_row"]],
        "addr_dff_row_summary": floorplan["addr_row"],
        "data_dff_row_summary": floorplan["data_row"],
        "placement_count": len(flattened_placements),
        "placements": flattened_placements,
        "physical_pitch_legality": floorplan["pitch_x_legal_for_bbox"],
        "overlap_risk": floorplan["overlap_risk_if_physically_placed"],
        "clock_domain_metadata": floorplan["clock_domain_metadata"],
        "relative_placement_hints": floorplan["relative_placement_hints"],
        "safe_for_metadata_floorplan": floorplan["safe_for_metadata_floorplan"] and adapter["dff_adapter_safe_for_metadata_plan"],
        "pitch_recommendation_available": floorplan["pitch_recommendation_available"],
        "can_enter_physical_row_placement": False,
        "can_enter_standalone_control_placement": False,
        "adapter_safe_for_metadata_plan": adapter["dff_adapter_safe_for_metadata_plan"],
        "safe_for_shared_rail": False,
        "pitch1_regression_check": {
            "pitch_x": 1.0,
            "pitch_x_legal_for_bbox": pitch1_check["pitch_x_legal_for_bbox"],
            "overlap_risk_if_physically_placed": pitch1_check["overlap_risk_if_physically_placed"],
            "can_enter_physical_row_placement": False,
        },
        "notes": [
            "This step stays metadata-only and does not place control rows into standalone.",
            "Recommended pitch uses the DFF bbox width by default because that is the minimum conservative no-overlap estimate available here.",
            "Clock domain metadata records source and sink rows only; no clock tree, routing, or skew proof is claimed.",
            "Row abutment, rail sharing, and integrated control routing remain unproven.",
        ],
            "step_6_4_recommendation": "Next, audit control-row legal pitch margin, clock-entry side constraints, and row-to-decoder/write-driver channel reservations before any physical control placement attempt.",
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
        "safe_for_metadata_floorplan="
        f"{report['safe_for_metadata_floorplan']} "
        f"physical_row_placement={report['can_enter_physical_row_placement']} "
        f"pitch1_legal={report['pitch1_regression_check']['pitch_x_legal_for_bbox']}"
    )
    return 0


def format_markdown(report: dict[str, Any]) -> str:
    return "\n".join(
        [
            "# OpenYield Control Row Floorplan Report",
            "",
            "This is a metadata-only control-row floorplan. It does not modify standalone.py, routing, or the GDS writer.",
            "",
            "## Summary",
            "",
            f"- addr_width: `{report['addr_width']}`",
            f"- data_width: `{report['data_width']}`",
            f"- local DFF bbox: `{json.dumps(report['local_dff_bbox'], ensure_ascii=False)}`",
            f"- recommended pitch_x: `{report['recommended_pitch_x']}`",
            f"- recommended row height: `{report['recommended_row_height']}`",
            f"- recommended row gap: `{report['recommended_row_gap']}`",
            f"- recommended_pitch_avoids_bbox_overlap: `{report['recommended_pitch_avoids_bbox_overlap']}`",
            f"- selected pitch policy: `{report['selected_pitch_policy']}`",
            f"- selected pitch_x: `{report['selected_pitch_x']}`",
            f"- placement count: `{report['placement_count']}`",
            f"- physical pitch legality: `{report['physical_pitch_legality']}`",
            f"- overlap risk: `{report['overlap_risk']}`",
            f"- safe_for_metadata_floorplan: `{report['safe_for_metadata_floorplan']}`",
            f"- can_enter_physical_row_placement: `{report['can_enter_physical_row_placement']}`",
            f"- can_enter_standalone_control_placement: `{report['can_enter_standalone_control_placement']}`",
            "",
            "## Row Summaries",
            "",
            table(
                ["row", "array", "bits", "clock", "input", "output", "consumer", "hint", "origin", "pitch_x", "row_height"],
                [
                    [
                        report["addr_dff_row_summary"]["row_name"],
                        report["addr_dff_row_summary"]["array_type"],
                        report["addr_dff_row_summary"]["bit_count"],
                        report["addr_dff_row_summary"]["clock_domain"],
                        report["addr_dff_row_summary"]["input_bus"],
                        report["addr_dff_row_summary"]["output_bus"],
                        report["addr_dff_row_summary"]["downstream_consumer"],
                        report["addr_dff_row_summary"]["relative_position_hint"],
                        f"({report['addr_dff_row_summary']['origin_x']}, {report['addr_dff_row_summary']['origin_y']})",
                        report["addr_dff_row_summary"]["pitch_x"],
                        report["addr_dff_row_summary"]["row_height"],
                    ],
                    [
                        report["data_dff_row_summary"]["row_name"],
                        report["data_dff_row_summary"]["array_type"],
                        report["data_dff_row_summary"]["bit_count"],
                        report["data_dff_row_summary"]["clock_domain"],
                        report["data_dff_row_summary"]["input_bus"],
                        report["data_dff_row_summary"]["output_bus"],
                        report["data_dff_row_summary"]["downstream_consumer"],
                        report["data_dff_row_summary"]["relative_position_hint"],
                        f"({report['data_dff_row_summary']['origin_x']}, {report['data_dff_row_summary']['origin_y']})",
                        report["data_dff_row_summary"]["pitch_x"],
                        report["data_dff_row_summary"]["row_height"],
                    ],
                ],
            ),
            "",
            "## Clock Domain Metadata",
            "",
            "```json",
            json.dumps(report["clock_domain_metadata"], ensure_ascii=False, indent=2),
            "```",
            "",
            "## Relative Placement Hints",
            "",
            *[f"- {item}" for item in report["relative_placement_hints"]],
            "",
            "## Pitch Regression Check",
            "",
            f"- pitch_x=1.0 legal: `{report['pitch1_regression_check']['pitch_x_legal_for_bbox']}`",
            f"- pitch_x=1.0 overlap risk: `{report['pitch1_regression_check']['overlap_risk_if_physically_placed']}`",
            "",
            "## Example Placements",
            "",
            table(
                ["instance", "row", "bit", "x", "y", "orientation", "d", "clk", "q", "consumer", "physical_pitch_legal"],
                [
                    [
                        item["instance_name"],
                        item["row_name"],
                        item["bit_index"],
                        item["x"],
                        item["y"],
                        item["orientation"],
                        item["d"],
                        item["clk"],
                        item["q"],
                        item["consumer"],
                        item["physical_pitch_legal"],
                    ]
                    for item in report["placements"][: min(6, len(report["placements"]))]
                ],
            ),
            "",
            "## Notes",
            "",
            *[f"- {item}" for item in report["notes"]],
            "",
        ]
    )


def table(headers: list[str], rows: list[list[Any]]) -> str:
    lines = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join("---" for _ in headers) + " |",
    ]
    for row in rows:
        lines.append("| " + " | ".join(str(item).replace("|", "\\|").replace("\n", "<br>") for item in row) + " |")
    return "\n".join(lines)


def flatten_placements(placements: list[dict[str, Any]], physical_pitch_legal: bool) -> list[dict[str, Any]]:
    normalized: list[dict[str, Any]] = []
    for item in placements:
        nets = item["nets"]
        normalized.append(
            {
                "instance_name": item["instance_name"],
                "row_name": "ADDR_DFF_ROW" if item["array_type"] == "ADDR_DFF" else "DATA_DFF_ROW",
                "array_type": item["array_type"],
                "bit_index": item["bit_index"],
                "x": item["x"],
                "y": item["y"],
                "orientation": item["orientation"],
                "d": nets["d"],
                "clk": nets["clk"],
                "q": nets["q"],
                "vdd": nets["vdd"],
                "gnd": nets["gnd"],
                "consumer": item["downstream_consumer"],
                "physical_pitch_legal": physical_pitch_legal,
            }
        )
    return normalized


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
