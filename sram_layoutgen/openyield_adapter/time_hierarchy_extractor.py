from __future__ import annotations

import ast
import contextlib
import io
import math
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

from sram_layoutgen.openyield_adapter.clean_top_export import TOP_MODULE_NAME, extract_clean_top, parse_spice_text
from sram_layoutgen.openyield_adapter.openyield_graph_export import build_clean_graph
from sram_layoutgen.openyield_adapter.pyspice_source_parser import parse_openyield_pyspice_sources


CONTROL_OUTPUT_HINTS = (
    "clk_buf",
    "clk_bar",
    "cs_bar",
    "cs",
    "we_bar",
    "we",
    "gated_clk_bar",
    "gated_clk_buf",
    "wl_en",
    "rbl_delay",
    "rbl_delay_bar",
    "s_en",
    "w_en",
    "pre",
    "a_dff",
    "din_dff",
)


def generate_operation_graph(
    *,
    repo_root: Path,
    openyield_root: Path,
    operation: str,
    num_rows: int,
    num_cols: int,
    choose_columnmux: bool,
    sim_path: Path,
) -> dict[str, Any]:
    if str(repo_root) not in sys.path:
        sys.path.insert(0, str(repo_root))
    from scripts.M12N2_clean_openyield_sram_top import _load_openyield_config

    if str(openyield_root) not in sys.path:
        sys.path.insert(0, str(openyield_root))
    from sram_compiler.testbenches.sram_6t_core_testbench import Sram6TCoreTestbench

    cfg = _load_openyield_config(openyield_root)
    cfg.global_config.num_rows = num_rows
    cfg.global_config.num_cols = num_cols
    cfg.global_config.choose_columnmux = choose_columnmux
    cfg.global_config.sram_cell_type = "SRAM_6T_CELL"
    tb = Sram6TCoreTestbench(
        cfg,
        sram_cell_type=cfg.global_config.sram_cell_type,
        w_rc=False,
        custom_mc=False,
        sweep_cell=False,
        sweep_precharge=False,
        sweep_senseamp=False,
        sweep_wordlinedriver=False,
        sweep_columnmux=False,
        sweep_writedriver=False,
        sweep_decoder=False,
        corner=cfg.global_config.corner,
        choose_columnmux=choose_columnmux,
        real_cell_mode=0,
        q_init_val=0,
        sim_path=str(sim_path),
    )
    capture = io.StringIO()
    with contextlib.redirect_stdout(capture), contextlib.redirect_stderr(capture):
        circuit = tb.create_testbench(operation, num_rows - 1, num_cols - 1)
    text = str(circuit)
    parsed = parse_spice_text(text)
    source_trace = {
        "generator": "sram_compiler/testbenches/sram_6t_core_testbench.py::Sram6TCoreTestbench.create_testbench",
        "sample_netlist": f"generated::{operation}",
    }
    payload = extract_clean_top(
        parsed,
        {
            "operation": operation,
            "num_rows": num_rows,
            "num_cols": num_cols,
            "num_words": num_rows,
            "word_size": num_cols,
            "words_per_row": 1,
            "mux_ratio": 1,
            "choose_columnmux": choose_columnmux,
            "sram_cell_type": "6T",
        },
        source_trace,
    )
    graph = build_clean_graph(
        clean_text=payload["clean_netlist_text"],
        top_module_name=TOP_MODULE_NAME,
        top_pin_roles=payload["pin_roles"],
        parameters=payload["parameters"],
        openyield_root=openyield_root,
        source_trace=source_trace,
    )
    return {
        "operation": operation,
        "clean_netlist_text": payload["clean_netlist_text"],
        "graph": graph,
        "top_pin_names": [item["name"] for item in payload["pin_roles"]],
    }


def extract_time_hierarchy(
    *,
    openyield_root: Path,
    reference_graph: dict[str, Any],
    operation_graphs: dict[str, dict[str, Any]],
    num_rows: int,
    num_cols: int,
) -> dict[str, Any]:
    module_sources, _warnings = parse_openyield_pyspice_sources(openyield_root)
    source_by_module = {item.original_module_name: item for item in module_sources}
    graph = reference_graph
    instances_by_parent: dict[str, list[dict[str, Any]]] = defaultdict(list)
    module_pin_map = {item["module_name"]: item["pins"] for item in graph["modules"]}
    module_trace_map = {item["module_name"]: item["source_trace"] for item in graph["modules"]}
    for row in graph["instances"]:
        instances_by_parent[row["parent_module"]].append(row)

    closure: set[str] = set()
    queue = ["TIME"]
    while queue:
        name = queue.pop(0)
        if name in closure:
            continue
        closure.add(name)
        for child in instances_by_parent.get(name, []):
            if child["module_name"] not in closure:
                queue.append(child["module_name"])

    consumer_modules: dict[str, set[str]] = defaultdict(set)
    child_modules: dict[str, set[str]] = defaultdict(set)
    module_instance_counts: Counter[str] = Counter()
    parent_modules: dict[str, set[str]] = defaultdict(set)
    for row in graph["instances"]:
        if row["parent_module"] in closure:
            child_modules[row["parent_module"]].add(row["module_name"])
        if row["module_name"] in closure:
            module_instance_counts[row["module_name"]] += 1
            parent_modules[row["module_name"]].add(row["parent_module"])
            consumer_modules[row["module_name"]].add(row["parent_module"])

    rows: list[dict[str, Any]] = []
    primitive_names: set[str] = set()
    total_instance_count = 0
    for module_name in sorted(closure):
        source_item = source_by_module.get(module_name)
        trace = module_trace_map.get(module_name, {})
        source_file = source_item.source_file if source_item else str(trace.get("source_file", ""))
        source_class = source_item.class_name if source_item else str(trace.get("source_class", ""))
        if _is_primitive(module_name, source_class):
            primitive_names.add(module_name)
        count = int(module_instance_counts.get(module_name, 0))
        total_instance_count += count
        pins = list(module_pin_map.get(module_name, []))
        rows.append(
            {
                "module_name": module_name,
                "source_file": source_file,
                "source_class": source_class or module_name,
                "parent_module": "|".join(sorted(parent_modules.get(module_name, []))),
                "pin_order": "|".join(pins),
                "pin_roles": "|".join(_infer_pin_roles(pins)),
                "instance_count": count,
                "instance_count_formula": _instance_formula(module_name),
                "parameter_dependencies": _parameter_dependencies(module_name),
                "operation_dependencies": _operation_dependencies(module_name),
                "row_dependencies": _row_dependencies(module_name),
                "column_dependencies": _column_dependencies(module_name),
                "drive_scale_dependencies": _drive_scale_dependencies(module_name),
                "child_modules": "|".join(sorted(child_modules.get(module_name, []))),
                "consumer_modules": "|".join(sorted(consumer_modules.get(module_name, []))),
                "control_signals_generated": "|".join(_control_signals_generated(pins)),
            }
        )
    return {
        "rows": rows,
        "module_count": len(rows),
        "primitive_count": len(primitive_names),
        "instance_count_for_reference_config": total_instance_count,
        "closure_modules": sorted(closure),
    }


def extract_source_modules_from_time_file(time_file: Path) -> set[str]:
    text = time_file.read_text(encoding="utf-8")
    tree = ast.parse(text)
    return {node.name for node in tree.body if isinstance(node, ast.ClassDef)}


def _is_primitive(module_name: str, source_class: str) -> bool:
    token = (source_class or module_name).lower()
    return token in {
        "transmissiongate",
        "pinv",
        "pnand2",
        "pnand3",
        "and2",
        "and3",
        "dff",
    } or module_name.startswith("PINV")


def _infer_pin_roles(pins: list[str]) -> list[str]:
    roles: list[str] = []
    for pin in pins:
        lower = pin.lower()
        if lower == "vdd":
            roles.append("power")
        elif lower in {"vss", "gnd", "0"}:
            roles.append("ground")
        elif lower == "clk":
            roles.append("clock")
        elif lower in {"csb", "cs", "web", "we", "we_bar", "cs_bar", "gated_clk_bar", "gated_clk_buf", "wl_en", "pre", "s_en", "w_en"}:
            roles.append("control")
        elif lower.startswith("a"):
            roles.append("address_or_address_reg")
        elif lower.startswith("din"):
            roles.append("data_or_data_reg")
        elif lower.startswith("rbl"):
            roles.append("replica_delay")
        else:
            roles.append("signal")
    return roles


def _control_signals_generated(pins: list[str]) -> list[str]:
    outputs: list[str] = []
    for pin in pins:
        lower = pin.lower()
        if any(lower.startswith(token) for token in CONTROL_OUTPUT_HINTS):
            outputs.append(pin)
    return outputs


def _instance_formula(module_name: str) -> str:
    formulas = {
        "TIME": "1",
        "ADDR_DFF": "1",
        "DATA_DFF": "1 if operation in {write, read&write} else 0",
        "DFF_BUF": "2 in TIME for cs/web register capture",
        "DFF": "ceil(log2(num_rows)) + (num_cols if operation in {write, read&write} else 0) + 1 template in each DFF_BUF",
        "TRANSMISSION_GATE": "4 per DFF template",
        "delay_chain": "1",
        "wen_delay_chain": "1 only if operation=write and num_rows=16 and num_cols=512",
        "pdrive": "1 with clk_dff_count/ref_dff_count drive scaling",
        "pdrive2_for_pre": "1 with pre_drive_scale derived from rows and cols",
        "wl_pdrive": "1",
        "AND2": "2 in TIME for gated clocks plus decoder-side uses outside TIME closure",
        "AND3": "2 in TIME for w_en and s_en",
        "PNAND2": "per AND2 decomposition or latch/driver decomposition",
        "PNAND3": "per AND3 decomposition plus PRE_UNBUF in TIME",
        "PINV": "operation- and topology-dependent support inverter count",
    }
    return formulas.get(module_name, "source-traced per generated subcircuit graph")


def _parameter_dependencies(module_name: str) -> str:
    deps = {
        "TIME": "num_rows,num_cols,operation,w_rc,length,nmos_model,pmos_model",
        "ADDR_DFF": "num_rows,length,nmos_model,pmos_model",
        "DATA_DFF": "num_cols,operation,length,nmos_model,pmos_model",
        "DFF": "length,nmos_model,pmos_model",
        "DFF_BUF": "length,nmos_model,pmos_model",
        "delay_chain": "length,nmos_model,pmos_model",
        "wen_delay_chain": "stages,loads_per_stage,length,nmos_model,pmos_model,operation,num_rows,num_cols",
        "pdrive": "drive_scale,length,nmos_model,pmos_model",
        "pdrive2_for_pre": "drive_scale,length,nmos_model,pmos_model",
        "wl_pdrive": "length,nmos_model,pmos_model",
        "AND2": "nand_pmos_width,nand_nmos_width,inv_pmos_width,inv_nmos_width,length,w_rc",
        "AND3": "nand_pmos_width,nand_nmos_width,inv_pmos_width,inv_nmos_width,length,w_rc",
        "Pinv": "nmos_width,pmos_width,length",
        "PNAND2": "nmos_width,pmos_width,length",
        "PNAND3": "nmos_width,pmos_width,length",
    }
    return deps.get(module_name, "source-traced")


def _operation_dependencies(module_name: str) -> str:
    if module_name == "DATA_DFF":
        return "present only in write/read&write"
    if module_name == "wen_delay_chain":
        return "present only in write with 16x512 special case"
    if module_name == "TIME":
        return "pin set expands in write/read&write via DIN/DIN_dff"
    if module_name in {"AND3", "pdrive"}:
        return "sizing depends on write-capable data path width"
    return "none for current V1 unless parent TIME enables write data path"


def _row_dependencies(module_name: str) -> str:
    if module_name in {"TIME", "ADDR_DFF", "pdrive2_for_pre"}:
        return "depends on num_rows or address_width=ceil(log2(num_rows))"
    if module_name == "wen_delay_chain":
        return "gated by num_rows==16 special case"
    return "none or indirect via parent topology"


def _column_dependencies(module_name: str) -> str:
    if module_name in {"TIME", "DATA_DFF", "AND3", "pdrive", "pdrive2_for_pre"}:
        return "depends on num_cols or derived scaling"
    if module_name == "wen_delay_chain":
        return "gated by num_cols==512 special case"
    return "none or indirect via parent topology"


def _drive_scale_dependencies(module_name: str) -> str:
    if module_name == "pdrive":
        return "clk_drive_scale=max(1, clk_dff_count/ref_dff_count)"
    if module_name == "pdrive2_for_pre":
        return "pre_drive_scale=max(1, ceil(((num_cols+1)/65)*max(0.5,num_rows/16)))"
    if module_name == "AND3":
        return "w_en_scale=max(1, ceil(num_cols/64))"
    return "none"
