from __future__ import annotations

import argparse
import sys
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run OpenYield C1 SRAM physical rule extraction.")
    parser.add_argument("--repo-root", required=True)
    parser.add_argument("--openram-root", required=True)
    parser.add_argument("--openyield-root", required=True)
    parser.add_argument("--c0-report-json", required=True)
    parser.add_argument("--c0-gap-dir", required=True)
    parser.add_argument("--r1-intent-dir", required=True)
    parser.add_argument("--r3-structure-dir", required=True)
    parser.add_argument("--r4-routing-dir", required=True)
    parser.add_argument("--module-gds-dir", required=True)
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
    from sram_layoutgen.openyield_adapter.sram_physical_rule_extraction import (
        SramPhysicalRuleExtractionConfig,
        SramPhysicalRuleExtractor,
    )

    config = SramPhysicalRuleExtractionConfig(
        repo_root=repo_root,
        openram_root=Path(args.openram_root).resolve(),
        openyield_root=Path(args.openyield_root).resolve(),
        c0_report_json=(repo_root / args.c0_report_json).resolve(),
        c0_gap_dir=(repo_root / args.c0_gap_dir).resolve(),
        r1_intent_dir=(repo_root / args.r1_intent_dir).resolve(),
        r3_structure_dir=(repo_root / args.r3_structure_dir).resolve(),
        r4_routing_dir=(repo_root / args.r4_routing_dir).resolve(),
        module_gds_dir=(repo_root / args.module_gds_dir).resolve(),
        out_dir=(repo_root / args.out_dir).resolve(),
        out_matrix_csv=(repo_root / args.out_matrix_csv).resolve(),
        out_matrix_md=(repo_root / args.out_matrix_md).resolve(),
        out_json=(repo_root / args.out_json).resolve(),
        out_report=(repo_root / args.out_report).resolve(),
    )
    SramPhysicalRuleExtractor(config).run()


if __name__ == "__main__":
    main()
