from __future__ import annotations

import argparse
import sys
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Evaluate OpenYield integration into the optimized layoutgen flow.")
    parser.add_argument("--repo-root", required=True)
    parser.add_argument("--status-md", required=True)
    parser.add_argument("--status-json", required=True)
    parser.add_argument("--m3f-dir", required=True)
    parser.add_argument("--m3f-report", required=True)
    parser.add_argument("--openyield-intent-dir", required=True)
    parser.add_argument("--openyield-module-gds-dir", required=True)
    parser.add_argument("--out-dir", required=True)
    parser.add_argument("--out-json", required=True)
    parser.add_argument("--out-report", required=True)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    repo_root = Path(args.repo_root).resolve()
    if str(repo_root) not in sys.path:
        sys.path.insert(0, str(repo_root))

    from sram_layoutgen.openyield_adapter.M4E_openyield_integration_feasibility import (
        run_m4e_openyield_integration_feasibility,
    )

    report = run_m4e_openyield_integration_feasibility(
        repo_root=repo_root,
        status_md=(repo_root / args.status_md).resolve(),
        status_json=(repo_root / args.status_json).resolve(),
        m3f_dir=(repo_root / args.m3f_dir).resolve(),
        m3f_report=(repo_root / args.m3f_report).resolve(),
        openyield_intent_dir=(repo_root / args.openyield_intent_dir).resolve(),
        openyield_module_gds_dir=(repo_root / args.openyield_module_gds_dir).resolve(),
        out_dir=(repo_root / args.out_dir).resolve(),
        out_json=(repo_root / args.out_json).resolve(),
        out_report=(repo_root / args.out_report).resolve(),
    )
    print(f"review_gds_path={report['review_gds_path']}")
    print(f"go_nogo_decision={report['go_nogo_decision']}")
    print(f"allowed_next_stage={report['allowed_next_stage']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
