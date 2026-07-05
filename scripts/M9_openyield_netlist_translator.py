from __future__ import annotations

import argparse
import sys
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Implement the M9 OpenYield netlist-to-layout translator.")
    parser.add_argument("--repo-root", required=True)
    parser.add_argument("--status-md", required=True)
    parser.add_argument("--status-json", required=True)
    parser.add_argument("--out-dir", required=True)
    parser.add_argument("--out-json", required=True)
    parser.add_argument("--out-report", required=True)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    repo_root = Path(args.repo_root).resolve()
    if str(repo_root) not in sys.path:
        sys.path.insert(0, str(repo_root))

    from sram_layoutgen.openyield_adapter.M9_openyield_netlist_translator import run_m9_openyield_netlist_translator

    report = run_m9_openyield_netlist_translator(
        repo_root=repo_root,
        status_md=(repo_root / args.status_md).resolve(),
        status_json=(repo_root / args.status_json).resolve(),
        out_dir=(repo_root / args.out_dir).resolve(),
        out_json=(repo_root / args.out_json).resolve(),
        out_report=(repo_root / args.out_report).resolve(),
    )
    print(f"translated_gds_path={report['translated_gds_path']}")
    print(f"translated_top_cell_name={report['translated_top_cell_name']}")
    print(f"remaining_M9_blockers_count={report['remaining_M9_blockers_count']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
