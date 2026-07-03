from __future__ import annotations

import argparse
import sys
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run OpenYield R5 final validation / comparison / handoff.")
    parser.add_argument("--repo-root", required=True)
    parser.add_argument("--openyield-root", required=True)
    parser.add_argument("--r1-report-json", required=True)
    parser.add_argument("--r2-report-json", required=True)
    parser.add_argument("--r3-report-json", required=True)
    parser.add_argument("--r4-report-json", required=True)
    parser.add_argument("--r3-structure-dir", required=True)
    parser.add_argument("--r4-routing-dir", required=True)
    parser.add_argument("--old-candidate-dir", required=True)
    parser.add_argument("--out-dir", required=True)
    parser.add_argument("--out-matrix-csv", required=True)
    parser.add_argument("--out-matrix-md", required=True)
    parser.add_argument("--out-json", required=True)
    parser.add_argument("--out-report", required=True)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    repo_root = Path(args.repo_root).resolve()
    if str(repo_root) not in sys.path:
        sys.path.insert(0, str(repo_root))
    from sram_layoutgen.openyield_adapter.final_validation_handoff import OpenYieldR5FinalHandoff

    context = {
        "repo_root": repo_root,
        "openyield_root": Path(args.openyield_root).resolve(),
        "r1_report_json": repo_root / args.r1_report_json,
        "r2_report_json": repo_root / args.r2_report_json,
        "r3_report_json": repo_root / args.r3_report_json,
        "r4_report_json": repo_root / args.r4_report_json,
        "r3_structure_dir": repo_root / args.r3_structure_dir,
        "r4_routing_dir": repo_root / args.r4_routing_dir,
        "old_candidate_dir": repo_root / args.old_candidate_dir,
        "out_dir": repo_root / args.out_dir,
        "out_matrix_csv": repo_root / args.out_matrix_csv,
        "out_matrix_md": repo_root / args.out_matrix_md,
        "out_json": repo_root / args.out_json,
        "out_report": repo_root / args.out_report,
    }
    OpenYieldR5FinalHandoff(context).run()


if __name__ == "__main__":
    main()
