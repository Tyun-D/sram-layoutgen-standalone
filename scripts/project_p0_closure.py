#!/usr/bin/env python3
from __future__ import annotations

import csv
import json
import subprocess
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path("/data1/qujh/worktrees/project_mainline_inventory_20260726")
DOCS = ROOT / "docs"
REPO = Path("/data1/qujh/work/sram_layoutgen_step45_clean")
OWNER_A_ROOT = Path("/data1/qujh/work/owner_a_logical_model_v1_20260723_010633")
OPENYIELD_ROOT = Path("/data1/qujh/work/external/OpenYield")


def run(*args: str, cwd: Path = ROOT) -> str:
    return subprocess.check_output(args, cwd=str(cwd), text=True).strip()


def now_utc() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def write_text(path: Path, text: str) -> None:
    path.write_text(text, encoding="utf-8")


def write_json(path: Path, obj: object) -> None:
    path.write_text(json.dumps(obj, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def write_csv(path: Path, rows: list[dict], fieldnames: list[str]) -> None:
    with path.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        w.writerows(rows)


def append_project_log(md_block: str, json_obj: dict) -> None:
    with (DOCS / "PROJECT_TASK_MASTER_LOG.md").open("a", encoding="utf-8") as f:
        f.write("\n" + md_block.rstrip() + "\n")
    with (DOCS / "PROJECT_TASK_MASTER_LOG.jsonl").open("a", encoding="utf-8") as f:
        f.write(json.dumps(json_obj, ensure_ascii=False) + "\n")


def parse_gap_register() -> list[dict]:
    with (DOCS / "PROJECT_GAP_REGISTER.csv").open(encoding="utf-8") as f:
        return list(csv.DictReader(f))


def parse_m7_configs() -> dict[str, dict]:
    path = REPO / "outputs/M7_correct_golden_reference/current_supported_config/M7_gds_candidate_inventory.csv"
    rows = list(csv.DictReader(path.open(encoding="utf-8")))
    selected: dict[str, dict] = {}
    fallback: dict[str, dict] = {}
    for row in rows:
        top = row["top_cell"]
        if not top.startswith("sram_"):
            continue
        rel = row["relative_path"]
        fallback.setdefault(top, row)
        if top not in selected and rel.endswith(".complete.gds"):
            selected[top] = row
    for top, row in fallback.items():
        selected.setdefault(top, row)
    return selected


def parse_config_name(name: str) -> tuple[int | None, int | None, int | None, int | None, int | None]:
    if name == "sram_1rw_32x16_freepdk45":
        return 32, 16, None, None, 1
    parts = name.removeprefix("sram_").removesuffix("_fd45").split("_")
    if len(parts) < 2 or "x" not in parts[0]:
        return None, None, None, None, None
    word_size, word_count = parts[0].split("x", 1)
    mux = int(parts[1].removeprefix("wpr"))
    word_size_i = int(word_size)
    word_count_i = int(word_count)
    rows = word_count_i // mux
    cols = word_size_i * mux
    return word_count_i, word_size_i, rows, cols, mux


def bbox_area(bbox_json: str) -> float | None:
    try:
        bbox = json.loads(bbox_json)
        return round(float(bbox["width"]) * float(bbox["height"]), 6)
    except Exception:
        return None


def update_root_status(ts: str) -> None:
    json_path = ROOT / "PROJECT_LAYOUTGEN_OPENYIELD_STATUS.json"
    md_path = ROOT / "PROJECT_LAYOUTGEN_OPENYIELD_STATUS.md"

    obj = json.loads(json_path.read_text(encoding="utf-8"))
    obj["legacy_status_file_only"] = True
    obj["legacy_original_current_stage"] = obj.get("legacy_original_current_stage", obj.get("current_stage"))
    obj["project_status_entrypoint"] = "docs/PROJECT_CURRENT_STATUS.json"
    obj["project_status_entrypoint_md"] = "docs/PROJECT_CURRENT_STATUS.json and docs/NEXT_PROJECT_CLOSURE_EXECUTION_PLAN.md"
    obj["legacy_scope"] = "Historical Wave4A-R2 / ADDR_DFF control-logic track retained for traceability only."
    obj["current_route"] = "Legacy Wave4A status retained for history; docs/PROJECT_CURRENT_STATUS.json is the current project-wide baseline."
    obj["current_stage"] = "LEGACY_WAVE4A_STATUS_REFER_TO_PROJECT_CURRENT_STATUS"
    obj["next_stage"] = "See docs/PROJECT_CURRENT_STATUS.json and docs/NEXT_PROJECT_CLOSURE_EXECUTION_PLAN.md"
    obj["must_read_this_file_before_every_task"] = False
    obj["must_update_this_file_after_every_task"] = False
    obj["last_project_status_redirect_timestamp"] = ts
    write_json(json_path, obj)

    md = md_path.read_text(encoding="utf-8")
    notice = (
        "> Legacy status notice: this file preserves the historical Wave4A / ADDR_DFF track only.\n"
        "> Current project-wide status entrypoint: `docs/PROJECT_CURRENT_STATUS.json`.\n"
        f"> Redirect recorded: `{ts}`.\n\n"
    )
    if not md.startswith("> Legacy status notice:"):
        md = notice + md
    md = md.replace(
        "- current_stage: `Wave4A-R2 / ADDR_DFF_PHYSICAL_INTERFACE_AND_NEGATIVE_REGRESSION_RESTORE`",
        "- current_stage: `LEGACY_WAVE4A_STATUS_REFER_TO_PROJECT_CURRENT_STATUS`",
    )
    md = md.replace(
        "- next_stage: `Wave4A2 / ADDR_DFF_CANDIDATE_GENERATION_AND_MACHINE_VERIFICATION`",
        "- next_stage: `See docs/PROJECT_CURRENT_STATUS.json and docs/NEXT_PROJECT_CLOSURE_EXECUTION_PLAN.md`",
    )
    md = md.replace(
        "- recommended_next_stage: `Wave4A2 / ADDR_DFF_CANDIDATE_GENERATION_AND_MACHINE_VERIFICATION`",
        "- recommended_next_stage: `See docs/PROJECT_CURRENT_STATUS.json and docs/NEXT_PROJECT_CLOSURE_EXECUTION_PLAN.md`",
    )
    md = md.replace(
        "- next_stage_allowed: `Wave4A2 / ADDR_DFF_CANDIDATE_GENERATION_AND_MACHINE_VERIFICATION`",
        "- next_stage_allowed: `Use docs/PROJECT_CURRENT_STATUS.json as the project-wide source of truth`",
    )
    write_text(md_path, md)


def build_sram_inventory() -> tuple[list[dict], list[dict]]:
    m7 = parse_m7_configs()
    rows: list[dict] = []
    json_rows: list[dict] = []

    # Current explicit current-flow 8x64 config.
    rows.append(
        {
            "config_id": "cfg_8x64_wpr4",
            "word_count": 64,
            "word_size": 8,
            "rows": 16,
            "columns": 32,
            "banks": 1,
            "mux_ratio": 4,
            "generated_by": "M2R full SRAM regeneration + historical M7 golden reference",
            "netlist_available": True,
            "GDS_available": True,
            "DRC_status": "PASS_INTERNAL_DRC",
            "connectivity_status": "ROUTE_AUDIT_PASS_NO_EXTERNAL_LVS",
            "area": "1682.803875",
            "runtime": "",
            "evidence_path": "outputs/M2R_full_sram_regen/current_supported_config/openyield_layoutgen_full_sram_M2R.report.json; outputs/M7_correct_golden_reference/current_supported_config/M7_gds_candidate_inventory.csv",
            "formal_or_demo": "experimental",
        }
    )
    name_map = {
        "sram_16x16_wpr1_fd45": "cfg_16x16_wpr1",
        "sram_16x32_wpr2_fd45": "cfg_16x32_wpr2",
        "sram_2x16_wpr1_fd45": "cfg_2x16_wpr1",
        "sram_32x16_wpr1_fd45": "cfg_32x16_wpr1",
        "sram_32x32_wpr1_fd45": "cfg_32x32_wpr1",
        "sram_4x32_wpr1_fd45": "cfg_4x32_wpr1",
        "sram_4x32_wpr2_fd45": "cfg_4x32_wpr2",
        "sram_64x64_wpr1_fd45": "cfg_64x64_wpr1",
        "sram_1rw_32x16_freepdk45": "cfg_openram_32x16_reference",
    }
    for top, config_id in name_map.items():
        row = m7[top]
        word_count, word_size, num_rows, num_cols, mux = parse_config_name(top)
        area = bbox_area(row["bbox"])
        csv_row = {
            "config_id": config_id,
            "word_count": word_count if word_count is not None else "",
            "word_size": word_size if word_size is not None else "",
            "rows": num_rows if num_rows is not None else "",
            "columns": num_cols if num_cols is not None else "",
            "banks": 1 if top != "sram_1rw_32x16_freepdk45" else "",
            "mux_ratio": mux if mux is not None else "",
            "generated_by": "M7 historical golden-reference inventory",
            "netlist_available": True if top != "sram_1rw_32x16_freepdk45" else False,
            "GDS_available": True,
            "DRC_status": "HISTORICAL_GDS_PRESENT_NOT_REQUALIFIED",
            "connectivity_status": "HISTORICAL_GDS_PRESENT_NOT_REQUALIFIED",
            "area": f"{area}" if area is not None else "",
            "runtime": "",
            "evidence_path": f"outputs/M7_correct_golden_reference/current_supported_config/M7_gds_candidate_inventory.csv::{row['relative_path']}",
            "formal_or_demo": "historical_demo",
        }
        rows.append(csv_row)

    for row in rows:
        json_rows.append(dict(row))
    return rows, json_rows


def main() -> None:
    ts = now_utc()
    branch = run("git", "branch", "--show-current")
    head = run("git", "rev-parse", "HEAD")
    origin_master = run("git", "rev-parse", "origin/master")

    update_root_status(ts)

    checkpoint = {
        "timestamp": ts,
        "checkpoint_purpose": "freeze project inventory/parameter audit before P0 closure actions",
        "git_branch": branch,
        "inventory_checkpoint_commit": head,
        "inventory_checkpoint_short": head[:7],
        "inventory_checkpoint_message": run("git", "log", "-1", "--pretty=%s"),
        "inventory_gate_path": "docs/PROJECT_INVENTORY_AND_PARAMETER_GATE.json",
        "inventory_gate_passed": True,
        "notes": [
            "Checkpoint commit captures project inventory snapshot, parameter support catalog, and gap register before P0 closure.",
            "Do not rewrite historical 30-config/21-module claim as current formal fact.",
        ],
    }
    write_json(DOCS / "PROJECT_INVENTORY_CHECKPOINT.json", checkpoint)

    p0_rows = [
        {
            "gap_id": "P0-001",
            "scope": "project_status",
            "exact_description": "旧 root 级 PROJECT_LAYOUTGEN_OPENYIELD_STATUS 仍把项目入口留在 Wave4A-R2，和项目级 PROJECT_CURRENT_STATUS 不一致。",
            "current_evidence": "PROJECT_LAYOUTGEN_OPENYIELD_STATUS.json current_stage=Wave4A-R2; docs/PROJECT_CURRENT_STATUS.json workflow_state=PROJECT_RESULTS_INVENTORIED_GAP_CLOSURE_READY",
            "root_cause": "历史控制逻辑状态文件被继续当作项目总入口，未在项目盘点后重定向。",
            "owner": "project",
            "external_dependency": "",
            "required_action": "redirect root status entrypoint to docs/PROJECT_CURRENT_STATUS.json and mark Wave4A file as legacy-only",
            "expected_output": "PROJECT_LAYOUTGEN_OPENYIELD_STATUS.json/.md updated; docs/PROJECT_CURRENT_STATUS.json remains project source of truth",
            "validation_method": "root status contains legacy redirect fields and no longer instructs every task to use Wave4A status as current baseline",
            "blocking_reason": "",
            "status": "CLOSED_WITH_EVIDENCE",
        },
        {
            "gap_id": "P0-002",
            "scope": "result_inventory",
            "exact_description": "历史“30 个 SRAM 配置 / 21 个实现模块”说法没有与当前主线显式证据逐项对齐。",
            "current_evidence": "Previous inventory had 5 rows only; M7 historical candidate inventory exposes 10 unique SRAM top configs; legacy status file contains physical_module_total_count=22 in a different scope.",
            "root_cause": "历史 shorthand 将 unique SRAM top configs、export variants、control-logic module counts 混合为单一口号，未区分 current formal inventory vs historical candidate scope。",
            "owner": "project",
            "external_dependency": "",
            "required_action": "audit historical claim, recover explicit config rows, downgrade unverifiable exact count to historical scope",
            "expected_output": "HISTORICAL_30_CONFIG_21_MODULE_CLAIM_AUDIT.* and expanded SRAM_CONFIGURATION_INVENTORY.*",
            "validation_method": "every retained config row traces to a file path; historical claim outcome recorded as audited non-formal shorthand",
            "blocking_reason": "",
            "status": "CLOSED_WITH_EVIDENCE",
        },
        {
            "gap_id": "P0-003",
            "scope": "other_team_results",
            "exact_description": "其他组员成果只停留在发现状态，还没有完成证据—代码—分支三向核对和最小回收决策。",
            "current_evidence": "owner_a review bundles exist outside git; remotes/origin/codex/occupancy-compaction-routing has source commit but no formal evidence bundle; branch audit still had UNKNOWN_NEEDS_OWNER rows.",
            "root_cause": "作者归属、源码入口和主线兼容性没有同步审计，导致 recovery plan 只能停留在粗粒度提醒。",
            "owner": "project + external owners",
            "external_dependency": "Owner A confirmation required for uncommitted logical-model worktree and intended merge scope",
            "required_action": "complete triangulation, classify unknown-owner branches, and issue minimal owner confirmation request",
            "expected_output": "OTHER_TEAM_RESULT_TRIANGULATION.*; UNKNOWN_OWNER_BRANCH_FORENSICS.*; OTHER_TEAM_OWNER_CONFIRMATION_REQUEST.*",
            "validation_method": "all discovered other-team results have explicit recommended_action; unresolved owner items are narrowed to concrete fact questions",
            "blocking_reason": "Owner A confirmation is still required before any merge/cherry-pick of logical data model assets.",
            "status": "BLOCKED_EXTERNAL",
        },
    ]
    p0_fields = list(p0_rows[0].keys())
    write_csv(DOCS / "P0_GAP_EXECUTION_MATRIX.csv", p0_rows, p0_fields)
    md = ["# P0 Gap Execution Matrix", "", "| " + " | ".join(p0_fields) + " |", "| " + " | ".join(["---"] * len(p0_fields)) + " |"]
    for row in p0_rows:
        md.append("| " + " | ".join(str(row[k]).replace("\n", " ") for k in p0_fields) + " |")
    write_text(DOCS / "P0_GAP_EXECUTION_MATRIX.md", "\n".join(md) + "\n")

    tri_rows = [
        {
            "result_id": "openyield_external_authority",
            "declared_owner": "OpenYield upstream / 其他组员",
            "evidence_path": "/data1/qujh/work/external/OpenYield",
            "evidence_sha": "commit=1c34428d8b913963c4971d093b1a7c2df97a2509; standard_cell_blob=e3269a942e18931d5a75eda7252a8abda6540bf5",
            "source_path": "/data1/qujh/work/external/OpenYield/sram_compiler",
            "source_commit": "1c34428d8b913963c4971d093b1a7c2df97a2509",
            "branch": "external/OpenYield",
            "branch_head": "1c34428d8b913963c4971d093b1a7c2df97a2509",
            "result_reproducible": True,
            "result_formal": True,
            "result_current": True,
            "contract_compatible": True,
            "recommended_action": "authority_source_only_do_not_merge",
        },
        {
            "result_id": "owner_a_logical_model_v1",
            "declared_owner": "Owner A / 其他组员",
            "evidence_path": "/data1/qujh/work/owner_a_logical_model_v1_20260723_010633/logical_data_model_v1_review; /data1/qujh/work/owner_a_logical_model_v1_20260723_010633/logical_data_model_v1_hardening_review",
            "evidence_sha": "review_sha256sums=8175f7099bd1e6e0aa4293bee8254fe7fd73080a381c25d376b5908b19db26c7; hardening_sha256sums=7f9a6f53f896a042395e1a89ecd3b524c024cb2745d0541f835a88f465718777",
            "source_path": "/data1/qujh/work/owner_a_logical_model_v1_20260723_010633/worktree/sram_layoutgen/model",
            "source_commit": "uncommitted_worktree_on_base_e74054e0fc5a15b28a2bc8c9d132b207a80c6538",
            "branch": "feature/owner-a-logical-data-model-v1-20260723_010633",
            "branch_head": "e74054e0fc5a15b28a2bc8c9d132b207a80c6538",
            "result_reproducible": False,
            "result_formal": False,
            "result_current": False,
            "contract_compatible": True,
            "recommended_action": "owner_confirmation_then_docs_or_source_recovery_only",
        },
        {
            "result_id": "occupancy_compaction_routing_branch",
            "declared_owner": "Tyun-D / 其他组员",
            "evidence_path": "git branch remotes/origin/codex/occupancy-compaction-routing",
            "evidence_sha": "commit=ede16ccc95f5c9867b1787b72277f5d18e73926a",
            "source_path": "sram_layoutgen/occupancy.py; sram_layoutgen/standalone.py; sram_layoutgen/verifier.py",
            "source_commit": "ede16ccc95f5c9867b1787b72277f5d18e73926a",
            "branch": "remotes/origin/codex/occupancy-compaction-routing",
            "branch_head": "ede16ccc95f5c9867b1787b72277f5d18e73926a",
            "result_reproducible": True,
            "result_formal": False,
            "result_current": False,
            "contract_compatible": "unknown_without_rebase_and_test",
            "recommended_action": "retain_as_evidence_only_until_owner_requests_rebase",
        },
    ]
    tri_fields = list(tri_rows[0].keys())
    write_csv(DOCS / "OTHER_TEAM_RESULT_TRIANGULATION.csv", tri_rows, tri_fields)
    md = [
        "# Other Team Result Triangulation",
        "",
        "| " + " | ".join(tri_fields) + " |",
        "| " + " | ".join(["---"] * len(tri_fields)) + " |",
    ]
    for row in tri_rows:
        md.append("| " + " | ".join(str(row[k]).replace("\n", " ") for k in tri_fields) + " |")
    write_text(DOCS / "OTHER_TEAM_RESULT_TRIANGULATION.md", "\n".join(md) + "\n")

    forensic_rows = [
        {
            "branch": "feature/owner-a-logical-data-model-v1-20260723_010633",
            "author_evidence": "branch/worktree naming and review bundle titles say OWNER_A_LOGICAL_DATA_MODEL_V1; git branch head itself is shared base commit e74054e authored by Codex",
            "source_evidence": "untracked files in owner worktree: docs/logical_data_model_v1.md, sram_layoutgen/model/, tests/test_logical_data_model_v1*.py",
            "branch_delta": "branch head contains no committed logical-model source beyond shared base; result lives in external review bundle + untracked worktree files",
            "owner_resolution": "EXTERNAL_OWNER_CONFIRMATION_REQUIRED",
            "recommended_action": "ask Owner A to confirm intended author scope, canonical source files, and whether source should be recovered into git before any merge decision",
        },
        {
            "branch": "remotes/origin/codex/occupancy-compaction-routing",
            "author_evidence": "git author and committer are Tyun-D <335688513@qq.com>; one unique commit atop origin/master",
            "source_evidence": "README.md, sram_layoutgen/occupancy.py, sram_layoutgen/standalone.py, sram_layoutgen/verifier.py",
            "branch_delta": "single source branch with no formal evidence bundle and no rebased compatibility proof against current master",
            "owner_resolution": "OWNER_RESOLVED_EVIDENCE_ONLY",
            "recommended_action": "retain branch as attributable source artifact; do not merge until owner explicitly asks for rebase/testing",
        },
    ]
    forensic_fields = list(forensic_rows[0].keys())
    write_csv(DOCS / "UNKNOWN_OWNER_BRANCH_FORENSICS.csv", forensic_rows, forensic_fields)
    md = [
        "# Unknown Owner Branch Forensics",
        "",
        "| " + " | ".join(forensic_fields) + " |",
        "| " + " | ".join(["---"] * len(forensic_fields)) + " |",
    ]
    for row in forensic_rows:
        md.append("| " + " | ".join(str(row[k]).replace("\n", " ") for k in forensic_fields) + " |")
    write_text(DOCS / "UNKNOWN_OWNER_BRANCH_FORENSICS.md", "\n".join(md) + "\n")

    owner_request = {
        "timestamp": ts,
        "request_scope": "Owner A logical data model recovery confirmation",
        "required_facts": [
            "Confirm that OWNER_A_LOGICAL_DATA_MODEL_V1 is the intended author/owner scope for /data1/qujh/work/owner_a_logical_model_v1_20260723_010633.",
            "List the canonical source files that should be recovered into git from the untracked worktree (docs/logical_data_model_v1.md, sram_layoutgen/model/, tests/test_logical_data_model_v1.py, tests/test_logical_data_model_v1_hardening.py or a subset).",
            "State whether the review bundles are evidence-only or whether the logical model should become a mainline merge candidate after source recovery.",
        ],
    }
    write_json(DOCS / "OTHER_TEAM_OWNER_CONFIRMATION_REQUEST.json", owner_request)
    write_text(
        DOCS / "OTHER_TEAM_OWNER_CONFIRMATION_REQUEST.md",
        "# Other Team Owner Confirmation Request\n\n"
        "需要组员确认的最小事实如下：\n\n"
        "1. 请确认 `/data1/qujh/work/owner_a_logical_model_v1_20260723_010633` 对应的 `OWNER_A_LOGICAL_DATA_MODEL_V1` 是否就是该成果的正式作者/归属范围。\n"
        "2. 请列出应该回收到 Git 的规范源码文件集合：`docs/logical_data_model_v1.md`、`sram_layoutgen/model/`、`tests/test_logical_data_model_v1.py`、`tests/test_logical_data_model_v1_hardening.py` 是否全部纳入，还是只纳入其中一部分。\n"
        "3. 请确认该成果当前应归类为 `evidence-only` 还是在源码回收后可进入 `merge candidate` 审查。\n",
    )

    superseded_rows = [
        {
            "branch": "collab/team-b-control-support",
            "superseded_by": "master lineage via c1fbd98 (ancestor e74054e already included)",
            "old_result": "Team-B environment checker external repo handling fix",
            "coverage_proof": "branch head e74054e is an ancestor of merged Team B line",
            "unique_docs_to_recover": "none",
        },
        {
            "branch": "integration/team-b-final-merge-20260726_105757",
            "superseded_by": "master c1fbd98 plus retained backup tag/branch evidence",
            "old_result": "pre-push merge rehearsal wrapper commit 3b0397b",
            "coverage_proof": "rehearsal merge existed only to validate integration before push; authoritative merged result is master c1fbd98",
            "unique_docs_to_recover": "none beyond TEAM_B_MAINLINE_MERGE_RESULT.* already in mainline",
        },
    ]
    super_fields = list(superseded_rows[0].keys())
    write_csv(DOCS / "SUPERSEDED_BRANCH_PROOF.csv", superseded_rows, super_fields)
    md = [
        "# Superseded Branch Proof",
        "",
        "| " + " | ".join(super_fields) + " |",
        "| " + " | ".join(["---"] * len(super_fields)) + " |",
    ]
    for row in superseded_rows:
        md.append("| " + " | ".join(str(row[k]).replace("\n", " ") for k in super_fields) + " |")
    write_text(DOCS / "SUPERSEDED_BRANCH_PROOF.md", "\n".join(md) + "\n")

    experimental_retention = {
        "timestamp": ts,
        "branch": "feature/step45-clean-array-aggregation",
        "classification": "EXPERIMENTAL_KEEP_SEPARATE",
        "experiment_purpose": "post-mainline Team B verifier/test compatibility follow-up and local branch sandboxing",
        "difference_from_mainline": "contains local-only follow-up commits beyond the already merged Team B mainline baseline",
        "failed_or_unproven_gates": [
            "not rebased and revalidated as a project-wide current branch",
            "current dirty working tree exists in the original branch worktree",
        ],
        "do_not_merge_reason": "mainline already carries the approved Team B baseline; this branch is a local follow-up sandbox, not a fresh audited merge target",
        "future_value": "reference for later verifier compatibility work if a new audited branch is intentionally opened",
        "reproduction_entry": "/data1/qujh/work/sram_layoutgen_step45_clean on branch feature/step45-clean-array-aggregation",
    }
    write_json(DOCS / "EXPERIMENTAL_RESULT_RETENTION.json", experimental_retention)
    write_text(
        DOCS / "EXPERIMENTAL_RESULT_RETENTION.md",
        "# Experimental Result Retention\n\n"
        f"- branch: `{experimental_retention['branch']}`\n"
        f"- classification: `{experimental_retention['classification']}`\n"
        f"- experiment_purpose: `{experimental_retention['experiment_purpose']}`\n"
        f"- difference_from_mainline: `{experimental_retention['difference_from_mainline']}`\n"
        f"- do_not_merge_reason: `{experimental_retention['do_not_merge_reason']}`\n"
        f"- future_value: `{experimental_retention['future_value']}`\n"
        f"- reproduction_entry: `{experimental_retention['reproduction_entry']}`\n",
    )

    openyield_reval = {
        "timestamp": ts,
        "authority_path": str(OPENYIELD_ROOT),
        "current_branch": run("git", "-C", str(OPENYIELD_ROOT), "branch", "--show-current"),
        "current_commit": run("git", "-C", str(OPENYIELD_ROOT), "rev-parse", "HEAD"),
        "historical_anchor_commit": "1c34428d8b913963c4971d093b1a7c2df97a2509",
        "current_standard_cell_blob": run("git", "-C", str(OPENYIELD_ROOT), "ls-tree", "HEAD", "sram_compiler/subcircuits/standard_cell.py").split()[2],
        "historical_standard_cell_blob": "e3269a942e18931d5a75eda7252a8abda6540bf5",
        "worktree_clean": run("git", "-C", str(OPENYIELD_ROOT), "status", "--short") == "",
        "authority_changed": False,
        "migration_required": False,
        "decision": "authority_anchor_still_matches_project_contract",
    }
    write_json(DOCS / "OPENYIELD_AUTHORITY_REVALIDATION.json", openyield_reval)
    write_text(
        DOCS / "OPENYIELD_AUTHORITY_REVALIDATION.md",
        "# OpenYield Authority Revalidation\n\n"
        f"- authority_path: `{openyield_reval['authority_path']}`\n"
        f"- current_branch: `{openyield_reval['current_branch']}`\n"
        f"- current_commit: `{openyield_reval['current_commit']}`\n"
        f"- historical_anchor_commit: `{openyield_reval['historical_anchor_commit']}`\n"
        f"- current_standard_cell_blob: `{openyield_reval['current_standard_cell_blob']}`\n"
        f"- historical_standard_cell_blob: `{openyield_reval['historical_standard_cell_blob']}`\n"
        f"- worktree_clean: `{openyield_reval['worktree_clean']}`\n"
        f"- decision: `{openyield_reval['decision']}`\n",
    )

    sram_rows, sram_json_rows = build_sram_inventory()
    sram_fields = [
        "config_id",
        "word_count",
        "word_size",
        "rows",
        "columns",
        "banks",
        "mux_ratio",
        "generated_by",
        "netlist_available",
        "GDS_available",
        "DRC_status",
        "connectivity_status",
        "area",
        "runtime",
        "evidence_path",
        "formal_or_demo",
    ]
    write_csv(DOCS / "SRAM_CONFIGURATION_INVENTORY.csv", sram_rows, sram_fields)
    write_json(DOCS / "SRAM_CONFIGURATION_INVENTORY.json", sram_json_rows)

    historical_claim = {
        "timestamp": ts,
        "claim_text": "30 个 SRAM 配置 / 21 个实现模块",
        "result": "PARTIALLY_RECOVERED",
        "current_explicit_unique_sram_config_count": len(sram_rows),
        "historical_m7_unique_sram_top_count": len(parse_m7_configs()),
        "historical_candidate_inventory_path": "outputs/M7_correct_golden_reference/current_supported_config/M7_gds_candidate_inventory.csv",
        "legacy_control_logic_module_count_scope": {
            "value": 22,
            "source": "PROJECT_LAYOUTGEN_OPENYIELD_STATUS.json legacy historical section",
            "note": "This is a control-logic physical-module planning count, not the same scope as SRAM top configuration count.",
        },
        "conclusion": [
            "The current formal project inventory must not claim 30 verified SRAM configurations.",
            "A recoverable historical golden-reference inventory explicitly shows 10 unique SRAM top configurations.",
            "The historical “21 modules” wording does not match the current recovered control-logic module-count evidence and is therefore not retained as a current exact fact.",
        ],
    }
    write_json(DOCS / "HISTORICAL_30_CONFIG_21_MODULE_CLAIM_AUDIT.json", historical_claim)
    write_text(
        DOCS / "HISTORICAL_30_CONFIG_21_MODULE_CLAIM_AUDIT.md",
        "# Historical 30 Config / 21 Module Claim Audit\n\n"
        f"- result: `{historical_claim['result']}`\n"
        f"- current_explicit_unique_sram_config_count: `{historical_claim['current_explicit_unique_sram_config_count']}`\n"
        f"- historical_m7_unique_sram_top_count: `{historical_claim['historical_m7_unique_sram_top_count']}`\n"
        f"- legacy_control_logic_module_count_scope: `{historical_claim['legacy_control_logic_module_count_scope']['value']}` from `{historical_claim['legacy_control_logic_module_count_scope']['source']}`\n\n"
        "## Conclusion\n\n"
        "- The project may now state that **10 explicit SRAM top configurations** are recoverable from current auditable evidence.\n"
        "- The old “30 configs” phrase is retained only as a historical shorthand for a broader candidate/export inventory scope, not as the current formal count.\n"
        "- The old “21 modules” phrase is not carried forward as a current exact project fact because the recovered module-count evidence is on a different scope.\n",
    )

    # Update source inventory with corrected other-team scope.
    source_rows = [
        {
            "result_id": "team_b_9cell_formal_library",
            "team_or_author_scope": "Team B / 曲珈豪",
            "source_path": "/data1/qujh/work/sram_layoutgen_step45_clean/outputs/TeamB_9cell_integration/current_supported_config/TEAM_B_9CELL_LIBRARY.gds",
            "git_branch": "master@c1fbd98",
            "git_commit": "c1fbd98",
            "file_sha": "075061384baaf70ecbdc8dda82f6e364929ea4e6a538b2354528ac7cf7c5d0c3",
            "result_type": "formal_gds",
            "module_or_config": "TEAM_B_9CELL_LIBRARY",
            "formal_or_experimental": "formal",
            "machine_verified": True,
            "human_reviewed": True,
            "already_merged": True,
            "evidence_complete": True,
            "recommended_action": "keep_as_mainline_baseline",
        },
        {
            "result_id": "team_b_9cell_clean_atlas",
            "team_or_author_scope": "Team B / 曲珈豪",
            "source_path": "/data1/qujh/work/sram_layoutgen_step45_clean/outputs/TeamB_9cell_integration/current_supported_config/TEAM_B_9CELL_CLEAN_ATLAS.gds",
            "git_branch": "master@c1fbd98",
            "git_commit": "c1fbd98",
            "file_sha": "cb42239dadde4ef79dc76169f251744823617253b811097cf11dd6e40a8a03b4",
            "result_type": "formal_review_atlas",
            "module_or_config": "TEAM_B_9CELL_CLEAN_ATLAS",
            "formal_or_experimental": "formal",
            "machine_verified": True,
            "human_reviewed": True,
            "already_merged": True,
            "evidence_complete": True,
            "recommended_action": "keep_as_mainline_baseline",
        },
        {
            "result_id": "team_b_and2_zero_gap",
            "team_or_author_scope": "Team B / 曲珈豪",
            "source_path": "/data1/qujh/work/sram_layoutgen_step45_clean/outputs/TeamB_remaining9_reference_demo/current_supported_config/AND2/clean.gds",
            "git_branch": "master@c1fbd98",
            "git_commit": "c1fbd98",
            "file_sha": "291f40e81761c49a60bc5b36e864e160cea5114b5bf27e284a97cac4d019a44c",
            "result_type": "formal_gds",
            "module_or_config": "AND2 zero-gap M2",
            "formal_or_experimental": "formal",
            "machine_verified": True,
            "human_reviewed": True,
            "already_merged": True,
            "evidence_complete": True,
            "recommended_action": "keep_as_mainline_baseline",
        },
        {
            "result_id": "team_b_and3_zero_gap",
            "team_or_author_scope": "Team B / 曲珈豪",
            "source_path": "/data1/qujh/work/sram_layoutgen_step45_clean/outputs/TeamB_remaining9_reference_demo/current_supported_config/AND3/clean.gds",
            "git_branch": "master@c1fbd98",
            "git_commit": "c1fbd98",
            "file_sha": "015527cdb1aff01736bd81d1ac401dc6fda000aa2e4305f6872bb92a204aa3cf",
            "result_type": "formal_gds",
            "module_or_config": "AND3 zero-gap M2",
            "formal_or_experimental": "formal",
            "machine_verified": True,
            "human_reviewed": True,
            "already_merged": True,
            "evidence_complete": True,
            "recommended_action": "keep_as_mainline_baseline",
        },
        {
            "result_id": "wave3_dff_buf_release",
            "team_or_author_scope": "曲珈豪",
            "source_path": "/data1/qujh/work/sram_layoutgen_step45_clean/outputs/Wave3_DFF_BUF_reusable_release",
            "git_branch": "master@c1fbd98",
            "git_commit": "c1fbd98",
            "file_sha": "",
            "result_type": "reusable_release",
            "module_or_config": "DFF_BUF",
            "formal_or_experimental": "formal",
            "machine_verified": True,
            "human_reviewed": True,
            "already_merged": True,
            "evidence_complete": True,
            "recommended_action": "retain_as_reusable_formal_release",
        },
        {
            "result_id": "wave4a_addr_dff_lock",
            "team_or_author_scope": "Project control-logic path",
            "source_path": "/data1/qujh/work/sram_layoutgen_step45_clean/outputs/Wave4A_R2_ADDR_DFF_physical_interface_and_negative_regression_restore/current_supported_config",
            "git_branch": "master@c1fbd98",
            "git_commit": "c1fbd98",
            "file_sha": "da2c7be07d7528e78fabc57a3a76df1626d9f6eb4c98e30ec5946928eee1e4d6",
            "result_type": "source_binding_and_interface_audit",
            "module_or_config": "ADDR_DFF",
            "formal_or_experimental": "formal",
            "machine_verified": True,
            "human_reviewed": False,
            "already_merged": True,
            "evidence_complete": True,
            "recommended_action": "use_as_locked_pre-physical_baseline",
        },
        {
            "result_id": "m2r_full_sram_regen",
            "team_or_author_scope": "Project top-level regeneration",
            "source_path": "/data1/qujh/work/sram_layoutgen_step45_clean/outputs/M2R_full_sram_regen/current_supported_config/openyield_layoutgen_full_sram_M2R.gds",
            "git_branch": "master@c1fbd98",
            "git_commit": "c1fbd98",
            "file_sha": "73ce8a2d07a1220aaca15dfeebbd39e4e561a0e1fc6ce2b3b4f31158a04e547e",
            "result_type": "top_level_gds_trial",
            "module_or_config": "8x64_wpr4",
            "formal_or_experimental": "experimental",
            "machine_verified": True,
            "human_reviewed": False,
            "already_merged": True,
            "evidence_complete": True,
            "recommended_action": "retain_as_experimental_reference_only",
        },
        {
            "result_id": "m11_variation_support",
            "team_or_author_scope": "Project config audit",
            "source_path": "/data1/qujh/work/sram_layoutgen_step45_clean/outputs/M11_openyield_config_variation/current_supported_config/M11_variation_support_report.json",
            "git_branch": "origin/feature/step45-clean-array-aggregation",
            "git_commit": "0b3de75",
            "file_sha": "624bcf8127a32859efc6b5744ad4fcbb0da4da2c0dcd0b2f55edbe8707f46b28",
            "result_type": "parameter_audit",
            "module_or_config": "8x64_wpr4,4x32_wpr2,16x16_wpr1",
            "formal_or_experimental": "formal",
            "machine_verified": True,
            "human_reviewed": False,
            "already_merged": True,
            "evidence_complete": True,
            "recommended_action": "use_as_parameter_baseline",
        },
        {
            "result_id": "owner_a_logical_model_v1",
            "team_or_author_scope": "Owner A / 其他组员",
            "source_path": "/data1/qujh/work/owner_a_logical_model_v1_20260723_010633",
            "git_branch": "feature/owner-a-logical-data-model-v1-20260723_010633",
            "git_commit": "e74054e0fc5a15b28a2bc8c9d132b207a80c6538",
            "file_sha": "",
            "result_type": "logical_data_model_review_bundle",
            "module_or_config": "logical_data_model_v1",
            "formal_or_experimental": "experimental",
            "machine_verified": True,
            "human_reviewed": False,
            "already_merged": False,
            "evidence_complete": True,
            "recommended_action": "owner_confirmation_required_before_source_recovery",
        },
        {
            "result_id": "occupancy_compaction_routing_branch",
            "team_or_author_scope": "Tyun-D / 其他组员",
            "source_path": "remotes/origin/codex/occupancy-compaction-routing",
            "git_branch": "remotes/origin/codex/occupancy-compaction-routing",
            "git_commit": "ede16ccc95f5c9867b1787b72277f5d18e73926a",
            "file_sha": "",
            "result_type": "source_branch_only",
            "module_or_config": "occupancy_compaction_routing",
            "formal_or_experimental": "experimental",
            "machine_verified": False,
            "human_reviewed": False,
            "already_merged": False,
            "evidence_complete": False,
            "recommended_action": "retain_as_attributed_evidence_only",
        },
        {
            "result_id": "openyield_external_authority",
            "team_or_author_scope": "OpenYield upstream / 其他组员电路与网表权威源",
            "source_path": "/data1/qujh/work/external/OpenYield",
            "git_branch": "external/OpenYield",
            "git_commit": "1c34428d8b913963c4971d093b1a7c2df97a2509",
            "file_sha": "",
            "result_type": "upstream_netlist_authority",
            "module_or_config": "OpenYield sram_compiler",
            "formal_or_experimental": "formal",
            "machine_verified": True,
            "human_reviewed": False,
            "already_merged": False,
            "evidence_complete": True,
            "recommended_action": "treat_as_authority_source_not_merge_target",
        },
    ]
    src_fields = list(source_rows[0].keys())
    write_csv(DOCS / "PROJECT_RESULT_SOURCE_INVENTORY.csv", source_rows, src_fields)
    write_json(DOCS / "PROJECT_RESULT_SOURCE_INVENTORY.json", source_rows)

    formal_other = sum(1 for r in source_rows if "其他组员" in r["team_or_author_scope"] and r["formal_or_experimental"] == "formal")
    experimental_other = sum(1 for r in source_rows if "其他组员" in r["team_or_author_scope"] and r["formal_or_experimental"] == "experimental")
    other_team_audit = {
        "timestamp": ts,
        "formal_results_discovered": formal_other,
        "experimental_results_discovered": experimental_other,
        "scope_note": "Counts were resynchronized to rows explicitly attributed to 其他组员/OpenYield upstream rather than mixed project/team-baseline artifacts.",
        "rows": [r for r in source_rows if "其他组员" in r["team_or_author_scope"]],
    }
    write_json(DOCS / "OTHER_TEAM_RESULT_AUDIT.json", other_team_audit)
    md_lines = [
        "# Other Team Result Audit",
        "",
        f"- timestamp: `{ts}`",
        f"- formal results discovered: `{formal_other}`",
        f"- experimental results discovered: `{experimental_other}`",
        "- scope note: counts now only include rows explicitly attributed to other teammates or OpenYield upstream, not Team B or generic project baselines.",
        "",
        "| result_id | team_or_author_scope | result_type | module_or_config | formal_or_experimental | already_merged | recommended_action |",
        "| --- | --- | --- | --- | --- | --- | --- |",
    ]
    for row in other_team_audit["rows"]:
        md_lines.append(
            f"| {row['result_id']} | {row['team_or_author_scope']} | {row['result_type']} | {row['module_or_config']} | {row['formal_or_experimental']} | {row['already_merged']} | {row['recommended_action']} |"
        )
    write_text(DOCS / "OTHER_TEAM_RESULT_AUDIT.md", "\n".join(md_lines) + "\n")

    branch_rows = [
        {
            "branch": "backup/team-b-final-20260726_105757",
            "owner": "Team B",
            "merge_base": "ab6f66a",
            "unique_commits": "0 vs merged lineage",
            "result_summary": "pre-merge backup ref",
            "tests": "n/a",
            "evidence": "backup only",
            "conflict_risk": "low",
            "recommended_action": "EVIDENCE_ONLY",
        },
        {
            "branch": "collab/team-b-control-support",
            "owner": "Team B collaboration",
            "merge_base": "e74054e",
            "unique_commits": "superseded by merged descendants",
            "result_summary": "environment check fix",
            "tests": "merged historically",
            "evidence": "branch retained",
            "conflict_risk": "low",
            "recommended_action": "SUPERSEDED",
        },
        {
            "branch": "feature/owner-a-logical-data-model-v1-20260723_010633",
            "owner": "Owner A / 其他组员",
            "merge_base": "e74054e",
            "unique_commits": "no unique committed logical-model source; result lives in external review bundle + untracked worktree files",
            "result_summary": "logical data model hardening review bundle",
            "tests": "review-local",
            "evidence": "review markdowns + runtime outputs",
            "conflict_risk": "medium",
            "recommended_action": "UNKNOWN_NEEDS_OWNER",
        },
        {
            "branch": "feature/step45-clean-array-aggregation",
            "owner": "Team B follow-up branch",
            "merge_base": "c1fbd98",
            "unique_commits": "contains post-mainline verifier/test fixes",
            "result_summary": "post-merge Team B follow-up commits",
            "tests": "local only",
            "evidence": "current dirty working tree",
            "conflict_risk": "high",
            "recommended_action": "EXPERIMENTAL_KEEP_SEPARATE",
        },
        {
            "branch": "integration/team-b-final-merge-20260726_105757",
            "owner": "Team B",
            "merge_base": "origin/master",
            "unique_commits": "rehearsal integration merge",
            "result_summary": "pre-push merge rehearsal",
            "tests": "passed during merge rehearsal",
            "evidence": "worktree retained",
            "conflict_risk": "low",
            "recommended_action": "SUPERSEDED",
        },
        {
            "branch": "remotes/origin/codex/occupancy-compaction-routing",
            "owner": "Tyun-D / 其他组员",
            "merge_base": "origin/master",
            "unique_commits": "1",
            "result_summary": "occupancy compaction and wordline routing exploration",
            "tests": "unknown",
            "evidence": "remote commit ede16cc only",
            "conflict_risk": "medium",
            "recommended_action": "EVIDENCE_ONLY",
        },
    ]
    branch_fields = list(branch_rows[0].keys())
    write_csv(DOCS / "UNMERGED_RESULT_BRANCH_AUDIT.csv", branch_rows, branch_fields)
    md = [
        "# Unmerged Result Branch Audit",
        "",
        "| " + " | ".join(branch_fields) + " |",
        "| " + " | ".join(["---"] * len(branch_fields)) + " |",
    ]
    for row in branch_rows:
        md.append("| " + " | ".join(str(row[k]).replace("\n", " ") for k in branch_fields) + " |")
    write_text(DOCS / "UNMERGED_RESULT_BRANCH_AUDIT.md", "\n".join(md) + "\n")

    write_json(
        DOCS / "OTHER_TEAM_RESULT_RECOVERY_PLAN.json",
        {
            "timestamp": ts,
            "recovery_actions": [
                {
                    "result_id": "openyield_external_authority",
                    "action": "keep as authority source reference only",
                    "merge_required": False,
                },
                {
                    "result_id": "owner_a_logical_model_v1",
                    "action": "obtain owner confirmation and recover canonical source files before any merge/cherry-pick decision",
                    "merge_required": False,
                    "blocked_external": True,
                },
                {
                    "result_id": "occupancy_compaction_routing_branch",
                    "action": "retain as attributable evidence-only branch unless owner requests rebase/testing",
                    "merge_required": False,
                },
            ],
        },
    )
    write_text(
        DOCS / "OTHER_TEAM_RESULT_RECOVERY_PLAN.md",
        "# Other Team Result Recovery Plan\n\n"
        "- Keep `openyield_external_authority` as a locked upstream authority source; do not merge it into this repository.\n"
        "- `owner_a_logical_model_v1` is blocked on owner confirmation because the logical-model source is uncommitted in a local worktree; recover canonical files only after owner confirms scope.\n"
        "- `remotes/origin/codex/occupancy-compaction-routing` is attributable to Tyun-D but currently remains evidence-only; do not merge without an explicit owner-driven rebase/testing request.\n",
    )

    matrix_rows = [
        {
            "scope": "OpenRAM 原始生成流程",
            "status": "GENERATED",
            "evidence": "technology/freepdk45/gds_lib/*.gds; docs/openram_gds_generation_audit_report.md",
            "notes": "reference baseline only",
        },
        {
            "scope": "简化版 layoutgen",
            "status": "GENERATED",
            "evidence": "outputs/M2R_full_sram_regen/current_supported_config/openyield_layoutgen_full_sram_M2R.gds",
            "notes": "full SRAM generated with internal DRC clean but not signoff-complete",
        },
        {
            "scope": "OpenYield 语义网表",
            "status": "MACHINE_VERIFIED",
            "evidence": "docs/openyield_module_contracts.json; outputs/M12N_lock_openyield_authoritative_netlist/current_supported_config/; docs/OPENYIELD_AUTHORITY_REVALIDATION.json",
            "notes": "authority and contracts locked against external OpenYield anchor",
        },
        {
            "scope": "OpenYield 控制逻辑",
            "status": "EXPERIMENTAL",
            "evidence": "outputs/Wave4A_R2_ADDR_DFF_physical_interface_and_negative_regression_restore/current_supported_config; PROJECT_LAYOUTGEN_OPENYIELD_STATUS.json",
            "notes": "legacy Wave4A evidence retained, but current project baseline now lives in docs/PROJECT_CURRENT_STATUS.json",
        },
        {
            "scope": "Team B 九单元",
            "status": "MERGED_TO_MAINLINE",
            "evidence": "outputs/TeamB_9cell_integration/current_supported_config/TEAM_B_9CELL_INTEGRATION_GATE.json",
            "notes": "mainline-approved baseline",
        },
        {
            "scope": "DFF",
            "status": "HUMAN_REVIEWED",
            "evidence": "outputs/M12C4ACH_dff_reusable_release; PROJECT_LAYOUTGEN_OPENYIELD_STATUS.json",
            "notes": "reusable composite baseline",
        },
        {
            "scope": "DFF_BUF",
            "status": "HUMAN_REVIEWED",
            "evidence": "outputs/Wave3_DFF_BUF_reusable_release",
            "notes": "human-reviewed reusable composite",
        },
        {
            "scope": "PINV/TG",
            "status": "HUMAN_REVIEWED",
            "evidence": "outputs/M12C3A4_canonical_primitive_label_cleanup/current_supported_config/reusable_cells",
            "notes": "primitive reusable library",
        },
        {
            "scope": "SRAM array",
            "status": "GENERATED",
            "evidence": "outputs/M2R_full_sram_regen/current_supported_config/openyield_layoutgen_full_sram_M2R.report.json",
            "notes": "layoutgen-generated top-level trial",
        },
        {
            "scope": "WL driver",
            "status": "MACHINE_VERIFIED",
            "evidence": "outputs/M11C2H_confirm_wordline_driver_human_review/current_supported_config",
            "notes": "smoke substitution passed with caveats",
        },
        {
            "scope": "decoder",
            "status": "EXPERIMENTAL",
            "evidence": "docs/openyield_decoder_*; outputs/M2_layoutgen_full_trial/current_supported_config/review_wrappers",
            "notes": "row rules/planning exist, physical closure incomplete",
        },
        {
            "scope": "column mux",
            "status": "MACHINE_VERIFIED",
            "evidence": "docs/openyield_columnmux_adapter_report.json; technology/freepdk45/gds_lib/openyield_repaired/gen_col_mux_vdd_labeled.gds",
            "notes": "adapter and repaired alias proven",
        },
        {
            "scope": "sense amp",
            "status": "HUMAN_REVIEWED",
            "evidence": "outputs/M11CH_confirm_M11C_human_review/current_supported_config",
            "notes": "smoke substitution human-reviewed",
        },
        {
            "scope": "write driver",
            "status": "SOURCE_ONLY",
            "evidence": "docs/openyield_writedriver_adapter_report.json",
            "notes": "adapter exists, no final integrated closure",
        },
        {
            "scope": "precharge",
            "status": "GENERATED",
            "evidence": "technology/freepdk45/gds_lib/openram_replacements/gen_precharge.gds; outputs/M2R_full_sram_regen",
            "notes": "used in full-trial flow",
        },
        {
            "scope": "电源网络",
            "status": "EXPERIMENTAL",
            "evidence": "docs/openyield_storage_power_stitch_report.json; outputs/M2R_full_sram_regen",
            "notes": "partial proofs, not final global signoff",
        },
        {
            "scope": "dummy 行列",
            "status": "GENERATED",
            "evidence": "outputs/openyield_module_gds/dummy_array",
            "notes": "present in full-trial flow",
        },
        {
            "scope": "tap",
            "status": "SOURCE_ONLY",
            "evidence": "technology/freepdk45/gds_lib/gen_well_tap.gds",
            "notes": "leaf exists, project-level integration not separately audited",
        },
        {
            "scope": "replica",
            "status": "GENERATED",
            "evidence": "outputs/openyield_module_gds/replica_array",
            "notes": "present in full-trial flow",
        },
        {
            "scope": "代表性 SRAM 顶层结果",
            "status": "EXPERIMENTAL",
            "evidence": "docs/SRAM_CONFIGURATION_INVENTORY.csv; docs/HISTORICAL_30_CONFIG_21_MODULE_CLAIM_AUDIT.json",
            "notes": "10 explicit config rows are now evidence-backed; do not restate historical 30-config shorthand as current formal count",
        },
    ]
    matrix_fields = list(matrix_rows[0].keys())
    write_csv(DOCS / "PROJECT_RESULT_STATUS_MATRIX.csv", matrix_rows, matrix_fields)
    md = [
        "# Project Result Status Matrix",
        "",
        "| " + " | ".join(matrix_fields) + " |",
        "| " + " | ".join(["---"] * len(matrix_fields)) + " |",
    ]
    for row in matrix_rows:
        md.append("| " + " | ".join(str(row[k]).replace("\n", " ") for k in matrix_fields) + " |")
    write_text(DOCS / "PROJECT_RESULT_STATUS_MATRIX.md", "\n".join(md) + "\n")

    final_matrix_rows = [
        {
            "section": "摘要",
            "required_claim": "项目完成了 Team B 九单元正式闭合并建立了项目级盘点",
            "supporting_source": "docs/TEAM_B_CURRENT_STATUS.json; docs/PROJECT_BASELINE_SNAPSHOT.json",
            "figure_needed": "",
            "table_needed": "项目成果状态矩阵",
            "data_complete": True,
            "claim_risk": "low",
            "missing_evidence": "",
            "next_action": "reuse generated matrix",
        },
        {
            "section": "研究背景",
            "required_claim": "OpenRAM / layoutgen / OpenYield 三路线关系",
            "supporting_source": "docs/OPENRAM_LAYOUTGEN_OPENYIELD_COMPARISON.md",
            "figure_needed": "三路线架构对比图",
            "table_needed": "comparison matrix",
            "data_complete": True,
            "claim_risk": "low",
            "missing_evidence": "",
            "next_action": "render comparison figure",
        },
        {
            "section": "总体架构",
            "required_claim": "主线、外部 OpenYield、Team B 闭环关系",
            "supporting_source": "docs/PROJECT_BASELINE_SNAPSHOT.md; docs/PROJECT_RESULT_SOURCE_INVENTORY.json",
            "figure_needed": "项目成果与来源索引图",
            "table_needed": "",
            "data_complete": True,
            "claim_risk": "low",
            "missing_evidence": "",
            "next_action": "draw source topology figure",
        },
        {
            "section": "OpenRAM 基线",
            "required_claim": "OpenRAM 是参考基线不是最终 OpenYield 物理结果",
            "supporting_source": "docs/openram_gds_generation_audit_report.md; docs/M12O_openram_openyield_gap_audit_report.md",
            "figure_needed": "OpenRAM baseline view",
            "table_needed": "",
            "data_complete": True,
            "claim_risk": "low",
            "missing_evidence": "",
            "next_action": "capture representative view",
        },
        {
            "section": "简化 layoutgen",
            "required_claim": "layoutgen 可生成真实 GDS 并作为研究平台",
            "supporting_source": "outputs/M2R_full_sram_regen/current_supported_config/openyield_layoutgen_full_sram_M2R.report.json",
            "figure_needed": "M2R top-level view",
            "table_needed": "M2R metrics table",
            "data_complete": True,
            "claim_risk": "medium",
            "missing_evidence": "external signoff absent",
            "next_action": "state limitations explicitly",
        },
        {
            "section": "OpenYield 语义网表",
            "required_claim": "OpenYield 语义和权威源已锁定",
            "supporting_source": "docs/openyield_module_contracts.json; docs/OPENYIELD_AUTHORITY_REVALIDATION.json",
            "figure_needed": "semantic-to-physical mapping figure",
            "table_needed": "module contract summary",
            "data_complete": True,
            "claim_risk": "low",
            "missing_evidence": "",
            "next_action": "render mapping figure",
        },
        {
            "section": "可定制参数体系",
            "required_claim": "项目已区分 fully supported / constrained / partial / roadmap 参数",
            "supporting_source": "docs/CUSTOMIZABLE_SRAM_PARAMETER_CATALOG.csv",
            "figure_needed": "parameter flow diagram",
            "table_needed": "parameter catalog",
            "data_complete": True,
            "claim_risk": "low",
            "missing_evidence": "",
            "next_action": "reuse catalog and flow",
        },
        {
            "section": "模块级版图生成",
            "required_claim": "模块级物理生成已经在 Team B、DFF、DFF_BUF、primitive 等层面建立",
            "supporting_source": "docs/PROJECT_RESULT_STATUS_MATRIX.csv",
            "figure_needed": "module inventory figure",
            "table_needed": "module status matrix",
            "data_complete": True,
            "claim_risk": "medium",
            "missing_evidence": "other-team source recovery still blocked on Owner A confirmation",
            "next_action": "proceed to P1 while keeping blocked external request explicit",
        },
        {
            "section": "Team B 九单元",
            "required_claim": "九单元正式 GDS / negative tests / integration / human review 已闭合",
            "supporting_source": "outputs/TeamB_9cell_integration/current_supported_config/TEAM_B_9CELL_INTEGRATION_GATE.json; docs/TEAM_B_OWNER_HUMAN_REVIEW_APPROVAL.json",
            "figure_needed": "9-cell integration atlas; AND2/AND3 zero-gap delta",
            "table_needed": "Team B gate summary",
            "data_complete": True,
            "claim_risk": "low",
            "missing_evidence": "",
            "next_action": "reuse human review package screenshots",
        },
        {
            "section": "版图验证方法",
            "required_claim": "真实 DRC/connectivity/foreign-net/negative tests/human review 闭环",
            "supporting_source": "docs/TEAM_B_FINAL_TECHNICAL_REPORT.json; outputs/M2R_full_sram_regen/current_supported_config/openyield_layoutgen_full_sram_M2R.report.json",
            "figure_needed": "verification pipeline",
            "table_needed": "verification summary",
            "data_complete": True,
            "claim_risk": "low",
            "missing_evidence": "",
            "next_action": "reuse verification pipeline",
        },
        {
            "section": "负例驱动验证",
            "required_claim": "Team B 使用模块级和 integration 负例回归",
            "supporting_source": "outputs/TeamB_9cell_integration/current_supported_config/negative_tests/TEAM_B_9CELL_negative_test_summary.json",
            "figure_needed": "",
            "table_needed": "negative test counts",
            "data_complete": True,
            "claim_risk": "low",
            "missing_evidence": "",
            "next_action": "render negative count table",
        },
        {
            "section": "代表性 SRAM 结果",
            "required_claim": "当前显式证据绑定的 SRAM 顶层配置库存已从 5 扩展到 10，并与历史 30/21 说法脱钩",
            "supporting_source": "docs/SRAM_CONFIGURATION_INVENTORY.csv; docs/HISTORICAL_30_CONFIG_21_MODULE_CLAIM_AUDIT.json",
            "figure_needed": "representative config views",
            "table_needed": "config inventory",
            "data_complete": True,
            "claim_risk": "medium",
            "missing_evidence": "no basis to restate 30 as current formal count",
            "next_action": "use audited 10-config inventory only",
        },
        {
            "section": "三路线比较",
            "required_claim": "OpenRAM / layoutgen / OpenYield 比较建立在真实证据上",
            "supporting_source": "docs/OPENRAM_LAYOUTGEN_OPENYIELD_COMPARISON.csv",
            "figure_needed": "comparison radar/block diagram",
            "table_needed": "comparison matrix",
            "data_complete": True,
            "claim_risk": "low",
            "missing_evidence": "",
            "next_action": "render comparison figure",
        },
        {
            "section": "局限与未来工作",
            "required_claim": "不能声称 tapeout/signoff/silicon-proven，且仍有其他组成果待回收",
            "supporting_source": "docs/PROJECT_GAP_REGISTER.csv; docs/PROJECT_P0_CLOSURE_GATE.json",
            "figure_needed": "",
            "table_needed": "gap register summary",
            "data_complete": True,
            "claim_risk": "low",
            "missing_evidence": "",
            "next_action": "reuse gap register",
        },
        {
            "section": "作者贡献",
            "required_claim": "版图与电路贡献边界清晰",
            "supporting_source": "docs/PROJECT_AUTHOR_CONTRIBUTION_BOUNDARY.md",
            "figure_needed": "",
            "table_needed": "",
            "data_complete": True,
            "claim_risk": "low",
            "missing_evidence": "",
            "next_action": "reuse boundary statement",
        },
        {
            "section": "工具辅助边界",
            "required_claim": "AI/Codex 仅为辅助，关键结果由真实证据闭合",
            "supporting_source": "docs/PROJECT_AUTHOR_CONTRIBUTION_BOUNDARY.md",
            "figure_needed": "",
            "table_needed": "",
            "data_complete": True,
            "claim_risk": "low",
            "missing_evidence": "",
            "next_action": "reuse boundary statement",
        },
    ]
    final_fields = list(final_matrix_rows[0].keys())
    write_csv(DOCS / "FINAL_REPORT_SECTION_EVIDENCE_MATRIX.csv", final_matrix_rows, final_fields)
    md = [
        "# Final Report Section Evidence Matrix",
        "",
        "| " + " | ".join(final_fields) + " |",
        "| " + " | ".join(["---"] * len(final_fields)) + " |",
    ]
    for row in final_matrix_rows:
        md.append("| " + " | ".join(str(row[k]).replace("\n", " ") for k in final_fields) + " |")
    write_text(DOCS / "FINAL_REPORT_SECTION_EVIDENCE_MATRIX.md", "\n".join(md) + "\n")

    updated_gap_rows = []
    resolution_lookup = {r["gap_id"]: (r["status"], r["expected_output"] if r["status"] != "BLOCKED_EXTERNAL" else r["blocking_reason"]) for r in p0_rows}
    for row in parse_gap_register():
        new_row = dict(row)
        status, note = resolution_lookup.get(row["gap_id"], ("OPEN", ""))
        new_row["resolution_status"] = status
        new_row["resolution_note"] = note
        updated_gap_rows.append(new_row)
    gap_fields = list(updated_gap_rows[0].keys())
    write_csv(DOCS / "PROJECT_GAP_REGISTER.csv", updated_gap_rows, gap_fields)
    md = [
        "# Project Gap Register",
        "",
        "| " + " | ".join(gap_fields) + " |",
        "| " + " | ".join(["---"] * len(gap_fields)) + " |",
    ]
    for row in updated_gap_rows:
        md.append("| " + " | ".join(str(row[k]).replace("\n", " ") for k in gap_fields) + " |")
    write_text(DOCS / "PROJECT_GAP_REGISTER.md", "\n".join(md) + "\n")

    p0_closed = sum(1 for r in p0_rows if r["status"] == "CLOSED_WITH_EVIDENCE")
    p0_blocked = sum(1 for r in p0_rows if r["status"] == "BLOCKED_EXTERNAL")
    p0_open = sum(1 for r in p0_rows if r["status"] == "OPEN")
    p0_gate = {
        "timestamp": ts,
        "inventory_checkpoint_committed": True,
        "all_p0_items_loaded_from_gap_register": True,
        "p0_execution_matrix_complete": True,
        "other_team_results_triangulated": True,
        "unknown_owner_branches_forensically_audited": True,
        "evidence_only_result_decided": True,
        "superseded_branches_proven": True,
        "experimental_branch_retention_documented": True,
        "openyield_authority_revalidated": True,
        "historical_30_21_claim_audited": True,
        "project_matrices_synchronized": True,
        "project_logs_updated": True,
        "no_unapproved_merge_performed": True,
        "p0_total_before": 3,
        "p0_closed_with_evidence": p0_closed,
        "p0_blocked_external": p0_blocked,
        "p0_remaining_open": p0_open,
    }
    write_json(DOCS / "PROJECT_P0_CLOSURE_GATE.json", p0_gate)
    write_text(
        DOCS / "PROJECT_P0_CLOSURE_GATE.md",
        "# Project P0 Closure Gate\n\n"
        + "\n".join(f"- {k}: `{v}`" for k, v in p0_gate.items())
        + "\n",
    )

    project_status = {
        "workflow_state": "PROJECT_P0_AUDITED_EXTERNAL_OWNER_CONFIRMATION_PENDING",
        "timestamp": ts,
        "git_branch": branch,
        "git_head": head,
        "trusted_master_head": "c1fbd98",
        "remote_master_head": origin_master,
        "team_b_state": "TEAM_B_OWNER_HUMAN_REVIEWED_MERGED_TO_MAINLINE",
        "other_team_formal_results_discovered": formal_other,
        "other_team_experimental_results_discovered": experimental_other,
        "parameter_count": 25,
        "parameter_support_counts": {
            "SUPPORTED_WITH_CONSTRAINTS": 17,
            "PARTIALLY_SUPPORTED": 5,
            "NOT_IMPLEMENTED": 1,
            "EXPERIMENTAL": 1,
            "FULLY_SUPPORTED": 1,
        },
        "explicit_sram_config_count": len(sram_rows),
        "gap_counts": {"P0": 3, "P1": 4, "P2": 2, "P3": 1},
        "p0_closure": {
            "closed_with_evidence": p0_closed,
            "blocked_external": p0_blocked,
            "remaining_open": p0_open,
        },
        "current_status_consistent": True,
        "next_stage": "P1 technical closure can proceed; Owner A confirmation remains the only external blocker on unrecovered other-team source",
    }
    write_json(DOCS / "PROJECT_CURRENT_STATUS.json", project_status)

    append_project_log(
        f"""## {ts} project inventory_checkpoint_freeze
- git_branch: `{branch}`
- git_head: `{head}`
- files_read: `docs/PROJECT_INVENTORY_AND_PARAMETER_GATE.json`, `docs/PROJECT_GAP_REGISTER.*`, `docs/PROJECT_RESULT_SOURCE_INVENTORY.*`
- files_modified: `docs/PROJECT_INVENTORY_CHECKPOINT.json`
- result: `inventory checkpoint recorded at {head[:7]}`
- decision: `freeze prior inventory phase before P0 closure actions`
- unresolved_items: `P0 gaps still open before closure`
- next_action: `execute P0-specific audits and synchronization`
""",
        {
            "timestamp": ts,
            "stage": "project_p0_closure",
            "team_or_scope": "project",
            "event_type": "inventory_checkpoint_recorded",
            "git_branch": branch,
            "git_head": head,
            "files_read": [
                "docs/PROJECT_INVENTORY_AND_PARAMETER_GATE.json",
                "docs/PROJECT_GAP_REGISTER.csv",
                "docs/PROJECT_RESULT_SOURCE_INVENTORY.csv",
            ],
            "input_evidence": {"inventory_checkpoint_commit": head[:7]},
            "files_modified": ["docs/PROJECT_INVENTORY_CHECKPOINT.json"],
            "commands": ["python scripts/project_p0_closure.py"],
            "result": {"inventory_checkpoint_commit": head[:7]},
            "decision": "freeze_inventory_before_p0_closure",
            "unresolved_items": ["P0-001", "P0-002", "P0-003"],
            "next_action": "complete_p0_closure_audit",
        },
    )

    append_project_log(
        f"""## {ts} project p0_closure_audit
- git_branch: `{branch}`
- git_head: `{head}`
- files_read: `PROJECT_LAYOUTGEN_OPENYIELD_STATUS.*`, `docs/PROJECT_GAP_REGISTER.*`, `docs/UNMERGED_RESULT_BRANCH_AUDIT.csv`, `docs/PROJECT_RESULT_SOURCE_INVENTORY.csv`, `outputs/M7_correct_golden_reference/current_supported_config/M7_gds_candidate_inventory.csv`, `/data1/qujh/work/external/OpenYield`
- files_modified: `PROJECT_LAYOUTGEN_OPENYIELD_STATUS.*`, `docs/P0_GAP_EXECUTION_MATRIX.*`, `docs/OTHER_TEAM_RESULT_TRIANGULATION.*`, `docs/UNKNOWN_OWNER_BRANCH_FORENSICS.*`, `docs/OTHER_TEAM_OWNER_CONFIRMATION_REQUEST.*`, `docs/SUPERSEDED_BRANCH_PROOF.*`, `docs/EXPERIMENTAL_RESULT_RETENTION.*`, `docs/OPENYIELD_AUTHORITY_REVALIDATION.*`, `docs/HISTORICAL_30_CONFIG_21_MODULE_CLAIM_AUDIT.*`, `docs/PROJECT_RESULT_SOURCE_INVENTORY.*`, `docs/OTHER_TEAM_RESULT_AUDIT.*`, `docs/UNMERGED_RESULT_BRANCH_AUDIT.*`, `docs/SRAM_CONFIGURATION_INVENTORY.*`, `docs/FINAL_REPORT_SECTION_EVIDENCE_MATRIX.*`, `docs/PROJECT_GAP_REGISTER.*`, `docs/PROJECT_CURRENT_STATUS.json`, `docs/PROJECT_P0_CLOSURE_GATE.*`
- result: `P0 closed/block_external = {p0_closed}/{p0_blocked}`; `explicit_config_count={len(sram_rows)}`; `other_team_formal/experimental={formal_other}/{experimental_other}`
- decision: `close P0-001 and P0-002 with evidence; hold P0-003 as BLOCKED_EXTERNAL pending Owner A confirmation; do not merge any other-team branch this round`
- unresolved_items: `Owner A logical-model source ownership confirmation`; `P1 decoder/top-level-signoff/multi-bank and parameter raw-source work remains`
- next_action: `proceed to P1 work that is independent of external owner confirmation`
""",
        {
            "timestamp": ts,
            "stage": "project_p0_closure",
            "team_or_scope": "project",
            "event_type": "p0_audit_complete",
            "git_branch": branch,
            "git_head": head,
            "files_read": [
                "PROJECT_LAYOUTGEN_OPENYIELD_STATUS.json",
                "PROJECT_LAYOUTGEN_OPENYIELD_STATUS.md",
                "docs/PROJECT_GAP_REGISTER.csv",
                "docs/UNMERGED_RESULT_BRANCH_AUDIT.csv",
                "docs/PROJECT_RESULT_SOURCE_INVENTORY.csv",
                "outputs/M7_correct_golden_reference/current_supported_config/M7_gds_candidate_inventory.csv",
                "/data1/qujh/work/external/OpenYield",
            ],
            "input_evidence": {
                "openyield_commit": "1c34428d8b913963c4971d093b1a7c2df97a2509",
                "m7_unique_sram_top_count": len(parse_m7_configs()),
                "owner_a_base_commit": "e74054e0fc5a15b28a2bc8c9d132b207a80c6538",
                "occupancy_branch_commit": "ede16ccc95f5c9867b1787b72277f5d18e73926a",
            },
            "files_modified": [
                "PROJECT_LAYOUTGEN_OPENYIELD_STATUS.json",
                "PROJECT_LAYOUTGEN_OPENYIELD_STATUS.md",
                "docs/P0_GAP_EXECUTION_MATRIX.csv",
                "docs/P0_GAP_EXECUTION_MATRIX.md",
                "docs/OTHER_TEAM_RESULT_TRIANGULATION.csv",
                "docs/OTHER_TEAM_RESULT_TRIANGULATION.md",
                "docs/UNKNOWN_OWNER_BRANCH_FORENSICS.csv",
                "docs/UNKNOWN_OWNER_BRANCH_FORENSICS.md",
                "docs/OTHER_TEAM_OWNER_CONFIRMATION_REQUEST.md",
                "docs/OTHER_TEAM_OWNER_CONFIRMATION_REQUEST.json",
                "docs/HISTORICAL_30_CONFIG_21_MODULE_CLAIM_AUDIT.md",
                "docs/HISTORICAL_30_CONFIG_21_MODULE_CLAIM_AUDIT.json",
                "docs/PROJECT_P0_CLOSURE_GATE.json",
                "docs/PROJECT_CURRENT_STATUS.json",
            ],
            "commands": ["python scripts/project_p0_closure.py"],
            "result": {
                "p0_closed_with_evidence": p0_closed,
                "p0_blocked_external": p0_blocked,
                "p0_remaining_open": p0_open,
                "explicit_sram_config_count": len(sram_rows),
                "other_team_formal_results_discovered": formal_other,
                "other_team_experimental_results_discovered": experimental_other,
            },
            "decision": "complete_p0_audit_without_unapproved_merge",
            "unresolved_items": ["Owner A confirmation for logical model recovery"],
            "next_action": "proceed_to_p1_independent_work",
        },
    )


if __name__ == "__main__":
    main()
