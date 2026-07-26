from __future__ import annotations

import ast
import csv
import hashlib
import json
import subprocess
from pathlib import Path
from typing import Any

from sram_layoutgen.openyield_adapter.delay_chain_contract import build_role_manifest, build_stage_topology
from sram_layoutgen.openyield_adapter.inverter_chain_source_lock import load_approved_asset_lock, resolve_approved_pinv_asset


EXPECTED_OPENYIELD_COMMIT = "1c34428d8b913963c4971d093b1a7c2df97a2509"
TIME_GENERATE_PATH = "sram_compiler/subcircuits/time_generate.py"
EXPECTED_TIME_GENERATE_BLOB = "16b38c5a5d3165f046557941d15d425bbcab20b5"

MODULE_SPECS: dict[str, dict[str, Any]] = {
    "wen_delay_chain": {
        "class_name": "WenDelayChain",
        "top_cell_name": "WEN_DELAY_CHAIN_FPDK45",
        "top_pin_order": ["VDD", "VSS", "in", "out"],
        "stage_count": 4,
        "loads_per_stage": 4,
        "child_variant": "PINV_NW90_PW270_L50",
        "output_polarity": "NONINVERTING",
    },
    "delay_chain": {
        "class_name": "DelayChain",
        "top_cell_name": "DELAY_CHAIN_FPDK45",
        "top_pin_order": ["VDD", "VSS", "in", "out"],
        "stage_count": 9,
        "loads_per_stage": 4,
        "child_variant": "PINV_NW90_PW270_L50",
        "output_polarity": "INVERTING",
    },
}


def _run_git(openyield_root: Path, *args: str) -> str:
    completed = subprocess.run(["git", "-C", str(openyield_root), *args], text=True, capture_output=True, check=True)
    return completed.stdout


def _git_show_bytes(openyield_root: Path, commit: str, relpath: str) -> bytes:
    completed = subprocess.run(["git", "-C", str(openyield_root), "show", f"{commit}:{relpath}"], capture_output=True, check=True)
    return completed.stdout


def _git_blob_sha(openyield_root: Path, commit: str, relpath: str) -> str:
    line = _run_git(openyield_root, "ls-tree", commit, relpath).strip()
    parts = line.split()
    if len(parts) < 3:
        raise RuntimeError(f"unable to read blob sha for {relpath}")
    return parts[2]


def _find_class(module: ast.Module, name: str) -> ast.ClassDef:
    for node in module.body:
        if isinstance(node, ast.ClassDef) and node.name == name:
            return node
    raise RuntimeError(f"class {name} not found")


def _find_method(class_node: ast.ClassDef, name: str) -> ast.FunctionDef:
    for node in class_node.body:
        if isinstance(node, ast.FunctionDef) and node.name == name:
            return node
    raise RuntimeError(f"method {class_node.name}.{name} not found")


def _const_eval(node: ast.AST) -> Any:
    if isinstance(node, ast.Constant):
        return node.value
    if isinstance(node, ast.JoinedStr):
        parts = []
        for value in node.values:
            if isinstance(value, ast.Constant):
                parts.append(str(value.value))
            else:
                raise ValueError(f"unsupported f-string part: {ast.dump(value)}")
        return "".join(parts)
    if isinstance(node, ast.UnaryOp) and isinstance(node.op, ast.USub):
        value = _const_eval(node.operand)
        if isinstance(value, (int, float)):
            return -value
    raise ValueError(f"unsupported expression: {ast.dump(node)}")


def _expr_text(source_text: str, node: ast.AST | None) -> str:
    if node is None:
        return ""
    return ast.get_source_segment(source_text, node) or ""


def _extract_ctor_defaults(source_text: str, class_node: ast.ClassDef) -> dict[str, Any]:
    ctor = _find_method(class_node, "__init__")
    args = ctor.args.args
    defaults = ctor.args.defaults
    offset = len(args) - len(defaults)
    result: dict[str, Any] = {}
    for index, arg in enumerate(args):
        if index == 0:
            continue
        default_node = defaults[index - offset] if index >= offset else None
        value = None
        if default_node is not None:
            try:
                value = _const_eval(default_node)
            except Exception:
                value = None
        result[arg.arg] = {
            "default_expr": _expr_text(source_text, default_node),
            "default_value": value,
        }
    return result


def _extract_instance_rows(source_text: str, class_node: ast.ClassDef) -> list[dict[str, Any]]:
    method = _find_method(class_node, "add_delay_chain")
    rows: list[dict[str, Any]] = []
    for stmt in ast.walk(method):
        if not isinstance(stmt, ast.Call):
            continue
        if not isinstance(stmt.func, ast.Attribute) or stmt.func.attr != "X" or len(stmt.args) < 3:
            continue
        try:
            instance_name = _const_eval(stmt.args[0])
        except Exception:
            instance_name = _expr_text(source_text, stmt.args[0])
        nets = []
        for arg in stmt.args[2:]:
            try:
                nets.append(_const_eval(arg))
            except Exception:
                nets.append(_expr_text(source_text, arg))
        rows.append(
            {
                "display_instance_name": instance_name,
                "resolved_child_name_expr": _expr_text(source_text, stmt.args[1]),
                "nets": nets,
                "line_start": getattr(stmt, "lineno", None),
                "line_end": getattr(stmt, "end_lineno", None),
            }
        )
    rows.sort(key=lambda row: (row["line_start"] or 0, row["display_instance_name"]))
    return rows


def _logical_children_for_module(module_name: str) -> list[dict[str, Any]]:
    spec = MODULE_SPECS[module_name]
    roles = build_role_manifest(stage_count=spec["stage_count"], loads_per_stage=spec["loads_per_stage"])
    rows = []
    for role in roles:
        rows.append(
            {
                "logical_child": role.instance_role,
                "stage_index": role.stage_index,
                "role_type": role.role_type,
                "load_index": role.load_index,
                "source_instance_path": f"{module_name}.{role.instance_role}",
                "resolved_physical_cell": spec["child_variant"],
            }
        )
    return rows


def build_delay_chain_source_lock(openyield_root: Path, repo_root: Path, module_name: str) -> dict[str, Any]:
    spec = MODULE_SPECS[module_name]
    source_bytes = _git_show_bytes(openyield_root.resolve(), EXPECTED_OPENYIELD_COMMIT, TIME_GENERATE_PATH)
    source_text = source_bytes.decode("utf-8")
    source_blob = _git_blob_sha(openyield_root.resolve(), EXPECTED_OPENYIELD_COMMIT, TIME_GENERATE_PATH)
    if source_blob != EXPECTED_TIME_GENERATE_BLOB:
        raise RuntimeError(f"unexpected time_generate.py blob {source_blob}")
    module = ast.parse(source_text, filename=TIME_GENERATE_PATH)
    cls = _find_class(module, spec["class_name"])
    ctor_defaults = _extract_ctor_defaults(source_text, cls)
    instance_rows = _extract_instance_rows(source_text, cls)
    approved_asset = resolve_approved_pinv_asset(repo_root, spec["child_variant"])
    stage_topology = build_stage_topology(
        module_name=module_name,
        stage_count=spec["stage_count"],
        loads_per_stage=spec["loads_per_stage"],
        output_polarity=spec["output_polarity"],
    )
    return {
        "authority_repository": str(openyield_root.resolve()),
        "authority_commit": EXPECTED_OPENYIELD_COMMIT,
        "source_relative_path": TIME_GENERATE_PATH,
        "git_blob_sha": source_blob,
        "source_snapshot_sha256": hashlib.sha256(source_bytes).hexdigest(),
        "class_name": spec["class_name"],
        "source_line_range": {"start": cls.lineno, "end": cls.end_lineno},
        "formal_constructor_parameters": ctor_defaults,
        "top_pin_names": spec["top_pin_order"],
        "top_pin_order": spec["top_pin_order"],
        "driver_stage_count": spec["stage_count"],
        "loads_per_stage": spec["loads_per_stage"],
        "child_variant": spec["child_variant"],
        "output_polarity": spec["output_polarity"],
        "child_contract": _logical_children_for_module(module_name),
        "approved_asset": approved_asset,
        "instance_rows": instance_rows,
        "stage_topology": stage_topology,
        "topology_digest": hashlib.sha256(
            json.dumps(
                {
                    "pins": spec["top_pin_order"],
                    "child_variant": spec["child_variant"],
                    "stage_topology": stage_topology,
                    "instance_rows": instance_rows,
                },
                sort_keys=True,
            ).encode("utf-8")
        ).hexdigest()[:16],
    }


def write_asset_lock_csv(repo_root: Path) -> None:
    asset_lock = load_approved_asset_lock(repo_root)
    csv_path = repo_root / "collaboration/APPROVED_REUSABLE_ASSET_LOCK.csv"
    fieldnames = list(asset_lock["assets"][0].keys())
    csv_path.parent.mkdir(parents=True, exist_ok=True)
    with csv_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(asset_lock["assets"])
