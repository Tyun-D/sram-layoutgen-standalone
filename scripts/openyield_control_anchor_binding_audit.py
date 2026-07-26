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

from sram_layoutgen.openyield_adapter.control_anchor_binding import build_control_anchor_binding  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description="Audit OpenYield control anchor binding.")
    parser.add_argument("--addr-width", type=int, default=5)
    parser.add_argument("--data-width", type=int, default=4)
    parser.add_argument("--dff-pitch-x", type=float, default=3.06)
    parser.add_argument("--row-height", type=float, default=2.67)
    parser.add_argument("--row-gap", type=float, default=2.67)
    parser.add_argument("--channel-width", type=float, default=2.0)
    parser.add_argument("--origin-x", type=float, default=0.0)
    parser.add_argument("--origin-y", type=float, default=0.0)
    parser.add_argument("--decoder-anchor-policy", default="metadata_window")
    parser.add_argument("--write-driver-anchor-policy", default="gds_pin_side")
    parser.add_argument("--geometry-window-report", default="docs/openyield_control_geometry_window_report.json")
    parser.add_argument("--writedriver-report", default="docs/openyield_writedriver_adapter_report.json")
    parser.add_argument("--out-json", default="docs/openyield_control_anchor_binding_report.json")
    parser.add_argument("--out-md", default="docs/openyield_control_anchor_binding_report.md")
    args = parser.parse_args()

    geometry = json.loads(resolve_input(args.geometry_window_report).read_text(encoding="utf-8"))
    writedriver = json.loads(resolve_input(args.writedriver_report).read_text(encoding="utf-8"))

    binding = build_control_anchor_binding(
        geometry_windows=geometry,
        decoder_anchor_policy=args.decoder_anchor_policy,
        write_driver_anchor_policy=args.write_driver_anchor_policy,
        write_driver_bbox=writedriver["local_macro"]["gds_bbox"],
        write_driver_preview_bbox=geometry.get("write_driver_preview_bbox"),
        addr_width=args.addr_width,
        data_width=args.data_width,
    )

    report = {
        "scope": "step6_7_openyield_control_anchor_binding",
        "standalone_modified": False,
        "routing_modified": False,
        "gds_writer_modified": False,
        "addr_width": args.addr_width,
        "data_width": args.data_width,
        "dff_row_bboxes": geometry["dff_row_bboxes"],
        "addr_to_decoder_window_summary": geometry["decoder_input_window"],
        "data_to_writedriver_window_summary": geometry["write_driver_input_window"],
        "decoder_anchor": binding["decoder_anchor"],
        "write_driver_anchor": binding["write_driver_anchor"],
        "decoder_side_geometry_proven": binding["decoder_side_geometry_proven"],
        "write_driver_side_pin_known": binding["write_driver_side_pin_known"],
        "anchor_binding_success": binding["anchor_binding_success"],
        "decoder_anchor_bound": binding["decoder_anchor_bound"],
        "write_driver_anchor_bound": binding["write_driver_anchor_bound"],
        "decoder_anchor_is_metadata_only": binding["decoder_anchor_is_metadata_only"],
        "write_driver_anchor_uses_gds_pin_side": binding["write_driver_anchor_uses_gds_pin_side"],
        "anchor_row_overlap": binding["anchor_row_overlap"],
        "anchor_keepout_overlap": binding["anchor_keepout_overlap"],
        "anchor_keepout_conflict_found": binding["anchor_keepout_conflict_found"],
        "anchor_hardmacro_overlap_found": binding["anchor_hardmacro_overlap_found"],
        "physical_routing_proven": binding["physical_routing_proven"],
        "safe_for_anchor_binding_metadata": binding["safe_for_anchor_binding_metadata"],
        "can_enter_limited_physical_smoke": binding["can_enter_limited_physical_smoke"],
        "can_enter_standalone_control_placement": binding["can_enter_standalone_control_placement"],
        "blocker_list": binding["blockers"],
        "step_6_8_recommendation": "Next, convert decoder-side metadata anchors into explicit local placement candidates or generated-block envelopes before any limited physical smoke.",
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
        "anchor_binding_metadata="
        f"{report['safe_for_anchor_binding_metadata']} "
        f"limited_physical_smoke={report['can_enter_limited_physical_smoke']} "
        f"standalone_control={report['can_enter_standalone_control_placement']}"
    )
    return 0


def format_markdown(report: dict[str, Any]) -> str:
    return "\n".join(
        [
            "# OpenYield Control Anchor Binding Report",
            "",
            "This is a metadata-only anchor binding audit. It does not modify standalone.py, routing, or the GDS writer.",
            "",
            "## Summary",
            "",
            f"- decoder_side_geometry_proven: `{report['decoder_side_geometry_proven']}`",
            f"- write_driver_side_pin_known: `{report['write_driver_side_pin_known']}`",
            f"- anchor_binding_success: `{report['anchor_binding_success']}`",
            f"- decoder_anchor_is_metadata_only: `{report['decoder_anchor_is_metadata_only']}`",
            f"- write_driver_anchor_uses_gds_pin_side: `{report['write_driver_anchor_uses_gds_pin_side']}`",
            f"- anchor_keepout_conflict_found: `{report['anchor_keepout_conflict_found']}`",
            f"- anchor_hardmacro_overlap_found: `{report['anchor_hardmacro_overlap_found']}`",
            f"- physical_routing_proven: `{report['physical_routing_proven']}`",
            f"- can_enter_limited_physical_smoke: `{report['can_enter_limited_physical_smoke']}`",
            f"- can_enter_standalone_control_placement: `{report['can_enter_standalone_control_placement']}`",
            "",
            "## Anchors",
            "",
            "```json",
            json.dumps(
                {
                    "decoder_anchor": report["decoder_anchor"],
                    "write_driver_anchor": report["write_driver_anchor"],
                },
                ensure_ascii=False,
                indent=2,
            ),
            "```",
            "",
            "## Overlap Checks",
            "",
            "```json",
            json.dumps(
                {
                    "anchor_row_overlap": report["anchor_row_overlap"],
                    "anchor_keepout_overlap": report["anchor_keepout_overlap"],
                },
                ensure_ascii=False,
                indent=2,
            ),
            "```",
            "",
            "## Blockers",
            "",
            *[f"- {item}" for item in report["blocker_list"]],
            "",
            "## Step 6.8 Recommendation",
            "",
            f"- {report['step_6_8_recommendation']}",
            "",
        ]
    )


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
