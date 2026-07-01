from __future__ import annotations

import argparse
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from sram_layoutgen.openyield_adapter.physical_primitive_library import (  # noqa: E402
    build_l1_physical_primitive_report,
    create_evidence_package,
    write_l1_evidence,
    write_l1_outputs,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="OpenYield L1 physical primitive closure inventory")
    parser.add_argument("--repo-root", required=True)
    parser.add_argument("--openyield-root", required=True)
    parser.add_argument("--l0-contract-json", required=True)
    parser.add_argument("--l0-control-contracts", required=True)
    parser.add_argument("--l0-time-contract", required=True)
    parser.add_argument("--l0-decoder-contract", required=True)
    parser.add_argument("--out-csv", required=True)
    parser.add_argument("--out-md", required=True)
    parser.add_argument("--out-module-deps-csv", required=True)
    parser.add_argument("--out-module-deps-md", required=True)
    parser.add_argument("--out-json", required=True)
    parser.add_argument("--out-report", required=True)
    parser.add_argument("--library-json", required=True)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    payload = build_l1_physical_primitive_report(
        repo_root=args.repo_root,
        openyield_root=args.openyield_root,
        l0_contract_json=args.l0_contract_json,
        l0_control_contracts=args.l0_control_contracts,
        l0_time_contract=args.l0_time_contract,
        l0_decoder_contract=args.l0_decoder_contract,
    )
    repo = Path(args.repo_root).resolve()
    write_l1_outputs(
        out_csv=args.out_csv,
        out_md=args.out_md,
        out_module_csv=args.out_module_deps_csv,
        out_module_md=args.out_module_deps_md,
        out_json=args.out_json,
        out_report=args.out_report,
        library_json=args.library_json,
        primitive_rows=payload["primitive_rows"],
        module_rows=payload["module_dependency_rows"],
        report=payload["report"],
        leaf_library=payload["leaf_library"],
    )
    write_l1_evidence(repo, payload["report"])
    if not payload["report"]["can_enter_L2_placement_abutment_rule_closure"]:
        pkg = create_evidence_package(repo)
        print(pkg)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
