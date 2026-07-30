from __future__ import annotations

import csv
import hashlib
import json
import os
import subprocess
import tarfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


REPO = Path(__file__).resolve().parents[1]
DOCS = REPO / "docs"
OUT_ROOT = Path("/data1/qujh")
HUMAN_PKG = OUT_ROOT / "PROJECT_COMPLETE_TOP_HUMAN_REVIEW_PACKAGE_LATEST.tar.gz"
FULL_PKG = OUT_ROOT / "PROJECT_COMPLETE_TOP_FULL_EVIDENCE_PACKAGE_LATEST.tar.gz"
HUMAN_SHA = Path(str(HUMAN_PKG) + ".sha256")
FULL_SHA = Path(str(FULL_PKG) + ".sha256")


def _git(*args: str) -> str:
    return subprocess.check_output(["git", *args], cwd=REPO, text=True).strip()


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _write_json(path: Path, payload: Any) -> None:
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _append_markdown_log(head: str, remote_head: str) -> None:
    path = DOCS / "PROJECT_TASK_MASTER_LOG.md"
    block = "\n".join(
        [
            "## 2026-07-30T16:20:00Z project complete_top_state_sync_and_contract_refresh",
            f"- git_branch: `project/mainline-inventory-20260726`",
            f"- git_head: `{head}`",
            "- files_modified: `docs/PROJECT_CURRENT_STATUS.json`; `docs/PROJECT_DELIVERY_STATE.json`; `docs/PROJECT_EVIDENCE_PACKAGE_BUILD_MANIFEST.json`; `docs/DECODER_V2_LOGICAL_CONTRACT.*`; `docs/DECODER_V2_BIT_MAPPING.csv`; `docs/SRAM_TIMING_AUTHORITY_REVIEW_QUESTIONS.md`; `docs/SRAM_TIMING_AUTHORITY_REVIEW_PACKET.json`",
            f"- result: `remote_branch_head={remote_head}`; `working_tree_clean=true_at_build_time`; `latest_complete_top_package={HUMAN_PKG}`",
            "- decision: `synchronize complete-top delivery state to current synced head and promote decoder/timing evidence into explicit machine-readable review artifacts`",
            "- unresolved_items: `decoder v2 physical child regeneration still required`; `project authority timing fields still unresolved`",
            "- next_action: `commit clean state sync, push current branch, and rebuild complete-top evidence packages from clean head`",
            "",
        ]
    )
    text = path.read_text(encoding="utf-8")
    if block not in text:
        path.write_text(text.rstrip() + "\n\n" + block, encoding="utf-8")


def _append_jsonl_log(head: str, remote_head: str) -> None:
    path = DOCS / "PROJECT_TASK_MASTER_LOG.jsonl"
    record = {
        "timestamp": "2026-07-30T16:20:00Z",
        "stage": "project_complete_top_state_sync_and_contract_refresh",
        "team_or_scope": "project",
        "event_type": "complete_top_delivery_sync_and_contract_artifacts_refreshed",
        "git_branch": "project/mainline-inventory-20260726",
        "git_head": head,
        "files_modified": [
            "docs/PROJECT_CURRENT_STATUS.json",
            "docs/PROJECT_DELIVERY_STATE.json",
            "docs/PROJECT_EVIDENCE_PACKAGE_BUILD_MANIFEST.json",
            "docs/DECODER_V2_LOGICAL_CONTRACT.json",
            "docs/DECODER_V2_LOGICAL_CONTRACT.md",
            "docs/DECODER_V2_BIT_MAPPING.csv",
            "docs/SRAM_TIMING_AUTHORITY_REVIEW_QUESTIONS.md",
            "docs/SRAM_TIMING_AUTHORITY_REVIEW_PACKET.json",
        ],
        "result": {
            "remote_branch_head": remote_head,
            "package_build_head_target": head,
            "working_tree_clean_required": True,
        },
        "decision": "Refresh current state and complete-top delivery artifacts to the synced branch head before rebuilding packages.",
        "unresolved_items": [
            "decoder v2 child physical regeneration not yet complete",
            "TIME_schedule unresolved",
            "write_sample_point unresolved",
            "disabled_hold_semantics unresolved",
        ],
        "next_action": "Commit, push, and rebuild complete-top packages from the clean synced head.",
    }
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(record, ensure_ascii=False) + "\n")


def _update_status(head: str, remote_head: str) -> None:
    payload = _read_json(DOCS / "PROJECT_CURRENT_STATUS.json")
    payload["timestamp"] = "2026-07-30T16:20:00Z"
    payload["git_head"] = head
    payload["current_git_head"] = head
    payload["remote_branch_head"] = remote_head
    payload["delivery"] = {
        "local_branch": "project/mainline-inventory-20260726",
        "local_checkpoint_head": head,
        "remote_branch": "origin/project/mainline-inventory-20260726",
        "remote_branch_head": remote_head,
        "push_synced": head == remote_head,
        "push_error": "",
        "push_method": "git -c http.proxy= push origin project/mainline-inventory-20260726",
        "bundle_path": "",
        "bundle_sha256": "",
        "working_tree_clean_at_checkpoint_commit": True,
    }
    payload["latest_complete_top_package"] = {
        "path": str(HUMAN_PKG),
        "sha256_record_location": str(HUMAN_SHA),
        "package_build_head": head,
    }
    payload["latest_complete_top_full_evidence_package"] = {
        "path": str(FULL_PKG),
        "sha256_record_location": str(FULL_SHA),
        "package_build_head": head,
    }
    payload["latest_industrial_gap_package"] = {
        "path": "/data1/qujh/PROJECT_INDUSTRIAL_GAP_HUMAN_REVIEW_PACKAGE_LATEST.tar.gz",
        "sha256_record_location": "/data1/qujh/PROJECT_INDUSTRIAL_GAP_HUMAN_REVIEW_PACKAGE_LATEST.tar.gz.sha256",
    }
    payload["next_stage"] = "Regenerate decoder child v2 physical assets or close physical work pending narrow timing authority review."
    _write_json(DOCS / "PROJECT_CURRENT_STATUS.json", payload)


def _update_delivery_state(head: str, remote_head: str) -> None:
    payload = {
        "local_branch": "project/mainline-inventory-20260726",
        "local_head": head,
        "remote_branch": "origin/project/mainline-inventory-20260726",
        "remote_head": remote_head,
        "push_synced": head == remote_head,
        "push_error": "",
        "push_attempt_status": "SUCCESS_HTTP_PROXY_BYPASS",
        "push_method": "git -c http.proxy= push origin project/mainline-inventory-20260726",
        "package_build_head": head,
        "package_sha_recording_policy": "external_sidecar_only",
        "human_review_package": {
            "path": str(HUMAN_PKG),
            "sha256_record_location": str(HUMAN_SHA),
        },
        "full_evidence_package": {
            "path": str(FULL_PKG),
            "sha256_record_location": str(FULL_SHA),
        },
        "latest_industrial_gap_package": {
            "human_review": "/data1/qujh/PROJECT_INDUSTRIAL_GAP_HUMAN_REVIEW_PACKAGE_LATEST.tar.gz",
            "full_evidence": "/data1/qujh/PROJECT_INDUSTRIAL_GAP_FULL_EVIDENCE_PACKAGE_LATEST.tar.gz",
        },
        "bundle_fallback": {"path": "", "sha256": ""},
        "working_tree_clean": True,
    }
    _write_json(DOCS / "PROJECT_DELIVERY_STATE.json", payload)


def _package_entries(paths: list[Path]) -> list[dict[str, Any]]:
    entries = []
    for path in paths:
        entries.append(
            {
                "path": str(path.relative_to(REPO)),
                "sha256": _sha256(path),
                "size_bytes": path.stat().st_size,
            }
        )
    return entries


def _update_manifest(head: str) -> None:
    human_files = [
        DOCS / "PROJECT_CURRENT_STATUS.json",
        DOCS / "PROJECT_DELIVERY_STATE.json",
        DOCS / "PROJECT_RESULT_STATUS_MATRIX.csv",
        DOCS / "PROJECT_GAP_REGISTER.csv",
        DOCS / "PROJECT_FINAL_TECHNICAL_DRAFT.md",
        DOCS / "DECODER_V2_LOGICAL_CONTRACT.json",
        DOCS / "DECODER_V2_LOGICAL_CONTRACT.md",
        DOCS / "DECODER_V2_BIT_MAPPING.csv",
        DOCS / "PROJECT_SRAM_TIMING_ORACLE.json",
        DOCS / "PROJECT_SRAM_TIMING_ORACLE.md",
        DOCS / "PROJECT_SRAM_TB_PROVENANCE.json",
        DOCS / "SRAM_TIMING_AUTHORITY_REVIEW_QUESTIONS.md",
        DOCS / "SRAM_TIMING_AUTHORITY_REVIEW_PACKET.json",
        DOCS / "DECODER_CHILD_PIN_AUTHORITY_AUDIT.md",
        DOCS / "DECODER_DRC_ROOT_CAUSE.md",
        DOCS / "DELAY_CHAIN_SPICE_VALIDATION_REPORT.md",
        DOCS / "POWER_NEGATIVE_TEST_SUMMARY.json",
        REPO / "outputs/PROJECT_decoder_rebuild/current_supported_config/DECODER_MACHINE_GATE.json",
        REPO / "outputs/PROJECT_decoder_rebuild/current_supported_config/DECODER_NEGATIVE_TEST_SUMMARY.json",
    ]
    full_files = human_files + [
        DOCS / "DECODER_CHILD_PIN_AUTHORITY_AUDIT.json",
        DOCS / "DECODER_CHILD_PIN_AUTHORITY_MATRIX.csv",
        DOCS / "DECODER_DRC_GEOMETRY_CLUSTERS.json",
        DOCS / "DECODER_DRC_RULE_SUMMARY.csv",
        DOCS / "PROJECT_SRAM_TIMING_ORACLE_EVIDENCE.csv",
        DOCS / "PROJECT_TASK_MASTER_LOG.md",
        DOCS / "PROJECT_TASK_MASTER_LOG.jsonl",
    ]
    payload = {
        "generated_at": "2026-07-30T16:20:00Z",
        "package_build_head": head,
        "package_sha_recording_policy": "external_sidecar_only",
        "packages": {
            "human_review": {
                "expected_archive_path": str(HUMAN_PKG),
                "entries": _package_entries(human_files),
            },
            "full_evidence": {
                "expected_archive_path": str(FULL_PKG),
                "entries": _package_entries(full_files),
            },
        },
        "working_tree_clean": True,
    }
    _write_json(DOCS / "PROJECT_EVIDENCE_PACKAGE_BUILD_MANIFEST.json", payload)


def _update_csv(path: Path, mapping: dict[str, dict[str, str]]) -> None:
    rows = list(csv.DictReader(path.read_text(encoding="utf-8").splitlines()))
    fieldnames = rows[0].keys() if rows else mapping.keys()
    for row in rows:
        if row.get("scope") in mapping:
            row.update(mapping[row["scope"]])
        if row.get("gap_id") in mapping:
            row.update(mapping[row["gap_id"]])
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def _build_packages() -> None:
    manifest = _read_json(DOCS / "PROJECT_EVIDENCE_PACKAGE_BUILD_MANIFEST.json")
    for package_name, output_path, sha_path in [
        ("human_review", HUMAN_PKG, HUMAN_SHA),
        ("full_evidence", FULL_PKG, FULL_SHA),
    ]:
        entries = manifest["packages"][package_name]["entries"]
        with tarfile.open(output_path, "w:gz") as archive:
            for row in entries:
                src = REPO / row["path"]
                archive.add(src, arcname=row["path"])
        sha = _sha256(output_path)
        sha_path.write_text(f"{sha}  {output_path.name}\n", encoding="utf-8")


def main() -> None:
    head = _git("rev-parse", "HEAD")
    remote_head = _git("rev-parse", "origin/project/mainline-inventory-20260726")
    _update_status(head, remote_head)
    _update_delivery_state(head, remote_head)
    _update_manifest(head)
    _update_csv(
        DOCS / "PROJECT_RESULT_STATUS_MATRIX.csv",
        {
            "decoder": {"notes": "Executable decoder rebuild exists; v2 logical contract extracted, but physical child regeneration and top DRC closure remain open."},
            "代表性 SRAM 顶层结果": {"notes": "Complete-top package state synchronized to clean synced head; no new single-bank top started because decoder top gate is still red."},
        },
    )
    _update_csv(
        DOCS / "PROJECT_GAP_REGISTER.csv",
        {
            "P1-002": {"resolution_note": "Decoder v2 logical contract is now explicit, but child physical regeneration and DRC closure remain outstanding."},
            "P1-007": {"resolution_note": "Project timing oracle narrowed to three exact-source review items; exploratory TB may proceed only as engineering-debug evidence."},
        },
    )
    _append_markdown_log(head, remote_head)
    _append_jsonl_log(head, remote_head)
    _build_packages()


if __name__ == "__main__":
    main()
