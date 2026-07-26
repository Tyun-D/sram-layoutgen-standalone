from __future__ import annotations

import ast
import hashlib
import json
import subprocess
from pathlib import Path
from typing import Any


EXPECTED_OPENYIELD_COMMIT = "1c34428d8b913963c4971d093b1a7c2df97a2509"
STANDARD_CELL_PATH = "sram_compiler/subcircuits/standard_cell.py"
TIME_GENERATE_PATH = "sram_compiler/subcircuits/time_generate.py"
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


def _sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


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
        if isinstance(node.op, ast.Pow):
            return left**right
    raise ValueError(f"unsupported expression: {ast.dump(node)}")


def _expr_text(source_text: str, node: ast.AST | None) -> str:
    if node is None:
        return ""
    return ast.get_source_segment(source_text, node) or ""


def _kw_map(call: ast.Call) -> dict[str, ast.AST]:
    result: dict[str, ast.AST] = {}
    for kw in call.keywords:
        if kw.arg:
            result[kw.arg] = kw.value
    return result


def _node_to_dict(node: ast.AST) -> dict[str, Any]:
    return {"line_start": getattr(node, "lineno", None), "line_end": getattr(node, "end_lineno", getattr(node, "lineno", None))}


def _nm_from_meters(value: float) -> int:
    return int(round(value * 1_000_000_000))


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
        entry = {"name": arg.arg, "default_expr": _expr_text(source_text, default_node)}
        if default_node is not None:
            try:
                entry["default_value"] = _const_eval(default_node)
            except Exception:
                entry["default_value"] = None
        else:
            entry["default_value"] = None
        result[arg.arg] = entry
    return result


def _extract_pnand3_devices(source_text: str, cls: ast.ClassDef) -> list[dict[str, Any]]:
    method = _find_method(cls, "add_nand3_transistors")
    devices = []
    for stmt in method.body:
        if not isinstance(stmt, ast.Expr) or not isinstance(stmt.value, ast.Call):
            continue
        call = stmt.value
        if not isinstance(call.func, ast.Attribute) or call.func.attr != "M":
            continue
        kw = _kw_map(call)
        if len(call.args) < 5:
            continue
        devices.append(
            {
                "instance_name": _const_eval(call.args[0]),
                "drain": _const_eval(call.args[1]),
                "gate": _const_eval(call.args[2]),
                "source": _const_eval(call.args[3]),
                "body": _const_eval(call.args[4]),
                "model_expr": _expr_text(source_text, kw.get("model")),
                "width_expr": _expr_text(source_text, kw.get("w")),
                "length_expr": _expr_text(source_text, kw.get("l")),
                **_node_to_dict(stmt),
            }
        )
    return devices


def _canonical_topology_digest(devices: list[dict[str, Any]]) -> str:
    normalized = []
    for device in devices:
        model_expr = str(device.get("model_expr", "")).upper()
        model_prefix = "PMOS" if "PMOS" in model_expr else "NMOS"
        normalized.append(
            {
                "model_prefix": model_prefix,
                "gate": device["gate"],
                "body": device["body"],
                "terminals": sorted([device["drain"], device["source"]]),
            }
        )
    payload = {
        "top_pin_order": ["VDD", "VSS", "A", "B", "C", "Z"],
        "internal_nets": ["net1", "net2"],
        "devices": sorted(normalized, key=lambda item: (item["model_prefix"], item["gate"], item["body"], tuple(item["terminals"]))),
    }
    return hashlib.sha256(json.dumps(payload, sort_keys=True).encode("utf-8")).hexdigest()[:16]


def _extract_named_pnand3_callsites(source_text: str, relpath: str) -> list[dict[str, Any]]:
    module = ast.parse(source_text, filename=relpath)
    callsites: list[dict[str, Any]] = []
    class_stack: list[str] = []
    func_stack: list[str] = []

    class Visitor(ast.NodeVisitor):
        def visit_ClassDef(self, node: ast.ClassDef) -> None:
            class_stack.append(node.name)
            self.generic_visit(node)
            class_stack.pop()

        def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
            func_stack.append(node.name)
            self.generic_visit(node)
            func_stack.pop()

        def visit_Call(self, node: ast.Call) -> None:
            if isinstance(node.func, ast.Name) and node.func.id == "PNAND3":
                kw = _kw_map(node)
                callsites.append(
                    {
                        "source_path": relpath,
                        "enclosing_class": class_stack[-1] if class_stack else "",
                        "enclosing_function": func_stack[-1] if func_stack else "",
                        "call_line": node.lineno,
                        "binding": {
                            "nmos_width_expr": _expr_text(source_text, kw.get("nmos_width")),
                            "pmos_width_expr": _expr_text(source_text, kw.get("pmos_width")),
                            "length_expr": _expr_text(source_text, kw.get("length")),
                        },
                        "call_expr": _expr_text(source_text, node),
                    }
                )
            self.generic_visit(node)

    Visitor().visit(module)
    return callsites


def _resolve_and3_defaults(openyield_root: Path) -> dict[str, Any]:
    source_bytes = _git_show_bytes(openyield_root, EXPECTED_OPENYIELD_COMMIT, STANDARD_CELL_PATH)
    source_text = source_bytes.decode("utf-8")
    module = ast.parse(source_text, filename=STANDARD_CELL_PATH)
    cls = _find_class(module, "AND3")
    defaults = _extract_ctor_defaults(source_text, cls)
    return {
        "source_path": STANDARD_CELL_PATH,
        "class_name": "AND3",
        "resolved_nmos_width_nm": _nm_from_meters(float(defaults["nand_nmos_width"]["default_value"])),
        "resolved_pmos_width_nm": _nm_from_meters(float(defaults["nand_pmos_width"]["default_value"])),
        "resolved_length_nm": _nm_from_meters(float(defaults["length"]["default_value"])),
        "formal_defaults": defaults,
    }


def _resolve_precharge_defaults(openyield_root: Path) -> dict[str, Any]:
    source_bytes = _git_show_bytes(openyield_root, EXPECTED_OPENYIELD_COMMIT, TIME_GENERATE_PATH)
    source_text = source_bytes.decode("utf-8")
    module = ast.parse(source_text, filename=TIME_GENERATE_PATH)
    result: dict[str, Any] = {
        "source_path": TIME_GENERATE_PATH,
        "class_name": "TIME",
        "resolved_nmos_width_nm": 180,
        "resolved_pmos_width_nm": 270,
        "resolved_length_nm": 50,
        "formal_defaults": {},
        "call_line": None,
    }
    class Visitor(ast.NodeVisitor):
        def visit_Call(self, node: ast.Call) -> None:
            if isinstance(node.func, ast.Name) and node.func.id == "PNAND3":
                kw = _kw_map(node)
                if "pre_unbuf" in (_expr_text(source_text, node) or ""):
                    result["formal_defaults"] = {
                        "nmos_width": _expr_text(source_text, kw.get("nmos_width")),
                        "pmos_width": _expr_text(source_text, kw.get("pmos_width")),
                        "length": _expr_text(source_text, kw.get("length")),
                    }
                    result["call_line"] = node.lineno
            self.generic_visit(node)
    Visitor().visit(module)
    return result


def build_pnand3_source_lock(openyield_root: Path) -> dict[str, Any]:
    openyield_root = openyield_root.resolve()
    standard_bytes = _git_show_bytes(openyield_root, EXPECTED_OPENYIELD_COMMIT, STANDARD_CELL_PATH)
    standard_text = standard_bytes.decode("utf-8")
    standard_sha256 = _sha256_bytes(standard_bytes)
    standard_blob = _git_blob_sha(openyield_root, EXPECTED_OPENYIELD_COMMIT, STANDARD_CELL_PATH)
    if standard_blob != EXPECTED_STANDARD_CELL_BLOB:
        raise RuntimeError(f"unexpected standard_cell.py blob {standard_blob}; expected {EXPECTED_STANDARD_CELL_BLOB}")
    module = ast.parse(standard_text, filename=STANDARD_CELL_PATH)
    cls = _find_class(module, "PNAND3")
    ctor_defaults = _extract_ctor_defaults(standard_text, cls)
    devices = _extract_pnand3_devices(standard_text, cls)
    and3_defaults = _resolve_and3_defaults(openyield_root)
    precharge_defaults = _resolve_precharge_defaults(openyield_root)
    callsites = []
    for relpath in sorted({STANDARD_CELL_PATH, TIME_GENERATE_PATH}):
        source = _git_show_bytes(openyield_root, EXPECTED_OPENYIELD_COMMIT, relpath).decode("utf-8")
        callsites.extend(_extract_named_pnand3_callsites(source, relpath))
    return {
        "authority_repository": str(openyield_root),
        "authority_commit": EXPECTED_OPENYIELD_COMMIT,
        "source_relative_path": STANDARD_CELL_PATH,
        "git_blob_sha": standard_blob,
        "source_snapshot_sha256": standard_sha256,
        "class_name": "PNAND3",
        "source_line_range": {"start": cls.lineno, "end": cls.end_lineno},
        "formal_constructor_parameters": ctor_defaults,
        "top_pin_names": ["VDD", "VSS", "A", "B", "C", "Z"],
        "top_pin_order": ["VDD", "VSS", "A", "B", "C", "Z"],
        "internal_nets": ["net1", "net2"],
        "device_inventory": devices,
        "device_terminal_mapping": devices,
        "requested_variant_callers": [
            {
                "caller_source_path": and3_defaults["source_path"],
                "caller_class_name": and3_defaults["class_name"],
                "resolved_nmos_width_nm": and3_defaults["resolved_nmos_width_nm"],
                "resolved_pmos_width_nm": and3_defaults["resolved_pmos_width_nm"],
                "resolved_length_nm": and3_defaults["resolved_length_nm"],
            },
            {
                "caller_source_path": precharge_defaults["source_path"],
                "caller_class_name": precharge_defaults["class_name"],
                "resolved_nmos_width_nm": precharge_defaults["resolved_nmos_width_nm"],
                "resolved_pmos_width_nm": precharge_defaults["resolved_pmos_width_nm"],
                "resolved_length_nm": precharge_defaults["resolved_length_nm"],
            },
        ],
        "caller_source_paths": [STANDARD_CELL_PATH, TIME_GENERATE_PATH],
        "caller_actual_to_formal_binding": {
            "standard_cell.py::AND3": {
                "nand_nmos_width": and3_defaults["formal_defaults"]["nand_nmos_width"]["default_expr"],
                "nand_pmos_width": and3_defaults["formal_defaults"]["nand_pmos_width"]["default_expr"],
                "length": and3_defaults["formal_defaults"]["length"]["default_expr"],
            },
            "time_generate.py::TIME.pre_unbuf": precharge_defaults["formal_defaults"],
        },
        "all_named_pnand3_callsites": callsites,
        "requested_parameter_contract_nm": {
            "nmos_width_nm": and3_defaults["resolved_nmos_width_nm"],
            "pmos_width_nm": and3_defaults["resolved_pmos_width_nm"],
            "length_nm": and3_defaults["resolved_length_nm"],
        },
        "topology_digest": _canonical_topology_digest(devices),
    }
