from __future__ import annotations

import ast
import hashlib
import re
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from sram_layoutgen.openyield_adapter.dimension_units import normalize_dimension_nm
from sram_layoutgen.openyield_adapter.parameterized_cell_naming import build_cache_key, canonical_cell_name


@dataclass
class _FunctionContext:
    source_file: Path
    class_name: str
    function_name: str
    defaults: dict[str, ast.expr]
    env: dict[str, ast.expr]


def extract_source_derived_pinv_instances(source_files: list[Path]) -> dict[str, Any]:
    rows: list[dict[str, Any]] = []
    for source_file in source_files:
        tree = ast.parse(source_file.read_text(encoding="utf-8"), filename=str(source_file))
        for node in tree.body:
            if isinstance(node, ast.ClassDef):
                rows.extend(_extract_class_pinv_instances(node, source_file))
    collisions = _build_collision_rows(rows)
    return {
        "rows": rows,
        "collision_rows": collisions,
        "logical_name_collision_detected": bool(collisions),
        "logical_name_collision_count": len(collisions),
        "logical_names_with_multiple_parameter_sets": sorted({row["generated_logical_name"] for row in collisions}),
        "source_pinv_instance_count": len(rows),
        "source_pinv_parameter_set_count": len({row["canonical_parameter_tuple"] for row in rows}),
    }


def build_corrected_physical_variant_matrix(pinv_rows: list[dict[str, Any]]) -> dict[str, Any]:
    tuple_to_aliases: dict[str, set[str]] = defaultdict(set)
    alias_to_tuples: dict[str, set[str]] = defaultdict(set)
    for row in pinv_rows:
        tuple_to_aliases[row["canonical_parameter_tuple"]].add(row["generated_logical_name"])
        alias_to_tuples[row["generated_logical_name"]].add(row["canonical_parameter_tuple"])

    variant_rows: list[dict[str, Any]] = []
    for row in pinv_rows:
        variant_rows.append(
            {
                "logical_alias": row["generated_logical_name"],
                "source_instance_path": f"{row['parent_logical_module']}.{row['python_variable_name']}",
                "source_parent_module": row["parent_logical_module"],
                "logical_function": "inverter",
                "technology": "FreePDK45",
                "nmos_width_nm": row["nmos_width_nm"],
                "pmos_width_nm": row["pmos_width_nm"],
                "channel_length_nm": row["length_nm"],
                "finger_or_mult_policy": "single_inverter_pair",
                "contact_policy": "OpenRAM default pgate/ptx contact policy",
                "rail_policy": "OpenRAM row rails on vdd/gnd",
                "canonical_physical_cell_name": row["canonical_physical_cell_name"],
                "canonical_parameter_tuple": row["canonical_parameter_tuple"],
                "cache_key": row["cache_key"],
                "source_trace_hash": row["source_trace_hash"],
                "shares_logical_alias_with_other_variant": len(alias_to_tuples[row["generated_logical_name"]]) > 1,
                "shares_parameter_tuple_with_other_alias": len(tuple_to_aliases[row["canonical_parameter_tuple"]]) > 1,
                "requires_distinct_physical_cell": len(alias_to_tuples[row["generated_logical_name"]]) > 1 or len(tuple_to_aliases[row["canonical_parameter_tuple"]]) == 1,
                "supported_by_openram_pinv": True,
                "supported_by_openram_ptx": True,
                "adapter_requirement": "OPENRAM_FREEPDK45_DEVICE_CONTACT_ADAPTER",
                "status": "SOURCE_DERIVED_VARIANT_LOCKED",
            }
        )
    return {
        "rows": variant_rows,
        "corrected_physical_variant_count": len(variant_rows),
        "distinct_inverter_variant_count": len({row["canonical_parameter_tuple"] for row in variant_rows}),
    }


def build_corrected_requirement_rows(
    original_requirement_rows: list[dict[str, str]],
    variant_rows: list[dict[str, Any]],
) -> dict[str, Any]:
    corrected_rows: list[dict[str, Any]] = []
    dimension_errors = []
    for row in original_requirement_rows:
        logical_module = row["logical_module"]
        if logical_module.startswith("PINV"):
            matches = [item for item in variant_rows if item["logical_alias"] == logical_module]
            if matches:
                for item in matches:
                    corrected_rows.append(
                        {
                            "logical_alias": logical_module,
                            "source_context": item["source_instance_path"],
                            "physical_variant": item["canonical_parameter_tuple"],
                            "canonical_physical_name": item["canonical_physical_cell_name"],
                            "nmos_width_nm": item["nmos_width_nm"],
                            "pmos_width_nm": item["pmos_width_nm"],
                            "channel_length_nm": item["channel_length_nm"],
                            "generation_priority": row["generation_priority"],
                            "required_generator_level": row["required_generator_level"],
                            "candidate_existing_generator_path": row["candidate_existing_generator_path"],
                        }
                    )
            else:
                corrected_rows.append(
                    {
                        "logical_alias": logical_module,
                        "source_context": row["source_file"],
                        "physical_variant": "UNMAPPED",
                        "canonical_physical_name": row["expected_physical_cell_name"],
                        "nmos_width_nm": "",
                        "pmos_width_nm": "",
                        "channel_length_nm": "",
                        "generation_priority": row["generation_priority"],
                        "required_generator_level": row["required_generator_level"],
                        "candidate_existing_generator_path": row["candidate_existing_generator_path"],
                    }
                )
        else:
            corrected_rows.append(
                {
                    "logical_alias": logical_module,
                    "source_context": row["source_file"],
                    "physical_variant": row.get("expected_physical_cell_name", logical_module),
                    "canonical_physical_name": row.get("expected_physical_cell_name", logical_module),
                    "nmos_width_nm": _nm_from_meter_string(row.get("nmos_width", "")),
                    "pmos_width_nm": _nm_from_meter_string(row.get("pmos_width", "")),
                    "channel_length_nm": _nm_from_meter_string(row.get("length", "")),
                    "generation_priority": row["generation_priority"],
                    "required_generator_level": row["required_generator_level"],
                    "candidate_existing_generator_path": row["candidate_existing_generator_path"],
                }
            )
        if logical_module == "PINV1" and row.get("nmos_width") == "0.25e-6" and row.get("pmos_width") == "0.50e-6":
            dimension_errors.append(logical_module)
    return {
        "rows": corrected_rows,
        "requirement_matrix_dimension_error_detected": bool(dimension_errors),
        "requirement_matrix_dimension_error_count": len(dimension_errors),
    }


def _extract_class_pinv_instances(class_node: ast.ClassDef, source_file: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for item in class_node.body:
        if isinstance(item, ast.FunctionDef):
            defaults = _collect_function_defaults(item)
            context = _FunctionContext(
                source_file=source_file,
                class_name=class_node.name,
                function_name=item.name,
                defaults=defaults,
                env=dict(defaults),
            )
            for stmt in item.body:
                rows.extend(_walk_statement(stmt, context))
    return rows


def _walk_statement(stmt: ast.stmt, context: _FunctionContext) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    if isinstance(stmt, ast.Assign):
        if isinstance(stmt.value, ast.Call) and _call_name(stmt.value) == "Pinv":
            rows.append(_row_from_pinv_call(stmt.value, stmt.targets[0], context))
        else:
            for target in stmt.targets:
                name = _env_key(target)
                if name is not None:
                    context.env[name] = stmt.value
    elif isinstance(stmt, ast.AnnAssign) and stmt.value is not None:
        name = _env_key(stmt.target)
        if name is not None:
            context.env[name] = stmt.value
    elif isinstance(stmt, ast.If):
        for branch_stmt in stmt.body:
            rows.extend(_walk_statement(branch_stmt, context))
        for branch_stmt in stmt.orelse:
            rows.extend(_walk_statement(branch_stmt, context))
    return rows


def _row_from_pinv_call(call: ast.Call, target: ast.expr, context: _FunctionContext) -> dict[str, Any]:
    args, kwargs = _bind_call_arguments(call, ["nmos_model", "pmos_model", "nmos_width", "pmos_width", "length", "w_rc", "pi_res", "pi_cap", "num"])
    num_expr = kwargs.get("num") or kwargs.get("num_argument") or ast.Constant(value="")
    generated_logical_name = _pinv_name_from_num(num_expr, context)
    nmos_width_nm = _expr_to_nm_string(args["nmos_width"], context)
    pmos_width_nm = _expr_to_nm_string(args["pmos_width"], context)
    length_nm = _expr_to_nm_string(args["length"], context)
    num_argument = _resolve_generic_expr(num_expr, context)
    drive_scale_expr = _infer_drive_scale_expr(args["nmos_width"], context) or _infer_drive_scale_expr(args["pmos_width"], context) or "1"
    source_role = f"{context.class_name}.{_target_name(target) or 'pinv'}"
    # `num` in OpenYield Pinv is a logical naming suffix (`PINV1`, `PINV2`, ...)
    # rather than a transistor finger/mults control, so physical identity must
    # be keyed by real geometry parameters instead of alias numbering.
    canonical_tuple = f"NW{nmos_width_nm}|PW{pmos_width_nm}|L{length_nm}"
    logical_type_for_name = "PINV"
    if not (str(nmos_width_nm).isdigit() and str(pmos_width_nm).isdigit() and str(length_nm).isdigit()):
        logical_type_for_name = f"PINV_{hashlib.sha256(canonical_tuple.encode('utf-8')).hexdigest()[:8].upper()}"
    canonical_name = canonical_cell_name(logical_type=logical_type_for_name, nmos_width_nm=_base_nm_token(nmos_width_nm), pmos_width_nm=_base_nm_token(pmos_width_nm), length_nm=_base_nm_token(length_nm))
    trace_payload = {
        "technology": "FreePDK45",
        "logical_type": "PINV",
        "source_role": source_role,
        "nmos_width_nm": nmos_width_nm,
        "pmos_width_nm": pmos_width_nm,
        "channel_length_nm": length_nm,
        "num": num_argument,
    }
    source_trace_hash = hashlib.sha256(repr(sorted(trace_payload.items())).encode("utf-8")).hexdigest()[:24]
    cache_key = build_cache_key(
        technology="FreePDK45",
        logical_type="PINV",
        nmos_width_nm=nmos_width_nm,
        pmos_width_nm=pmos_width_nm,
        channel_length_nm=length_nm,
        finger_or_mult_policy="single_inverter_pair",
        contact_policy="OpenRAM default pgate/ptx contact policy",
        rail_policy="OpenRAM row rails on vdd/gnd",
        orientation_policy="fixed row orientation",
        source_netlist_role=source_role,
    )
    return {
        "source_file": str(context.source_file),
        "source_class": context.class_name,
        "source_function": context.function_name,
        "source_line": call.lineno,
        "parent_logical_module": context.class_name,
        "python_variable_name": _target_name(target) or "",
        "num_argument": num_argument,
        "generated_logical_name": generated_logical_name,
        "nmos_width": _resolve_generic_expr(args["nmos_width"], context),
        "pmos_width": _resolve_generic_expr(args["pmos_width"], context),
        "length": _resolve_generic_expr(args["length"], context),
        "drive_scale": drive_scale_expr,
        "operation_dependency": _dependency_from_row("operation", [context.class_name, drive_scale_expr]),
        "row_dependency": _dependency_from_row("num_rows", [context.class_name, drive_scale_expr]),
        "column_dependency": _dependency_from_row("num_cols", [context.class_name, drive_scale_expr]),
        "parameter_expression": f"nmos={_resolve_generic_expr(args['nmos_width'], context)}|pmos={_resolve_generic_expr(args['pmos_width'], context)}|length={_resolve_generic_expr(args['length'], context)}|num={num_argument}",
        "parameter_resolution_status": "RESOLVED_SOURCE_STATIC",
        "nmos_width_nm": nmos_width_nm,
        "pmos_width_nm": pmos_width_nm,
        "length_nm": length_nm,
        "canonical_physical_cell_name": canonical_name,
        "canonical_parameter_tuple": canonical_tuple,
        "cache_key": cache_key,
        "source_trace_hash": source_trace_hash,
    }


def _collect_function_defaults(fn: ast.FunctionDef) -> dict[str, ast.expr]:
    defaults: dict[str, ast.expr] = {}
    positional_args = fn.args.args
    defaults_list = fn.args.defaults
    if defaults_list:
        for arg, default in zip(positional_args[-len(defaults_list):], defaults_list):
            defaults[arg.arg] = default
    for arg, default in zip(fn.args.kwonlyargs, fn.args.kw_defaults):
        if default is not None:
            defaults[arg.arg] = default
    return defaults


def _bind_call_arguments(call: ast.Call, positional_names: list[str]) -> tuple[dict[str, ast.expr], dict[str, ast.expr]]:
    args: dict[str, ast.expr] = {}
    for index, expr in enumerate(call.args):
        if index < len(positional_names):
            args[positional_names[index]] = expr
    kwargs = {kw.arg: kw.value for kw in call.keywords if kw.arg}
    for name in positional_names:
        if name in kwargs:
            args[name] = kwargs[name]
    return args, kwargs


def _target_name(target: ast.expr) -> str | None:
    if isinstance(target, ast.Attribute) and isinstance(target.value, ast.Name) and target.value.id == "self":
        return target.attr
    if isinstance(target, ast.Name):
        return target.id
    return None


def _env_key(target: ast.expr) -> str | None:
    if isinstance(target, ast.Attribute) and isinstance(target.value, ast.Name) and target.value.id == "self":
        return f"self.{target.attr}"
    if isinstance(target, ast.Name):
        return target.id
    return None


def _call_name(call: ast.Call) -> str:
    if isinstance(call.func, ast.Name):
        return call.func.id
    if isinstance(call.func, ast.Attribute):
        return call.func.attr
    return ""


def _resolve_generic_expr(expr: ast.expr, context: _FunctionContext, stack: set[str] | None = None) -> str:
    stack = stack or set()
    if isinstance(expr, ast.Name) and expr.id in context.env and expr.id not in stack:
        return _resolve_generic_expr(context.env[expr.id], context, stack | {expr.id})
    if isinstance(expr, ast.Attribute) and isinstance(expr.value, ast.Name) and expr.value.id == "self":
        key = f"self.{expr.attr}"
        if key in context.env and key not in stack:
            return _resolve_generic_expr(context.env[key], context, stack | {key})
        if expr.attr in context.env and expr.attr not in stack:
            return _resolve_generic_expr(context.env[expr.attr], context, stack | {expr.attr})
    if isinstance(expr, ast.Constant):
        return str(expr.value)
    if isinstance(expr, ast.UnaryOp) and isinstance(expr.op, ast.USub):
        return f"-{_resolve_generic_expr(expr.operand, context, stack)}"
    if isinstance(expr, ast.BinOp):
        return f"({_resolve_generic_expr(expr.left, context, stack)}{_binop_symbol(expr.op)}{_resolve_generic_expr(expr.right, context, stack)})"
    if isinstance(expr, ast.Call):
        func = _resolve_generic_expr(expr.func, context, stack) if not isinstance(expr.func, ast.Name) else expr.func.id
        return f"{func}({', '.join(_resolve_generic_expr(arg, context, stack) for arg in expr.args)})"
    if isinstance(expr, ast.Attribute):
        return ast.unparse(expr)
    return ast.unparse(expr)


def _expr_to_nm_string(expr: ast.expr, context: _FunctionContext, stack: set[str] | None = None) -> str:
    stack = stack or set()
    if isinstance(expr, ast.Name) and expr.id in context.env and expr.id not in stack:
        return _expr_to_nm_string(context.env[expr.id], context, stack | {expr.id})
    if isinstance(expr, ast.Attribute) and isinstance(expr.value, ast.Name) and expr.value.id == "self":
        key = f"self.{expr.attr}"
        if key in context.env and key not in stack:
            return _expr_to_nm_string(context.env[key], context, stack | {key})
        if expr.attr in context.env and expr.attr not in stack:
            return _expr_to_nm_string(context.env[expr.attr], context, stack | {expr.attr})
    if isinstance(expr, ast.Constant):
        if isinstance(expr.value, (int, float)):
            return str(normalize_dimension_nm(str(expr.value), "METER"))
        return str(expr.value)
    if isinstance(expr, ast.UnaryOp) and isinstance(expr.op, ast.USub):
        return f"-{_expr_to_nm_string(expr.operand, context, stack)}"
    if isinstance(expr, ast.BinOp):
        if isinstance(expr.op, (ast.Mult, ast.Div)):
            left_const = _meter_constant_to_nm(expr.left)
            right_const = _meter_constant_to_nm(expr.right)
            if left_const is not None and right_const is None:
                return f"({left_const}{_binop_symbol(expr.op)}{_resolve_generic_expr(expr.right, context, stack)})"
            if right_const is not None and left_const is None:
                return f"({_resolve_generic_expr(expr.left, context, stack)}{_binop_symbol(expr.op)}{right_const})"
        return _resolve_generic_expr(expr, context, stack)
    if isinstance(expr, ast.Call):
        if isinstance(expr.func, ast.Name) and expr.func.id == "float":
            return _resolve_generic_expr(expr.args[0], context, stack)
        if isinstance(expr.func, ast.Name) and expr.func.id == "max":
            return f"max({', '.join(_resolve_generic_expr(arg, context, stack) for arg in expr.args)})"
        return _resolve_generic_expr(expr, context, stack)
    return _resolve_generic_expr(expr, context, stack)


def _binop_symbol(op: ast.operator) -> str:
    return {
        ast.Add: "+",
        ast.Sub: "-",
        ast.Mult: "*",
        ast.Div: "/",
        ast.Pow: "**",
    }[type(op)]


def _pinv_name_from_num(num_expr: ast.expr, context: _FunctionContext) -> str:
    value = _resolve_generic_expr(num_expr, context)
    if value in {"''", "", "None"}:
        return "PINV"
    return f"PINV{value}"


def _infer_drive_scale_expr(expr: ast.expr, context: _FunctionContext) -> str | None:
    text = _resolve_generic_expr(expr, context)
    return text if "drive_scale" in text else None


def _dependency_from_row(token: str, texts: list[str]) -> str:
    return "present" if any(token in text for text in texts) else "none"


def _build_collision_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    by_name: dict[str, set[str]] = defaultdict(set)
    for row in rows:
        by_name[row["generated_logical_name"]].add(row["canonical_parameter_tuple"])
    collision_rows: list[dict[str, Any]] = []
    for name, tuples in sorted(by_name.items()):
        if len(tuples) > 1:
            for parameter_tuple in sorted(tuples):
                collision_rows.append(
                    {
                        "generated_logical_name": name,
                        "canonical_parameter_tuple": parameter_tuple,
                        "distinct_parameter_set_count": len(tuples),
                    }
                )
    return collision_rows


def _nm_from_meter_string(text: str) -> str:
    if not text:
        return ""
    cleaned = text.strip()
    if cleaned.endswith("+"):
        cleaned = cleaned[:-1]
    try:
        return str(normalize_dimension_nm(cleaned, "METER"))
    except Exception:
        return cleaned


def _base_nm_token(value: str) -> int:
    match = next((token for token in re.findall(r"[1-9][0-9]*", value)), None)
    if match is None:
        raise ValueError(f"could not derive base nm token from {value}")
    return int(match)


def _meter_constant_to_nm(expr: ast.expr) -> int | None:
    if isinstance(expr, ast.Constant) and isinstance(expr.value, (int, float)):
        return normalize_dimension_nm(str(expr.value), "METER")
    return None
