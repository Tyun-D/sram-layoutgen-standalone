from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


SCRIPT_DIR = Path(__file__).resolve().parent
STANDALONE_ROOT = SCRIPT_DIR.parent
REPO_ROOT = STANDALONE_ROOT.parents[1]
if str(STANDALONE_ROOT) not in sys.path:
    sys.path.insert(0, str(STANDALONE_ROOT))

from sram_layoutgen.openyield_adapter.control_decomposition import (  # noqa: E402
    build_time_control_decomposition_report,
    build_time_control_decomposition_markdown,
    write_reports,
)


DEFAULT_OUT_JSON = Path("docs/openyield_time_control_decomposition_report.json")
DEFAULT_OUT_MD = Path("docs/openyield_time_control_decomposition_report.md")
DEFAULT_OUT_GRAPH_JSON = Path("docs/openyield_time_control_decomposition_graph.json")


def main() -> int:
    parser = argparse.ArgumentParser(description="Audit OpenYield TIME/control decomposition and consumer signal relationships.")
    parser.add_argument("--openyield-root", default="third_party/OpenYield")
    parser.add_argument("--contracts", default="docs/openyield_module_contracts.json")
    parser.add_argument("--tech-dir", default="technology/freepdk45")
    parser.add_argument("--out-json", type=Path, default=DEFAULT_OUT_JSON)
    parser.add_argument("--out-md", type=Path, default=DEFAULT_OUT_MD)
    parser.add_argument("--out-graph-json", type=Path, default=DEFAULT_OUT_GRAPH_JSON)
    args = parser.parse_args()

    openyield_root = resolve_input(args.openyield_root)
    contracts = resolve_input(args.contracts)
    tech_dir = resolve_input(args.tech_dir)
    out_json = resolve_output(args.out_json)
    out_md = resolve_output(args.out_md)
    out_graph = resolve_output(args.out_graph_json)

    report = write_reports(openyield_root, contracts, tech_dir, out_json, out_md, out_graph)
    print(f"Wrote {out_json}")
    print(f"Wrote {out_md}")
    print(f"Wrote {out_graph}")
    print(
        "time_decomposition_success="
        f"{report['time_decomposition_success']} "
        f"single_macro_allowed={report['time_as_single_macro_allowed']} "
        f"subblock_planning={report['can_enter_control_subblock_adapter_planning']} "
        f"standalone_control={report['can_enter_standalone_control_placement']}"
    )
    return 0


def resolve_input(value: str) -> Path:
    path = Path(value)
    if path.exists():
        return path
    for base in (Path.cwd(), STANDALONE_ROOT, REPO_ROOT):
        candidate = base / value
        if candidate.exists():
            return candidate
    return path


def resolve_output(value: Path) -> Path:
    path = Path(value)
    if path.is_absolute():
        return path
    return STANDALONE_ROOT / path


if __name__ == "__main__":
    raise SystemExit(main())
