from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
import sys

if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from sram_layoutgen.openyield_adapter.teamb_9cell_integration_gate import log_teamb_event, recompute_current_status, run_teamb_9cell_integration


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", default=str(REPO_ROOT))
    parser.add_argument("--openyield-root", default="/data1/qujh/work/external/OpenYield")
    parser.add_argument("--klayout-bin", default="/usr/bin/klayout")
    parser.add_argument("--drc-deck", default="technology/freepdk45/tech/freepdk45.lydrc")
    parser.add_argument("--resume", action="store_true")
    parser.add_argument("--rebuild-failed", action="store_true")
    parser.add_argument("--resume-negative-tests", action="store_true")
    parser.add_argument("--scratch-root", default="/tmp/qujh_teamb9cell_scratch")
    parser.add_argument("--cleanup-completed-scratch", action="store_true")
    args = parser.parse_args()

    repo_root = Path(args.repo_root).resolve()
    git_head = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=repo_root,
        check=False,
        capture_output=True,
        text=True,
    ).stdout.strip()
    files_read = [
        str((repo_root / "docs/TEAM_B_TASK_MASTER_LOG.md").resolve()),
        str((repo_root / "docs/TEAM_B_CURRENT_STATUS.json").resolve()),
        str((repo_root / "outputs/TeamB_9cell_integration/current_supported_config/TEAM_B_9CELL_INTEGRATION_GATE.json").resolve()),
        str((repo_root / "outputs/TeamB_9cell_integration/current_supported_config/PACKAGED_IMMUTABILITY_REPORT.json").resolve()),
        str((repo_root / "outputs/TeamB_9cell_integration/current_supported_config/HORIZONTAL_PAIRWISE_ABUTMENT_MATRIX.csv").resolve()),
        str((repo_root / "outputs/TeamB_9cell_integration/current_supported_config/VERTICAL_PAIRWISE_ABUTMENT_MATRIX.csv").resolve()),
    ]
    result = run_teamb_9cell_integration(
        repo_root=repo_root,
        openyield_root=Path(args.openyield_root).resolve(),
        klayout_bin=Path(args.klayout_bin).resolve(),
        drc_deck=(repo_root / args.drc_deck).resolve(),
        resume=args.resume,
        rebuild_failed=args.rebuild_failed,
        resume_negative_tests=args.resume_negative_tests,
        scratch_root=Path(args.scratch_root).resolve(),
        cleanup_completed_scratch=args.cleanup_completed_scratch,
    )
    log_teamb_event(
        repo_root=repo_root,
        stage="integration",
        module="TEAM_B_9CELL",
        event_type="integration_run",
        git_head=git_head,
        files_read=files_read,
        input_evidence={"all_input_sha_matched": result["input_lock"]["all_input_sha_matched"]},
        files_modified=[
            str((repo_root / "outputs/TeamB_9cell_integration").resolve()),
            str((repo_root / "docs/TEAM_B_TASK_MASTER_LOG.md").resolve()),
            str((repo_root / "docs/TEAM_B_CURRENT_STATUS.json").resolve()),
        ],
        commands=[
            "TeamB_9cell_integration.py",
            *([ "--resume" ] if args.resume else []),
            *([ "--resume-negative-tests" ] if args.resume_negative_tests else []),
            *([ "--rebuild-failed" ] if args.rebuild_failed else []),
            *([ "--cleanup-completed-scratch" ] if args.cleanup_completed_scratch else []),
            f"--scratch-root={Path(args.scratch_root).resolve()}",
            f"--openyield-root={Path(args.openyield_root).resolve()}",
        ],
        result={
            "combined_atlas_drc_marker_count": result["drc"]["marker_count"],
            "library_gds_path": result["library"]["library_gds_path"],
            "clean_atlas_path": result["clean_atlas_path"],
        },
        clean_gds_sha_before={row["module_name"]: row["expected_sha256"] for row in result["input_lock"]["rows"]},
        clean_gds_sha_after={row["module_name"]: row["actual_sha256"] for row in result["input_lock"]["rows"]},
        machine_gate_before={},
        machine_gate_after=result["gate"],
        decision="produce_initial_9cell_integration_outputs",
        next_action="inspect gate failures and complete negative suite",
    )
    recompute_current_status(repo_root=repo_root, integration_gate=result["gate"])
    print(json.dumps(result["gate"], ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
