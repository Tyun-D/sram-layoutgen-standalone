from __future__ import annotations

import csv
from pathlib import Path
from typing import Any


FIELDS = [
    "logical_module",
    "source_class",
    "source_file",
    "source_parameters",
    "nmos_width",
    "pmos_width",
    "length",
    "drive_scale",
    "stage_count",
    "loads_per_stage",
    "pin_order",
    "power_pins",
    "input_pins",
    "output_pins",
    "expected_child_modules",
    "expected_child_count",
    "parameter_dependencies",
    "required_generator_level",
    "candidate_existing_generator",
    "candidate_existing_generator_path",
    "adapter_required",
    "fixed_or_parameterized",
    "must_generate_distinct_variant",
    "expected_physical_cell_name",
    "expected_cell_height_policy",
    "expected_rail_policy",
    "expected_pin_access_policy",
    "expected_orientation_policy",
    "generation_priority",
    "blocking_dependencies",
]


def _read_hierarchy(path: Path) -> dict[str, dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        return {row["module_name"]: row for row in csv.DictReader(handle)}


def build_primitive_requirement_matrix(
    hierarchy_csv: Path,
) -> dict[str, Any]:
    hierarchy = _read_hierarchy(hierarchy_csv)
    rows = [
        _row("NMOS_DEVICE", "NMOS_VTG", "", "model width|length", "0.09e-6+", "", "0.05e-6", "", "", "", "D|G|S|B", "B", "D|G|S", "", "", "", "transistor_width|length", "DEVICE", "OpenRAM ptx", "/data1/qujh/OpenRAM/compiler/modules/ptx.py", True, "PARAMETERIZED", True, "NMOS_NW{nmos}_L{length}", "device-only", "none", "device pins only", "flexible", "P0_REQUIRED_FIRST", "LOCKED_FREEPDK45_V1"),
        _row("PMOS_DEVICE", "PMOS_VTG", "", "model width|length", "", "0.09e-6+", "0.05e-6", "", "", "", "D|G|S|B", "B", "D|G|S", "", "", "", "transistor_width|length", "DEVICE", "OpenRAM ptx", "/data1/qujh/OpenRAM/compiler/modules/ptx.py", True, "PARAMETERIZED", True, "PMOS_PW{pmos}_L{length}", "device-only", "none", "device pins only", "flexible", "P0_REQUIRED_FIRST", "LOCKED_FREEPDK45_V1"),
        _row("CONTACT", "contact", "", "stack|dimensions", "", "", "", "", "", "", "lower|upper", "", "lower", "upper", "", "", "contact array dimensions", "DEVICE", "OpenRAM contact", "/data1/qujh/OpenRAM/compiler/base/contact.py", True, "PARAMETERIZED", True, "CONTACT_{stack}_{dims}", "primitive-contact", "none", "stack-specific", "flexible", "P0_REQUIRED_FIRST", "LOCKED_FREEPDK45_V1"),
        _row("VIA1", "contact", "", "stack|dimensions", "", "", "", "", "", "", "m1|m2", "", "m1", "m2", "", "", "via dimensions", "DEVICE", "OpenRAM contact", "/data1/qujh/OpenRAM/compiler/base/contact.py", True, "PARAMETERIZED", True, "VIA1_{dims}", "primitive-contact", "none", "stack-specific", "flexible", "P0_REQUIRED_FIRST", "LOCKED_FREEPDK45_V1"),
        _row("POWER_TAP", "contact", "", "tap type|dimensions", "", "", "", "", "", "", "VDD|VSS", "VDD|VSS", "", "", "CONTACT", "contact array", "tap type", "DEVICE", "OpenRAM contact", "/data1/qujh/OpenRAM/compiler/base/contact.py", True, "PARAMETERIZED", True, "POWER_TAP_{well}_{dims}", "row-compatible", "abuttable rails", "rail aligned", "fixed rail orientation", "P0_REQUIRED_FIRST", "LOCKED_FREEPDK45_V1"),
        _from_hierarchy("PINV", hierarchy, "PRIMITIVE_GATE", "OpenRAM pinv", "/data1/qujh/OpenRAM/compiler/modules/pinv.py", "P0_REQUIRED_FIRST", "OpenRAM adapter plus naming contract", "0.09e-6", "0.27e-6", "0.05e-6", "1", "", "", True, True),
        _from_hierarchy("PINV1", hierarchy, "PRIMITIVE_GATE", "OpenRAM pinv", "/data1/qujh/OpenRAM/compiler/modules/pinv.py", "P0_REQUIRED_FIRST", "Distinct size variant", "0.25e-6", "0.50e-6", "0.05e-6", "fixed", "", "", True, True),
        _from_hierarchy("PINV2", hierarchy, "PRIMITIVE_GATE", "OpenRAM pinv", "/data1/qujh/OpenRAM/compiler/modules/pinv.py", "P0_REQUIRED_FIRST", "Distinct size variant", "0.27e-6", "0.81e-6", "0.05e-6", "parameterized", "", "", True, True),
        _from_hierarchy("PINV3", hierarchy, "PRIMITIVE_GATE", "OpenRAM pinv", "/data1/qujh/OpenRAM/compiler/modules/pinv.py", "P0_REQUIRED_FIRST", "Distinct size variant", "0.91e-6", "2.43e-6", "0.05e-6", "parameterized", "", "", True, True),
        _from_hierarchy("PINV4", hierarchy, "PRIMITIVE_GATE", "OpenRAM pinv", "/data1/qujh/OpenRAM/compiler/modules/pinv.py", "P0_REQUIRED_FIRST", "Distinct size variant", "2.43e-6", "7.29e-6", "0.05e-6", "parameterized", "", "", True, True),
        _from_hierarchy("PINV_wl_en_bar", hierarchy, "PRIMITIVE_GATE", "OpenRAM pinv", "/data1/qujh/OpenRAM/compiler/modules/pinv.py", "P0_REQUIRED_FIRST", "Separate traceable alias", "0.09e-6", "0.27e-6", "0.05e-6", "1", "", "", True, False),
        _from_hierarchy("PNAND2", hierarchy, "PRIMITIVE_GATE", "No trusted parameterized NAND generator in current repo", "", "P0_REQUIRED_FIRST", "Need adapter or new implementation", "0.18e-6", "0.27e-6", "0.05e-6", "fixed", "", "", True, True),
        _from_hierarchy("PNAND3", hierarchy, "PRIMITIVE_GATE", "No trusted parameterized NAND generator in current repo", "", "P0_REQUIRED_FIRST", "Need adapter or new implementation", "0.27e-6", "0.27e-6", "0.05e-6", "fixed", "", "", True, True),
        _from_hierarchy("TRANSMISSION_GATE", hierarchy, "PRIMITIVE_GATE", "OpenRAM ptx pair + contact composition", "/data1/qujh/OpenRAM/compiler/modules/ptx.py", "P0_REQUIRED_FIRST", "Compose NMOS+PMOS with shared control pins", "0.25e-6", "0.50e-6", "0.05e-6", "fixed", "", "", True, True),
        _from_hierarchy("AND2", hierarchy, "PRIMITIVE_GATE", "Composite from PNAND2+PINV", "", "P1_REQUIRED_FOR_DFF", "Composite after NAND/INV lock", "", "", "0.05e-6", "", "", "", True, False),
        _from_hierarchy("AND3", hierarchy, "PRIMITIVE_GATE", "Composite from PNAND3+PINV", "", "P1_REQUIRED_FOR_DFF", "Composite after NAND/INV lock", "", "", "0.05e-6", "", "", "", True, False),
        _from_hierarchy("DFF", hierarchy, "SEQUENTIAL_CELL", "Reference-only today", "", "P1_REQUIRED_FOR_DFF", "Requires transistor-level contract beyond wrapper", "", "", "0.05e-6", "", "", "", True, True),
        _from_hierarchy("DFF_BUF", hierarchy, "SEQUENTIAL_CELL", "Composite from DFF+PINV1+PINV2", "", "P1_REQUIRED_FOR_DFF", "Requires DFF and inverter variants", "", "", "0.05e-6", "", "", "", True, True),
        _from_hierarchy("ADDR_DFF", hierarchy, "SEQUENTIAL_CELL", "Composite from DFF rows", "", "P2_REQUIRED_FOR_CONTROL_PATH", "Depends on DFF implementation", "", "", "0.05e-6", "", "", "", True, False),
        _from_hierarchy("DATA_DFF", hierarchy, "SEQUENTIAL_CELL", "Composite from DFF rows", "", "P2_REQUIRED_FOR_CONTROL_PATH", "Depends on DFF implementation and operation topology", "", "", "0.05e-6", "", "", "", True, True),
        _from_hierarchy("pdrive", hierarchy, "BUFFER_CHAIN", "Composite from PINV1-4", "", "P2_REQUIRED_FOR_CONTROL_PATH", "Needs four locked inverter variants", "0.25e-6", "0.50e-6", "0.05e-6", "parameterized", "4", "", True, True),
        _from_hierarchy("pdrive2_for_pre", hierarchy, "BUFFER_CHAIN", "Composite from PINV1-2", "", "P2_REQUIRED_FOR_CONTROL_PATH", "Needs drive-scale-aware variants", "0.25e-6", "0.50e-6", "0.05e-6", "parameterized", "2", "", True, True),
        _from_hierarchy("wl_pdrive", hierarchy, "BUFFER_CHAIN", "Composite from PINV1-2", "", "P2_REQUIRED_FOR_CONTROL_PATH", "Needs drive-scale-aware variants", "0.25e-6", "0.50e-6", "0.05e-6", "fixed", "2", "", True, False),
        _from_hierarchy("delay_chain", hierarchy, "DELAY_CHAIN", "Fixed candidate exists but generator plan missing", "", "P2_REQUIRED_FOR_CONTROL_PATH", "Need scalable delay chain after PINV lock", "0.25e-6", "0.50e-6", "0.05e-6", "fixed", "", "", True, True),
        _row("WenDelayChain", "WenDelayChain", "sram_compiler/subcircuits/time_generate.py", "length|delay_chain_stages|loads_per_stage", "0.25e-6", "0.50e-6", "0.05e-6", "", "variable", "variable", "VDD|VSS|in|out", "VDD|VSS", "in", "out", "PINV1", "variable", "delay_chain_stages|loads_per_stage|operation", "DELAY_CHAIN", "No trusted generator yet", "", True, "PARAMETERIZED", True, "WEN_DELAY_CHAIN_ST{stage_count}", "row-compatible", "abuttable rails", "edge-access pins", "fixed row orientation", "P2_REQUIRED_FOR_CONTROL_PATH", "delay_chain_stage_contract"),
    ]
    return {
        "rows": rows,
        "fields": FIELDS,
        "primitive_requirement_matrix_generated": True,
        "primitive_requirement_count": len(rows),
        "p0_primitive_count": len([row for row in rows if row["generation_priority"] == "P0_REQUIRED_FIRST"]),
        "p1_primitive_count": len([row for row in rows if row["generation_priority"] == "P1_REQUIRED_FOR_DFF"]),
        "p2_primitive_count": len([row for row in rows if row["generation_priority"] == "P2_REQUIRED_FOR_CONTROL_PATH"]),
    }


def _row(
    logical_module: str,
    source_class: str,
    source_file: str,
    source_parameters: str,
    nmos_width: str,
    pmos_width: str,
    length: str,
    drive_scale: str,
    stage_count: str,
    loads_per_stage: str,
    pin_order: str,
    power_pins: str,
    input_pins: str,
    output_pins: str,
    expected_child_modules: str,
    expected_child_count: str,
    parameter_dependencies: str,
    required_generator_level: str,
    candidate_existing_generator: str,
    candidate_existing_generator_path: str,
    adapter_required: bool,
    fixed_or_parameterized: str,
    must_generate_distinct_variant: bool,
    expected_physical_cell_name: str,
    expected_cell_height_policy: str,
    expected_rail_policy: str,
    expected_pin_access_policy: str,
    expected_orientation_policy: str,
    generation_priority: str,
    blocking_dependencies: str,
) -> dict[str, Any]:
    return {
        "logical_module": logical_module,
        "source_class": source_class,
        "source_file": source_file,
        "source_parameters": source_parameters,
        "nmos_width": nmos_width,
        "pmos_width": pmos_width,
        "length": length,
        "drive_scale": drive_scale,
        "stage_count": stage_count,
        "loads_per_stage": loads_per_stage,
        "pin_order": pin_order,
        "power_pins": power_pins,
        "input_pins": input_pins,
        "output_pins": output_pins,
        "expected_child_modules": expected_child_modules,
        "expected_child_count": expected_child_count,
        "parameter_dependencies": parameter_dependencies,
        "required_generator_level": required_generator_level,
        "candidate_existing_generator": candidate_existing_generator,
        "candidate_existing_generator_path": candidate_existing_generator_path,
        "adapter_required": adapter_required,
        "fixed_or_parameterized": fixed_or_parameterized,
        "must_generate_distinct_variant": must_generate_distinct_variant,
        "expected_physical_cell_name": expected_physical_cell_name,
        "expected_cell_height_policy": expected_cell_height_policy,
        "expected_rail_policy": expected_rail_policy,
        "expected_pin_access_policy": expected_pin_access_policy,
        "expected_orientation_policy": expected_orientation_policy,
        "generation_priority": generation_priority,
        "blocking_dependencies": blocking_dependencies,
    }


def _from_hierarchy(
    module_name: str,
    hierarchy: dict[str, dict[str, str]],
    required_level: str,
    generator: str,
    generator_path: str,
    priority: str,
    blocking: str,
    nmos_width: str,
    pmos_width: str,
    length: str,
    drive_scale: str,
    stage_count: str,
    loads_per_stage: str,
    adapter_required: bool,
    distinct: bool,
) -> dict[str, Any]:
    row = hierarchy.get(module_name, {})
    pin_order = row.get("pin_order", "")
    pin_names = pin_order.split("|") if pin_order else []
    power_pins = "|".join([name for name in pin_names if name.upper() in {"VDD", "VSS", "GND"}])
    input_pins = "|".join([name for name in pin_names if name not in power_pins.split("|") and name not in {"Z", "Q", "QB", "out", "OUT", "PRE", "w_en", "s_en"}])
    output_pins = "|".join([name for name in pin_names if name not in power_pins.split("|") and name not in input_pins.split("|")])
    return _row(
        module_name,
        row.get("source_class", module_name),
        row.get("source_file", ""),
        row.get("parameter_dependencies", ""),
        nmos_width,
        pmos_width,
        length,
        drive_scale,
        stage_count,
        loads_per_stage,
        pin_order,
        power_pins,
        input_pins,
        output_pins,
        row.get("child_modules", ""),
        row.get("instance_count_formula", ""),
        row.get("parameter_dependencies", ""),
        required_level,
        generator,
        generator_path,
        adapter_required,
        "PARAMETERIZED" if "parameterized" in drive_scale.lower() or distinct or module_name in {"TRANSMISSION_GATE", "PINV1", "PINV2", "PINV3", "PINV4"} else "FIXED_OR_ADAPTED",
        distinct,
        module_name.upper(),
        "row-compatible",
        "M1 rails",
        "edge-access pins",
        "fixed row orientation",
        priority,
        blocking,
    )
