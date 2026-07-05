from __future__ import annotations

import argparse
import sys
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Harden the M10 raw OpenYield source trace for the translator.")
    parser.add_argument("--repo-root", required=True)
    parser.add_argument("--status-md", required=True)
    parser.add_argument("--status-json", required=True)
    parser.add_argument("--m9h-report", required=True)
    parser.add_argument("--m9-report", required=True)
    parser.add_argument("--m9-dir", required=True)
    parser.add_argument("--golden-reference", required=True)
    parser.add_argument("--openyield-root", required=True)
    parser.add_argument("--openyield-intent-dir", required=True)
    parser.add_argument("--t1-inventory", required=True)
    parser.add_argument("--out-dir", required=True)
    parser.add_argument("--out-json", required=True)
    parser.add_argument("--out-report", required=True)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    repo_root = Path(args.repo_root).resolve()
    if str(repo_root) not in sys.path:
        sys.path.insert(0, str(repo_root))

    from sram_layoutgen.openyield_adapter.M10_harden_raw_openyield_trace import run_m10_harden_raw_openyield_trace

    report = run_m10_harden_raw_openyield_trace(
        repo_root=repo_root,
        status_md=(repo_root / args.status_md).resolve(),
        status_json=(repo_root / args.status_json).resolve(),
        m9h_report=(repo_root / args.m9h_report).resolve(),
        m9_report=(repo_root / args.m9_report).resolve(),
        m9_dir=(repo_root / args.m9_dir).resolve(),
        golden_reference=(repo_root / args.golden_reference).resolve(),
        openyield_root=Path(args.openyield_root).resolve(),
        openyield_intent_dir=(repo_root / args.openyield_intent_dir).resolve(),
        t1_inventory=(repo_root / args.t1_inventory).resolve(),
        out_dir=(repo_root / args.out_dir).resolve(),
        out_json=(repo_root / args.out_json).resolve(),
        out_report=(repo_root / args.out_report).resolve(),
    )
    print(f"gds_path={report['gds_path']}")
    print(f"reference_vs_m10_geometry_match={report['reference_vs_m10_geometry_match']}")
    print(f"remaining_M10_blockers_count={report['remaining_M10_blockers_count']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
