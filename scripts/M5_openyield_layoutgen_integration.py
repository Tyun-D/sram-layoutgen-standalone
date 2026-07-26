from __future__ import annotations

import argparse
import sys
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Implement OpenYield integration into the optimized layoutgen flow.")
    parser.add_argument("--repo-root", required=True)
    parser.add_argument("--status-md", required=True)
    parser.add_argument("--status-json", required=True)
    parser.add_argument("--m3f-dir", required=True)
    parser.add_argument("--m4e-dir", required=True)
    parser.add_argument("--m4e-report", required=True)
    parser.add_argument("--m4e-binding", required=True)
    parser.add_argument("--m4e-code-matrix", required=True)
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

    from sram_layoutgen.openyield_adapter.M5_openyield_layoutgen_integration import (
        run_m5_openyield_layoutgen_integration,
    )

    report = run_m5_openyield_layoutgen_integration(
        repo_root=repo_root,
        status_md=(repo_root / args.status_md).resolve(),
        status_json=(repo_root / args.status_json).resolve(),
        m3f_dir=(repo_root / args.m3f_dir).resolve(),
        m4e_dir=(repo_root / args.m4e_dir).resolve(),
        m4e_report=(repo_root / args.m4e_report).resolve(),
        m4e_binding=(repo_root / args.m4e_binding).resolve(),
        m4e_code_matrix=(repo_root / args.m4e_code_matrix).resolve(),
        openyield_intent_dir=(repo_root / args.openyield_intent_dir).resolve(),
        out_dir=(repo_root / args.out_dir).resolve(),
        out_json=(repo_root / args.out_json).resolve(),
        out_report=(repo_root / args.out_report).resolve(),
    )
    print(f"integrated_gds_path={report['integrated_gds_path']}")
    print(f"openyield_modules_implemented_count={report['openyield_modules_implemented_count']}")
    print(f"openyield_nets_implemented_count={report['openyield_nets_implemented_count']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
