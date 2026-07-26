from __future__ import annotations

import argparse
import sys
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Bind OpenYield semantics onto the preserved layoutgen SRAM backbone.")
    parser.add_argument("--repo-root", required=True)
    parser.add_argument("--status-md", required=True)
    parser.add_argument("--status-json", required=True)
    parser.add_argument("--m2r-dir", required=True)
    parser.add_argument("--m1-binding", required=True)
    parser.add_argument("--m1-net-binding", required=True)
    parser.add_argument("--openyield-module-gds-dir", required=True)
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

    from sram_layoutgen.openyield_adapter.M3R_openyield_semantic_bound import run_m3r_openyield_semantic_bound

    report = run_m3r_openyield_semantic_bound(
        repo_root=repo_root,
        status_md=(repo_root / args.status_md).resolve(),
        status_json=(repo_root / args.status_json).resolve(),
        m2r_dir=(repo_root / args.m2r_dir).resolve(),
        m1_binding=(repo_root / args.m1_binding).resolve(),
        m1_net_binding=(repo_root / args.m1_net_binding).resolve(),
        openyield_module_gds_dir=(repo_root / args.openyield_module_gds_dir).resolve(),
        openyield_intent_dir=(repo_root / args.openyield_intent_dir).resolve(),
        out_dir=(repo_root / args.out_dir).resolve(),
        out_json=(repo_root / args.out_json).resolve(),
        out_report=(repo_root / args.out_report).resolve(),
    )
    print(f"semantic_bound_gds_path={report['semantic_bound_gds_path']}")
    print(f"top_cell_name={report['top_cell_name']}")
    print(f"gds_sanity_status={report['gds_sanity_status']}")
    print(f"openyield_modules_bound_count={report['openyield_modules_bound_count']}")
    print(f"openyield_net_bound_count={report['openyield_net_bound_count']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
