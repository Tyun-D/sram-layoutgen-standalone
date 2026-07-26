from __future__ import annotations

import argparse
import sys
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Audit the ten required assets for netlist-to-layout generation.")
    parser.add_argument("--repo-root", required=True)
    parser.add_argument("--status-md", required=True)
    parser.add_argument("--status-json", required=True)
    parser.add_argument("--openyield-root", required=True)
    parser.add_argument("--out-dir", required=True)
    parser.add_argument("--out-json", required=True)
    parser.add_argument("--out-report", required=True)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    repo_root = Path(args.repo_root).resolve()
    if str(repo_root) not in sys.path:
        sys.path.insert(0, str(repo_root))

    from sram_layoutgen.openyield_adapter.M12_ten_asset_audit import run_m12_ten_asset_audit

    report = run_m12_ten_asset_audit(
        repo_root=repo_root,
        status_md=(repo_root / args.status_md).resolve(),
        status_json=(repo_root / args.status_json).resolve(),
        openyield_root=Path(args.openyield_root).resolve(),
        out_dir=(repo_root / args.out_dir).resolve(),
        out_json=(repo_root / args.out_json).resolve(),
        out_report=(repo_root / args.out_report).resolve(),
    )
    for key in [
        "asset_count_total",
        "asset_complete_count",
        "asset_partial_count",
        "asset_missing_count",
        "blocking_asset_count",
        "recommended_next_stage",
    ]:
        print(f"{key}={report[key]}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
