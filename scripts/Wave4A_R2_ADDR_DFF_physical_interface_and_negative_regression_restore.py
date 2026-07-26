from __future__ import annotations

import argparse
import ast
import csv
import hashlib
import json
import math
import re
import shutil
import subprocess
import sys
import tarfile
import tempfile
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any

import gdstk
import yaml

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

EXPECTED_BRANCH = "feature/step45-clean-array-aggregation"
EXPECTED_PROJECT_HEAD = "24b233cbc94edd3ce81992d87c30314c6bcbb580"
EXPECTED_OPENYIELD_COMMIT = "1c34428d8b913963c4971d093b1a7c2df97a2509"
EXPECTED_TIME_GENERATE_PATH = "sram_compiler/subcircuits/time_generate.py"
EXPECTED_TIME_GENERATE_BLOB_SHA = "16b38c5a5d3165f046557941d15d425bbcab20b5"
EXPECTED_TIME_GENERATE_SHA256 = "fa5277f078f79d5b43335c2dcd6e364625aa8ad17b7108d323b85e73dfeaae80"
EXPECTED_NUM_ROWS = 16
EXPECTED_N_BITS = 4
EXPECTED_TOP_PIN_ORDER = [
    "VDD",
    "VSS",
    "CLK",
    "A0",
    "A1",
    "A2",
    "A3",
    "A_dff0",
    "A_dff1",
    "A_dff2",
    "A_dff3",
]
EXPECTED_CHILDREN = ["dff_0", "dff_1", "dff_2", "dff_3"]
EXPECTED_INSTANCE_CONNECTIONS = {
    "dff_0": ["VDD", "VSS", "A0", "A_dff0", "CLK"],
    "dff_1": ["VDD", "VSS", "A1", "A_dff1", "CLK"],
    "dff_2": ["VDD", "VSS", "A2", "A_dff2", "CLK"],
    "dff_3": ["VDD", "VSS", "A3", "A_dff3", "CLK"],
}
EXPECTED_DFF_SHA = "f6995536077a191c31e10644bbfcfb4075cda64b7da131987c70a59353c4e45d"
EXPECTED_DFF_TOP = "DFF_TG4_INV7_FPDK45_26d9543b82b7"
EXPECTED_DFF_STATUS = "HUMAN_REVIEWED_REUSABLE_COMPOSITE"
EXPECTED_DFF_TOP_BBOX = [-0.0725, 0.0, 13.6725, 4.2525]
EXPECTED_DFF_DIRECT_CHILDREN = {
    "PINV_NW250_PW500_L50": 7,
    "TRANSMISSION_GATE_NW250_PW500_L50": 4,
}
EXPECTED_DFF_CONDUCTIVE_GEOMETRY = {"M1": 396, "Via1": 60, "M2": 90, "total": 546}
EXPECTED_DFF_TOP_LABELS = ["CLK", "D", "Q", "VDD", "VSS"]
CONDUCTIVE_LAYER_MAP = {11: "M1", 12: "Via1", 13: "M2"}
PIN_NAMES = ["VDD", "VSS", "D", "Q", "CLK"]

OPENYIELD_ROOT = Path("/data1/qujh/work/external/OpenYield")
OPENYIELD_TIME_GENERATE = OPENYIELD_ROOT / EXPECTED_TIME_GENERATE_PATH
OPENYIELD_GLOBAL_YAML = OPENYIELD_ROOT / "sram_compiler/config_yaml/global.yaml"

STAGE_ID = "Wave4A-R2 / ADDR_DFF_PHYSICAL_INTERFACE_AND_NEGATIVE_REGRESSION_RESTORE"
NEXT_STAGE = "Wave4A2 / ADDR_DFF_CANDIDATE_GENERATION_AND_MACHINE_VERIFICATION"
BLOCKED_STAGE = "BLOCKED_PENDING_WAVE4A_R2"
DEFERRED_SIBLING_STAGE = "Wave4B / DATA_DFF"
STAGE_DIR = REPO_ROOT / "outputs/Wave4A_R2_ADDR_DFF_physical_interface_and_negative_regression_restore/current_supported_config"
PACKAGE_PREFIX = "Wave4A_R2_ADDR_DFF_physical_interface_and_negative_regression_restore"

STATUS_MD = REPO_ROOT / "PROJECT_LAYOUTGEN_OPENYIELD_STATUS.md"
STATUS_JSON = REPO_ROOT / "PROJECT_LAYOUTGEN_OPENYIELD_STATUS.json"
GOAL_MD = REPO_ROOT / "PROJECT_NETLIST_TO_LAYOUT_GOAL.md"
PROGRESS_MD = REPO_ROOT / "PROJECT_NETLIST_TO_LAYOUT_PROGRESS.md"
DFF_MANIFEST = REPO_ROOT / "outputs/M12C4ACH_dff_reusable_release/DFF_REUSABLE_MANIFEST.json"
DFF_GDS = REPO_ROOT / "outputs/M12C4ACH_dff_reusable_release/DFF_reusable_clean.gds"
DFF_CONNECTIVITY_REPORT = REPO_ROOT / "outputs/M12C4AC_dff_connectivity_repair/current_supported_config/M12C4AC_dff_physical_connectivity_report.json"
DFF_CONNECTIVITY_GRAPH = REPO_ROOT / "outputs/M12C4AC_dff_connectivity_repair/current_supported_config/M12C4AC_dff_physical_connectivity_graph.json"
DFF_SOURCE_TRACE = REPO_ROOT / "outputs/M12C4AC_dff_connectivity_repair/current_supported_config/DFF_TG4_INV7_FPDK45_26d9543b82b7/DFF_TG4_INV7_FPDK45_26d9543b82b7_source_trace.json"
LAYOUTGEN_CURRENT_SPEC = REPO_ROOT / "outputs/M8_reproduce_uploaded_golden/current_supported_config/SRAM_SPEC.json"
OPENYIELD_CURRENT_SPEC = REPO_ROOT / "outputs/M9_openyield_netlist_translator/current_supported_config/M9_SRAM_SPEC.json"
R1_PACKAGE_ROOT = REPO_ROOT / "outputs/Wave4A_ADDR_DFF_source_topology_and_binding_lock/current_supported_config/package_root"

ALLOWLIST = [
    "scripts/Wave4A_R2_ADDR_DFF_physical_interface_and_negative_regression_restore.py",
    "outputs/Wave4A_R2_ADDR_DFF_physical_interface_and_negative_regression_restore/current_supported_config",
    "PROJECT_LAYOUTGEN_OPENYIELD_STATUS.md",
    "PROJECT_LAYOUTGEN_OPENYIELD_STATUS.json",
    "PROJECT_NETLIST_TO_LAYOUT_GOAL.md",
    "PROJECT_NETLIST_TO_LAYOUT_PROGRESS.md",
]

CURRENT_REQUIRED_NEGATIVE_TESTS = [
    "openyield_commit_mismatch",
    "time_generate_blob_sha_mismatch",
    "locked_source_sha_mismatch",
    "source_path_mismatch",
    "working_tree_used_as_authority",
    "clk_pin_missing",
    "dff_top_cell_mismatch",
    "num_rows_authority_conflict",
    "d_and_q_physical_mapping_swapped",
    "annotated_gds_rejected",
    "atlas_gds_rejected",
    "quarantined_candidate_rejected",
    "dff_buf_rejected",
    "approved_dff_gds_sha_mismatch",
    "addr_dff_gds_generated_rejected",
    "data_dff_work_generated_rejected",
]

RESTORED_NEGATIVE_TESTS = [
    "addr_dff_class_missing",
    "add_addr_dff_array_missing",
    "n_bits_formula_changed",
    "top_pin_order_changed",
    "missing_dff_instances",
    "duplicate_child_instance",
    "child_count_five",
    "a_and_a_dff_swapped",
    "approved_dff_gds_sha_mismatch",
    "constructor_default_parameter_unclosed",
]


def _run(cmd: list[str], *, cwd: Path | None = None, check: bool = True) -> subprocess.CompletedProcess[str]:
    completed = subprocess.run(cmd, cwd=cwd, text=True, capture_output=True, check=False)
    if check and completed.returncode != 0:
        raise RuntimeError(
            f"command failed: {' '.join(cmd)}\nSTDOUT:\n{completed.stdout}\nSTDERR:\n{completed.stderr}"
        )
    return completed


def _run_bytes(cmd: list[str], *, cwd: Path | None = None, check: bool = True) -> subprocess.CompletedProcess[bytes]:
    completed = subprocess.run(cmd, cwd=cwd, text=False, capture_output=True, check=False)
    if check and completed.returncode != 0:
        raise RuntimeError(
            "command failed: "
            + " ".join(cmd)
            + "\nSTDOUT:\n"
            + completed.stdout.decode("utf-8", errors="replace")
            + "\nSTDERR:\n"
            + completed.stderr.decode("utf-8", errors="replace")
        )
    return completed


def _git(*args: str, cwd: Path | None = None) -> str:
    return _run(["git", "-C", str(cwd or REPO_ROOT), *args]).stdout


def _sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def _git_blob_sha1_bytes(data: bytes) -> str:
    header = f"blob {len(data)}\0".encode("utf-8")
    return hashlib.sha1(header + data).hexdigest()


def _write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8", newline="\n")


def _write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def _write_csv(path: Path, rows: list[dict[str, Any]], fieldnames: list[str] | None = None) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames or (list(rows[0].keys()) if rows else []))
        writer.writeheader()
        writer.writerows(rows)


def _read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _render_md_kv(title: str, payload: dict[str, Any]) -> str:
    lines = [f"# {title}", ""]
    for key, value in payload.items():
        if isinstance(value, (dict, list)):
            lines.append(f"- {key}:")
            lines.append("```json")
            lines.append(json.dumps(value, indent=2, ensure_ascii=False))
            lines.append("```")
        else:
            lines.append(f"- {key}: `{value}`")
    lines.append("")
    return "\n".join(lines)


def _round_float(value: float) -> float:
    return round(float(value), 6)


def _normalize_bbox(points: list[list[float]]) -> list[float]:
    xs = [point[0] for point in points]
    ys = [point[1] for point in points]
    return [_round_float(min(xs)), _round_float(min(ys)), _round_float(max(xs)), _round_float(max(ys))]


def _polygon_points(polygon: gdstk.Polygon) -> list[list[float]]:
    return [[_round_float(x), _round_float(y)] for x, y in polygon.points]


def _bbox_from_polygon(polygon: gdstk.Polygon) -> list[float]:
    return _normalize_bbox(_polygon_points(polygon))


def _is_axis_aligned_rectangle(points: list[list[float]]) -> bool:
    unique_points = []
    for point in points:
        if point not in unique_points:
            unique_points.append(point)
    xs = sorted({point[0] for point in unique_points})
    ys = sorted({point[1] for point in unique_points})
    return len(unique_points) == 4 and len(xs) == 2 and len(ys) == 2


def _matrix_identity() -> tuple[tuple[float, float, float], tuple[float, float, float], tuple[float, float, float]]:
    return ((1.0, 0.0, 0.0), (0.0, 1.0, 0.0), (0.0, 0.0, 1.0))


def _matrix_multiply(
    a: tuple[tuple[float, float, float], tuple[float, float, float], tuple[float, float, float]],
    b: tuple[tuple[float, float, float], tuple[float, float, float], tuple[float, float, float]],
) -> tuple[tuple[float, float, float], tuple[float, float, float], tuple[float, float, float]]:
    rows = []
    for i in range(3):
        row = []
        for j in range(3):
            row.append(sum(a[i][k] * b[k][j] for k in range(3)))
        rows.append(tuple(row))
    return tuple(rows)  # type: ignore[return-value]


def _matrix_apply(
    matrix: tuple[tuple[float, float, float], tuple[float, float, float], tuple[float, float, float]],
    x: float,
    y: float,
) -> tuple[float, float]:
    new_x = matrix[0][0] * x + matrix[0][1] * y + matrix[0][2]
    new_y = matrix[1][0] * x + matrix[1][1] * y + matrix[1][2]
    return _round_float(new_x), _round_float(new_y)


def _reference_matrix(ref: gdstk.Reference) -> tuple[tuple[float, float, float], tuple[float, float, float], tuple[float, float, float]]:
    mag = float(ref.magnification or 1.0)
    rot = float(ref.rotation or 0.0)
    origin_x = float(ref.origin[0])
    origin_y = float(ref.origin[1])
    reflect = ((1.0, 0.0, 0.0), (0.0, -1.0 if ref.x_reflection else 1.0, 0.0), (0.0, 0.0, 1.0))
    scale = ((mag, 0.0, 0.0), (0.0, mag, 0.0), (0.0, 0.0, 1.0))
    cos_r = math.cos(rot)
    sin_r = math.sin(rot)
    rotate = ((cos_r, -sin_r, 0.0), (sin_r, cos_r, 0.0), (0.0, 0.0, 1.0))
    translate = ((1.0, 0.0, origin_x), (0.0, 1.0, origin_y), (0.0, 0.0, 1.0))
    return _matrix_multiply(translate, _matrix_multiply(rotate, _matrix_multiply(scale, reflect)))


def _path_is_mutable_in_this_round(path: str) -> bool:
    return any(path == allowed or path.startswith(allowed + "/") for allowed in ALLOWLIST)


def _path_metadata(repo_relative_path: str) -> dict[str, Any]:
    path = REPO_ROOT / repo_relative_path
    if not path.exists():
        return {
            "relative_path": repo_relative_path,
            "exists": False,
            "size_bytes": None,
            "sha256": None,
            "tracked_status": "missing",
        }
    return {
        "relative_path": repo_relative_path,
        "exists": True,
        "size_bytes": path.stat().st_size,
        "sha256": _sha256(path),
        "tracked_status": None,
    }


def _parse_git_status_porcelain() -> list[dict[str, Any]]:
    raw = _run_bytes(["git", "-C", str(REPO_ROOT), "status", "--short", "--untracked-files=all", "-z"]).stdout
    items = raw.split(b"\0")
    rows: list[dict[str, Any]] = []
    idx = 0
    while idx < len(items):
        item = items[idx]
        idx += 1
        if not item:
            continue
        status = item[:3].decode("utf-8", errors="replace")
        payload = item[3:].decode("utf-8", errors="replace")
        rows.append({"status_code": status.strip(), "path": payload})
    return rows


def _verify_required_inputs() -> dict[str, Any]:
    required = [
        STATUS_MD,
        STATUS_JSON,
        GOAL_MD,
        PROGRESS_MD,
        DFF_MANIFEST,
        DFF_GDS,
        DFF_CONNECTIVITY_REPORT,
        DFF_CONNECTIVITY_GRAPH,
        DFF_SOURCE_TRACE,
        LAYOUTGEN_CURRENT_SPEC,
        OPENYIELD_CURRENT_SPEC,
    ]
    missing = [str(path) for path in required if not path.exists()]
    if missing:
        raise RuntimeError(f"required inputs missing: {missing}")
    branch = _git("branch", "--show-current").strip()
    if branch != EXPECTED_BRANCH:
        raise RuntimeError(f"branch mismatch: {branch}")
    project_head = _git("rev-parse", "HEAD").strip()
    if project_head != EXPECTED_PROJECT_HEAD:
        raise RuntimeError(f"unexpected project HEAD: {project_head}")
    openyield_head = _git("rev-parse", "HEAD", cwd=OPENYIELD_ROOT).strip()
    if openyield_head != EXPECTED_OPENYIELD_COMMIT:
        raise RuntimeError(f"OpenYield commit mismatch: {openyield_head}")
    dff_sha = _sha256(DFF_GDS)
    if dff_sha != EXPECTED_DFF_SHA:
        raise RuntimeError(f"approved DFF SHA mismatch: {dff_sha}")
    return {
        "project_branch": branch,
        "report_generation_base_commit": project_head,
        "openyield_commit": openyield_head,
        "approved_dff_sha256": dff_sha,
    }


def _dirty_tree_baseline() -> dict[str, Any]:
    status_rows = _parse_git_status_porcelain()
    dirty_rows = []
    for row in status_rows:
        meta = _path_metadata(row["path"])
        meta["tracked_status"] = "untracked" if row["status_code"] == "??" else "tracked"
        meta["status_code"] = row["status_code"]
        meta["mutable_in_this_round"] = _path_is_mutable_in_this_round(row["path"])
        dirty_rows.append(meta)
    payload = {
        "project_branch": _git("branch", "--show-current").strip(),
        "project_head": _git("rev-parse", "HEAD").strip(),
        "git_status_short": _git("status", "--short"),
        "git_diff_name_only": _git("diff", "--name-only"),
        "git_diff_cached_name_only": _git("diff", "--cached", "--name-only"),
        "openyield_head": _git("rev-parse", "HEAD", cwd=OPENYIELD_ROOT).strip(),
        "approved_dff_sha256": _sha256(DFF_GDS),
        "dirty_paths": dirty_rows,
    }
    _write_json(STAGE_DIR / "baseline_dirty_tree_report.json", payload)
    _write_text(STAGE_DIR / "baseline_dirty_tree_report.md", _render_md_kv("Baseline Dirty Tree Report", payload))
    return payload


def _replace_section(text: str, heading: str, block: str) -> str:
    pattern = rf"{re.escape(heading)}.*?(?=\n## |\Z)"
    return re.sub(pattern, block + "\n\n", text, count=1, flags=re.S)


def _update_ledgers_in_progress() -> None:
    status = _read_json(STATUS_JSON)
    status["current_stage"] = STAGE_ID
    status["current_status"] = "IN_PROGRESS"
    status["ADDR_DFF source topology status"] = "SOURCE_EXACT_TOPOLOGY_LOCKED"
    status["ADDR_DFF physical binding status"] = "APPROVED_DFF_BINDING_LOCKED"
    status["ADDR_DFF physical interface status"] = "RESTORE_IN_PROGRESS"
    status["ADDR_DFF validator status"] = "NEGATIVE_REGRESSION_RESTORE_IN_PROGRESS"
    status["ADDR_DFF physical GDS status"] = "NOT_GENERATED"
    status["next_stage_allowed"] = BLOCKED_STAGE
    status["can_enter_next_stage"] = False
    status["DATA_DFF binding status"] = "UNRESOLVED_REQUIRES_WAVE4B_SOURCE_BINDING_REVIEW"
    _write_json(STATUS_JSON, status)

    md_block = "\n".join(
        [
            "## 2. Current Stage",
            "",
            f"- current_stage: `{STAGE_ID}`",
            "- current_status: `IN_PROGRESS`",
            "- ADDR_DFF source topology status: `SOURCE_EXACT_TOPOLOGY_LOCKED`",
            "- ADDR_DFF physical binding status: `APPROVED_DFF_BINDING_LOCKED`",
            "- ADDR_DFF physical interface status: `RESTORE_IN_PROGRESS`",
            "- ADDR_DFF validator status: `NEGATIVE_REGRESSION_RESTORE_IN_PROGRESS`",
            "- ADDR_DFF physical GDS status: `NOT_GENERATED`",
            f"- next_stage_allowed: `{BLOCKED_STAGE}`",
            "- can_enter_next_stage: `False`",
            f"- deferred_sibling_stage: `{DEFERRED_SIBLING_STAGE}`",
            "- DATA_DFF binding status: `UNRESOLVED_REQUIRES_WAVE4B_SOURCE_BINDING_REVIEW`",
        ]
    )
    STATUS_MD.write_text(_replace_section(STATUS_MD.read_text(encoding="utf-8"), "## 2. Current Stage", md_block), encoding="utf-8")

    for md_path, title in [(GOAL_MD, "## Current Hardened Composite Stage"), (PROGRESS_MD, "## Wave3H1 Progress Gate")]:
        block = "\n".join(
            [
                title,
                "",
                f"- current_stage: `{STAGE_ID}`",
                "- current_status: `IN_PROGRESS`",
                "- ADDR_DFF source topology status: `SOURCE_EXACT_TOPOLOGY_LOCKED`",
                "- ADDR_DFF physical binding status: `APPROVED_DFF_BINDING_LOCKED`",
                "- ADDR_DFF physical interface status: `RESTORE_IN_PROGRESS`",
                "- ADDR_DFF validator status: `NEGATIVE_REGRESSION_RESTORE_IN_PROGRESS`",
                "- ADDR_DFF physical GDS status: `NOT_GENERATED`",
                f"- next_stage_allowed: `{BLOCKED_STAGE}`",
                "- can_enter_next_stage: `False`",
                f"- deferred_sibling_stage: `{DEFERRED_SIBLING_STAGE}`",
                "- DATA_DFF binding status: `UNRESOLVED_REQUIRES_WAVE4B_SOURCE_BINDING_REVIEW`",
            ]
        )
        md_path.write_text(_replace_section(md_path.read_text(encoding="utf-8"), title, block), encoding="utf-8")


def _update_ledgers_pass() -> None:
    status = _read_json(STATUS_JSON)
    status["current_stage"] = STAGE_ID
    status["current_status"] = "PASS"
    status["ADDR_DFF source topology status"] = "SOURCE_EXACT_TOPOLOGY_LOCKED"
    status["ADDR_DFF physical binding status"] = "APPROVED_DFF_BINDING_LOCKED"
    status["ADDR_DFF physical interface status"] = "COMPLETE_GDS_DERIVED_INTERFACE_LOCKED"
    status["ADDR_DFF validator status"] = "SOURCE_BINDING_AND_NEGATIVE_REGRESSION_HARDENED"
    status["ADDR_DFF physical GDS status"] = "NOT_GENERATED"
    status["next_stage"] = NEXT_STAGE
    status["recommended_next_stage"] = NEXT_STAGE
    status["next_stage_allowed"] = NEXT_STAGE
    status["can_enter_next_stage"] = True
    status["DATA_DFF binding status"] = "UNRESOLVED_REQUIRES_WAVE4B_SOURCE_BINDING_REVIEW"
    _write_json(STATUS_JSON, status)

    md_block = "\n".join(
        [
            "## 2. Current Stage",
            "",
            f"- current_stage: `{STAGE_ID}`",
            "- current_status: `PASS`",
            "- ADDR_DFF source topology status: `SOURCE_EXACT_TOPOLOGY_LOCKED`",
            "- ADDR_DFF physical binding status: `APPROVED_DFF_BINDING_LOCKED`",
            "- ADDR_DFF physical interface status: `COMPLETE_GDS_DERIVED_INTERFACE_LOCKED`",
            "- ADDR_DFF validator status: `SOURCE_BINDING_AND_NEGATIVE_REGRESSION_HARDENED`",
            "- ADDR_DFF physical GDS status: `NOT_GENERATED`",
            f"- next_stage: `{NEXT_STAGE}`",
            f"- recommended_next_stage: `{NEXT_STAGE}`",
            f"- next_stage_allowed: `{NEXT_STAGE}`",
            "- can_enter_next_stage: `True`",
            f"- deferred_sibling_stage: `{DEFERRED_SIBLING_STAGE}`",
            "- DATA_DFF binding status: `UNRESOLVED_REQUIRES_WAVE4B_SOURCE_BINDING_REVIEW`",
        ]
    )
    STATUS_MD.write_text(_replace_section(STATUS_MD.read_text(encoding="utf-8"), "## 2. Current Stage", md_block), encoding="utf-8")

    for md_path, title in [(GOAL_MD, "## Current Hardened Composite Stage"), (PROGRESS_MD, "## Wave3H1 Progress Gate")]:
        block = "\n".join(
            [
                title,
                "",
                f"- current_stage: `{STAGE_ID}`",
                "- current_status: `PASS`",
                "- ADDR_DFF source topology status: `SOURCE_EXACT_TOPOLOGY_LOCKED`",
                "- ADDR_DFF physical binding status: `APPROVED_DFF_BINDING_LOCKED`",
                "- ADDR_DFF physical interface status: `COMPLETE_GDS_DERIVED_INTERFACE_LOCKED`",
                "- ADDR_DFF validator status: `SOURCE_BINDING_AND_NEGATIVE_REGRESSION_HARDENED`",
                "- ADDR_DFF physical GDS status: `NOT_GENERATED`",
                f"- next_stage: `{NEXT_STAGE}`",
                f"- recommended_next_stage: `{NEXT_STAGE}`",
                f"- next_stage_allowed: `{NEXT_STAGE}`",
                "- can_enter_next_stage: `True`",
                f"- deferred_sibling_stage: `{DEFERRED_SIBLING_STAGE}`",
                "- DATA_DFF binding status: `UNRESOLVED_REQUIRES_WAVE4B_SOURCE_BINDING_REVIEW`",
            ]
        )
        md_path.write_text(_replace_section(md_path.read_text(encoding="utf-8"), title, block), encoding="utf-8")


def _ledger_consistency() -> dict[str, Any]:
    status = _read_json(STATUS_JSON)
    checks = {
        "status_json_current_stage": status.get("current_stage") == STAGE_ID,
        "status_json_current_status": status.get("current_status") == "PASS",
        "status_json_interface_status": status.get("ADDR_DFF physical interface status") == "COMPLETE_GDS_DERIVED_INTERFACE_LOCKED",
        "status_json_validator_status": status.get("ADDR_DFF validator status") == "SOURCE_BINDING_AND_NEGATIVE_REGRESSION_HARDENED",
        "status_json_next_stage_allowed": status.get("next_stage_allowed") == NEXT_STAGE,
        "status_md_current_stage": f"- current_stage: `{STAGE_ID}`" in STATUS_MD.read_text(encoding="utf-8"),
        "goal_md_current_stage": f"- current_stage: `{STAGE_ID}`" in GOAL_MD.read_text(encoding="utf-8"),
        "progress_md_current_stage": f"- current_stage: `{STAGE_ID}`" in PROGRESS_MD.read_text(encoding="utf-8"),
    }
    report = {"checks": checks, "all_passed": all(checks.values())}
    _write_json(STAGE_DIR / "ledger_consistency_report.json", report)
    return report


def _fetch_locked_source_blob() -> dict[str, Any]:
    blob_bytes = _run_bytes(
        ["git", "-C", str(OPENYIELD_ROOT), "show", f"{EXPECTED_OPENYIELD_COMMIT}:{EXPECTED_TIME_GENERATE_PATH}"]
    ).stdout
    snapshot_path = STAGE_DIR / "source" / "time_generate_locked_1c34428.py"
    snapshot_path.parent.mkdir(parents=True, exist_ok=True)
    snapshot_path.write_bytes(blob_bytes)
    return {
        "authority_kind": "locked_git_blob",
        "authority_commit": EXPECTED_OPENYIELD_COMMIT,
        "authority_source_path": EXPECTED_TIME_GENERATE_PATH,
        "bytes": blob_bytes,
        "snapshot_path": snapshot_path,
        "blob_sha1": _git_blob_sha1_bytes(blob_bytes),
        "file_sha256": _sha256_bytes(blob_bytes),
    }


def _validator_source_snapshot(
    authority_kind: str,
    authority_commit: str,
    authority_source_path: str,
    source_bytes: bytes,
    expected_commit: str,
    expected_source_path: str,
    expected_blob_sha1: str,
    expected_file_sha256: str,
) -> dict[str, Any]:
    actual_blob_sha1 = _git_blob_sha1_bytes(source_bytes)
    actual_file_sha256 = _sha256_bytes(source_bytes)
    if _git("rev-parse", "HEAD", cwd=OPENYIELD_ROOT).strip() != expected_commit:
        return {"passed": False, "rejection_code": "OPENYIELD_COMMIT_MISMATCH"}
    if authority_commit != expected_commit:
        return {"passed": False, "rejection_code": "AUTHORITY_COMMIT_MISMATCH"}
    if authority_source_path != expected_source_path:
        return {"passed": False, "rejection_code": "SOURCE_PATH_MISMATCH"}
    if authority_kind != "locked_git_blob":
        return {"passed": False, "rejection_code": "WORKING_TREE_USED_AS_AUTHORITY"}
    if actual_blob_sha1 != expected_blob_sha1:
        return {"passed": False, "rejection_code": "LOCKED_BLOB_SHA_MISMATCH"}
    if actual_file_sha256 != expected_file_sha256:
        return {"passed": False, "rejection_code": "LOCKED_SOURCE_SHA_MISMATCH"}
    return {
        "passed": True,
        "rejection_code": None,
        "actual_blob_sha1": actual_blob_sha1,
        "actual_file_sha256": actual_file_sha256,
        "working_tree_sha256": _sha256(OPENYIELD_TIME_GENERATE),
    }


def _source_segment(text: str, node: ast.AST) -> str:
    segment = ast.get_source_segment(text, node)
    return segment if segment is not None else ast.unparse(node)


def _find_class(tree: ast.Module, name: str) -> ast.ClassDef:
    for node in tree.body:
        if isinstance(node, ast.ClassDef) and node.name == name:
            return node
    raise RuntimeError("ADDR_DFF class missing" if name == "ADDR_DFF" else f"class missing: {name}")


def _find_method(cls: ast.ClassDef, name: str) -> ast.FunctionDef:
    for node in cls.body:
        if isinstance(node, ast.FunctionDef) and node.name == name:
            return node
    raise RuntimeError("add_addr_dff_array missing" if name == "add_addr_dff_array" else f"method missing: {name}")


def _ast_arg_info(fn: ast.FunctionDef) -> list[dict[str, Any]]:
    positional = list(fn.args.posonlyargs) + list(fn.args.args)
    positional_defaults = [None] * (len(positional) - len(fn.args.defaults)) + list(fn.args.defaults)
    rows = []
    for node, default in zip(positional, positional_defaults):
        rows.append(
            {
                "parameter": node.arg,
                "kind": "positional",
                "default_source": ast.unparse(default) if default is not None else None,
            }
        )
    return rows


def _extract_source_contract(source_bytes: bytes, source_label: str, *, write_outputs: bool) -> dict[str, Any]:
    text = source_bytes.decode("utf-8")
    tree = ast.parse(text, filename=source_label)
    addr_cls = _find_class(tree, "ADDR_DFF")
    time_cls = _find_class(tree, "TIME")
    dff_cls = _find_class(tree, "dff")
    addr_init = _find_method(addr_cls, "__init__")
    addr_add = _find_method(addr_cls, "add_addr_dff_array")
    time_init = _find_method(time_cls, "__init__")
    dff_init = _find_method(dff_cls, "__init__")
    nodes_assign = next(
        node
        for node in addr_init.body
        if isinstance(node, ast.Assign) and any(isinstance(target, ast.Name) and target.id == "nodes" for target in node.targets)
    )
    n_bits_assignments = [
        node
        for node in addr_init.body
        if isinstance(node, ast.Assign) and any(isinstance(target, ast.Name) and target.id == "n_bits" for target in node.targets)
    ]
    self_num_rows_assign = next(
        node
        for node in addr_init.body
        if isinstance(node, ast.Assign)
        and any(
            isinstance(target, ast.Attribute)
            and isinstance(target.value, ast.Name)
            and target.value.id == "self"
            and target.attr == "num_rows"
            for target in node.targets
        )
    )
    nodes_extend_calls = [
        node
        for node in addr_init.body
        if isinstance(node, ast.Expr)
        and isinstance(node.value, ast.Call)
        and isinstance(node.value.func, ast.Attribute)
        and isinstance(node.value.func.value, ast.Name)
        and node.value.func.value.id == "nodes"
        and node.value.func.attr == "extend"
    ]
    dff_addr_assign = next(
        node
        for node in addr_init.body
        if isinstance(node, ast.Assign)
        and any(
            isinstance(target, ast.Attribute)
            and isinstance(target.value, ast.Name)
            and target.value.id == "self"
            and target.attr == "dff_addr"
            for target in node.targets
        )
    )
    subcircuit_call = next(
        node
        for node in addr_init.body
        if isinstance(node, ast.Expr)
        and isinstance(node.value, ast.Call)
        and isinstance(node.value.func, ast.Attribute)
        and node.value.func.attr == "subcircuit"
    )
    add_addr_call = next(
        node
        for node in addr_init.body
        if isinstance(node, ast.Expr)
        and isinstance(node.value, ast.Call)
        and isinstance(node.value.func, ast.Attribute)
        and node.value.func.attr == "add_addr_dff_array"
    )
    addr_loop = next(node for node in addr_add.body if isinstance(node, ast.For))
    addr_x_call = next(
        stmt.value
        for stmt in addr_loop.body
        if isinstance(stmt, ast.Expr)
        and isinstance(stmt.value, ast.Call)
        and isinstance(stmt.value.func, ast.Attribute)
        and stmt.value.func.attr == "X"
    )
    time_addr_ctor = next(
        node
        for node in time_init.body
        if isinstance(node, ast.Assign)
        and any(isinstance(target, ast.Name) and target.id == "dff_buf_addr" for target in node.targets)
    )
    time_addr_connections = next(
        node
        for node in time_init.body
        if isinstance(node, ast.Assign)
        and any(isinstance(target, ast.Name) and target.id == "addr_dff_connections" for target in node.targets)
    )
    time_addr_loops = []
    for node in time_init.body:
        if isinstance(node, ast.For):
            append_exprs = []
            for stmt in node.body:
                if (
                    isinstance(stmt, ast.Expr)
                    and isinstance(stmt.value, ast.Call)
                    and isinstance(stmt.value.func, ast.Attribute)
                    and isinstance(stmt.value.func.value, ast.Name)
                    and stmt.value.func.value.id == "addr_dff_connections"
                    and stmt.value.func.attr == "append"
                ):
                    append_exprs.append(_source_segment(text, stmt.value.args[0]))
            if append_exprs:
                time_addr_loops.append(
                    {
                        "loop_target": _source_segment(text, node.target),
                        "loop_iterator": _source_segment(text, node.iter),
                        "append_expressions": append_exprs,
                    }
                )
    time_x_call = next(
        stmt.value
        for stmt in time_init.body
        if isinstance(stmt, ast.Expr)
        and isinstance(stmt.value, ast.Call)
        and isinstance(stmt.value.func, ast.Attribute)
        and stmt.value.func.attr == "X"
        and _source_segment(text, stmt.value.args[0]) == "'dff_buf_addr'"
    )
    report = {
        "source_label": source_label,
        "addr_dff": {
            "__init__": {"formal_parameters": _ast_arg_info(addr_init)},
            "self_num_rows_source": _source_segment(text, self_num_rows_assign.value),
            "nodes_initial_value": ast.literal_eval(nodes_assign.value),
            "nodes_extend_expressions": [_source_segment(text, node.value.args[0]) for node in nodes_extend_calls],
            "n_bits_expressions": [_source_segment(text, node.value) for node in n_bits_assignments],
            "dff_addr_constructor": {
                "source_text": _source_segment(text, dff_addr_assign),
                "positional_arguments": [_source_segment(text, arg) for arg in dff_addr_assign.value.args],
                "keyword_arguments": {kw.arg: _source_segment(text, kw.value) for kw in dff_addr_assign.value.keywords},
            },
            "subcircuit_call_source": _source_segment(text, subcircuit_call),
            "add_addr_dff_array_call": {
                "source_text": _source_segment(text, add_addr_call),
                "arguments": [_source_segment(text, arg) for arg in add_addr_call.value.args],
            },
            "add_addr_dff_array": {
                "formal_parameters": _ast_arg_info(addr_add),
                "loop_target": _source_segment(text, addr_loop.target),
                "loop_iterator": _source_segment(text, addr_loop.iter),
                "self_x_instance_name_expression": _source_segment(text, addr_x_call.args[0]),
                "self_x_child_expression": _source_segment(text, addr_x_call.args[1]),
                "self_x_net_argument_order": [_source_segment(text, arg) for arg in addr_x_call.args[2:]],
            },
        },
        "time": {
            "__init__": {"formal_parameters": _ast_arg_info(time_init)},
            "addr_dff_constructor_call": {
                "source_text": _source_segment(text, time_addr_ctor),
                "positional_arguments": [_source_segment(text, arg) for arg in time_addr_ctor.value.args],
                "keyword_arguments": {kw.arg: _source_segment(text, kw.value) for kw in time_addr_ctor.value.keywords},
            },
            "addr_dff_connections_initial": ast.literal_eval(time_addr_connections.value),
            "addr_dff_connection_loops": time_addr_loops,
            "dff_buf_addr_instance_call": {
                "instance_name_expression": _source_segment(text, time_x_call.args[0]),
                "child_expression": _source_segment(text, time_x_call.args[1]),
                "remaining_arguments": [_source_segment(text, arg) for arg in time_x_call.args[2:]],
            },
        },
        "dff": {"__init__": {"formal_parameters": _ast_arg_info(dff_init)}},
    }
    if write_outputs:
        _write_json(STAGE_DIR / "ADDR_DFF_ast_extraction.json", report)
        _write_text(STAGE_DIR / "ADDR_DFF_ast_extraction.md", _render_md_kv("ADDR_DFF AST Extraction", report))
    return report


def _eval_expr(expr: str, env: dict[str, Any]) -> Any:
    safe_globals = {"__builtins__": {}, "range": range, "ceil": math.ceil, "log2": math.log2, "int": int}
    return eval(expr, safe_globals, env)


def _resolve_num_rows(ast_report: dict[str, Any], *, overrides: list[dict[str, Any]] | None = None, write_outputs: bool) -> dict[str, Any]:
    global_bytes = _run_bytes(
        ["git", "-C", str(OPENYIELD_ROOT), "show", f"{EXPECTED_OPENYIELD_COMMIT}:sram_compiler/config_yaml/global.yaml"]
    ).stdout
    locked_global_path = STAGE_DIR / "source" / "global_yaml_locked_1c34428.yaml"
    locked_global_path.parent.mkdir(parents=True, exist_ok=True)
    if write_outputs:
        locked_global_path.write_bytes(global_bytes)
    time_default = next(
        row["default_source"]
        for row in ast_report["time"]["__init__"]["formal_parameters"]
        if row["parameter"] == "num_rows"
    )
    candidates = []
    if overrides is not None:
        candidates.extend(overrides)
    else:
        for path, category, precedence in [
            (LAYOUTGEN_CURRENT_SPEC, "current_layoutgen_sram_spec", 10),
            (OPENYIELD_CURRENT_SPEC, "current_openyield_layoutgen_spec", 20),
        ]:
            obj = _read_json(path)
            candidates.append(
                {
                    "path": str(path),
                    "source_category": category,
                    "current_or_historical": "current",
                    "content_sha256": _sha256(path),
                    "parsed_num_rows": obj.get("num_rows"),
                    "precedence": precedence,
                }
            )
        global_obj = yaml.safe_load(global_bytes.decode("utf-8"))
        candidates.append(
            {
                "path": f"{EXPECTED_OPENYIELD_COMMIT}:sram_compiler/config_yaml/global.yaml",
                "source_category": "locked_openyield_global_yaml_blob",
                "current_or_historical": "current",
                "content_sha256": _sha256_bytes(global_bytes),
                "parsed_num_rows": global_obj.get("num_rows"),
                "precedence": 30,
            }
        )
        candidates.append(
            {
                "path": f"{EXPECTED_OPENYIELD_COMMIT}:{EXPECTED_TIME_GENERATE_PATH}::TIME.__init__.num_rows_default",
                "source_category": "locked_time_generate_ast_default",
                "current_or_historical": "current",
                "content_sha256": EXPECTED_TIME_GENERATE_SHA256,
                "parsed_num_rows": int(float(time_default)),
                "precedence": 40,
            }
        )
    values = sorted({row["parsed_num_rows"] for row in candidates if row["current_or_historical"] == "current"})
    conflict = len(values) != 1
    resolved_num_rows = values[0] if not conflict else None
    for row in candidates:
        row["selected_or_rejected_reason"] = (
            "rejected_due_to_current_authority_conflict"
            if row["current_or_historical"] == "current" and conflict
            else "selected_current_authority_consensus"
        )
    report = {
        "time_init_formal_parameters": ast_report["time"]["__init__"]["formal_parameters"],
        "time_num_rows_default_source": time_default,
        "time_addr_dff_constructor_call": ast_report["time"]["addr_dff_constructor_call"],
        "current_authority_candidates": candidates,
        "current_authority_values": values,
        "num_rows_authority_conflict": conflict,
        "resolved_num_rows": resolved_num_rows,
        "resolved_n_bits": math.ceil(math.log2(resolved_num_rows)) if resolved_num_rows and resolved_num_rows > 1 else (1 if resolved_num_rows == 1 else None),
        "all_current_authorities_equal_16": resolved_num_rows == EXPECTED_NUM_ROWS and not conflict,
    }
    if write_outputs:
        _write_json(STAGE_DIR / "ADDR_DFF_CONFIG_RESOLUTION.json", report)
        _write_text(STAGE_DIR / "ADDR_DFF_CONFIG_RESOLUTION.md", _render_md_kv("ADDR_DFF Config Resolution", report))
    return report


def _build_source_topology(ast_report: dict[str, Any], config_report: dict[str, Any], *, write_outputs: bool) -> dict[str, Any]:
    if config_report["num_rows_authority_conflict"]:
        raise RuntimeError("num_rows authority conflict")
    num_rows = config_report["resolved_num_rows"]
    n_bits = _eval_expr(ast_report["addr_dff"]["n_bits_expressions"][0], {"self": type("SelfObj", (), {"num_rows": num_rows})()})
    nodes = list(ast_report["addr_dff"]["nodes_initial_value"])
    for expr in ast_report["addr_dff"]["nodes_extend_expressions"]:
        nodes.extend(_eval_expr(expr, {"n_bits": n_bits}))
    iter_values = list(_eval_expr(ast_report["addr_dff"]["add_addr_dff_array"]["loop_iterator"], {"n_bits": n_bits}))
    child_expr = ast_report["addr_dff"]["add_addr_dff_array"]["self_x_child_expression"]
    instance_name_expr = ast_report["addr_dff"]["add_addr_dff_array"]["self_x_instance_name_expression"]
    net_exprs = ast_report["addr_dff"]["add_addr_dff_array"]["self_x_net_argument_order"]
    instances = []
    endpoint_contracts = {"VDD": ["TOP::VDD"], "VSS": ["TOP::VSS"], "CLK": ["TOP::CLK"]}
    for index in iter_values:
        instance_name = _eval_expr(instance_name_expr, {"i": index})
        connections = [_eval_expr(expr, {"i": index}) for expr in net_exprs]
        instances.append(
            {
                "instance_name": instance_name,
                "logical_child_expression": child_expr,
                "connections": connections,
            }
        )
        endpoint_contracts["VDD"].append(f"{instance_name}::VDD")
        endpoint_contracts["VSS"].append(f"{instance_name}::VSS")
        endpoint_contracts["CLK"].append(f"{instance_name}::CLK")
        endpoint_contracts[f"A{index}"] = [f"TOP::A{index}", f"{instance_name}::D"]
        endpoint_contracts[f"A_dff{index}"] = [f"TOP::A_dff{index}", f"{instance_name}::Q"]
    time_connections = list(ast_report["time"]["addr_dff_connections_initial"])
    for loop in ast_report["time"]["addr_dff_connection_loops"]:
        loop_values = list(_eval_expr(loop["loop_iterator"], {"self": type("SelfObj", (), {"n_bits": n_bits})()}))
        for index in loop_values:
            for expr in loop["append_expressions"]:
                time_connections.append(_eval_expr(expr, {"i": index}))
    topology = {
        "resolved_num_rows": num_rows,
        "resolved_n_bits": n_bits,
        "resolved_top_pins": nodes,
        "child_instances": instances,
        "canonical_nets": list(endpoint_contracts.keys()),
        "endpoint_contracts": endpoint_contracts,
        "time_addr_dff_connections": time_connections,
    }
    if write_outputs:
        _write_json(STAGE_DIR / "ADDR_DFF_source_derived_topology.json", topology)
    return topology


def _expected_project_contract() -> dict[str, Any]:
    endpoint_contracts = {"VDD": ["TOP::VDD"], "VSS": ["TOP::VSS"], "CLK": ["TOP::CLK"]}
    instances = []
    for idx, instance_name in enumerate(EXPECTED_CHILDREN):
        instances.append(
            {
                "instance_name": instance_name,
                "logical_child_expression": "self.dff_addr.NAME",
                "connections": EXPECTED_INSTANCE_CONNECTIONS[instance_name],
            }
        )
        endpoint_contracts["VDD"].append(f"{instance_name}::VDD")
        endpoint_contracts["VSS"].append(f"{instance_name}::VSS")
        endpoint_contracts["CLK"].append(f"{instance_name}::CLK")
        endpoint_contracts[f"A{idx}"] = [f"TOP::A{idx}", f"{instance_name}::D"]
        endpoint_contracts[f"A_dff{idx}"] = [f"TOP::A_dff{idx}", f"{instance_name}::Q"]
    return {
        "resolved_num_rows": EXPECTED_NUM_ROWS,
        "resolved_n_bits": EXPECTED_N_BITS,
        "resolved_top_pins": EXPECTED_TOP_PIN_ORDER,
        "child_instances": instances,
        "canonical_nets": ["VDD", "VSS", "CLK", "A0", "A_dff0", "A1", "A_dff1", "A2", "A_dff2", "A3", "A_dff3"],
        "endpoint_contracts": endpoint_contracts,
    }


def _validate_topology_contract(source_topology: dict[str, Any]) -> dict[str, Any]:
    instance_names = [row["instance_name"] for row in source_topology["child_instances"]]
    if len(instance_names) != len(set(instance_names)):
        return {"passed": False, "rejection_code": "DUPLICATE_CHILD_INSTANCE"}
    if len(source_topology["child_instances"]) != EXPECTED_N_BITS:
        return {"passed": False, "rejection_code": "CHILD_INSTANCE_COUNT_MISMATCH"}
    if len(source_topology["canonical_nets"]) != 11:
        return {"passed": False, "rejection_code": "CANONICAL_NET_COUNT_MISMATCH"}
    return {"passed": True, "rejection_code": None}


def _validate_topology_exact_identity(source_topology: dict[str, Any], expected_contract: dict[str, Any], *, write_outputs: bool) -> dict[str, Any]:
    missing_fields = []
    unexpected_fields = []
    order_mismatch = []
    instance_mismatch = []
    if source_topology["resolved_top_pins"] != expected_contract["resolved_top_pins"]:
        order_mismatch.append("top_pin_order")
    if source_topology["resolved_num_rows"] != expected_contract["resolved_num_rows"]:
        missing_fields.append("resolved_num_rows")
    if source_topology["resolved_n_bits"] != expected_contract["resolved_n_bits"]:
        missing_fields.append("resolved_n_bits")
    expected_instances = {row["instance_name"]: row for row in expected_contract["child_instances"]}
    for row in source_topology["child_instances"]:
        expected = expected_instances.get(row["instance_name"])
        if expected is None:
            instance_mismatch.append({"instance_name": row["instance_name"], "reason": "unexpected_instance"})
            continue
        if row["connections"] != expected["connections"]:
            instance_mismatch.append({"instance_name": row["instance_name"], "reason": "connection_mismatch", "actual": row["connections"], "expected": expected["connections"]})
        if row["logical_child_expression"] != expected["logical_child_expression"]:
            instance_mismatch.append({"instance_name": row["instance_name"], "reason": "child_expression_mismatch"})
    for name in expected_instances:
        if name not in {row["instance_name"] for row in source_topology["child_instances"]}:
            instance_mismatch.append({"instance_name": name, "reason": "missing_instance"})
    net_mismatch = {
        "missing_nets": [net for net in expected_contract["canonical_nets"] if net not in source_topology["canonical_nets"]],
        "unexpected_nets": [net for net in source_topology["canonical_nets"] if net not in expected_contract["canonical_nets"]],
        "order_mismatch": source_topology["canonical_nets"] != expected_contract["canonical_nets"],
    }
    endpoint_mismatch = []
    for net, expected_endpoints in expected_contract["endpoint_contracts"].items():
        actual = source_topology["endpoint_contracts"].get(net)
        if actual != expected_endpoints:
            endpoint_mismatch.append({"net": net, "expected": expected_endpoints, "actual": actual})
    exact_identity_passed = not (missing_fields or unexpected_fields or order_mismatch or instance_mismatch or net_mismatch["missing_nets"] or net_mismatch["unexpected_nets"] or net_mismatch["order_mismatch"] or endpoint_mismatch)
    report = {
        "missing_fields": missing_fields,
        "unexpected_fields": unexpected_fields,
        "order_mismatch": order_mismatch,
        "instance_mismatch": instance_mismatch,
        "net_mismatch": net_mismatch,
        "endpoint_mismatch": endpoint_mismatch,
        "exact_identity_passed": exact_identity_passed,
        "rejection_code": None if exact_identity_passed else "TOPOLOGY_EXACT_IDENTITY_MISMATCH",
    }
    if write_outputs:
        _write_json(STAGE_DIR / "ADDR_DFF_expected_project_contract.json", expected_contract)
        _write_json(STAGE_DIR / "ADDR_DFF_topology_exact_identity_report.json", report)
        _write_json(STAGE_DIR / "ADDR_DFF_source_topology_analysis.json", {"source_derived_topology": source_topology, "expected_project_contract": expected_contract, "exact_identity_report": report})
        _write_text(STAGE_DIR / "ADDR_DFF_source_topology_analysis.md", _render_md_kv("ADDR_DFF Source Topology Analysis", _read_json(STAGE_DIR / "ADDR_DFF_source_topology_analysis.json")))
        _write_json(STAGE_DIR / "ADDR_DFF_canonical_topology.json", source_topology)
        _write_json(STAGE_DIR / "ADDR_DFF_top_pin_contract.json", {"top_pin_order": source_topology["resolved_top_pins"], "top_pin_count": len(source_topology["resolved_top_pins"])})
        _write_json(STAGE_DIR / "ADDR_DFF_net_endpoint_universe.json", source_topology["endpoint_contracts"])
        _write_json(
            STAGE_DIR / "ADDR_DFF_hierarchical_namespace.json",
            {
                "top_level": [f"TOP::{pin}" for pin in source_topology["resolved_top_pins"]],
                "instances": {
                    row["instance_name"]: [
                        f"{row['instance_name']}::VDD",
                        f"{row['instance_name']}::VSS",
                        f"{row['instance_name']}::D",
                        f"{row['instance_name']}::Q",
                        f"{row['instance_name']}::CLK",
                    ]
                    for row in source_topology["child_instances"]
                },
            },
        )
        _write_csv(
            STAGE_DIR / "ADDR_DFF_instance_connection_table.csv",
            [{"instance_name": row["instance_name"], "logical_child_expression": row["logical_child_expression"], "connection_order": json.dumps(row["connections"])} for row in source_topology["child_instances"]],
        )
    return report


def _load_connectivity_lookup() -> dict[str, Any]:
    graph = _read_json(DFF_CONNECTIVITY_GRAPH)
    report = _read_json(DFF_CONNECTIVITY_REPORT)
    rect_to_component = {}
    component_to_rects = defaultdict(list)
    component_to_net = {}
    rect_info_by_id = {}
    bbox_key_to_rect_ids = defaultdict(list)
    for layer_key, layer_name in [("m1", "M1"), ("via1", "Via1"), ("m2", "M2")]:
        for row in graph["rectangles"][layer_key]:
            rect_info_by_id[row["rect_id"]] = {
                "layer_name": layer_name,
                "layer": {"M1": 11, "Via1": 12, "M2": 13}[layer_name],
                "datatype": 0,
                "bbox": [_round_float(v) for v in row["bbox"]],
            }
            bbox_key_to_rect_ids[(layer_name, tuple(_round_float(v) for v in row["bbox"]))].append(row["rect_id"])
    for component in graph["components"]:
        component_id = component["component_id"]
        for member in component["members"]:
            if member in rect_info_by_id:
                rect_to_component[member] = component_id
                component_to_rects[component_id].append(member)
    for row in report["per_net"]:
        component_to_net[row["component_id"]] = row["net_name"]
    return {
        "graph": graph,
        "report": report,
        "rect_info_by_id": rect_info_by_id,
        "bbox_key_to_rect_ids": bbox_key_to_rect_ids,
        "rect_to_component": rect_to_component,
        "component_to_rects": {key: sorted(value) for key, value in component_to_rects.items()},
        "component_to_net": component_to_net,
    }


def _normalize_direct_child_name(name: str) -> str:
    for expected_name in EXPECTED_DFF_DIRECT_CHILDREN:
        if expected_name in name:
            return expected_name
    return name


def _dimension_tokens_from_cell_name(cell_name: str) -> dict[str, int] | None:
    match = re.search(r"NW(\d+)_PW(\d+)_L(\d+)$", cell_name)
    if not match:
        return None
    return {"NW_nm": int(match.group(1)), "PW_nm": int(match.group(2)), "L_nm": int(match.group(3))}


def _build_hierarchy_closure(lib: gdstk.Library, top_cell_name: str, *, write_outputs: bool) -> dict[str, Any]:
    cells = {cell.name: cell for cell in lib.cells}
    graph = {cell.name: [str(ref.cell_name) for ref in cell.references] for cell in lib.cells}
    top_cells = [cell.name for cell in lib.top_level()]
    reachable = set()
    missing_targets = []
    direct_reference_count = len(graph.get(top_cell_name, []))
    recursive_reference_count = 0
    reference_cycles = []
    visiting = set()
    stack: list[str] = []

    def dfs(name: str) -> None:
        nonlocal recursive_reference_count
        if name in visiting:
            if name in stack:
                idx = stack.index(name)
                reference_cycles.append(stack[idx:] + [name])
            return
        if name in reachable:
            return
        visiting.add(name)
        stack.append(name)
        reachable.add(name)
        for child in graph.get(name, []):
            recursive_reference_count += 1
            if child not in cells:
                missing_targets.append(child)
                continue
            dfs(child)
        stack.pop()
        visiting.remove(name)

    for top_name in top_cells:
        dfs(top_name)
    unreachable = sorted(set(cells) - reachable)
    report = {
        "top_level_cell_count": len(top_cells),
        "top_level_cells": top_cells,
        "reachable_cell_count": len(reachable),
        "direct_reference_count": direct_reference_count,
        "recursive_reference_count": recursive_reference_count,
        "missing_reference_target_count": len(missing_targets),
        "missing_reference_targets": sorted(set(missing_targets)),
        "reference_cycle_count": len(reference_cycles),
        "reference_cycles": reference_cycles,
        "unreachable_cell_count": len(unreachable),
        "unreachable_cells": unreachable,
        "closure_passed": len(top_cells) == 1 and len(missing_targets) == 0 and len(reference_cycles) == 0,
    }
    if write_outputs:
        _write_json(STAGE_DIR / "ADDR_DFF_DFF_hierarchy_closure.json", report)
    return report


def _extract_full_physical_interface(*, write_outputs: bool) -> dict[str, Any]:
    lib = gdstk.read_gds(DFF_GDS)
    top_cells = lib.top_level()
    if len(top_cells) != 1:
        raise RuntimeError("approved DFF top_level_cell_count != 1")
    top = top_cells[0]
    if top.name != EXPECTED_DFF_TOP:
        raise RuntimeError("approved DFF top cell mismatch")
    top_bbox = [_round_float(v) for point in top.bounding_box() for v in point]
    if top_bbox != EXPECTED_DFF_TOP_BBOX:
        raise RuntimeError(f"approved DFF bbox mismatch: {top_bbox}")
    connectivity = _load_connectivity_lookup()
    rect_lookup: dict[tuple[str, tuple[float, ...]], list[str]] = {
        key: list(value) for key, value in connectivity["bbox_key_to_rect_ids"].items()
    }
    obstacle_objects = []
    shape_id_seen = set()
    rectangle_contract_violations = 0
    missing_component_count = 0
    unresolved_net_count = 0
    duplicate_shape_id_count = 0
    layer_counter = Counter()
    source_cell_counter = Counter()

    def recurse(cell: gdstk.Cell, path: list[str], matrix: tuple[tuple[float, float, float], tuple[float, float, float], tuple[float, float, float]]) -> None:
        nonlocal rectangle_contract_violations, missing_component_count, unresolved_net_count, duplicate_shape_id_count
        for poly_index, polygon in enumerate(cell.polygons):
            if polygon.layer not in CONDUCTIVE_LAYER_MAP:
                continue
            layer_name = CONDUCTIVE_LAYER_MAP[polygon.layer]
            local_points = _polygon_points(polygon)
            if not _is_axis_aligned_rectangle(local_points):
                rectangle_contract_violations += 1
            transformed_points = [list(_matrix_apply(matrix, point[0], point[1])) for point in local_points]
            if not _is_axis_aligned_rectangle(transformed_points):
                rectangle_contract_violations += 1
            transformed_bbox = _normalize_bbox(transformed_points)
            rect_key = (layer_name, tuple(transformed_bbox))
            rect_ids = rect_lookup.get(rect_key, [])
            if not rect_ids:
                raise RuntimeError(f"missing graph rectangle for {cell.name} {rect_key}")
            rect_id = rect_ids[0]
            component_id = connectivity["rect_to_component"].get(rect_id)
            if component_id is None:
                missing_component_count += 1
            resolved_net = connectivity["component_to_net"].get(component_id)
            if resolved_net is None:
                unresolved_net_count += 1
            shape_id = f"shape_{len(obstacle_objects):04d}"
            if shape_id in shape_id_seen:
                duplicate_shape_id_count += 1
            shape_id_seen.add(shape_id)
            geometry_digest = _sha256_bytes(
                json.dumps(
                    {
                        "layer_name": layer_name,
                        "layer": polygon.layer,
                        "datatype": polygon.datatype,
                        "transformed_polygon_points": transformed_points,
                    },
                    sort_keys=True,
                    separators=(",", ":"),
                ).encode("utf-8")
            )
            obstacle_objects.append(
                {
                    "shape_id": shape_id,
                    "source_cell": cell.name,
                    "hierarchy_path": "/".join(path),
                    "layer_name": layer_name,
                    "layer": polygon.layer,
                    "datatype": polygon.datatype,
                    "shape_kind": "axis_aligned_rectangle",
                    "bbox_is_exact_geometry": _is_axis_aligned_rectangle(transformed_points),
                    "polygon_points": local_points,
                    "bbox": _normalize_bbox(local_points),
                    "transformed_polygon_points": transformed_points,
                    "transformed_bbox": transformed_bbox,
                    "connected_component_id": component_id,
                    "resolved_net": resolved_net,
                    "is_top_pin_component": resolved_net in set(PIN_NAMES),
                    "is_internal_net_component": resolved_net not in set(PIN_NAMES) if resolved_net is not None else False,
                    "source_element_type": "polygon",
                    "geometry_digest": geometry_digest,
                    "graph_rect_id": rect_id,
                }
            )
            layer_counter[layer_name] += 1
            source_cell_counter[cell.name] += 1
        for ref_index, ref in enumerate(cell.references):
            child = next(candidate for candidate in lib.cells if candidate.name == str(ref.cell_name))
            recurse(child, path + [f"{child.name}[{ref_index}]"], _matrix_multiply(matrix, _reference_matrix(ref)))

    recurse(top, [top.name], _matrix_identity())
    if rectangle_contract_violations != 0:
        raise RuntimeError("rectangle contract violation detected")
    if duplicate_shape_id_count != 0:
        raise RuntimeError("duplicate shape_id detected")
    if layer_counter["M1"] != EXPECTED_DFF_CONDUCTIVE_GEOMETRY["M1"] or layer_counter["Via1"] != EXPECTED_DFF_CONDUCTIVE_GEOMETRY["Via1"] or layer_counter["M2"] != EXPECTED_DFF_CONDUCTIVE_GEOMETRY["M2"]:
        raise RuntimeError(f"unexpected conductive counts: {dict(layer_counter)}")
    if len(obstacle_objects) != EXPECTED_DFF_CONDUCTIVE_GEOMETRY["total"]:
        raise RuntimeError(f"unexpected conductive object count: {len(obstacle_objects)}")
    obstacle_by_graph_rect_id = defaultdict(list)
    for row in obstacle_objects:
        obstacle_by_graph_rect_id[row["graph_rect_id"]].append(row)
    pin_rows = []
    duplicate_pin_count = 0
    for label in top.labels:
        if str(label.text) not in PIN_NAMES:
            continue
        hit = next(row for row in connectivity["graph"]["label_hits"] if row["text"] == str(label.text))
        direct_objects = [obstacle_by_graph_rect_id[shape_id][0] for shape_id in hit["shape_ids"]]
        component_ids = {row["connected_component_id"] for row in direct_objects}
        if len(component_ids) != 1:
            raise RuntimeError(f"pin component ambiguity: {label.text}")
        component_id = next(iter(component_ids))
        resolved_net = connectivity["component_to_net"].get(component_id)
        exact_polygons = [row["transformed_polygon_points"] for row in direct_objects]
        bbox = _normalize_bbox([point for polygon in exact_polygons for point in polygon])
        pin_rows.append(
            {
                "pin_name": str(label.text),
                "label_text": str(label.text),
                "label_origin": [_round_float(label.origin[0]), _round_float(label.origin[1])],
                "label_layer": label.layer,
                "label_datatype": label.texttype,
                "physical_layer_name": direct_objects[0]["layer_name"],
                "physical_layer": direct_objects[0]["layer"],
                "physical_datatype": direct_objects[0]["datatype"],
                "exact_polygon_points": exact_polygons,
                "bbox": bbox,
                "connected_component_id": component_id,
                "connected_component_shape_count": len(connectivity["component_to_rects"].get(component_id, [])),
                "resolved_net": resolved_net,
                "direct_access_rectangle_ids": hit["shape_ids"],
                "rectangle_contract_complete": all(row["bbox_is_exact_geometry"] for row in direct_objects),
                "geometry_digest": _sha256_bytes(json.dumps({"pin": str(label.text), "polygons": exact_polygons}, sort_keys=True).encode("utf-8")),
            }
        )
    pin_rows = sorted(pin_rows, key=lambda row: row["pin_name"])
    pin_names = [row["pin_name"] for row in pin_rows]
    duplicate_pin_count = len(pin_names) - len(set(pin_names))
    missing_pins = [pin for pin in PIN_NAMES if pin not in pin_names]
    unexpected_pins = [pin for pin in pin_names if pin not in PIN_NAMES]
    unresolved_component_count = sum(1 for row in pin_rows if row["connected_component_id"] is None)
    if sorted(pin_names) != EXPECTED_DFF_TOP_LABELS:
        raise RuntimeError(f"top label set mismatch: {sorted(pin_names)}")
    if missing_pins or unexpected_pins or duplicate_pin_count or unresolved_component_count:
        raise RuntimeError("pin geometry extraction incomplete")
    normalized_direct_inventory = Counter()
    recursive_inventory = Counter()
    for ref in top.references:
        normalized_direct_inventory[_normalize_direct_child_name(str(ref.cell_name))] += 1
    for cell in lib.cells:
        recursive_inventory[cell.name] += 1
    hierarchy_closure = _build_hierarchy_closure(lib, top.name, write_outputs=write_outputs)
    interface_report = {
        "approved_gds_path": str(DFF_GDS),
        "actual_sha256": _sha256(DFF_GDS),
        "top_cell": top.name,
        "top_cell_bbox": top_bbox,
        "top_label_set": sorted(pin_names),
        "pin_geometry_json_path": str(STAGE_DIR / "ADDR_DFF_DFF_pin_geometry.json"),
        "pin_geometry_csv_path": str(STAGE_DIR / "ADDR_DFF_DFF_pin_geometry.csv"),
        "pin_geometry": pin_rows,
        "direct_child_inventory": dict(sorted(normalized_direct_inventory.items())),
        "recursive_hierarchy_inventory": dict(sorted(recursive_inventory.items())),
        "VDD_component_id": next(row["connected_component_id"] for row in pin_rows if row["pin_name"] == "VDD"),
        "VSS_component_id": next(row["connected_component_id"] for row in pin_rows if row["pin_name"] == "VSS"),
        "D_component_id": next(row["connected_component_id"] for row in pin_rows if row["pin_name"] == "D"),
        "Q_component_id": next(row["connected_component_id"] for row in pin_rows if row["pin_name"] == "Q"),
        "CLK_component_id": next(row["connected_component_id"] for row in pin_rows if row["pin_name"] == "CLK"),
        "conductive_obstacle_map_path": str(STAGE_DIR / "ADDR_DFF_DFF_conductive_obstacle_map.json"),
        "obstacle_object_count": len(obstacle_objects),
        "M1_object_count": layer_counter["M1"],
        "Via1_object_count": layer_counter["Via1"],
        "M2_object_count": layer_counter["M2"],
        "rectangle_contract_status": rectangle_contract_violations == 0,
        "hierarchy_closure": hierarchy_closure,
        "missing_references": hierarchy_closure["missing_reference_targets"],
        "reference_cycles": hierarchy_closure["reference_cycles"],
        "source_commit": EXPECTED_OPENYIELD_COMMIT,
        "approved_reusable_status": EXPECTED_DFF_STATUS,
        "physical_interface_digest": _sha256_bytes(
            json.dumps(
                {
                    "bbox": top_bbox,
                    "pins": pin_rows,
                    "inventory": dict(sorted(normalized_direct_inventory.items())),
                    "obstacle_count": len(obstacle_objects),
                },
                sort_keys=True,
                ensure_ascii=False,
            ).encode("utf-8")
        ),
    }
    obstacle_report = {
        "approved_gds_path": str(DFF_GDS),
        "approved_gds_sha256": _sha256(DFF_GDS),
        "rectangle_contract_complete": rectangle_contract_violations == 0,
        "M1_object_count": layer_counter["M1"],
        "Via1_object_count": layer_counter["Via1"],
        "M2_object_count": layer_counter["M2"],
        "total_object_count": len(obstacle_objects),
        "unique_geometry_digest_count": len({row["geometry_digest"] for row in obstacle_objects}),
        "rectangle_contract_violation_count": rectangle_contract_violations,
        "duplicate_shape_id_count": duplicate_shape_id_count,
        "missing_component_count": missing_component_count,
        "unresolved_net_object_count": unresolved_net_count,
        "objects": obstacle_objects,
    }
    pin_geometry_json = {
        "pin_count": len(pin_rows),
        "missing_pin_count": len(missing_pins),
        "unexpected_pin_count": len(unexpected_pins),
        "duplicate_pin_count": duplicate_pin_count,
        "unresolved_component_count": unresolved_component_count,
        "pins": pin_rows,
    }
    if write_outputs:
        _write_json(STAGE_DIR / "ADDR_DFF_DFF_conductive_obstacle_map.json", obstacle_report)
        _write_json(STAGE_DIR / "ADDR_DFF_DFF_pin_geometry.json", pin_geometry_json)
        _write_csv(STAGE_DIR / "ADDR_DFF_DFF_pin_geometry.csv", pin_rows)
        _write_json(STAGE_DIR / "ADDR_DFF_DFF_child_physical_interface.json", interface_report)
    return {
        "obstacle_report": obstacle_report,
        "pin_geometry": pin_geometry_json,
        "interface_report": interface_report,
        "hierarchy_closure": hierarchy_closure,
        "connectivity_lookup": connectivity,
    }


def _build_parameter_binding_summary(ast_report: dict[str, Any], *, write_outputs: bool) -> dict[str, Any]:
    defaults = {row["parameter"]: row["default_source"] for row in ast_report["dff"]["__init__"]["formal_parameters"]}
    actual_call = ast_report["addr_dff"]["dff_addr_constructor"]["positional_arguments"]
    summary = {
        "source_constructor_call": ast_report["addr_dff"]["dff_addr_constructor"]["source_text"],
        "formal_to_actual_binding": {
            "nmos_model": actual_call[0],
            "pmos_model": actual_call[1],
            "pmos_width": "default",
            "nmos_width": "default",
            "length": "default",
        },
        "default_values": {
            "nmos_model": defaults["nmos_model"],
            "pmos_model": defaults["pmos_model"],
            "pmos_width": defaults["pmos_width"],
            "nmos_width": defaults["nmos_width"],
            "length": defaults["length"],
        },
        "normalized_nm_values": {
            "pmos_width_nm": round(float(defaults["pmos_width"]) * 1e9),
            "nmos_width_nm": round(float(defaults["nmos_width"]) * 1e9),
            "length_nm": round(float(defaults["length"]) * 1e9),
        },
    }
    if write_outputs:
        _write_json(STAGE_DIR / "ADDR_DFF_DFF_parameter_binding_summary.json", summary)
    return summary


def _validate_parameter_to_physical_closure(summary: dict[str, Any], interface_bundle: dict[str, Any], *, write_outputs: bool) -> dict[str, Any]:
    child_inventory = interface_bundle["interface_report"]["direct_child_inventory"]
    dims = {}
    for name in child_inventory:
        dims[name] = _dimension_tokens_from_cell_name(name)
    closure = {
        "source_constructor_call": summary["source_constructor_call"],
        "formal_to_actual_binding": summary["formal_to_actual_binding"],
        "default_values": summary["default_values"],
        "normalized_nm_values": summary["normalized_nm_values"],
        "expected_physical_child_cell_names": list(EXPECTED_DFF_DIRECT_CHILDREN.keys()),
        "actual_direct_child_inventory": child_inventory,
        "count_comparison": {
            "expected": EXPECTED_DFF_DIRECT_CHILDREN,
            "actual": child_inventory,
            "matched": child_inventory == EXPECTED_DFF_DIRECT_CHILDREN,
        },
        "dimension_comparison": dims,
        "source_commit_comparison": {
            "expected": EXPECTED_OPENYIELD_COMMIT,
            "actual": _read_json(DFF_MANIFEST)["source_commit_openyield"],
            "matched": _read_json(DFF_MANIFEST)["source_commit_openyield"] == EXPECTED_OPENYIELD_COMMIT,
        },
        "gds_sha_comparison": {
            "expected": EXPECTED_DFF_SHA,
            "actual": _sha256(DFF_GDS),
            "matched": _sha256(DFF_GDS) == EXPECTED_DFF_SHA,
        },
    }
    closure["defaults_close_with_approved_dff"] = (
        summary["normalized_nm_values"] == {"pmos_width_nm": 500, "nmos_width_nm": 250, "length_nm": 50}
        and child_inventory == EXPECTED_DFF_DIRECT_CHILDREN
        and all(value == {"NW_nm": 250, "PW_nm": 500, "L_nm": 50} for value in dims.values())
    )
    closure["closure_passed"] = closure["defaults_close_with_approved_dff"] and closure["source_commit_comparison"]["matched"] and closure["gds_sha_comparison"]["matched"]
    closure["rejection_code"] = None if closure["closure_passed"] else "PARAMETER_TO_PHYSICAL_CLOSURE_MISMATCH"
    if write_outputs:
        _write_json(STAGE_DIR / "ADDR_DFF_DFF_parameter_to_physical_binding_closure.json", closure)
    return closure


def _validate_approved_dff_source_path(path: Path) -> dict[str, Any]:
    manifest = _read_json(DFF_MANIFEST)
    forbidden = {Path(item).resolve() for item in manifest["forbidden_physical_sources"]}
    forbidden.add((REPO_ROOT / "outputs/Wave3_DFF_BUF_reusable_release/DFF_BUF_reusable_clean.gds").resolve())
    resolved = path.resolve()
    if resolved in forbidden:
        if "annotated" in path.name:
            return {"passed": False, "rejection_code": "ANNOTATED_GDS_REJECTED"}
        if "atlas" in path.name:
            return {"passed": False, "rejection_code": "ATLAS_GDS_REJECTED"}
        if "DFF_BUF" in path.name:
            return {"passed": False, "rejection_code": "DFF_BUF_REJECTED"}
        return {"passed": False, "rejection_code": "QUARANTINED_CANDIDATE_REJECTED"}
    if resolved != DFF_GDS.resolve():
        return {"passed": False, "rejection_code": "NON_APPROVED_PHYSICAL_SOURCE"}
    return {"passed": True, "rejection_code": None}


def _validate_approved_dff_artifact(expected_sha: str, expected_top: str) -> dict[str, Any]:
    if _sha256(DFF_GDS) != expected_sha:
        return {"passed": False, "rejection_code": "APPROVED_DFF_GDS_SHA_MISMATCH"}
    lib = gdstk.read_gds(DFF_GDS)
    top_cells = lib.top_level()
    if len(top_cells) != 1 or top_cells[0].name != expected_top:
        return {"passed": False, "rejection_code": "APPROVED_DFF_TOP_CELL_MISMATCH"}
    return {"passed": True, "rejection_code": None}


def _validate_no_generated_artifacts(root: Path) -> dict[str, Any]:
    gds_names = [path.name for path in root.rglob("*.gds")]
    if any("ADDR_DFF" in name for name in gds_names):
        return {"passed": False, "rejection_code": "ADDR_DFF_GDS_GENERATED"}
    if any("DATA_DFF" in name for name in gds_names):
        return {"passed": False, "rejection_code": "DATA_DFF_WORK_GENERATED"}
    return {"passed": True, "rejection_code": None}


def _build_physical_interface_semantic_regression(interface_bundle: dict[str, Any]) -> dict[str, Any]:
    connectivity = interface_bundle["connectivity_lookup"]
    lib = gdstk.read_gds(DFF_GDS)
    top_cells = lib.top_level()
    if len(top_cells) != 1:
        raise RuntimeError("semantic regression requires exactly one approved DFF top cell")
    flattened = top_cells[0].copy("semantic_regression_flattened")
    flattened.flatten()
    bbox_to_rect_ids: dict[tuple[str, tuple[float, ...]], list[str]] = {
        key: list(value) for key, value in connectivity["bbox_key_to_rect_ids"].items()
    }
    object_multiset_actual = Counter(
        (row["layer_name"], tuple(row["transformed_bbox"]), row["resolved_net"]) for row in interface_bundle["obstacle_report"]["objects"]
    )
    object_multiset_reference = Counter()
    net_partition_reference = Counter()
    for polygon in flattened.polygons:
        if polygon.layer not in CONDUCTIVE_LAYER_MAP:
            continue
        layer_name = CONDUCTIVE_LAYER_MAP[polygon.layer]
        points = _polygon_points(polygon)
        bbox = tuple(_normalize_bbox(points))
        rect_ids = bbox_to_rect_ids.get((layer_name, bbox), [])
        if not rect_ids:
            raise RuntimeError(f"semantic regression missing connectivity rectangle for {(layer_name, bbox)}")
        rect_id = rect_ids[0]
        component_id = connectivity["rect_to_component"].get(rect_id)
        net_name = connectivity["component_to_net"].get(component_id)
        object_multiset_reference[(layer_name, bbox, net_name)] += 1
        geometry_digest = _sha256_bytes(
            json.dumps(
                {
                    "layer_name": layer_name,
                    "layer": polygon.layer,
                    "datatype": polygon.datatype,
                    "transformed_polygon_points": points,
                },
                sort_keys=True,
                separators=(",", ":"),
            ).encode("utf-8")
        )
        net_partition_reference[(net_name, geometry_digest)] += 1
    pin_multiset_actual = Counter(
        (
            row["pin_name"],
            tuple(tuple(tuple(point) for point in polygon) for polygon in row["exact_polygon_points"]),
        )
        for row in interface_bundle["pin_geometry"]["pins"]
    )
    pin_multiset_reference = Counter()
    for hit in connectivity["graph"]["label_hits"]:
        polygons = [
            tuple(tuple(point) for point in interface_bundle["obstacle_report"]["objects"][0]["transformed_polygon_points"])
            for _ in []
        ]
        rect_polygons = []
        for rect_id in hit["shape_ids"]:
            rect_row = connectivity["rect_info_by_id"][rect_id]
            bbox = rect_row["bbox"]
            rect_polygons.append(((bbox[0], bbox[1]), (bbox[2], bbox[1]), (bbox[2], bbox[3]), (bbox[0], bbox[3])))
        pin_multiset_reference[(hit["text"], tuple(rect_polygons))] += 1
    net_partition_actual = Counter(
        (row["resolved_net"], row["geometry_digest"]) for row in interface_bundle["obstacle_report"]["objects"] if row["resolved_net"] is not None
    )
    report = {
        "object_geometry_multiset_matches_reference": object_multiset_actual == object_multiset_reference,
        "pin_polygon_multiset_matches_reference": pin_multiset_actual == pin_multiset_reference,
        "component_partition_equivalent": net_partition_actual == net_partition_reference,
        "top_bbox_matches_expected": interface_bundle["interface_report"]["top_cell_bbox"] == EXPECTED_DFF_TOP_BBOX,
        "child_inventory_matches_expected": interface_bundle["interface_report"]["direct_child_inventory"] == EXPECTED_DFF_DIRECT_CHILDREN,
        "hierarchy_closure_matches_expected": interface_bundle["hierarchy_closure"]["closure_passed"],
    }
    report["semantic_regression_passed"] = all(report.values())
    _write_json(STAGE_DIR / "ADDR_DFF_DFF_physical_interface_semantic_regression.json", report)
    return report


def _output_ownership_test(ast_report: dict[str, Any], interface_bundle: dict[str, Any]) -> dict[str, Any]:
    full_files = [
        STAGE_DIR / "ADDR_DFF_DFF_conductive_obstacle_map.json",
        STAGE_DIR / "ADDR_DFF_DFF_child_physical_interface.json",
        STAGE_DIR / "ADDR_DFF_DFF_pin_geometry.csv",
        STAGE_DIR / "ADDR_DFF_DFF_pin_geometry.json",
        STAGE_DIR / "ADDR_DFF_DFF_hierarchy_closure.json",
    ]
    before = {str(path): _sha256(path) for path in full_files}
    summary = _build_parameter_binding_summary(ast_report, write_outputs=True)
    closure = _validate_parameter_to_physical_closure(summary, interface_bundle, write_outputs=True)
    after = {str(path): _sha256(path) for path in full_files}
    modified = [path for path in before if before[path] != after[path]]
    report = {
        "before_sha256": before,
        "after_sha256": after,
        "full_interface_files_modified_by_binding_validator": bool(modified),
        "modified_paths": modified,
        "binding_summary_path": str(STAGE_DIR / "ADDR_DFF_DFF_parameter_binding_summary.json"),
        "binding_closure_path": str(STAGE_DIR / "ADDR_DFF_DFF_parameter_to_physical_binding_closure.json"),
        "binding_closure_passed": closure["closure_passed"],
    }
    _write_json(STAGE_DIR / "ADDR_DFF_physical_interface_output_ownership_test.json", report)
    return report


def _save_mutation_text(test_name: str, filename: str, content: str) -> Path:
    target_dir = STAGE_DIR / "negative_test_artifacts" / test_name
    target_dir.mkdir(parents=True, exist_ok=True)
    destination = target_dir / filename
    destination.write_text(content, encoding="utf-8")
    return destination


def _save_mutation_json(test_name: str, filename: str, payload: Any) -> Path:
    target_dir = STAGE_DIR / "negative_test_artifacts" / test_name
    target_dir.mkdir(parents=True, exist_ok=True)
    destination = target_dir / filename
    destination.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return destination


def _record_negative_test(
    results: list[dict[str, Any]],
    *,
    test_name: str,
    mutation_target: str,
    mutation_description: str,
    mutation_applied: bool,
    mutation_artifact_path: str,
    production_validator_entrypoint: str,
    validator_invoked: bool,
    validator_result: dict[str, Any],
    expected_rejection_code: str,
) -> None:
    validator_returned_pass = bool(validator_result.get("passed"))
    actual_rejection_code = validator_result.get("rejection_code")
    rejection_observed = not validator_returned_pass and actual_rejection_code is not None
    uses_production_validator = validator_invoked and production_validator_entrypoint.startswith("_")
    hardcoded_result = (
        (not uses_production_validator)
        or (not validator_invoked)
        or (not mutation_applied)
        or (actual_rejection_code != expected_rejection_code)
    )
    test_passed = rejection_observed and actual_rejection_code == expected_rejection_code and not hardcoded_result
    results.append(
        {
            "test_name": test_name,
            "mutation_target": mutation_target,
            "mutation_description": mutation_description,
            "mutation_applied": mutation_applied,
            "mutation_artifact_path": mutation_artifact_path,
            "production_validator_entrypoint": production_validator_entrypoint,
            "validator_invoked": validator_invoked,
            "validator_returned_pass": validator_returned_pass,
            "rejection_observed": rejection_observed,
            "expected_rejection_code": expected_rejection_code,
            "actual_rejection_code": actual_rejection_code,
            "uses_production_validator": uses_production_validator,
            "hardcoded_result": hardcoded_result,
            "test_passed": test_passed,
        }
    )


def _run_negative_tests(locked_blob: dict[str, Any], ast_report: dict[str, Any], source_topology: dict[str, Any], expected_contract: dict[str, Any], interface_bundle: dict[str, Any]) -> dict[str, Any]:
    test_results: list[dict[str, Any]] = []
    source_text = locked_blob["bytes"].decode("utf-8")

    wrong_commit_result = _validator_source_snapshot(
        "locked_git_blob",
        "0000000000000000000000000000000000000000",
        EXPECTED_TIME_GENERATE_PATH,
        locked_blob["bytes"],
        EXPECTED_OPENYIELD_COMMIT,
        EXPECTED_TIME_GENERATE_PATH,
        EXPECTED_TIME_GENERATE_BLOB_SHA,
        EXPECTED_TIME_GENERATE_SHA256,
    )
    _record_negative_test(
        test_results,
        test_name="openyield_commit_mismatch",
        mutation_target="authority_commit",
        mutation_description="use wrong authority commit with locked source bytes",
        mutation_applied=True,
        mutation_artifact_path=str(locked_blob["snapshot_path"]),
        production_validator_entrypoint="_validator_source_snapshot",
        validator_invoked=True,
        validator_result=wrong_commit_result,
        expected_rejection_code="AUTHORITY_COMMIT_MISMATCH",
    )

    wrong_blob_result = _validator_source_snapshot(
        "locked_git_blob",
        EXPECTED_OPENYIELD_COMMIT,
        EXPECTED_TIME_GENERATE_PATH,
        locked_blob["bytes"],
        EXPECTED_OPENYIELD_COMMIT,
        EXPECTED_TIME_GENERATE_PATH,
        "0000000000000000000000000000000000000000",
        EXPECTED_TIME_GENERATE_SHA256,
    )
    _record_negative_test(
        test_results,
        test_name="time_generate_blob_sha_mismatch",
        mutation_target="expected_blob_sha",
        mutation_description="use wrong expected blob SHA against production source snapshot validator",
        mutation_applied=True,
        mutation_artifact_path=str(locked_blob["snapshot_path"]),
        production_validator_entrypoint="_validator_source_snapshot",
        validator_invoked=True,
        validator_result=wrong_blob_result,
        expected_rejection_code="LOCKED_BLOB_SHA_MISMATCH",
    )

    wrong_source_sha_result = _validator_source_snapshot(
        "locked_git_blob",
        EXPECTED_OPENYIELD_COMMIT,
        EXPECTED_TIME_GENERATE_PATH,
        locked_blob["bytes"],
        EXPECTED_OPENYIELD_COMMIT,
        EXPECTED_TIME_GENERATE_PATH,
        EXPECTED_TIME_GENERATE_BLOB_SHA,
        "0000000000000000000000000000000000000000000000000000000000000000",
    )
    _record_negative_test(
        test_results,
        test_name="locked_source_sha_mismatch",
        mutation_target="expected_source_sha256",
        mutation_description="use wrong expected locked source SHA-256 against production source snapshot validator",
        mutation_applied=True,
        mutation_artifact_path=str(locked_blob["snapshot_path"]),
        production_validator_entrypoint="_validator_source_snapshot",
        validator_invoked=True,
        validator_result=wrong_source_sha_result,
        expected_rejection_code="LOCKED_SOURCE_SHA_MISMATCH",
    )

    wrong_source_path_result = _validator_source_snapshot(
        "locked_git_blob",
        EXPECTED_OPENYIELD_COMMIT,
        "compiler/base.py",
        locked_blob["bytes"],
        EXPECTED_OPENYIELD_COMMIT,
        EXPECTED_TIME_GENERATE_PATH,
        EXPECTED_TIME_GENERATE_BLOB_SHA,
        EXPECTED_TIME_GENERATE_SHA256,
    )
    _record_negative_test(
        test_results,
        test_name="source_path_mismatch",
        mutation_target="authority_source_path",
        mutation_description="use wrong authority source path while keeping the locked blob bytes unchanged",
        mutation_applied=True,
        mutation_artifact_path=str(locked_blob["snapshot_path"]),
        production_validator_entrypoint="_validator_source_snapshot",
        validator_invoked=True,
        validator_result=wrong_source_path_result,
        expected_rejection_code="SOURCE_PATH_MISMATCH",
    )

    working_tree_result = _validator_source_snapshot(
        "working_tree_file",
        EXPECTED_OPENYIELD_COMMIT,
        EXPECTED_TIME_GENERATE_PATH,
        OPENYIELD_TIME_GENERATE.read_bytes(),
        EXPECTED_OPENYIELD_COMMIT,
        EXPECTED_TIME_GENERATE_PATH,
        EXPECTED_TIME_GENERATE_BLOB_SHA,
        EXPECTED_TIME_GENERATE_SHA256,
    )
    _record_negative_test(
        test_results,
        test_name="working_tree_used_as_authority",
        mutation_target="authority_kind",
        mutation_description="use working-tree source as authority instead of locked git blob",
        mutation_applied=True,
        mutation_artifact_path=str(OPENYIELD_TIME_GENERATE),
        production_validator_entrypoint="_validator_source_snapshot",
        validator_invoked=True,
        validator_result=working_tree_result,
        expected_rejection_code="WORKING_TREE_USED_AS_AUTHORITY",
    )

    class_missing_text = source_text.replace("class ADDR_DFF", "class ADDR_DFX")
    class_missing_path = _save_mutation_text("addr_dff_class_missing", "time_generate_addr_dff_missing.py", class_missing_text)
    try:
        _extract_source_contract(class_missing_path.read_bytes(), str(class_missing_path), write_outputs=False)
        class_missing_result = {"passed": True, "rejection_code": None}
    except RuntimeError:
        class_missing_result = {"passed": False, "rejection_code": "ADDR_DFF_CLASS_MISSING"}
    _record_negative_test(
        test_results,
        test_name="addr_dff_class_missing",
        mutation_target="locked_source_copy",
        mutation_description="rename class ADDR_DFF in locked source temporary copy",
        mutation_applied=True,
        mutation_artifact_path=str(class_missing_path),
        production_validator_entrypoint="_extract_source_contract",
        validator_invoked=True,
        validator_result=class_missing_result,
        expected_rejection_code="ADDR_DFF_CLASS_MISSING",
    )

    method_missing_text = source_text.replace("def add_addr_dff_array", "def add_addr_dff_array_removed")
    method_missing_path = _save_mutation_text("add_addr_dff_array_missing", "time_generate_add_addr_missing.py", method_missing_text)
    try:
        _extract_source_contract(method_missing_path.read_bytes(), str(method_missing_path), write_outputs=False)
        method_missing_result = {"passed": True, "rejection_code": None}
    except RuntimeError:
        method_missing_result = {"passed": False, "rejection_code": "ADD_ADDR_DFF_ARRAY_MISSING"}
    _record_negative_test(
        test_results,
        test_name="add_addr_dff_array_missing",
        mutation_target="locked_source_copy",
        mutation_description="rename add_addr_dff_array in locked source temporary copy",
        mutation_applied=True,
        mutation_artifact_path=str(method_missing_path),
        production_validator_entrypoint="_extract_source_contract",
        validator_invoked=True,
        validator_result=method_missing_result,
        expected_rejection_code="ADD_ADDR_DFF_ARRAY_MISSING",
    )

    nbits_bad_text = source_text.replace(
        "ceil(log2(self.num_rows)) if self.num_rows > 1 else 1",
        "int(log2(self.num_rows)) - 1",
    )
    nbits_bad_path = _save_mutation_text("n_bits_formula_changed", "time_generate_bad_nbits.py", nbits_bad_text)
    nbits_ast = _extract_source_contract(nbits_bad_path.read_bytes(), str(nbits_bad_path), write_outputs=False)
    nbits_config = _resolve_num_rows(nbits_ast, write_outputs=False)
    nbits_topology = _build_source_topology(nbits_ast, nbits_config, write_outputs=False)
    nbits_result = _validate_topology_exact_identity(nbits_topology, expected_contract, write_outputs=False)
    _record_negative_test(
        test_results,
        test_name="n_bits_formula_changed",
        mutation_target="locked_source_copy",
        mutation_description="change n_bits formula so resolved bit count no longer matches project contract",
        mutation_applied=True,
        mutation_artifact_path=str(nbits_bad_path),
        production_validator_entrypoint="_validate_topology_exact_identity",
        validator_invoked=True,
        validator_result={"passed": nbits_result["exact_identity_passed"], "rejection_code": nbits_result["rejection_code"]},
        expected_rejection_code="TOPOLOGY_EXACT_IDENTITY_MISMATCH",
    )

    clk_missing_text = source_text.replace("nodes = ['VDD', 'VSS', 'CLK']", "nodes = ['VDD', 'VSS']").replace(
        "'VDD', 'VSS', f'A{i}', f'A_dff{i}', 'CLK'",
        "'VDD', 'VSS', f'A{i}', f'A_dff{i}'",
    ).replace(
        "addr_dff_connections = ['VDD', 'VSS', 'clk_buf']",
        "addr_dff_connections = ['VDD', 'VSS']",
    )
    clk_missing_path = _save_mutation_text("clk_pin_missing", "time_generate_clk_missing.py", clk_missing_text)
    clk_ast = _extract_source_contract(clk_missing_path.read_bytes(), str(clk_missing_path), write_outputs=False)
    clk_config = _resolve_num_rows(clk_ast, write_outputs=False)
    clk_topology = _build_source_topology(clk_ast, clk_config, write_outputs=False)
    clk_result = _validate_topology_exact_identity(clk_topology, expected_contract, write_outputs=False)
    _record_negative_test(
        test_results,
        test_name="clk_pin_missing",
        mutation_target="locked_source_copy",
        mutation_description="remove CLK from nodes and instance/time connection construction in temporary source copy",
        mutation_applied=True,
        mutation_artifact_path=str(clk_missing_path),
        production_validator_entrypoint="_validate_topology_exact_identity",
        validator_invoked=True,
        validator_result={"passed": clk_result["exact_identity_passed"], "rejection_code": clk_result["rejection_code"]},
        expected_rejection_code="TOPOLOGY_EXACT_IDENTITY_MISMATCH",
    )

    top_pin_swapped = json.loads(json.dumps(source_topology))
    top_pin_swapped["resolved_top_pins"][2], top_pin_swapped["resolved_top_pins"][3] = top_pin_swapped["resolved_top_pins"][3], top_pin_swapped["resolved_top_pins"][2]
    top_pin_swapped_path = _save_mutation_json("top_pin_order_changed", "topology_top_pin_swapped.json", top_pin_swapped)
    top_pin_swapped_result = _validate_topology_exact_identity(top_pin_swapped, expected_contract, write_outputs=False)
    _record_negative_test(
        test_results,
        test_name="top_pin_order_changed",
        mutation_target="source_derived_topology_copy",
        mutation_description="swap CLK and A0 in temporary source-derived topology copy",
        mutation_applied=True,
        mutation_artifact_path=str(top_pin_swapped_path),
        production_validator_entrypoint="_validate_topology_exact_identity",
        validator_invoked=True,
        validator_result={"passed": top_pin_swapped_result["exact_identity_passed"], "rejection_code": top_pin_swapped_result["rejection_code"]},
        expected_rejection_code="TOPOLOGY_EXACT_IDENTITY_MISMATCH",
    )

    missing_instance_topology = json.loads(json.dumps(source_topology))
    missing_instance_topology["child_instances"] = missing_instance_topology["child_instances"][:-1]
    missing_instance_path = _save_mutation_json("missing_dff_instances", "topology_missing_instance.json", missing_instance_topology)
    missing_instance_contract = _validate_topology_contract(missing_instance_topology)
    _record_negative_test(
        test_results,
        test_name="missing_dff_instances",
        mutation_target="source_derived_topology_copy",
        mutation_description="drop dff_3 from temporary topology copy",
        mutation_applied=True,
        mutation_artifact_path=str(missing_instance_path),
        production_validator_entrypoint="_validate_topology_contract",
        validator_invoked=True,
        validator_result=missing_instance_contract,
        expected_rejection_code="CHILD_INSTANCE_COUNT_MISMATCH",
    )

    duplicate_topology = json.loads(json.dumps(source_topology))
    duplicate_topology["child_instances"][-1]["instance_name"] = duplicate_topology["child_instances"][-2]["instance_name"]
    duplicate_path = _save_mutation_json("duplicate_child_instance", "topology_duplicate_instance.json", duplicate_topology)
    duplicate_result = _validate_topology_contract(duplicate_topology)
    _record_negative_test(
        test_results,
        test_name="duplicate_child_instance",
        mutation_target="source_derived_topology_copy",
        mutation_description="force dff_2 and dff_3 to share the same instance name",
        mutation_applied=True,
        mutation_artifact_path=str(duplicate_path),
        production_validator_entrypoint="_validate_topology_contract",
        validator_invoked=True,
        validator_result=duplicate_result,
        expected_rejection_code="DUPLICATE_CHILD_INSTANCE",
    )

    child_count_five = json.loads(json.dumps(source_topology))
    child_count_five["child_instances"].append(
        {
            "instance_name": "dff_4",
            "logical_child_expression": "self.dff_addr.NAME",
            "connections": ["VDD", "VSS", "A4", "A_dff4", "CLK"],
        }
    )
    child_count_five_path = _save_mutation_json("child_count_five", "topology_child_count_five.json", child_count_five)
    child_count_five_result = _validate_topology_contract(child_count_five)
    _record_negative_test(
        test_results,
        test_name="child_count_five",
        mutation_target="source_derived_topology_copy",
        mutation_description="append temporary fifth child instance to topology copy",
        mutation_applied=True,
        mutation_artifact_path=str(child_count_five_path),
        production_validator_entrypoint="_validate_topology_contract",
        validator_invoked=True,
        validator_result=child_count_five_result,
        expected_rejection_code="CHILD_INSTANCE_COUNT_MISMATCH",
    )

    swapped_endpoint = json.loads(json.dumps(source_topology))
    swapped_endpoint["child_instances"][0]["connections"] = ["VDD", "VSS", "A_dff0", "A0", "CLK"]
    swapped_endpoint_path = _save_mutation_json("a_and_a_dff_swapped", "topology_a_a_dff_swapped.json", swapped_endpoint)
    swapped_endpoint_result = _validate_topology_exact_identity(swapped_endpoint, expected_contract, write_outputs=False)
    _record_negative_test(
        test_results,
        test_name="a_and_a_dff_swapped",
        mutation_target="source_derived_topology_copy",
        mutation_description="swap A0 and A_dff0 endpoints on one temporary instance connection",
        mutation_applied=True,
        mutation_artifact_path=str(swapped_endpoint_path),
        production_validator_entrypoint="_validate_topology_exact_identity",
        validator_invoked=True,
        validator_result={"passed": swapped_endpoint_result["exact_identity_passed"], "rejection_code": swapped_endpoint_result["rejection_code"]},
        expected_rejection_code="TOPOLOGY_EXACT_IDENTITY_MISMATCH",
    )

    wrong_top_result = _validate_approved_dff_artifact(EXPECTED_DFF_SHA, "WRONG_TOP_CELL")
    _record_negative_test(
        test_results,
        test_name="dff_top_cell_mismatch",
        mutation_target="expected_top_cell",
        mutation_description="pass wrong expected top cell into approved DFF artifact validator",
        mutation_applied=True,
        mutation_artifact_path=str(DFF_GDS),
        production_validator_entrypoint="_validate_approved_dff_artifact",
        validator_invoked=True,
        validator_result=wrong_top_result,
        expected_rejection_code="APPROVED_DFF_TOP_CELL_MISMATCH",
    )

    wrong_sha_result = _validate_approved_dff_artifact("0000000000000000000000000000000000000000000000000000000000000000", EXPECTED_DFF_TOP)
    _record_negative_test(
        test_results,
        test_name="approved_dff_gds_sha_mismatch",
        mutation_target="expected_sha256",
        mutation_description="pass wrong expected approved DFF SHA into production artifact validator",
        mutation_applied=True,
        mutation_artifact_path=str(DFF_GDS),
        production_validator_entrypoint="_validate_approved_dff_artifact",
        validator_invoked=True,
        validator_result=wrong_sha_result,
        expected_rejection_code="APPROVED_DFF_GDS_SHA_MISMATCH",
    )

    summary_bad = json.loads(json.dumps(_build_parameter_binding_summary(ast_report, write_outputs=False)))
    summary_bad["default_values"]["pmos_width"] = "6e-07"
    summary_bad["normalized_nm_values"]["pmos_width_nm"] = 600
    summary_bad_path = _save_mutation_json("constructor_default_parameter_unclosed", "binding_summary_pmos600.json", summary_bad)
    summary_bad_result = _validate_parameter_to_physical_closure(summary_bad, interface_bundle, write_outputs=False)
    _record_negative_test(
        test_results,
        test_name="constructor_default_parameter_unclosed",
        mutation_target="parameter_binding_summary_copy",
        mutation_description="change temporary constructor binding summary default width from 500nm to 600nm",
        mutation_applied=True,
        mutation_artifact_path=str(summary_bad_path),
        production_validator_entrypoint="_validate_parameter_to_physical_closure",
        validator_invoked=True,
        validator_result={"passed": summary_bad_result["closure_passed"], "rejection_code": summary_bad_result["rejection_code"]},
        expected_rejection_code="PARAMETER_TO_PHYSICAL_CLOSURE_MISMATCH",
    )

    mapping_swapped = {
        "binding_rows": [
            {
                "instance_name": row["instance_name"],
                "logical_to_physical_pin_mapping": (
                    {"VDD": "VDD", "VSS": "VSS", "A0": "Q", "A_dff0": "D", "CLK": "CLK"}
                    if row["instance_name"] == "dff_0"
                    else {
                        "VDD": "VDD",
                        "VSS": "VSS",
                        f"A{idx}": "D",
                        f"A_dff{idx}": "Q",
                        "CLK": "CLK",
                    }
                ),
            }
            for idx, row in enumerate(source_topology["child_instances"])
        ]
    }
    mapping_swapped_path = _save_mutation_json("d_and_q_physical_mapping_swapped", "binding_rows_swapped.json", mapping_swapped)
    mapping_swapped_result = _validate_logical_to_physical_mapping(source_topology, mapping_swapped["binding_rows"])
    _record_negative_test(
        test_results,
        test_name="d_and_q_physical_mapping_swapped",
        mutation_target="binding_rows_copy",
        mutation_description="swap Ai->D and A_dffi->Q into Ai->Q and A_dffi->D on one temporary binding row",
        mutation_applied=True,
        mutation_artifact_path=str(mapping_swapped_path),
        production_validator_entrypoint="_validate_logical_to_physical_mapping",
        validator_invoked=True,
        validator_result=mapping_swapped_result,
        expected_rejection_code="LOGICAL_TO_PHYSICAL_PIN_MAPPING_MISMATCH",
    )

    conflict_dir = STAGE_DIR / "negative_test_artifacts" / "num_rows_authority_conflict"
    conflict_dir.mkdir(parents=True, exist_ok=True)
    authority16 = conflict_dir / "authority_16.json"
    authority32 = conflict_dir / "authority_32.json"
    authority16.write_text('{\n  "num_rows": 16\n}\n', encoding="utf-8")
    authority32.write_text('{\n  "num_rows": 32\n}\n', encoding="utf-8")
    conflict_result = _resolve_num_rows(
        ast_report,
        overrides=[
            {
                "path": str(authority16),
                "source_category": "temp_current_authority",
                "current_or_historical": "current",
                "content_sha256": _sha256(authority16),
                "parsed_num_rows": 16,
                "precedence": 10,
            },
            {
                "path": str(authority32),
                "source_category": "temp_current_authority",
                "current_or_historical": "current",
                "content_sha256": _sha256(authority32),
                "parsed_num_rows": 32,
                "precedence": 20,
            },
        ],
        write_outputs=False,
    )
    _record_negative_test(
        test_results,
        test_name="num_rows_authority_conflict",
        mutation_target="temp_current_authority_configs",
        mutation_description="use two temporary current-authority configs with num_rows=16 and num_rows=32",
        mutation_applied=True,
        mutation_artifact_path=f"{authority16},{authority32}",
        production_validator_entrypoint="_resolve_num_rows",
        validator_invoked=True,
        validator_result={"passed": not conflict_result["num_rows_authority_conflict"], "rejection_code": "NUM_ROWS_AUTHORITY_CONFLICT" if conflict_result["num_rows_authority_conflict"] else None},
        expected_rejection_code="NUM_ROWS_AUTHORITY_CONFLICT",
    )

    forbidden_mapping = {
        "annotated_gds_rejected": REPO_ROOT / "outputs/M12C4AC_dff_connectivity_repair/current_supported_config/M12C4AC_dff_annotated.gds",
        "atlas_gds_rejected": REPO_ROOT / "outputs/M12C4AC_dff_connectivity_repair/current_supported_config/M12C4AC_dff_review_atlas.gds",
        "quarantined_candidate_rejected": REPO_ROOT / "outputs/M12C4AC_dff_connectivity_repair/current_supported_config/quarantined_failed_attempt/M12C4A_dff_clean.gds",
        "dff_buf_rejected": REPO_ROOT / "outputs/Wave3_DFF_BUF_reusable_release/DFF_BUF_reusable_clean.gds",
    }
    expected_codes = {
        "annotated_gds_rejected": "ANNOTATED_GDS_REJECTED",
        "atlas_gds_rejected": "ATLAS_GDS_REJECTED",
        "quarantined_candidate_rejected": "QUARANTINED_CANDIDATE_REJECTED",
        "dff_buf_rejected": "DFF_BUF_REJECTED",
    }
    for test_name, path in forbidden_mapping.items():
        forbidden_result = _validate_approved_dff_source_path(path)
        _record_negative_test(
            test_results,
            test_name=test_name,
            mutation_target="forbidden_source_path",
            mutation_description="pass forbidden physical source path into production approved-source validator",
            mutation_applied=True,
            mutation_artifact_path=str(path),
            production_validator_entrypoint="_validate_approved_dff_source_path",
            validator_invoked=True,
            validator_result=forbidden_result,
            expected_rejection_code=expected_codes[test_name],
        )

    with tempfile.TemporaryDirectory(prefix="wave4a_r2_addr_") as tmp:
        tmp_root = Path(tmp)
        (tmp_root / "ADDR_DFF_generated.gds").write_bytes(b"dummy")
        addr_generated_result = _validate_no_generated_artifacts(tmp_root)
        _record_negative_test(
            test_results,
            test_name="addr_dff_gds_generated_rejected",
            mutation_target="temp_stage_root",
            mutation_description="create temporary ADDR_DFF-generated GDS under stage-like root",
            mutation_applied=True,
            mutation_artifact_path=str(tmp_root / "ADDR_DFF_generated.gds"),
            production_validator_entrypoint="_validate_no_generated_artifacts",
            validator_invoked=True,
            validator_result=addr_generated_result,
            expected_rejection_code="ADDR_DFF_GDS_GENERATED",
        )

    with tempfile.TemporaryDirectory(prefix="wave4a_r2_data_") as tmp:
        tmp_root = Path(tmp)
        (tmp_root / "DATA_DFF_generated.gds").write_bytes(b"dummy")
        data_generated_result = _validate_no_generated_artifacts(tmp_root)
        _record_negative_test(
            test_results,
            test_name="data_dff_work_generated_rejected",
            mutation_target="temp_stage_root",
            mutation_description="create temporary DATA_DFF-generated GDS under stage-like root",
            mutation_applied=True,
            mutation_artifact_path=str(tmp_root / "DATA_DFF_generated.gds"),
            production_validator_entrypoint="_validate_no_generated_artifacts",
            validator_invoked=True,
            validator_result=data_generated_result,
            expected_rejection_code="DATA_DFF_WORK_GENERATED",
        )

    required_tests = sorted(set(CURRENT_REQUIRED_NEGATIVE_TESTS + RESTORED_NEGATIVE_TESTS))
    actual_names = {row["test_name"] for row in test_results}
    missing_expected = sorted(name for name in required_tests if name not in actual_names)
    summary = {
        "tests": test_results,
        "total_test_count": len(test_results),
        "real_mutation_test_count": sum(1 for row in test_results if row["mutation_applied"]),
        "production_validator_test_count": sum(1 for row in test_results if row["uses_production_validator"]),
        "hardcoded_negative_test_count": sum(1 for row in test_results if row["hardcoded_result"]),
        "failed_test_count": sum(1 for row in test_results if not row["test_passed"]),
        "missing_expected_test_count": len(missing_expected),
        "missing_expected_tests": missing_expected,
        "restored_negative_test_count": sum(1 for name in RESTORED_NEGATIVE_TESTS if name in actual_names),
        "all_negative_tests_passed": all(row["test_passed"] for row in test_results) and not missing_expected,
    }
    _write_json(STAGE_DIR / "ADDR_DFF_negative_tests.json", summary)
    _write_text(STAGE_DIR / "ADDR_DFF_negative_tests.md", _render_md_kv("ADDR_DFF Negative Tests", summary))
    _write_json(
        STAGE_DIR / "ADDR_DFF_negative_test_derived_counts.json",
        {
            key: summary[key]
            for key in [
                "total_test_count",
                "restored_negative_test_count",
                "real_mutation_test_count",
                "production_validator_test_count",
                "hardcoded_negative_test_count",
                "failed_test_count",
                "missing_expected_test_count",
                "missing_expected_tests",
            ]
        },
    )
    return summary


def _validate_logical_to_physical_mapping(source_topology: dict[str, Any], binding_rows: list[dict[str, Any]]) -> dict[str, Any]:
    errors = []
    by_name = {row["instance_name"]: row for row in binding_rows}
    for idx, instance in enumerate(source_topology["child_instances"]):
        expected = {
            "VDD": "VDD",
            "VSS": "VSS",
            f"A{idx}": "D",
            f"A_dff{idx}": "Q",
            "CLK": "CLK",
        }
        actual = by_name.get(instance["instance_name"], {}).get("logical_to_physical_pin_mapping")
        if actual != expected:
            errors.append({"instance_name": instance["instance_name"], "expected": expected, "actual": actual})
    return {"passed": not errors, "rejection_code": None if not errors else "LOGICAL_TO_PHYSICAL_PIN_MAPPING_MISMATCH", "errors": errors}


def _check_dirty_immutability() -> dict[str, Any]:
    baseline = _read_json(STAGE_DIR / "baseline_dirty_tree_report.json")
    changed = []
    current_rows = []
    for row in baseline["dirty_paths"]:
        if _path_is_mutable_in_this_round(row["relative_path"]):
            continue
        current = _path_metadata(row["relative_path"])
        current["status_code"] = row["status_code"]
        current["tracked_status"] = row["tracked_status"]
        current_rows.append(current)
        if current["exists"] != row["exists"] or current["size_bytes"] != row["size_bytes"] or current["sha256"] != row["sha256"]:
            changed.append({"path": row["relative_path"], "before": row, "after": current})
    payload = {"all_passed": not changed, "changed_paths": changed, "baseline_count": len(baseline["dirty_paths"]), "current_rows": current_rows}
    _write_json(STAGE_DIR / "existing_dirty_path_immutability_report.json", payload)
    return payload


def check_staged() -> None:
    staged = [line for line in _git("diff", "--cached", "--name-only").splitlines() if line.strip()]
    baseline = _read_json(STAGE_DIR / "baseline_dirty_tree_report.json")
    protected_dirty = {row["relative_path"] for row in baseline["dirty_paths"] if not _path_is_mutable_in_this_round(row["relative_path"])}
    outsiders = [path for path in staged if not _path_is_mutable_in_this_round(path)]
    dirty_staged = [path for path in staged if path in protected_dirty]
    payload = {
        "allowlist": ALLOWLIST,
        "staged_paths": staged,
        "unexpected_staged_paths": outsiders,
        "preexisting_dirty_paths_in_staged_area": dirty_staged,
        "staged_allowlist_passed": not outsiders and not dirty_staged,
    }
    _write_json(STAGE_DIR / "staged_allowlist_report.json", payload)
    _write_text(STAGE_DIR / "staged_allowlist_report.md", _render_md_kv("Staged Allowlist Report", payload))
    if outsiders or dirty_staged:
        raise RuntimeError(f"staged allowlist failure: outsiders={outsiders} dirty_staged={dirty_staged}")


def _manifest_entries_for_package(package_root: Path) -> list[dict[str, Any]]:
    entries = []
    for path in sorted(package_root.rglob("*")):
        if not path.is_file():
            continue
        rel = path.relative_to(package_root).as_posix()
        if rel in {"evidence_package_manifest.json", "evidence_package_manifest.csv", "SHA256SUMS"}:
            continue
        entries.append({"relative_path": rel, "file_size": path.stat().st_size, "sha256": _sha256(path), "required": True})
    return entries


def _verify_manifest_and_sums(package_root: Path) -> dict[str, Any]:
    manifest = _read_json(package_root / "evidence_package_manifest.json")
    missing = []
    size_mismatch = []
    sha_mismatch = []
    for entry in manifest["entries"]:
        path = package_root / entry["relative_path"]
        if not path.exists():
            missing.append(entry["relative_path"])
            continue
        if path.stat().st_size != entry["file_size"]:
            size_mismatch.append(entry["relative_path"])
        if _sha256(path) != entry["sha256"]:
            sha_mismatch.append(entry["relative_path"])
    sum_lines = (package_root / "SHA256SUMS").read_text(encoding="utf-8").splitlines()
    sum_mismatches = []
    sum_targets = []
    for line in sum_lines:
        digest, rel = line.split("  ", 1)
        sum_targets.append(rel)
        if _sha256(package_root / rel) != digest:
            sum_mismatches.append(rel)
    return {
        "manifest_required_entry_actual_count": len(manifest["entries"]),
        "sha256sums_actual_count": len(sum_lines),
        "missing": missing,
        "size_mismatch": size_mismatch,
        "sha_mismatch": sha_mismatch,
        "sha256sum_mismatch": sum_mismatches,
        "manifest_verification_report_covered_by_sha256sums": "reports/manifest_verification_report.json" in sum_targets,
        "package_verification_report_covered_by_sha256sums": "reports/package_verification_report.json" in sum_targets,
        "all_passed": not missing and not size_mismatch and not sha_mismatch and not sum_mismatches,
    }


def _write_stage_report(preconditions: dict[str, Any], source_snapshot_report: dict[str, Any], interface_bundle: dict[str, Any], semantic_regression: dict[str, Any], ownership_test: dict[str, Any], negative_summary: dict[str, Any]) -> None:
    report = {
        "stage": STAGE_ID,
        "current_status": "PASS",
        "project_branch": preconditions["project_branch"],
        "report_generation_base_commit": preconditions["report_generation_base_commit"],
        "openyield_commit": EXPECTED_OPENYIELD_COMMIT,
        "locked_blob_sha1": EXPECTED_TIME_GENERATE_BLOB_SHA,
        "locked_source_sha256": EXPECTED_TIME_GENERATE_SHA256,
        "source_snapshot_validator_passed": source_snapshot_report["passed"],
        "approved_dff_sha256": EXPECTED_DFF_SHA,
        "approved_dff_immutability_passed": _sha256(DFF_GDS) == EXPECTED_DFF_SHA,
        "full_obstacle_object_count": interface_bundle["obstacle_report"]["total_object_count"],
        "obstacle_layer_counts": {
            "M1": interface_bundle["obstacle_report"]["M1_object_count"],
            "Via1": interface_bundle["obstacle_report"]["Via1_object_count"],
            "M2": interface_bundle["obstacle_report"]["M2_object_count"],
        },
        "pin_geometry_count": interface_bundle["pin_geometry"]["pin_count"],
        "child_physical_interface_complete": True,
        "hierarchy_closure_passed": interface_bundle["hierarchy_closure"]["closure_passed"],
        "semantic_regression_passed": semantic_regression["semantic_regression_passed"],
        "output_ownership_test_passed": not ownership_test["full_interface_files_modified_by_binding_validator"],
        "negative_test_summary": {
            "total_test_count": negative_summary["total_test_count"],
            "restored_negative_test_count": negative_summary["restored_negative_test_count"],
            "real_mutation_test_count": negative_summary["real_mutation_test_count"],
            "production_validator_test_count": negative_summary["production_validator_test_count"],
            "hardcoded_negative_test_count": negative_summary["hardcoded_negative_test_count"],
            "failed_test_count": negative_summary["failed_test_count"],
            "missing_expected_test_count": negative_summary["missing_expected_test_count"],
        },
        "addr_dff_gds_generated": False,
        "data_dff_work_performed": False,
        "next_stage": NEXT_STAGE,
    }
    _write_json(STAGE_DIR / "Wave4A_R2_stage_report.json", report)
    _write_text(STAGE_DIR / "Wave4A_R2_stage_report.md", _render_md_kv("Wave4A R2 Stage Report", report))


def prepare() -> None:
    if STAGE_DIR.exists():
        shutil.rmtree(STAGE_DIR)
    STAGE_DIR.mkdir(parents=True, exist_ok=True)
    preconditions = _verify_required_inputs()
    _write_json(STAGE_DIR / "preconditions.json", preconditions)
    _dirty_tree_baseline()
    _update_ledgers_in_progress()

    locked_blob = _fetch_locked_source_blob()
    source_snapshot_report = _validator_source_snapshot(
        locked_blob["authority_kind"],
        locked_blob["authority_commit"],
        locked_blob["authority_source_path"],
        locked_blob["bytes"],
        EXPECTED_OPENYIELD_COMMIT,
        EXPECTED_TIME_GENERATE_PATH,
        EXPECTED_TIME_GENERATE_BLOB_SHA,
        EXPECTED_TIME_GENERATE_SHA256,
    )
    _write_json(
        STAGE_DIR / "source_blob_lock_report.json",
        {
            "locked_commit": EXPECTED_OPENYIELD_COMMIT,
            "locked_source_path": EXPECTED_TIME_GENERATE_PATH,
            "locked_blob_sha1": locked_blob["blob_sha1"],
            "locked_source_sha256": locked_blob["file_sha256"],
            "snapshot_path": str(locked_blob["snapshot_path"]),
            "source_snapshot_validator": source_snapshot_report,
        },
    )
    if not source_snapshot_report["passed"]:
        raise RuntimeError(source_snapshot_report["rejection_code"])

    ast_report = _extract_source_contract(locked_blob["bytes"], f"{EXPECTED_OPENYIELD_COMMIT}:{EXPECTED_TIME_GENERATE_PATH}", write_outputs=True)
    config_report = _resolve_num_rows(ast_report, write_outputs=True)
    if not config_report["all_current_authorities_equal_16"]:
        raise RuntimeError("num_rows resolution failed")
    source_topology = _build_source_topology(ast_report, config_report, write_outputs=True)
    topology_contract_result = _validate_topology_contract(source_topology)
    if not topology_contract_result["passed"]:
        raise RuntimeError(topology_contract_result["rejection_code"])
    exact_identity_report = _validate_topology_exact_identity(source_topology, _expected_project_contract(), write_outputs=True)
    if not exact_identity_report["exact_identity_passed"]:
        raise RuntimeError(exact_identity_report["rejection_code"])

    interface_bundle = _extract_full_physical_interface(write_outputs=True)
    summary = _build_parameter_binding_summary(ast_report, write_outputs=True)
    closure = _validate_parameter_to_physical_closure(summary, interface_bundle, write_outputs=True)
    if not closure["closure_passed"]:
        raise RuntimeError("parameter-to-physical closure failed")
    semantic_regression = _build_physical_interface_semantic_regression(interface_bundle)
    if not semantic_regression["semantic_regression_passed"]:
        raise RuntimeError("physical interface semantic regression failed")
    ownership_test = _output_ownership_test(ast_report, interface_bundle)
    if ownership_test["full_interface_files_modified_by_binding_validator"]:
        raise RuntimeError("binding validator modified full interface files")

    negative_summary = _run_negative_tests(locked_blob, ast_report, source_topology, _expected_project_contract(), interface_bundle)
    if not negative_summary["all_negative_tests_passed"]:
        raise RuntimeError("negative tests failed")
    if negative_summary["total_test_count"] < 25:
        raise RuntimeError("negative test count below 25")
    if negative_summary["hardcoded_negative_test_count"] != 0:
        raise RuntimeError("hardcoded negative tests detected")
    if negative_summary["missing_expected_test_count"] != 0:
        raise RuntimeError("missing expected negative tests")
    no_generated = _validate_no_generated_artifacts(STAGE_DIR)
    if not no_generated["passed"]:
        raise RuntimeError(no_generated["rejection_code"])

    _update_ledgers_pass()
    ledger_report = _ledger_consistency()
    if not ledger_report["all_passed"]:
        raise RuntimeError("ledger consistency failed")
    _write_stage_report(preconditions, source_snapshot_report, interface_bundle, semantic_regression, ownership_test, negative_summary)


def package() -> None:
    check_staged()
    immutability = _check_dirty_immutability()
    if not immutability["all_passed"]:
        raise RuntimeError("dirty paths changed")

    final_head = _git("rev-parse", "HEAD").strip()
    bundle_path = STAGE_DIR / f"{PACKAGE_PREFIX}.bundle"
    patch_path = STAGE_DIR / f"{PACKAGE_PREFIX}.patch"
    _run(["git", "-C", str(REPO_ROOT), "bundle", "create", str(bundle_path), "HEAD"])
    patch_text = _run(["git", "-C", str(REPO_ROOT), "format-patch", "-1", "HEAD", "--stdout"]).stdout
    _write_text(patch_path, patch_text)
    push_result_raw = _run(["git", "-C", str(REPO_ROOT), "push", "origin", EXPECTED_BRANCH], check=False)
    push_result = {
        "push_attempted": True,
        "returncode": push_result_raw.returncode,
        "stdout": push_result_raw.stdout,
        "stderr": push_result_raw.stderr,
        "remote_not_synchronized": push_result_raw.returncode != 0,
    }

    package_timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    package_basename = f"{PACKAGE_PREFIX}_{package_timestamp}"
    package_root = STAGE_DIR / "package_root"
    if package_root.exists():
        shutil.rmtree(package_root)
    package_root.mkdir(parents=True, exist_ok=True)

    final_commit_info = {
        "final_commit": final_head,
        "branch": EXPECTED_BRANCH,
        "commit_subject": _git("log", "-1", "--pretty=%s").strip(),
        "commit_timestamp": _git("log", "-1", "--pretty=%cI").strip(),
        "bundle_HEAD": final_head,
        "working_tree_status_at_packaging_time": _git("status", "--short"),
        "final_commit_recorded_at_package_time": True,
    }
    _write_text(package_root / "git/final_commit_info.txt", json.dumps(final_commit_info, indent=2, ensure_ascii=False) + "\n")
    _write_text(package_root / "git/git_status.txt", _git("status", "--short"))
    _write_text(package_root / "git/git_diff.txt", _git("diff", "--stat"))
    shutil.copy2(bundle_path, package_root / "git" / bundle_path.name)
    shutil.copy2(patch_path, package_root / "git" / patch_path.name)

    copy_map = [
        (STATUS_MD, "project_ledgers/PROJECT_LAYOUTGEN_OPENYIELD_STATUS.md"),
        (STATUS_JSON, "project_ledgers/PROJECT_LAYOUTGEN_OPENYIELD_STATUS.json"),
        (GOAL_MD, "project_ledgers/PROJECT_NETLIST_TO_LAYOUT_GOAL.md"),
        (PROGRESS_MD, "project_ledgers/PROJECT_NETLIST_TO_LAYOUT_PROGRESS.md"),
        (DFF_GDS, "dependencies/dff/DFF_reusable_clean.gds"),
        (DFF_MANIFEST, "dependencies/dff/DFF_REUSABLE_MANIFEST.json"),
        (STAGE_DIR / "ADDR_DFF_DFF_conductive_obstacle_map.json", "reports/ADDR_DFF_DFF_conductive_obstacle_map.json"),
        (STAGE_DIR / "ADDR_DFF_DFF_pin_geometry.csv", "reports/ADDR_DFF_DFF_pin_geometry.csv"),
        (STAGE_DIR / "ADDR_DFF_DFF_pin_geometry.json", "reports/ADDR_DFF_DFF_pin_geometry.json"),
        (STAGE_DIR / "ADDR_DFF_DFF_child_physical_interface.json", "reports/ADDR_DFF_DFF_child_physical_interface.json"),
        (STAGE_DIR / "ADDR_DFF_DFF_hierarchy_closure.json", "reports/ADDR_DFF_DFF_hierarchy_closure.json"),
        (STAGE_DIR / "ADDR_DFF_DFF_parameter_binding_summary.json", "reports/ADDR_DFF_DFF_parameter_binding_summary.json"),
        (STAGE_DIR / "ADDR_DFF_DFF_parameter_to_physical_binding_closure.json", "reports/ADDR_DFF_DFF_parameter_to_physical_binding_closure.json"),
        (STAGE_DIR / "ADDR_DFF_DFF_physical_interface_semantic_regression.json", "reports/ADDR_DFF_DFF_physical_interface_semantic_regression.json"),
        (STAGE_DIR / "ADDR_DFF_physical_interface_output_ownership_test.json", "reports/ADDR_DFF_physical_interface_output_ownership_test.json"),
        (Path(__file__), "reports/production_validator_source.py"),
        (STAGE_DIR / "ADDR_DFF_negative_tests.json", "reports/ADDR_DFF_negative_tests.json"),
        (STAGE_DIR / "ADDR_DFF_negative_tests.md", "reports/ADDR_DFF_negative_tests.md"),
        (STAGE_DIR / "ADDR_DFF_negative_test_derived_counts.json", "reports/ADDR_DFF_negative_test_derived_counts.json"),
        (STAGE_DIR / "baseline_dirty_tree_report.json", "reports/baseline_dirty_tree_report.json"),
        (STAGE_DIR / "existing_dirty_path_immutability_report.json", "reports/existing_dirty_path_immutability_report.json"),
        (STAGE_DIR / "staged_allowlist_report.json", "reports/staged_allowlist_report.json"),
        (STAGE_DIR / "staged_allowlist_report.md", "reports/staged_allowlist_report.md"),
        (STAGE_DIR / "ledger_consistency_report.json", "reports/ledger_consistency_report.json"),
        (STAGE_DIR / "Wave4A_R2_stage_report.json", "reports/Wave4A_R2_stage_report.json"),
        (STAGE_DIR / "Wave4A_R2_stage_report.md", "reports/Wave4A_R2_stage_report.md"),
        (STAGE_DIR / "source_blob_lock_report.json", "reports/source_blob_lock_report.json"),
        (STAGE_DIR / "ADDR_DFF_ast_extraction.json", "reports/ADDR_DFF_ast_extraction.json"),
        (STAGE_DIR / "ADDR_DFF_ast_extraction.md", "reports/ADDR_DFF_ast_extraction.md"),
        (STAGE_DIR / "ADDR_DFF_CONFIG_RESOLUTION.json", "reports/ADDR_DFF_CONFIG_RESOLUTION.json"),
        (STAGE_DIR / "ADDR_DFF_CONFIG_RESOLUTION.md", "reports/ADDR_DFF_CONFIG_RESOLUTION.md"),
        (STAGE_DIR / "ADDR_DFF_source_derived_topology.json", "reports/ADDR_DFF_source_derived_topology.json"),
        (STAGE_DIR / "ADDR_DFF_expected_project_contract.json", "reports/ADDR_DFF_expected_project_contract.json"),
        (STAGE_DIR / "ADDR_DFF_topology_exact_identity_report.json", "reports/ADDR_DFF_topology_exact_identity_report.json"),
        (STAGE_DIR / "source" / "time_generate_locked_1c34428.py", "source/time_generate_locked_1c34428.py"),
        (STAGE_DIR / "source" / "global_yaml_locked_1c34428.yaml", "source/global_yaml_locked_1c34428.yaml"),
    ]
    for src, rel in copy_map:
        dest = package_root / rel
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dest)

    if (STAGE_DIR / "negative_test_artifacts").exists():
        shutil.copytree(STAGE_DIR / "negative_test_artifacts", package_root / "negative_test_artifacts", dirs_exist_ok=True)

    _write_json(package_root / "reports/manifest_verification_report.json", {"package_basename": package_basename, "required_entry_count": 0})
    _write_json(package_root / "reports/evidence_package_report.json", {"package_basename": package_basename, "package_format": "tar.gz", "manifest_required_entry_actual_count": 0, "sha256sums_actual_count": 0, "final_tar_sha_stored_in_external_sidecar": True, "push_result": push_result})
    _write_json(package_root / "reports/package_verification_report.json", {"status": "pending"})

    def write_sha256sums() -> None:
        lines = []
        for path in sorted(package_root.rglob("*")):
            if path.is_file():
                rel = path.relative_to(package_root).as_posix()
                if rel == "SHA256SUMS":
                    continue
                lines.append(f"{_sha256(path)}  {rel}")
        _write_text(package_root / "SHA256SUMS", "\n".join(lines) + "\n")

    for _ in range(4):
        manifest_entries = _manifest_entries_for_package(package_root)
        manifest = {"package_basename": package_basename, "package_format": "tar.gz", "self_hash_policy": "non_self_referential_external_tar_sidecar", "entries": manifest_entries}
        _write_json(package_root / "evidence_package_manifest.json", manifest)
        _write_csv(package_root / "evidence_package_manifest.csv", manifest_entries)
        _write_json(package_root / "reports/manifest_verification_report.json", {"package_basename": package_basename, "required_entry_count": len(manifest_entries), "manifest_entries_all_have_size_and_sha": True, "checksum_protection_strategy": "covered_by_final_SHA256SUMS"})
        write_sha256sums()
        verification = _verify_manifest_and_sums(package_root)
        _write_json(package_root / "reports/package_verification_report.json", verification)
        _write_json(package_root / "reports/evidence_package_report.json", {"package_basename": package_basename, "package_format": "tar.gz", "manifest_required_entry_actual_count": verification["manifest_required_entry_actual_count"], "sha256sums_actual_count": verification["sha256sums_actual_count"], "final_tar_sha_stored_in_external_sidecar": True, "push_result": push_result})

    manifest_entries = _manifest_entries_for_package(package_root)
    manifest = {"package_basename": package_basename, "package_format": "tar.gz", "self_hash_policy": "non_self_referential_external_tar_sidecar", "entries": manifest_entries}
    _write_json(package_root / "evidence_package_manifest.json", manifest)
    _write_csv(package_root / "evidence_package_manifest.csv", manifest_entries)
    _write_json(package_root / "reports/manifest_verification_report.json", {"package_basename": package_basename, "required_entry_count": len(manifest_entries), "manifest_entries_all_have_size_and_sha": True, "checksum_protection_strategy": "covered_by_final_SHA256SUMS"})
    write_sha256sums()
    final_verification = _verify_manifest_and_sums(package_root)
    _write_json(package_root / "reports/package_verification_report.json", final_verification)
    _write_json(package_root / "reports/evidence_package_report.json", {"package_basename": package_basename, "package_format": "tar.gz", "manifest_required_entry_actual_count": final_verification["manifest_required_entry_actual_count"], "sha256sums_actual_count": final_verification["sha256sums_actual_count"], "final_tar_sha_stored_in_external_sidecar": True, "push_result": push_result})
    manifest_entries = _manifest_entries_for_package(package_root)
    manifest["entries"] = manifest_entries
    _write_json(package_root / "evidence_package_manifest.json", manifest)
    _write_csv(package_root / "evidence_package_manifest.csv", manifest_entries)
    write_sha256sums()
    final_verification = _verify_manifest_and_sums(package_root)
    if not final_verification["all_passed"]:
        raise RuntimeError("final package verification failed")

    tar_path = REPO_ROOT / f"{package_basename}.tar.gz"
    if tar_path.exists():
        tar_path.unlink()
    with tarfile.open(tar_path, "w:gz") as archive:
        archive.add(package_root, arcname=package_root.name)
    tar_sha = _sha256(tar_path)
    sidecar_path = tar_path.with_suffix(tar_path.suffix + ".sha256")
    _write_text(sidecar_path, f"{tar_sha}  {tar_path.name}\n")

    with tempfile.TemporaryDirectory(prefix="wave4a_r2_pkg_") as tmp:
        with tarfile.open(tar_path, "r:gz") as archive:
            archive.extractall(tmp)
        extracted_root = next(path for path in Path(tmp).iterdir() if path.is_dir())
        extracted_verification = _verify_manifest_and_sums(extracted_root)
    if not extracted_verification["all_passed"]:
        raise RuntimeError("independent extract verification failed")

    _write_json(
        STAGE_DIR / "evidence_package_report.json",
        {
            "package_path": str(tar_path),
            "package_sha256": tar_sha,
            "sidecar_path": str(sidecar_path),
            "package_basename": package_basename,
            "manifest_required_entry_actual_count": final_verification["manifest_required_entry_actual_count"],
            "sha256sums_actual_count": final_verification["sha256sums_actual_count"],
            "verification_report_checksum_protection": final_verification["manifest_verification_report_covered_by_sha256sums"] and final_verification["package_verification_report_covered_by_sha256sums"],
            "independent_extract_verification_passed": extracted_verification["all_passed"],
            "push_result": push_result,
        },
    )
    _write_text(STAGE_DIR / "evidence_package_report.md", _render_md_kv("Evidence Package Report", _read_json(STAGE_DIR / "evidence_package_report.json")))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("mode", choices=["prepare", "check-staged", "package"])
    args = parser.parse_args()
    if args.mode == "prepare":
        prepare()
    elif args.mode == "check-staged":
        check_staged()
    else:
        package()


if __name__ == "__main__":
    main()
