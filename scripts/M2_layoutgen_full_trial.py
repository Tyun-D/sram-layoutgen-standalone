from __future__ import annotations

import argparse
import sys
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate M2 layoutgen-based OpenYield full SRAM trial review GDS.")
    parser.add_argument("--repo-root", required=True)
    parser.add_argument("--status-md", required=True)
    parser.add_argument("--status-json", required=True)
    parser.add_argument("--m1-binding", required=True)
    parser.add_argument("--m1-net-binding", required=True)
    parser.add_argument("--openyield-module-gds-dir", required=True)
    parser.add_argument("--layoutgen-reference-gds", required=True)
    parser.add_argument("--out-dir", required=True)
    parser.add_argument("--out-json", required=True)
    parser.add_argument("--out-report", required=True)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    repo_root = Path(args.repo_root).resolve()
    if str(repo_root) not in sys.path:
        sys.path.insert(0, str(repo_root))

    from sram_layoutgen.openyield_adapter.M2_layoutgen_full_trial import run_m2_full_trial

    report = run_m2_full_trial(
        repo_root=repo_root,
        status_md=(repo_root / args.status_md).resolve(),
        status_json=(repo_root / args.status_json).resolve(),
        m1_binding=(repo_root / args.m1_binding).resolve(),
        m1_net_binding=(repo_root / args.m1_net_binding).resolve(),
        openyield_module_gds_dir=(repo_root / args.openyield_module_gds_dir).resolve(),
        layoutgen_reference_gds=(repo_root / args.layoutgen_reference_gds).resolve(),
        out_dir=(repo_root / args.out_dir).resolve(),
        out_json=(repo_root / args.out_json).resolve(),
        out_report=(repo_root / args.out_report).resolve(),
    )
    print(f"M2 full SRAM review GDS: {report['full_sram_review_gds_path']}")
    print(f"top_cell_name={report['top_cell_name']}")
    print(f"gds_sanity_status={report['gds_sanity_status']}")
    print(f"modules_placed_count={report['modules_placed_count']}")
    print(f"temporary_wrapper_count={report['temporary_wrapper_count']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
