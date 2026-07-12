from __future__ import annotations

import ast
from dataclasses import dataclass
from pathlib import Path
from typing import Any


CANONICAL_NAME_MAP = {
    "Pinv": "PINV",
    "TransmissionGate": "TRANSMISSION_GATE",
    "dff": "DFF",
    "DFF_BUF": "DFF_BUF",
    "ADDR_DFF": "ADDR_DFF",
    "DATA_DFF": "DATA_DFF",
    "DelayChain": "delay_chain",
    "WenDelayChain": "wen_delay_chain",
    "PNAND2": "PNAND2",
    "PNAND3": "PNAND3",
    "AND2": "AND2",
    "AND3": "AND3",
    "pdrive": "pdrive",
    "pdrive2_for_pre": "pdrive2_for_pre",
    "wl_pdrive": "wl_pdrive",
    "TIME": "TIME",
}


@dataclass(frozen=True)
class SourceClassRecord:
    source_file: str
    class_name: str
    source_name_constant: str
    canonical_module_name: str
    source_nodes: list[str]
    normalized_pin_order: list[str]
    resolution_method: str
    hardcoded_crosscheck_result: str
    resolution_status: str
    failure_reason: str
    source_line: int
    constructor_defaults: dict[str, Any]
    init_arg_names: list[str]
    init_function: ast.FunctionDef | None
    methods: dict[str, ast.FunctionDef]
    ast_class: ast.ClassDef


def _safe_unparse(node: ast.AST | None) -> str:
    if node is None:
        return ""
    try:
        return ast.unparse(node)
    except Exception:
        return ""


def _const_string(node: ast.AST | None) -> str | None:
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return node.value
    return None


def _boolish(node: ast.AST) -> Any:
    if isinstance(node, ast.Constant):
        return node.value
    return None


def _signature_defaults(func: ast.FunctionDef | None) -> dict[str, Any]:
    if func is None:
        return {}
    defaults: dict[str, Any] = {}
    positional = list(func.args.args)
    positional_defaults = list(func.args.defaults)
    if positional_defaults:
        default_offset = len(positional) - len(positional_defaults)
        for index, node in enumerate(positional_defaults):
            arg = positional[default_offset + index]
            defaults[arg.arg] = _literal_value(node)
    for kwarg, node in zip(func.args.kwonlyargs, func.args.kw_defaults):
        if node is not None:
            defaults[kwarg.arg] = _literal_value(node)
    return defaults


def _literal_value(node: ast.AST) -> Any:
    if isinstance(node, ast.Constant):
        return node.value
    if isinstance(node, ast.UnaryOp) and isinstance(node.op, ast.USub) and isinstance(node.operand, ast.Constant):
        return -node.operand.value
    try:
        return ast.literal_eval(node)
    except Exception:
        return _safe_unparse(node)


def _normalize_name(class_name: str, name_constant: str | None) -> str:
    if class_name in CANONICAL_NAME_MAP:
        return CANONICAL_NAME_MAP[class_name]
    if name_constant and name_constant in CANONICAL_NAME_MAP.values():
        return name_constant
    return class_name


def _expand_dynamic_nodes(record_name: str, init_func: ast.FunctionDef | None, defaults: dict[str, Any]) -> tuple[list[str], str]:
    if init_func is None:
        return [], "NO_INIT"
    nodes: list[str] = []
    vars_env: dict[str, Any] = dict(defaults)
    self_env: dict[str, Any] = {}
    for stmt in init_func.body:
        if isinstance(stmt, ast.Assign):
            if len(stmt.targets) != 1:
                continue
            target = stmt.targets[0]
            if isinstance(target, ast.Name):
                if target.id == "nodes" and isinstance(stmt.value, ast.List):
                    nodes = [_literal_value(item) for item in stmt.value.elts]
                else:
                    vars_env[target.id] = _evaluate_numeric_expr(stmt.value, vars_env, self_env)
            elif isinstance(target, ast.Attribute) and isinstance(target.value, ast.Name) and target.value.id == "self":
                self_env[target.attr] = _evaluate_numeric_expr(stmt.value, vars_env, self_env)
                if target.attr == "NODES" and isinstance(stmt.value, ast.Name) and stmt.value.id == "nodes":
                    return [str(item) for item in nodes], "INIT_DYNAMIC_LIST"
        elif isinstance(stmt, ast.Expr) and isinstance(stmt.value, ast.Call):
            call = stmt.value
            if isinstance(call.func, ast.Attribute) and isinstance(call.func.value, ast.Name) and call.func.value.id == "nodes":
                if call.func.attr == "extend" and call.args:
                    nodes.extend(_expand_list_expr(call.args[0], vars_env, self_env))
                elif call.func.attr == "append" and call.args:
                    nodes.append(str(_format_template(call.args[0], vars_env, self_env)))
    return [str(item) for item in nodes], "INIT_DYNAMIC_LIST" if nodes else "NO_DYNAMIC_NODES"


def _expand_list_expr(node: ast.AST, vars_env: dict[str, Any], self_env: dict[str, Any]) -> list[str]:
    if isinstance(node, ast.List):
        return [str(_format_template(item, vars_env, self_env)) for item in node.elts]
    if isinstance(node, ast.ListComp) and len(node.generators) == 1:
        generator = node.generators[0]
        if isinstance(generator.target, ast.Name):
            target_name = generator.target.id
            values = _evaluate_range_expr(generator.iter, vars_env, self_env)
            rendered = []
            for value in values:
                local_vars = dict(vars_env)
                local_vars[target_name] = value
                rendered.append(str(_format_template(node.elt, local_vars, self_env)))
            return rendered
    if isinstance(node, ast.Name):
        value = vars_env.get(node.id)
        if isinstance(value, list):
            return [str(item) for item in value]
    return [str(_format_template(node, vars_env, self_env))]


def _evaluate_range_expr(node: ast.AST, vars_env: dict[str, Any], self_env: dict[str, Any]) -> list[int]:
    if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == "range":
        args = [_evaluate_numeric_expr(arg, vars_env, self_env) for arg in node.args]
        if len(args) == 1 and isinstance(args[0], int):
            return list(range(args[0]))
        if len(args) == 2 and all(isinstance(value, int) for value in args):
            return list(range(args[0], args[1]))
    return []


def _format_template(node: ast.AST, vars_env: dict[str, Any], self_env: dict[str, Any]) -> str:
    if isinstance(node, ast.Constant):
        return str(node.value)
    if isinstance(node, ast.JoinedStr):
        parts: list[str] = []
        for value in node.values:
            if isinstance(value, ast.Constant):
                parts.append(str(value.value))
            elif isinstance(value, ast.FormattedValue):
                rendered = _evaluate_numeric_expr(value.value, vars_env, self_env)
                parts.append(str(rendered if rendered is not None else _safe_unparse(value.value)))
        return "".join(parts)
    if isinstance(node, ast.Name):
        value = vars_env.get(node.id)
        return str(value if value is not None else node.id)
    if isinstance(node, ast.Attribute) and isinstance(node.value, ast.Name) and node.value.id == "self":
        value = self_env.get(node.attr)
        return str(value if value is not None else f"self.{node.attr}")
    return _safe_unparse(node).strip("'\"")


def _evaluate_numeric_expr(node: ast.AST, vars_env: dict[str, Any], self_env: dict[str, Any]) -> Any:
    if isinstance(node, ast.Constant):
        return node.value
    if isinstance(node, ast.Name):
        return vars_env.get(node.id, node.id)
    if isinstance(node, ast.Attribute) and isinstance(node.value, ast.Name) and node.value.id == "self":
        return self_env.get(node.attr, f"self.{node.attr}")
    if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
        fn = node.func.id
        args = [_evaluate_numeric_expr(arg, vars_env, self_env) for arg in node.args]
        if fn == "int" and args:
            return int(args[0])
        if fn == "float" and args:
            return float(args[0])
        if fn == "max" and all(isinstance(arg, (int, float)) for arg in args):
            return max(args)
        if fn == "ceil" and args:
            import math

            return int(math.ceil(float(args[0])))
        if fn == "log2" and args:
            import math

            return math.log2(float(args[0]))
    if isinstance(node, ast.IfExp):
        condition = _evaluate_condition(node.test, vars_env, self_env)
        if condition is True:
            return _evaluate_numeric_expr(node.body, vars_env, self_env)
        if condition is False:
            return _evaluate_numeric_expr(node.orelse, vars_env, self_env)
    if isinstance(node, ast.BinOp):
        left = _evaluate_numeric_expr(node.left, vars_env, self_env)
        right = _evaluate_numeric_expr(node.right, vars_env, self_env)
        if isinstance(left, (int, float)) and isinstance(right, (int, float)):
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
    return _safe_unparse(node)


def _evaluate_condition(node: ast.AST, vars_env: dict[str, Any], self_env: dict[str, Any]) -> bool | None:
    if isinstance(node, ast.Constant) and isinstance(node.value, bool):
        return node.value
    if isinstance(node, ast.Name):
        value = vars_env.get(node.id)
        if isinstance(value, bool):
            return value
    if isinstance(node, ast.Attribute) and isinstance(node.value, ast.Name) and node.value.id == "self":
        value = self_env.get(node.attr)
        if isinstance(value, bool):
            return value
    if isinstance(node, ast.Compare) and len(node.ops) == 1 and len(node.comparators) == 1:
        left = _evaluate_numeric_expr(node.left, vars_env, self_env)
        right = _evaluate_numeric_expr(node.comparators[0], vars_env, self_env)
        if isinstance(node.ops[0], ast.Eq):
            return left == right
        if isinstance(node.ops[0], ast.NotEq):
            return left != right
        if isinstance(node.ops[0], ast.Gt):
            return left > right
        if isinstance(node.ops[0], ast.GtE):
            return left >= right
        if isinstance(node.ops[0], ast.Lt):
            return left < right
        if isinstance(node.ops[0], ast.LtE):
            return left <= right
    if isinstance(node, ast.BoolOp):
        values = [_evaluate_condition(value, vars_env, self_env) for value in node.values]
        if any(value is None for value in values):
            return None
        if isinstance(node.op, ast.And):
            return all(values)
        if isinstance(node.op, ast.Or):
            return any(values)
    return None


def build_source_registry(openyield_root: str | Path) -> dict[str, Any]:
    root = Path(openyield_root)
    source_files = [
        root / "sram_compiler/subcircuits/standard_cell.py",
        root / "sram_compiler/subcircuits/time_generate.py",
    ]
    records: dict[str, SourceClassRecord] = {}
    rows: list[dict[str, Any]] = []
    hardcoded_reference = {
        "PINV": ["VDD", "VSS", "A", "Z"],
        "TRANSMISSION_GATE": ["VDD", "VSS", "IN", "OUT", "CTR_P", "CTR_N"],
        "PNAND2": ["VDD", "VSS", "A", "B", "Z"],
        "PNAND3": ["VDD", "VSS", "A", "B", "C", "Z"],
        "AND2": ["VDD", "VSS", "A", "B", "Z"],
        "AND3": ["VDD", "VSS", "A", "B", "C", "Z"],
        "DFF": ["VDD", "VSS", "D", "Q", "CLK"],
        "DFF_BUF": ["VDD", "VSS", "D", "Q", "QB", "CLK"],
        "delay_chain": ["VDD", "VSS", "in", "out"],
        "wen_delay_chain": ["VDD", "VSS", "in", "out"],
        "pdrive": ["VDD", "VSS", "A", "Z"],
        "pdrive2_for_pre": ["VDD", "VSS", "A", "Z"],
        "wl_pdrive": ["VDD", "VSS", "A", "Z"],
    }
    for source_file in source_files:
        module = ast.parse(source_file.read_text(encoding="utf-8"))
        for node in module.body:
            if not isinstance(node, ast.ClassDef):
                continue
            init_func = next((item for item in node.body if isinstance(item, ast.FunctionDef) and item.name == "__init__"), None)
            methods = {item.name: item for item in node.body if isinstance(item, ast.FunctionDef)}
            name_constant = None
            nodes_constant: list[str] = []
            for stmt in node.body:
                if isinstance(stmt, ast.Assign):
                    for target in stmt.targets:
                        if isinstance(target, ast.Name) and target.id == "NAME":
                            name_constant = _const_string(stmt.value) or _safe_unparse(stmt.value)
                        if isinstance(target, ast.Name) and target.id == "NODES" and isinstance(stmt.value, (ast.Tuple, ast.List)):
                            nodes_constant = [str(_literal_value(item)) for item in stmt.value.elts]
            defaults = _signature_defaults(init_func)
            dynamic_nodes, method = _expand_dynamic_nodes(node.name, init_func, defaults)
            resolved_nodes = nodes_constant or dynamic_nodes
            canonical_name = _normalize_name(node.name, name_constant)
            if canonical_name not in CANONICAL_NAME_MAP.values() and node.name not in CANONICAL_NAME_MAP:
                continue
            crosscheck = "NO_REFERENCE"
            if canonical_name in hardcoded_reference:
                crosscheck = "MATCH" if resolved_nodes == hardcoded_reference[canonical_name] else "MISMATCH"
            record = SourceClassRecord(
                source_file=str(source_file),
                class_name=node.name,
                source_name_constant=name_constant or "",
                canonical_module_name=canonical_name,
                source_nodes=resolved_nodes,
                normalized_pin_order=resolved_nodes,
                resolution_method="CLASS_NODES" if nodes_constant else method,
                hardcoded_crosscheck_result=crosscheck,
                resolution_status="RESOLVED" if resolved_nodes else "UNRESOLVED",
                failure_reason="" if resolved_nodes else "NODES not recovered from source",
                source_line=node.lineno,
                constructor_defaults=defaults,
                init_arg_names=[arg.arg for arg in init_func.args.args[1:]] if init_func is not None else [],
                init_function=init_func,
                methods=methods,
                ast_class=node,
            )
            records[node.name] = record
            records[canonical_name] = record
            rows.append(
                {
                    "source_class": node.name,
                    "source_name_constant": record.source_name_constant,
                    "canonical_module_name": canonical_name,
                    "source_nodes": "|".join(record.source_nodes),
                    "normalized_pin_order": "|".join(record.normalized_pin_order),
                    "init_arg_names": "|".join(record.init_arg_names),
                    "resolution_method": record.resolution_method,
                    "hardcoded_crosscheck_result": record.hardcoded_crosscheck_result,
                    "resolution_status": record.resolution_status,
                    "failure_reason": record.failure_reason,
                }
            )
    return {"records": records, "rows": rows}
