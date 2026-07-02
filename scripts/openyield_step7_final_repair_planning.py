from __future__ import annotations

import argparse
import csv
import json
import subprocess
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
STANDALONE_ROOT = SCRIPT_DIR.parent
REPO_ROOT = STANDALONE_ROOT.parents[1]
if str(STANDALONE_ROOT) not in sys.path:
    sys.path.insert(0, str(STANDALONE_ROOT))

from sram_layoutgen.openyield_adapter.final_repair_planning import (  # noqa: E402
    OpenYieldFinalRepairPlanner,
    emit_step7_reports,
)


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate Step 7 final repair planning / project closure artifacts.")
    parser.add_argument("--repo-root", default=".")
    parser.add_argument("--openyield-root", required=True)
    parser.add_argument("--l5-report-json", required=True)
    parser.add_argument("--l6-report-json", required=True)
    parser.add_argument("--l6-matrix-csv", required=True)
    parser.add_argument("--drc-rule-summary", required=True)
    parser.add_argument("--drc-root-cause", required=True)
    parser.add_argument("--drc-fix-priority", required=True)
    parser.add_argument("--drc-smoke-report", required=True)
    parser.add_argument("--lvs-feasibility-report", required=True)
    parser.add_argument("--candidate-risk-report", required=True)
    parser.add_argument("--top-gds", required=True)
    parser.add_argument("--top-assembly-dir", required=True)
    parser.add_argument("--out-dir", required=True)
    parser.add_argument("--out-matrix-csv", required=True)
    parser.add_argument("--out-matrix-md", required=True)
    parser.add_argument("--out-json", required=True)
    parser.add_argument("--out-report", required=True)
    args = parser.parse_args()

    repo_root = resolve_input(args.repo_root)
    top_assembly_dir = resolve_input(args.top_assembly_dir)
    out_dir = resolve_output(args.out_dir)

    required = [
        resolve_input(args.l5_report_json),
        resolve_input(args.l6_report_json),
        resolve_input(args.l6_matrix_csv),
        resolve_input(args.drc_rule_summary),
        resolve_input(args.drc_root_cause),
        resolve_input(args.drc_fix_priority),
        resolve_input(args.drc_smoke_report),
        resolve_input(args.lvs_feasibility_report),
        resolve_input(args.candidate_risk_report),
        resolve_input(args.top_gds),
        top_assembly_dir / "top_level_generator_manifest.json",
        top_assembly_dir / "module_placement.json",
        repo_root / "docs/openyield_L5_validation_report.md",
        repo_root / "docs/openyield_L6_drc_marker_triage_report.md",
        repo_root / "docs/evidence/L6_drc_marker_triage_gap_summary.md",
        repo_root / "outputs/openyield_validation/current_supported_config/pin_accessibility_audit.json",
        repo_root / "outputs/openyield_validation/current_supported_config/rail_stitch_audit.json",
        repo_root / "outputs/openyield_validation/current_supported_config/routing_handoff_audit.json",
    ]
    missing = [str(path) for path in required if not path.exists()]
    if missing:
        for item in missing:
            print(f"Missing required Step 7 input: {item}", file=sys.stderr)
        return 2

    context = load_context(
        repo_root=repo_root,
        openyield_root=resolve_input(args.openyield_root),
        l5_report_json=resolve_input(args.l5_report_json),
        l6_report_json=resolve_input(args.l6_report_json),
        l6_matrix_csv=resolve_input(args.l6_matrix_csv),
        drc_rule_summary=resolve_input(args.drc_rule_summary),
        drc_root_cause=resolve_input(args.drc_root_cause),
        drc_fix_priority=resolve_input(args.drc_fix_priority),
        drc_smoke_report=resolve_input(args.drc_smoke_report),
        lvs_feasibility_report=resolve_input(args.lvs_feasibility_report),
        candidate_risk_report=resolve_input(args.candidate_risk_report),
        top_gds=resolve_input(args.top_gds),
        top_assembly_dir=top_assembly_dir,
        out_dir=out_dir,
    )
    report = OpenYieldFinalRepairPlanner(context).run()
    emit_step7_reports(
        report,
        out_matrix_csv=resolve_output(args.out_matrix_csv),
        out_matrix_md=resolve_output(args.out_matrix_md),
        out_json=resolve_output(args.out_json),
        out_report=resolve_output(args.out_report),
        evidence_gap_summary=repo_root / "docs/evidence/step7_final_repair_planning_gap_summary.md",
        evidence_timeline=repo_root / "docs/evidence/evidence_timeline.md",
        milestone_summary=repo_root / "docs/evidence/milestone_summary.md",
    )

    pkg_path = None
    if not report.summary["can_claim_project_v1_closure_ready"]:
        pkg_path = create_evidence_package(repo_root)

    print(f"Wrote {out_dir}")
    print(f"Wrote {resolve_output(args.out_json)}")
    print(f"Wrote {resolve_output(args.out_report)}")
    if pkg_path:
        print(f"Step 7 evidence package: {pkg_path}")
    print(f"can_claim_project_v1_closure_ready={report.summary['can_claim_project_v1_closure_ready']}")
    print(f"can_enter_step8_final_report_handoff={report.summary['can_enter_step8_final_report_handoff']}")
    print(f"top_repair_priority={report.summary['top_repair_priority']}")
    print(f"top_repair_root_cause={report.summary['top_repair_root_cause']}")
    return 0


def load_context(**paths: Path) -> dict[str, object]:
    repo_root = paths["repo_root"]
    top_assembly_dir = paths["top_assembly_dir"]
    return {
        **paths,
        "repo_head": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=repo_root, text=True).strip(),
        "l5_report": load_json(paths["l5_report_json"]),
        "l6_report": load_json(paths["l6_report_json"]),
        "l6_matrix_rows": load_csv(paths["l6_matrix_csv"]),
        "l6_rule_summary": load_json(paths["drc_rule_summary"]),
        "l6_root_cause": load_json(paths["drc_root_cause"]),
        "l6_fix_priority": load_json(paths["drc_fix_priority"]),
        "drc_smoke_report": load_json(paths["drc_smoke_report"]),
        "lvs_feasibility_report": load_json(paths["lvs_feasibility_report"]),
        "candidate_risk_report": load_json(paths["candidate_risk_report"]),
        "pin_access_audit": load_json(repo_root / "outputs/openyield_validation/current_supported_config/pin_accessibility_audit.json"),
        "rail_stitch_audit": load_json(repo_root / "outputs/openyield_validation/current_supported_config/rail_stitch_audit.json"),
        "routing_handoff_audit": load_json(repo_root / "outputs/openyield_validation/current_supported_config/routing_handoff_audit.json"),
        "top_manifest": load_json(top_assembly_dir / "top_level_generator_manifest.json"),
        "module_placement": load_json(top_assembly_dir / "module_placement.json"),
        "l5_report_md_path": repo_root / "docs/openyield_L5_validation_report.md",
        "l6_report_md_path": repo_root / "docs/openyield_L6_drc_marker_triage_report.md",
        "top_hierarchy_diag_path": repo_root / "outputs/openyield_validation/current_supported_config/top_gds_hierarchy_diagnosis.json",
        "l6_fix_priority_path": paths["drc_fix_priority"],
        "candidate_risk_report_path": paths["candidate_risk_report"],
        "lvs_feasibility_report_path": paths["lvs_feasibility_report"],
        "drc_smoke_report_path": paths["drc_smoke_report"],
        "pin_access_audit_path": repo_root / "outputs/openyield_validation/current_supported_config/pin_accessibility_audit.json",
        "module_placement_path": top_assembly_dir / "module_placement.json",
        "top_manifest_path": top_assembly_dir / "top_level_generator_manifest.json",
        "module_gds_inventory_path": repo_root / "docs/mapping/openyield_module_gds_inventory.csv",
        "module_gds_dir": repo_root / "outputs/openyield_module_gds",
        "l2_rule_library_json": repo_root / "technology/freepdk45/openyield_L2_placement_abutment_rule_library.json",
    }


def create_evidence_package(repo_root: Path) -> Path:
    download_dir = repo_root.parent / "download_packages"
    download_dir.mkdir(parents=True, exist_ok=True)
    timestamp = subprocess.check_output(["date", "+%Y%m%d_%H%M%S"], text=True).strip()
    pkg = download_dir / f"openyield_step7_final_repair_planning_evidence_{timestamp}.tar.gz"
    targets = [
        "docs/openyield_step7_final_repair_planning_report.md",
        "docs/openyield_step7_final_repair_planning_report.json",
        "docs/mapping/openyield_step7_final_repair_plan_matrix.csv",
        "docs/mapping/openyield_step7_final_repair_plan_matrix.md",
        "docs/evidence/step7_final_repair_planning_gap_summary.md",
        "outputs/openyield_project_closure/current_supported_config",
    ]
    subprocess.run(["tar", "-czf", str(pkg), *targets], cwd=repo_root, check=False)
    return pkg


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def load_csv(path: Path) -> list[dict[str, str]]:
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
