from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from sram_layoutgen.openyield_adapter.decoder_preplacement_feasibility import (
    build_decoder_preplacement_feasibility_markdown,
    build_decoder_preplacement_feasibility_report,
)


def _resolve_input_path(raw: str) -> Path:
    candidate = Path(raw)
    if candidate.is_absolute():
        return candidate
    local = (REPO_ROOT / candidate).resolve()
    if local.exists():
        return local
    workspace = (REPO_ROOT.parent.parent / candidate).resolve()
    if workspace.exists():
        return workspace
    return local


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--openyield-root", required=True)
    parser.add_argument("--tech-dir", required=True)
    parser.add_argument("--addr-width", type=int, default=5)
    parser.add_argument("--stage-row-gap", type=float, default=1.565)
    parser.add_argument("--level-gap", type=float, default=2.0)
    parser.add_argument("--handoff-channel-width", type=float, default=2.0)
    parser.add_argument("--route-pitch", type=float, default=0.2)
    parser.add_argument("--route-margin", type=float, default=0.2)
    parser.add_argument("--out-json", required=True)
    parser.add_argument("--out-md", required=True)
    parser.add_argument("--out-graph")
    args = parser.parse_args()

    report, graph = build_decoder_preplacement_feasibility_report(
        openyield_root=_resolve_input_path(args.openyield_root),
        tech_dir=_resolve_input_path(args.tech_dir),
        addr_width=args.addr_width,
        stage_row_gap=args.stage_row_gap,
        level_gap=args.level_gap,
        handoff_channel_width=args.handoff_channel_width,
        route_pitch=args.route_pitch,
        route_margin=args.route_margin,
    )

    out_json = Path(args.out_json)
    out_md = Path(args.out_md)
    out_json.parent.mkdir(parents=True, exist_ok=True)
    out_md.parent.mkdir(parents=True, exist_ok=True)
    out_json.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    out_md.write_text(build_decoder_preplacement_feasibility_markdown(report) + "\n", encoding="utf-8")
    print(f"Wrote {out_json.resolve()}")
    print(f"Wrote {out_md.resolve()}")
    if args.out_graph:
        out_graph = Path(args.out_graph)
        out_graph.parent.mkdir(parents=True, exist_ok=True)
        out_graph.write_text(json.dumps(graph, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(f"Wrote {out_graph.resolve()}")
    print(
        "decoder_preplacement_feasibility_available="
        f"{report['decoder_preplacement_feasibility_available']} "
        "metadata_stage_packing_consistent="
        f"{report['metadata_stage_packing_consistent']} "
        "decoder_physical_prototype="
        f"{report['can_enter_decoder_physical_prototype']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
