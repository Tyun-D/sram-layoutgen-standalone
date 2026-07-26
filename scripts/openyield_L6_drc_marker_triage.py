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

from sram_layoutgen.openyield_adapter.drc_marker_triage import (  # noqa: E402
    OpenYieldDrcMarkerTriage,
    emit_triage_reports,
)


def main() -> int:
    parser = argparse.ArgumentParser(description="Run OpenYield L6 DRC marker triage.")
    parser.add_argument("--repo-root", default=".")
    parser.add_argument("--openyield-root", required=True)
    parser.add_argument("--top-gds", required=True)
    parser.add_argument("--top-assembly-dir", required=True)
    parser.add_argument("--validation-dir", required=True)
    parser.add_argument("--module-gds-dir", required=True)
    parser.add_argument("--module-placement", required=True)
    parser.add_argument("--rail-stitch-plan", required=True)
    parser.add_argument("--routing-handoff", required=True)
    parser.add_argument("--top-pin-map", required=True)
    parser.add_argument("--l5-report-json", required=True)
    parser.add_argument("--module-gds-inventory", required=True)
    parser.add_argument("--top-assembly-inventory", required=True)
    parser.add_argument("--l2-rule-library-json", required=True)
    parser.add_argument("--out-dir", required=True)
    parser.add_argument("--out-matrix-csv", required=True)
    parser.add_argument("--out-matrix-md", required=True)
    parser.add_argument("--out-json", required=True)
    parser.add_argument("--out-report", required=True)
    args = parser.parse_args()

    repo_root = resolve_input(args.repo_root)
    top_assembly_dir = resolve_input(args.top_assembly_dir)
    validation_dir = resolve_input(args.validation_dir)
    module_gds_dir = resolve_input(args.module_gds_dir)
    out_dir = resolve_output(args.out_dir)

    required = [
        resolve_input(args.top_gds),
        resolve_input(args.module_placement),
        resolve_input(args.rail_stitch_plan),
        resolve_input(args.routing_handoff),
        resolve_input(args.top_pin_map),
        resolve_input(args.l5_report_json),
        resolve_input(args.module_gds_inventory),
        resolve_input(args.top_assembly_inventory),
        resolve_input(args.l2_rule_library_json),
        top_assembly_dir / "top_level_floorplan.json",
        top_assembly_dir / "top_level_generator_manifest.json",
        validation_dir / "drc_smoke_report.json",
        validation_dir / "candidate_geometry_risk_report.json",
        validation_dir / "rail_stitch_audit.json",
        validation_dir / "routing_handoff_audit.json",
        validation_dir / "pin_accessibility_audit.json",
        validation_dir / "top_gds_hierarchy_diagnosis.json",
        validation_dir / "top_level_candidate_drc.lyrdb",
        repo_root / "docs/mapping/openyield_placement_rule_matrix.csv",
        repo_root / "docs/mapping/openyield_abutment_rule_matrix.csv",
        repo_root / "docs/mapping/openyield_rail_rule_matrix.csv",
        repo_root / "docs/mapping/openyield_orientation_policy_matrix.csv",
        repo_root / "docs/mapping/openyield_pin_access_rule_matrix.csv",
    ]
    missing = [str(path) for path in required if not path.exists()]
    if missing:
        for item in missing:
            print(f"Missing required L6 input: {item}", file=sys.stderr)
        return 2

    context = load_context(
        repo_root=repo_root,
        openyield_root=resolve_input(args.openyield_root),
        top_gds=resolve_input(args.top_gds),
        top_assembly_dir=top_assembly_dir,
        validation_dir=validation_dir,
        module_gds_dir=module_gds_dir,
        module_placement=resolve_input(args.module_placement),
        rail_stitch_plan=resolve_input(args.rail_stitch_plan),
        routing_handoff=resolve_input(args.routing_handoff),
        top_pin_map=resolve_input(args.top_pin_map),
        l5_report_json=resolve_input(args.l5_report_json),
        module_gds_inventory=resolve_input(args.module_gds_inventory),
        top_assembly_inventory=resolve_input(args.top_assembly_inventory),
        l2_rule_library_json=resolve_input(args.l2_rule_library_json),
        out_dir=out_dir,
    )
    report = OpenYieldDrcMarkerTriage(context).run()
    emit_triage_reports(
        report,
        out_matrix_csv=resolve_output(args.out_matrix_csv),
        out_matrix_md=resolve_output(args.out_matrix_md),
        out_json=resolve_output(args.out_json),
        out_report=resolve_output(args.out_report),
        evidence_gap_summary=repo_root / "docs/evidence/L6_drc_marker_triage_gap_summary.md",
        evidence_timeline=repo_root / "docs/evidence/evidence_timeline.md",
        milestone_summary=repo_root / "docs/evidence/milestone_summary.md",
    )

    pkg_path = None
    if not report.summary["can_claim_L6_drc_triage_completed_now"]:
        pkg_path = create_evidence_package(repo_root)

    print(f"Wrote {out_dir}")
    print(f"Wrote {resolve_output(args.out_json)}")
    print(f"Wrote {resolve_output(args.out_report)}")
    if pkg_path:
        print(f"L6 evidence package: {pkg_path}")
    print(f"drc_marker_total_count={report.summary['drc_marker_total_count']}")
    print(f"drc_marker_classification_coverage={report.summary['drc_marker_classification_coverage']}")
    print(f"top_root_cause_category={report.summary['top_root_cause_category']}")
    print(f"remaining_L6_triage_blockers_count={report.summary['remaining_L6_triage_blockers_count']}")
    print(f"can_claim_L6_drc_triage_completed_now={report.summary['can_claim_L6_drc_triage_completed_now']}")
    print(f"can_enter_L7_drc_repair_planning={report.summary['can_enter_L7_drc_repair_planning']}")
    return 0


def load_context(**paths: Path) -> dict[str, object]:
    repo_root = paths["repo_root"]
    top_assembly_dir = paths["top_assembly_dir"]
    validation_dir = paths["validation_dir"]
    context: dict[str, object] = dict(paths)
    context.update(
        {
            "repo_head": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=repo_root, text=True).strip(),
            "module_placement": load_json(paths["module_placement"]),
            "top_level_floorplan": load_json(top_assembly_dir / "top_level_floorplan.json"),
            "top_level_pin_map": load_json(paths["top_pin_map"]),
            "top_level_rail_stitch_plan": load_json(paths["rail_stitch_plan"]),
            "top_level_routing_handoff": load_json(paths["routing_handoff"]),
            "top_level_generator_manifest": load_json(top_assembly_dir / "top_level_generator_manifest.json"),
            "drc_smoke_report": load_json(validation_dir / "drc_smoke_report.json"),
            "candidate_geometry_risk_report": load_json(validation_dir / "candidate_geometry_risk_report.json"),
            "rail_stitch_audit": load_json(validation_dir / "rail_stitch_audit.json"),
            "routing_handoff_audit": load_json(validation_dir / "routing_handoff_audit.json"),
            "pin_accessibility_audit": load_json(validation_dir / "pin_accessibility_audit.json"),
            "top_gds_hierarchy_diagnosis": load_json(validation_dir / "top_gds_hierarchy_diagnosis.json"),
            "l5_report": load_json(paths["l5_report_json"]),
            "module_gds_inventory_rows": load_csv(paths["module_gds_inventory"]),
            "top_assembly_inventory_rows": load_csv(paths["top_assembly_inventory"]),
            "placement_rule_rows": load_csv(repo_root / "docs/mapping/openyield_placement_rule_matrix.csv"),
            "abutment_rule_rows": load_csv(repo_root / "docs/mapping/openyield_abutment_rule_matrix.csv"),
            "rail_rule_rows": load_csv(repo_root / "docs/mapping/openyield_rail_rule_matrix.csv"),
            "orientation_policy_rows": load_csv(repo_root / "docs/mapping/openyield_orientation_policy_matrix.csv"),
            "pin_access_rule_rows": load_csv(repo_root / "docs/mapping/openyield_pin_access_rule_matrix.csv"),
            "l2_rule_library": load_json(paths["l2_rule_library_json"]),
            "lyrdb_path": validation_dir / "top_level_candidate_drc.lyrdb",
            "module_metadata": load_module_metadata(paths["module_gds_dir"]),
        }
    )
    return context


def load_module_metadata(module_gds_dir: Path) -> dict[str, dict[str, object]]:
    data: dict[str, dict[str, object]] = {}
    for module_dir in sorted(module_gds_dir.iterdir()):
        if not module_dir.is_dir():
            continue
        module = module_dir.name
        payload: dict[str, object] = {}
        for name in ["bbox.json", "pins.json", "rail_report.json", "generation_report.json", "generator_manifest.json"]:
            path = module_dir / name
            if path.exists():
                payload[name[:-5]] = load_json(path)
        data[module] = payload
    return data


def create_evidence_package(repo_root: Path) -> Path:
    download_dir = repo_root.parent / "download_packages"
    download_dir.mkdir(parents=True, exist_ok=True)
    timestamp = subprocess.check_output(["date", "+%Y%m%d_%H%M%S"], text=True).strip()
    pkg = download_dir / f"openyield_L6_drc_marker_triage_evidence_{timestamp}.tar.gz"
    targets = [
        "docs/openyield_L6_drc_marker_triage_report.md",
        "docs/openyield_L6_drc_marker_triage_report.json",
        "docs/mapping/openyield_L6_drc_marker_triage_matrix.csv",
        "docs/mapping/openyield_L6_drc_marker_triage_matrix.md",
        "docs/evidence/L6_drc_marker_triage_gap_summary.md",
        "outputs/openyield_drc_triage/current_supported_config",
        "outputs/openyield_validation/current_supported_config/drc_smoke_report.json",
        "outputs/openyield_top_level_assembly/current_supported_config/module_placement.json",
        "outputs/openyield_top_level_assembly/current_supported_config/top_level_rail_stitch_plan.json",
        "outputs/openyield_top_level_assembly/current_supported_config/top_level_routing_handoff.json",
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
