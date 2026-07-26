from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
STANDALONE_ROOT = SCRIPT_DIR.parent
REPO_ROOT = STANDALONE_ROOT.parents[1]
if str(STANDALONE_ROOT) not in sys.path:
    sys.path.insert(0, str(STANDALONE_ROOT))

from sram_layoutgen.openyield_adapter.top_level_assembly import run_top_level_assembly  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description="Assemble reproducible OpenYield L4 top-level candidate GDS artifacts.")
    parser.add_argument("--repo-root", default=".")
    parser.add_argument("--openyield-root", required=True)
    parser.add_argument("--module-gds-inventory", required=True)
    parser.add_argument("--module-generator-inventory", required=True)
    parser.add_argument("--module-gds-dir", required=True)
    parser.add_argument("--l0-contract-json", required=True)
    parser.add_argument("--l2-rule-library-json", required=True)
    parser.add_argument("--out-dir", required=True)
    parser.add_argument("--out-inventory-csv", required=True)
    parser.add_argument("--out-inventory-md", required=True)
    parser.add_argument("--out-json", required=True)
    parser.add_argument("--out-report", required=True)
    args = parser.parse_args()

    repo_root = resolve_input(args.repo_root)
    openyield_root = resolve_input(args.openyield_root)
    module_gds_inventory = resolve_input(args.module_gds_inventory)
    module_generator_inventory = resolve_input(args.module_generator_inventory)
    module_gds_dir = resolve_input(args.module_gds_dir)
    l0_contract_json = resolve_input(args.l0_contract_json)
    l2_rule_library_json = resolve_input(args.l2_rule_library_json)
    out_dir = resolve_output(args.out_dir)
    out_inventory_csv = resolve_output(args.out_inventory_csv)
    out_inventory_md = resolve_output(args.out_inventory_md)
    out_json = resolve_output(args.out_json)
    out_report = resolve_output(args.out_report)

    reproducible_command = (
        "python scripts/openyield_L4_top_level_assembly.py "
        f"--repo-root {repo_root} "
        f"--openyield-root {openyield_root} "
        f"--module-gds-inventory {module_gds_inventory} "
        f"--module-generator-inventory {module_generator_inventory} "
        f"--module-gds-dir {module_gds_dir} "
        f"--l0-contract-json {l0_contract_json} "
        f"--l2-rule-library-json {l2_rule_library_json} "
        f"--out-dir {out_dir} "
        f"--out-inventory-csv {out_inventory_csv} "
        f"--out-inventory-md {out_inventory_md} "
        f"--out-json {out_json} "
        f"--out-report {out_report}"
    )

    result = run_top_level_assembly(
        repo_root=repo_root,
        openyield_root=openyield_root,
        module_gds_inventory=module_gds_inventory,
        module_generator_inventory=module_generator_inventory,
        module_gds_dir=module_gds_dir,
        l0_contract_json=l0_contract_json,
        l2_rule_library_json=l2_rule_library_json,
        out_dir=out_dir,
        out_inventory_csv=out_inventory_csv,
        out_inventory_md=out_inventory_md,
        out_json=out_json,
        out_report=out_report,
        reproducible_command=reproducible_command,
    )

    pkg_path = create_evidence_package(repo_root)
    print(f"Wrote {out_dir / 'openyield_top_level_candidate.gds'}")
    print(f"Wrote {out_dir / 'top_level_config.json'}")
    print(f"Wrote {out_dir / 'module_placement.json'}")
    print(f"Wrote {out_dir / 'top_level_pin_map.json'}")
    print(f"Wrote {out_dir / 'top_level_rail_stitch_plan.json'}")
    print(f"Wrote {out_dir / 'top_level_routing_handoff.json'}")
    print(f"Wrote {out_inventory_csv}")
    print(f"Wrote {out_inventory_md}")
    print(f"Wrote {out_json}")
    print(f"Wrote {out_report}")
    print(f"L4 evidence package: {pkg_path}")
    print(f"required_l3_modules_count={result.report['required_l3_modules_count']}")
    print(f"required_l3_modules_instantiated_count={result.report['required_l3_modules_instantiated_count']}")
    print(f"remaining_L4_blockers_count={result.report['remaining_L4_blockers_count']}")
    print(f"can_claim_L4_top_level_candidate_gds_generated_now={result.report['can_claim_L4_top_level_candidate_gds_generated_now']}")
    print(f"can_enter_L5_validation={result.report['can_enter_L5_validation']}")
    print(f"can_claim_validated_full_openyield_gds_now={result.report['can_claim_validated_full_openyield_gds_now']}")
    return 0


def create_evidence_package(repo_root: Path) -> Path:
    download_dir = repo_root.parent / "download_packages"
    download_dir.mkdir(parents=True, exist_ok=True)
    timestamp = subprocess.check_output(["date", "+%Y%m%d_%H%M%S"], text=True).strip()
    pkg = download_dir / f"openyield_L4_top_level_assembly_evidence_{timestamp}.tar.gz"
    targets = [
        "docs/mapping/openyield_top_level_assembly_inventory.csv",
        "docs/mapping/openyield_top_level_assembly_inventory.md",
        "docs/openyield_L4_top_level_assembly_report.md",
        "docs/openyield_L4_top_level_assembly_report.json",
        "docs/evidence/L4_top_level_assembly_gap_summary.md",
        "outputs/openyield_top_level_assembly",
    ]
    subprocess.run(["tar", "-czf", str(pkg), *targets], cwd=repo_root, check=False)
    return pkg


def resolve_input(value: str) -> Path:
    path = Path(value)
    if path.is_absolute():
        return path
    for base in (Path.cwd(), STANDALONE_ROOT, REPO_ROOT):
        candidate = base / value
        if candidate.exists():
            return candidate.resolve()
    return (Path.cwd() / value).resolve()


def resolve_output(value: str) -> Path:
    path = Path(value)
    if path.is_absolute():
        return path
    if Path.cwd().resolve() == REPO_ROOT.resolve():
        return (STANDALONE_ROOT / value).resolve()
    return (Path.cwd() / value).resolve()


if __name__ == "__main__":
    raise SystemExit(main())
