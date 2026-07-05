from __future__ import annotations

import argparse
import sys
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Confirm uploaded golden reference and clear M7 blockers.")
    parser.add_argument("--repo-root", required=True)
    parser.add_argument("--status-md", required=True)
    parser.add_argument("--status-json", required=True)
    parser.add_argument("--m7-report", required=True)
    parser.add_argument("--golden-reference", required=True)
    parser.add_argument("--golden-clean-review", required=True)
    parser.add_argument("--out-dir", required=True)
    parser.add_argument("--out-json", required=True)
    parser.add_argument("--out-report", required=True)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    repo_root = Path(args.repo_root).resolve()
    if str(repo_root) not in sys.path:
        sys.path.insert(0, str(repo_root))

    from sram_layoutgen.openyield_adapter.M7C_golden_reference_confirmation import run_m7c_golden_reference_confirmation

    report = run_m7c_golden_reference_confirmation(
        repo_root=repo_root,
        status_md=(repo_root / args.status_md).resolve(),
        status_json=(repo_root / args.status_json).resolve(),
        m7_report=(repo_root / args.m7_report).resolve(),
        golden_reference=(repo_root / args.golden_reference).resolve(),
        golden_clean_review=(repo_root / args.golden_clean_review).resolve(),
        out_dir=(repo_root / args.out_dir).resolve(),
        out_json=(repo_root / args.out_json).resolve(),
        out_report=(repo_root / args.out_report).resolve(),
    )
    print(f"next_stage_allowed={report['next_stage_allowed']}")
    print(f"can_enter_M8_after_this_gate={report['can_enter_M8_after_this_gate']}")
    print(f"m7_blockers_after_count={report['m7_blockers_after_count']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
