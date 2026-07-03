from __future__ import annotations

import argparse
import sys
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate OpenYield R4 routing/power/pin/net-mapping prototype artifacts.")
    parser.add_argument("--repo-root", required=True)
    parser.add_argument("--openyield-root", required=True)
    parser.add_argument("--r1-intent-dir", required=True)
    parser.add_argument("--r2-architecture-dir", required=True)
    parser.add_argument("--r3-structure-dir", required=True)
    parser.add_argument("--module-gds-dir", required=True)
    parser.add_argument("--module-gds-inventory", required=True)
    parser.add_argument("--module-generator-inventory", required=True)
    parser.add_argument("--out-dir", required=True)
    parser.add_argument("--out-net-to-shape-csv", required=True)
    parser.add_argument("--out-net-to-shape-md", required=True)
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
    from sram_layoutgen.openyield_adapter.routing_power_pin import OpenYieldRoutingPowerPinGenerator

    context = {
        "repo_root": repo_root,
        "openyield_root": Path(args.openyield_root).resolve(),
        "r1_intent_dir": repo_root / args.r1_intent_dir,
        "r2_architecture_dir": repo_root / args.r2_architecture_dir,
        "r3_structure_dir": repo_root / args.r3_structure_dir,
        "module_gds_dir": repo_root / args.module_gds_dir,
        "module_gds_inventory": repo_root / args.module_gds_inventory,
        "module_generator_inventory": repo_root / args.module_generator_inventory,
        "out_dir": repo_root / args.out_dir,
        "out_net_to_shape_csv": repo_root / args.out_net_to_shape_csv,
        "out_net_to_shape_md": repo_root / args.out_net_to_shape_md,
        "out_matrix_csv": repo_root / args.out_matrix_csv,
        "out_matrix_md": repo_root / args.out_matrix_md,
        "out_json": repo_root / args.out_json,
        "out_report": repo_root / args.out_report,
    }
    OpenYieldRoutingPowerPinGenerator(context).run()


if __name__ == "__main__":
    main()
