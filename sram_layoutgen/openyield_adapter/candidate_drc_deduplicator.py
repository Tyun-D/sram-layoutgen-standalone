from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def deduplicate_candidate_drc(
    drc_report_path: Path,
    manifest_path: Path,
    repo_root: Path,
) -> dict[str, Any]:
    drc_report = json.loads(drc_report_path.read_text(encoding="utf-8"))
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    gds_by_logical = {row["logical_module"]: Path(row["gds_path"]) for row in manifest if row.get("gds_path")}

    unique_groups: dict[str, dict[str, Any]] = {}
    duplicate_groups: list[dict[str, Any]] = []
    for artifact in drc_report.get("artifacts", []):
        logical_module = artifact["logical_module"]
        report_path = Path(artifact["report_path"])
        gds_path = gds_by_logical.get(logical_module)
        group_key = f"{_sha256(report_path)}::{_sha256(gds_path) if gds_path and gds_path.exists() else 'missing-gds'}"
        row = {
            "logical_module": logical_module,
            "report_path": str(report_path),
            "report_sha256": _sha256(report_path),
            "gds_path": str(gds_path) if gds_path else "",
            "gds_sha256": _sha256(gds_path) if gds_path and gds_path.exists() else "",
            "marker_count": int(artifact.get("marker_count", 0)),
        }
        if group_key not in unique_groups:
            unique_groups[group_key] = row
        else:
            duplicate_groups.append(row)

    unique_marker_count = sum(row["marker_count"] for row in unique_groups.values())
    return {
        "raw_candidate_drc_marker_count": int(drc_report.get("candidate_cell_drc_marker_count", 0)),
        "duplicate_drc_artifact_detected": bool(duplicate_groups),
        "unique_candidate_drc_marker_count": unique_marker_count,
        "unique_artifacts": list(unique_groups.values()),
        "duplicate_artifacts": duplicate_groups,
        "deduplication_scope": "candidate top-cell DRC artifacts only",
        "repo_root": str(repo_root),
    }
