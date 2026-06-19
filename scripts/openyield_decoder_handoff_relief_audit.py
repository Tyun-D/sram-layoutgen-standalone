from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from sram_layoutgen.openyield_adapter.decoder_handoff_relief import (
    build_decoder_handoff_relief_markdown,
    build_decoder_handoff_relief_report,
)


def _parse_widths(raw: str) -> list[float]:
    return [float(item.strip()) for item in raw.split(",") if item.strip()]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--addr-width", type=int, default=5)
    parser.add_argument("--route-pitch", type=float, default=0.2)
    parser.add_argument("--route-margin", type=float, default=0.2)
    parser.add_argument("--base-wordline-channel-width", type=float, default=2.0)
    parser.add_argument("--candidate-wordline-channel-widths", default="2.0,2.2,2.4,2.6,3.0")
    parser.add_argument("--enable-channel-width", type=float, default=2.0)
    parser.add_argument("--grouping-policy", default="current_8_outputs_per_stage")
    parser.add_argument("--stage-order-policy", default="current_level1_order")
    parser.add_argument("--out-json", required=True)
    parser.add_argument("--out-md", required=True)
    parser.add_argument("--out-graph")
    args = parser.parse_args()

    report, graph = build_decoder_handoff_relief_report(
        addr_width=args.addr_width,
        route_pitch=args.route_pitch,
        route_margin=args.route_margin,
        base_wordline_channel_width=args.base_wordline_channel_width,
        candidate_wordline_channel_widths=_parse_widths(args.candidate_wordline_channel_widths),
        enable_channel_width=args.enable_channel_width,
        grouping_policy=args.grouping_policy,
        stage_order_policy=args.stage_order_policy,
    )

    out_json = Path(args.out_json)
    out_md = Path(args.out_md)
    out_json.parent.mkdir(parents=True, exist_ok=True)
    out_md.parent.mkdir(parents=True, exist_ok=True)
    out_json.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    out_md.write_text(build_decoder_handoff_relief_markdown(report) + "\n", encoding="utf-8")
    print(f"Wrote {out_json.resolve()}")
    print(f"Wrote {out_md.resolve()}")
    if args.out_graph:
        out_graph = Path(args.out_graph)
        out_graph.parent.mkdir(parents=True, exist_ok=True)
        out_graph.write_text(json.dumps(graph, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(f"Wrote {out_graph.resolve()}")
    print(
        "decoder_handoff_relief_available="
        f"{report['decoder_handoff_relief_available']} "
        "positive_margin_candidate_available="
        f"{report['positive_margin_candidate_available']} "
        "recommended_handoff_relief_strategy="
        f"{report['recommended_handoff_relief_strategy']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
