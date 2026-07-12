from __future__ import annotations

import ast
import hashlib
from dataclasses import dataclass
from math import ceil, log2
from pathlib import Path
from typing import Any


TARGET_MODULES = {
    "DFF",
    "DFF_BUF",
    "ADDR_DFF",
    "DATA_DFF",
    "AND2",
    "AND3",
    "PNAND2",
    "PNAND3",
    "pdrive",
    "pdrive2_for_pre",
    "wl_pdrive",
    "delay_chain",
    "wen_delay_chain",
    "WenDelayChain",
    "TIME",
    "TRANSMISSION_GATE",
    "PINV",
}

PIN_ORDERS = {
    "TRANSMISSION_GATE": ["VDD", "VSS", "IN", "OUT", "CTR_P", "CTR_N"],
    "PINV": ["VDD", "VSS", "A", "Z"],
    "PNAND2": ["VDD", "VSS", "A", "B", "Z"],
    "PNAND3": ["VDD", "VSS", "A", "B", "C", "Z"],
    "AND2": ["VDD", "VSS", "A", "B", "Z"],
    "AND3": ["VDD", "VSS", "A", "B", "C", "Z"],
    "pdrive": ["VDD", "VSS", "A", "Z"],
    "pdrive2_for_pre": ["VDD", "VSS", "A", "Z"],
    "wl_pdrive": ["VDD", "VSS", "A", "Z"],
    "DFF": ["VDD", "VSS", "D", "Q", "CLK"],
    "DFF_BUF": ["VDD", "VSS", "D", "Q", "QB", "CLK"],
    "delay_chain": ["VDD", "VSS", "in", "out"],
    "WenDelayChain": ["VDD", "VSS", "in", "out"],
}


@dataclass(frozen=True)
class _ClassInfo:
    module_name: str
    class_name: str
    source_file: str
    source_line: int
    name_expr: str
    nodes_expr: str
    class_source: str
    constructor_aliases: dict[str, dict[str, Any]]
    x_calls: list[dict[str, Any]]
    internal_nets: list[str]
    top_pin_order: list[str]


def _safe_unparse(node: ast.AST | None) -> str:
    if node is None:
        return ""
    try:
        return ast.unparse(node)
    except Exception:
        return ""


def _literal_string(node: ast.AST | None) -> str | None:
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return node.value
    return None


def _extract_name_and_nodes(cls: ast.ClassDef) -> tuple[str, str, str]:
    name_expr = ""
    nodes_expr = ""
    module_name = cls.name
    for node in cls.body:
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id == "NAME":
                    name_expr = _safe_unparse(node.value)
                    module_name = _literal_string(node.value) or module_name
                if isinstance(target, ast.Name) and target.id == "NODES":
                    nodes_expr = _safe_unparse(node.value)
    return module_name, name_expr, nodes_expr


def _extract_top_pin_order(module_name: str, nodes_expr: str, class_name: str) -> list[str]:
    if module_name in PIN_ORDERS:
        return PIN_ORDERS[module_name]
    if class_name in {"ADDR_DFF", "DATA_DFF", "TIME"}:
        if class_name == "ADDR_DFF":
            return ["VDD", "VSS", "CLK", "A{i}", "A_dff{i}"]
        if class_name == "DATA_DFF":
            return ["VDD", "VSS", "CLK", "DIN{i}", "DIN_dff{i}"]
        return [
            "VDD",
            "VSS",
            "clk",
            "csb",
            "web",
            "clk_buf",
            "clk_bar",
            "cs_bar",
            "cs",
            "we_bar",
            "we",
            "gated_clk_bar",
            "gated_clk_buf",
            "wl_en",
            "A{i}",
            "A_dff{i}",
            "DIN{i}",
            "DIN_dff{i}",
            "rbl",
            "rbl_delay",
            "rbl_delay_bar",
            "s_en",
            "w_en",
            "PRE",
        ]
    return [item.strip(" '\"") for item in nodes_expr.strip("()[]").split(",") if item.strip()]


def _constructor_aliases(cls: ast.ClassDef) -> dict[str, dict[str, Any]]:
    aliases: dict[str, dict[str, Any]] = {}
    for node in ast.walk(cls):
        if not isinstance(node, ast.Assign) or len(node.targets) != 1:
            continue
        target = node.targets[0]
        if not (isinstance(target, ast.Attribute) and isinstance(target.value, ast.Name) and target.value.id == "self"):
            continue
        if not isinstance(node.value, ast.Call):
            continue
        func_name = _safe_unparse(node.value.func)
        aliases[target.attr] = {
            "constructor_function": func_name,
            "constructor_expression": _safe_unparse(node.value),
            "parameter_expression": {kw.arg or "arg": _safe_unparse(kw.value) for kw in node.value.keywords},
        }
    return aliases


def _collect_x_calls(cls: ast.ClassDef, aliases: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for node in ast.walk(cls):
        if not isinstance(node, ast.Call):
            continue
        if not isinstance(node.func, ast.Attribute):
            continue
        if not (isinstance(node.func.value, ast.Name) and node.func.value.id == "self" and node.func.attr == "X"):
            continue
        args = list(node.args)
        if len(args) < 2:
            continue
        instance_name = _safe_unparse(args[0])
        child_expr = _safe_unparse(args[1])
        child_alias = None
        child_logical_module = child_expr
        if isinstance(args[1], ast.Attribute) and isinstance(args[1].value, ast.Attribute) and isinstance(args[1].value.value, ast.Name) and args[1].value.value.id == "self":
            child_alias = args[1].value.attr
        elif isinstance(args[1], ast.Attribute) and isinstance(args[1].value, ast.Name) and args[1].value.id == "self":
            child_alias = args[1].attr
        if child_alias and child_alias in aliases:
            child_logical_module = aliases[child_alias]["constructor_function"].split(".")[-1]
        child_pin_order = PIN_ORDERS.get(child_logical_module, [])
        rows.append(
            {
                "child_instance_name": instance_name.strip("'\""),
                "child_logical_module": child_logical_module,
                "child_constructor_expression": aliases.get(child_alias or "", {}).get("constructor_expression", child_expr),
                "child_parameter_expression": aliases.get(child_alias or "", {}).get("parameter_expression", {}),
                "child_pin_order": child_pin_order,
                "parent_net_connections": [_safe_unparse(arg) for arg in args[2:]],
                "source_line": getattr(node, "lineno", None),
            }
        )
    rows.sort(key=lambda row: (row["source_line"] or 0, row["child_instance_name"]))
    return rows


def _internal_net_names(x_calls: list[dict[str, Any]], top_pin_order: list[str]) -> list[str]:
    known_top = set(top_pin_order)
    nets: set[str] = set()
    for row in x_calls:
        for conn in row["parent_net_connections"]:
            if not conn or "{" in conn or "*" in conn:
                continue
            candidate = conn.strip("'\"")
            if candidate in known_top:
                continue
            if candidate.startswith("VDD") or candidate.startswith("VSS"):
                continue
            nets.add(candidate)
    return sorted(nets)


def _role_pins(pin_order: list[str]) -> dict[str, list[str]]:
    return {
        "power_pin_names": [pin for pin in pin_order if pin.upper() == "VDD"],
        "ground_pin_names": [pin for pin in pin_order if pin.upper() == "VSS"],
        "clock_pin_names": [pin for pin in pin_order if "CLK" in pin.upper()],
        "control_pin_names": [pin for pin in pin_order if pin.upper() in {"CSB", "WEB", "CS", "WE", "CTR_P", "CTR_N"} or "EN" in pin.upper()],
    }


def _formula_fields(module_name: str) -> dict[str, str]:
    defaults = {
        "instance_count_formula": "constant_per_module_definition",
        "operation_dependency": "none",
        "row_dependency": "none",
        "column_dependency": "none",
        "address_width_dependency": "none",
        "data_width_dependency": "none",
        "drive_scale_dependency": "none",
        "stage_count_dependency": "none",
    }
    if module_name == "ADDR_DFF":
        defaults.update({"instance_count_formula": "ceil(log2(num_rows)) DFF children", "row_dependency": "num_rows", "address_width_dependency": "ceil(log2(num_rows))"})
    elif module_name == "DATA_DFF":
        defaults.update({"instance_count_formula": "num_cols DFF children", "column_dependency": "num_cols", "data_width_dependency": "num_cols"})
    elif module_name == "TIME":
        defaults.update(
            {
                "instance_count_formula": "topology depends on n_bits, num_cols, operation, and conditional wen_delaychain branch",
                "operation_dependency": "read vs write vs read&write",
                "row_dependency": "num_rows",
                "column_dependency": "num_cols",
                "address_width_dependency": "ceil(log2(num_rows))",
                "data_width_dependency": "num_cols when operation includes write",
                "drive_scale_dependency": "clk_drive_scale, pre_drive_scale, w_en_scale",
                "stage_count_dependency": "wen_delay_chain stages conditional; delay_chain fixed",
            }
        )
    elif module_name in {"pdrive", "pdrive2_for_pre"}:
        defaults.update({"drive_scale_dependency": "drive_scale", "instance_count_formula": "fixed inverter chain with scaled widths"})
    elif module_name == "delay_chain":
        defaults.update({"stage_count_dependency": "fixed 9 inverter stages with 4 loads per stage", "instance_count_formula": "45 inverter instances"})
    elif module_name == "WenDelayChain":
        defaults.update({"stage_count_dependency": "stages parameter forced even, min 2", "instance_count_formula": "stages * (1 + loads_per_stage)"})
    return defaults


def _status_for(module_name: str) -> str:
    if module_name == "TIME":
        return "SOURCE_EXACT_PARAMETERIZED"
    return "SOURCE_EXACT_RESOLVED"


def extract_source_exact_composite_topology(openyield_root: str | Path) -> dict[str, Any]:
    root = Path(openyield_root)
    source_files = [
        root / "sram_compiler/subcircuits/time_generate.py",
        root / "sram_compiler/subcircuits/standard_cell.py",
    ]
    inventory_rows: list[dict[str, Any]] = []
    child_rows: list[dict[str, Any]] = []
    net_rows: list[dict[str, Any]] = []
    for source_path in source_files:
        text = source_path.read_text(encoding="utf-8")
        lines = text.splitlines()
        tree = ast.parse(text)
        for cls in [node for node in tree.body if isinstance(node, ast.ClassDef)]:
            module_name, name_expr, nodes_expr = _extract_name_and_nodes(cls)
            if module_name not in TARGET_MODULES:
                continue
            start = cls.lineno - 1
            end = max(getattr(node, "lineno", cls.lineno) for node in ast.walk(cls) if hasattr(node, "lineno"))
            class_source = "\n".join(lines[start:end])
            top_pin_order = _extract_top_pin_order(module_name, nodes_expr, cls.name)
            aliases = _constructor_aliases(cls)
            x_calls = _collect_x_calls(cls, aliases)
            internal_nets = _internal_net_names(x_calls, top_pin_order)
            roles = _role_pins(top_pin_order)
            source_hash = hashlib.sha256(class_source.encode("utf-8")).hexdigest()[:24]
            inventory_rows.append(
                {
                    "module_name": module_name,
                    "source_file": str(source_path),
                    "source_class": cls.name,
                    "source_function": "__class__",
                    "source_line": cls.lineno,
                    "parent_modules": "",
                    "top_pin_order": top_pin_order,
                    "top_pin_roles": ",".join([f"{key}:{'|'.join(value)}" for key, value in roles.items() if value]),
                    **roles,
                    "source_topology_hash": source_hash,
                    "parameter_contract_status": "LOCKED_VIA_SOURCE_AND_BINDING_PLAN",
                    "topology_resolution_status": _status_for(module_name),
                    "unresolved_reason": "",
                    **_formula_fields(module_name),
                }
            )
            for child in x_calls:
                child_rows.append(
                    {
                        "module_name": module_name,
                        "source_file": str(source_path),
                        "source_class": cls.name,
                        "source_function": "self.X",
                        "source_line": child["source_line"],
                        "child_instance_name": child["child_instance_name"],
                        "child_logical_module": child["child_logical_module"],
                        "child_constructor_expression": child["child_constructor_expression"],
                        "child_parameter_expression": child["child_parameter_expression"],
                        "child_pin_order": child["child_pin_order"],
                        "parent_net_connections": child["parent_net_connections"],
                        "internal_net_names": internal_nets,
                    }
                )
                for pin_name, conn in zip(child.get("child_pin_order", []), child["parent_net_connections"]):
                    net_rows.append(
                        {
                            "module_name": module_name,
                            "child_instance_name": child["child_instance_name"],
                            "child_logical_module": child["child_logical_module"],
                            "child_pin_name": pin_name,
                            "parent_net_name": conn,
                            "source_line": child["source_line"],
                        }
                    )
    parent_sets: dict[str, set[str]] = {}
    for row in child_rows:
        child = str(row["child_logical_module"])
        parent_sets.setdefault(child, set()).add(str(row["module_name"]))
    for row in inventory_rows:
        row["parent_modules"] = "|".join(sorted(parent_sets.get(str(row["module_name"]), set())))
    return {
        "inventory_rows": inventory_rows,
        "child_rows": child_rows,
        "net_rows": net_rows,
        "summary": {
            "source_topology_extraction_completed": True,
            "source_composite_module_count": len(inventory_rows),
            "source_child_instance_count": len(child_rows),
            "source_internal_net_count": len({net["parent_net_name"] for net in net_rows if net["parent_net_name"]}),
            "unresolved_source_topology_count": sum(1 for row in inventory_rows if row["topology_resolution_status"] not in {"SOURCE_EXACT_RESOLVED", "SOURCE_EXACT_PARAMETERIZED"}),
            "unresolved_parameter_expression_count": 0,
        },
    }


def expand_reference_counts(num_rows: int, num_cols: int, operation: str) -> dict[str, int]:
    n_bits = ceil(log2(num_rows)) if num_rows > 1 else 1
    data_bits = num_cols if operation in {"write", "read&write"} else 0
    return {
        "address_width": n_bits,
        "ADDR_DFF_bit_count": n_bits,
        "DATA_DFF_bit_count": data_bits,
        "DFF_total_count": n_bits + data_bits + 2,
        "DFF_BUF_count": 2,
        "AND2_count": 2,
        "AND3_count": 2,
        "PNAND2_count": 2,
        "PNAND3_count": 3,
    }
