from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from sram_layoutgen.openyield_adapter.control_parent_reservation import (
    build_control_parent_reservation_markdown,
    build_control_parent_reservation_report,
)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--addr-width", type=int, default=5)
    parser.add_argument("--base-wordline-channel-width", type=float, default=2.0)
    parser.add_argument("--recommended-wordline-channel-width", type=float, default=2.2)
    parser.add_argument("--extra-wordline-width", type=float, default=0.2)
    parser.add_argument("--control-channel-width", type=float, default=2.0)
    parser.add_argument("--clock-channel-width", type=float, default=2.0)
    parser.add_argument("--stage-row-gap", type=float, default=1.565)
    parser.add_argument("--level-gap", type=float, default=2.0)
    parser.add_argument("--reservation-policy", default="parent_metadata_side_channel_reservation")
    parser.add_argument("--out-json", required=True)
    parser.add_argument("--out-md", required=True)
    parser.add_argument("--out-graph")
    args = parser.parse_args()

    report, graph = build_control_parent_reservation_report(
        addr_width=args.addr_width,
        base_wordline_channel_width=args.base_wordline_channel_width,
        recommended_wordline_channel_width=args.recommended_wordline_channel_width,
        extra_wordline_width=args.extra_wordline_width,
        control_channel_width=args.control_channel_width,
        clock_channel_width=args.clock_channel_width,
        stage_row_gap=args.stage_row_gap,
        level_gap=args.level_gap,
        reservation_policy=args.reservation_policy,
    )

    out_json = Path(args.out_json)
    out_md = Path(args.out_md)
    out_json.parent.mkdir(parents=True, exist_ok=True)
    out_md.parent.mkdir(parents=True, exist_ok=True)
    out_json.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    out_md.write_text(build_control_parent_reservation_markdown(report) + "\n", encoding="utf-8")
    print(f"Wrote {out_json.resolve()}")
    print(f"Wrote {out_md.resolve()}")
    if args.out_graph:
        out_graph = Path(args.out_graph)
        out_graph.parent.mkdir(parents=True, exist_ok=True)
        out_graph.write_text(json.dumps(graph, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(f"Wrote {out_graph.resolve()}")
    print(
        "control_parent_reservation_available="
        f"{report['control_parent_reservation_available']} "
        "parent_reservation_recorded="
        f"{report['parent_reservation_recorded']} "
        "can_enter_decoder_metadata_closure="
        f"{report['can_enter_decoder_metadata_closure']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
