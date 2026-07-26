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

from sram_layoutgen.openyield_adapter.final_handoff import (  # noqa: E402
    OpenYieldFinalHandoffBuilder,
    emit_step8_reports,
)


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


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
    return (Path.cwd() / value).resolve()


def build_context(args: argparse.Namespace) -> dict[str, object]:
    repo_root = resolve_input(args.repo_root)
    top_assembly_dir = resolve_input(args.top_assembly_dir)
    return {
        "repo_root": repo_root,
        "openyield_root": resolve_input(args.openyield_root),
        "step7_report_json": resolve_input(args.step7_report_json),
        "l5_report_json": resolve_input(args.l5_report_json),
        "l6_report_json": resolve_input(args.l6_report_json),
        "step7_closure_dir": resolve_input(args.step7_closure_dir),
        "top_gds": resolve_input(args.top_gds),
        "top_assembly_dir": top_assembly_dir,
        "validation_dir": resolve_input(args.validation_dir),
        "drc_triage_dir": resolve_input(args.drc_triage_dir),
        "out_dir": resolve_output(args.out_dir),
        "repo_head": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=repo_root, text=True).strip(),
        "step7_report": load_json(resolve_input(args.step7_report_json)),
        "l5_report": load_json(resolve_input(args.l5_report_json)),
        "l6_report": load_json(resolve_input(args.l6_report_json)),
        "top_manifest": load_json(top_assembly_dir / "top_level_generator_manifest.json"),
        "module_placement": load_json(top_assembly_dir / "module_placement.json"),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate Step 8 final handoff artifacts.")
    parser.add_argument("--repo-root", default=".")
    parser.add_argument("--openyield-root", required=True)
    parser.add_argument("--step7-report-json", required=True)
    parser.add_argument("--l5-report-json", required=True)
    parser.add_argument("--l6-report-json", required=True)
    parser.add_argument("--step7-closure-dir", required=True)
    parser.add_argument("--top-gds", required=True)
    parser.add_argument("--top-assembly-dir", required=True)
    parser.add_argument("--validation-dir", required=True)
    parser.add_argument("--drc-triage-dir", required=True)
    parser.add_argument("--out-dir", required=True)
    parser.add_argument("--out-json", required=True)
    parser.add_argument("--out-report", required=True)
    args = parser.parse_args()

    repo_root = resolve_input(args.repo_root)
    required = [
        resolve_input(args.step7_report_json),
        resolve_input(args.l5_report_json),
        resolve_input(args.l6_report_json),
        resolve_input(args.step7_closure_dir) / "final_repair_plan.md",
        resolve_input(args.step7_closure_dir) / "project_v1_capability_statement.md",
        resolve_input(args.step7_closure_dir) / "project_v1_limitation_statement.md",
        resolve_input(args.step7_closure_dir) / "future_work_roadmap.md",
        resolve_input(args.step7_closure_dir) / "final_handoff_checklist.md",
        resolve_input(args.top_gds),
        resolve_input(args.top_assembly_dir) / "top_level_generator_manifest.json",
        resolve_input(args.top_assembly_dir) / "module_placement.json",
        repo_root / "docs/openyield_L5_validation_report.md",
        repo_root / "docs/openyield_L6_drc_marker_triage_report.md",
        repo_root / "docs/mapping/openyield_L6_drc_marker_triage_matrix.csv",
        repo_root / "docs/mapping/openyield_L6_drc_marker_triage_matrix.md",
        repo_root / "docs/openyield_step7_final_repair_planning_report.md",
        repo_root / "docs/mapping/openyield_step7_final_repair_plan_matrix.csv",
        repo_root / "docs/mapping/openyield_step7_final_repair_plan_matrix.md",
        repo_root / "docs/evidence/evidence_timeline.md",
        repo_root / "docs/evidence/milestone_summary.md",
    ]
    missing = [str(path) for path in required if not path.exists()]
    if missing:
        for item in missing:
            print(f"Missing required Step 8 input: {item}", file=sys.stderr)
        return 2

    context = build_context(args)
    result = OpenYieldFinalHandoffBuilder(context).run()
    emit_step8_reports(
        result,
        out_json=resolve_output(args.out_json),
        out_report=resolve_output(args.out_report),
        evidence_summary=repo_root / "docs/evidence/step8_final_handoff_summary.md",
        evidence_timeline=repo_root / "docs/evidence/evidence_timeline.md",
        milestone_summary=repo_root / "docs/evidence/milestone_summary.md",
    )
    report = result["step8_report"]
    print(f"Wrote {resolve_output(args.out_json)}")
    print(f"Wrote {resolve_output(args.out_report)}")
    print(f"can_claim_final_handoff_completed_now={report['can_claim_final_handoff_completed_now']}")
    print(f"remaining_step8_blockers_count={report['remaining_step8_blockers_count']}")
    print(f"project_v1_status={report['project_v1_status']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
