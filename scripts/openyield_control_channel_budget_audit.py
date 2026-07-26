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

from sram_layoutgen.openyield_adapter.control_channel_budget import build_channel_budget  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description="Audit OpenYield control-row channel budget and side geometry.")
    parser.add_argument("--addr-width", type=int, default=5)
    parser.add_argument("--data-width", type=int, default=4)
    parser.add_argument("--channel-width", type=float, default=2.0)
    parser.add_argument("--clock-channel-width", type=float, default=2.0)
    parser.add_argument("--route-pitch", type=float, default=0.2)
    parser.add_argument("--route-margin", type=float, default=0.2)
    parser.add_argument("--clock-entry-side", default="control_side")
    parser.add_argument("--decoder-side", default="decoder_input_side")
    parser.add_argument("--write-driver-side", default="write_driver_input_side")
    parser.add_argument("--out-json", default="docs/openyield_control_channel_budget_report.json")
    parser.add_argument("--out-md", default="docs/openyield_control_channel_budget_report.md")
    args = parser.parse_args()

    budget = build_channel_budget(
        addr_width=args.addr_width,
        data_width=args.data_width,
        channel_width=args.channel_width,
        clock_channel_width=args.clock_channel_width,
        route_pitch=args.route_pitch,
        route_margin=args.route_margin,
        clock_entry_side=args.clock_entry_side,
        decoder_side=args.decoder_side,
        write_driver_side=args.write_driver_side,
        write_driver_pin_known=True,
    )

    report = {
        "scope": "step6_5_openyield_control_channel_budget",
        "standalone_modified": False,
        "routing_modified": False,
        "gds_writer_modified": False,
        "addr_width": budget["addr_width"],
        "data_width": budget["data_width"],
        "channel_width": budget["channel_width"],
        "clock_channel_width": budget["clock_channel_width"],
        "route_pitch": budget["route_pitch"],
        "route_margin": budget["route_margin"],
        "row_to_decoder_required_tracks": budget["row_to_decoder_channel"]["required_tracks"],
        "row_to_decoder_estimated_required_width": budget["row_to_decoder_channel"]["estimated_required_width"],
        "row_to_decoder_metadata_budget_pass": budget["row_to_decoder_budget_pass"],
        "row_to_write_driver_required_tracks": budget["row_to_write_driver_channel"]["required_tracks"],
        "row_to_write_driver_estimated_required_width": budget["row_to_write_driver_channel"]["estimated_required_width"],
        "row_to_write_driver_metadata_budget_pass": budget["row_to_write_driver_budget_pass"],
        "clock_channel_required_tracks": budget["clock_channel"]["required_tracks"],
        "clock_channel_estimated_required_width": budget["clock_channel"]["estimated_required_width"],
        "clock_channel_metadata_budget_pass": budget["clock_channel_budget_pass"],
        "clock_entry_side": budget["clock_entry_side"],
        "decoder_side": budget["decoder_side"],
        "write_driver_side": budget["write_driver_side"],
        "channels": [
            budget["clock_channel"],
            budget["row_to_decoder_channel"],
            budget["row_to_write_driver_channel"],
        ],
        "decoder_side_geometry_proven": budget["decoder_side_geometry_proven"],
        "write_driver_side_pin_known": budget["write_driver_side_pin_known"],
        "physical_routing_proven": budget["physical_routing_proven"],
        "clock_skew_checked": budget["clock_skew_checked"],
        "safe_for_channel_budget_metadata": budget["safe_for_channel_budget_metadata"],
        "can_enter_physical_row_placement": budget["can_enter_physical_row_placement"],
        "can_enter_standalone_control_placement": budget["can_enter_standalone_control_placement"],
        "blocker_list": budget["blockers"],
        "step_6_6_recommendation": "Next, bind decoder-side and write-driver-side budget hints to explicit local geometry windows or placement keepouts before any physical control-row placement smoke.",
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
        "channel_budget_metadata="
        f"{report['safe_for_channel_budget_metadata']} "
        f"physical_row_placement={report['can_enter_physical_row_placement']} "
        f"standalone_control={report['can_enter_standalone_control_placement']}"
    )
    return 0


def format_markdown(report: dict[str, Any]) -> str:
    return "\n".join(
        [
            "# OpenYield Control Channel Budget Report",
            "",
            "This is a metadata-only channel budget and side-geometry audit. It does not modify standalone.py, routing, or the GDS writer.",
            "",
            "## Summary",
            "",
            f"- addr_width: `{report['addr_width']}`",
            f"- data_width: `{report['data_width']}`",
            f"- channel_width: `{report['channel_width']}`",
            f"- clock_channel_width: `{report['clock_channel_width']}`",
            f"- route_pitch: `{report['route_pitch']}`",
            f"- route_margin: `{report['route_margin']}`",
            f"- row_to_decoder_metadata_budget_pass: `{report['row_to_decoder_metadata_budget_pass']}`",
            f"- row_to_write_driver_metadata_budget_pass: `{report['row_to_write_driver_metadata_budget_pass']}`",
            f"- clock_channel_metadata_budget_pass: `{report['clock_channel_metadata_budget_pass']}`",
            f"- decoder_side_geometry_proven: `{report['decoder_side_geometry_proven']}`",
            f"- write_driver_side_pin_known: `{report['write_driver_side_pin_known']}`",
            f"- physical_routing_proven: `{report['physical_routing_proven']}`",
            f"- clock_skew_checked: `{report['clock_skew_checked']}`",
            f"- safe_for_channel_budget_metadata: `{report['safe_for_channel_budget_metadata']}`",
            f"- can_enter_physical_row_placement: `{report['can_enter_physical_row_placement']}`",
            f"- can_enter_standalone_control_placement: `{report['can_enter_standalone_control_placement']}`",
            "",
            "## Channel Budgets",
            "",
            table(
                ["channel", "required_tracks", "estimated_required_width", "available_width", "budget_pass", "source_side", "sink_side", "physical_access_proven", "physical_routing_proven"],
                [
                    [
                        item["channel_name"],
                        item["required_tracks"],
                        item["estimated_required_width"],
                        item["available_width"],
                        item["metadata_budget_pass"],
                        item["source_side_hint"],
                        item["sink_side_hint"],
                        item["physical_access_proven"],
                        item["physical_routing_proven"],
                    ]
                    for item in report["channels"]
                ],
            ),
            "",
            "## Channel Details",
            "",
            "```json",
            json.dumps(report["channels"], ensure_ascii=False, indent=2),
            "```",
            "",
            "## Blockers",
            "",
            *[f"- {item}" for item in report["blocker_list"]],
            "",
            "## Step 6.6 Recommendation",
            "",
            f"- {report['step_6_6_recommendation']}",
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


def resolve_output(value: str) -> Path:
    path = Path(value)
    return path if path.is_absolute() else STANDALONE_ROOT / path


if __name__ == "__main__":
    raise SystemExit(main())
