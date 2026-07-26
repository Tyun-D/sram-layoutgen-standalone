from __future__ import annotations

import hashlib
import json
import shutil
from pathlib import Path
from typing import Any


HISTORICAL_WRONG_REFERENCE = "outputs/layout_prototype/hybrid_openyield_rail_overlap/hybrid_openyield_rail_overlap.complete.gds"
CURRENT_GOLDEN_REFERENCE_PATH = "outputs/M7_correct_golden_reference/current_supported_config/golden_reference.gds"
CURRENT_GOLDEN_REFERENCE_CLEAN_REVIEW_PATH = (
    "outputs/M7_correct_golden_reference/current_supported_config/golden_reference_clean_review.gds"
)
NEXT_STAGE_ALLOWED = "M8_REPRODUCE_UPLOADED_GOLDEN_REFERENCE"
M7_BLOCKERS_BEFORE = [
    "Human KLayout review of uploaded golden reference is required.",
    "Next repair stage must reproduce the new uploaded golden reference instead of historical hybrid reference.",
]


def _read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _json_dump(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8", newline="\n")


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _copy(src: Path, dst: Path) -> Path:
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dst)
    return dst


def _rel(repo_root: Path, path: Path) -> str:
    return path.resolve().relative_to(repo_root.resolve()).as_posix()


def _render_status_md(report: dict[str, Any]) -> str:
    cleared = report["m7_blockers_cleared"]
    lines = [
        "# OpenYield SRAM LayoutGen Project Status",
        "",
        "## 1. Current Correct Goal",
        "",
        "先复现并修复用户上传确认的正确 layoutgen golden reference，再以该 golden 为唯一物理目标推进后续修复与最终 OpenYield 集成。",
        "",
        "## 2. Current Stage",
        "",
        "- current_stage: `M7C`",
        f"- next_stage: `{report['next_stage_allowed']}`",
        "- human_klayout_review_required_every_stage: `True`",
        "- can_enter_next_stage_without_human_review: `False`",
        "",
        "## 3. Latest Human Review",
        "",
        f"- User confirmed `{report['current_golden_reference_clean_review_path']}` is the correct uploaded golden reference.",
        f"- historical_wrong_reference: `{HISTORICAL_WRONG_REFERENCE}` must remain non-golden.",
        "- M7 blocker 1 cleared: human KLayout review of the uploaded golden reference is complete.",
        "- M7 blocker 2 cleared: next repair stage is locked to reproducing the uploaded golden reference rather than the historical hybrid reference.",
        "",
        "## 4. M7C Result",
        "",
        f"- golden_reference_user_confirmed: `{report['golden_reference_user_confirmed']}`",
        f"- golden_reference_is_now_locked: `{report['golden_reference_is_now_locked']}`",
        f"- current_golden_reference_path: `{report['current_golden_reference_path']}`",
        f"- current_golden_reference_clean_review_path: `{report['current_golden_reference_clean_review_path']}`",
        f"- historical_wrong_reference: `{HISTORICAL_WRONG_REFERENCE}`",
        f"- hybrid_openyield_rail_overlap_is_golden: `{report['hybrid_openyield_rail_overlap_is_golden']}`",
        f"- new_uploaded_reference_is_golden: `{report['new_uploaded_reference_is_golden']}`",
        f"- m7_blockers_before_count: `{report['m7_blockers_before_count']}`",
        f"- m7_blockers_after_count: `{report['m7_blockers_after_count']}`",
        "",
        "## 5. Blocker Clearance",
        "",
        *[f"- {item}" for item in cleared],
        "",
        "## 6. Next Immediate Task",
        "",
        f"进入 `{report['next_stage_allowed']}`，先复现 `{report['current_golden_reference_path']}`。注意：M8 新生成的 GDS 仍然必须等待人工 KLayout review，不能直接跨阶段声称完成。",
        "",
    ]
    return "\n".join(lines)


def _update_status_json(status: dict[str, Any], report: dict[str, Any], repo_root: Path) -> dict[str, Any]:
    updated = dict(status)
    updated["current_stage"] = "M7C"
    updated["next_stage"] = NEXT_STAGE_ALLOWED
    updated["next_stage_allowed"] = NEXT_STAGE_ALLOWED
    updated["next_task_summary"] = (
        "Proceed to M8 by reproducing the uploaded golden reference first; any M8-generated GDS still requires human KLayout review."
    )
    updated["golden_reference_user_confirmed"] = True
    updated["golden_reference_is_now_locked"] = True
    updated["current_golden_reference_path"] = CURRENT_GOLDEN_REFERENCE_PATH
    updated["current_golden_reference_clean_review_path"] = CURRENT_GOLDEN_REFERENCE_CLEAN_REVIEW_PATH
    updated["current_golden_reference"] = str((repo_root / CURRENT_GOLDEN_REFERENCE_PATH).resolve())
    updated["historical_wrong_reference"] = HISTORICAL_WRONG_REFERENCE
    updated["hybrid_openyield_rail_overlap_is_golden"] = False
    updated["new_uploaded_reference_is_golden"] = True
    updated["next_stage_must_reproduce_uploaded_golden_reference"] = True
    updated["can_enter_next_stage_without_human_review"] = False
    updated["last_human_review"] = (
        "M7C confirmation:\n"
        f"- User confirmed {CURRENT_GOLDEN_REFERENCE_CLEAN_REVIEW_PATH} is the correct uploaded golden reference.\n"
        f"- {HISTORICAL_WRONG_REFERENCE} remains a historical wrong reference and is not golden.\n"
        f"- Next allowed stage is {NEXT_STAGE_ALLOWED}, which must reproduce the uploaded golden reference first.\n"
        "- M8-generated GDS still requires human KLayout review before any later stage transition."
    )
    updated["last_M7C_report"] = report
    last_m7 = dict(updated.get("last_M7_report", {}))
    last_m7["human_klayout_review_required"] = False
    last_m7["can_enter_next_stage_before_human_review"] = True
    last_m7["remaining_M7_blockers"] = []
    last_m7["remaining_M7_blockers_count"] = 0
    updated["last_M7_report"] = last_m7
    return updated


def _render_report_md(report: dict[str, Any], manifest: dict[str, Any]) -> str:
    lines = [
        "# M7C Golden Reference Confirmation Report",
        "",
        f"- status_file_read: `{report['status_file_read']}`",
        f"- status_file_updated: `{report['status_file_updated']}`",
        f"- golden_reference_user_confirmed: `{report['golden_reference_user_confirmed']}`",
        f"- golden_reference_is_now_locked: `{report['golden_reference_is_now_locked']}`",
        f"- current_golden_reference_path: `{report['current_golden_reference_path']}`",
        f"- current_golden_reference_clean_review_path: `{report['current_golden_reference_clean_review_path']}`",
        f"- hybrid_openyield_rail_overlap_is_golden: `{report['hybrid_openyield_rail_overlap_is_golden']}`",
        f"- new_uploaded_reference_is_golden: `{report['new_uploaded_reference_is_golden']}`",
        f"- m7_blockers_before_count: `{report['m7_blockers_before_count']}`",
        f"- m7_blockers_after_count: `{report['m7_blockers_after_count']}`",
        f"- next_stage_allowed: `{report['next_stage_allowed']}`",
        f"- can_enter_M8_after_this_gate: `{report['can_enter_M8_after_this_gate']}`",
        f"- human_klayout_review_required_for_M8_output: `{report['human_klayout_review_required_for_M8_output']}`",
        f"- can_enter_next_stage_without_human_review: `{report['can_enter_next_stage_without_human_review']}`",
        "",
        "## Cleared M7 Blockers",
        "",
        *[f"- {item}" for item in report["m7_blockers_cleared"]],
        "",
        "## Review GDS Manifest",
        "",
        f"- source_gds: `{manifest['source_gds']}`",
        f"- copied_review_gds: `{manifest['copied_review_gds']}`",
        f"- size_bytes: `{manifest['size_bytes']}`",
        f"- sha256: `{manifest['sha256']}`",
        "",
        "## Gate Decision",
        "",
        f"M7C clears the two M7 blockers and allows `{report['next_stage_allowed']}` to start. M8 output still requires a fresh human KLayout review before any later-stage transition.",
        "",
    ]
    return "\n".join(lines)


def _render_manifest_md(manifest: dict[str, Any]) -> str:
    lines = [
        "# M7C Review GDS Manifest",
        "",
        f"- source_gds: `{manifest['source_gds']}`",
        f"- copied_review_gds: `{manifest['copied_review_gds']}`",
        f"- size_bytes: `{manifest['size_bytes']}`",
        f"- sha256: `{manifest['sha256']}`",
        f"- source_exists: `{manifest['source_exists']}`",
        f"- copied_exists: `{manifest['copied_exists']}`",
        f"- file_name: `{manifest['file_name']}`",
        "",
    ]
    return "\n".join(lines)


def _render_evidence_summary(report: dict[str, Any], manifest: dict[str, Any]) -> str:
    lines = [
        "# M7C Golden Reference Confirmation Summary",
        "",
        f"- M7C completed: `{report['can_enter_M8_after_this_gate']}`",
        f"- current_golden_reference_path: `{report['current_golden_reference_path']}`",
        f"- current_golden_reference_clean_review_path: `{report['current_golden_reference_clean_review_path']}`",
        f"- historical_wrong_reference: `{HISTORICAL_WRONG_REFERENCE}`",
        f"- m7_blockers_before_count: `{report['m7_blockers_before_count']}`",
        f"- m7_blockers_after_count: `{report['m7_blockers_after_count']}`",
        f"- next_stage_allowed: `{report['next_stage_allowed']}`",
        f"- M8 output still needs human review: `{report['human_klayout_review_required_for_M8_output']}`",
        f"- copied_review_gds_sha256: `{manifest['sha256']}`",
        "",
    ]
    return "\n".join(lines)


def run_m7c_golden_reference_confirmation(
    *,
    repo_root: Path,
    status_md: Path,
    status_json: Path,
    m7_report: Path,
    golden_reference: Path,
    golden_clean_review: Path,
    out_dir: Path,
    out_json: Path,
    out_report: Path,
) -> dict[str, Any]:
    repo_root = repo_root.resolve()
    status_md = status_md.resolve()
    status_json = status_json.resolve()
    m7_report = m7_report.resolve()
    golden_reference = golden_reference.resolve()
    golden_clean_review = golden_clean_review.resolve()
    out_dir = out_dir.resolve()
    out_json = out_json.resolve()
    out_report = out_report.resolve()

    status = _read_json(status_json)
    m7 = _read_json(m7_report)
    out_dir.mkdir(parents=True, exist_ok=True)

    copied_review = _copy(golden_clean_review, out_dir / "golden_reference_clean_review.gds")
    manifest = {
        "source_gds": _rel(repo_root, golden_clean_review),
        "copied_review_gds": _rel(repo_root, copied_review),
        "file_name": copied_review.name,
        "size_bytes": copied_review.stat().st_size,
        "sha256": _sha256(copied_review),
        "source_exists": golden_clean_review.exists(),
        "copied_exists": copied_review.exists(),
    }

    report = {
        "status_file_read": True,
        "status_file_updated": True,
        "golden_reference_user_confirmed": True,
        "golden_reference_is_now_locked": True,
        "current_golden_reference_path": CURRENT_GOLDEN_REFERENCE_PATH,
        "current_golden_reference_clean_review_path": CURRENT_GOLDEN_REFERENCE_CLEAN_REVIEW_PATH,
        "hybrid_openyield_rail_overlap_is_golden": False,
        "new_uploaded_reference_is_golden": True,
        "m7_blockers_before_count": int(m7.get("remaining_M7_blockers_count", len(M7_BLOCKERS_BEFORE))),
        "m7_blockers_after_count": 0,
        "m7_blockers_cleared": list(M7_BLOCKERS_BEFORE),
        "next_stage_allowed": NEXT_STAGE_ALLOWED,
        "can_enter_M8_after_this_gate": True,
        "human_klayout_review_required_for_M8_output": True,
        "can_enter_next_stage_without_human_review": False,
    }
    report["new_uploaded_reference_is_golden"] = bool(report["golden_reference_user_confirmed"])

    updated_status = _update_status_json(status, report, repo_root)
    _json_dump(status_json, updated_status)
    _write_text(status_md, _render_status_md(report))

    local_report_json = out_dir / "golden_reference_confirmation_report.json"
    local_report_md = out_dir / "golden_reference_confirmation_report.md"
    manifest_json = out_dir / "review_gds_manifest.json"
    manifest_md = out_dir / "review_gds_manifest.md"
    evidence_summary = repo_root / "docs/evidence/M7C_golden_reference_confirmation_summary.md"

    _json_dump(local_report_json, report)
    _write_text(local_report_md, _render_report_md(report, manifest))
    _json_dump(manifest_json, manifest)
    _write_text(manifest_md, _render_manifest_md(manifest))
    _json_dump(out_json, report)
    _write_text(out_report, _render_report_md(report, manifest))
    _write_text(evidence_summary, _render_evidence_summary(report, manifest))
    return report
