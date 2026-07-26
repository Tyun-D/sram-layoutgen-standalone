from __future__ import annotations

import argparse
import sys
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run OpenYield C3 complete floorplan reconstruction.")
    parser.add_argument("--repo-root", required=True)
    parser.add_argument("--openyield-root", required=True)
    parser.add_argument("--c0-gap-dir", required=True)
    parser.add_argument("--c1-rule-dir", required=True)
    parser.add_argument("--c2-pin-access-dir", required=True)
    parser.add_argument("--r1-intent-dir", required=True)
    parser.add_argument("--r3-structure-dir", required=True)
    parser.add_argument("--r4-routing-dir", required=True)
    parser.add_argument("--layoutgen-reference-gds", required=True)
    parser.add_argument("--out-dir", required=True)
    parser.add_argument("--out-placement-csv", required=True)
    parser.add_argument("--out-placement-md", required=True)
    parser.add_argument("--out-json", required=True)
    parser.add_argument("--out-report", required=True)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    repo_root = Path(args.repo_root).resolve()
    if str(repo_root) not in sys.path:
        sys.path.insert(0, str(repo_root))
    from sram_layoutgen.openyield_adapter.complete_floorplan_reconstruction import (
        CompleteFloorplanReconstructionConfig,
        CompleteFloorplanReconstructor,
    )

    config = CompleteFloorplanReconstructionConfig(
        repo_root=repo_root,
        openyield_root=Path(args.openyield_root).resolve(),
        c0_gap_dir=(repo_root / args.c0_gap_dir).resolve(),
        c1_rule_dir=(repo_root / args.c1_rule_dir).resolve(),
        c2_pin_access_dir=(repo_root / args.c2_pin_access_dir).resolve(),
        r1_intent_dir=(repo_root / args.r1_intent_dir).resolve(),
        r3_structure_dir=(repo_root / args.r3_structure_dir).resolve(),
        r4_routing_dir=(repo_root / args.r4_routing_dir).resolve(),
        layoutgen_reference_gds=(repo_root / args.layoutgen_reference_gds).resolve(),
        out_dir=(repo_root / args.out_dir).resolve(),
        out_placement_csv=(repo_root / args.out_placement_csv).resolve(),
        out_placement_md=(repo_root / args.out_placement_md).resolve(),
        out_json=(repo_root / args.out_json).resolve(),
        out_report=(repo_root / args.out_report).resolve(),
    )
    CompleteFloorplanReconstructor(config).run()


if __name__ == "__main__":
    main()
