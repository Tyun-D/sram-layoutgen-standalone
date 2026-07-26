from __future__ import annotations

import ast
from itertools import product
from pathlib import Path
from typing import Any

from .source_connection_expander import build_module_environment
from .source_module_registry import SourceClassRecord, _evaluate_condition, _evaluate_numeric_expr, _evaluate_range_expr, _safe_unparse


REFERENCE_CONFIGS = {
    "16x16": {
        "num_rows": 16,
        "num_cols": 16,
        "num_words": 16,
        "word_size": 16,
        "words_per_row": 1,
        "mux_ratio": 1,
        "choose_columnmux": False,
        "operation": "read&write",
        "tech": "FreePDK45",
    },
    "64x8": {
        "num_rows": 64,
        "num_cols": 8,
        "num_words": 64,
        "word_size": 8,
        "words_per_row": 1,
        "mux_ratio": 1,
        "choose_columnmux": False,
        "operation": "read&write",
        "tech": "FreePDK45",
    },
}


def module_overrides_for_config(module_name: str, config: dict[str, Any]) -> dict[str, Any]:
    overrides: dict[str, Any] = {}
    if module_name in {"TIME", "ADDR_DFF"}:
        overrides["num_rows"] = config["num_rows"]
    if module_name in {"TIME", "DATA_DFF"}:
        overrides["num_cols"] = config["num_cols"]
    if module_name == "TIME":
        overrides["operation"] = config["operation"]
    return overrides


def build_module_context(record: SourceClassRecord, config: dict[str, Any] | None = None, parameter_overrides: dict[str, Any] | None = None) -> tuple[dict[str, Any], dict[str, Any]]:
    overrides = dict(parameter_overrides or {})
    if config:
        overrides.update(module_overrides_for_config(record.canonical_module_name, config))
    return build_module_environment(record, overrides=overrides)


def evaluate_condition_text(condition_text: str, vars_env: dict[str, Any], self_env: dict[str, Any]) -> tuple[bool | None, str]:
    text = (condition_text or "").strip()
    if not text:
        return True, "ALWAYS_ACTIVE"
    try:
        node = ast.parse(text, mode="eval").body
    except SyntaxError:
        return None, "UNRESOLVED_CONDITION"
    value = _evaluate_condition(node, vars_env, self_env)
    if value is True:
        return True, "ACTIVE_FOR_CONFIG"
    if value is False:
        return False, "INACTIVE_FOR_CONFIG"
    return None, "UNRESOLVED_CONDITION"


def parse_loop_context_items(loop_context_text: str) -> list[tuple[str, str]]:
    text = (loop_context_text or "").strip()
    if not text:
        return []
    items: list[tuple[str, str]] = []
    for raw_item in text.split("|"):
        item = raw_item.strip()
        if not item or " in " not in item:
            continue
        name, expr = item.split(" in ", 1)
        items.append((name.strip(), expr.strip()))
    return items


def evaluate_loop_context_items(loop_context_text: str, vars_env: dict[str, Any], self_env: dict[str, Any]) -> tuple[list[dict[str, Any]], int]:
    items = parse_loop_context_items(loop_context_text)
    if not items:
        return [{}], 0
    value_sets: list[list[Any]] = []
    unresolved = 0
    for loop_var, expr_text in items:
        try:
            expr_node = ast.parse(expr_text, mode="eval").body
        except SyntaxError:
            value_sets.append([expr_text])
            unresolved += 1
            continue
        values = _evaluate_range_expr(expr_node, vars_env, self_env)
        if not values:
            value_sets.append([expr_text])
            unresolved += 1
        else:
            value_sets.append(values)
    combinations: list[dict[str, Any]] = []
    for combo in product(*value_sets):
        combinations.append({items[index][0]: combo[index] for index in range(len(items))})
    return combinations, unresolved


def render_template_expression(expr_text: str, loop_values: dict[str, Any]) -> str:
    text = expr_text.strip()
    if not text:
        return text
    try:
        node = ast.parse(text, mode="eval").body
    except SyntaxError:
        return text.strip("'\"")
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return node.value
    if isinstance(node, ast.JoinedStr):
        rendered: list[str] = []
        for part in node.values:
            if isinstance(part, ast.Constant):
                rendered.append(str(part.value))
            elif isinstance(part, ast.FormattedValue):
                value = _evaluate_numeric_expr(part.value, loop_values, {})
                rendered.append(str(value))
        return "".join(rendered)
    if isinstance(node, ast.Name) and node.id in loop_values:
        return str(loop_values[node.id])
    return _safe_unparse(node).strip("'\"")


def normalize_connection_name(connection_expr: str, loop_values: dict[str, Any]) -> str:
    text = (connection_expr or "").strip()
    if not text:
        return text
    if text.startswith("f'") or text.startswith('f"'):
        return render_template_expression(text, loop_values)
    return text.strip("'\"")


def evaluate_parameter_expression(expr_text: str, vars_env: dict[str, Any], self_env: dict[str, Any], loop_values: dict[str, Any] | None = None) -> tuple[Any, bool]:
    text = (expr_text or "").strip()
    if not text:
        return "", True
    loop_env = dict(loop_values or {})
    try:
        node = ast.parse(text, mode="eval").body
    except SyntaxError:
        return text, False
    if isinstance(node, ast.Constant):
        return node.value, True
    if isinstance(node, ast.JoinedStr):
        return render_template_expression(text, loop_env), True
    value = _evaluate_numeric_expr(node, {**vars_env, **loop_env}, self_env)
    if isinstance(value, str):
        unknown_tokens = ("self.", "range(", "log2(", "ceil(", "{", "}")
        if value == text or any(token in value for token in unknown_tokens):
            if isinstance(node, ast.Name) and node.id in {**vars_env, **loop_env}:
                return ({**vars_env, **loop_env})[node.id], True
            return value, False
    return value, True
