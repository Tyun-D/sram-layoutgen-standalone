from __future__ import annotations

import argparse
import sys
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build OpenYield R1 SRAM layout intent artifacts.")
    parser.add_argument("--repo-root", required=True)
    parser.add_argument("--openyield-root", required=True)
    parser.add_argument("--openram-audit-json", required=True)
    parser.add_argument("--openram-reuse-matrix", required=True)
    parser.add_argument("--canonical-contract", required=True)
    parser.add_argument("--top-bank-contract", required=True)
    parser.add_argument("--parameter-map", required=True)
    parser.add_argument("--module-connection-matrix", required=True)
    parser.add_argument("--decoder-wordline-contract", required=True)
    parser.add_argument("--time-control-contract", required=True)
    parser.add_argument("--control-path-contracts", required=True)
    parser.add_argument("--module-gds-inventory", required=True)
    parser.add_argument("--module-generator-inventory", required=True)
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
    from sram_layoutgen.openyield_adapter.layout_intent import LayoutIntentBuilder

    context = {
        "repo_root": repo_root,
        "openyield_root": Path(args.openyield_root).resolve(),
        "openram_audit_json": repo_root / args.openram_audit_json,
        "openram_reuse_matrix": repo_root / args.openram_reuse_matrix,
        "canonical_contract": repo_root / args.canonical_contract,
        "top_bank_contract": repo_root / args.top_bank_contract,
        "parameter_map": repo_root / args.parameter_map,
        "module_connection_matrix": repo_root / args.module_connection_matrix,
        "decoder_wordline_contract": repo_root / args.decoder_wordline_contract,
        "time_control_contract": repo_root / args.time_control_contract,
        "control_path_contracts": repo_root / args.control_path_contracts,
        "module_gds_inventory": repo_root / args.module_gds_inventory,
        "module_generator_inventory": repo_root / args.module_generator_inventory,
        "module_gds_dir": repo_root / args.module_gds_dir,
        "l5_report_json": repo_root / "docs/openyield_L5_validation_report.json",
        "l6_report_json": repo_root / "docs/openyield_L6_drc_marker_triage_report.json",
        "step8_report_json": repo_root / "docs/openyield_step8_final_handoff_report.json",
        "top_gds": repo_root / "outputs/openyield_top_level_assembly/current_supported_config/openyield_top_level_candidate.gds",
        "out_dir": repo_root / args.out_dir,
        "out_matrix_csv": repo_root / args.out_matrix_csv,
        "out_matrix_md": repo_root / args.out_matrix_md,
        "out_json": repo_root / args.out_json,
        "out_report": repo_root / args.out_report,
    }
    builder = LayoutIntentBuilder(context)
    builder.run()


if __name__ == "__main__":
    main()
