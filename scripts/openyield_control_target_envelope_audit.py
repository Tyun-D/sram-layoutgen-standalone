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

from sram_layoutgen.openyield_adapter.control_target_envelopes import build_control_target_envelopes  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description="Audit OpenYield control target envelopes.")
    parser.add_argument("--addr-width", type=int, default=5)
    parser.add_argument("--data-width", type=int, default=4)
    parser.add_argument("--dff-pitch-x", type=float, default=3.06)
    parser.add_argument("--row-height", type=float, default=2.67)
    parser.add_argument("--row-gap", type=float, default=2.67)
    parser.add_argument("--channel-width", type=float, default=2.0)
    parser.add_argument("--origin-x", type=float, default=0.0)
    parser.add_argument("--origin-y", type=float, default=0.0)
    parser.add_argument("--decoder-envelope-policy", default="metadata_generated_block")
    parser.add_argument("--write-driver-target-policy", default="gds_pin_side_array_reference")
    parser.add_argument("--anchor-binding-report", default="docs/openyield_control_anchor_binding_report.json")
    parser.add_argument("--geometry-window-report", default="docs/openyield_control_geometry_window_report.json")
    parser.add_argument("--out-json", default="docs/openyield_control_target_envelope_report.json")
    parser.add_argument("--out-md", default="docs/openyield_control_target_envelope_report.md")
    args = parser.parse_args()

    anchor_binding = json.loads(resolve_input(args.anchor_binding_report).read_text(encoding="utf-8"))
    geometry_windows = json.loads(resolve_input(args.geometry_window_report).read_text(encoding="utf-8"))

    model = build_control_target_envelopes(
        anchor_binding=anchor_binding,
        geometry_windows=geometry_windows,
        addr_width=args.addr_width,
        data_width=args.data_width,
        channel_width=args.channel_width,
        row_height=args.row_height,
        decoder_envelope_policy=args.decoder_envelope_policy,
        write_driver_target_policy=args.write_driver_target_policy,
    )

    report = {
        "scope": "step6_8_openyield_control_target_envelopes",
        "standalone_modified": False,
        "routing_modified": False,
        "gds_writer_modified": False,
        "addr_width": args.addr_width,
        "data_width": args.data_width,
        "decoder_input_anchor_summary": anchor_binding["decoder_anchor"],
        "write_driver_input_anchor_summary": anchor_binding["write_driver_anchor"],
        "decoder_generated_block_envelope": model["decoder_envelope"],
        "decoder_input_side_hint": model["decoder_envelope"]["input_side_hint"],
        "decoder_output_side_hint": model["decoder_envelope"]["output_side_hint"],
        "decoder_envelope_pin_proven": model["decoder_hardmacro_pin_proven"],
        "write_driver_target_reference": model["write_driver_target"],
        "write_driver_input_side": model["write_driver_target"]["write_driver_input_side"],
        "decoder_envelope_bound": model["decoder_envelope_bound"],
        "write_driver_target_bound": model["write_driver_target_bound"],
        "decoder_envelope_is_metadata_only": model["decoder_envelope_is_metadata_only"],
        "write_driver_target_uses_gds_pin_side": model["write_driver_target_uses_gds_pin_side"],
        "decoder_envelope_conflict_found": model["decoder_envelope_conflict_found"],
        "write_driver_target_conflict_found": model["write_driver_target_conflict_found"],
        "hardmacro_overlap_found": model["hardmacro_overlap_found"],
        "physical_routing_proven": model["physical_routing_proven"],
        "safe_for_target_envelope_metadata": model["safe_for_target_envelope_metadata"],
        "can_enter_very_limited_physical_smoke": model["can_enter_very_limited_physical_smoke"],
        "can_enter_standalone_control_placement": model["can_enter_standalone_control_placement"],
        "blocker_list": model["blockers"],
        "step_6_9_recommendation": "Next, refine DECODER_CASCADE into explicit stage/group metadata candidates, or stop and summarize blockers before any control-row physical smoke attempt.",
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
        "target_envelope_metadata="
        f"{report['safe_for_target_envelope_metadata']} "
        f"very_limited_smoke={report['can_enter_very_limited_physical_smoke']} "
        f"standalone_control={report['can_enter_standalone_control_placement']}"
    )
    return 0


def format_markdown(report: dict[str, Any]) -> str:
    return "\n".join(
        [
            "# OpenYield Control Target Envelope Report",
            "",
            "This is a metadata-only decoder envelope and write-driver target audit. It does not modify standalone.py, routing, or the GDS writer.",
            "",
            "## Summary",
            "",
            f"- decoder_envelope_bound: `{report['decoder_envelope_bound']}`",
            f"- write_driver_target_bound: `{report['write_driver_target_bound']}`",
            f"- decoder_envelope_is_metadata_only: `{report['decoder_envelope_is_metadata_only']}`",
            f"- decoder_envelope_pin_proven: `{report['decoder_envelope_pin_proven']}`",
            f"- write_driver_target_uses_gds_pin_side: `{report['write_driver_target_uses_gds_pin_side']}`",
            f"- decoder_envelope_conflict_found: `{report['decoder_envelope_conflict_found']}`",
            f"- write_driver_target_conflict_found: `{report['write_driver_target_conflict_found']}`",
            f"- hardmacro_overlap_found: `{report['hardmacro_overlap_found']}`",
            f"- physical_routing_proven: `{report['physical_routing_proven']}`",
            f"- can_enter_very_limited_physical_smoke: `{report['can_enter_very_limited_physical_smoke']}`",
            f"- can_enter_standalone_control_placement: `{report['can_enter_standalone_control_placement']}`",
            "",
            "## Decoder Envelope",
            "",
            "```json",
            json.dumps(report["decoder_generated_block_envelope"], ensure_ascii=False, indent=2),
            "```",
            "",
            "## Write-Driver Target",
            "",
            "```json",
            json.dumps(report["write_driver_target_reference"], ensure_ascii=False, indent=2),
            "```",
            "",
            "## Blockers",
            "",
            *[f"- {item}" for item in report["blocker_list"]],
            "",
            "## Step 6.9 Recommendation",
            "",
            f"- {report['step_6_9_recommendation']}",
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
