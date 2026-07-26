from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from sram_layoutgen.openyield_adapter.decoder_metadata_closure import (
    build_decoder_metadata_closure_markdown,
    build_decoder_metadata_closure_report,
)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--addr-width", type=int, default=5)
    parser.add_argument("--out-json", required=True)
    parser.add_argument("--out-md", required=True)
    parser.add_argument("--out-graph")
    args = parser.parse_args()

    report, graph = build_decoder_metadata_closure_report(addr_width=args.addr_width)

    out_json = Path(args.out_json)
    out_md = Path(args.out_md)
    out_json.parent.mkdir(parents=True, exist_ok=True)
    out_md.parent.mkdir(parents=True, exist_ok=True)
    out_json.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    out_md.write_text(build_decoder_metadata_closure_markdown(report) + "\n", encoding="utf-8")
    print(f"Wrote {out_json.resolve()}")
    print(f"Wrote {out_md.resolve()}")
    if args.out_graph:
        out_graph = Path(args.out_graph)
        out_graph.parent.mkdir(parents=True, exist_ok=True)
        out_graph.write_text(json.dumps(graph, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(f"Wrote {out_graph.resolve()}")
    print(
        "decoder_metadata_closure_available="
        f"{report['metadata_closure_available']} "
        "closed_metadata_items_complete="
        f"{report['closed_metadata_items_complete']} "
        "recommended_next_phase="
        f"{report['decision_summary']['recommended_next_phase']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
