from __future__ import annotations

import argparse
import sys
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Restore optimized layoutgen SRAM flow and bind OpenYield semantics.")
    parser.add_argument("--repo-root", required=True)
    parser.add_argument("--status-md", required=True)
    parser.add_argument("--status-json", required=True)
    parser.add_argument("--m2r-dir", required=True)
    parser.add_argument("--m3r-dir", required=True)
    parser.add_argument("--openyield-intent-dir", required=True)
    parser.add_argument("--out-dir", required=True)
    parser.add_argument("--out-json", required=True)
    parser.add_argument("--out-report", required=True)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    repo_root = Path(args.repo_root).resolve()
    if str(repo_root) not in sys.path:
        sys.path.insert(0, str(repo_root))

    from sram_layoutgen.openyield_adapter.M3F_optimized_layoutgen_restore import run_m3f_optimized_layoutgen_restore

    report = run_m3f_optimized_layoutgen_restore(
        repo_root=repo_root,
        status_md=(repo_root / args.status_md).resolve(),
        status_json=(repo_root / args.status_json).resolve(),
        m2r_dir=(repo_root / args.m2r_dir).resolve(),
        m3r_dir=(repo_root / args.m3r_dir).resolve(),
        openyield_intent_dir=(repo_root / args.openyield_intent_dir).resolve(),
        out_dir=(repo_root / args.out_dir).resolve(),
        out_json=(repo_root / args.out_json).resolve(),
        out_report=(repo_root / args.out_report).resolve(),
    )
    print(f"full_sram_review_gds_path={report['full_sram_review_gds_path']}")
    print(f"top_cell_name={report['top_cell_name']}")
    print(f"power_rail_stitch_restored={report['power_rail_stitch_restored']}")
    print(f"openyield_physical_binding_count={report['openyield_physical_binding_count']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
