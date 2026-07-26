from __future__ import annotations

import argparse
import sys
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Fix geometry delta between M8 reproduced GDS and uploaded golden reference.")
    parser.add_argument("--repo-root", required=True)
    parser.add_argument("--status-md", required=True)
    parser.add_argument("--status-json", required=True)
    parser.add_argument("--golden-reference", required=True)
    parser.add_argument("--m8-reproduced", required=True)
    parser.add_argument("--m8-raw-dir", required=True)
    parser.add_argument("--m8-report", required=True)
    parser.add_argument("--out-dir", required=True)
    parser.add_argument("--out-json", required=True)
    parser.add_argument("--out-report", required=True)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    repo_root = Path(args.repo_root).resolve()
    if str(repo_root) not in sys.path:
        sys.path.insert(0, str(repo_root))

    from sram_layoutgen.openyield_adapter.M8R_fix_golden_geometry_delta import run_m8r_fix_golden_geometry_delta

    report = run_m8r_fix_golden_geometry_delta(
        repo_root=repo_root,
        status_md=(repo_root / args.status_md).resolve(),
        status_json=(repo_root / args.status_json).resolve(),
        golden_reference=(repo_root / args.golden_reference).resolve(),
        m8_reproduced=(repo_root / args.m8_reproduced).resolve(),
        m8_raw_dir=(repo_root / args.m8_raw_dir).resolve(),
        m8_report=(repo_root / args.m8_report).resolve(),
        out_dir=(repo_root / args.out_dir).resolve(),
        out_json=(repo_root / args.out_json).resolve(),
        out_report=(repo_root / args.out_report).resolve(),
    )
    print(f"fixed_reproduced_gds_path={report['fixed_reproduced_gds_path']}")
    print(f"reference_vs_m8r_geometry_match={report['reference_vs_m8r_geometry_match']}")
    print(f"remaining_M8R_blockers_count={report['remaining_M8R_blockers_count']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
