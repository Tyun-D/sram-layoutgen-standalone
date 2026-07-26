from __future__ import annotations

import argparse
import sys
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Clean M5 review GDS and inventory OpenYield files.")
    parser.add_argument("--repo-root", required=True)
    parser.add_argument("--status-md", required=True)
    parser.add_argument("--status-json", required=True)
    parser.add_argument("--m5-gds", required=True)
    parser.add_argument("--openyield-root", required=True)
    parser.add_argument("--out-clean-dir", required=True)
    parser.add_argument("--out-inventory-dir", required=True)
    parser.add_argument("--out-json", required=True)
    parser.add_argument("--out-report", required=True)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    repo_root = Path(args.repo_root).resolve()
    if str(repo_root) not in sys.path:
        sys.path.insert(0, str(repo_root))

    from sram_layoutgen.openyield_adapter.T1_openyield_file_inventory import (
        run_t1_openyield_file_inventory,
    )

    report = run_t1_openyield_file_inventory(
        repo_root=repo_root,
        status_md=(repo_root / args.status_md).resolve(),
        status_json=(repo_root / args.status_json).resolve(),
        m5_gds=(repo_root / args.m5_gds).resolve(),
        openyield_root=Path(args.openyield_root).resolve(),
        out_clean_dir=(repo_root / args.out_clean_dir).resolve(),
        out_inventory_dir=(repo_root / args.out_inventory_dir).resolve(),
        out_json=(repo_root / args.out_json).resolve(),
        out_report=(repo_root / args.out_report).resolve(),
    )
    print(f"clean_review_gds_path={report['clean_review_gds_path']}")
    print(f"removed_text_count={report['removed_text_count']}")
    print(f"openyield_file_count_total={report['openyield_file_count_total']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
