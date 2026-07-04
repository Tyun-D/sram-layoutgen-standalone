from __future__ import annotations

import argparse
import sys
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Reference-locked reproduction fix for M6.")
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

    from sram_layoutgen.openyield_adapter.M6R_reference_locked_reproduce import run_m6r_reference_locked_reproduce

    report = run_m6r_reference_locked_reproduce(
        repo_root=repo_root,
        status_md=(repo_root / args.status_md).resolve(),
        status_json=(repo_root / args.status_json).resolve(),
        out_dir=(repo_root / args.out_dir).resolve(),
        out_json=(repo_root / args.out_json).resolve(),
        out_report=(repo_root / args.out_report).resolve(),
    )
    print(f"reference_copy={report['reference_copy_for_review_gds_path']}")
    print(f"reproduced={report['layoutgen_hybrid_reproduced_M6R_gds_path']}")
    print(f"reproduced_matches_reference={report['reproduced_matches_reference']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
