from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
STANDALONE_ROOT = SCRIPT_DIR.parent
REPO_ROOT = STANDALONE_ROOT.parents[1]
if str(STANDALONE_ROOT) not in sys.path:
    sys.path.insert(0, str(STANDALONE_ROOT))

from sram_layoutgen.openyield_adapter.top_level_validation import (  # noqa: E402
    OpenYieldL5Validator,
    emit_validation_reports,
)


def main() -> int:
    parser = argparse.ArgumentParser(description="Run OpenYield L5 validation on the current top-level candidate GDS.")
    parser.add_argument("--repo-root", default=".")
    parser.add_argument("--openyield-root", required=True)
    parser.add_argument("--top-gds", required=True)
    parser.add_argument("--top-assembly-dir", required=True)
    parser.add_argument("--module-gds-dir", required=True)
    parser.add_argument("--module-gds-inventory", required=True)
    parser.add_argument("--top-assembly-inventory", required=True)
    parser.add_argument("--module-connection-matrix", required=True)
    parser.add_argument("--control-contracts", required=True)
    parser.add_argument("--time-contract", required=True)
    parser.add_argument("--l2-rule-library-json", required=True)
    parser.add_argument("--out-dir", required=True)
    parser.add_argument("--out-matrix-csv", required=True)
    parser.add_argument("--out-matrix-md", required=True)
    parser.add_argument("--out-json", required=True)
    parser.add_argument("--out-report", required=True)
    args = parser.parse_args()

    repo_root = resolve_input(args.repo_root)
    openyield_root = resolve_input(args.openyield_root)
    top_gds = resolve_input(args.top_gds)
    top_assembly_dir = resolve_input(args.top_assembly_dir)
    module_gds_dir = resolve_input(args.module_gds_dir)
    module_gds_inventory = resolve_input(args.module_gds_inventory)
    top_assembly_inventory = resolve_input(args.top_assembly_inventory)
    module_connection_matrix = resolve_input(args.module_connection_matrix)
    control_contracts = resolve_input(args.control_contracts)
    time_contract = resolve_input(args.time_contract)
    l2_rule_library_json = resolve_input(args.l2_rule_library_json)
    out_dir = resolve_output(args.out_dir)
    out_matrix_csv = resolve_output(args.out_matrix_csv)
    out_matrix_md = resolve_output(args.out_matrix_md)
    out_json = resolve_output(args.out_json)
    out_report = resolve_output(args.out_report)

    required = [
        top_gds,
        top_assembly_dir / "top_level_config.json",
        top_assembly_dir / "top_level_floorplan.json",
        top_assembly_dir / "module_placement.json",
        top_assembly_dir / "top_level_pin_map.json",
        top_assembly_dir / "top_level_rail_stitch_plan.json",
        top_assembly_dir / "top_level_routing_handoff.json",
        top_assembly_dir / "top_level_generator_manifest.json",
        top_assembly_dir / "top_level_generation_report.json",
        top_assembly_inventory,
        module_gds_inventory,
        control_contracts,
        time_contract,
        l2_rule_library_json,
        repo_root / "docs/openyield_L4_top_level_assembly_report.json",
    ]
    missing = [str(path) for path in required if not path.exists()]
    if missing:
        for item in missing:
            print(f"Missing required L4/L5 input: {item}", file=sys.stderr)
        return 2

    context = load_context(
        repo_root=repo_root,
        openyield_root=openyield_root,
        top_gds=top_gds,
        top_assembly_dir=top_assembly_dir,
        module_gds_dir=module_gds_dir,
        module_gds_inventory=module_gds_inventory,
        top_assembly_inventory=top_assembly_inventory,
        module_connection_matrix=module_connection_matrix,
        control_contracts=control_contracts,
        time_contract=time_contract,
        l2_rule_library_json=l2_rule_library_json,
        out_dir=out_dir,
    )
    report = OpenYieldL5Validator(context).run()
    emit_validation_reports(
        report=report,
        out_dir=out_dir,
        out_matrix_csv=out_matrix_csv,
        out_matrix_md=out_matrix_md,
        out_json=out_json,
        out_report=out_report,
        evidence_gap_summary=repo_root / "docs/evidence/L5_validation_gap_summary.md",
        evidence_timeline=repo_root / "docs/evidence/evidence_timeline.md",
        milestone_summary=repo_root / "docs/evidence/milestone_summary.md",
    )

    pkg_path = None
    if not report.summary["can_claim_L5_basic_validation_passed_now"]:
        pkg_path = create_evidence_package(repo_root)

    print(f"Wrote {out_dir}")
    print(f"Wrote {out_matrix_csv}")
    print(f"Wrote {out_matrix_md}")
    print(f"Wrote {out_json}")
    print(f"Wrote {out_report}")
    if pkg_path:
        print(f"L5 evidence package: {pkg_path}")
    print(f"top_gds_sanity_status={report.summary['top_gds_sanity_status']}")
    print(f"module_completeness_status={report.summary['module_completeness_status']}")
    print(f"placement_consistency_status={report.summary['placement_consistency_status']}")
    print(f"remaining_L5_basic_validation_blockers_count={report.summary['remaining_L5_basic_validation_blockers_count']}")
    print(f"can_claim_L5_basic_validation_passed_now={report.summary['can_claim_L5_basic_validation_passed_now']}")
    print(f"can_claim_validated_full_openyield_gds_now={report.summary['can_claim_validated_full_openyield_gds_now']}")
    return 0


def load_context(**paths: Path) -> dict:
    repo_root = paths["repo_root"]
    top_assembly_dir = paths["top_assembly_dir"]
    context = dict(paths)
    context.update(
        {
            "repo_head": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=repo_root, text=True).strip(),
            "top_level_config": load_json(top_assembly_dir / "top_level_config.json"),
            "top_level_floorplan": load_json(top_assembly_dir / "top_level_floorplan.json"),
            "module_placement": load_json(top_assembly_dir / "module_placement.json"),
            "top_level_pin_map": load_json(top_assembly_dir / "top_level_pin_map.json"),
            "top_level_rail_stitch_plan": load_json(top_assembly_dir / "top_level_rail_stitch_plan.json"),
            "top_level_routing_handoff": load_json(top_assembly_dir / "top_level_routing_handoff.json"),
            "top_level_generator_manifest": load_json(top_assembly_dir / "top_level_generator_manifest.json"),
            "top_level_generation_report": load_json(top_assembly_dir / "top_level_generation_report.json"),
            "top_level_assembly_inventory_rows": load_csv(paths["top_assembly_inventory"]),
            "module_gds_inventory_rows": load_csv(paths["module_gds_inventory"]),
            "module_connection_matrix_rows": load_csv(paths["module_connection_matrix"]),
            "control_contract_rows": load_csv(paths["control_contracts"]),
            "time_contract": load_json(paths["time_contract"]),
            "l2_rule_library": load_json(paths["l2_rule_library_json"]),
            "l4_report": load_json(repo_root / "docs/openyield_L4_top_level_assembly_report.json"),
            "pin_access_rule_rows": load_csv(repo_root / "docs/mapping/openyield_pin_access_rule_matrix.csv"),
            "rail_rule_rows": load_csv(repo_root / "docs/mapping/openyield_rail_rule_matrix.csv"),
            "timing_metadata_report": load_json(repo_root / "docs/openyield_delay_chain_timing_metadata_report.json"),
            "timing_metadata_summary_path": repo_root / "docs/evidence/timing_metadata_summary.md",
        }
    )
    return context


def create_evidence_package(repo_root: Path) -> Path:
    download_dir = repo_root.parent / "download_packages"
    download_dir.mkdir(parents=True, exist_ok=True)
    timestamp = subprocess.check_output(["date", "+%Y%m%d_%H%M%S"], text=True).strip()
    pkg = download_dir / f"openyield_L5_validation_evidence_{timestamp}.tar.gz"
    targets = [
        "docs/openyield_L5_validation_report.md",
        "docs/openyield_L5_validation_report.json",
        "docs/mapping/openyield_L5_validation_matrix.csv",
        "docs/mapping/openyield_L5_validation_matrix.md",
        "docs/evidence/L5_validation_gap_summary.md",
        "outputs/openyield_validation/current_supported_config",
    ]
    subprocess.run(["tar", "-czf", str(pkg), *targets], cwd=repo_root, check=False)
    return pkg


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def load_csv(path: Path) -> list[dict[str, str]]:
    import csv

    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


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
