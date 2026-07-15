#!/usr/bin/env python3
import csv
import json
import os
import sys


REQUIRED_FILES = [
    "collaboration/MODULE_OWNERSHIP.csv",
    "collaboration/MODULE_OWNERSHIP.md",
    "collaboration/COLLABORATION_PLAN.json",
    "collaboration/COLLABORATION_PLAN.md",
    "collaboration/team_b/TEAM_B_MODULE_QUEUE.csv",
    "collaboration/team_b/TEAM_B_STATUS.json",
    "collaboration/team_b/TEAM_B_STATUS.md",
    "collaboration/SHARED_CODE_OWNERSHIP.md",
    "collaboration/FORBIDDEN_PATHS_TEAM_B.txt",
    "collaboration/ALLOWED_PATHS_TEAM_B.txt",
    "collaboration/MERGE_POLICY.md",
    "collaboration/EXISTING_GDS_QUALIFICATION_POLICY.md",
    "collaboration/team_b/START_HERE.md",
    "collaboration/team_b/CODEX_STARTER_PROMPT.txt",
    "collaboration/team_b/HANDOFF_TEMPLATE.md",
    "collaboration/team_b/RESULT_SUBMISSION_CHECKLIST.md",
    "collaboration/team_b/ENVIRONMENT_CHECK.sh",
    "collaboration/GITHUB_WORKFLOW.md",
    "collaboration/ARTIFACT_STORAGE_POLICY.md",
]


def fail(msg: str) -> None:
    print(f"FAIL: {msg}")
    sys.exit(1)


def main() -> None:
    repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    for rel in REQUIRED_FILES:
      path = os.path.join(repo_root, rel)
      if not os.path.exists(path):
          fail(f"missing required file: {rel}")

    with open(os.path.join(repo_root, "collaboration/COLLABORATION_PLAN.json"), encoding="utf-8") as f:
        plan = json.load(f)
    if plan["openyield_commit"] != "1c34428d8b913963c4971d093b1a7c2df97a2509":
        fail("OpenYield commit mismatch in collaboration plan")
    if plan["owner_b"]["current_stage"] != "TEAM-B0 / ASSIGNED_MODULE_SOURCE_ASSET_AND_DEPENDENCY_LOCK":
        fail("unexpected Team-B current stage")

    with open(os.path.join(repo_root, "collaboration/MODULE_OWNERSHIP.csv"), encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    modules = {row["module"]: row for row in rows}
    for required in [
        "PNAND2", "PNAND3", "AND2", "AND3",
        "pdrive", "pdrive2_for_pre", "wl_pdrive", "delay_chain", "wen_delay_chain",
        "ADDR_DFF", "DATA_DFF", "TIME",
    ]:
        if required not in modules:
            fail(f"ownership missing module {required}")
    if modules["TIME"]["owner"] != "Owner A":
        fail("TIME must stay with Owner A")
    if modules["PNAND2"]["owner"] != "Owner B":
        fail("PNAND2 must be owned by Owner B")

    with open(os.path.join(repo_root, "collaboration/team_b/TEAM_B_STATUS.json"), encoding="utf-8") as f:
        status = json.load(f)
    if status["gds_generation_allowed"] is not False:
        fail("Team-B gds_generation_allowed must be false")
    if status["next_instruction_source"] != "GPT_EVIDENCE_REVIEW_REQUIRED":
        fail("unexpected next instruction source")

    print("PASS: collaboration baseline files present and structurally consistent")


if __name__ == "__main__":
    main()
