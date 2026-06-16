"""Static parser for OpenYield PySpice source files.

The parser deliberately avoids importing OpenYield or PySpice.  It only reads
Python AST nodes so it remains usable in the layout generator environment.
"""

from __future__ import annotations

import ast
from pathlib import Path
from typing import Iterable

from .canonical_names import module_role
from .contracts import ParsedPySpiceModule


def parse_openyield_pyspice_sources(openyield_root: str | Path) -> tuple[list[ParsedPySpiceModule], list[str]]:
    root = Path(openyield_root)
    warnings: list[str] = []
    files = _source_files(root)
    modules: list[ParsedPySpiceModule] = []
    for path in files:
        parsed, file_warnings = parse_pyspice_source_file(path, root)
        modules.extend(parsed)
        warnings.extend(file_warnings)
    modules.sort(key=lambda item: (item.source_file, item.class_name))
    return modules, warnings


def parse_pyspice_source_file(path: str | Path, openyield_root: str | Path | None = None) -> tuple[list[ParsedPySpiceModule], list[str]]:
    source_path = Path(path)
    root = Path(openyield_root) if openyield_root is not None else source_path.parents[0]
    rel_path = _rel(source_path, root)
    warnings: list[str] = []
    try:
        text = _read_text(source_path)
        tree = ast.parse(text)
    except Exception as exc:
        return [], [f"{rel_path}: parse failed: {exc}"]

    modules: list[ParsedPySpiceModule] = []
    for cls in [node for node in tree.body if isinstance(node, ast.ClassDef)]:
        info = _parse_class(cls, rel_path)
        if info is not None:
            modules.append(info)
    return modules, warnings


def _source_files(root: Path) -> list[Path]:
    paths: list[Path] = []
    for subdir in ("sram_compiler/subcircuits", "sram_compiler/testbenches"):
        d = root / subdir
        if d.exists():
            paths.extend(sorted(d.glob("*.py")))
    return paths


def _parse_class(cls: ast.ClassDef, rel_path: str) -> ParsedPySpiceModule | None:
    name_expr = ""
    nodes_expr = ""
    nodes: tuple[str, ...] = ()
    mos_calls = 0
    self_x_calls = 0
    circuit_x_calls = 0
    subcircuit_calls = 0
    warnings: list[str] = []

    for node in ast.walk(cls):
        if isinstance(node, ast.Assign):
            for target in node.targets:
                target_name = _target_name(target)
                if target_name in {"NAME", "self.NAME"}:
                    name_expr = _safe_unparse(node.value)
                elif target_name in {"NODES", "self.NODES"}:
                    nodes_expr = _safe_unparse(node.value)
                    extracted = _extract_literal_strings(node.value)
                    if extracted:
                        nodes = tuple(extracted)
        elif isinstance(node, ast.Call):
            call = _call_name(node)
            if call in {"self.M", "M"} or call.endswith(".M"):
                mos_calls += 1
            elif call == "self.X":
                self_x_calls += 1
            elif call == "circuit.X":
                circuit_x_calls += 1
            elif call.endswith(".subcircuit") or call == "self.subcircuit":
                subcircuit_calls += 1

    original_name = _module_name_from_expr(name_expr, cls.name)
    if not nodes:
        nodes = _heuristic_nodes(original_name, cls.name)
        if nodes:
            warnings.append(f"{cls.name}: NODES are dynamic; used heuristic pin pattern {nodes}.")
    if not _looks_like_pyspice_module(original_name, cls.name, nodes, mos_calls, self_x_calls, circuit_x_calls, rel_path):
        return None
    role = module_role(original_name, cls.name, rel_path)
    if not name_expr:
        warnings.append(f"{cls.name}: no NAME assignment found; using class name as module name.")
    if not nodes:
        warnings.append(f"{cls.name}: no static or heuristic NODES found.")
    return ParsedPySpiceModule(
        source_file=rel_path,
        class_name=cls.name,
        original_module_name=original_name,
        nodes=nodes,
        node_expr=nodes_expr,
        name_expr=name_expr,
        role_hint=role,
        mos_call_count=mos_calls,
        self_instance_call_count=self_x_calls,
        circuit_instance_call_count=circuit_x_calls,
        subcircuit_call_count=subcircuit_calls,
        warnings=tuple(warnings),
    )


def _looks_like_pyspice_module(
    original_name: str,
    class_name: str,
    nodes: tuple[str, ...],
    mos_calls: int,
    self_x_calls: int,
    circuit_x_calls: int,
    rel_path: str,
) -> bool:
    text = f"{original_name} {class_name} {rel_path}".lower()
    if nodes or mos_calls or self_x_calls or circuit_x_calls:
        return True
    return any(k in text for k in ["factory", "testbench", "sram", "decoder", "precharge", "write", "sense", "mux"])


def _module_name_from_expr(expr: str, class_name: str) -> str:
    if not expr:
        return class_name
    stripped = expr.strip()
    if (stripped.startswith("'") and stripped.endswith("'")) or (stripped.startswith('"') and stripped.endswith('"')):
        return stripped[1:-1]
    if stripped.startswith("f'COLUMNMUX") or stripped.startswith('f"COLUMNMUX'):
        return "COLUMNMUX*"
    if stripped.startswith("f'SRAM_6T_CORE") or stripped.startswith('f"SRAM_6T_CORE'):
        return "SRAM_6T_CORE_*"
    if stripped.startswith("f'SRAM_10T_CORE") or stripped.startswith('f"SRAM_10T_CORE'):
        return "SRAM_10T_CORE_*"
    if "Dummy_column" in stripped:
        return "Dummy_Column"
    if "Dummy_row" in stripped:
        return "Dummy_Row"
    if "replica_column" in stripped:
        return "Replica_Column"
    return stripped


def _heuristic_nodes(original_name: str, class_name: str) -> tuple[str, ...]:
    key = f"{original_name} {class_name}"
    if "COLUMNMUX" in key:
        return ("VDD", "VSS", "SA_IN", "SA_INB", "SEL{i}", "BL{i}", "BLB{i}")
    if "SRAM_6T_CORE" in key or class_name == "Sram6TCore":
        return ("VDD", "VSS", "BL{i}", "BLB{i}", "WL{i}")
    if "SRAM_10T_CORE" in key or class_name == "Sram10TCore":
        return ("VDD", "VSS", "BL{i}", "BLB{i}", "WL{i}")
    if class_name == "DECODER_CASCADE" or original_name == "DECODER_CASCADE":
        return ("VDD", "VSS", "A{i}", "WL{i}")
    if class_name == "ADDR_DFF" or original_name == "ADDR_DFF":
        return ("VDD", "VSS", "CLK", "A{i}", "A_dff{i}")
    if class_name == "DATA_DFF" or original_name == "DATA_DFF":
        return ("VDD", "VSS", "CLK", "DIN{i}", "DIN_dff{i}")
    if class_name == "TIME" or original_name == "TIME":
        return (
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
        )
    if class_name == "Dummy_Column":
        return ("VDD", "VSS", "BL", "BLB", "WL{i}")
    if class_name == "Dummy_Row":
        return ("VDD", "VSS", "BL{i}", "BLB{i}", "WL")
    if class_name == "Replica_Column":
        return ("VDD", "VSS", "RBL", "RBLB", "WL{i}")
    return ()


def _extract_literal_strings(node: ast.AST) -> list[str]:
    if isinstance(node, (ast.Tuple, ast.List)):
        values: list[str] = []
        for elt in node.elts:
            if isinstance(elt, ast.Constant) and isinstance(elt.value, str):
                values.append(elt.value)
            elif isinstance(elt, ast.Starred):
                values.extend(_pattern_from_starred(elt.value))
        return values
    return []


def _pattern_from_starred(node: ast.AST) -> list[str]:
    text = _safe_unparse(node)
    if "BLB" in text:
        return ["BLB{i}"]
    if "BL" in text:
        return ["BL{i}"]
    if "WL" in text:
        return ["WL{i}"]
    if "SELB" in text:
        return ["SELB{i}"]
    if "SEL" in text:
        return ["SEL{i}"]
    if "A_dff" in text:
        return ["A_dff{i}"]
    if "A" in text:
        return ["A{i}"]
    if "DIN_dff" in text:
        return ["DIN_dff{i}"]
    if "DIN" in text:
        return ["DIN{i}"]
    return []


def _target_name(node: ast.AST) -> str:
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute) and isinstance(node.value, ast.Name):
        return f"{node.value.id}.{node.attr}"
    return ""


def _call_name(node: ast.Call) -> str:
    func = node.func
    if isinstance(func, ast.Name):
        return func.id
    if isinstance(func, ast.Attribute):
        if isinstance(func.value, ast.Name):
            return f"{func.value.id}.{func.attr}"
        if isinstance(func.value, ast.Attribute):
            return f"{_safe_unparse(func.value)}.{func.attr}"
        return func.attr
    return ""


def _safe_unparse(node: ast.AST) -> str:
    try:
        return ast.unparse(node)
    except Exception:
        return type(node).__name__


def _read_text(path: Path) -> str:
    for enc in ("utf-8-sig", "utf-8", "gb18030"):
        try:
            return path.read_text(encoding=enc)
        except UnicodeDecodeError:
            continue
    return path.read_text(encoding="utf-8", errors="replace")


def _rel(path: Path, root: Path) -> str:
    try:
        return path.resolve().relative_to(root.resolve()).as_posix()
    except ValueError:
        return path.as_posix()
