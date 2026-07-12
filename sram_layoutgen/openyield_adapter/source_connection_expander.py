from __future__ import annotations

import ast
from dataclasses import dataclass
from typing import Any

from .source_module_registry import SourceClassRecord, _evaluate_condition, _evaluate_numeric_expr, _evaluate_range_expr, _expand_list_expr, _format_template, _safe_unparse


@dataclass
class AliasInfo:
    alias_name: str
    scope: str
    constructor_function: str
    constructor_expression: str
    child_source_class: str
    child_canonical_module: str
    parameter_expression: dict[str, str]
    source_line: int


def _constructor_name(node: ast.Call) -> str:
    if isinstance(node.func, ast.Name):
        return node.func.id
    return _safe_unparse(node.func).split(".")[-1]


def _call_parameter_map(node: ast.Call) -> dict[str, str]:
    payload = {kw.arg or f"kw_{index}": _safe_unparse(kw.value) for index, kw in enumerate(node.keywords)}
    if node.args:
        payload["__args__"] = "|".join(_safe_unparse(arg) for arg in node.args)
    return payload


def _resolve_alias_value(node: ast.AST, aliases: dict[str, AliasInfo]) -> AliasInfo | None:
    if isinstance(node, ast.Attribute) and node.attr in {"NAME", "name"}:
        base = node.value
        if isinstance(base, ast.Name):
            return aliases.get(base.id)
        if isinstance(base, ast.Attribute) and isinstance(base.value, ast.Name) and base.value.id == "self":
            return aliases.get(f"self.{base.attr}")
    if isinstance(node, ast.Name):
        return aliases.get(node.id)
    return None


def _clone_env(env: dict[str, Any]) -> dict[str, Any]:
    cloned: dict[str, Any] = {}
    for key, value in env.items():
        if isinstance(value, list):
            cloned[key] = list(value)
        elif isinstance(value, dict):
            cloned[key] = dict(value)
        else:
            cloned[key] = value
    return cloned


def _default_env(record: SourceClassRecord) -> tuple[dict[str, Any], dict[str, Any]]:
    vars_env = dict(record.constructor_defaults)
    self_env: dict[str, Any] = {}
    init_func = record.init_function
    if init_func is None:
        return vars_env, self_env
    for stmt in init_func.body:
        if isinstance(stmt, ast.Assign) and len(stmt.targets) == 1:
            target = stmt.targets[0]
            if isinstance(target, ast.Attribute) and isinstance(target.value, ast.Name) and target.value.id == "self":
                self_env[target.attr] = _evaluate_numeric_expr(stmt.value, vars_env, self_env)
            elif isinstance(target, ast.Name):
                if isinstance(stmt.value, ast.List):
                    vars_env[target.id] = [_format_template(item, vars_env, self_env) for item in stmt.value.elts]
                else:
                    vars_env[target.id] = _evaluate_numeric_expr(stmt.value, vars_env, self_env)
    return vars_env, self_env


def _collect_aliases(record: SourceClassRecord, registry: dict[str, SourceClassRecord]) -> dict[str, AliasInfo]:
    aliases: dict[str, AliasInfo] = {}
    for method in record.methods.values():
        for stmt in ast.walk(method):
            if not isinstance(stmt, ast.Assign) or len(stmt.targets) != 1 or not isinstance(stmt.value, ast.Call):
                continue
            constructor_name = _constructor_name(stmt.value)
            child_record = registry.get(constructor_name) or registry.get(constructor_name.upper())
            if child_record is None:
                continue
            target = stmt.targets[0]
            alias_name = ""
            scope = "local"
            if isinstance(target, ast.Name):
                alias_name = target.id
            elif isinstance(target, ast.Attribute) and isinstance(target.value, ast.Name) and target.value.id == "self":
                alias_name = f"self.{target.attr}"
                scope = "self"
            if not alias_name:
                continue
            aliases[alias_name] = AliasInfo(
                alias_name=alias_name,
                scope=scope,
                constructor_function=constructor_name,
                constructor_expression=_safe_unparse(stmt.value),
                child_source_class=child_record.class_name,
                child_canonical_module=child_record.canonical_module_name,
                parameter_expression=_call_parameter_map(stmt.value),
                source_line=stmt.lineno,
            )
    return aliases


def expand_source_connections(record: SourceClassRecord, registry: dict[str, SourceClassRecord]) -> dict[str, Any]:
    aliases = _collect_aliases(record, registry)
    child_rows: list[dict[str, Any]] = []
    net_rows: list[dict[str, Any]] = []

    def contains_x_call(statements: list[ast.stmt]) -> bool:
        for stmt in statements:
            for node in ast.walk(stmt):
                if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute) and isinstance(node.func.value, ast.Name) and node.func.value.id == "self" and node.func.attr == "X":
                    return True
        return False

    def process_statements(
        statements: list[ast.stmt],
        method_name: str,
        vars_env: dict[str, Any],
        self_env: dict[str, Any],
        loop_contexts: list[str],
        branch_conditions: list[str],
        branch_active: bool,
    ) -> None:
        for stmt in statements:
            if isinstance(stmt, ast.Assign) and len(stmt.targets) == 1:
                target = stmt.targets[0]
                if isinstance(target, ast.Name):
                    if isinstance(stmt.value, ast.List):
                        vars_env[target.id] = [_format_template(item, vars_env, self_env) for item in stmt.value.elts]
                    else:
                        vars_env[target.id] = _evaluate_numeric_expr(stmt.value, vars_env, self_env)
                elif isinstance(target, ast.Attribute) and isinstance(target.value, ast.Name) and target.value.id == "self":
                    self_env[target.attr] = _evaluate_numeric_expr(stmt.value, vars_env, self_env)
                continue
            if isinstance(stmt, ast.Expr) and isinstance(stmt.value, ast.Call):
                call = stmt.value
                if isinstance(call.func, ast.Attribute) and isinstance(call.func.value, ast.Name):
                    if call.func.value.id == "self" and call.func.attr == "X":
                        args = list(call.args)
                        if len(args) < 2:
                            continue
                        alias_info = _resolve_alias_value(args[1], aliases)
                        child_canonical = alias_info.child_canonical_module if alias_info else _safe_unparse(args[1])
                        child_record = registry.get(child_canonical) or registry.get(child_canonical.upper())
                        pin_order = child_record.normalized_pin_order if child_record else []
                        parent_connections: list[str] = []
                        for arg in args[2:]:
                            if isinstance(arg, ast.Starred):
                                expanded = _expand_list_expr(arg.value, vars_env, self_env)
                                parent_connections.extend(str(item).strip("'\"") for item in expanded)
                            else:
                                parent_connections.append(str(_format_template(arg, vars_env, self_env)).strip("'\""))
                        topology_status = "SOURCE_EXACT_RESOLVED"
                        if not child_record:
                            topology_status = "UNRESOLVED_SYMBOLIC"
                        elif not pin_order:
                            topology_status = "UNRESOLVED_SYMBOLIC"
                        elif len(pin_order) != len(parent_connections):
                            topology_status = "UNRESOLVED_SYMBOLIC"
                        child_row = {
                            "module_name": record.canonical_module_name,
                            "source_file": record.source_file,
                            "source_line": stmt.lineno,
                            "source_loop_context": " | ".join(loop_contexts),
                            "instance_name_expression": _safe_unparse(args[0]),
                            "instance_name_template": _safe_unparse(args[0]),
                            "child_constructor_alias": alias_info.alias_name if alias_info else _safe_unparse(args[1]),
                            "child_source_class": alias_info.child_source_class if alias_info else "",
                            "child_logical_module": child_canonical,
                            "child_pin_order": pin_order,
                            "parent_net_connections": parent_connections,
                            "pin_count": len(pin_order),
                            "connection_count": len(parent_connections),
                            "pin_connection_count_match": len(pin_order) == len(parent_connections),
                            "parameter_expression": alias_info.parameter_expression if alias_info else {},
                            "topology_resolution_status": topology_status,
                            "branch_condition": " and ".join(branch_conditions),
                            "method_name": method_name,
                        }
                        child_rows.append(child_row)
                        if branch_active:
                            for index, pin_name in enumerate(pin_order):
                                net_rows.append(
                                    {
                                        "parent_module": record.canonical_module_name,
                                        "instance_name_expression": _safe_unparse(args[0]),
                                        "child_module": child_canonical,
                                        "child_pin_index": index,
                                        "child_pin_name": pin_name,
                                        "parent_net_expression": parent_connections[index] if index < len(parent_connections) else "",
                                        "normalized_parent_net": parent_connections[index] if index < len(parent_connections) else "",
                                        "source_line": stmt.lineno,
                                        "loop_variables": " | ".join(loop_contexts),
                                        "branch_condition": " and ".join(branch_conditions),
                                        "operation_condition": " and ".join(branch_conditions),
                                        "configuration_condition": " and ".join(branch_conditions),
                                    }
                                )
                        continue
                    if call.func.value.id in vars_env:
                        if call.func.attr == "extend" and call.args:
                            existing = list(vars_env.get(call.func.value.id, []))
                            existing.extend(_expand_list_expr(call.args[0], vars_env, self_env))
                            vars_env[call.func.value.id] = existing
                            continue
                        if call.func.attr == "append" and call.args:
                            existing = list(vars_env.get(call.func.value.id, []))
                            existing.append(_format_template(call.args[0], vars_env, self_env))
                            vars_env[call.func.value.id] = existing
                            continue
            if isinstance(stmt, ast.For):
                loop_vars = list(loop_contexts)
                target_name = _safe_unparse(stmt.target)
                iter_values = _evaluate_range_expr(stmt.iter, vars_env, self_env)
                loop_vars.append(f"{target_name} in {_safe_unparse(stmt.iter)}")
                if not contains_x_call(stmt.body) and iter_values:
                    for value in iter_values:
                        vars_env[target_name] = value
                        process_statements(stmt.body, method_name, vars_env, self_env, loop_vars, list(branch_conditions), branch_active)
                else:
                    scoped_env = vars_env
                    if iter_values:
                        scoped_env[target_name] = iter_values[0]
                    else:
                        scoped_env[target_name] = _safe_unparse(stmt.iter)
                    process_statements(stmt.body, method_name, scoped_env, self_env, loop_vars, list(branch_conditions), branch_active)
                continue
            if isinstance(stmt, ast.If):
                condition = _safe_unparse(stmt.test)
                condition_value = _evaluate_condition(stmt.test, vars_env, self_env)
                then_active = branch_active and bool(condition_value) if isinstance(condition_value, bool) else False
                else_active = branch_active and (not bool(condition_value)) if isinstance(condition_value, bool) else branch_active
                process_statements(stmt.body, method_name, _clone_env(vars_env), _clone_env(self_env), list(loop_contexts), [*branch_conditions, condition], then_active)
                if stmt.orelse:
                    process_statements(stmt.orelse, method_name, _clone_env(vars_env), _clone_env(self_env), list(loop_contexts), [*branch_conditions, f"not ({condition})"], else_active)
                continue

    base_vars, base_self = _default_env(record)
    for method_name, method in record.methods.items():
        process_statements(method.body, method_name, _clone_env(base_vars), _clone_env(base_self), [], [], True)
    return {
        "alias_rows": [
            {
                "source_class": record.class_name,
                "source_name_constant": record.source_name_constant,
                "canonical_module_name": record.canonical_module_name,
                "child_constructor_alias": alias.alias_name,
                "child_source_class": alias.child_source_class,
                "child_canonical_module": alias.child_canonical_module,
                "resolution_method": "constructor_assignment",
                "hardcoded_crosscheck_result": "MATCH" if alias.child_canonical_module == (registry.get(alias.child_source_class) or registry.get(alias.child_canonical_module)).canonical_module_name else "MISMATCH",
                "resolution_status": "RESOLVED",
                "failure_reason": "",
            }
            for alias in aliases.values()
        ],
        "child_rows": child_rows,
        "net_rows": net_rows,
    }
