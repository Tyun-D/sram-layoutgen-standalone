from __future__ import annotations

import argparse
import sys
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Confirm the M11 config-aware translator v3 gate state.")
    parser.add_argument("--repo-root", required=True)
    parser.add_argument("--status-md", required=True)
    parser.add_argument("--status-json", required=True)
    parser.add_argument("--goal-md", required=True)
    parser.add_argument("--progress-md", required=True)
    parser.add_argument("--m11-report", required=True)
    parser.add_argument("--m12-report", required=True)
    parser.add_argument("--m12-assets", required=True)
    parser.add_argument("--m12-backlog", required=True)
    parser.add_argument("--m11-dir", required=True)
    parser.add_argument("--out-dir", required=True)
    parser.add_argument("--out-json", required=True)
    parser.add_argument("--out-report", required=True)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    repo_root = Path(args.repo_root).resolve()
    if str(repo_root) not in sys.path:
        sys.path.insert(0, str(repo_root))

    from sram_layoutgen.openyield_adapter.M11H_confirm_config_aware_translator import (
        run_m11h_confirm_config_aware_translator,
    )

    report = run_m11h_confirm_config_aware_translator(
        repo_root=repo_root,
        status_md=(repo_root / args.status_md).resolve(),
        status_json=(repo_root / args.status_json).resolve(),
        goal_md=(repo_root / args.goal_md).resolve(),
        progress_md=(repo_root / args.progress_md).resolve(),
        m11_report=(repo_root / args.m11_report).resolve(),
        m12_report=(repo_root / args.m12_report).resolve(),
        m12_assets=(repo_root / args.m12_assets).resolve(),
        m12_backlog=(repo_root / args.m12_backlog).resolve(),
        m11_dir=(repo_root / args.m11_dir).resolve(),
        out_dir=(repo_root / args.out_dir).resolve(),
        out_json=(repo_root / args.out_json).resolve(),
        out_report=(repo_root / args.out_report).resolve(),
    )
    for key in [
        "m11_clean_gds_user_review_passed",
        "can_claim_config_aware_translator_v3",
        "can_claim_full_raw_netlist_compiler",
        "next_stage_allowed",
        "can_enter_M11A_after_this_gate",
    ]:
        print(f"{key}={report[key]}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
