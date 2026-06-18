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

from sram_layoutgen.openyield_adapter.control_row_feasibility import build_control_row_feasibility  # noqa: E402
from sram_layoutgen.openyield_adapter.dff_array_adapter import build_dff_array_adapter_report  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description="Audit OpenYield control-row metadata placement feasibility.")
    parser.add_argument("--openyield-root", default="third_party/OpenYield")
    parser.add_argument("--contracts", default="docs/openyield_module_contracts.json")
    parser.add_argument("--tech-dir", default="technology/freepdk45")
    parser.add_argument("--addr-width", type=int, required=True)
    parser.add_argument("--data-width", type=int, required=True)
    parser.add_argument("--pitch-margin", type=float, default=0.2)
    parser.add_argument("--channel-width", type=float, default=2.0)
    parser.add_argument("--clock-entry-side", default="control_side")
    parser.add_argument("--origin-x", type=float, default=0.0)
    parser.add_argument("--origin-y", type=float, default=0.0)
    parser.add_argument("--out-json", default="docs/openyield_control_row_feasibility_report.json")
    parser.add_argument("--out-md", default="docs/openyield_control_row_feasibility_report.md")
    args = parser.parse_args()

    adapter = build_dff_array_adapter_report(
        resolve_input(args.openyield_root),
        resolve_input(args.contracts),
        resolve_input(args.tech_dir),
    )
    bbox = adapter["local_dff_gds_bbox"]
    dff_width = float(bbox["x1"]) - float(bbox["x0"])
    dff_height = float(bbox["y1"]) - float(bbox["y0"])

    feasibility = build_control_row_feasibility(
        addr_width=args.addr_width,
        data_width=args.data_width,
        dff_width=dff_width,
        dff_height=dff_height,
        pitch_margin=args.pitch_margin,
        channel_width=args.channel_width,
        clock_entry_side=args.clock_entry_side,
        origin_x=args.origin_x,
        origin_y=args.origin_y,
    )

    report = {
        "scope": "step6_4_openyield_control_row_feasibility",
        "standalone_modified": False,
        "routing_modified": False,
        "gds_writer_modified": False,
        "addr_width": args.addr_width,
        "data_width": args.data_width,
        "local_dff_bbox": bbox,
        "local_dff_bbox_dimensions": feasibility["dff_bbox"],
        "minimum_no_overlap_pitch_x": feasibility["minimum_no_overlap_pitch_x"],
        "recommended_pitch_x_no_margin": feasibility["recommended_pitch_x_no_margin"],
        "recommended_pitch_x_with_margin": feasibility["recommended_pitch_x_with_margin"],
        "pitch_margin_um": feasibility["pitch_margin_um"],
        "pitch_margin_policy": feasibility["pitch_margin_policy"],
        "bbox_overlap_avoided": feasibility["bbox_overlap_avoided"],
        "margin_added": feasibility["margin_added"],
        "recommended_row_height": feasibility["recommended_row_height"],
        "recommended_row_gap": feasibility["recommended_row_gap"],
        "clock_entry_side": feasibility["clock_entry_side"],
        "addr_dff_row_feasibility": feasibility["addr_dff_row_feasibility"],
        "data_dff_row_feasibility": feasibility["data_dff_row_feasibility"],
        "clock_channel": feasibility["clock_channel"],
        "row_to_decoder_channel": feasibility["row_to_decoder_channel"],
        "row_to_write_driver_channel": feasibility["row_to_write_driver_channel"],
        "safe_for_control_row_metadata_feasibility": feasibility["safe_for_control_row_metadata_feasibility"],
        "channel_reservation_available": feasibility["channel_reservation_available"],
        "clock_channel_reserved": feasibility["clock_channel_reserved"],
        "row_to_decoder_channel_reserved": feasibility["row_to_decoder_channel_reserved"],
        "row_to_write_driver_channel_reserved": feasibility["row_to_write_driver_channel_reserved"],
        "metadata_only_status": True,
        "physical_routing_proven": feasibility["physical_routing_proven"],
        "clock_skew_checked": feasibility["clock_skew_checked"],
        "shared_rail_enabled": feasibility["shared_rail_enabled"],
        "can_enter_physical_row_placement": feasibility["can_enter_physical_row_placement"],
        "can_enter_standalone_control_placement": feasibility["can_enter_standalone_control_placement"],
        "blocking_items": feasibility["blocking_items"],
        "step_6_5_recommendation": "Next, prove control-row channel usage against decoder/write-driver side geometry and define a physical reservation model before attempting standalone control placement.",
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
        "metadata_feasible="
        f"{report['safe_for_control_row_metadata_feasibility']} "
        f"physical_row_placement={report['can_enter_physical_row_placement']} "
        f"standalone_control={report['can_enter_standalone_control_placement']}"
    )
    return 0


def format_markdown(report: dict[str, Any]) -> str:
    return "\n".join(
        [
            "# OpenYield Control Row Feasibility Report",
            "",
            "This is a metadata-only feasibility audit. It does not modify standalone.py, routing, or the GDS writer.",
            "",
            "## Summary",
            "",
            f"- addr_width: `{report['addr_width']}`",
            f"- data_width: `{report['data_width']}`",
            f"- local DFF bbox: `{json.dumps(report['local_dff_bbox'], ensure_ascii=False)}`",
            f"- minimum_no_overlap_pitch_x: `{report['minimum_no_overlap_pitch_x']}`",
            f"- recommended_pitch_x_with_margin: `{report['recommended_pitch_x_with_margin']}`",
            f"- pitch_margin_um: `{report['pitch_margin_um']}`",
            f"- pitch_margin_policy: `{report['pitch_margin_policy']}`",
            f"- clock_entry_side: `{report['clock_entry_side']}`",
            f"- safe_for_control_row_metadata_feasibility: `{report['safe_for_control_row_metadata_feasibility']}`",
            f"- can_enter_physical_row_placement: `{report['can_enter_physical_row_placement']}`",
            f"- can_enter_standalone_control_placement: `{report['can_enter_standalone_control_placement']}`",
            "",
            "## Row Feasibility",
            "",
            table(
                ["row", "bits", "pitch_x", "row_height", "clock_entry_side", "consumer", "channel_reserved", "channel_width_um", "physical_routing_proven"],
                [
                    [
                        report["addr_dff_row_feasibility"]["row_name"],
                        report["addr_dff_row_feasibility"]["bit_count"],
                        report["addr_dff_row_feasibility"]["pitch_x"],
                        report["addr_dff_row_feasibility"]["row_height"],
                        report["addr_dff_row_feasibility"]["clock_entry_side"],
                        report["addr_dff_row_feasibility"]["downstream_consumer"],
                        report["addr_dff_row_feasibility"]["channel_to_decoder_reserved"],
                        report["addr_dff_row_feasibility"]["channel_width_um"],
                        report["addr_dff_row_feasibility"]["physical_routing_proven"],
                    ],
                    [
                        report["data_dff_row_feasibility"]["row_name"],
                        report["data_dff_row_feasibility"]["bit_count"],
                        report["data_dff_row_feasibility"]["pitch_x"],
                        report["data_dff_row_feasibility"]["row_height"],
                        report["data_dff_row_feasibility"]["clock_entry_side"],
                        report["data_dff_row_feasibility"]["downstream_consumer"],
                        report["data_dff_row_feasibility"]["channel_to_write_driver_reserved"],
                        report["data_dff_row_feasibility"]["channel_width_um"],
                        report["data_dff_row_feasibility"]["physical_routing_proven"],
                    ],
                ],
            ),
            "",
            "## Channel Reservations",
            "",
            "```json",
            json.dumps(
                {
                    "clock_channel": report["clock_channel"],
                    "row_to_decoder_channel": report["row_to_decoder_channel"],
                    "row_to_write_driver_channel": report["row_to_write_driver_channel"],
                },
                ensure_ascii=False,
                indent=2,
            ),
            "```",
            "",
            "## Blocking Items",
            "",
            *[f"- {item}" for item in report["blocking_items"]],
            "",
            "## Step 6.5 Recommendation",
            "",
            f"- {report['step_6_5_recommendation']}",
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
