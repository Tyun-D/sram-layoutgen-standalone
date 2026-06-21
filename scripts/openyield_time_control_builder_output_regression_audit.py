from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from sram_layoutgen.openyield_adapter.time_control_builder_output_regression import (
    build_time_control_builder_output_regression_markdown,
    build_time_control_builder_output_regression_report,
)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--openyield-root", required=True)
    parser.add_argument("--contracts", required=True)
    parser.add_argument("--tech-dir", required=True)
    parser.add_argument("--out-json", required=True)
    parser.add_argument("--out-md", required=True)
    parser.add_argument("--out-graph", required=True)
    args = parser.parse_args()

    report, graph = build_time_control_builder_output_regression_report(
        openyield_root=args.openyield_root,
        contracts_path=args.contracts,
        tech_dir=args.tech_dir,
    )

    out_json = Path(args.out_json)
    out_md = Path(args.out_md)
    out_graph = Path(args.out_graph)
    out_json.parent.mkdir(parents=True, exist_ok=True)
    out_md.parent.mkdir(parents=True, exist_ok=True)
    out_graph.parent.mkdir(parents=True, exist_ok=True)
    out_json.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    out_md.write_text(build_time_control_builder_output_regression_markdown(report) + "\n", encoding="utf-8")
    out_graph.write_text(json.dumps(graph, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote {out_json.resolve()}")
    print(f"Wrote {out_md.resolve()}")
    print(f"Wrote {out_graph.resolve()}")
    print(
        "builder_output_regression_audit_available="
        f"{report['consistency_checks']['builder_output_regression_audit_available']} "
        "future_default_off_builder_output_regression_clean="
        f"{report['consistency_checks']['future_default_off_builder_output_regression_clean']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
