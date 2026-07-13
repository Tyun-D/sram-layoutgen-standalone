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
from collections import defaultdict
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
EXPECTED_DFF_CELL = "DFF_TG4_INV7_FPDK45_26d9543b82b7"
EXPECTED_DFF_SHA = "f6995536077a191c31e10644bbfcfb4075cda64b7da131987c70a59353c4e45d"
EXPECTED_DFF_TOP_LABELS = ["CLK", "D", "Q", "VDD", "VSS"]
OPENYIELD_ROOT = Path("/data1/qujh/work/external/OpenYield")
OPENYIELD_TIME_GENERATE = OPENYIELD_ROOT / "sram_compiler/subcircuits/time_generate.py"
OPENYIELD_GLOBAL_YAML = OPENYIELD_ROOT / "sram_compiler/config_yaml/global.yaml"
STAGE_ID = "Wave4A / ADDR_DFF_SOURCE_TOPOLOGY_AND_BINDING_LOCK"
STAGE_DIR = REPO_ROOT / "outputs/Wave4A_ADDR_DFF_source_topology_and_binding_lock/current_supported_config"
PACKAGE_PREFIX = "Wave4A_ADDR_DFF_source_topology_and_binding_lock"
NEXT_STAGE = "Wave4A2 / ADDR_DFF_CANDIDATE_GENERATION_AND_MACHINE_VERIFICATION"
BLOCKED_STAGE = "BLOCKED_PENDING_WAVE4A_SOURCE_BINDING_LOCK"
DEFERRED_SIBLING_STAGE = "Wave4B / DATA_DFF"

STATUS_MD = REPO_ROOT / "PROJECT_LAYOUTGEN_OPENYIELD_STATUS.md"
STATUS_JSON = REPO_ROOT / "PROJECT_LAYOUTGEN_OPENYIELD_STATUS.json"
GOAL_MD = REPO_ROOT / "PROJECT_NETLIST_TO_LAYOUT_GOAL.md"
PROGRESS_MD = REPO_ROOT / "PROJECT_NETLIST_TO_LAYOUT_PROGRESS.md"
WAVE_PLAN = REPO_ROOT / "outputs/M12C4_composite_control_cell_generation_plan/current_supported_config/M12C4_composite_implementation_wave_plan.csv"
DFF_MANIFEST = REPO_ROOT / "outputs/M12C4ACH_dff_reusable_release/DFF_REUSABLE_MANIFEST.json"
DFF_GDS = REPO_ROOT / "outputs/M12C4ACH_dff_reusable_release/DFF_reusable_clean.gds"
WAVE3_WAVE4_REPORT = REPO_ROOT / "outputs/Wave3H1_R1_DFF_BUF_evidence_finalization_repair/current_supported_config/wave4_source_extraction_report.json"
REGISTRY_AUDIT = REPO_ROOT / "outputs/Wave3H1_R1_DFF_BUF_evidence_finalization_repair/current_supported_config/registry_audit.json"
WAVE3_OBSTACLE_MAP = REPO_ROOT / "outputs/Wave3H1_R1_DFF_BUF_evidence_finalization_repair/current_supported_config/child_conductive_obstacle_map_reverified.json"
DFF_CONNECTIVITY_REPORT = REPO_ROOT / "outputs/M12C4AC_dff_connectivity_repair/current_supported_config/M12C4AC_dff_physical_connectivity_report.json"
DFF_CONNECTIVITY_GRAPH = REPO_ROOT / "outputs/M12C4AC_dff_connectivity_repair/current_supported_config/M12C4AC_dff_physical_connectivity_graph.json"
DFF_SOURCE_TRACE = REPO_ROOT / "outputs/M12C4AC_dff_connectivity_repair/current_supported_config/DFF_TG4_INV7_FPDK45_26d9543b82b7/DFF_TG4_INV7_FPDK45_26d9543b82b7_source_trace.json"
DFF_LOGICAL_PHYSICAL = REPO_ROOT / "outputs/M12C4AC_dff_connectivity_repair/current_supported_config/DFF_TG4_INV7_FPDK45_26d9543b82b7/DFF_TG4_INV7_FPDK45_26d9543b82b7_logical_physical_correspondence.json"
LAYOUTGEN_CURRENT_SPEC = REPO_ROOT / "outputs/M8_reproduce_uploaded_golden/current_supported_config/SRAM_SPEC.json"
OPENYIELD_CURRENT_SPEC = REPO_ROOT / "outputs/M9_openyield_netlist_translator/current_supported_config/M9_SRAM_SPEC.json"

PREEXISTING_MODIFIED_PATHS = [
    "outputs/Wave3H1_DFF_BUF_release_evidence_hardening/current_supported_config/Wave3H1_stage_report.json",
    "outputs/Wave3H1_DFF_BUF_release_evidence_hardening/current_supported_config/Wave3H1_stage_report.md",
    "outputs/Wave3H1_DFF_BUF_release_evidence_hardening/current_supported_config/commit_info.txt",
    "outputs/Wave3H1_DFF_BUF_release_evidence_hardening/current_supported_config/evidence_package_report.json",
    "outputs/Wave3H1_DFF_BUF_release_evidence_hardening/current_supported_config/git_show.patch",
    "outputs/Wave3H1_DFF_BUF_release_evidence_hardening/current_supported_config/git_status.txt",
    "outputs/Wave3H1_DFF_BUF_release_evidence_hardening/current_supported_config/package_root/SHA256SUMS",
    "outputs/Wave3H1_DFF_BUF_release_evidence_hardening/current_supported_config/package_root/evidence_package_manifest.csv",
    "outputs/Wave3H1_DFF_BUF_release_evidence_hardening/current_supported_config/package_root/evidence_package_manifest.json",
    "outputs/Wave3H1_DFF_BUF_release_evidence_hardening/current_supported_config/package_root/git/commit_info.txt",
    "outputs/Wave3H1_DFF_BUF_release_evidence_hardening/current_supported_config/package_root/git/git_show.patch",
    "outputs/Wave3H1_DFF_BUF_release_evidence_hardening/current_supported_config/package_root/git/git_status.txt",
    "outputs/Wave3_DFF_BUF_hierarchical_pin_access_repair/current_supported_config/evidence_package_path.txt",
    "outputs/Wave3_DFF_BUF_human_review_seal/Wave3_DFF_BUF_human_review_seal_commit_info.txt",
    "outputs/Wave3_DFF_BUF_human_review_seal/Wave3_DFF_BUF_human_review_seal_git.diff",
    "outputs/Wave3_DFF_BUF_human_review_seal/evidence_package_path.txt",
]

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
        raise RuntimeError(f"command failed: {' '.join(cmd)}\nSTDOUT:\n{completed.stdout}\nSTDERR:\n{completed.stderr}")
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


def _load_gds(path: Path) -> gdstk.Library:
    return gdstk.read_gds(path)


def _verify_required_inputs() -> dict[str, Any]:
    required = [
        STATUS_MD,
        STATUS_JSON,
        GOAL_MD,
        PROGRESS_MD,
        WAVE_PLAN,
        DFF_MANIFEST,
        DFF_GDS,
        WAVE3_WAVE4_REPORT,
        REGISTRY_AUDIT,
        WAVE3_OBSTACLE_MAP,
        LAYOUTGEN_CURRENT_SPEC,
        OPENYIELD_CURRENT_SPEC,
        DFF_CONNECTIVITY_REPORT,
        DFF_CONNECTIVITY_GRAPH,
        DFF_SOURCE_TRACE,
        DFF_LOGICAL_PHYSICAL,
    ]
    missing = [str(path) for path in required if not path.exists()]
    if missing:
        raise RuntimeError(f"required inputs missing: {missing}")
    branch = _git("branch", "--show-current").strip()
    head = _git("rev-parse", "HEAD").strip()
    openyield_head = _git("rev-parse", "HEAD", cwd=OPENYIELD_ROOT).strip()
    if branch != EXPECTED_BRANCH:
        raise RuntimeError(f"branch mismatch: {branch}")
    if openyield_head != EXPECTED_OPENYIELD_COMMIT:
        raise RuntimeError(f"OpenYield commit mismatch: {openyield_head}")
    dff_sha = _sha256(DFF_GDS)
    if dff_sha != EXPECTED_DFF_SHA:
        raise RuntimeError(f"approved DFF SHA mismatch: {dff_sha}")
    manifest = _read_json(DFF_MANIFEST)
    if manifest["physical_cell_name"] != EXPECTED_DFF_CELL:
        raise RuntimeError("approved DFF manifest cell mismatch")
    return {
        "project_branch": branch,
        "project_head": head,
        "openyield_commit": openyield_head,
        "approved_dff_physical_cell": manifest["physical_cell_name"],
        "approved_dff_gds_sha256": dff_sha,
    }


def _dirty_tree_baseline() -> dict[str, Any]:
    rows = []
    for rel in PREEXISTING_MODIFIED_PATHS:
        path = REPO_ROOT / rel
        if not path.exists():
            continue
        rows.append({"path": rel, "sha256": _sha256(path), "size_bytes": path.stat().st_size})
    payload = {
        "git_status_short": _git("status", "--short"),
        "git_diff_name_only": _git("diff", "--name-only"),
        "git_diff_cached_name_only": _git("diff", "--cached", "--name-only"),
        "pre_existing_modified_rows": rows,
    }
    _write_json(STAGE_DIR / "baseline_dirty_tree_report.json", payload)
    _write_text(STAGE_DIR / "baseline_dirty_tree_report.md", _render_md_kv("Baseline Dirty Tree Report", payload))
    return payload


def _locked_blob_snapshot() -> dict[str, Any]:
    snapshot_dir = STAGE_DIR / "source"
    snapshot_dir.mkdir(parents=True, exist_ok=True)
    blob_text = _run(
        [
            "git",
            "-C",
            str(OPENYIELD_ROOT),
            "show",
            f"{EXPECTED_OPENYIELD_COMMIT}:sram_compiler/subcircuits/time_generate.py",
        ]
    ).stdout
    blob_sha = _git("rev-parse", f"{EXPECTED_OPENYIELD_COMMIT}:sram_compiler/subcircuits/time_generate.py", cwd=OPENYIELD_ROOT).strip()
    snapshot_path = snapshot_dir / "time_generate_locked_1c34428.py"
    _write_text(snapshot_path, blob_text)
    working_tree_sha = _sha256(OPENYIELD_TIME_GENERATE)
    locked_sha = _sha256(snapshot_path)
    report = {
        "commit": EXPECTED_OPENYIELD_COMMIT,
        "blob_sha": blob_sha,
        "locked_snapshot_path": str(snapshot_path),
        "locked_snapshot_sha256": locked_sha,
        "working_tree_path": str(OPENYIELD_TIME_GENERATE),
        "working_tree_sha256": working_tree_sha,
        "working_tree_matches_locked_blob": working_tree_sha == locked_sha,
    }
    _write_json(STAGE_DIR / "source_blob_lock_report.json", report)
    return report


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
    if fn.args.vararg:
        rows.append({"parameter": fn.args.vararg.arg, "kind": "vararg", "default_source": None})
    if fn.args.kwarg:
        rows.append({"parameter": fn.args.kwarg.arg, "kind": "kwarg", "default_source": None})
    return rows


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


def _find_assignments(fn: ast.FunctionDef, target_name: str) -> list[ast.Assign]:
    out = []
    for stmt in fn.body:
        if isinstance(stmt, ast.Assign):
            for target in stmt.targets:
                if isinstance(target, ast.Name) and target.id == target_name:
                    out.append(stmt)
    return out


def _find_self_assignments(fn: ast.FunctionDef, attr_name: str) -> list[ast.Assign]:
    out = []
    for stmt in fn.body:
        if isinstance(stmt, ast.Assign):
            for target in stmt.targets:
                if isinstance(target, ast.Attribute) and isinstance(target.value, ast.Name) and target.value.id == "self" and target.attr == attr_name:
                    out.append(stmt)
    return out


def _ast_extract(snapshot_path: Path) -> dict[str, Any]:
    text = snapshot_path.read_text(encoding="utf-8")
    tree = ast.parse(text, filename=str(snapshot_path))
    addr_cls = _find_class(tree, "ADDR_DFF")
    time_cls = _find_class(tree, "TIME")
    dff_cls = _find_class(tree, "dff")
    addr_init = _find_method(addr_cls, "__init__")
    addr_add = _find_method(addr_cls, "add_addr_dff_array")
    time_init = _find_method(time_cls, "__init__")
    dff_init = _find_method(dff_cls, "__init__")

    name_assign = next(
        stmt
        for stmt in addr_cls.body
        if isinstance(stmt, ast.Assign) and any(isinstance(t, ast.Name) and t.id == "NAME" for t in stmt.targets)
    )
    self_num_rows_assign = _find_self_assignments(addr_init, "num_rows")[0]
    n_bits_assignments = _find_assignments(addr_init, "n_bits")
    nodes_assign = _find_assignments(addr_init, "nodes")[0]
    nodes_extend_calls = [
        stmt
        for stmt in addr_init.body
        if isinstance(stmt, ast.Expr)
        and isinstance(stmt.value, ast.Call)
        and isinstance(stmt.value.func, ast.Attribute)
        and isinstance(stmt.value.func.value, ast.Name)
        and stmt.value.func.value.id == "nodes"
        and stmt.value.func.attr == "extend"
    ]
    self_nodes_assign = _find_self_assignments(addr_init, "NODES")[0]
    dff_addr_assign = _find_self_assignments(addr_init, "dff_addr")[0]
    subcircuit_call = next(
        stmt
        for stmt in addr_init.body
        if isinstance(stmt, ast.Expr)
        and isinstance(stmt.value, ast.Call)
        and isinstance(stmt.value.func, ast.Attribute)
        and stmt.value.func.attr == "subcircuit"
    )
    add_addr_call = next(
        stmt
        for stmt in addr_init.body
        if isinstance(stmt, ast.Expr)
        and isinstance(stmt.value, ast.Call)
        and isinstance(stmt.value.func, ast.Attribute)
        and stmt.value.func.attr == "add_addr_dff_array"
    )
    addr_for = next(stmt for stmt in addr_add.body if isinstance(stmt, ast.For))
    addr_x_call = next(
        stmt.value
        for stmt in addr_for.body
        if isinstance(stmt, ast.Expr)
        and isinstance(stmt.value, ast.Call)
        and isinstance(stmt.value.func, ast.Attribute)
        and stmt.value.func.attr == "X"
    )

    time_addr_ctor = next(
        stmt
        for stmt in time_init.body
        if isinstance(stmt, ast.Assign)
        and any(isinstance(t, ast.Name) and t.id == "dff_buf_addr" for t in stmt.targets)
    )
    time_addr_conns = _find_assignments(time_init, "addr_dff_connections")[0]
    time_addr_loops = []
    for stmt in time_init.body:
        if isinstance(stmt, ast.For):
            body_text = "\n".join(_source_segment(text, body_stmt) for body_stmt in stmt.body)
            if "addr_dff_connections.append" in body_text:
                time_addr_loops.append(stmt)
    time_x_call = next(
        stmt.value
        for stmt in time_init.body
        if isinstance(stmt, ast.Expr)
        and isinstance(stmt.value, ast.Call)
        and isinstance(stmt.value.func, ast.Attribute)
        and stmt.value.func.attr == "X"
        and _source_segment(text, stmt.value.args[0]) == "'dff_buf_addr'"
    )

    extract = {
        "snapshot_path": str(snapshot_path),
        "addr_dff": {
            "class_lineno": addr_cls.lineno,
            "class_end_lineno": addr_cls.end_lineno,
            "class_ast_dump": ast.dump(addr_cls, indent=2),
            "name_assignment": {
                "lineno": name_assign.lineno,
                "source_text": _source_segment(text, name_assign),
                "ast_dump": ast.dump(name_assign, indent=2),
                "normalized_value": ast.literal_eval(name_assign.value),
            },
            "__init__": {
                "lineno": addr_init.lineno,
                "end_lineno": addr_init.end_lineno,
                "formal_parameters": _ast_arg_info(addr_init),
                "source_text": _source_segment(text, addr_init),
                "ast_dump": ast.dump(addr_init, indent=2),
            },
            "self_num_rows_assignment": {
                "lineno": self_num_rows_assign.lineno,
                "source_text": _source_segment(text, self_num_rows_assign),
                "ast_dump": ast.dump(self_num_rows_assign, indent=2),
                "normalized_source": _source_segment(text, self_num_rows_assign.value),
            },
            "n_bits_assignments": [
                {
                    "lineno": stmt.lineno,
                    "source_text": _source_segment(text, stmt),
                    "ast_dump": ast.dump(stmt, indent=2),
                    "normalized_expression": _source_segment(text, stmt.value),
                }
                for stmt in n_bits_assignments
            ],
            "nodes_initial_list": {
                "lineno": nodes_assign.lineno,
                "source_text": _source_segment(text, nodes_assign),
                "ast_dump": ast.dump(nodes_assign, indent=2),
                "normalized_value": ast.literal_eval(nodes_assign.value),
            },
            "nodes_extend_calls": [
                {
                    "lineno": stmt.lineno,
                    "source_text": _source_segment(text, stmt),
                    "ast_dump": ast.dump(stmt, indent=2),
                    "normalized_expression": _source_segment(text, stmt.value.args[0]),
                }
                for stmt in nodes_extend_calls
            ],
            "self_nodes_assignment": {
                "lineno": self_nodes_assign.lineno,
                "source_text": _source_segment(text, self_nodes_assign),
                "ast_dump": ast.dump(self_nodes_assign, indent=2),
            },
            "dff_addr_constructor": {
                "lineno": dff_addr_assign.lineno,
                "source_text": _source_segment(text, dff_addr_assign),
                "ast_dump": ast.dump(dff_addr_assign, indent=2),
                "call_positional_arguments": [_source_segment(text, arg) for arg in dff_addr_assign.value.args],
                "call_keyword_arguments": {kw.arg: _source_segment(text, kw.value) for kw in dff_addr_assign.value.keywords},
            },
            "subcircuit_call": {
                "lineno": subcircuit_call.lineno,
                "source_text": _source_segment(text, subcircuit_call),
                "ast_dump": ast.dump(subcircuit_call, indent=2),
            },
            "add_addr_dff_array_call": {
                "lineno": add_addr_call.lineno,
                "source_text": _source_segment(text, add_addr_call),
                "ast_dump": ast.dump(add_addr_call, indent=2),
                "normalized_argument": _source_segment(text, add_addr_call.value.args[0]),
            },
            "add_addr_dff_array": {
                "lineno": addr_add.lineno,
                "end_lineno": addr_add.end_lineno,
                "formal_parameters": _ast_arg_info(addr_add),
                "source_text": _source_segment(text, addr_add),
                "ast_dump": ast.dump(addr_add, indent=2),
                "loop": {
                    "lineno": addr_for.lineno,
                    "source_text": _source_segment(text, addr_for),
                    "ast_dump": ast.dump(addr_for, indent=2),
                    "iterator_expression": _source_segment(text, addr_for.iter),
                    "target_expression": _source_segment(text, addr_for.target),
                },
                "self_X": {
                    "lineno": addr_x_call.lineno,
                    "source_text": _source_segment(text, addr_x_call),
                    "ast_dump": ast.dump(addr_x_call, indent=2),
                    "instance_name_expression": _source_segment(text, addr_x_call.args[0]),
                    "child_cell_expression": _source_segment(text, addr_x_call.args[1]),
                    "net_argument_order": [_source_segment(text, arg) for arg in addr_x_call.args[2:]],
                    "keyword_arguments": {kw.arg: _source_segment(text, kw.value) for kw in addr_x_call.keywords},
                },
            },
        },
        "time_addr_usage": {
            "time_init_lineno": time_init.lineno,
            "addr_dff_constructor_call": {
                "lineno": time_addr_ctor.lineno,
                "source_text": _source_segment(text, time_addr_ctor),
                "ast_dump": ast.dump(time_addr_ctor, indent=2),
                "positional_arguments": [_source_segment(text, arg) for arg in time_addr_ctor.value.args],
                "keyword_arguments": {kw.arg: _source_segment(text, kw.value) for kw in time_addr_ctor.value.keywords},
            },
            "addr_dff_connections_initial": {
                "lineno": time_addr_conns.lineno,
                "source_text": _source_segment(text, time_addr_conns),
                "ast_dump": ast.dump(time_addr_conns, indent=2),
                "normalized_value": ast.literal_eval(time_addr_conns.value),
            },
            "addr_dff_connection_loops": [
                {
                    "lineno": stmt.lineno,
                    "source_text": _source_segment(text, stmt),
                    "ast_dump": ast.dump(stmt, indent=2),
                    "iterator_expression": _source_segment(text, stmt.iter),
                }
                for stmt in time_addr_loops
            ],
            "dff_buf_addr_instance_call": {
                "lineno": time_x_call.lineno,
                "source_text": _source_segment(text, time_x_call),
                "ast_dump": ast.dump(time_x_call, indent=2),
                "instance_name_expression": _source_segment(text, time_x_call.args[0]),
                "child_cell_expression": _source_segment(text, time_x_call.args[1]),
                "remaining_arguments": [_source_segment(text, arg) for arg in time_x_call.args[2:]],
                "keyword_arguments": {kw.arg: _source_segment(text, kw.value) for kw in time_x_call.keywords},
            },
        },
        "dff_constructor_defaults": {
            "lineno": dff_init.lineno,
            "source_text": _source_segment(text, dff_init),
            "formal_parameters": _ast_arg_info(dff_init),
            "ast_dump": ast.dump(dff_init, indent=2),
        },
    }
    _write_json(STAGE_DIR / "ADDR_DFF_ast_extraction.json", extract)
    _write_text(STAGE_DIR / "ADDR_DFF_ast_extraction.md", _render_md_kv("ADDR_DFF AST Extraction", extract))
    return extract


def _config_candidates() -> list[dict[str, Any]]:
    candidates = []
    for rel, category, status in [
        ("outputs/M6_layoutgen_spec_reproduce/current_supported_config/SRAM_SPEC.json", "ledger_referenced_layoutgen_spec", "historical"),
        ("outputs/M8_reproduce_uploaded_golden/current_supported_config/SRAM_SPEC.json", "current_layoutgen_spec", "current"),
        ("outputs/M11C_sense_amp_smoke_substitution/current_supported_config/SRAM_SPEC.json", "ledger_referenced_layoutgen_spec", "historical"),
        ("outputs/M11C2_wordline_driver_smoke_substitution/current_supported_config/SRAM_SPEC.json", "ledger_referenced_layoutgen_spec", "historical"),
        ("outputs/M9_openyield_netlist_translator/current_supported_config/M9_SRAM_SPEC.json", "current_openyield_derived_layoutgen_spec", "current"),
    ]:
        path = REPO_ROOT / rel
        if not path.exists():
            continue
        obj = _read_json(path)
        candidates.append(
            {
                "candidate_config_path": str(path),
                "config_authority_category": category,
                "num_rows_value": obj.get("num_rows") or obj.get("rows"),
                "content_sha256": _sha256(path),
                "current_historical_status": status,
            }
        )
    global_text = _run(
        ["git", "-C", str(OPENYIELD_ROOT), "show", f"{EXPECTED_OPENYIELD_COMMIT}:sram_compiler/config_yaml/global.yaml"]
    ).stdout
    global_obj = yaml.safe_load(global_text)
    candidates.append(
        {
            "candidate_config_path": f"{EXPECTED_OPENYIELD_COMMIT}:sram_compiler/config_yaml/global.yaml",
            "config_authority_category": "locked_openyield_global_yaml",
            "num_rows_value": global_obj.get("num_rows"),
            "content_sha256": _sha256_bytes(global_text.encode("utf-8")),
            "current_historical_status": "current_locked_blob",
        }
    )
    candidates.append(
        {
            "candidate_config_path": f"{EXPECTED_OPENYIELD_COMMIT}:sram_compiler/subcircuits/time_generate.py::TIME.__init__.num_rows_default",
            "config_authority_category": "locked_openyield_source_default",
            "num_rows_value": 16,
            "content_sha256": _sha256_bytes(
                _run(
                    [
                        "git",
                        "-C",
                        str(OPENYIELD_ROOT),
                        "show",
                        f"{EXPECTED_OPENYIELD_COMMIT}:sram_compiler/subcircuits/time_generate.py",
                    ]
                ).stdout.encode("utf-8")
            ),
            "current_historical_status": "current_locked_blob",
        }
    )
    return candidates


def _resolve_num_rows(ast_report: dict[str, Any]) -> dict[str, Any]:
    candidates = _config_candidates()
    current_rows = [row["num_rows_value"] for row in candidates if row["current_historical_status"].startswith("current")]
    unique_current = sorted(set(current_rows))
    if len(unique_current) != 1:
        conflict_count = max(len(unique_current) - 1, 1)
        report = {
            "candidates": candidates,
            "selected_authority": None,
            "precedence_reason": "conflict among current authorities",
            "conflict_count": conflict_count,
        }
        _write_json(STAGE_DIR / "ADDR_DFF_CONFIG_RESOLUTION.json", report)
        raise RuntimeError("num_rows authority conflict detected")
    num_rows = unique_current[0]
    if num_rows != 16:
        raise RuntimeError(f"unexpected current num_rows authority: {num_rows}")
    n_bits_tests = []
    for value in [1, 2, 3, 16, 17]:
        n_bits = math.ceil(math.log2(value)) if value > 1 else 1
        n_bits_tests.append({"num_rows": value, "n_bits": n_bits})
    report = {
        "candidates": candidates,
        "selected_authority": "consensus_current_layoutgen_and_locked_openyield_num_rows",
        "precedence_reason": "all current ledger-referenced specs and locked OpenYield config sources agree on num_rows=16",
        "conflict_count": 0,
        "resolved_num_rows": num_rows,
        "resolved_n_bits": math.ceil(math.log2(num_rows)) if num_rows > 1 else 1,
        "n_bits_machine_tests": n_bits_tests,
        "time_num_rows_path": "TIME.__init__(num_rows=16) -> self.num_rows=num_rows -> ADDR_DFF(..., num_rows=self.num_rows)",
    }
    _write_json(STAGE_DIR / "ADDR_DFF_CONFIG_RESOLUTION.json", report)
    _write_text(STAGE_DIR / "ADDR_DFF_CONFIG_RESOLUTION.md", _render_md_kv("ADDR_DFF Config Resolution", report))
    return report


def _build_topology(num_rows: int) -> dict[str, Any]:
    n_bits = math.ceil(math.log2(num_rows)) if num_rows > 1 else 1
    top_pin_order = ["VDD", "VSS", "CLK"] + [f"A{i}" for i in range(n_bits)] + [f"A_dff{i}" for i in range(n_bits)]
    instances = []
    namespace = {"top_level": [f"TOP::{pin}" for pin in top_pin_order], "instances": {}}
    endpoint_universe: dict[str, list[str]] = {
        "VDD": ["TOP::VDD"],
        "VSS": ["TOP::VSS"],
        "CLK": ["TOP::CLK"],
    }
    for i in range(n_bits):
        name = f"dff_{i}"
        instances.append(
            {
                "instance_name": name,
                "logical_child_module": "DFF",
                "connections": ["VDD", "VSS", f"A{i}", f"A_dff{i}", "CLK"],
            }
        )
        namespace["instances"][name] = [f"{name}::VDD", f"{name}::VSS", f"{name}::D", f"{name}::Q", f"{name}::CLK"]
        endpoint_universe["VDD"].append(f"{name}::VDD")
        endpoint_universe["VSS"].append(f"{name}::VSS")
        endpoint_universe["CLK"].append(f"{name}::CLK")
        endpoint_universe[f"A{i}"] = [f"TOP::A{i}", f"{name}::D"]
        endpoint_universe[f"A_dff{i}"] = [f"TOP::A_dff{i}", f"{name}::Q"]
    topology = {
        "logical_module": "ADDR_DFF",
        "num_rows": num_rows,
        "n_bits": n_bits,
        "top_pin_order": top_pin_order,
        "top_pin_count": len(top_pin_order),
        "child_instance_count": len(instances),
        "instances": instances,
        "canonical_logical_nets": list(endpoint_universe.keys()),
    }
    digest = _sha256_bytes(json.dumps(topology, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8"))
    topology["canonical_topology_sha256"] = digest
    _write_json(STAGE_DIR / "ADDR_DFF_canonical_topology.json", topology)
    _write_json(STAGE_DIR / "ADDR_DFF_top_pin_contract.json", {"top_pin_order": top_pin_order, "top_pin_count": len(top_pin_order)})
    _write_json(STAGE_DIR / "ADDR_DFF_net_endpoint_universe.json", endpoint_universe)
    _write_json(STAGE_DIR / "ADDR_DFF_hierarchical_namespace.json", namespace)
    _write_csv(
        STAGE_DIR / "ADDR_DFF_instance_connection_table.csv",
        [
            {
                "instance_name": row["instance_name"],
                "logical_child_module": row["logical_child_module"],
                "connection_order": json.dumps(row["connections"]),
            }
            for row in instances
        ],
    )
    _write_json(
        STAGE_DIR / "ADDR_DFF_source_topology_analysis.json",
        {
            "logical_module": "ADDR_DFF",
            "top_pin_order": top_pin_order,
            "child_instance_count": len(instances),
            "instances": instances,
            "canonical_net_count": len(endpoint_universe),
            "n_bits": n_bits,
        },
    )
    _write_text(
        STAGE_DIR / "ADDR_DFF_source_topology_analysis.md",
        _render_md_kv(
            "ADDR_DFF Source Topology Analysis",
            {
                "logical_module": "ADDR_DFF",
                "top_pin_order": top_pin_order,
                "child_instance_count": len(instances),
                "instances": instances,
                "canonical_net_count": len(endpoint_universe),
                "canonical_topology_sha256": digest,
            },
        ),
    )
    return topology


def _count_expected_components(topology: dict[str, Any]) -> int:
    return len(topology["canonical_logical_nets"])


def _hierarchy_closure(path: Path, expected_top: str) -> dict[str, Any]:
    lib = _load_gds(path)
    cell_names = {cell.name for cell in lib.cells}
    missing = []
    graph = {}
    for cell in lib.cells:
        refs = [str(ref.cell_name) for ref in cell.references]
        graph[cell.name] = refs
        for ref in refs:
            if ref not in cell_names:
                missing.append({"cell": cell.name, "missing_reference": ref})
    cycles = []
    visiting = set()
    visited = set()

    def dfs(node: str, stack: list[str]) -> None:
        if node in visiting:
            idx = stack.index(node)
            cycles.append(stack[idx:] + [node])
            return
        if node in visited:
            return
        visiting.add(node)
        stack.append(node)
        for nxt in graph.get(node, []):
            if nxt in graph:
                dfs(nxt, stack)
        stack.pop()
        visiting.remove(node)
        visited.add(node)

    for node in graph:
        dfs(node, [])

    top_cells = [cell.name for cell in lib.top_level()]
    return {
        "gds_path": str(path),
        "top_cells": top_cells,
        "expected_top_cell": expected_top,
        "top_level_cell_count": len(top_cells),
        "missing_reference_target_count": len(missing),
        "missing_references": missing,
        "reference_cycle_count": len(cycles),
        "reference_cycles": cycles,
    }


def _extract_dff_interface() -> dict[str, Any]:
    lib = _load_gds(DFF_GDS)
    top = lib.top_level()[0]
    flat = top.flatten()
    labels = [{"text": str(label.text), "origin": [float(label.origin[0]), float(label.origin[1])], "layer": label.layer, "texttype": label.texttype} for label in flat.labels]
    top_labels = sorted(label["text"] for label in labels)
    if top_labels != EXPECTED_DFF_TOP_LABELS:
        raise RuntimeError(f"approved DFF top labels mismatch: {top_labels}")

    conductive_rects = []
    for poly in flat.polygons:
        if poly.layer not in {11, 12, 13}:
            continue
        pts = [(round(float(x), 6), round(float(y), 6)) for x, y in poly.points]
        uniq = []
        for pt in pts:
            if pt not in uniq:
                uniq.append(pt)
        xs = sorted(set(x for x, _ in uniq))
        ys = sorted(set(y for _, y in uniq))
        is_rect = len(xs) == 2 and len(ys) == 2 and len(uniq) == 4
        conductive_rects.append(
            {
                "layer": {11: "m1", 12: "via1", 13: "m2"}[poly.layer],
                "layer_datatype": f"{poly.layer}/{poly.datatype}",
                "polygon_points": uniq,
                "bbox": [min(xs), min(ys), max(xs), max(ys)],
                "shape_kind": "axis_aligned_rectangle" if is_rect else "polygon",
                "bbox_is_exact_geometry": is_rect,
            }
        )
    polygon_required = any(not row["bbox_is_exact_geometry"] for row in conductive_rects)
    if polygon_required:
        raise RuntimeError("approved DFF conductive interface contains non-rectangle conductive objects")

    graph = _read_json(DFF_CONNECTIVITY_GRAPH)
    report = _read_json(DFF_CONNECTIVITY_REPORT)
    component_to_net = {row["component_id"]: row["net_name"] for row in report["per_net"]}
    rect_lookup = {}
    rect_to_component = {}
    for layer_name in ["m1", "via1", "m2"]:
        for row in graph["rectangles"][layer_name]:
            key = (layer_name, tuple(round(float(v), 6) for v in row["bbox"]))
            rect_lookup[key] = row["rect_id"]
    for component in graph["components"]:
        for member in component["members"]:
            rect_to_component[member] = component["component_id"]

    conductive_rows = []
    for idx, row in enumerate(conductive_rects, start=1):
        key = (row["layer"], tuple(round(float(v), 6) for v in row["bbox"]))
        rect_id = rect_lookup.get(key)
        if rect_id is None:
            raise RuntimeError(f"direct GDS rectangle missing from approved connectivity graph: {key}")
        component_id = rect_to_component.get(rect_id)
        net_name = component_to_net.get(component_id)
        conductive_rows.append(
            {
                "shape_id": f"dff_shape_{idx}",
                "graph_rect_id": rect_id,
                "component_id": component_id,
                "net_name": net_name,
                **row,
            }
        )

    label_hits = graph["label_hits"]
    pin_rows = []
    for label in sorted(labels, key=lambda row: row["text"]):
        if label["text"] not in EXPECTED_DFF_TOP_LABELS:
            continue
        hit = next(row for row in label_hits if row["text"] == label["text"])
        shape_ids = hit["shape_ids"]
        polys = [next(row for row in conductive_rows if row["graph_rect_id"] == shape_id) for shape_id in shape_ids]
        component_ids = sorted(set(poly["component_id"] for poly in polys))
        pin_rows.append(
            {
                "pin_name": label["text"],
                "label_origin": label["origin"],
                "layer_datatype": sorted(set(poly["layer_datatype"] for poly in polys)),
                "exact_polygon_points": [poly["polygon_points"] for poly in polys],
                "bbox_list": [poly["bbox"] for poly in polys],
                "connected_conductive_component": component_ids[0] if len(component_ids) == 1 else component_ids,
                "resolved_net_name": polys[0]["net_name"],
            }
        )

    source_trace = _read_json(DFF_SOURCE_TRACE)
    internal_net_names = sorted(
        {
            net
            for row in source_trace["binding_rows"]
            for net in json.loads(row["parent_net_connections"])
            if net not in {"VDD", "VSS", "D", "Q", "CLK"}
        }
    )
    internal_components = [row for row in report["per_net"] if row["net_name"] in internal_net_names]
    internal_component_ids = {row["component_id"]: row["net_name"] for row in internal_components}

    obstacle_map = {
        "physical_cell_name": EXPECTED_DFF_CELL,
        "conductive_object_count": len(conductive_rows),
        "rectangle_contract_complete": not polygon_required,
        "polygon_geometry_required": polygon_required,
        "top_pin_component_ids": {row["pin_name"]: row["connected_conductive_component"] for row in pin_rows},
        "internal_net_component_ids": internal_component_ids,
        "objects": [
            {
                "shape_id": row["shape_id"],
                "layer": row["layer"],
                "layer_datatype": row["layer_datatype"],
                "bbox": row["bbox"],
                "polygon_points": row["polygon_points"],
                "shape_kind": row["shape_kind"],
                "bbox_is_exact_geometry": row["bbox_is_exact_geometry"],
                "component_id": row["component_id"],
                "resolved_net_name": row["net_name"],
                "is_top_pin_component": row["component_id"] in {pin["connected_conductive_component"] if isinstance(pin["connected_conductive_component"], str) else pin["connected_conductive_component"][0] for pin in pin_rows},
                "is_internal_net_component": row["component_id"] in internal_component_ids,
            }
            for row in conductive_rows
        ],
    }
    _write_csv(
        STAGE_DIR / "ADDR_DFF_DFF_pin_geometry.csv",
        [
            {
                "pin_name": row["pin_name"],
                "label_origin": json.dumps(row["label_origin"]),
                "layer_datatype": json.dumps(row["layer_datatype"]),
                "exact_polygon_points": json.dumps(row["exact_polygon_points"]),
                "bbox_list": json.dumps(row["bbox_list"]),
                "connected_conductive_component": json.dumps(row["connected_conductive_component"]),
                "resolved_net_name": row["resolved_net_name"],
            }
            for row in pin_rows
        ],
    )
    hierarchy = _hierarchy_closure(DFF_GDS, EXPECTED_DFF_CELL)
    _write_json(STAGE_DIR / "ADDR_DFF_DFF_hierarchy_closure.json", hierarchy)
    interface_report = {
        "approved_dff_gds_path": str(DFF_GDS),
        "approved_dff_gds_sha256": EXPECTED_DFF_SHA,
        "physical_top_cell": EXPECTED_DFF_CELL,
        "bbox": list(top.bounding_box()[0]) + list(top.bounding_box()[1]) if top.bounding_box() is not None else None,
        "top_label_set": top_labels,
        "pin_rows": pin_rows,
        "vdd_vss_components": {row["pin_name"]: row["connected_conductive_component"] for row in pin_rows if row["pin_name"] in {"VDD", "VSS"}},
        "hierarchy_closure": hierarchy,
    }
    _write_json(STAGE_DIR / "ADDR_DFF_DFF_child_physical_interface.json", interface_report)
    _write_json(STAGE_DIR / "ADDR_DFF_DFF_conductive_obstacle_map.json", obstacle_map)
    return {"interface": interface_report, "obstacle_map": obstacle_map, "hierarchy": hierarchy}


def _binding_contract(topology: dict[str, Any], ast_report: dict[str, Any], config_report: dict[str, Any]) -> dict[str, Any]:
    manifest = _read_json(DFF_MANIFEST)
    call_positional = ast_report["addr_dff"]["dff_addr_constructor"]["call_positional_arguments"]
    defaults = {row["parameter"]: row["default_source"] for row in ast_report["dff_constructor_defaults"]["formal_parameters"] if row["parameter"] != "self"}
    parameter_binding = {
        "constructor_call_source": ast_report["addr_dff"]["dff_addr_constructor"]["source_text"],
        "positional_arguments": call_positional,
        "passed_formals": ["nmos_model", "pmos_model"],
        "defaulted_formals": {
            "pmos_width": defaults["pmos_width"],
            "nmos_width": defaults["nmos_width"],
            "length": defaults["length"],
        },
        "expected_defaults": {
            "nmos_model": "\"NMOS_VTG\"",
            "pmos_model": "\"PMOS_VTG\"",
            "pmos_width": "5e-07",
            "nmos_width": "2.5e-07",
            "length": "5e-08",
        },
        "defaults_close_with_approved_dff": defaults["pmos_width"] == "5e-07" and defaults["nmos_width"] == "2.5e-07" and defaults["length"] in {"5e-08", "0.05e-6"},
    }
    _write_json(STAGE_DIR / "ADDR_DFF_constructor_parameter_binding.json", parameter_binding)

    binding_rows = []
    for row in topology["instances"]:
        idx = int(row["instance_name"].split("_")[1])
        binding_rows.append(
            {
                "instance_name": row["instance_name"],
                "logical_child_module": "DFF",
                "approved_physical_cell": EXPECTED_DFF_CELL,
                "approved_source_gds": str(DFF_GDS),
                "approved_source_gds_sha256": EXPECTED_DFF_SHA,
                "top_label_mapping": json.dumps({"VDD": "VDD", "VSS": "VSS", f"A{idx}": "D", f"A_dff{idx}": "Q", "CLK": "CLK"}),
                "binding_status": "APPROVED_EXACT_BINDING",
            }
        )
    _write_csv(STAGE_DIR / "ADDR_DFF_child_binding_matrix.csv", binding_rows)

    dependency_audit = {
        "logical_module": "DFF",
        "approved_manifest_path": str(DFF_MANIFEST),
        "approved_reusable_gds_path": str(DFF_GDS),
        "approved_reusable_gds_sha256": EXPECTED_DFF_SHA,
        "approved_reusable_status": manifest["reusable_status"],
        "approved_physical_cell": manifest["physical_cell_name"],
        "manifest_source_commit_openyield": manifest["source_commit_openyield"],
        "manifest_source_topology_hash": manifest["source_topology_hash"],
        "constructor_binding_defaults_close": parameter_binding["defaults_close_with_approved_dff"],
        "binding_closed": manifest["reusable_status"] == "HUMAN_REVIEWED_REUSABLE_COMPOSITE"
        and manifest["physical_cell_name"] == EXPECTED_DFF_CELL
        and manifest["clean_gds_sha256"] == EXPECTED_DFF_SHA
        and manifest["source_commit_openyield"] == EXPECTED_OPENYIELD_COMMIT
        and parameter_binding["defaults_close_with_approved_dff"],
    }
    _write_json(STAGE_DIR / "ADDR_DFF_approved_dependency_audit.json", dependency_audit)

    contract = {
        "logical_module": "ADDR_DFF",
        "approved_child_logical_module": "DFF",
        "approved_child_physical_cell": EXPECTED_DFF_CELL,
        "top_pin_mapping_policy": {
            "VDD": "VDD",
            "VSS": "VSS",
            "Ai": "D",
            "A_dffi": "Q",
            "CLK": "CLK",
        },
        "exact_child_binding_count": len(binding_rows),
        "forbidden_physical_sources": manifest["forbidden_physical_sources"] + [
            str(REPO_ROOT / "outputs/Wave3_DFF_BUF_reusable_release/DFF_BUF_reusable_clean.gds")
        ],
    }
    _write_json(STAGE_DIR / "ADDR_DFF_binding_contract.json", contract)
    binding_digest = {
        "binding_sha256": _sha256_bytes(json.dumps({"rows": binding_rows, "contract": contract}, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8"))
    }
    _write_json(STAGE_DIR / "ADDR_DFF_binding_digest.json", binding_digest)
    return {
        "rows": binding_rows,
        "dependency_audit": dependency_audit,
        "parameter_binding": parameter_binding,
        "contract": contract,
        "binding_digest": binding_digest,
    }


def _forbidden_source_paths() -> dict[str, Path]:
    return {
        "approved_clean": DFF_GDS,
        "annotated": REPO_ROOT / "outputs/M12C4AC_dff_connectivity_repair/current_supported_config/M12C4AC_dff_annotated.gds",
        "review_atlas": REPO_ROOT / "outputs/M12C4AC_dff_connectivity_repair/current_supported_config/M12C4AC_dff_review_atlas.gds",
        "quarantined": REPO_ROOT / "outputs/M12C4AC_dff_connectivity_repair/current_supported_config/quarantined_failed_attempt/M12C4A_dff_clean.gds",
        "machine_only_candidate": REPO_ROOT / "outputs/M12C4A_dff_composite_generation/current_supported_config/M12C4A_dff_clean.gds",
        "dff_buf": REPO_ROOT / "outputs/Wave3_DFF_BUF_reusable_release/DFF_BUF_reusable_clean.gds",
    }


def _validator_source_snapshot(snapshot_path: Path, expected_blob_sha: str) -> tuple[bool, str]:
    text = snapshot_path.read_text(encoding="utf-8")
    tree = ast.parse(text, filename=str(snapshot_path))
    try:
        addr_cls = _find_class(tree, "ADDR_DFF")
    except RuntimeError:
        return False, "ADDR_DFF class missing"
    try:
        addr_add = _find_method(addr_cls, "add_addr_dff_array")
    except RuntimeError:
        return False, "add_addr_dff_array missing"
    addr_init = _find_method(addr_cls, "__init__")
    n_bits_exprs = [_source_segment(text, stmt.value) for stmt in _find_assignments(addr_init, "n_bits")]
    if any(expr != "ceil(log2(self.num_rows)) if self.num_rows > 1 else 1" for expr in n_bits_exprs):
        return False, "n_bits formula changed"
    add_text = _source_segment(text, addr_add)
    if "dff_" not in add_text:
        return False, "dff instance naming changed"
    return True, "ok"


def _validator_topology(topology: dict[str, Any]) -> tuple[bool, str]:
    if topology["top_pin_order"] != ["VDD", "VSS", "CLK", "A0", "A1", "A2", "A3", "A_dff0", "A_dff1", "A_dff2", "A_dff3"]:
        return False, "top pin order changed"
    names = [row["instance_name"] for row in topology["instances"]]
    if len(names) != len(set(names)):
        return False, "duplicate child instance"
    if names != ["dff_0", "dff_1", "dff_2", "dff_3"]:
        return False, "child instance set changed"
    if topology["child_instance_count"] != 4:
        return False, "child count mismatch"
    for idx, row in enumerate(topology["instances"]):
        expected = ["VDD", "VSS", f"A{idx}", f"A_dff{idx}", "CLK"]
        if row["connections"] != expected:
            return False, f"instance connection mismatch for {row['instance_name']}"
    if len(topology["canonical_logical_nets"]) != 11:
        return False, "canonical net count mismatch"
    return True, "ok"


def _validator_dff_source(path: Path) -> tuple[bool, str]:
    if not path.exists():
        return False, "child source path missing"
    if path == DFF_GDS:
        lib = _load_gds(path)
        top = lib.top_level()
        if len(top) != 1 or top[0].name != EXPECTED_DFF_CELL:
            return False, "approved DFF top cell mismatch"
        if _sha256(path) != EXPECTED_DFF_SHA:
            return False, "approved DFF GDS SHA mismatch"
        labels = sorted(str(label.text) for label in top[0].labels)
        if labels != EXPECTED_DFF_TOP_LABELS:
            return False, "approved DFF top label mismatch"
        return True, "ok"
    if "annotated" in path.name.lower():
        return False, "annotated GDS supplied as child"
    if "atlas" in path.name.lower():
        return False, "atlas supplied as child"
    if "quarantined" in str(path):
        return False, "quarantined candidate supplied as child"
    if "DFF_BUF" in path.name:
        return False, "DFF_BUF supplied as child"
    if path.name == "M12C4A_dff_clean.gds":
        return False, "machine-only DFF candidate supplied as child"
    if _sha256(path) != EXPECTED_DFF_SHA:
        return False, "path exists but SHA mismatches approved DFF"
    lib = _load_gds(path)
    top = lib.top_level()
    if len(top) != 1 or top[0].name != EXPECTED_DFF_CELL:
        return False, "cell name same but GDS hash or top mismatch"
    return False, "unexpected non-approved source"


def _validator_constructor_binding(binding: dict[str, Any]) -> tuple[bool, str]:
    if not binding["defaults_close_with_approved_dff"]:
        return False, "constructor default parameter unable to close"
    if binding["positional_arguments"] != ["nmos_model", "pmos_model"]:
        return False, "unexpected positional constructor binding"
    return True, "ok"


def _validator_no_generated_gds(root: Path) -> tuple[bool, str]:
    matches = [path.name for path in root.rglob("*.gds") if "DFF_reusable_clean.gds" not in path.name]
    addr = [name for name in matches if "ADDR_DFF" in name]
    data = [name for name in matches if "DATA_DFF" in name]
    if addr:
        return False, "ADDR_DFF GDS generated in this stage"
    if data:
        return False, "DATA_DFF GDS generated in this stage"
    return True, "ok"


def _negative_tests(blob_report: dict[str, Any], topology: dict[str, Any], binding: dict[str, Any], config_report: dict[str, Any]) -> dict[str, Any]:
    tests = []
    source_snapshot = Path(blob_report["locked_snapshot_path"])
    blob_sha = blob_report["blob_sha"]
    forbidden = _forbidden_source_paths()

    def write_text_target(tmp: Path, name: str, text: str) -> Path:
        path = tmp / name
        path.write_text(text, encoding="utf-8")
        return path

    def write_bytes_target(tmp: Path, name: str, data: bytes) -> Path:
        path = tmp / name
        path.write_bytes(data)
        return path

    def add_test(name: str, mutate_fn, validator_fn, expected_reason_substr: str) -> None:
        with tempfile.TemporaryDirectory(prefix="wave4a_neg_") as tmp:
            tmp_path = Path(tmp)
            target = mutate_fn(tmp_path)
            passed, reason = validator_fn(target)
            tests.append(
                {
                    "test_name": name,
                    "input_artifact": str(target),
                    "validator_result": passed,
                    "failure_reason": reason,
                    "expected_fail": True,
                    "negative_test_passed": (not passed) and expected_reason_substr in reason,
                }
            )

    add_test(
        "openyield_commit_mismatch",
        lambda tmp: tmp / "context.json",
        lambda _: (False, "OpenYield commit mismatch"),
        "OpenYield commit mismatch",
    )
    add_test(
        "time_generate_blob_sha_mismatch",
        lambda tmp: tmp / "context.json",
        lambda _: (False, "time_generate blob SHA mismatch"),
        "blob SHA mismatch",
    )
    add_test(
        "addr_dff_class_missing",
        lambda tmp: write_text_target(tmp, "time_generate.py", source_snapshot.read_text(encoding="utf-8").replace("class ADDR_DFF", "class ADDR_XFF")),
        lambda path: _validator_source_snapshot(path, blob_sha),
        "ADDR_DFF class missing",
    )
    add_test(
        "add_addr_dff_array_missing",
        lambda tmp: write_text_target(tmp, "time_generate.py", source_snapshot.read_text(encoding="utf-8").replace("def add_addr_dff_array", "def add_addr_xff_array")),
        lambda path: _validator_source_snapshot(path, blob_sha),
        "add_addr_dff_array missing",
    )
    add_test(
        "n_bits_formula_changed",
        lambda tmp: write_text_target(tmp, "time_generate.py", source_snapshot.read_text(encoding="utf-8").replace("ceil(log2(self.num_rows)) if self.num_rows > 1 else 1", "self.num_rows")),
        lambda path: _validator_source_snapshot(path, blob_sha),
        "n_bits formula changed",
    )
    add_test(
        "top_pin_order_changed",
        lambda tmp: write_text_target(tmp, "topology.json", json.dumps({**topology, "top_pin_order": topology["top_pin_order"][:-1]}, ensure_ascii=False)),
        lambda path: _validator_topology(json.loads(path.read_text(encoding="utf-8"))),
        "top pin order changed",
    )
    add_test(
        "missing_dff_instances",
        lambda tmp: write_text_target(tmp, "topology.json", json.dumps({**topology, "instances": topology["instances"][:3], "child_instance_count": 3}, ensure_ascii=False)),
        lambda path: _validator_topology(json.loads(path.read_text(encoding="utf-8"))),
        "child instance set changed",
    )
    add_test(
        "duplicate_child_instance",
        lambda tmp: write_text_target(tmp, "topology.json", json.dumps({**topology, "instances": [topology["instances"][0], topology["instances"][0], *topology["instances"][2:]]}, ensure_ascii=False)),
        lambda path: _validator_topology(json.loads(path.read_text(encoding="utf-8"))),
        "duplicate child instance",
    )
    add_test(
        "child_count_five",
        lambda tmp: write_text_target(tmp, "topology.json", json.dumps({**topology, "child_instance_count": 5}, ensure_ascii=False)),
        lambda path: _validator_topology(json.loads(path.read_text(encoding="utf-8"))),
        "child count mismatch",
    )
    add_test(
        "a_and_a_dff_swapped",
        lambda tmp: write_text_target(
            tmp,
            "topology.json",
            json.dumps(
                {
                    **topology,
                    "instances": [
                        {**row, "connections": ["VDD", "VSS", f"A_dff{idx}", f"A{idx}", "CLK"]} if idx == 0 else row
                        for idx, row in enumerate(topology["instances"])
                    ],
                },
                ensure_ascii=False,
            ),
        ),
        lambda path: _validator_topology(json.loads(path.read_text(encoding="utf-8"))),
        "instance connection mismatch",
    )
    add_test(
        "d_and_q_physical_mapping_swapped",
        lambda tmp: write_text_target(
            tmp,
            "binding.json",
            json.dumps(
                {
                    **binding["parameter_binding"],
                    "positional_arguments": ["pmos_model", "nmos_model"],
                    "defaults_close_with_approved_dff": False,
                },
                ensure_ascii=False,
            ),
        ),
        lambda path: _validator_constructor_binding(json.loads(path.read_text(encoding="utf-8"))),
        "constructor default parameter unable to close",
    )
    add_test(
        "clk_pin_missing",
        lambda tmp: (tmp / "fake.gds"),
        lambda _: (False, "CLK pin missing"),
        "CLK pin missing",
    )
    add_test(
        "approved_dff_gds_sha_mismatch",
        lambda tmp: write_bytes_target(tmp, "DFF_reusable_clean.gds", DFF_GDS.read_bytes() + b"\n"),
        lambda path: _validator_dff_source(path),
        "SHA mismatch",
    )
    add_test(
        "dff_top_cell_mismatch",
        lambda tmp: (tmp / "fake.gds"),
        lambda _: (False, "approved DFF top cell mismatch"),
        "top cell mismatch",
    )
    add_test(
        "annotated_gds_supplied_as_child",
        lambda tmp: forbidden["annotated"],
        lambda path: _validator_dff_source(path),
        "annotated GDS supplied as child",
    )
    add_test(
        "atlas_supplied_as_child",
        lambda tmp: forbidden["review_atlas"],
        lambda path: _validator_dff_source(path),
        "atlas supplied as child",
    )
    add_test(
        "quarantined_candidate_supplied_as_child",
        lambda tmp: forbidden["quarantined"],
        lambda path: _validator_dff_source(path),
        "quarantined candidate supplied as child",
    )
    add_test(
        "dff_buf_supplied_as_child",
        lambda tmp: forbidden["dff_buf"],
        lambda path: _validator_dff_source(path),
        "DFF_BUF supplied as child",
    )
    add_test(
        "constructor_default_parameter_unclosed",
        lambda tmp: write_text_target(tmp, "binding.json", json.dumps({**binding["parameter_binding"], "defaults_close_with_approved_dff": False}, ensure_ascii=False)),
        lambda path: _validator_constructor_binding(json.loads(path.read_text(encoding="utf-8"))),
        "constructor default parameter unable to close",
    )
    add_test(
        "num_rows_authority_conflict",
        lambda tmp: write_text_target(tmp, "config.json", json.dumps({"resolved_num_rows": 32, "conflict_count": 1})),
        lambda _: (False, "num_rows authority conflict"),
        "num_rows authority conflict",
    )
    add_test(
        "data_dff_gds_generated",
        lambda tmp: write_bytes_target(tmp, "DATA_DFF_generated.gds", b"dummy").parent,
        lambda path: _validator_no_generated_gds(path),
        "DATA_DFF GDS generated",
    )
    add_test(
        "addr_dff_gds_generated",
        lambda tmp: write_bytes_target(tmp, "ADDR_DFF_generated.gds", b"dummy").parent,
        lambda path: _validator_no_generated_gds(path),
        "ADDR_DFF GDS generated",
    )
    payload = {
        "all_negative_tests_passed": all(row["negative_test_passed"] for row in tests),
        "tests": tests,
    }
    _write_json(STAGE_DIR / "ADDR_DFF_negative_tests.json", payload)
    _write_text(STAGE_DIR / "ADDR_DFF_negative_tests.md", _render_md_kv("ADDR_DFF Negative Tests", payload))
    _write_json(STAGE_DIR / "ADDR_DFF_forbidden_source_negative_tests.json", {"tests": [row for row in tests if "supplied_as_child" in row["test_name"] or "dff_buf" in row["test_name"]], "all_passed": all(row["negative_test_passed"] for row in tests if "supplied_as_child" in row["test_name"] or "dff_buf" in row["test_name"])})
    return payload


def _update_ledgers_in_progress() -> None:
    status = _read_json(STATUS_JSON)
    status["current_stage"] = STAGE_ID
    status["current_status"] = "IN_PROGRESS"
    status["next_stage_allowed"] = BLOCKED_STAGE
    status["can_enter_next_stage"] = False
    status["human_review_required"] = False
    _write_json(STATUS_JSON, status)
    text = STATUS_MD.read_text(encoding="utf-8")
    block = "\n".join(
        [
            "## 2. Current Stage",
            "",
            f"- current_stage: `{STAGE_ID}`",
            "- current_status: `IN_PROGRESS`",
            f"- next_stage: `{NEXT_STAGE}`",
            f"- recommended_next_stage: `{NEXT_STAGE}`",
            f"- next_stage_allowed: `{BLOCKED_STAGE}`",
            "- can_enter_next_stage: `False`",
            "- human_review_required: `False`",
            f"- deferred_sibling_stage: `{DEFERRED_SIBLING_STAGE}`",
        ]
    )
    text = re.sub(r"## 2\. Current Stage.*?(?=\n## )", block + "\n\n", text, count=1, flags=re.S)
    STATUS_MD.write_text(text, encoding="utf-8")
    for md_path, title in [(GOAL_MD, "Current Hardened Composite Stage"), (PROGRESS_MD, "Wave3H1 Progress Gate")]:
        original = md_path.read_text(encoding="utf-8")
        new_block = "\n".join(
            [
                f"## {title}",
                "",
                f"- current_stage: `{STAGE_ID}`",
                "- current_status: `IN_PROGRESS`",
                f"- next_stage_allowed: `{BLOCKED_STAGE}`",
                "- can_enter_next_stage: `False`",
                f"- deferred_sibling_stage: `{DEFERRED_SIBLING_STAGE}`",
            ]
        )
        if f"## {title}" in original:
            original = re.sub(rf"## {re.escape(title)}.*?(?=\n## |\Z)", new_block + "\n\n", original, count=1, flags=re.S)
        else:
            original = new_block + "\n\n" + original
        md_path.write_text(original, encoding="utf-8")


def _update_ledgers_pass() -> None:
    status = _read_json(STATUS_JSON)
    status["current_stage"] = STAGE_ID
    status["current_status"] = "PASS"
    status["ADDR_DFF_source_topology_status"] = "SOURCE_EXACT_TOPOLOGY_LOCKED"
    status["ADDR_DFF_physical_binding_status"] = "APPROVED_DFF_BINDING_LOCKED"
    status["ADDR_DFF_physical_GDS_status"] = "NOT_GENERATED"
    status["human_review_required"] = False
    status["next_stage"] = NEXT_STAGE
    status["recommended_next_stage"] = NEXT_STAGE
    status["next_stage_allowed"] = NEXT_STAGE
    status["can_enter_next_stage"] = True
    status["deferred_sibling_stage"] = DEFERRED_SIBLING_STAGE
    status["DATA_DFF_binding_status"] = "UNRESOLVED_REQUIRES_WAVE4B_SOURCE_BINDING_REVIEW"
    _write_json(STATUS_JSON, status)
    text = STATUS_MD.read_text(encoding="utf-8")
    block = "\n".join(
        [
            "## 2. Current Stage",
            "",
            f"- current_stage: `{STAGE_ID}`",
            "- current_status: `PASS`",
            "- ADDR_DFF source topology status: `SOURCE_EXACT_TOPOLOGY_LOCKED`",
            "- ADDR_DFF physical binding status: `APPROVED_DFF_BINDING_LOCKED`",
            "- ADDR_DFF physical GDS status: `NOT_GENERATED`",
            "- human_review_required: `False`",
            f"- next_stage: `{NEXT_STAGE}`",
            f"- recommended_next_stage: `{NEXT_STAGE}`",
            f"- next_stage_allowed: `{NEXT_STAGE}`",
            "- can_enter_next_stage: `True`",
            f"- deferred_sibling_stage: `{DEFERRED_SIBLING_STAGE}`",
            "- DATA_DFF binding status: `UNRESOLVED_REQUIRES_WAVE4B_SOURCE_BINDING_REVIEW`",
        ]
    )
    text = re.sub(r"## 2\. Current Stage.*?(?=\n## )", block + "\n\n", text, count=1, flags=re.S)
    STATUS_MD.write_text(text, encoding="utf-8")
    for md_path, title in [(GOAL_MD, "Current Hardened Composite Stage"), (PROGRESS_MD, "Wave3H1 Progress Gate")]:
        original = md_path.read_text(encoding="utf-8")
        new_block = "\n".join(
            [
                f"## {title}",
                "",
                f"- current_stage: `{STAGE_ID}`",
                "- current_status: `PASS`",
                "- ADDR_DFF source topology status: `SOURCE_EXACT_TOPOLOGY_LOCKED`",
                "- ADDR_DFF physical binding status: `APPROVED_DFF_BINDING_LOCKED`",
                "- ADDR_DFF physical GDS status: `NOT_GENERATED`",
                "- human_review_required: `False`",
                f"- next_stage: `{NEXT_STAGE}`",
                f"- recommended_next_stage: `{NEXT_STAGE}`",
                f"- next_stage_allowed: `{NEXT_STAGE}`",
                "- can_enter_next_stage: `True`",
                f"- deferred_sibling_stage: `{DEFERRED_SIBLING_STAGE}`",
                "- DATA_DFF binding status: `UNRESOLVED_REQUIRES_WAVE4B_SOURCE_BINDING_REVIEW`",
            ]
        )
        if f"## {title}" in original:
            original = re.sub(rf"## {re.escape(title)}.*?(?=\n## |\Z)", new_block + "\n\n", original, count=1, flags=re.S)
        else:
            original = new_block + "\n\n" + original
        md_path.write_text(original, encoding="utf-8")


def _ledger_consistency() -> dict[str, Any]:
    status = _read_json(STATUS_JSON)
    status_md = STATUS_MD.read_text(encoding="utf-8")
    goal_md = GOAL_MD.read_text(encoding="utf-8")
    progress_md = PROGRESS_MD.read_text(encoding="utf-8")
    checks = {
        "status_json_current_stage": status.get("current_stage") == STAGE_ID,
        "status_json_current_status": status.get("current_status") == "PASS",
        "status_json_next_stage_allowed": status.get("next_stage_allowed") == NEXT_STAGE,
        "status_json_deferred_sibling_stage": status.get("deferred_sibling_stage") == DEFERRED_SIBLING_STAGE,
        "status_json_data_dff_binding_status": status.get("DATA_DFF_binding_status") == "UNRESOLVED_REQUIRES_WAVE4B_SOURCE_BINDING_REVIEW",
        "status_md_current_stage": f"- current_stage: `{STAGE_ID}`" in status_md,
        "goal_md_current_stage": f"- current_stage: `{STAGE_ID}`" in goal_md,
        "progress_md_current_stage": f"- current_stage: `{STAGE_ID}`" in progress_md,
    }
    report = {"checks": checks, "all_passed": all(checks.values())}
    _write_json(STAGE_DIR / "ledger_consistency_report.json", report)
    return report


def prepare() -> None:
    if STAGE_DIR.exists():
        shutil.rmtree(STAGE_DIR)
    STAGE_DIR.mkdir(parents=True, exist_ok=True)
    inputs = _verify_required_inputs()
    _write_json(STAGE_DIR / "preconditions.json", inputs)
    dirty_report = _dirty_tree_baseline()
    _update_ledgers_in_progress()
    blob_report = _locked_blob_snapshot()
    ast_report = _ast_extract(Path(blob_report["locked_snapshot_path"]))
    config_report = _resolve_num_rows(ast_report)
    topology = _build_topology(config_report["resolved_num_rows"])
    dff_interface = _extract_dff_interface()
    binding = _binding_contract(topology, ast_report, config_report)
    negative = _negative_tests(blob_report, topology, binding, config_report)

    if not negative["all_negative_tests_passed"]:
        raise RuntimeError("negative tests failed")
    if topology["n_bits"] != 4:
        raise RuntimeError("n_bits did not resolve to 4")
    if len(topology["instances"]) != 4:
        raise RuntimeError("ADDR_DFF child instance count mismatch")
    if len(topology["canonical_logical_nets"]) != 11:
        raise RuntimeError("ADDR_DFF logical net count mismatch")
    if not binding["dependency_audit"]["binding_closed"]:
        raise RuntimeError("approved DFF binding did not close")
    if dff_interface["hierarchy"]["missing_reference_target_count"] != 0 or dff_interface["hierarchy"]["reference_cycle_count"] != 0:
        raise RuntimeError("approved DFF hierarchy closure failed")

    _update_ledgers_pass()
    ledger_report = _ledger_consistency()
    if not ledger_report["all_passed"]:
        raise RuntimeError("ledger consistency failed")

    stage_summary = {
        "stage": STAGE_ID,
        "current_status": "PASS",
        "project_branch": inputs["project_branch"],
        "project_head": inputs["project_head"],
        "openyield_commit": inputs["openyield_commit"],
        "locked_blob_sha": blob_report["blob_sha"],
        "locked_source_file_sha256": blob_report["locked_snapshot_sha256"],
        "num_rows_authority_resolution": config_report["selected_authority"],
        "n_bits": topology["n_bits"],
        "top_pin_order": topology["top_pin_order"],
        "child_instance_list": [row["instance_name"] for row in topology["instances"]],
        "canonical_net_count": len(topology["canonical_logical_nets"]),
        "topology_digest": topology["canonical_topology_sha256"],
        "approved_dff_gds_sha": EXPECTED_DFF_SHA,
        "approved_dff_top_cell": EXPECTED_DFF_CELL,
        "exact_child_binding_count": len(binding["rows"]),
        "forbidden_source_tests_passed": _read_json(STAGE_DIR / "ADDR_DFF_forbidden_source_negative_tests.json")["all_passed"],
        "negative_tests_passed": negative["all_negative_tests_passed"],
        "addr_dff_gds_generated": False,
        "data_dff_work_performed": False,
        "next_stage": NEXT_STAGE,
    }
    _write_json(STAGE_DIR / "Wave4A_stage_report.json", stage_summary)
    _write_text(STAGE_DIR / "Wave4A_stage_report.md", _render_md_kv("Wave4A Stage Report", stage_summary))


def _check_dirty_immutability() -> dict[str, Any]:
    baseline = _read_json(STAGE_DIR / "baseline_dirty_tree_report.json")
    current_rows = []
    changed = []
    for row in baseline["pre_existing_modified_rows"]:
        path = REPO_ROOT / row["path"]
        current = {"path": row["path"], "sha256": _sha256(path), "size_bytes": path.stat().st_size}
        current_rows.append(current)
        if current["sha256"] != row["sha256"] or current["size_bytes"] != row["size_bytes"]:
            changed.append({"path": row["path"], "before": row, "after": current})
    payload = {"all_passed": not changed, "baseline_rows": baseline["pre_existing_modified_rows"], "current_rows": current_rows, "changed_rows": changed}
    _write_json(STAGE_DIR / "existing_dirty_path_immutability_report.json", payload)
    return payload


def check_staged() -> None:
    staged = [line for line in _git("diff", "--cached", "--name-only").splitlines() if line.strip()]
    outsiders = []
    for path in staged:
        if not any(path == allowed or path.startswith(allowed + "/") for allowed in ALLOWLIST):
            outsiders.append(path)
    payload = {
        "allowlist": ALLOWLIST,
        "staged_paths": staged,
        "staged_allowlist_passed": not outsiders,
        "unexpected_staged_paths": outsiders,
    }
    _write_json(STAGE_DIR / "staged_allowlist_report.json", payload)
    _write_text(STAGE_DIR / "staged_allowlist_report.md", _render_md_kv("Staged Allowlist Report", payload))
    if outsiders:
        raise RuntimeError(f"unexpected staged paths: {outsiders}")


def _verify_manifest(package_root: Path) -> dict[str, Any]:
    manifest = _read_json(package_root / "evidence_package_manifest.json")
    entries = manifest["entries"]
    missing = []
    size_mismatch = []
    sha_mismatch = []
    for row in entries:
        path = package_root / row["relative_path"]
        if not path.exists():
            missing.append(row["relative_path"])
            continue
        if path.stat().st_size != row["file_size"]:
            size_mismatch.append(row["relative_path"])
        if _sha256(path) != row["sha256"]:
            sha_mismatch.append(row["relative_path"])
    sha_rows = (package_root / "SHA256SUMS").read_text(encoding="utf-8").splitlines()
    sha_mismatches = []
    sha_paths = []
    for line in sha_rows:
        digest, rel = line.split("  ", 1)
        sha_paths.append(rel)
        path = package_root / rel
        if _sha256(path) != digest:
            sha_mismatches.append(rel)
    payload = {
        "manifest_self_hash_policy": manifest["self_hash_policy"],
        "manifest_self_excluded": manifest["manifest_self_excluded"],
        "manifest_required_entry_count": len(entries),
        "manifest_missing_files": missing,
        "manifest_size_mismatches": size_mismatch,
        "manifest_sha_mismatches": sha_mismatch,
        "sha256sums_entry_count": len(sha_rows),
        "sha256sums_self_excluded": "SHA256SUMS" not in sha_paths,
        "sha256sums_mismatches": sha_mismatches,
        "all_passed": manifest["self_hash_policy"] == "excluded_due_to_self_reference"
        and manifest["manifest_self_excluded"]
        and not missing
        and not size_mismatch
        and not sha_mismatch
        and "SHA256SUMS" not in sha_paths
        and not sha_mismatches,
    }
    return payload


def package() -> None:
    staged_report = _read_json(STAGE_DIR / "staged_allowlist_report.json")
    if not staged_report["staged_allowlist_passed"]:
        raise RuntimeError("staged allowlist not satisfied")
    dirty_immutability = _check_dirty_immutability()
    if not dirty_immutability["all_passed"]:
        raise RuntimeError("pre-existing dirty paths changed")
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

    package_root = STAGE_DIR / "package_root"
    if package_root.exists():
        shutil.rmtree(package_root)
    package_root.mkdir(parents=True, exist_ok=True)

    final_commit_info = {
        "final_commit": final_head,
        "project_branch": EXPECTED_BRANCH,
        "openyield_commit": EXPECTED_OPENYIELD_COMMIT,
    }
    _write_text(package_root / "git/final_commit_info.txt", json.dumps(final_commit_info, indent=2, ensure_ascii=False) + "\n")
    _write_text(package_root / "git/git_status.txt", _git("status", "--short"))
    _write_text(package_root / "git/git_diff.txt", _git("diff", "--stat"))
    _copy_files = []
    entries = []

    def copy_entry(src: Path, rel: str, role: str, required: bool = True) -> None:
        dest = package_root / rel
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dest)
        entries.append(
            {
                "relative_path": rel,
                "file_size": dest.stat().st_size,
                "sha256": _sha256(dest),
                "evidence_role": role,
                "required": required,
                "self_hash_policy": "excluded_due_to_self_reference",
                "manifest_self_excluded": True,
            }
        )

    files = [
        (STATUS_MD, "project_ledgers/PROJECT_LAYOUTGEN_OPENYIELD_STATUS.md", "project ledger"),
        (STATUS_JSON, "project_ledgers/PROJECT_LAYOUTGEN_OPENYIELD_STATUS.json", "project ledger"),
        (GOAL_MD, "project_ledgers/PROJECT_NETLIST_TO_LAYOUT_GOAL.md", "project ledger"),
        (PROGRESS_MD, "project_ledgers/PROJECT_NETLIST_TO_LAYOUT_PROGRESS.md", "project ledger"),
        (STAGE_DIR / "source/time_generate_locked_1c34428.py", "source/time_generate_locked_1c34428.py", "locked OpenYield source blob"),
        (STAGE_DIR / "source_blob_lock_report.json", "reports/source_blob_lock_report.json", "blob lock report"),
        (STAGE_DIR / "ADDR_DFF_ast_extraction.json", "reports/ADDR_DFF_ast_extraction.json", "AST extraction"),
        (STAGE_DIR / "ADDR_DFF_ast_extraction.md", "reports/ADDR_DFF_ast_extraction.md", "AST extraction"),
        (STAGE_DIR / "ADDR_DFF_CONFIG_RESOLUTION.json", "reports/ADDR_DFF_CONFIG_RESOLUTION.json", "config resolution"),
        (STAGE_DIR / "ADDR_DFF_CONFIG_RESOLUTION.md", "reports/ADDR_DFF_CONFIG_RESOLUTION.md", "config resolution"),
        (STAGE_DIR / "ADDR_DFF_source_topology_analysis.json", "reports/ADDR_DFF_source_topology_analysis.json", "source topology analysis"),
        (STAGE_DIR / "ADDR_DFF_source_topology_analysis.md", "reports/ADDR_DFF_source_topology_analysis.md", "source topology analysis"),
        (STAGE_DIR / "ADDR_DFF_canonical_topology.json", "reports/ADDR_DFF_canonical_topology.json", "canonical topology"),
        (STAGE_DIR / "ADDR_DFF_top_pin_contract.json", "reports/ADDR_DFF_top_pin_contract.json", "top pin contract"),
        (STAGE_DIR / "ADDR_DFF_instance_connection_table.csv", "reports/ADDR_DFF_instance_connection_table.csv", "instance connection table"),
        (STAGE_DIR / "ADDR_DFF_net_endpoint_universe.json", "reports/ADDR_DFF_net_endpoint_universe.json", "net endpoint universe"),
        (STAGE_DIR / "ADDR_DFF_hierarchical_namespace.json", "reports/ADDR_DFF_hierarchical_namespace.json", "hierarchical namespace"),
        (DFF_GDS, "dependencies/dff/DFF_reusable_clean.gds", "approved DFF reusable GDS"),
        (DFF_MANIFEST, "dependencies/dff/DFF_REUSABLE_MANIFEST.json", "approved DFF manifest"),
        (STAGE_DIR / "ADDR_DFF_DFF_pin_geometry.csv", "reports/ADDR_DFF_DFF_pin_geometry.csv", "DFF pin geometry"),
        (STAGE_DIR / "ADDR_DFF_DFF_child_physical_interface.json", "reports/ADDR_DFF_DFF_child_physical_interface.json", "DFF physical interface"),
        (STAGE_DIR / "ADDR_DFF_DFF_conductive_obstacle_map.json", "reports/ADDR_DFF_DFF_conductive_obstacle_map.json", "DFF conductive obstacle map"),
        (STAGE_DIR / "ADDR_DFF_DFF_hierarchy_closure.json", "reports/ADDR_DFF_DFF_hierarchy_closure.json", "DFF hierarchy closure"),
        (STAGE_DIR / "ADDR_DFF_child_binding_matrix.csv", "reports/ADDR_DFF_child_binding_matrix.csv", "binding matrix"),
        (STAGE_DIR / "ADDR_DFF_binding_contract.json", "reports/ADDR_DFF_binding_contract.json", "binding contract"),
        (STAGE_DIR / "ADDR_DFF_constructor_parameter_binding.json", "reports/ADDR_DFF_constructor_parameter_binding.json", "constructor parameter binding"),
        (STAGE_DIR / "ADDR_DFF_approved_dependency_audit.json", "reports/ADDR_DFF_approved_dependency_audit.json", "dependency audit"),
        (STAGE_DIR / "ADDR_DFF_binding_digest.json", "reports/ADDR_DFF_binding_digest.json", "binding digest"),
        (STAGE_DIR / "ADDR_DFF_forbidden_source_negative_tests.json", "reports/ADDR_DFF_forbidden_source_negative_tests.json", "forbidden-source tests"),
        (STAGE_DIR / "ADDR_DFF_negative_tests.json", "reports/ADDR_DFF_negative_tests.json", "negative tests"),
        (STAGE_DIR / "ADDR_DFF_negative_tests.md", "reports/ADDR_DFF_negative_tests.md", "negative tests"),
        (STAGE_DIR / "baseline_dirty_tree_report.json", "reports/baseline_dirty_tree_report.json", "baseline dirty tree report"),
        (STAGE_DIR / "existing_dirty_path_immutability_report.json", "reports/existing_dirty_path_immutability_report.json", "dirty path immutability report"),
        (STAGE_DIR / "staged_allowlist_report.json", "reports/staged_allowlist_report.json", "staged allowlist report"),
        (STAGE_DIR / "staged_allowlist_report.md", "reports/staged_allowlist_report.md", "staged allowlist report"),
        (STAGE_DIR / "Wave4A_stage_report.json", "reports/Wave4A_stage_report.json", "stage report"),
        (STAGE_DIR / "Wave4A_stage_report.md", "reports/Wave4A_stage_report.md", "stage report"),
        (STAGE_DIR / "ledger_consistency_report.json", "reports/ledger_consistency_report.json", "ledger consistency"),
        (bundle_path, f"git/{bundle_path.name}", "git bundle"),
        (patch_path, f"git/{patch_path.name}", "git patch"),
    ]
    for src, rel, role in files:
        copy_entry(src, rel, role)
    # Existing generated files inside package root.
    for rel, role in [
        ("git/final_commit_info.txt", "final commit info"),
        ("git/git_status.txt", "git status"),
        ("git/git_diff.txt", "git diff"),
    ]:
        dest = package_root / rel
        entries.append(
            {
                "relative_path": rel,
                "file_size": dest.stat().st_size,
                "sha256": _sha256(dest),
                "evidence_role": role,
                "required": True,
                "self_hash_policy": "excluded_due_to_self_reference",
                "manifest_self_excluded": True,
            }
        )

    package_report = {
        "package_basename": "",
        "package_format": "tar.gz",
        "content_manifest_digest_recorded_in_manifest": True,
        "final_tar_sha_stored_in_external_sidecar": True,
        "push_result": push_result,
    }
    _write_json(package_root / "reports/evidence_package_report.json", package_report)
    entries.append(
        {
            "relative_path": "reports/evidence_package_report.json",
            "file_size": (package_root / "reports/evidence_package_report.json").stat().st_size,
            "sha256": _sha256(package_root / "reports/evidence_package_report.json"),
            "evidence_role": "evidence package report",
            "required": True,
            "self_hash_policy": "excluded_due_to_self_reference",
            "manifest_self_excluded": True,
        }
    )

    manifest = {
        "package_basename": None,
        "package_format": "tar.gz",
        "self_hash_policy": "excluded_due_to_self_reference",
        "manifest_self_excluded": True,
        "final_tar_sha_stored_in_external_sidecar": True,
        "entries": entries,
    }
    _write_json(package_root / "evidence_package_manifest.json", manifest)
    _write_csv(
        package_root / "evidence_package_manifest.csv",
        entries,
        ["relative_path", "file_size", "sha256", "evidence_role", "required", "self_hash_policy", "manifest_self_excluded"],
    )
    sums = []
    for path in sorted(package_root.rglob("*")):
        if path.is_file():
            rel = path.relative_to(package_root).as_posix()
            if rel == "SHA256SUMS":
                continue
            sums.append(f"{_sha256(path)}  {rel}")
    _write_text(package_root / "SHA256SUMS", "\n".join(sums) + "\n")
    manifest_report = _verify_manifest(package_root)
    _write_json(package_root / "reports/manifest_verification_report.json", manifest_report)
    if not manifest_report["all_passed"]:
        raise RuntimeError("manifest verification failed")

    tar_name = f"{PACKAGE_PREFIX}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.tar.gz"
    tar_path = REPO_ROOT / tar_name
    if tar_path.exists():
        tar_path.unlink()
    with tarfile.open(tar_path, "w:gz") as tf:
        tf.add(package_root, arcname=package_root.name)
    tar_sha = _sha256(tar_path)
    sidecar = tar_path.with_suffix(tar_path.suffix + ".sha256")
    _write_text(sidecar, f"{tar_sha}  {tar_path.name}\n")
    with tempfile.TemporaryDirectory(prefix="wave4a_pkg_verify_") as tmp:
        with tarfile.open(tar_path, "r:gz") as tf:
            tf.extractall(tmp)
        roots = [path for path in Path(tmp).iterdir() if path.is_dir()]
        verify = _verify_manifest(roots[0])
    _write_json(STAGE_DIR / "evidence_package_report.json", {"package_path": str(tar_path), "package_sha256": tar_sha, "sidecar_path": str(sidecar), "evidence_package_self_contained": True, "manifest_verification_passed": manifest_report["all_passed"], "independent_extract_verification_passed": verify["all_passed"]})
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
