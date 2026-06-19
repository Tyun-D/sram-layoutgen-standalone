from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from sram_layoutgen.openyield_adapter.time_control_evidence_crossing_bundle import (
    build_time_control_evidence_crossing_bundle_markdown,
    build_time_control_evidence_crossing_bundle_report,
)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--openyield-root", required=True)
    parser.add_argument("--contracts", required=True)
    parser.add_argument("--tech-dir", required=True)
    parser.add_argument("--route-pitch", type=float, default=0.2)
    parser.add_argument("--route-margin", type=float, default=0.2)
    parser.add_argument("--default-control-channel-width", type=float, default=2.0)
    parser.add_argument("--out-json", required=True)
    parser.add_argument("--out-md", required=True)
    parser.add_argument("--out-graph", required=True)
    args = parser.parse_args()

    report, graph = build_time_control_evidence_crossing_bundle_report(
        openyield_root=args.openyield_root,
        contracts_path=args.contracts,
        tech_dir=args.tech_dir,
        route_pitch=args.route_pitch,
        route_margin=args.route_margin,
        default_control_channel_width=args.default_control_channel_width,
    )

    out_json = Path(args.out_json)
    out_md = Path(args.out_md)
    out_graph = Path(args.out_graph)
    out_json.parent.mkdir(parents=True, exist_ok=True)
    out_md.parent.mkdir(parents=True, exist_ok=True)
    out_graph.parent.mkdir(parents=True, exist_ok=True)
    out_json.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    out_md.write_text(build_time_control_evidence_crossing_bundle_markdown(report) + "\n", encoding="utf-8")
    out_graph.write_text(json.dumps(graph, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote {out_json.resolve()}")
    print(f"Wrote {out_md.resolve()}")
    print(f"Wrote {out_graph.resolve()}")
    print(
        "time_control_evidence_crossing_bundle_available="
        f"{report['consistency_checks']['time_control_evidence_crossing_bundle_available']} "
        "can_enter_time_control_metadata_closure="
        f"{report['can_enter_time_control_metadata_closure']} "
        "can_enter_time_control_physical_placement="
        f"{report['can_enter_time_control_physical_placement']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
