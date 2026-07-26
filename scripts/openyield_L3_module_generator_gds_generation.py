from __future__ import annotations

import argparse
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
STANDALONE_ROOT = SCRIPT_DIR.parent
REPO_ROOT = STANDALONE_ROOT.parents[1]
if str(STANDALONE_ROOT) not in sys.path:
    sys.path.insert(0, str(STANDALONE_ROOT))

from sram_layoutgen.openyield_adapter.module_gds_generators import run_module_gds_generation  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate reproducible OpenYield L3 standalone module GDS artifacts.")
    parser.add_argument("--repo-root", default=".")
    parser.add_argument("--openyield-root", required=True)
    parser.add_argument("--l0-contract-json", required=True)
    parser.add_argument("--l1-library-json", required=True)
    parser.add_argument("--l1-composition-library-json", required=True)
    parser.add_argument("--l2-rule-library-json", required=True)
    parser.add_argument("--module-handoff-matrix", required=True)
    parser.add_argument("--out-dir", required=True)
    parser.add_argument("--out-generator-inventory-csv", required=True)
    parser.add_argument("--out-generator-inventory-md", required=True)
    parser.add_argument("--out-gds-inventory-csv", required=True)
    parser.add_argument("--out-gds-inventory-md", required=True)
    parser.add_argument("--out-json", required=True)
    parser.add_argument("--out-report", required=True)
    args = parser.parse_args()

    repo_root = resolve_input(args.repo_root)
    openyield_root = resolve_input(args.openyield_root)
    out_dir = resolve_output(args.out_dir)
    generator_inventory_csv = resolve_output(args.out_generator_inventory_csv)
    generator_inventory_md = resolve_output(args.out_generator_inventory_md)
    gds_inventory_csv = resolve_output(args.out_gds_inventory_csv)
    gds_inventory_md = resolve_output(args.out_gds_inventory_md)
    out_json = resolve_output(args.out_json)
    out_report = resolve_output(args.out_report)
    gap_summary = STANDALONE_ROOT / "docs/evidence/L3_module_generator_gds_gap_summary.md"

    reproducible_command = (
        "python scripts/openyield_L3_module_generator_gds_generation.py "
        f"--repo-root {repo_root} "
        f"--openyield-root {openyield_root} "
        f"--l0-contract-json {resolve_input(args.l0_contract_json)} "
        f"--l1-library-json {resolve_input(args.l1_library_json)} "
        f"--l1-composition-library-json {resolve_input(args.l1_composition_library_json)} "
        f"--l2-rule-library-json {resolve_input(args.l2_rule_library_json)} "
        f"--module-handoff-matrix {resolve_input(args.module_handoff_matrix)} "
        f"--out-dir {out_dir} "
        f"--out-generator-inventory-csv {generator_inventory_csv} "
        f"--out-generator-inventory-md {generator_inventory_md} "
        f"--out-gds-inventory-csv {gds_inventory_csv} "
        f"--out-gds-inventory-md {gds_inventory_md} "
        f"--out-json {out_json} "
        f"--out-report {out_report}"
    )

    generated = run_module_gds_generation(
        repo_root=repo_root,
        openyield_root=openyield_root,
        out_dir=out_dir,
        reproducible_command=reproducible_command,
        l0_contract_json=resolve_input(args.l0_contract_json),
        l1_library_json=resolve_input(args.l1_library_json),
        l1_composition_library_json=resolve_input(args.l1_composition_library_json),
        l2_rule_library_json=resolve_input(args.l2_rule_library_json),
        module_handoff_matrix=resolve_input(args.module_handoff_matrix),
        out_generator_inventory_csv=generator_inventory_csv,
        out_generator_inventory_md=generator_inventory_md,
        out_gds_inventory_csv=gds_inventory_csv,
        out_gds_inventory_md=gds_inventory_md,
        out_json=out_json,
        out_report=out_report,
        out_gap_summary=gap_summary,
    )
    report = generated["report"]

    print(f"Wrote {generator_inventory_csv}")
    print(f"Wrote {generator_inventory_md}")
    print(f"Wrote {gds_inventory_csv}")
    print(f"Wrote {gds_inventory_md}")
    print(f"Wrote {out_json}")
    print(f"Wrote {out_report}")
    print(f"Wrote {gap_summary}")
    print(f"module_generator_rows_count={report['module_generator_rows_count']}")
    print(f"module_gds_rows_count={report['module_gds_rows_count']}")
    print(f"remaining_L3_blockers_count={report['remaining_L3_blockers_count']}")
    print(f"can_claim_L3_module_generators_closed_now={report['can_claim_L3_module_generators_closed_now']}")
    print(f"can_claim_L3_standalone_module_gds_closed_now={report['can_claim_L3_standalone_module_gds_closed_now']}")
    print(f"can_enter_L4_top_level_assembly={report['can_enter_L4_top_level_assembly']}")
    print(f"can_claim_full_openyield_gds_now={report['can_claim_full_openyield_gds_now']}")
    return 0


def resolve_input(value: str) -> Path:
    path = Path(value)
    if path.is_absolute():
        return path
    for base in (Path.cwd(), STANDALONE_ROOT, REPO_ROOT):
        candidate = base / value
        if candidate.exists():
            return candidate
    return Path.cwd() / value


def resolve_output(value: str) -> Path:
    path = Path(value)
    if path.is_absolute():
        return path
    if Path.cwd().resolve() == REPO_ROOT.resolve():
        return STANDALONE_ROOT / value
    return Path.cwd() / value


if __name__ == "__main__":
    raise SystemExit(main())
