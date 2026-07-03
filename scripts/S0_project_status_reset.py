from __future__ import annotations

import argparse
import sys
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run S0 project status reset.")
    parser.add_argument("--repo-root", required=True)
    parser.add_argument("--out-status-md", required=True)
    parser.add_argument("--out-status-json", required=True)
    parser.add_argument("--out-review-dir", required=True)
    parser.add_argument("--out-report-json", required=True)
    parser.add_argument("--out-report-md", required=True)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    repo_root = Path(args.repo_root).resolve()
    if str(repo_root) not in sys.path:
        sys.path.insert(0, str(repo_root))
    from sram_layoutgen.openyield_adapter.project_status_reset import ProjectStatusReset, ProjectStatusResetConfig

    config = ProjectStatusResetConfig(
        repo_root=repo_root,
        out_status_md=(repo_root / args.out_status_md).resolve(),
        out_status_json=(repo_root / args.out_status_json).resolve(),
        out_review_dir=(repo_root / args.out_review_dir).resolve(),
        out_report_json=(repo_root / args.out_report_json).resolve(),
        out_report_md=(repo_root / args.out_report_md).resolve(),
    )
    ProjectStatusReset(config).run()


if __name__ == "__main__":
    main()
