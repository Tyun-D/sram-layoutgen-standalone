from __future__ import annotations

import json
import ast
from math import ceil, log2
from pathlib import Path
from typing import Any

from .config_branch_evaluator import build_module_context, evaluate_condition_text, evaluate_loop_context_items, evaluate_parameter_expression, normalize_connection_name, render_template_expression
from .source_module_registry import _expand_list_expr


def _address_width(num_rows: int) -> int:
    return ceil(log2(num_rows)) if num_rows > 1 else 1


def _read_resolution_rows(path: Path) -> list[dict[str, Any]]:
    return json.loads(path.read_text(encoding="utf-8"))["rows"]


def _resolution_index(rows: list[dict[str, Any]]) -> dict[tuple[str, str], dict[str, Any]]:
    return {(row["source_class"], row["source_instance_path"]): row for row in rows}


def expand_concrete_configuration(config: dict[str, Any]) -> dict[str, Any]:
    num_rows = int(config["num_rows"])
    num_cols = int(config["num_cols"])
    operation = str(config["operation"])
    address_width = _address_width(num_rows)
    data_bits = num_cols if operation in {"write", "read&write"} else 0
    return {
        "config": config,
        "address_width": address_width,
        "ADDR_DFF_bit_count": address_width,
        "DATA_DFF_bit_count": data_bits,
        "DFF_total_count": address_width + data_bits + 2,
        "DFF_BUF_count": 2,
        "AND2_count": 2,
        "AND3_count": 2,
        "PNAND2_count": 2,
        "PNAND3_count": 3,
        "source_template_instance_count": 12,
        "concrete_expanded_instance_count": 12,
    }


def build_concrete_binding_report(
    *,
    config: dict[str, Any],
    resolution_json: Path,
    contract: dict[str, Any],
) -> dict[str, Any]:
    expansion = expand_concrete_configuration(config)
    rows = _read_resolution_rows(resolution_json)
    index = _resolution_index(rows)
    approved_root = contract["approved_reusable_cell_root"]
    config_id = f"R{config['num_rows']}_C{config['num_cols']}_{config['operation']}"
    leaf_rows: list[dict[str, Any]] = []
    failure_rows: list[dict[str, Any]] = []
    for key, row in sorted(index.items()):
        physical = row["canonical_physical_cell_name"]
        binding_status = "APPROVED_PRIMITIVE_BINDING" if physical in contract["approved_geometry_fingerprints"] else "NEW_PRIMITIVE_REQUIRED"
        leaf_rows.append(
            {
                "config_id": config_id,
                "concrete_instance_name": row["source_instance_path"],
                "parent_module": row["source_class"],
                "child_module": physical if physical.startswith("TRANSMISSION_GATE") else "PINV",
                "concrete_parameter_values": json.dumps(
                    {
                        "resolved_nmos_width_nm": row["resolved_nmos_width_nm"],
                        "resolved_pmos_width_nm": row["resolved_pmos_width_nm"],
                        "resolved_channel_length_nm": row["resolved_channel_length_nm"],
                    },
                    sort_keys=True,
                ),
                "parent_net_connections": "",
                "resolved_physical_cell_name": physical,
                "binding_status": binding_status,
                "source_trace": row["resolution_source_trace"],
            }
        )
        if binding_status != "APPROVED_PRIMITIVE_BINDING":
            failure_rows.append(
                {
                    "config_id": config_id,
                    "failure_class": "NEW_PRIMITIVE_REQUIRED",
                    "instance_name": row["source_instance_path"],
                    "parent_module": row["source_class"],
                    "reason": f"{physical} not found in approved reusable contract",
                }
            )
    for composite_name, count in {
        "DFF": expansion["DFF_total_count"],
        "DFF_BUF": expansion["DFF_BUF_count"],
        "AND2": expansion["AND2_count"],
        "AND3": expansion["AND3_count"],
        "PNAND2": expansion["PNAND2_count"],
        "PNAND3": expansion["PNAND3_count"],
    }.items():
        if composite_name in {"PNAND2", "PNAND3"}:
            failure_rows.append(
                {
                    "config_id": config_id,
                    "failure_class": "NEW_PRIMITIVE_REQUIRED",
                    "instance_name": composite_name,
                    "parent_module": "TIME",
                    "reason": "OpenYield PNAND physical primitive is not yet approved",
                }
            )
        else:
            failure_rows.append(
                {
                    "config_id": config_id,
                    "failure_class": "COMPOSITE_CHILD_NOT_YET_GENERATED",
                    "instance_name": composite_name,
                    "parent_module": "TIME",
                    "reason": f"{count} composite child instances remain hierarchical in M12C4R",
                }
            )
    expansion["concrete_leaf_primitive_instance_count"] = len(leaf_rows)
    expansion["concrete_composite_instance_count"] = 12
    expansion["leaf_rows"] = leaf_rows
    expansion["failure_rows"] = failure_rows
    expansion["approved_reusable_root"] = approved_root
    return expansion


def concrete_instance_matrix(expansions: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for expansion in expansions:
        cfg = expansion["config"]
        tag = f"R{cfg['num_rows']}_C{cfg['num_cols']}_{cfg['operation']}"
        for key in ["DFF_total_count", "DFF_BUF_count", "AND2_count", "AND3_count", "PNAND2_count", "PNAND3_count"]:
            rows.append({"config_id": tag, "module_name": key.replace("_count", ""), "instance_count": expansion[key]})
    return rows


def resolution_index_by_instance(path: Path) -> dict[tuple[str, str], dict[str, Any]]:
    rows = _read_resolution_rows(path)
    return {(row["source_class"], row["source_instance_path"]): row for row in rows}


def _group_child_rows(child_rows: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    grouped: dict[str, list[dict[str, Any]]] = {}
    for row in child_rows:
        grouped.setdefault(row["module_name"], []).append(row)
    return grouped


def _child_alias_key(parent_record_class: str, child_alias: str) -> str:
    return f"{parent_record_class}.{child_alias.split('.')[-1]}"


def _module_top_pin_map(record) -> list[str]:
    return list(record.normalized_pin_order)


def _parameter_overrides(row: dict[str, Any], vars_env: dict[str, Any], self_env: dict[str, Any], loop_values: dict[str, Any]) -> tuple[dict[str, Any], int]:
    payload = row.get("parameter_expression") or {}
    unresolved = 0
    if isinstance(payload, str):
        try:
            payload = json.loads(payload)
        except Exception:
            try:
                import ast

                payload = ast.literal_eval(payload)
            except Exception:
                payload = {}
    overrides: dict[str, Any] = {}
    for key, value in payload.items():
        if key == "__args__":
            continue
        evaluated, resolved = evaluate_parameter_expression(str(value), vars_env, self_env, loop_values)
        overrides[key] = evaluated
        if not resolved:
            unresolved += 1
    return overrides, unresolved


def _resolve_parent_connections(row: dict[str, Any], vars_env: dict[str, Any], self_env: dict[str, Any], loop_values: dict[str, Any]) -> list[str]:
    expressions = row.get("parent_net_connection_expressions") or []
    if isinstance(expressions, str):
        try:
            expressions = ast.literal_eval(expressions)
        except Exception:
            expressions = []
    if not expressions:
        return [normalize_connection_name(connection, loop_values) for connection in row["parent_net_connections"]]
    resolved: list[str] = []
    for expr in expressions:
        if isinstance(expr, str) and expr.startswith("*"):
            try:
                node = ast.parse(expr[1:], mode="eval").body
                expanded = _expand_list_expr(node, {**vars_env, **loop_values}, self_env)
                resolved.extend(str(item).strip("'\"") for item in expanded)
            except SyntaxError:
                resolved.append(expr)
        else:
            resolved.append(normalize_connection_name(str(expr), loop_values))
    return resolved


def resolve_parent_connections_for_row(row: dict[str, Any], vars_env: dict[str, Any], self_env: dict[str, Any], loop_values: dict[str, Any] | None = None) -> list[str]:
    return _resolve_parent_connections(row, vars_env, self_env, loop_values or {})


def build_active_template_rows(
    *,
    child_rows: list[dict[str, Any]],
    registry: dict[str, Any],
    config: dict[str, Any] | None,
    root_module: str = "TIME",
) -> dict[str, Any]:
    grouped = _group_child_rows(child_rows)
    active_rows: list[dict[str, Any]] = []
    visited: set[str] = set()
    unresolved_branch_conditions = 0
    unresolved_loop_bounds = 0

    def visit(module_name: str, parameter_overrides: dict[str, Any] | None = None) -> None:
        nonlocal unresolved_branch_conditions, unresolved_loop_bounds
        if module_name in visited:
            return
        visited.add(module_name)
        record = registry[module_name]
        vars_env, self_env = build_module_context(record, config, parameter_overrides)
        for row in grouped.get(module_name, []):
            cond_value, cond_status = evaluate_condition_text(row.get("branch_condition", ""), vars_env, self_env)
            row_copy = dict(row)
            row_copy["active_for_config"] = cond_value is True
            row_copy["condition_evaluation_status"] = cond_status
            row_copy["config_connection_count"] = int(row["connection_count"])
            active_rows.append(row_copy)
            if cond_status == "UNRESOLVED_CONDITION":
                unresolved_branch_conditions += 1
            _, loop_unresolved = evaluate_loop_context_items(row.get("source_loop_context", ""), vars_env, self_env)
            unresolved_loop_bounds += loop_unresolved
            if cond_value is True and row["child_logical_module"] in grouped:
                overrides, _ = _parameter_overrides(row, vars_env, self_env, {})
                visit(row["child_logical_module"], overrides)

    visit(root_module)
    return {
        "active_rows": active_rows,
        "active_child_rows": [row for row in active_rows if row["active_for_config"]],
        "active_net_connection_count": sum(int(row["config_connection_count"]) for row in active_rows if row["active_for_config"]),
        "unresolved_branch_condition_count": unresolved_branch_conditions,
        "unresolved_loop_bound_count": unresolved_loop_bounds,
    }


def build_source_derived_concrete_expansion(
    *,
    config: dict[str, Any],
    child_rows: list[dict[str, Any]],
    registry: dict[str, Any],
    contract: dict[str, Any],
    resolution_json: Path,
    root_module: str = "TIME",
) -> dict[str, Any]:
    grouped = _group_child_rows(child_rows)
    resolution_index = resolution_index_by_instance(resolution_json)
    instances: list[dict[str, Any]] = []
    failures: list[dict[str, Any]] = []
    unresolved_count = 0

    def expand(module_name: str, instance_path: str, net_binding: dict[str, str], parameter_overrides: dict[str, Any] | None = None) -> None:
        nonlocal unresolved_count
        record = registry[module_name]
        vars_env, self_env = build_module_context(record, config, parameter_overrides)
        top_pins = _module_top_pin_map(record)
        for row in grouped.get(module_name, []):
            cond_value, cond_status = evaluate_condition_text(row.get("branch_condition", ""), vars_env, self_env)
            loop_combos, loop_unresolved = evaluate_loop_context_items(row.get("source_loop_context", ""), vars_env, self_env)
            if cond_status == "UNRESOLVED_CONDITION" or loop_unresolved > 0:
                unresolved_count += 1
            for loop_values in loop_combos:
                concrete_instance_name = render_template_expression(row["instance_name_template"], loop_values)
                hierarchical_path = f"{instance_path}.{concrete_instance_name}" if instance_path else concrete_instance_name
                raw_connections = _resolve_parent_connections(row, vars_env, self_env, loop_values)
                normalized_connections: list[str] = []
                for index, raw_connection in enumerate(raw_connections):
                    pin_name = top_pins[index] if index < len(top_pins) else ""
                    if raw_connection in net_binding:
                        normalized_connections.append(net_binding[raw_connection])
                    elif raw_connection in top_pins and raw_connection in net_binding:
                        normalized_connections.append(net_binding[raw_connection])
                    else:
                        normalized_connections.append(f"{instance_path}.{raw_connection}" if instance_path else raw_connection)
                classification = "INACTIVE_BRANCH"
                if cond_status == "UNRESOLVED_CONDITION" or loop_unresolved > 0:
                    classification = "UNRESOLVED"
                elif cond_value is True:
                    classification = "COMPOSITE_INSTANCE" if row["child_logical_module"] in grouped else "APPROVED_LEAF_PRIMITIVE"

                resolved_physical = ""
                binding_status = classification
                if classification == "APPROVED_LEAF_PRIMITIVE":
                    if row["child_logical_module"] == "PINV":
                        key = (record.class_name, _child_alias_key(record.class_name, row["child_constructor_alias"]))
                        resolution_row = resolution_index.get(key)
                        if resolution_row is None:
                            binding_status = "UNRESOLVED"
                            unresolved_count += 1
                        else:
                            resolved_physical = resolution_row["canonical_physical_cell_name"]
                    elif row["child_logical_module"] == "TRANSMISSION_GATE":
                        resolved_physical = contract["approved_transmission_gate_cell"]
                    elif row["child_logical_module"] in {"PNAND2", "PNAND3"}:
                        binding_status = "NEW_PRIMITIVE_REQUIRED"
                    else:
                        binding_status = "UNRESOLVED"
                        unresolved_count += 1
                instances.append(
                    {
                        "config_id": f"{config['num_rows']}x{config['num_cols']}_{config['operation']}",
                        "hierarchical_instance_path": hierarchical_path,
                        "parent_instance_path": instance_path,
                        "parent_module": module_name,
                        "child_module": row["child_logical_module"],
                        "source_instance_template": row["instance_name_template"],
                        "source_line": row["source_line"],
                        "loop_variable_values": json.dumps(loop_values, sort_keys=True),
                        "branch_condition": row.get("branch_condition", ""),
                        "branch_active": cond_value is True,
                        "concrete_parameters": json.dumps(_parameter_overrides(row, vars_env, self_env, loop_values)[0], sort_keys=True),
                        "child_pin_order": json.dumps(row["child_pin_order"]),
                        "parent_net_connections": json.dumps(raw_connections),
                        "normalized_parent_net_connections": json.dumps(normalized_connections),
                        "instance_classification": binding_status,
                        "resolved_physical_cell_name": resolved_physical,
                    }
                )
                if binding_status == "NEW_PRIMITIVE_REQUIRED":
                    failures.append(
                        {
                            "config_id": f"{config['num_rows']}x{config['num_cols']}_{config['operation']}",
                            "hierarchical_instance_path": hierarchical_path,
                            "instance_classification": binding_status,
                            "reason": f"{row['child_logical_module']} is not an approved reusable primitive",
                        }
                    )
                elif binding_status == "UNRESOLVED":
                    failures.append(
                        {
                            "config_id": f"{config['num_rows']}x{config['num_cols']}_{config['operation']}",
                            "hierarchical_instance_path": hierarchical_path,
                            "instance_classification": binding_status,
                            "reason": "branch condition, loop bounds, or leaf resolution remained unresolved",
                        }
                    )
                if cond_value is True and row["child_logical_module"] in grouped:
                    overrides, _ = _parameter_overrides(row, vars_env, self_env, loop_values)
                    child_binding = {row["child_pin_order"][index]: normalized_connections[index] for index in range(min(len(row["child_pin_order"]), len(normalized_connections)))}
                    expand(row["child_logical_module"], hierarchical_path, child_binding, overrides)

    root_record = registry[root_module]
    expand(root_module, root_module, {pin: pin for pin in root_record.normalized_pin_order}, module_overrides_for_root(config))
    return {
        "config": config,
        "instances": instances,
        "failure_rows": failures,
        "concrete_leaf_primitive_instance_count": sum(1 for row in instances if row["instance_classification"] == "APPROVED_LEAF_PRIMITIVE"),
        "concrete_composite_instance_count": sum(1 for row in instances if row["instance_classification"] == "COMPOSITE_INSTANCE"),
        "unresolved_concrete_instance_count": sum(1 for row in instances if row["instance_classification"] == "UNRESOLVED"),
        "active_leaf_parent_net_connections_complete": all(
            row["parent_net_connections"] != "[]"
            for row in instances
            if row["instance_classification"] == "APPROVED_LEAF_PRIMITIVE"
        ),
    }


def module_overrides_for_root(config: dict[str, Any]) -> dict[str, Any]:
    return {"num_rows": config["num_rows"], "num_cols": config["num_cols"], "operation": config["operation"]}
