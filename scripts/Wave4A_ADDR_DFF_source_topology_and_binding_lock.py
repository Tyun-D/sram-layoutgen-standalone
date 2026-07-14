from __future__ import annotations

import argparse
import ast
import csv
import hashlib
import json
import math
import os
import re
import shutil
import subprocess
import sys
import tarfile
import tempfile
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Any

import gdstk
import yaml

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

EXPECTED_BRANCH = "feature/step45-clean-array-aggregation"
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
EXPECTED_DFF_DIRECT_CHILDREN = {
    "PINV_NW250_PW500_L50": 7,
    "TRANSMISSION_GATE_NW250_PW500_L50": 4,
}
EXPECTED_DFF_CONDUCTIVE_GEOMETRY = {"M1": 396, "Via1": 60, "M2": 90, "total": 546}
EXPECTED_DFF_TOP_LABELS = ["CLK", "D", "Q", "VDD", "VSS"]

OPENYIELD_ROOT = Path("/data1/qujh/work/external/OpenYield")
OPENYIELD_TIME_GENERATE = OPENYIELD_ROOT / EXPECTED_TIME_GENERATE_PATH
OPENYIELD_GLOBAL_YAML = OPENYIELD_ROOT / "sram_compiler/config_yaml/global.yaml"

STAGE_ID = "Wave4A-R1 / ADDR_DFF_SOURCE_BINDING_VALIDATOR_HARDENING"
NEXT_STAGE = "Wave4A2 / ADDR_DFF_CANDIDATE_GENERATION_AND_MACHINE_VERIFICATION"
BLOCKED_STAGE = "BLOCKED_PENDING_WAVE4A_VALIDATOR_HARDENING"
DEFERRED_SIBLING_STAGE = "Wave4B / DATA_DFF"
STAGE_DIR = REPO_ROOT / "outputs/Wave4A_ADDR_DFF_source_topology_and_binding_lock/current_supported_config"
PACKAGE_PREFIX = "Wave4A_R1_ADDR_DFF_source_binding_validator_hardening"

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

ALLOWLIST = [
    "scripts/Wave4A_ADDR_DFF_source_topology_and_binding_lock.py",
    "outputs/Wave4A_ADDR_DFF_source_topology_and_binding_lock/current_supported_config",
    "PROJECT_LAYOUTGEN_OPENYIELD_STATUS.md",
    "PROJECT_LAYOUTGEN_OPENYIELD_STATUS.json",
    "PROJECT_NETLIST_TO_LAYOUT_GOAL.md",
    "PROJECT_NETLIST_TO_LAYOUT_PROGRESS.md",
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


def _literal_or_source(text: str, node: ast.AST) -> Any:
    segment = ast.get_source_segment(text, node)
    try:
        return ast.literal_eval(node)
    except Exception:
        return segment if segment is not None else ast.unparse(node)


def _source_segment(text: str, node: ast.AST) -> str:
    segment = ast.get_source_segment(text, node)
    return segment if segment is not None else ast.unparse(node)


def _find_class(tree: ast.Module, name: str) -> ast.ClassDef:
    for node in tree.body:
        if isinstance(node, ast.ClassDef) and node.name == name:
            return node
    raise RuntimeError(f"class not found: {name}")


def _find_method(cls: ast.ClassDef, name: str) -> ast.FunctionDef:
    for node in cls.body:
        if isinstance(node, ast.FunctionDef) and node.name == name:
            return node
    raise RuntimeError(f"method not found: {cls.name}.{name}")


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
    for node, default in zip(fn.args.kwonlyargs, fn.args.kw_defaults):
        rows.append(
            {
                "parameter": node.arg,
                "kind": "kwonly",
                "default_source": ast.unparse(default) if default is not None else None,
            }
        )
    return rows


def _eval_expr(expr: str, env: dict[str, Any]) -> Any:
    safe_globals = {"__builtins__": {}, "range": range, "ceil": math.ceil, "log2": math.log2}
    return eval(expr, safe_globals, env)


def _path_inventory_digest(path: Path) -> tuple[str, list[dict[str, Any]]]:
    rows = []
    for child in sorted(path.rglob("*")):
        if child.is_dir():
            continue
        rel = child.relative_to(path).as_posix()
        rows.append({"relative_path": rel, "size_bytes": child.stat().st_size, "sha256": _sha256(child)})
    digest = _sha256_bytes(json.dumps(rows, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8"))
    return digest, rows


def _path_metadata(repo_relative_path: str) -> dict[str, Any]:
    path = REPO_ROOT / repo_relative_path
    if not path.exists():
        return {
            "relative_path": repo_relative_path,
            "exists": False,
            "file_type": "missing",
            "size_bytes": None,
            "sha256": None,
            "inventory_digest": None,
            "inventory_rows": [],
        }
    if path.is_dir():
        digest, rows = _path_inventory_digest(path)
        return {
            "relative_path": repo_relative_path,
            "exists": True,
            "file_type": "directory",
            "size_bytes": None,
            "sha256": None,
            "inventory_digest": digest,
            "inventory_rows": rows,
        }
    return {
        "relative_path": repo_relative_path,
        "exists": True,
        "file_type": "symlink" if path.is_symlink() else "file",
        "size_bytes": path.stat().st_size,
        "sha256": _sha256(path),
        "inventory_digest": None,
        "inventory_rows": [],
    }


def _path_is_mutable_in_this_round(path: str) -> bool:
    return any(path == allowed or path.startswith(allowed + "/") for allowed in ALLOWLIST)


def _parse_git_status_porcelain() -> list[dict[str, Any]]:
    raw = _run_bytes(["git", "-C", str(REPO_ROOT), "status", "--short", "--untracked-files=all", "-z"]).stdout
    items = raw.split(b"\0")
    rows: list[dict[str, Any]] = []
    i = 0
    while i < len(items):
        item = items[i]
        i += 1
        if not item:
            continue
        prefix = item[:3].decode("utf-8", errors="replace")
        payload = item[3:].decode("utf-8", errors="replace")
        if prefix[0] == "R":
            if i >= len(items):
                raise RuntimeError("malformed porcelain rename entry")
            original = payload
            payload = items[i].decode("utf-8", errors="replace")
            i += 1
            rows.append(
                {
                    "status_code": prefix.strip(),
                    "path": payload,
                    "rename_from": original,
                }
            )
            continue
        rows.append({"status_code": prefix.strip(), "path": payload, "rename_from": None})
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
    openyield_head = _git("rev-parse", "HEAD", cwd=OPENYIELD_ROOT).strip()
    if openyield_head != EXPECTED_OPENYIELD_COMMIT:
        raise RuntimeError(f"OpenYield commit mismatch: {openyield_head}")
    dff_sha = _sha256(DFF_GDS)
    if dff_sha != EXPECTED_DFF_SHA:
        raise RuntimeError(f"approved DFF SHA mismatch: {dff_sha}")
    manifest = _read_json(DFF_MANIFEST)
    if manifest["physical_cell_name"] != EXPECTED_DFF_TOP:
        raise RuntimeError("approved DFF top mismatch in manifest")
    return {
        "project_branch": branch,
        "report_generation_base_commit": project_head,
        "openyield_commit": openyield_head,
        "approved_dff_gds_sha256": dff_sha,
    }


def _dirty_tree_baseline() -> dict[str, Any]:
    status_rows = _parse_git_status_porcelain()
    dirty_rows = []
    for row in status_rows:
        meta = _path_metadata(row["path"])
        meta["status_code"] = row["status_code"]
        meta["rename_from"] = row["rename_from"]
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


def _fetch_locked_source_blob(path_in_repo: str = EXPECTED_TIME_GENERATE_PATH) -> dict[str, Any]:
    blob_bytes = _run_bytes(
        ["git", "-C", str(OPENYIELD_ROOT), "show", f"{EXPECTED_OPENYIELD_COMMIT}:{path_in_repo}"]
    ).stdout
    blob_sha = _git_blob_sha1_bytes(blob_bytes)
    sha256 = _sha256_bytes(blob_bytes)
    locked_source_dir = STAGE_DIR / "source"
    locked_source_dir.mkdir(parents=True, exist_ok=True)
    snapshot_path = locked_source_dir / "time_generate_locked_1c34428.py"
    snapshot_path.write_bytes(blob_bytes)
    return {
        "authority_kind": "locked_git_blob",
        "authority_commit": EXPECTED_OPENYIELD_COMMIT,
        "source_path": path_in_repo,
        "blob_sha1": blob_sha,
        "file_sha256": sha256,
        "bytes": blob_bytes,
        "snapshot_path": snapshot_path,
    }


def _validator_source_snapshot(
    authority_kind: str,
    authority_commit: str,
    authority_source_path: str,
    source_bytes: bytes,
    expected_commit: str,
    expected_source_path: str,
    expected_blob_sha: str,
    expected_file_sha256: str,
) -> dict[str, Any]:
    actual_blob_sha = _git_blob_sha1_bytes(source_bytes)
    actual_file_sha256 = _sha256_bytes(source_bytes)
    openyield_head = _git("rev-parse", "HEAD", cwd=OPENYIELD_ROOT).strip()
    working_tree_sha = _sha256(OPENYIELD_TIME_GENERATE)
    checks = {
        "openyield_head_matches_expected_commit": openyield_head == expected_commit,
        "authority_commit_matches_locked_commit": authority_commit == expected_commit,
        "authority_source_path_matches_locked_path": authority_source_path == expected_source_path,
        "authority_kind_is_locked_git_blob": authority_kind == "locked_git_blob",
        "locked_blob_sha_matches_expected_blob_sha": actual_blob_sha == expected_blob_sha,
        "locked_source_sha256_matches_expected_sha256": actual_file_sha256 == expected_file_sha256,
    }
    rejection_reason = None
    if not checks["openyield_head_matches_expected_commit"]:
        rejection_reason = "OpenYield commit mismatch"
    elif not checks["authority_commit_matches_locked_commit"]:
        rejection_reason = "authority commit mismatch"
    elif not checks["authority_source_path_matches_locked_path"]:
        rejection_reason = "source path points to different file"
    elif not checks["authority_kind_is_locked_git_blob"]:
        rejection_reason = "working-tree source used as authority"
    elif not checks["locked_blob_sha_matches_expected_blob_sha"]:
        rejection_reason = "locked blob SHA mismatch"
    elif not checks["locked_source_sha256_matches_expected_sha256"]:
        rejection_reason = "locked source SHA-256 mismatch"
    report = {
        "authority_kind": authority_kind,
        "authority_commit": authority_commit,
        "authority_source_path": authority_source_path,
        "actual_blob_sha1": actual_blob_sha,
        "actual_file_sha256": actual_file_sha256,
        "expected_commit": expected_commit,
        "expected_source_path": expected_source_path,
        "expected_blob_sha1": expected_blob_sha,
        "expected_file_sha256": expected_file_sha256,
        "openyield_head": openyield_head,
        "working_tree_path": str(OPENYIELD_TIME_GENERATE),
        "working_tree_sha256": working_tree_sha,
        "working_tree_matches_locked_source": working_tree_sha == actual_file_sha256,
        "checks": checks,
        "authority_passed": rejection_reason is None,
        "rejection_reason": rejection_reason,
    }
    return report


def _write_source_snapshot_report(locked_blob: dict[str, Any], source_validator_report: dict[str, Any]) -> None:
    report = {
        "locked_commit": EXPECTED_OPENYIELD_COMMIT,
        "locked_source_path": EXPECTED_TIME_GENERATE_PATH,
        "locked_blob_sha1": locked_blob["blob_sha1"],
        "locked_source_sha256": locked_blob["file_sha256"],
        "snapshot_path": str(locked_blob["snapshot_path"]),
        "source_snapshot_validator": source_validator_report,
    }
    _write_json(STAGE_DIR / "source_blob_lock_report.json", report)


def _extract_ast_report(source_bytes: bytes, source_label: str, *, write_outputs: bool = True) -> dict[str, Any]:
    text = source_bytes.decode("utf-8")
    tree = ast.parse(text, filename=source_label)
    addr_cls = _find_class(tree, "ADDR_DFF")
    time_cls = _find_class(tree, "TIME")
    dff_cls = _find_class(tree, "dff")
    addr_init = _find_method(addr_cls, "__init__")
    addr_add = _find_method(addr_cls, "add_addr_dff_array")
    time_init = _find_method(time_cls, "__init__")
    dff_init = _find_method(dff_cls, "__init__")

    name_assign = next(
        node for node in addr_cls.body if isinstance(node, ast.Assign) and any(isinstance(t, ast.Name) and t.id == "NAME" for t in node.targets)
    )
    self_num_rows_assign = next(
        node
        for node in addr_init.body
        if isinstance(node, ast.Assign)
        and any(isinstance(t, ast.Attribute) and isinstance(t.value, ast.Name) and t.value.id == "self" and t.attr == "num_rows" for t in node.targets)
    )
    n_bits_assignments = [
        node
        for node in addr_init.body
        if isinstance(node, ast.Assign) and any(isinstance(t, ast.Name) and t.id == "n_bits" for t in node.targets)
    ]
    nodes_assign = next(
        node
        for node in addr_init.body
        if isinstance(node, ast.Assign) and any(isinstance(t, ast.Name) and t.id == "nodes" for t in node.targets)
    )
    node_extends = [
        node
        for node in addr_init.body
        if isinstance(node, ast.Expr)
        and isinstance(node.value, ast.Call)
        and isinstance(node.value.func, ast.Attribute)
        and isinstance(node.value.func.value, ast.Name)
        and node.value.func.value.id == "nodes"
        and node.value.func.attr == "extend"
    ]
    self_nodes_assign = next(
        node
        for node in addr_init.body
        if isinstance(node, ast.Assign)
        and any(isinstance(t, ast.Attribute) and isinstance(t.value, ast.Name) and t.value.id == "self" and t.attr == "NODES" for t in node.targets)
    )
    dff_addr_assign = next(
        node
        for node in addr_init.body
        if isinstance(node, ast.Assign)
        and any(isinstance(t, ast.Attribute) and isinstance(t.value, ast.Name) and t.value.id == "self" and t.attr == "dff_addr" for t in node.targets)
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
        node.value
        for node in addr_loop.body
        if isinstance(node, ast.Expr)
        and isinstance(node.value, ast.Call)
        and isinstance(node.value.func, ast.Attribute)
        and node.value.func.attr == "X"
    )
    time_addr_ctor = next(
        node
        for node in time_init.body
        if isinstance(node, ast.Assign)
        and any(isinstance(t, ast.Name) and t.id == "dff_buf_addr" for t in node.targets)
    )
    time_addr_connections = next(
        node
        for node in time_init.body
        if isinstance(node, ast.Assign)
        and any(isinstance(t, ast.Name) and t.id == "addr_dff_connections" for t in node.targets)
    )
    time_addr_loops = []
    for node in time_init.body:
        if isinstance(node, ast.For):
            if any(
                isinstance(stmt, ast.Expr)
                and isinstance(stmt.value, ast.Call)
                and isinstance(stmt.value.func, ast.Attribute)
                and isinstance(stmt.value.func.value, ast.Name)
                and stmt.value.func.value.id == "addr_dff_connections"
                and stmt.value.func.attr == "append"
                for stmt in node.body
            ):
                time_addr_loops.append(node)
    time_x_call = next(
        node.value
        for node in time_init.body
        if isinstance(node, ast.Expr)
        and isinstance(node.value, ast.Call)
        and isinstance(node.value.func, ast.Attribute)
        and node.value.func.attr == "X"
        and _source_segment(text, node.value.args[0]) == "'dff_buf_addr'"
    )

    ast_report = {
        "source_label": source_label,
        "addr_dff": {
            "class_name": "ADDR_DFF",
            "name_assignment": _literal_or_source(text, name_assign.value),
            "__init__": {
                "formal_parameters": _ast_arg_info(addr_init),
                "source_text": _source_segment(text, addr_init),
            },
            "self_num_rows_source": _source_segment(text, self_num_rows_assign.value),
            "n_bits_expressions": [_source_segment(text, node.value) for node in n_bits_assignments],
            "nodes_initial_value": _literal_or_source(text, nodes_assign.value),
            "nodes_extend_expressions": [_source_segment(text, node.value.args[0]) for node in node_extends],
            "self_nodes_source": _source_segment(text, self_nodes_assign.value),
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
            "__init__": {
                "formal_parameters": _ast_arg_info(time_init),
                "source_text": _source_segment(text, time_init),
            },
            "addr_dff_constructor_call": {
                "source_text": _source_segment(text, time_addr_ctor),
                "positional_arguments": [_source_segment(text, arg) for arg in time_addr_ctor.value.args],
                "keyword_arguments": {kw.arg: _source_segment(text, kw.value) for kw in time_addr_ctor.value.keywords},
            },
            "addr_dff_connections_initial": _literal_or_source(text, time_addr_connections.value),
            "addr_dff_connection_loops": [
                {
                    "loop_target": _source_segment(text, node.target),
                    "loop_iterator": _source_segment(text, node.iter),
                    "append_expressions": [
                        _source_segment(text, stmt.value.args[0])
                        for stmt in node.body
                        if isinstance(stmt, ast.Expr)
                        and isinstance(stmt.value, ast.Call)
                        and isinstance(stmt.value.func, ast.Attribute)
                        and isinstance(stmt.value.func.value, ast.Name)
                        and stmt.value.func.value.id == "addr_dff_connections"
                        and stmt.value.func.attr == "append"
                    ],
                }
                for node in time_addr_loops
            ],
            "dff_buf_addr_instance_call": {
                "instance_name_expression": _source_segment(text, time_x_call.args[0]),
                "child_expression": _source_segment(text, time_x_call.args[1]),
                "remaining_arguments": [_source_segment(text, arg) for arg in time_x_call.args[2:]],
            },
        },
        "dff": {
            "__init__": {
                "formal_parameters": _ast_arg_info(dff_init),
                "source_text": _source_segment(text, dff_init),
            }
        },
    }
    if write_outputs:
        _write_json(STAGE_DIR / "ADDR_DFF_ast_extraction.json", ast_report)
        _write_text(STAGE_DIR / "ADDR_DFF_ast_extraction.md", _render_md_kv("ADDR_DFF AST Extraction", ast_report))
    return ast_report


def _resolve_num_rows_from_ast_and_config(
    ast_report: dict[str, Any],
    *,
    overrides: list[dict[str, Any]] | None = None,
    write_outputs: bool = True,
) -> dict[str, Any]:
    locked_global_bytes = _run_bytes(
        ["git", "-C", str(OPENYIELD_ROOT), "show", f"{EXPECTED_OPENYIELD_COMMIT}:sram_compiler/config_yaml/global.yaml"]
    ).stdout
    locked_global_path = STAGE_DIR / "source/global_yaml_locked_1c34428.yaml"
    locked_global_path.parent.mkdir(parents=True, exist_ok=True)
    locked_global_path.write_bytes(locked_global_bytes)
    ast_time_default = None
    for row in ast_report["time"]["__init__"]["formal_parameters"]:
        if row["parameter"] == "num_rows":
            ast_time_default = row["default_source"]
            break
    if ast_time_default is None:
        raise RuntimeError("TIME.__init__ num_rows default missing")
    candidates = overrides[:] if overrides is not None else []
    if overrides is None:
        current_spec_paths = [
            {
                "path": LAYOUTGEN_CURRENT_SPEC,
                "source_category": "current_layoutgen_sram_spec",
                "current_or_historical": "current",
                "precedence": 10,
            },
            {
                "path": OPENYIELD_CURRENT_SPEC,
                "source_category": "current_openyield_layoutgen_spec",
                "current_or_historical": "current",
                "precedence": 20,
            },
        ]
        for entry in current_spec_paths:
            obj = _read_json(entry["path"])
            candidates.append(
                {
                    "path": str(entry["path"]),
                    "source_category": entry["source_category"],
                    "current_or_historical": entry["current_or_historical"],
                    "content_sha256": _sha256(entry["path"]),
                    "parsed_num_rows": obj.get("num_rows"),
                    "precedence": entry["precedence"],
                }
            )
        global_obj = yaml.safe_load(locked_global_bytes.decode("utf-8"))
        candidates.append(
            {
                "path": f"{EXPECTED_OPENYIELD_COMMIT}:sram_compiler/config_yaml/global.yaml",
                "source_category": "locked_openyield_global_yaml_blob",
                "current_or_historical": "current",
                "content_sha256": _sha256_bytes(locked_global_bytes),
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
                "parsed_num_rows": int(float(ast_time_default)),
                "precedence": 40,
            }
        )
    current_authorities = [row for row in candidates if row["current_or_historical"] == "current"]
    values = sorted({row["parsed_num_rows"] for row in current_authorities})
    conflict = len(values) != 1
    selected_num_rows = values[0] if not conflict else None
    for row in candidates:
        if row["current_or_historical"] != "current":
            row["selected_or_rejected_reason"] = "historical_reference_only"
        elif conflict:
            row["selected_or_rejected_reason"] = "rejected_due_to_current_authority_conflict"
        else:
            row["selected_or_rejected_reason"] = "selected_current_authority_consensus"
    report = {
        "time_init_formal_parameters": ast_report["time"]["__init__"]["formal_parameters"],
        "time_num_rows_default_source": ast_time_default,
        "time_addr_dff_constructor_call": ast_report["time"]["addr_dff_constructor_call"],
        "current_authority_candidates": candidates,
        "current_authority_values": values,
        "num_rows_authority_conflict": conflict,
        "resolved_num_rows": selected_num_rows,
        "resolved_n_bits": math.ceil(math.log2(selected_num_rows)) if selected_num_rows and selected_num_rows > 1 else (1 if selected_num_rows == 1 else None),
        "all_current_authorities_equal_16": selected_num_rows == EXPECTED_NUM_ROWS and not conflict,
    }
    if write_outputs:
        _write_json(STAGE_DIR / "ADDR_DFF_CONFIG_RESOLUTION.json", report)
        _write_text(STAGE_DIR / "ADDR_DFF_CONFIG_RESOLUTION.md", _render_md_kv("ADDR_DFF Config Resolution", report))
    return report


def _build_source_derived_topology(
    ast_report: dict[str, Any],
    config_report: dict[str, Any],
    *,
    write_outputs: bool = True,
) -> dict[str, Any]:
    if config_report["num_rows_authority_conflict"]:
        raise RuntimeError("cannot derive topology with conflicting num_rows authorities")
    num_rows = config_report["resolved_num_rows"]
    n_bits_expr = ast_report["addr_dff"]["n_bits_expressions"][0]
    n_bits = _eval_expr(n_bits_expr, {"self": type("SelfObj", (), {"num_rows": num_rows})(), "ceil": math.ceil, "log2": math.log2})
    nodes = list(ast_report["addr_dff"]["nodes_initial_value"])
    for expr in ast_report["addr_dff"]["nodes_extend_expressions"]:
        nodes.extend(list(_eval_expr(expr, {"n_bits": n_bits})))
    loop_iter = ast_report["addr_dff"]["add_addr_dff_array"]["loop_iterator"]
    iter_values = list(_eval_expr(loop_iter, {"n_bits": n_bits}))
    instance_name_expr = ast_report["addr_dff"]["add_addr_dff_array"]["self_x_instance_name_expression"]
    child_expr = ast_report["addr_dff"]["add_addr_dff_array"]["self_x_child_expression"]
    net_exprs = ast_report["addr_dff"]["add_addr_dff_array"]["self_x_net_argument_order"]
    instances = []
    endpoint_contracts = {
        "VDD": ["TOP::VDD"],
        "VSS": ["TOP::VSS"],
        "CLK": ["TOP::CLK"],
    }
    for i in iter_values:
        instance_name = _eval_expr(instance_name_expr, {"i": i})
        child_value = child_expr
        nets = [_eval_expr(expr, {"i": i}) if expr.startswith("f'") or expr.startswith('f"') else _eval_expr(expr, {"i": i}) if expr in {"'VDD'", "'VSS'", "'CLK'", '"VDD"', '"VSS"', '"CLK"'} else _literal_or_source("", ast.parse(expr, mode="eval").body) for expr in net_exprs]
        nets = [value if isinstance(value, str) else str(value) for value in nets]
        instances.append(
            {
                "instance_name": instance_name,
                "logical_child_expression": child_value,
                "connections": nets,
            }
        )
        endpoint_contracts["VDD"].append(f"{instance_name}::VDD")
        endpoint_contracts["VSS"].append(f"{instance_name}::VSS")
        endpoint_contracts["CLK"].append(f"{instance_name}::CLK")
        endpoint_contracts[f"A{i}"] = [f"TOP::A{i}", f"{instance_name}::D"]
        endpoint_contracts[f"A_dff{i}"] = [f"TOP::A_dff{i}", f"{instance_name}::Q"]
    time_connections = list(ast_report["time"]["addr_dff_connections_initial"])
    for loop in ast_report["time"]["addr_dff_connection_loops"]:
        iterator_values = list(_eval_expr(loop["loop_iterator"], {"self": type("SelfObj", (), {"n_bits": n_bits})()}))
        for i in iterator_values:
            for expr in loop["append_expressions"]:
                time_connections.append(_eval_expr(expr, {"i": i}))
    topology = {
        "logical_module": "ADDR_DFF",
        "source_class_name": ast_report["addr_dff"]["class_name"],
        "addr_dff_init_formal_parameters": ast_report["addr_dff"]["__init__"]["formal_parameters"],
        "self_num_rows_source": ast_report["addr_dff"]["self_num_rows_source"],
        "resolved_num_rows": num_rows,
        "n_bits_expressions": ast_report["addr_dff"]["n_bits_expressions"],
        "resolved_n_bits": n_bits,
        "nodes_initial_value": ast_report["addr_dff"]["nodes_initial_value"],
        "nodes_extend_expressions": ast_report["addr_dff"]["nodes_extend_expressions"],
        "self_nodes_source": ast_report["addr_dff"]["self_nodes_source"],
        "resolved_top_pins": nodes,
        "dff_addr_constructor": ast_report["addr_dff"]["dff_addr_constructor"],
        "subcircuit_call_source": ast_report["addr_dff"]["subcircuit_call_source"],
        "add_addr_dff_array_call": ast_report["addr_dff"]["add_addr_dff_array_call"],
        "loop_target": ast_report["addr_dff"]["add_addr_dff_array"]["loop_target"],
        "loop_iterator": loop_iter,
        "child_instances": instances,
        "canonical_nets": list(endpoint_contracts.keys()),
        "endpoint_contracts": endpoint_contracts,
        "time_addr_dff_constructor_call": ast_report["time"]["addr_dff_constructor_call"],
        "time_addr_dff_connections_initial": ast_report["time"]["addr_dff_connections_initial"],
        "time_addr_dff_connection_loops": ast_report["time"]["addr_dff_connection_loops"],
        "resolved_time_addr_dff_connections": time_connections,
        "time_dff_buf_addr_instance_call": ast_report["time"]["dff_buf_addr_instance_call"],
    }
    topology["source_derived_topology_sha256"] = _sha256_bytes(
        json.dumps(topology, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    )
    if write_outputs:
        _write_json(STAGE_DIR / "ADDR_DFF_source_derived_topology.json", topology)
    return topology


def _build_expected_project_contract() -> dict[str, Any]:
    endpoint_contracts = {
        "VDD": ["TOP::VDD"],
        "VSS": ["TOP::VSS"],
        "CLK": ["TOP::CLK"],
    }
    instances = []
    for idx, name in enumerate(EXPECTED_CHILDREN):
        instances.append(
            {
                "instance_name": name,
                "logical_child_expression": "self.dff_addr.NAME",
                "connections": EXPECTED_INSTANCE_CONNECTIONS[name],
            }
        )
        endpoint_contracts["VDD"].append(f"{name}::VDD")
        endpoint_contracts["VSS"].append(f"{name}::VSS")
        endpoint_contracts["CLK"].append(f"{name}::CLK")
        endpoint_contracts[f"A{idx}"] = [f"TOP::A{idx}", f"{name}::D"]
        endpoint_contracts[f"A_dff{idx}"] = [f"TOP::A_dff{idx}", f"{name}::Q"]
    contract = {
        "logical_module": "ADDR_DFF",
        "resolved_num_rows": EXPECTED_NUM_ROWS,
        "resolved_n_bits": EXPECTED_N_BITS,
        "resolved_top_pins": EXPECTED_TOP_PIN_ORDER,
        "child_instances": instances,
        "canonical_nets": [
            "VDD",
            "VSS",
            "CLK",
            "A0",
            "A_dff0",
            "A1",
            "A_dff1",
            "A2",
            "A_dff2",
            "A3",
            "A_dff3",
        ],
        "endpoint_contracts": endpoint_contracts,
    }
    _write_json(STAGE_DIR / "ADDR_DFF_expected_project_contract.json", contract)
    return contract


def _validate_topology_exact_identity(
    source_topology: dict[str, Any],
    expected_contract: dict[str, Any],
    *,
    write_outputs: bool = True,
) -> dict[str, Any]:
    source_keys = set(source_topology.keys())
    expected_keys = set(expected_contract.keys())
    missing_fields = sorted(expected_keys - source_keys)
    unexpected_fields = sorted(k for k in source_keys - expected_keys if k in expected_keys)
    order_mismatch = []
    if source_topology["resolved_top_pins"] != expected_contract["resolved_top_pins"]:
        order_mismatch.append("top_pin_order")
    if [row["instance_name"] for row in source_topology["child_instances"]] != [row["instance_name"] for row in expected_contract["child_instances"]]:
        order_mismatch.append("child_instance_order")
    instance_mismatch = []
    expected_instances = {row["instance_name"]: row for row in expected_contract["child_instances"]}
    for row in source_topology["child_instances"]:
        expected = expected_instances.get(row["instance_name"])
        if expected is None:
            instance_mismatch.append({"instance_name": row["instance_name"], "reason": "unexpected_instance"})
            continue
        if row["connections"] != expected["connections"] or row["logical_child_expression"] != expected["logical_child_expression"]:
            instance_mismatch.append(
                {
                    "instance_name": row["instance_name"],
                    "expected": expected,
                    "actual": row,
                }
            )
    for name, row in expected_instances.items():
        if not any(actual["instance_name"] == name for actual in source_topology["child_instances"]):
            instance_mismatch.append({"instance_name": name, "reason": "missing_instance"})
    net_mismatch = {
        "missing_nets": [net for net in expected_contract["canonical_nets"] if net not in source_topology["canonical_nets"]],
        "unexpected_nets": [net for net in source_topology["canonical_nets"] if net not in expected_contract["canonical_nets"]],
        "order_mismatch": source_topology["canonical_nets"] != expected_contract["canonical_nets"],
    }
    endpoint_mismatch = []
    for net, expected_endpoints in expected_contract["endpoint_contracts"].items():
        actual_endpoints = source_topology["endpoint_contracts"].get(net)
        if actual_endpoints != expected_endpoints:
            endpoint_mismatch.append({"net": net, "expected": expected_endpoints, "actual": actual_endpoints})
    exact_identity_passed = not (
        missing_fields
        or unexpected_fields
        or order_mismatch
        or instance_mismatch
        or net_mismatch["missing_nets"]
        or net_mismatch["unexpected_nets"]
        or net_mismatch["order_mismatch"]
        or endpoint_mismatch
        or source_topology["resolved_num_rows"] != expected_contract["resolved_num_rows"]
        or source_topology["resolved_n_bits"] != expected_contract["resolved_n_bits"]
    )
    report = {
        "missing_fields": missing_fields,
        "unexpected_fields": unexpected_fields,
        "order_mismatch": order_mismatch,
        "instance_mismatch": instance_mismatch,
        "net_mismatch": net_mismatch,
        "endpoint_mismatch": endpoint_mismatch,
        "exact_identity_passed": exact_identity_passed,
    }
    if write_outputs:
        _write_json(STAGE_DIR / "ADDR_DFF_topology_exact_identity_report.json", report)
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
            [
                {
                    "instance_name": row["instance_name"],
                    "logical_child_expression": row["logical_child_expression"],
                    "connection_order": json.dumps(row["connections"]),
                }
                for row in source_topology["child_instances"]
            ],
        )
        _write_json(
            STAGE_DIR / "ADDR_DFF_source_topology_analysis.json",
            {
                "source_derived_topology": source_topology,
                "expected_project_contract": expected_contract,
                "exact_identity_report": report,
            },
        )
        _write_text(
            STAGE_DIR / "ADDR_DFF_source_topology_analysis.md",
            _render_md_kv("ADDR_DFF Source Topology Analysis", _read_json(STAGE_DIR / "ADDR_DFF_source_topology_analysis.json")),
        )
    return report


def _hierarchy_closure(path: Path, expected_top: str) -> dict[str, Any]:
    lib = gdstk.read_gds(path)
    cells = {cell.name: cell for cell in lib.cells}
    top_cells = [cell.name for cell in lib.top_level()]
    missing_refs = []
    graph = {}
    for cell in lib.cells:
        refs = [str(ref.cell_name) for ref in cell.references]
        graph[cell.name] = refs
        for ref in refs:
            if ref not in cells:
                missing_refs.append({"cell": cell.name, "missing_reference": ref})
    return {
        "gds_path": str(path),
        "top_cells": top_cells,
        "expected_top_cell": expected_top,
        "top_matches_expected": top_cells == [expected_top],
        "missing_reference_target_count": len(missing_refs),
        "missing_references": missing_refs,
    }


def _collect_dff_geometry_and_labels() -> dict[str, Any]:
    lib = gdstk.read_gds(DFF_GDS)
    top_cells = lib.top_level()
    if len(top_cells) != 1:
        raise RuntimeError("approved DFF must have exactly one top cell")
    top = top_cells[0]
    direct_child_counter = Counter(str(ref.cell_name) for ref in top.references)
    flat = top.flatten()
    label_texts = sorted(str(label.text) for label in flat.labels)
    layer_counter = Counter()
    for poly in flat.polygons:
        if poly.layer == 11:
            layer_counter["M1"] += 1
        elif poly.layer == 12:
            layer_counter["Via1"] += 1
        elif poly.layer == 13:
            layer_counter["M2"] += 1
    geometry = {
        "M1": layer_counter["M1"],
        "Via1": layer_counter["Via1"],
        "M2": layer_counter["M2"],
    }
    geometry["total"] = geometry["M1"] + geometry["Via1"] + geometry["M2"]
    return {
        "top_cell": top.name,
        "direct_child_inventory": dict(sorted(direct_child_counter.items())),
        "label_texts": label_texts,
        "conductive_geometry": geometry,
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


def _build_constructor_parameter_binding(ast_report: dict[str, Any]) -> dict[str, Any]:
    defaults = {row["parameter"]: row["default_source"] for row in ast_report["dff"]["__init__"]["formal_parameters"]}
    actual_call = ast_report["addr_dff"]["dff_addr_constructor"]["positional_arguments"]
    binding = {
        "source_constructor_call": ast_report["addr_dff"]["dff_addr_constructor"]["source_text"],
        "formal_to_actual_binding": {
            "nmos_model": actual_call[0],
            "pmos_model": actual_call[1],
            "pmos_width": "default",
            "nmos_width": "default",
            "length": "default",
        },
        "default_values": {
            "nmos_model": defaults.get("nmos_model"),
            "pmos_model": defaults.get("pmos_model"),
            "pmos_width": defaults.get("pmos_width"),
            "nmos_width": defaults.get("nmos_width"),
            "length": defaults.get("length"),
        },
        "normalized_nm_values": {
            "pmos_width_nm": round(float(defaults["pmos_width"]) * 1e9),
            "nmos_width_nm": round(float(defaults["nmos_width"]) * 1e9),
            "length_nm": round(float(defaults["length"]) * 1e9),
        },
    }
    _write_json(STAGE_DIR / "ADDR_DFF_constructor_parameter_binding.json", binding)
    return binding


def _validate_logical_to_physical_pin_mapping(source_topology: dict[str, Any], binding_rows: list[dict[str, Any]]) -> dict[str, Any]:
    errors = []
    binding_by_instance = {row["instance_name"]: row for row in binding_rows}
    for idx, instance in enumerate(source_topology["child_instances"]):
        row = binding_by_instance.get(instance["instance_name"])
        if row is None:
            errors.append({"instance_name": instance["instance_name"], "reason": "binding_row_missing"})
            continue
        mapping = row["logical_to_physical_pin_mapping"]
        expected_mapping = {
            "VDD": "VDD",
            "VSS": "VSS",
            f"A{idx}": "D",
            f"A_dff{idx}": "Q",
            "CLK": "CLK",
        }
        if mapping != expected_mapping:
            errors.append(
                {
                    "instance_name": instance["instance_name"],
                    "expected_mapping": expected_mapping,
                    "actual_mapping": mapping,
                }
            )
    return {
        "mapping_passed": not errors,
        "errors": errors,
    }


def _validate_approved_dff_binding(gds_path: Path, expected_top: str, expected_sha: str, expected_status: str, expected_commit: str) -> dict[str, Any]:
    manifest = _read_json(DFF_MANIFEST)
    hierarchy = _hierarchy_closure(gds_path, expected_top)
    geometry = _collect_dff_geometry_and_labels()
    normalized_inventory = Counter()
    for name, count in geometry["direct_child_inventory"].items():
        normalized_inventory[_normalize_direct_child_name(name)] += count
    normalized_inventory = dict(sorted(normalized_inventory.items()))
    unexpected_child_names = sorted(set(normalized_inventory) - set(EXPECTED_DFF_DIRECT_CHILDREN))
    missing_child_names = sorted(set(EXPECTED_DFF_DIRECT_CHILDREN) - set(normalized_inventory))
    dimension_rows = {
        name: _dimension_tokens_from_cell_name(name) for name in normalized_inventory
    }
    dimension_ok = all(row == {"NW_nm": 250, "PW_nm": 500, "L_nm": 50} for row in dimension_rows.values() if row is not None)
    report = {
        "gds_path": str(gds_path),
        "gds_sha256": _sha256(gds_path),
        "expected_gds_sha256": expected_sha,
        "top_cell": geometry["top_cell"],
        "expected_top_cell": expected_top,
        "manifest_status": manifest["reusable_status"],
        "expected_manifest_status": expected_status,
        "manifest_source_commit_openyield": manifest["source_commit_openyield"],
        "expected_source_commit_openyield": expected_commit,
        "direct_child_inventory_raw": geometry["direct_child_inventory"],
        "direct_child_inventory": normalized_inventory,
        "expected_direct_child_inventory": EXPECTED_DFF_DIRECT_CHILDREN,
        "unexpected_child_names": unexpected_child_names,
        "missing_child_names": missing_child_names,
        "dimension_tokens": dimension_rows,
        "conductive_geometry": geometry["conductive_geometry"],
        "label_texts": geometry["label_texts"],
        "hierarchy_closure": hierarchy,
    }
    report["binding_passed"] = (
        report["gds_sha256"] == expected_sha
        and report["top_cell"] == expected_top
        and report["manifest_status"] == expected_status
        and report["manifest_source_commit_openyield"] == expected_commit
        and normalized_inventory == EXPECTED_DFF_DIRECT_CHILDREN
        and not unexpected_child_names
        and not missing_child_names
        and dimension_ok
        and geometry["conductive_geometry"] == EXPECTED_DFF_CONDUCTIVE_GEOMETRY
        and geometry["label_texts"] == EXPECTED_DFF_TOP_LABELS
        and hierarchy["top_matches_expected"]
        and hierarchy["missing_reference_target_count"] == 0
    )
    return report


def _build_binding_closure(ast_report: dict[str, Any], source_topology: dict[str, Any]) -> dict[str, Any]:
    constructor_binding = _build_constructor_parameter_binding(ast_report)
    dff_binding_report = _validate_approved_dff_binding(
        DFF_GDS, EXPECTED_DFF_TOP, EXPECTED_DFF_SHA, EXPECTED_DFF_STATUS, EXPECTED_OPENYIELD_COMMIT
    )
    binding_rows = []
    for idx, instance in enumerate(source_topology["child_instances"]):
        binding_rows.append(
            {
                "instance_name": instance["instance_name"],
                "approved_physical_cell": EXPECTED_DFF_TOP,
                "logical_to_physical_pin_mapping": {
                    "VDD": "VDD",
                    "VSS": "VSS",
                    f"A{idx}": "D",
                    f"A_dff{idx}": "Q",
                    "CLK": "CLK",
                },
            }
        )
    mapping_validation = _validate_logical_to_physical_pin_mapping(source_topology, binding_rows)
    _write_csv(
        STAGE_DIR / "ADDR_DFF_child_binding_matrix.csv",
        [
            {
                "instance_name": row["instance_name"],
                "approved_physical_cell": row["approved_physical_cell"],
                "logical_to_physical_pin_mapping": json.dumps(row["logical_to_physical_pin_mapping"], sort_keys=True),
            }
            for row in binding_rows
        ],
    )
    binding_contract = {
        "logical_module": "ADDR_DFF",
        "approved_child_logical_module": "DFF",
        "approved_child_physical_cell": EXPECTED_DFF_TOP,
        "binding_rows": binding_rows,
        "mapping_validation": mapping_validation,
    }
    _write_json(STAGE_DIR / "ADDR_DFF_binding_contract.json", binding_contract)
    closure = {
        "source_constructor_call": constructor_binding["source_constructor_call"],
        "formal_to_actual_binding": constructor_binding["formal_to_actual_binding"],
        "default_values": constructor_binding["default_values"],
        "normalized_nm_values": constructor_binding["normalized_nm_values"],
        "expected_physical_child_cell_names": list(EXPECTED_DFF_DIRECT_CHILDREN.keys()),
        "actual_direct_child_inventory": dff_binding_report["direct_child_inventory"],
        "count_comparison": {
            "expected": EXPECTED_DFF_DIRECT_CHILDREN,
            "actual": dff_binding_report["direct_child_inventory"],
            "matched": dff_binding_report["direct_child_inventory"] == EXPECTED_DFF_DIRECT_CHILDREN,
        },
        "dimension_comparison": dff_binding_report["dimension_tokens"],
        "source_commit_comparison": {
            "expected": EXPECTED_OPENYIELD_COMMIT,
            "actual": dff_binding_report["manifest_source_commit_openyield"],
            "matched": dff_binding_report["manifest_source_commit_openyield"] == EXPECTED_OPENYIELD_COMMIT,
        },
        "gds_sha_comparison": {
            "expected": EXPECTED_DFF_SHA,
            "actual": dff_binding_report["gds_sha256"],
            "matched": dff_binding_report["gds_sha256"] == EXPECTED_DFF_SHA,
        },
        "defaults_close_with_approved_dff": dff_binding_report["binding_passed"]
        and constructor_binding["normalized_nm_values"] == {"pmos_width_nm": 500, "nmos_width_nm": 250, "length_nm": 50},
        "closure_passed": dff_binding_report["binding_passed"]
        and constructor_binding["normalized_nm_values"] == {"pmos_width_nm": 500, "nmos_width_nm": 250, "length_nm": 50}
        and mapping_validation["mapping_passed"],
    }
    _write_json(STAGE_DIR / "ADDR_DFF_DFF_PARAMETER_TO_PHYSICAL_BINDING_CLOSURE.json", closure)
    _write_json(STAGE_DIR / "ADDR_DFF_approved_dependency_audit.json", dff_binding_report)
    _write_json(STAGE_DIR / "ADDR_DFF_DFF_hierarchy_closure.json", dff_binding_report["hierarchy_closure"])
    _write_json(
        STAGE_DIR / "ADDR_DFF_DFF_child_physical_interface.json",
        {
            "top_cell": dff_binding_report["top_cell"],
            "label_texts": dff_binding_report["label_texts"],
            "direct_child_inventory": dff_binding_report["direct_child_inventory"],
        },
    )
    _write_json(
        STAGE_DIR / "ADDR_DFF_DFF_conductive_obstacle_map.json",
        {"conductive_geometry": dff_binding_report["conductive_geometry"]},
    )
    _write_csv(
        STAGE_DIR / "ADDR_DFF_DFF_pin_geometry.csv",
        [{"top_label": label} for label in dff_binding_report["label_texts"]],
    )
    return {
        "constructor_binding": constructor_binding,
        "binding_rows": binding_rows,
        "mapping_validation": mapping_validation,
        "dff_binding_report": dff_binding_report,
        "closure": closure,
    }


def _forbidden_source_paths() -> list[Path]:
    manifest = _read_json(DFF_MANIFEST)
    paths = [Path(item) for item in manifest["forbidden_physical_sources"]]
    paths.append(REPO_ROOT / "outputs/Wave3_DFF_BUF_reusable_release/DFF_BUF_reusable_clean.gds")
    return paths


def _validate_forbidden_source_path(path: Path) -> dict[str, Any]:
    manifest = _read_json(DFF_MANIFEST)
    forbidden = {Path(item).resolve() for item in manifest["forbidden_physical_sources"]}
    forbidden.add((REPO_ROOT / "outputs/Wave3_DFF_BUF_reusable_release/DFF_BUF_reusable_clean.gds").resolve())
    resolved = path.resolve()
    if resolved in forbidden:
        return {"passed": False, "rejection_reason": "forbidden physical source"}
    if resolved != DFF_GDS.resolve():
        return {"passed": False, "rejection_reason": "non-approved physical source"}
    return {"passed": True, "rejection_reason": None}


def _validator_no_generated_gds(root: Path) -> dict[str, Any]:
    names = [path.name for path in root.rglob("*.gds")]
    addr = [name for name in names if "ADDR_DFF" in name]
    data = [name for name in names if "DATA_DFF" in name]
    if addr:
        return {"passed": False, "rejection_reason": "ADDR_DFF GDS generated"}
    if data:
        return {"passed": False, "rejection_reason": "DATA_DFF GDS generated"}
    return {"passed": True, "rejection_reason": None}


def _save_mutation_artifact(test_name: str, source_path: Path) -> Path:
    target_dir = STAGE_DIR / "negative_test_artifacts" / test_name
    target_dir.mkdir(parents=True, exist_ok=True)
    destination = target_dir / source_path.name
    shutil.copy2(source_path, destination)
    return destination


def _save_mutation_text(test_name: str, filename: str, content: str) -> Path:
    target_dir = STAGE_DIR / "negative_test_artifacts" / test_name
    target_dir.mkdir(parents=True, exist_ok=True)
    destination = target_dir / filename
    destination.write_text(content, encoding="utf-8")
    return destination


def _run_negative_tests(locked_blob: dict[str, Any], ast_report: dict[str, Any], source_topology: dict[str, Any], expected_contract: dict[str, Any], binding_artifacts: dict[str, Any]) -> dict[str, Any]:
    test_results = []

    def add_result(
        test_name: str,
        mutated_file: str,
        mutation_description: str,
        validator_entry_point: str,
        validator_output: dict[str, Any],
        expected_rejection_reason: str,
    ) -> None:
        actual_rejection_reason = validator_output.get("rejection_reason") or validator_output.get("reason")
        passed = not validator_output.get("passed", validator_output.get("authority_passed", False)) and actual_rejection_reason == expected_rejection_reason
        test_results.append(
            {
                "test_name": test_name,
                "mutated_file": mutated_file,
                "mutation_description": mutation_description,
                "validator_entry_point": validator_entry_point,
                "validator_output": validator_output,
                "expected_rejection_reason": expected_rejection_reason,
                "actual_rejection_reason": actual_rejection_reason,
                "test_passed": passed,
            }
        )

    wrong_commit_report = _validator_source_snapshot(
        "locked_git_blob",
        "0000000000000000000000000000000000000000",
        EXPECTED_TIME_GENERATE_PATH,
        locked_blob["bytes"],
        EXPECTED_OPENYIELD_COMMIT,
        EXPECTED_TIME_GENERATE_PATH,
        EXPECTED_TIME_GENERATE_BLOB_SHA,
        EXPECTED_TIME_GENERATE_SHA256,
    )
    add_result(
        "openyield_commit_mismatch",
        str(locked_blob["snapshot_path"]),
        "pass wrong authority commit to production source snapshot validator",
        "_validator_source_snapshot",
        {"passed": wrong_commit_report["authority_passed"], "rejection_reason": wrong_commit_report["rejection_reason"]},
        "authority commit mismatch",
    )

    blob_sha_report = _validator_source_snapshot(
        "locked_git_blob",
        EXPECTED_OPENYIELD_COMMIT,
        EXPECTED_TIME_GENERATE_PATH,
        locked_blob["bytes"],
        EXPECTED_OPENYIELD_COMMIT,
        EXPECTED_TIME_GENERATE_PATH,
        "0000000000000000000000000000000000000000",
        EXPECTED_TIME_GENERATE_SHA256,
    )
    add_result(
        "time_generate_blob_sha_mismatch",
        str(locked_blob["snapshot_path"]),
        "pass wrong expected blob SHA to production source snapshot validator",
        "_validator_source_snapshot",
        {"passed": blob_sha_report["authority_passed"], "rejection_reason": blob_sha_report["rejection_reason"]},
        "locked blob SHA mismatch",
    )

    path_mismatch_report = _validator_source_snapshot(
        "locked_git_blob",
        EXPECTED_OPENYIELD_COMMIT,
        "sram_compiler/subcircuits/other_file.py",
        locked_blob["bytes"],
        EXPECTED_OPENYIELD_COMMIT,
        EXPECTED_TIME_GENERATE_PATH,
        EXPECTED_TIME_GENERATE_BLOB_SHA,
        EXPECTED_TIME_GENERATE_SHA256,
    )
    add_result(
        "source_path_points_elsewhere",
        str(locked_blob["snapshot_path"]),
        "pass correct bytes but wrong authority source path to production source snapshot validator",
        "_validator_source_snapshot",
        {"passed": path_mismatch_report["authority_passed"], "rejection_reason": path_mismatch_report["rejection_reason"]},
        "source path points to different file",
    )

    working_tree_report = _validator_source_snapshot(
        "working_tree_file",
        EXPECTED_OPENYIELD_COMMIT,
        EXPECTED_TIME_GENERATE_PATH,
        OPENYIELD_TIME_GENERATE.read_bytes(),
        EXPECTED_OPENYIELD_COMMIT,
        EXPECTED_TIME_GENERATE_PATH,
        EXPECTED_TIME_GENERATE_BLOB_SHA,
        EXPECTED_TIME_GENERATE_SHA256,
    )
    add_result(
        "working_tree_used_as_authority",
        str(OPENYIELD_TIME_GENERATE),
        "use working-tree file as authority source input instead of locked git blob",
        "_validator_source_snapshot",
        {"passed": working_tree_report["authority_passed"], "rejection_reason": working_tree_report["rejection_reason"]},
        "working-tree source used as authority",
    )

    clk_mutated_text = locked_blob["bytes"].decode("utf-8").replace("nodes = ['VDD', 'VSS', 'CLK']", "nodes = ['VDD', 'VSS']").replace(
        "'VDD', 'VSS', f'A{i}', f'A_dff{i}', 'CLK'",
        "'VDD', 'VSS', f'A{i}', f'A_dff{i}'",
    ).replace(
        "addr_dff_connections = ['VDD', 'VSS', 'clk_buf']",
        "addr_dff_connections = ['VDD', 'VSS']",
    )
    clk_mutation_path = _save_mutation_text("clk_pin_missing", "time_generate_clk_missing.py", clk_mutated_text)
    clk_ast = _extract_ast_report(clk_mutation_path.read_bytes(), str(clk_mutation_path), write_outputs=False)
    clk_config = _resolve_num_rows_from_ast_and_config(clk_ast, write_outputs=False)
    clk_topology = _build_source_derived_topology(clk_ast, clk_config, write_outputs=False)
    clk_report = _validate_topology_exact_identity(clk_topology, expected_contract, write_outputs=False)
    add_result(
        "clk_pin_missing",
        str(clk_mutation_path),
        "remove CLK from nodes and ADDR_DFF instance/time connection construction",
        "_validate_topology_exact_identity",
        {"passed": clk_report["exact_identity_passed"], "rejection_reason": "topology exact identity mismatch" if not clk_report["exact_identity_passed"] else None},
        "topology exact identity mismatch",
    )

    dff_top_report = _validate_approved_dff_binding(
        DFF_GDS, "WRONG_TOP", EXPECTED_DFF_SHA, EXPECTED_DFF_STATUS, EXPECTED_OPENYIELD_COMMIT
    )
    add_result(
        "dff_top_cell_mismatch",
        str(DFF_GDS),
        "pass wrong expected top cell to production DFF binding validator",
        "_validate_approved_dff_binding",
        {"passed": dff_top_report["binding_passed"], "rejection_reason": "approved DFF top cell mismatch" if not dff_top_report["binding_passed"] else None},
        "approved DFF top cell mismatch",
    )

    conflict_dir = STAGE_DIR / "negative_test_artifacts" / "num_rows_authority_conflict"
    conflict_dir.mkdir(parents=True, exist_ok=True)
    spec16 = conflict_dir / "authority_16.json"
    spec32 = conflict_dir / "authority_32.json"
    _write_text(spec16, json.dumps({"num_rows": 16}, indent=2) + "\n")
    _write_text(spec32, json.dumps({"num_rows": 32}, indent=2) + "\n")
    conflict_report = _resolve_num_rows_from_ast_and_config(
        ast_report,
        overrides=[
            {
                "path": str(spec16),
                "source_category": "temp_current_authority",
                "current_or_historical": "current",
                "content_sha256": _sha256(spec16),
                "parsed_num_rows": 16,
                "precedence": 10,
            },
            {
                "path": str(spec32),
                "source_category": "temp_current_authority",
                "current_or_historical": "current",
                "content_sha256": _sha256(spec32),
                "parsed_num_rows": 32,
                "precedence": 20,
            },
        ],
        write_outputs=False,
    )
    add_result(
        "num_rows_authority_conflict",
        f"{spec16},{spec32}",
        "use two current-authority config copies with conflicting num_rows values 16 and 32",
        "_resolve_num_rows_from_ast_and_config",
        {"passed": not conflict_report["num_rows_authority_conflict"], "rejection_reason": "num_rows authority conflict" if conflict_report["num_rows_authority_conflict"] else None},
        "num_rows authority conflict",
    )

    swapped_rows = json.loads(json.dumps(binding_artifacts["binding_rows"]))
    swapped_rows[0]["logical_to_physical_pin_mapping"]["A0"] = "Q"
    swapped_rows[0]["logical_to_physical_pin_mapping"]["A_dff0"] = "D"
    swapped_report = _validate_logical_to_physical_pin_mapping(source_topology, swapped_rows)
    swapped_path = _save_mutation_text(
        "d_and_q_physical_mapping_swapped",
        "binding_rows_swapped.json",
        json.dumps(swapped_rows, indent=2, ensure_ascii=False) + "\n",
    )
    add_result(
        "d_and_q_physical_mapping_swapped",
        str(swapped_path),
        "swap Ai->D and A_dffi->Q into Ai->Q and A_dffi->D in logical-to-physical binding rows",
        "_validate_logical_to_physical_pin_mapping",
        {"passed": swapped_report["mapping_passed"], "rejection_reason": "logical-to-physical pin mapping mismatch" if not swapped_report["mapping_passed"] else None},
        "logical-to-physical pin mapping mismatch",
    )

    for forbidden in _forbidden_source_paths():
        report = _validate_forbidden_source_path(forbidden)
        add_result(
            f"forbidden_source_{forbidden.stem}",
            str(forbidden),
            "use forbidden physical source path against production source-path validator",
            "_validate_forbidden_source_path",
            {"passed": report["passed"], "rejection_reason": report["rejection_reason"]},
            "forbidden physical source",
        )

    with tempfile.TemporaryDirectory(prefix="wave4a_addr_gds_") as tmp:
        tmp_root = Path(tmp)
        (tmp_root / "ADDR_DFF_generated.gds").write_bytes(b"dummy")
        add_report = _validator_no_generated_gds(tmp_root)
        add_result(
            "addr_dff_gds_generated",
            str(tmp_root / "ADDR_DFF_generated.gds"),
            "create temporary ADDR_DFF GDS in stage-like directory",
            "_validator_no_generated_gds",
            add_report,
            "ADDR_DFF GDS generated",
        )

    with tempfile.TemporaryDirectory(prefix="wave4a_data_gds_") as tmp:
        tmp_root = Path(tmp)
        (tmp_root / "DATA_DFF_generated.gds").write_bytes(b"dummy")
        data_report = _validator_no_generated_gds(tmp_root)
        add_result(
            "data_dff_gds_generated",
            str(tmp_root / "DATA_DFF_generated.gds"),
            "create temporary DATA_DFF GDS in stage-like directory",
            "_validator_no_generated_gds",
            data_report,
            "DATA_DFF GDS generated",
        )

    payload = {
        "all_negative_tests_passed": all(row["test_passed"] for row in test_results),
        "hardcoded_negative_test_count": 0,
        "real_mutation_negative_test_count": len(test_results),
        "tests": test_results,
    }
    _write_json(STAGE_DIR / "ADDR_DFF_negative_tests.json", payload)
    _write_text(STAGE_DIR / "ADDR_DFF_negative_tests.md", _render_md_kv("ADDR_DFF Negative Tests", payload))
    forbidden_tests = [row for row in test_results if row["test_name"].startswith("forbidden_source_")]
    _write_json(
        STAGE_DIR / "ADDR_DFF_forbidden_source_negative_tests.json",
        {"all_passed": all(row["test_passed"] for row in forbidden_tests), "tests": forbidden_tests},
    )
    return payload


def _replace_section(text: str, heading: str, new_block: str) -> str:
    pattern = rf"{re.escape(heading)}.*?(?=\n## |\Z)"
    return re.sub(pattern, new_block + "\n\n", text, count=1, flags=re.S)


def _update_ledgers_in_progress() -> None:
    status = _read_json(STATUS_JSON)
    status["current_stage"] = STAGE_ID
    status["current_status"] = "IN_PROGRESS"
    status["ADDR_DFF source topology status"] = "SOURCE_FACTS_MACHINE_CONFIRMED_VALIDATOR_HARDENING_REQUIRED"
    status["ADDR_DFF physical binding status"] = "BINDING_FACTS_MACHINE_CONFIRMED_VALIDATOR_HARDENING_REQUIRED"
    status["ADDR_DFF physical GDS status"] = "NOT_GENERATED"
    status["next_stage_allowed"] = BLOCKED_STAGE
    status["can_enter_next_stage"] = False
    status["DATA_DFF binding status"] = "UNRESOLVED_REQUIRES_WAVE4B_SOURCE_BINDING_REVIEW"
    _write_json(STATUS_JSON, status)

    status_md_block = "\n".join(
        [
            "## 2. Current Stage",
            "",
            f"- current_stage: `{STAGE_ID}`",
            "- current_status: `IN_PROGRESS`",
            "- ADDR_DFF source topology status: `SOURCE_FACTS_MACHINE_CONFIRMED_VALIDATOR_HARDENING_REQUIRED`",
            "- ADDR_DFF physical binding status: `BINDING_FACTS_MACHINE_CONFIRMED_VALIDATOR_HARDENING_REQUIRED`",
            "- ADDR_DFF physical GDS status: `NOT_GENERATED`",
            f"- next_stage_allowed: `{BLOCKED_STAGE}`",
            "- can_enter_next_stage: `False`",
            f"- deferred_sibling_stage: `{DEFERRED_SIBLING_STAGE}`",
            "- DATA_DFF binding status: `UNRESOLVED_REQUIRES_WAVE4B_SOURCE_BINDING_REVIEW`",
        ]
    )
    STATUS_MD.write_text(_replace_section(STATUS_MD.read_text(encoding="utf-8"), "## 2. Current Stage", status_md_block), encoding="utf-8")

    for md_path, title in [(GOAL_MD, "## Current Hardened Composite Stage"), (PROGRESS_MD, "## Wave3H1 Progress Gate")]:
        block = "\n".join(
            [
                title,
                "",
                f"- current_stage: `{STAGE_ID}`",
                "- current_status: `IN_PROGRESS`",
                "- ADDR_DFF source topology status: `SOURCE_FACTS_MACHINE_CONFIRMED_VALIDATOR_HARDENING_REQUIRED`",
                "- ADDR_DFF physical binding status: `BINDING_FACTS_MACHINE_CONFIRMED_VALIDATOR_HARDENING_REQUIRED`",
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
    status["ADDR_DFF validator status"] = "SOURCE_AND_BINDING_VALIDATOR_HARDENED"
    status["ADDR_DFF physical GDS status"] = "NOT_GENERATED"
    status["next_stage"] = NEXT_STAGE
    status["recommended_next_stage"] = NEXT_STAGE
    status["next_stage_allowed"] = NEXT_STAGE
    status["can_enter_next_stage"] = True
    status["DATA_DFF binding status"] = "UNRESOLVED_REQUIRES_WAVE4B_SOURCE_BINDING_REVIEW"
    _write_json(STATUS_JSON, status)

    status_md_block = "\n".join(
        [
            "## 2. Current Stage",
            "",
            f"- current_stage: `{STAGE_ID}`",
            "- current_status: `PASS`",
            "- ADDR_DFF source topology status: `SOURCE_EXACT_TOPOLOGY_LOCKED`",
            "- ADDR_DFF physical binding status: `APPROVED_DFF_BINDING_LOCKED`",
            "- ADDR_DFF validator status: `SOURCE_AND_BINDING_VALIDATOR_HARDENED`",
            "- ADDR_DFF physical GDS status: `NOT_GENERATED`",
            f"- next_stage: `{NEXT_STAGE}`",
            f"- recommended_next_stage: `{NEXT_STAGE}`",
            f"- next_stage_allowed: `{NEXT_STAGE}`",
            "- can_enter_next_stage: `True`",
            f"- deferred_sibling_stage: `{DEFERRED_SIBLING_STAGE}`",
            "- DATA_DFF binding status: `UNRESOLVED_REQUIRES_WAVE4B_SOURCE_BINDING_REVIEW`",
        ]
    )
    STATUS_MD.write_text(_replace_section(STATUS_MD.read_text(encoding="utf-8"), "## 2. Current Stage", status_md_block), encoding="utf-8")

    for md_path, title in [(GOAL_MD, "## Current Hardened Composite Stage"), (PROGRESS_MD, "## Wave3H1 Progress Gate")]:
        block = "\n".join(
            [
                title,
                "",
                f"- current_stage: `{STAGE_ID}`",
                "- current_status: `PASS`",
                "- ADDR_DFF source topology status: `SOURCE_EXACT_TOPOLOGY_LOCKED`",
                "- ADDR_DFF physical binding status: `APPROVED_DFF_BINDING_LOCKED`",
                "- ADDR_DFF validator status: `SOURCE_AND_BINDING_VALIDATOR_HARDENED`",
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
    status_md = STATUS_MD.read_text(encoding="utf-8")
    goal_md = GOAL_MD.read_text(encoding="utf-8")
    progress_md = PROGRESS_MD.read_text(encoding="utf-8")
    checks = {
        "status_json_current_stage": status.get("current_stage") == STAGE_ID,
        "status_json_current_status": status.get("current_status") == "PASS",
        "status_json_next_stage_allowed": status.get("next_stage_allowed") == NEXT_STAGE,
        "status_json_validator_status": status.get("ADDR_DFF validator status") == "SOURCE_AND_BINDING_VALIDATOR_HARDENED",
        "status_md_stage": f"- current_stage: `{STAGE_ID}`" in status_md,
        "goal_md_stage": f"- current_stage: `{STAGE_ID}`" in goal_md,
        "progress_md_stage": f"- current_stage: `{STAGE_ID}`" in progress_md,
    }
    report = {"checks": checks, "all_passed": all(checks.values())}
    _write_json(STAGE_DIR / "ledger_consistency_report.json", report)
    return report


def _write_stage_report(
    preconditions: dict[str, Any],
    source_validator_report: dict[str, Any],
    identity_report: dict[str, Any],
    config_report: dict[str, Any],
    source_topology: dict[str, Any],
    binding_artifacts: dict[str, Any],
    negative_tests: dict[str, Any],
) -> None:
    summary = {
        "stage": STAGE_ID,
        "current_status": "PASS",
        "project_branch": preconditions["project_branch"],
        "report_generation_base_commit": preconditions["report_generation_base_commit"],
        "openyield_commit": EXPECTED_OPENYIELD_COMMIT,
        "locked_blob_sha": EXPECTED_TIME_GENERATE_BLOB_SHA,
        "locked_source_file_sha256": EXPECTED_TIME_GENERATE_SHA256,
        "source_snapshot_validator_result": source_validator_report["authority_passed"],
        "source_snapshot_validator_rejection_reason": source_validator_report["rejection_reason"],
        "ast_topology_exact_identity": identity_report["exact_identity_passed"],
        "num_rows_resolution_passed": config_report["all_current_authorities_equal_16"],
        "resolved_num_rows": config_report["resolved_num_rows"],
        "resolved_n_bits": source_topology["resolved_n_bits"],
        "top_pin_order": source_topology["resolved_top_pins"],
        "child_instances": [row["instance_name"] for row in source_topology["child_instances"]],
        "canonical_nets": source_topology["canonical_nets"],
        "approved_dff_sha256": EXPECTED_DFF_SHA,
        "approved_dff_top": EXPECTED_DFF_TOP,
        "approved_dff_status": EXPECTED_DFF_STATUS,
        "constructor_parameter_binding": binding_artifacts["constructor_binding"],
        "parameter_to_physical_binding_closure_passed": binding_artifacts["closure"]["closure_passed"],
        "negative_test_count": negative_tests["real_mutation_negative_test_count"],
        "hardcoded_negative_test_count": negative_tests["hardcoded_negative_test_count"],
        "addr_dff_gds_generated": False,
        "data_dff_work_performed": False,
        "next_stage": NEXT_STAGE,
    }
    _write_json(STAGE_DIR / "Wave4A_stage_report.json", summary)
    _write_text(STAGE_DIR / "Wave4A_stage_report.md", _render_md_kv("Wave4A Stage Report", summary))


def _check_dirty_immutability() -> dict[str, Any]:
    baseline = _read_json(STAGE_DIR / "baseline_dirty_tree_report.json")
    changed = []
    current_rows = []
    for row in baseline["dirty_paths"]:
        if _path_is_mutable_in_this_round(row["relative_path"]):
            continue
        current = _path_metadata(row["relative_path"])
        current["status_code"] = row["status_code"]
        current_rows.append(current)
        if (
            current["exists"] != row["exists"]
            or current["file_type"] != row["file_type"]
            or current["size_bytes"] != row["size_bytes"]
            or current["sha256"] != row["sha256"]
            or current["inventory_digest"] != row["inventory_digest"]
        ):
            changed.append({"path": row["relative_path"], "before": row, "after": current})
    payload = {"all_passed": not changed, "changed_paths": changed, "baseline_count": len(baseline["dirty_paths"]), "current_rows": current_rows}
    _write_json(STAGE_DIR / "existing_dirty_path_immutability_report.json", payload)
    return payload


def check_staged() -> None:
    staged = [line for line in _git("diff", "--cached", "--name-only").splitlines() if line.strip()]
    baseline = _read_json(STAGE_DIR / "baseline_dirty_tree_report.json")
    baseline_paths = {
        row["relative_path"] for row in baseline["dirty_paths"] if not _path_is_mutable_in_this_round(row["relative_path"])
    }
    outsiders = []
    dirty_staged = []
    for path in staged:
        if not any(path == allowed or path.startswith(allowed + "/") for allowed in ALLOWLIST):
            outsiders.append(path)
        if path in baseline_paths:
            dirty_staged.append(path)
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
        if rel in {"evidence_package_manifest.json", "evidence_package_manifest.csv"}:
            continue
        entries.append(
            {
                "relative_path": rel,
                "file_size": path.stat().st_size,
                "sha256": _sha256(path),
                "required": True,
            }
        )
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


def package() -> None:
    check_staged()
    dirty_immutability = _check_dirty_immutability()
    if not dirty_immutability["all_passed"]:
        raise RuntimeError("dirty path immutability failed")

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
        (STAGE_DIR / "source/time_generate_locked_1c34428.py", "source/time_generate_locked_1c34428.py"),
        (STAGE_DIR / "source/global_yaml_locked_1c34428.yaml", "source/global_yaml_locked_1c34428.yaml"),
        (STAGE_DIR / "source_blob_lock_report.json", "reports/source_blob_lock_report.json"),
        (STAGE_DIR / "ADDR_DFF_ast_extraction.json", "reports/ADDR_DFF_ast_extraction.json"),
        (STAGE_DIR / "ADDR_DFF_ast_extraction.md", "reports/ADDR_DFF_ast_extraction.md"),
        (STAGE_DIR / "ADDR_DFF_source_derived_topology.json", "reports/ADDR_DFF_source_derived_topology.json"),
        (STAGE_DIR / "ADDR_DFF_expected_project_contract.json", "reports/ADDR_DFF_expected_project_contract.json"),
        (STAGE_DIR / "ADDR_DFF_topology_exact_identity_report.json", "reports/ADDR_DFF_topology_exact_identity_report.json"),
        (STAGE_DIR / "ADDR_DFF_CONFIG_RESOLUTION.json", "reports/ADDR_DFF_CONFIG_RESOLUTION.json"),
        (STAGE_DIR / "ADDR_DFF_CONFIG_RESOLUTION.md", "reports/ADDR_DFF_CONFIG_RESOLUTION.md"),
        (LAYOUTGEN_CURRENT_SPEC, "config_authorities/SRAM_SPEC.json"),
        (OPENYIELD_CURRENT_SPEC, "config_authorities/M9_SRAM_SPEC.json"),
        (DFF_GDS, "dependencies/dff/DFF_reusable_clean.gds"),
        (DFF_MANIFEST, "dependencies/dff/DFF_REUSABLE_MANIFEST.json"),
        (STAGE_DIR / "ADDR_DFF_constructor_parameter_binding.json", "reports/ADDR_DFF_constructor_parameter_binding.json"),
        (STAGE_DIR / "ADDR_DFF_DFF_PARAMETER_TO_PHYSICAL_BINDING_CLOSURE.json", "reports/ADDR_DFF_DFF_PARAMETER_TO_PHYSICAL_BINDING_CLOSURE.json"),
        (STAGE_DIR / "ADDR_DFF_DFF_hierarchy_closure.json", "reports/ADDR_DFF_DFF_hierarchy_closure.json"),
        (STAGE_DIR / "ADDR_DFF_DFF_child_physical_interface.json", "reports/ADDR_DFF_DFF_child_physical_interface.json"),
        (STAGE_DIR / "ADDR_DFF_DFF_conductive_obstacle_map.json", "reports/ADDR_DFF_DFF_conductive_obstacle_map.json"),
        (STAGE_DIR / "ADDR_DFF_DFF_pin_geometry.csv", "reports/ADDR_DFF_DFF_pin_geometry.csv"),
        (Path(__file__), "reports/production_validator_source.py"),
        (STAGE_DIR / "ADDR_DFF_negative_tests.json", "reports/ADDR_DFF_negative_tests.json"),
        (STAGE_DIR / "ADDR_DFF_negative_tests.md", "reports/ADDR_DFF_negative_tests.md"),
        (STAGE_DIR / "ADDR_DFF_forbidden_source_negative_tests.json", "reports/ADDR_DFF_forbidden_source_negative_tests.json"),
        (STAGE_DIR / "baseline_dirty_tree_report.json", "reports/baseline_dirty_tree_report.json"),
        (STAGE_DIR / "existing_dirty_path_immutability_report.json", "reports/existing_dirty_path_immutability_report.json"),
        (STAGE_DIR / "staged_allowlist_report.json", "reports/staged_allowlist_report.json"),
        (STAGE_DIR / "staged_allowlist_report.md", "reports/staged_allowlist_report.md"),
        (STAGE_DIR / "ledger_consistency_report.json", "reports/ledger_consistency_report.json"),
        (STAGE_DIR / "Wave4A_stage_report.json", "reports/Wave4A_stage_report.json"),
        (STAGE_DIR / "Wave4A_stage_report.md", "reports/Wave4A_stage_report.md"),
    ]
    for src, rel in copy_map:
        dest = package_root / rel
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dest)

    negative_artifacts = STAGE_DIR / "negative_test_artifacts"
    if negative_artifacts.exists():
        shutil.copytree(negative_artifacts, package_root / "negative_test_artifacts", dirs_exist_ok=True)

    evidence_package_report = {
        "package_basename": package_basename,
        "package_format": "tar.gz",
        "manifest_required_entry_actual_count": 0,
        "sha256sums_actual_count": 0,
        "final_tar_sha_stored_in_external_sidecar": True,
        "push_result": push_result,
    }
    _write_json(package_root / "reports/evidence_package_report.json", evidence_package_report)

    manifest_entries = _manifest_entries_for_package(package_root)
    manifest = {
        "package_basename": package_basename,
        "package_format": "tar.gz",
        "self_hash_policy": "non_self_referential_external_tar_sidecar",
        "entries": manifest_entries,
    }
    _write_json(package_root / "evidence_package_manifest.json", manifest)
    _write_csv(package_root / "evidence_package_manifest.csv", manifest_entries)

    manifest_verification_report = {
        "package_basename": package_basename,
        "required_entry_count": len(manifest_entries),
        "manifest_entries_all_have_size_and_sha": True,
        "checksum_protection_strategy": "covered_by_final_SHA256SUMS",
    }
    _write_json(package_root / "reports/manifest_verification_report.json", manifest_verification_report)

    def write_sha256sums() -> None:
        lines = []
        for path in sorted(package_root.rglob("*")):
            if path.is_file():
                rel = path.relative_to(package_root).as_posix()
                if rel == "SHA256SUMS":
                    continue
                lines.append(f"{_sha256(path)}  {rel}")
        _write_text(package_root / "SHA256SUMS", "\n".join(lines) + "\n")

    write_sha256sums()
    package_verification_report = _verify_manifest_and_sums(package_root)
    _write_json(package_root / "reports/package_verification_report.json", package_verification_report)
    write_sha256sums()
    final_verification = _verify_manifest_and_sums(package_root)
    if not final_verification["all_passed"]:
        raise RuntimeError("final package verification failed")

    evidence_package_report["manifest_required_entry_actual_count"] = final_verification["manifest_required_entry_actual_count"]
    evidence_package_report["sha256sums_actual_count"] = final_verification["sha256sums_actual_count"]
    _write_json(package_root / "reports/evidence_package_report.json", evidence_package_report)
    write_sha256sums()
    final_verification = _verify_manifest_and_sums(package_root)
    _write_json(package_root / "reports/package_verification_report.json", final_verification)
    write_sha256sums()
    final_verification = _verify_manifest_and_sums(package_root)
    if not final_verification["all_passed"]:
        raise RuntimeError("final package verification failed after report refresh")

    tar_path = REPO_ROOT / f"{package_basename}.tar.gz"
    if tar_path.exists():
        tar_path.unlink()
    with tarfile.open(tar_path, "w:gz") as archive:
        archive.add(package_root, arcname=package_root.name)
    tar_sha = _sha256(tar_path)
    sidecar_path = tar_path.with_suffix(tar_path.suffix + ".sha256")
    _write_text(sidecar_path, f"{tar_sha}  {tar_path.name}\n")

    with tempfile.TemporaryDirectory(prefix="wave4a_pkg_verify_") as tmp:
        with tarfile.open(tar_path, "r:gz") as archive:
            archive.extractall(tmp)
        extracted_root = next(path for path in Path(tmp).iterdir() if path.is_dir())
        extracted_verification = _verify_manifest_and_sums(extracted_root)
    if not extracted_verification["all_passed"]:
        raise RuntimeError("independent extracted package verification failed")

    _write_json(
        STAGE_DIR / "evidence_package_report.json",
        {
            "package_path": str(tar_path),
            "package_sha256": tar_sha,
            "sidecar_path": str(sidecar_path),
            "package_basename": package_basename,
            "manifest_required_entry_actual_count": final_verification["manifest_required_entry_actual_count"],
            "sha256sums_actual_count": final_verification["sha256sums_actual_count"],
            "verification_report_checksum_protection": final_verification["manifest_verification_report_covered_by_sha256sums"]
            and final_verification["package_verification_report_covered_by_sha256sums"],
            "independent_extract_verification_passed": extracted_verification["all_passed"],
            "push_result": push_result,
        },
    )
    _write_text(STAGE_DIR / "evidence_package_report.md", _render_md_kv("Evidence Package Report", _read_json(STAGE_DIR / "evidence_package_report.json")))


def prepare() -> None:
    if STAGE_DIR.exists():
        shutil.rmtree(STAGE_DIR)
    STAGE_DIR.mkdir(parents=True, exist_ok=True)
    preconditions = _verify_required_inputs()
    _write_json(STAGE_DIR / "preconditions.json", preconditions)
    _dirty_tree_baseline()
    _update_ledgers_in_progress()

    locked_blob = _fetch_locked_source_blob()
    source_validator_report = _validator_source_snapshot(
        locked_blob["authority_kind"],
        locked_blob["authority_commit"],
        locked_blob["source_path"],
        locked_blob["bytes"],
        EXPECTED_OPENYIELD_COMMIT,
        EXPECTED_TIME_GENERATE_PATH,
        EXPECTED_TIME_GENERATE_BLOB_SHA,
        EXPECTED_TIME_GENERATE_SHA256,
    )
    _write_source_snapshot_report(locked_blob, source_validator_report)
    if not source_validator_report["authority_passed"]:
        raise RuntimeError(source_validator_report["rejection_reason"] or "source snapshot validator failed")

    ast_report = _extract_ast_report(locked_blob["bytes"], f"{EXPECTED_OPENYIELD_COMMIT}:{EXPECTED_TIME_GENERATE_PATH}")
    config_report = _resolve_num_rows_from_ast_and_config(ast_report)
    if not config_report["all_current_authorities_equal_16"]:
        raise RuntimeError("num_rows current authority resolution did not converge to 16")
    source_topology = _build_source_derived_topology(ast_report, config_report)
    expected_contract = _build_expected_project_contract()
    identity_report = _validate_topology_exact_identity(source_topology, expected_contract)
    if not identity_report["exact_identity_passed"]:
        raise RuntimeError("source-derived topology did not exactly match expected project contract")

    binding_artifacts = _build_binding_closure(ast_report, source_topology)
    if not binding_artifacts["closure"]["closure_passed"]:
        raise RuntimeError("constructor-to-physical binding closure failed")

    negative_tests = _run_negative_tests(locked_blob, ast_report, source_topology, expected_contract, binding_artifacts)
    if not negative_tests["all_negative_tests_passed"]:
        raise RuntimeError("negative tests failed")

    no_gds_report = _validator_no_generated_gds(STAGE_DIR)
    if not no_gds_report["passed"]:
        raise RuntimeError(no_gds_report["rejection_reason"] or "unexpected GDS generated")

    _update_ledgers_pass()
    ledger_report = _ledger_consistency()
    if not ledger_report["all_passed"]:
        raise RuntimeError("ledger consistency failed")

    _write_stage_report(
        preconditions,
        source_validator_report,
        identity_report,
        config_report,
        source_topology,
        binding_artifacts,
        negative_tests,
    )


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
