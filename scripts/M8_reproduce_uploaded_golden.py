from __future__ import annotations

import argparse
import sys
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Reproduce uploaded golden reference from layoutgen source.")
    parser.add_argument("--repo-root", required=True)
    parser.add_argument("--status-md", required=True)
    parser.add_argument("--status-json", required=True)
    parser.add_argument("--golden-reference", required=True)
    parser.add_argument("--golden-clean-review", required=True)
    parser.add_argument("--m7-extracted-dir", required=True)
    parser.add_argument("--m7c-report", required=True)
    parser.add_argument("--out-dir", required=True)
    parser.add_argument("--out-json", required=True)
    parser.add_argument("--out-report", required=True)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    repo_root = Path(args.repo_root).resolve()
    if str(repo_root) not in sys.path:
        sys.path.insert(0, str(repo_root))

    from sram_layoutgen.openyield_adapter.M8_reproduce_uploaded_golden import run_m8_reproduce_uploaded_golden

    report = run_m8_reproduce_uploaded_golden(
        repo_root=repo_root,
        status_md=(repo_root / args.status_md).resolve(),
        status_json=(repo_root / args.status_json).resolve(),
        golden_reference=(repo_root / args.golden_reference).resolve(),
        golden_clean_review=(repo_root / args.golden_clean_review).resolve(),
        m7_extracted_dir=(repo_root / args.m7_extracted_dir).resolve(),
        m7c_report=(repo_root / args.m7c_report).resolve(),
        out_dir=(repo_root / args.out_dir).resolve(),
        out_json=(repo_root / args.out_json).resolve(),
        out_report=(repo_root / args.out_report).resolve(),
    )
    print(f"reproduced_gds_path={report['reproduced_gds_path']}")
    print(f"geometry_match={report['reference_vs_reproduced_geometry_match']}")
    print(f"remaining_M8_blockers_count={report['remaining_M8_blockers_count']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
