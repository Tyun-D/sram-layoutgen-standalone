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

from sram_layoutgen.openyield_adapter.control_geometry_windows import build_control_geometry_windows  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description="Audit OpenYield control geometry windows and keepouts.")
    parser.add_argument("--addr-width", type=int, default=5)
    parser.add_argument("--data-width", type=int, default=4)
    parser.add_argument("--dff-pitch-x", type=float, default=3.06)
    parser.add_argument("--row-height", type=float, default=2.67)
    parser.add_argument("--row-gap", type=float, default=2.67)
    parser.add_argument("--channel-width", type=float, default=2.0)
    parser.add_argument("--clock-channel-width", type=float, default=2.0)
    parser.add_argument("--origin-x", type=float, default=0.0)
    parser.add_argument("--origin-y", type=float, default=0.0)
    parser.add_argument("--decoder-side", default="decoder_input_side")
    parser.add_argument("--write-driver-side", default="write_driver_input_side")
    parser.add_argument("--clock-entry-side", default="control_side")
    parser.add_argument("--channel-budget-report", default="docs/openyield_control_channel_budget_report.json")
    parser.add_argument("--writedriver-report", default="docs/openyield_writedriver_adapter_report.json")
    parser.add_argument("--floorplan-report", default="docs/openyield_control_row_floorplan_report.json")
    parser.add_argument("--out-json", default="docs/openyield_control_geometry_window_report.json")
    parser.add_argument("--out-md", default="docs/openyield_control_geometry_window_report.md")
    args = parser.parse_args()

    budget = json.loads(resolve_input(args.channel_budget_report).read_text(encoding="utf-8"))
    writedriver = json.loads(resolve_input(args.writedriver_report).read_text(encoding="utf-8"))
    floorplan = json.loads(resolve_input(args.floorplan_report).read_text(encoding="utf-8"))
    dff_width = float(floorplan["local_dff_bbox_dimensions"]["width"])
    local_wd_bbox = writedriver["local_macro"]["gds_bbox"]

    model = build_control_geometry_windows(
        addr_width=args.addr_width,
        data_width=args.data_width,
        dff_pitch_x=args.dff_pitch_x,
        dff_width=dff_width,
        row_height=args.row_height,
        row_gap=args.row_gap,
        channel_width=args.channel_width,
        clock_channel_width=args.clock_channel_width,
        origin_x=args.origin_x,
        origin_y=args.origin_y,
        decoder_side=args.decoder_side,
        write_driver_side=args.write_driver_side,
        clock_entry_side=args.clock_entry_side,
        row_to_decoder_required_width=float(budget["row_to_decoder_estimated_required_width"]),
        row_to_write_driver_required_width=float(budget["row_to_write_driver_estimated_required_width"]),
        clock_required_width=float(budget["clock_channel_estimated_required_width"]),
        write_driver_bbox=local_wd_bbox,
        write_driver_input_side="bottom",
        write_driver_pin_side_confirmed=bool(budget["write_driver_side_pin_known"]),
    )

    report = {
        "scope": "step6_6_openyield_control_geometry_windows",
        "standalone_modified": False,
        "routing_modified": False,
        "gds_writer_modified": False,
        "addr_width": args.addr_width,
        "data_width": args.data_width,
        "dff_row_bboxes": model["dff_row_bboxes"],
        "channel_window_list": model["geometry_windows"],
        "keepout_rectangle_list": model["keepout_rectangles"],
        "clock_entry_window": next(item for item in model["geometry_windows"] if item["window_name"] == "CLOCK_ENTRY_WINDOW"),
        "decoder_input_window": next(item for item in model["geometry_windows"] if item["window_name"] == "ADDR_TO_DECODER_WINDOW"),
        "write_driver_input_window": next(item for item in model["geometry_windows"] if item["window_name"] == "DATA_TO_WRITEDRIVER_WINDOW"),
        "decoder_side_geometry_proven": model["decoder_side_geometry_proven"],
        "write_driver_side_pin_known": model["write_driver_pin_side_confirmed"],
        "keepout_conflict_found": model["keepout_conflict_found"],
        "hardmacro_overlap_found": model["hardmacro_overlap_found"],
        "decoder_pin_proof_required": model["decoder_pin_proof_required"],
        "write_driver_pin_side_confirmed": model["write_driver_pin_side_confirmed"],
        "clock_window_physical_access_proven": model["clock_window_physical_access_proven"],
        "physical_routing_proven": model["physical_routing_proven"],
        "clock_skew_checked": model["clock_skew_checked"],
        "shared_rail_enabled": model["shared_rail_enabled"],
        "geometry_window_budget_pass": model["geometry_window_budget_pass"],
        "safe_for_geometry_window_metadata": model["safe_for_geometry_window_metadata"],
        "can_enter_physical_row_placement": model["can_enter_physical_row_placement"],
        "can_enter_standalone_control_placement": model["can_enter_standalone_control_placement"],
        "write_driver_preview_bbox": model["write_driver_preview_bbox"],
        "blocker_list": model["blockers"],
        "step_6_7_recommendation": "Next, tie decoder-side and write-driver-side windows to explicit local placement candidates or hardmacro anchors before attempting the first physical control-row placement smoke.",
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
        "geometry_window_metadata="
        f"{report['safe_for_geometry_window_metadata']} "
        f"physical_row_placement={report['can_enter_physical_row_placement']} "
        f"standalone_control={report['can_enter_standalone_control_placement']}"
    )
    return 0


def format_markdown(report: dict[str, Any]) -> str:
    return "\n".join(
        [
            "# OpenYield Control Geometry Window Report",
            "",
            "This is a metadata-only geometry window and keepout audit. It does not modify standalone.py, routing, or the GDS writer.",
            "",
            "## Summary",
            "",
            f"- addr_width: `{report['addr_width']}`",
            f"- data_width: `{report['data_width']}`",
            f"- decoder_side_geometry_proven: `{report['decoder_side_geometry_proven']}`",
            f"- write_driver_side_pin_known: `{report['write_driver_side_pin_known']}`",
            f"- keepout_conflict_found: `{report['keepout_conflict_found']}`",
            f"- hardmacro_overlap_found: `{report['hardmacro_overlap_found']}`",
            f"- physical_routing_proven: `{report['physical_routing_proven']}`",
            f"- clock_skew_checked: `{report['clock_skew_checked']}`",
            f"- safe_for_geometry_window_metadata: `{report['safe_for_geometry_window_metadata']}`",
            f"- can_enter_physical_row_placement: `{report['can_enter_physical_row_placement']}`",
            f"- can_enter_standalone_control_placement: `{report['can_enter_standalone_control_placement']}`",
            "",
            "## DFF Row BBoxes",
            "",
            "```json",
            json.dumps(report["dff_row_bboxes"], ensure_ascii=False, indent=2),
            "```",
            "",
            "## Geometry Windows",
            "",
            table(
                ["window", "x0", "y0", "x1", "y1", "width", "height", "metadata_only", "physical_routing_proven"],
                [
                    [
                        item["window_name"],
                        item["x0"],
                        item["y0"],
                        item["x1"],
                        item["y1"],
                        item["width"],
                        item["height"],
                        item["metadata_only"],
                        item["physical_routing_proven"],
                    ]
                    for item in report["channel_window_list"]
                ],
            ),
            "",
            "## Keepouts",
            "",
            table(
                ["keepout", "x0", "y0", "x1", "y1", "width", "height", "overlaps_known_hardmacro"],
                [
                    [
                        item["keepout_name"],
                        item["x0"],
                        item["y0"],
                        item["x1"],
                        item["y1"],
                        item["width"],
                        item["height"],
                        item["overlaps_known_hardmacro"],
                    ]
                    for item in report["keepout_rectangle_list"]
                ],
            ),
            "",
            "## Blockers",
            "",
            *[f"- {item}" for item in report["blocker_list"]],
            "",
            "## Step 6.7 Recommendation",
            "",
            f"- {report['step_6_7_recommendation']}",
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
