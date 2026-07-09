from __future__ import annotations

import argparse
import sys
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Qualify OpenYield module GDS for selective hardmacro substitution.")
    parser.add_argument("--repo-root", required=True)
    parser.add_argument("--status-md", required=True)
    parser.add_argument("--status-json", required=True)
    parser.add_argument("--goal-md", required=True)
    parser.add_argument("--progress-md", required=True)
    parser.add_argument("--module-gds-dir", required=True)
    parser.add_argument("--golden-reference", required=True)
    parser.add_argument("--m10-module-trace", required=True)
    parser.add_argument("--m10-net-trace", required=True)
    parser.add_argument("--m9-module-binding", required=True)
    parser.add_argument("--m9-net-binding", required=True)
    parser.add_argument("--m12-assets", required=True)
    parser.add_argument("--m12-backlog", required=True)
    parser.add_argument("--out-dir", required=True)
    parser.add_argument("--out-json", required=True)
    parser.add_argument("--out-report", required=True)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    repo_root = Path(args.repo_root).resolve()
    if str(repo_root) not in sys.path:
        sys.path.insert(0, str(repo_root))

    from sram_layoutgen.openyield_adapter.M11A_module_gds_qualification import run_m11a_module_gds_qualification

    report = run_m11a_module_gds_qualification(
        repo_root=repo_root,
        status_md=(repo_root / args.status_md).resolve(),
        status_json=(repo_root / args.status_json).resolve(),
        goal_md=(repo_root / args.goal_md).resolve(),
        progress_md=(repo_root / args.progress_md).resolve(),
        module_gds_dir=(repo_root / args.module_gds_dir).resolve(),
        golden_reference=(repo_root / args.golden_reference).resolve(),
        m10_module_trace=(repo_root / args.m10_module_trace).resolve(),
        m10_net_trace=(repo_root / args.m10_net_trace).resolve(),
        m9_module_binding=(repo_root / args.m9_module_binding).resolve(),
        m9_net_binding=(repo_root / args.m9_net_binding).resolve(),
        m12_assets=(repo_root / args.m12_assets).resolve(),
        m12_backlog=(repo_root / args.m12_backlog).resolve(),
        out_dir=(repo_root / args.out_dir).resolve(),
        out_json=(repo_root / args.out_json).resolve(),
        out_report=(repo_root / args.out_report).resolve(),
    )
    for key in [
        "module_gds_count",
        "direct_hardmacro_replace_count",
        "constraint_extraction_only_count",
        "semantic_reference_only_count",
        "rejected_count",
        "review_gds_path",
    ]:
        print(f"{key}={report[key]}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
