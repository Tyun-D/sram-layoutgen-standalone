from __future__ import annotations

import argparse
import sys
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", required=True)
    parser.add_argument("--openyield-root", required=True)
    parser.add_argument("--c0-gap-dir", required=True)
    parser.add_argument("--c1-rule-dir", required=True)
    parser.add_argument("--c2-pin-access-dir", required=True)
    parser.add_argument("--c3-floorplan-dir", required=True)
    parser.add_argument("--c4-signal-dir", required=True)
    parser.add_argument("--out-dir", required=True)
    parser.add_argument("--out-power-map-csv", required=True)
    parser.add_argument("--out-power-map-md", required=True)
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
    from sram_layoutgen.openyield_adapter.complete_power_network import (
        CompletePowerNetworkBuilder,
        CompletePowerNetworkConfig,
    )

    cfg = CompletePowerNetworkConfig(
        repo_root=repo_root,
        openyield_root=Path(args.openyield_root).resolve(),
        c0_gap_dir=(repo_root / args.c0_gap_dir).resolve(),
        c1_rule_dir=(repo_root / args.c1_rule_dir).resolve(),
        c2_pin_access_dir=(repo_root / args.c2_pin_access_dir).resolve(),
        c3_floorplan_dir=(repo_root / args.c3_floorplan_dir).resolve(),
        c4_signal_dir=(repo_root / args.c4_signal_dir).resolve(),
        out_dir=(repo_root / args.out_dir).resolve(),
        out_power_map_csv=(repo_root / args.out_power_map_csv).resolve(),
        out_power_map_md=(repo_root / args.out_power_map_md).resolve(),
        out_matrix_csv=(repo_root / args.out_matrix_csv).resolve(),
        out_matrix_md=(repo_root / args.out_matrix_md).resolve(),
        out_json=(repo_root / args.out_json).resolve(),
        out_report=(repo_root / args.out_report).resolve(),
    )
    CompletePowerNetworkBuilder(cfg).run()


if __name__ == "__main__":
    main()
