from __future__ import annotations

import ast
import hashlib
import json
import subprocess
from pathlib import Path
from typing import Any


EXPECTED_OPENYIELD_COMMIT = "1c34428d8b913963c4971d093b1a7c2df97a2509"
STANDARD_CELL_PATH = "sram_compiler/subcircuits/standard_cell.py"
EXPECTED_STANDARD_CELL_BLOB = "e3269a942e18931d5a75eda7252a8abda6540bf5"


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
    if isinstance(node, ast.BinOp):
        left = _const_eval(node.left)
        right = _const_eval(node.right)
        if isinstance(node.op, ast.Add):
            return left + right
        if isinstance(node.op, ast.Sub):
            return left - right
        if isinstance(node.op, ast.Mult):
            return left * right
        if isinstance(node.op, ast.Div):
            return left / right
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


def build_and3_source_lock(openyield_root: Path) -> dict[str, Any]:
    openyield_root = openyield_root.resolve()
    source_bytes = _git_show_bytes(openyield_root, EXPECTED_OPENYIELD_COMMIT, STANDARD_CELL_PATH)
    source_text = source_bytes.decode("utf-8")
    source_blob = _git_blob_sha(openyield_root, EXPECTED_OPENYIELD_COMMIT, STANDARD_CELL_PATH)
    if source_blob != EXPECTED_STANDARD_CELL_BLOB:
        raise RuntimeError(f"unexpected standard_cell.py blob {source_blob}")
    module = ast.parse(source_text, filename=STANDARD_CELL_PATH)
    cls = _find_class(module, "AND3")
    ctor_defaults = _extract_ctor_defaults(source_text, cls)
    add_components = _find_method(cls, "add_and3_components")
    instance_rows: list[dict[str, Any]] = []
    for stmt in add_components.body:
        if not isinstance(stmt, ast.Expr) or not isinstance(stmt.value, ast.Call):
            continue
        call = stmt.value
        if not isinstance(call.func, ast.Attribute) or call.func.attr != "X" or len(call.args) < 3:
            continue
        instance_rows.append(
            {
                "display_instance_name": _const_eval(call.args[0]),
                "resolved_child_name_expr": _expr_text(source_text, call.args[1]),
                "nets": [(_const_eval(arg) if isinstance(arg, (ast.Constant, ast.JoinedStr, ast.UnaryOp, ast.BinOp)) else _expr_text(source_text, arg)) for arg in call.args[2:]],
                "line_start": stmt.lineno,
                "line_end": stmt.end_lineno,
            }
        )
    return {
        "authority_repository": str(openyield_root),
        "authority_commit": EXPECTED_OPENYIELD_COMMIT,
        "source_relative_path": STANDARD_CELL_PATH,
        "git_blob_sha": source_blob,
        "source_snapshot_sha256": hashlib.sha256(source_bytes).hexdigest(),
        "class_name": "AND3",
        "source_line_range": {"start": cls.lineno, "end": cls.end_lineno},
        "formal_constructor_parameters": ctor_defaults,
        "top_pin_names": ["VDD", "VSS", "A", "B", "C", "Z"],
        "top_pin_order": ["VDD", "VSS", "A", "B", "C", "Z"],
        "internal_nets": ["zb_int"],
        "child_contract": [
            {
                "logical_child": "nand3_gate",
                "logical_type": "PNAND3",
                "requested_nmos_width_nm": 180,
                "requested_pmos_width_nm": 270,
                "requested_length_nm": 50,
            },
            {
                "logical_child": "inv_driver",
                "logical_type": "PINV",
                "requested_nmos_width_nm": 90,
                "requested_pmos_width_nm": 270,
                "requested_length_nm": 50,
            },
        ],
        "instance_rows": instance_rows,
        "topology_digest": hashlib.sha256(
            json.dumps(
                {
                    "pins": ["VDD", "VSS", "A", "B", "C", "Z"],
                    "internal": ["zb_int"],
                    "instances": instance_rows,
                },
                sort_keys=True,
            ).encode("utf-8")
        ).hexdigest()[:16],
    }
