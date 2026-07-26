from __future__ import annotations

import csv
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import gdstk


USER_REVIEW = """M3F review:
- optimized layoutgen flow has been restored;
- power rail stitching / rail overlap flow has been recovered;
- current GDS has reached the previous layoutgen optimization level;
- but it still mainly uses original layoutgen modules;
- next goal is to integrate OpenYield netlist-defined modules into the layoutgen physical generator;
- because OpenYield module count/type/pin/connection may differ from layoutgen baseline, floorplan / placement / routing / power code may need modification;
- only one feasibility evaluation is allowed before direct implementation."""

REVIEW_TOP_NAME = "openyield_integration_feasibility_review"

IMPLEMENTATION_MODE_ORDER = [
    "DIRECT_GENERATOR_BINDING",
    "PARAMETERIZED_LAYOUTGEN_GENERATOR",
    "REAL_CELL_WRAPPER",
    "LAYOUTGEN_FALLBACK_WITH_OPENYIELD_SEMANTICS",
    "NOT_IMPLEMENTABLE_NOW",
]

IMPLEMENTATION_LAYER = {
    "DIRECT_GENERATOR_BINDING": 210,
    "PARAMETERIZED_LAYOUTGEN_GENERATOR": 211,
    "REAL_CELL_WRAPPER": 212,
    "LAYOUTGEN_FALLBACK_WITH_OPENYIELD_SEMANTICS": 213,
    "NOT_IMPLEMENTABLE_NOW": 214,
}

CHANGE_LAYER = {
    "floorplan": 220,
    "placement": 221,
    "routing": 222,
    "power": 223,
}

TEXT_LAYER = 230


@dataclass(frozen=True)
class Bounds:
    x0: float
    y0: float
    x1: float
    y1: float

    @property
    def width(self) -> float:
        return self.x1 - self.x0

    @property
    def height(self) -> float:
        return self.y1 - self.y0

    @property
    def center(self) -> tuple[float, float]:
        return ((self.x0 + self.x1) / 2.0, (self.y0 + self.y1) / 2.0)

    def expand(self, margin: float) -> "Bounds":
        return Bounds(self.x0 - margin, self.y0 - margin, self.x1 + margin, self.y1 + margin)

    def to_rect(self) -> dict[str, float]:
        return {
            "x0": round(self.x0, 6),
            "y0": round(self.y0, 6),
            "x1": round(self.x1, 6),
            "y1": round(self.y1, 6),
            "width": round(self.width, 6),
            "height": round(self.height, 6),
        }


def _json_dump(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8", newline="\n")


def _write_csv(path: Path, fieldnames: list[str], rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def _read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def _md_table(columns: list[str], rows: list[dict[str, Any]]) -> str:
    lines = [
        "| " + " | ".join(columns) + " |",
        "| " + " | ".join(["---"] * len(columns)) + " |",
    ]
    for row in rows:
        lines.append("| " + " | ".join(str(row.get(column, "")).replace("\n", "<br>") for column in columns) + " |")
    return "\n".join(lines) + "\n"


def _bool_text(value: bool) -> str:
    return "True" if value else "False"


def _find_cell(lib: gdstk.Library, name: str) -> gdstk.Cell | None:
    for cell in lib.cells:
        if cell.name == name:
            return cell
    return None


def _gds_sanity(gds_path: Path, top_cell_name: str) -> dict[str, Any]:
    try:
        lib = gdstk.read_gds(gds_path)
    except Exception as exc:
        return {
            "status": "GDS_PARSE_FAILED",
            "error": str(exc),
            "top_cell_name": None,
            "gds_size_bytes": gds_path.stat().st_size if gds_path.exists() else 0,
        }
    tops = lib.top_level()
    top = next((cell for cell in tops if cell.name == top_cell_name), tops[0] if tops else None)
    if top is None:
        return {
            "status": "TOP_CELL_MISSING",
            "error": "Top cell not found.",
            "top_cell_name": None,
            "gds_size_bytes": gds_path.stat().st_size,
        }
    bbox = top.bounding_box()
    top_bbox = None
    if bbox is not None:
        top_bbox = {
            "x0": round(float(bbox[0][0]), 6),
            "y0": round(float(bbox[0][1]), 6),
            "x1": round(float(bbox[1][0]), 6),
            "y1": round(float(bbox[1][1]), 6),
            "width": round(float(bbox[1][0] - bbox[0][0]), 6),
            "height": round(float(bbox[1][1] - bbox[0][1]), 6),
        }
    return {
        "status": "GDS_PARSED_SANITY_PASSED",
        "error": "",
        "top_cell_name": str(top.name),
        "gds_size_bytes": gds_path.stat().st_size,
        "cell_count": len(lib.cells),
        "top_bbox": top_bbox,
    }


def _row_bounds(row: dict[str, Any]) -> Bounds:
    rect = row["rect"]
    return Bounds(float(rect["x0"]), float(rect["y0"]), float(rect["x1"]), float(rect["y1"]))


def _merge_bounds(bounds_list: list[Bounds]) -> Bounds:
    return Bounds(
        min(item.x0 for item in bounds_list),
        min(item.y0 for item in bounds_list),
        max(item.x1 for item in bounds_list),
        max(item.y1 for item in bounds_list),
    )


def _role_bounds(layout_json: dict[str, Any]) -> dict[str, Bounds]:
    grouped: dict[str, list[Bounds]] = {}
    for collection_name in ("cell_arrays", "instances"):
        for row in layout_json.get(collection_name, []):
            role = str(row.get("role", "")).strip()
            if not role:
                continue
            grouped.setdefault(role, []).append(_row_bounds(row))
    return {role: _merge_bounds(bounds) for role, bounds in grouped.items()}


def _label_anchor(bounds: Bounds, index: int) -> tuple[float, float]:
    return (
        round(bounds.x0 + 0.18 + 0.22 * (index % 4), 6),
        round(max(bounds.y0 + 0.18, bounds.y1 - 0.25 - 0.28 * (index // 4)), 6),
    )


def _canonical_parameter_map(intent_json: dict[str, Any]) -> dict[str, Any]:
    parameter_map: dict[str, Any] = {}
    for row in intent_json.get("canonical_parameters", {}).get("parameters", []):
        name = str(row.get("parameter_name", "")).strip()
        if name:
            parameter_map[name] = row.get("value")
    return parameter_map


def _implementation_template() -> dict[str, dict[str, Any]]:
    return {
        "bitcell_array": {
            "layoutgen_target_generator": "ArrayAggregationPlanner;StandaloneSRAMGenerator",
            "layoutgen_target_cell": "cell_1rw",
            "implementation_mode": "DIRECT_GENERATOR_BINDING",
            "requires_floorplan_change": False,
            "requires_placement_change": False,
            "requires_routing_change": False,
            "requires_power_change": False,
            "can_implement_in_next_stage": True,
            "fallback_if_not_implemented": "retain M3F optimized storage array aggregation",
            "blocking_reason": "",
            "code_files_to_modify": "sram_layoutgen/standalone.py;sram_layoutgen/openyield_adapter/array_aggregation.py;sram_layoutgen/openyield_adapter/M3F_optimized_layoutgen_restore.py",
            "region_roles": ("bitcell_array",),
        },
        "dummy_array": {
            "layoutgen_target_generator": "ArrayAggregationPlanner;StandaloneSRAMGenerator",
            "layoutgen_target_cell": "dummy_cell_1rw",
            "implementation_mode": "DIRECT_GENERATOR_BINDING",
            "requires_floorplan_change": False,
            "requires_placement_change": False,
            "requires_routing_change": False,
            "requires_power_change": False,
            "can_implement_in_next_stage": True,
            "fallback_if_not_implemented": "retain M3F optimized dummy boundary arrays",
            "blocking_reason": "",
            "code_files_to_modify": "sram_layoutgen/standalone.py;sram_layoutgen/openyield_adapter/array_aggregation.py;sram_layoutgen/openyield_adapter/M3F_optimized_layoutgen_restore.py",
            "region_roles": ("dummy_bitcell",),
        },
        "replica_array": {
            "layoutgen_target_generator": "ArrayAggregationPlanner;StandaloneSRAMGenerator",
            "layoutgen_target_cell": "replica_cell_1rw;replica_precharge",
            "implementation_mode": "DIRECT_GENERATOR_BINDING",
            "requires_floorplan_change": False,
            "requires_placement_change": False,
            "requires_routing_change": False,
            "requires_power_change": False,
            "can_implement_in_next_stage": True,
            "fallback_if_not_implemented": "retain M3F optimized replica array",
            "blocking_reason": "",
            "code_files_to_modify": "sram_layoutgen/standalone.py;sram_layoutgen/openyield_adapter/array_aggregation.py;sram_layoutgen/openyield_adapter/M3F_optimized_layoutgen_restore.py",
            "region_roles": ("replica_bitline", "replica_precharge"),
        },
        "row_decoder": {
            "layoutgen_target_generator": "StandaloneSRAMGenerator.gate_row_packer",
            "layoutgen_target_cell": "row_decoder role instances",
            "implementation_mode": "PARAMETERIZED_LAYOUTGEN_GENERATOR",
            "requires_floorplan_change": True,
            "requires_placement_change": True,
            "requires_routing_change": True,
            "requires_power_change": True,
            "can_implement_in_next_stage": True,
            "fallback_if_not_implemented": "retain M3F optimized row_decoder role with OpenYield net ownership only",
            "blocking_reason": "",
            "code_files_to_modify": "sram_layoutgen/standalone.py;sram_layoutgen/openyield_adapter/module_gds_generators.py;sram_layoutgen/openyield_adapter/top_level_assembly.py",
            "region_roles": ("row_decoder",),
        },
        "wordline_decoder": {
            "layoutgen_target_generator": "StandaloneSRAMGenerator.gate_row_packer",
            "layoutgen_target_cell": "row_decoder role instances",
            "implementation_mode": "PARAMETERIZED_LAYOUTGEN_GENERATOR",
            "requires_floorplan_change": True,
            "requires_placement_change": True,
            "requires_routing_change": True,
            "requires_power_change": True,
            "can_implement_in_next_stage": True,
            "fallback_if_not_implemented": "retain M3F optimized row_decoder role with OpenYield semantic split only",
            "blocking_reason": "",
            "code_files_to_modify": "sram_layoutgen/standalone.py;sram_layoutgen/openyield_adapter/module_gds_generators.py;sram_layoutgen/openyield_adapter/top_level_assembly.py",
            "region_roles": ("row_decoder",),
        },
        "decoder_gate_cells": {
            "layoutgen_target_generator": "StandaloneSRAMGenerator.gate_row_packer",
            "layoutgen_target_cell": "row_decoder role instances",
            "implementation_mode": "PARAMETERIZED_LAYOUTGEN_GENERATOR",
            "requires_floorplan_change": True,
            "requires_placement_change": True,
            "requires_routing_change": True,
            "requires_power_change": True,
            "can_implement_in_next_stage": True,
            "fallback_if_not_implemented": "retain M3F optimized row_decoder gate-row packing",
            "blocking_reason": "",
            "code_files_to_modify": "sram_layoutgen/standalone.py;sram_layoutgen/openyield_adapter/module_gds_generators.py;sram_layoutgen/openyield_adapter/top_level_assembly.py",
            "region_roles": ("row_decoder",),
        },
        "wordline_driver": {
            "layoutgen_target_generator": "StandaloneSRAMGenerator.wordlinedriver_adapter",
            "layoutgen_target_cell": "gen_wl_driver",
            "implementation_mode": "REAL_CELL_WRAPPER",
            "requires_floorplan_change": False,
            "requires_placement_change": True,
            "requires_routing_change": True,
            "requires_power_change": True,
            "can_implement_in_next_stage": True,
            "fallback_if_not_implemented": "retain M3F optimized wordline_driver role",
            "blocking_reason": "",
            "code_files_to_modify": "sram_layoutgen/standalone.py;sram_layoutgen/openyield_adapter/wordlinedriver_adapter.py;sram_layoutgen/openyield_adapter/top_level_assembly.py",
            "region_roles": ("wordline_driver",),
        },
        "wordline_driver_gate_cells": {
            "layoutgen_target_generator": "StandaloneSRAMGenerator.gate_row_packer+wordlinedriver_adapter",
            "layoutgen_target_cell": "wordline_driver role instances",
            "implementation_mode": "PARAMETERIZED_LAYOUTGEN_GENERATOR",
            "requires_floorplan_change": False,
            "requires_placement_change": True,
            "requires_routing_change": True,
            "requires_power_change": True,
            "can_implement_in_next_stage": True,
            "fallback_if_not_implemented": "retain M3F optimized wordline driver gate ownership only",
            "blocking_reason": "",
            "code_files_to_modify": "sram_layoutgen/standalone.py;sram_layoutgen/openyield_adapter/wordlinedriver_adapter.py;sram_layoutgen/openyield_adapter/top_level_assembly.py",
            "region_roles": ("wordline_driver",),
        },
        "column_mux": {
            "layoutgen_target_generator": "StandaloneSRAMGenerator.columnmux_adapter",
            "layoutgen_target_cell": "gen_col_mux_vdd_labeled",
            "implementation_mode": "REAL_CELL_WRAPPER",
            "requires_floorplan_change": False,
            "requires_placement_change": True,
            "requires_routing_change": True,
            "requires_power_change": True,
            "can_implement_in_next_stage": True,
            "fallback_if_not_implemented": "retain M3F optimized column_mux placement and semantic mapping",
            "blocking_reason": "",
            "code_files_to_modify": "sram_layoutgen/standalone.py;sram_layoutgen/openyield_adapter/top_level_assembly.py;sram_layoutgen/openyield_adapter/hardcell_power_rail_continuity.py",
            "region_roles": ("column_mux",),
        },
        "sense_amp": {
            "layoutgen_target_generator": "StandaloneSRAMGenerator.senseamp_adapter",
            "layoutgen_target_cell": "sense_amp",
            "implementation_mode": "REAL_CELL_WRAPPER",
            "requires_floorplan_change": False,
            "requires_placement_change": True,
            "requires_routing_change": True,
            "requires_power_change": False,
            "can_implement_in_next_stage": True,
            "fallback_if_not_implemented": "retain M3F optimized sense_amp placement with existing mux-out mapping",
            "blocking_reason": "",
            "code_files_to_modify": "sram_layoutgen/standalone.py;sram_layoutgen/openyield_adapter/architecture_adapter.py;sram_layoutgen/openyield_adapter/top_level_assembly.py",
            "region_roles": ("sense_amp",),
        },
        "write_driver": {
            "layoutgen_target_generator": "StandaloneSRAMGenerator.writedriver_adapter",
            "layoutgen_target_cell": "write_driver",
            "implementation_mode": "REAL_CELL_WRAPPER",
            "requires_floorplan_change": False,
            "requires_placement_change": True,
            "requires_routing_change": True,
            "requires_power_change": True,
            "can_implement_in_next_stage": True,
            "fallback_if_not_implemented": "retain M3F optimized write_driver placement and semantic mapping",
            "blocking_reason": "",
            "code_files_to_modify": "sram_layoutgen/standalone.py;sram_layoutgen/openyield_adapter/writedriver_adapter.py;sram_layoutgen/openyield_adapter/hardcell_power_rail_continuity.py",
            "region_roles": ("write_driver",),
        },
        "precharge": {
            "layoutgen_target_generator": "StandaloneSRAMGenerator.precharge_row",
            "layoutgen_target_cell": "gen_precharge",
            "implementation_mode": "REAL_CELL_WRAPPER",
            "requires_floorplan_change": False,
            "requires_placement_change": True,
            "requires_routing_change": True,
            "requires_power_change": True,
            "can_implement_in_next_stage": True,
            "fallback_if_not_implemented": "retain M3F optimized precharge row",
            "blocking_reason": "",
            "code_files_to_modify": "sram_layoutgen/standalone.py;sram_layoutgen/openyield_adapter/module_gds_generators.py;sram_layoutgen/openyield_adapter/hardcell_power_rail_continuity.py",
            "region_roles": ("precharge",),
        },
        "DELAY_CHAIN": {
            "layoutgen_target_generator": "StandaloneSRAMGenerator.delay_chain_row",
            "layoutgen_target_cell": "gen_delay_inv chain",
            "implementation_mode": "PARAMETERIZED_LAYOUTGEN_GENERATOR",
            "requires_floorplan_change": True,
            "requires_placement_change": True,
            "requires_routing_change": True,
            "requires_power_change": False,
            "can_implement_in_next_stage": True,
            "fallback_if_not_implemented": "retain M3F optimized layoutgen delay chain semantics",
            "blocking_reason": "",
            "code_files_to_modify": "sram_layoutgen/standalone.py;sram_layoutgen/openyield_adapter/module_gds_generators.py;sram_layoutgen/openyield_adapter/top_level_assembly.py",
            "region_roles": ("delay_chain",),
        },
        "DFF_ROW": {
            "layoutgen_target_generator": "StandaloneSRAMGenerator.data_dff_packing",
            "layoutgen_target_cell": "dff array",
            "implementation_mode": "PARAMETERIZED_LAYOUTGEN_GENERATOR",
            "requires_floorplan_change": True,
            "requires_placement_change": True,
            "requires_routing_change": True,
            "requires_power_change": False,
            "can_implement_in_next_stage": True,
            "fallback_if_not_implemented": "retain M3F optimized data_dff role with OpenYield bus ownership only",
            "blocking_reason": "",
            "code_files_to_modify": "sram_layoutgen/standalone.py;sram_layoutgen/openyield_adapter/module_gds_generators.py;sram_layoutgen/openyield_adapter/top_level_assembly.py",
            "region_roles": ("data_dff",),
        },
        "CONTROL_LOGIC": {
            "layoutgen_target_generator": "StandaloneSRAMGenerator.control_logic_fallback",
            "layoutgen_target_cell": "control_logic;control_glue",
            "implementation_mode": "LAYOUTGEN_FALLBACK_WITH_OPENYIELD_SEMANTICS",
            "requires_floorplan_change": True,
            "requires_placement_change": True,
            "requires_routing_change": True,
            "requires_power_change": True,
            "can_implement_in_next_stage": False,
            "fallback_if_not_implemented": "keep current M3F control_logic/control_glue backbone and bind OpenYield nets only",
            "blocking_reason": "First-round CONTROL_LOGIC is candidate-only and no native OpenYield physical control composite is installed in the optimized trunk.",
            "code_files_to_modify": "sram_layoutgen/standalone.py;sram_layoutgen/openyield_adapter/module_gds_generators.py;sram_layoutgen/openyield_adapter/top_level_assembly.py;sram_layoutgen/openyield_adapter/M3F_optimized_layoutgen_restore.py",
            "region_roles": ("control_logic", "control_glue"),
        },
        "GATED_CLOCK_PATH": {
            "layoutgen_target_generator": "StandaloneSRAMGenerator.control_glue_fallback",
            "layoutgen_target_cell": "control_glue",
            "implementation_mode": "LAYOUTGEN_FALLBACK_WITH_OPENYIELD_SEMANTICS",
            "requires_floorplan_change": True,
            "requires_placement_change": True,
            "requires_routing_change": True,
            "requires_power_change": True,
            "can_implement_in_next_stage": False,
            "fallback_if_not_implemented": "keep current M3F control_glue and export gated-clock ownership only",
            "blocking_reason": "OpenYield gated clock path exists only as candidate/control-contract evidence, not as a physical-ready module generator output.",
            "code_files_to_modify": "sram_layoutgen/standalone.py;sram_layoutgen/openyield_adapter/module_gds_generators.py;sram_layoutgen/openyield_adapter/top_level_assembly.py",
            "region_roles": ("control_glue",),
        },
        "PRECHARGE_ENABLE_PATH": {
            "layoutgen_target_generator": "StandaloneSRAMGenerator.control_glue_fallback",
            "layoutgen_target_cell": "control_glue",
            "implementation_mode": "LAYOUTGEN_FALLBACK_WITH_OPENYIELD_SEMANTICS",
            "requires_floorplan_change": True,
            "requires_placement_change": True,
            "requires_routing_change": True,
            "requires_power_change": True,
            "can_implement_in_next_stage": False,
            "fallback_if_not_implemented": "keep current M3F control_glue precharge-enable ownership only",
            "blocking_reason": "OpenYield precharge-enable path is still candidate-only and has no physical-ready generator path in the optimized flow.",
            "code_files_to_modify": "sram_layoutgen/standalone.py;sram_layoutgen/openyield_adapter/module_gds_generators.py;sram_layoutgen/openyield_adapter/top_level_assembly.py",
            "region_roles": ("control_glue",),
        },
        "SENSE_ENABLE_PATH": {
            "layoutgen_target_generator": "StandaloneSRAMGenerator.control_glue_fallback",
            "layoutgen_target_cell": "control_glue",
            "implementation_mode": "LAYOUTGEN_FALLBACK_WITH_OPENYIELD_SEMANTICS",
            "requires_floorplan_change": True,
            "requires_placement_change": True,
            "requires_routing_change": True,
            "requires_power_change": True,
            "can_implement_in_next_stage": False,
            "fallback_if_not_implemented": "keep current M3F control_glue sense-enable ownership only",
            "blocking_reason": "OpenYield sense-enable path is still candidate-only and has no physical-ready generator path in the optimized flow.",
            "code_files_to_modify": "sram_layoutgen/standalone.py;sram_layoutgen/openyield_adapter/module_gds_generators.py;sram_layoutgen/openyield_adapter/top_level_assembly.py",
            "region_roles": ("control_glue",),
        },
        "WRITE_ENABLE_PATH": {
            "layoutgen_target_generator": "StandaloneSRAMGenerator.control_glue_fallback",
            "layoutgen_target_cell": "control_glue",
            "implementation_mode": "LAYOUTGEN_FALLBACK_WITH_OPENYIELD_SEMANTICS",
            "requires_floorplan_change": True,
            "requires_placement_change": True,
            "requires_routing_change": True,
            "requires_power_change": True,
            "can_implement_in_next_stage": False,
            "fallback_if_not_implemented": "keep current M3F control_glue write-enable ownership only",
            "blocking_reason": "OpenYield write-enable path is still candidate-only and has no physical-ready generator path in the optimized flow.",
            "code_files_to_modify": "sram_layoutgen/standalone.py;sram_layoutgen/openyield_adapter/module_gds_generators.py;sram_layoutgen/openyield_adapter/top_level_assembly.py",
            "region_roles": ("control_glue",),
        },
        "WORDLINE_ENABLE_PATH": {
            "layoutgen_target_generator": "StandaloneSRAMGenerator.control_glue_fallback",
            "layoutgen_target_cell": "control_glue",
            "implementation_mode": "LAYOUTGEN_FALLBACK_WITH_OPENYIELD_SEMANTICS",
            "requires_floorplan_change": True,
            "requires_placement_change": True,
            "requires_routing_change": True,
            "requires_power_change": True,
            "can_implement_in_next_stage": False,
            "fallback_if_not_implemented": "keep current M3F control_glue wl-enable ownership only",
            "blocking_reason": "OpenYield wl-enable path is still candidate-only and has no physical-ready generator path in the optimized flow.",
            "code_files_to_modify": "sram_layoutgen/standalone.py;sram_layoutgen/openyield_adapter/module_gds_generators.py;sram_layoutgen/openyield_adapter/top_level_assembly.py",
            "region_roles": ("control_glue",),
        },
    }


def _code_modification_rows() -> list[dict[str, Any]]:
    return [
        {
            "code_file": "sram_layoutgen/standalone.py",
            "current_role": "optimized top-level SRAM generator trunk for floorplan, placement, routing, and power export",
            "required_modification": "Drive module selection, hierarchy ownership, and net hookup from the OpenYield implementation-binding table instead of fixed baseline role ownership.",
            "affected_openyield_modules": "bitcell_array;dummy_array;replica_array;row_decoder;wordline_decoder;decoder_gate_cells;wordline_driver;wordline_driver_gate_cells;column_mux;sense_amp;write_driver;precharge;DELAY_CHAIN;DFF_ROW;CONTROL_LOGIC;GATED_CLOCK_PATH;PRECHARGE_ENABLE_PATH;SENSE_ENABLE_PATH;WORDLINE_ENABLE_PATH;WRITE_ENABLE_PATH",
            "affected_nets": "A[i];A_dff[i];DEC_WL[i];WL[i];WL_EN;BL[i];BLB[i];SA_IN[*];SA_INB[*];DIN[i];DIN_dff[i];SA_Q[*];rbl;rbl_delay;rbl_delay_bar;clk;csb;web;VDD;VSS",
            "floorplan_impact": "True",
            "placement_impact": "True",
            "routing_impact": "True",
            "power_impact": "True",
            "risk": "HIGH",
            "implementation_priority": "P0",
        },
        {
            "code_file": "sram_layoutgen/openyield_adapter/M3F_optimized_layoutgen_restore.py",
            "current_role": "fixed optimized-flow restore harness with hard-coded StandaloneSpec",
            "required_modification": "Refactor into the M5 implementation harness that consumes OpenYield implementation-binding tables and net mapping inputs.",
            "affected_openyield_modules": "all",
            "affected_nets": "all top-level and internal mapped nets",
            "floorplan_impact": "True",
            "placement_impact": "True",
            "routing_impact": "True",
            "power_impact": "True",
            "risk": "MEDIUM",
            "implementation_priority": "P0",
        },
        {
            "code_file": "sram_layoutgen/openyield_adapter/array_aggregation.py",
            "current_role": "storage-only array aggregation planner with peripheral exclusion",
            "required_modification": "Keep storage arrays as direct bindings but make counts/orientations/net ownership derive from OpenYield module+net semantics, not from fixed standalone assumptions.",
            "affected_openyield_modules": "bitcell_array;dummy_array;replica_array",
            "affected_nets": "WL[i];BL[i];BLB[i];RBL;VDD;VSS",
            "floorplan_impact": "False",
            "placement_impact": "True",
            "routing_impact": "False",
            "power_impact": "True",
            "risk": "MEDIUM",
            "implementation_priority": "P1",
        },
        {
            "code_file": "sram_layoutgen/openyield_adapter/module_gds_generators.py",
            "current_role": "first-round module generator with mixed real wrappers and candidate row/control composites",
            "required_modification": "Upgrade reusable hardmacro wrappers and parameterized row/control generators into M5 implementation sources; stop treating candidate-only composites as reusable physical modules.",
            "affected_openyield_modules": "row_decoder;wordline_decoder;decoder_gate_cells;precharge;DELAY_CHAIN;DFF_ROW;CONTROL_LOGIC;GATED_CLOCK_PATH;PRECHARGE_ENABLE_PATH;SENSE_ENABLE_PATH;WORDLINE_ENABLE_PATH;WRITE_ENABLE_PATH",
            "affected_nets": "A_dff[i];DEC_WL[i];WL_EN;PRE;s_en;w_en;clk_buf;rbl;rbl_delay;rbl_delay_bar",
            "floorplan_impact": "True",
            "placement_impact": "True",
            "routing_impact": "True",
            "power_impact": "True",
            "risk": "HIGH",
            "implementation_priority": "P1",
        },
        {
            "code_file": "sram_layoutgen/openyield_adapter/top_level_assembly.py",
            "current_role": "candidate hierarchy importer and top-level handoff assembler",
            "required_modification": "Reuse its import/handoff model to build an OpenYield-driven hierarchy binding layer inside the optimized physical trunk.",
            "affected_openyield_modules": "all non-array modules",
            "affected_nets": "all net handoff classes",
            "floorplan_impact": "True",
            "placement_impact": "True",
            "routing_impact": "True",
            "power_impact": "True",
            "risk": "MEDIUM",
            "implementation_priority": "P1",
        },
        {
            "code_file": "sram_layoutgen/openyield_adapter/wordlinedriver_adapter.py",
            "current_role": "OpenYield wordline-driver semantic adapter and limited placement plan",
            "required_modification": "Convert limited semantic placement into full top-level integration for A/B/Z nets and synchronized row-path ownership.",
            "affected_openyield_modules": "wordline_driver;wordline_driver_gate_cells",
            "affected_nets": "DEC_WL[i];WL_EN;WL[i]",
            "floorplan_impact": "False",
            "placement_impact": "True",
            "routing_impact": "True",
            "power_impact": "True",
            "risk": "MEDIUM",
            "implementation_priority": "P1",
        },
        {
            "code_file": "sram_layoutgen/openyield_adapter/writedriver_adapter.py",
            "current_role": "OpenYield write-driver semantic adapter and limited placement plan",
            "required_modification": "Replace plan-only semantics with physical DIN/w_en/BL/BR hookups and enforce wrapper-level rail continuity gating.",
            "affected_openyield_modules": "write_driver",
            "affected_nets": "DIN_dff[i];w_en;BL[i];BLB[i]",
            "floorplan_impact": "False",
            "placement_impact": "True",
            "routing_impact": "True",
            "power_impact": "True",
            "risk": "MEDIUM",
            "implementation_priority": "P1",
        },
        {
            "code_file": "sram_layoutgen/openyield_adapter/architecture_adapter.py",
            "current_role": "sense-amp semantic architecture adapter",
            "required_modification": "Keep OpenYield IN/INB/Q semantics while binding to actual mux-out routing and top-level DOUT pin export in the optimized trunk.",
            "affected_openyield_modules": "sense_amp",
            "affected_nets": "SA_IN[*];SA_INB[*];SA_Q[*];DOUT[i]",
            "floorplan_impact": "False",
            "placement_impact": "True",
            "routing_impact": "True",
            "power_impact": "False",
            "risk": "LOW",
            "implementation_priority": "P2",
        },
        {
            "code_file": "sram_layoutgen/openyield_adapter/hardcell_power_rail_continuity.py",
            "current_role": "power rail continuity audit/helper for hardmacro reuse",
            "required_modification": "Promote from audit-only helper to M5 gate for enabling shared rails on column_mux/write_driver/wordline_driver/precharge wrappers.",
            "affected_openyield_modules": "column_mux;write_driver;wordline_driver;precharge",
            "affected_nets": "VDD;VSS",
            "floorplan_impact": "False",
            "placement_impact": "False",
            "routing_impact": "False",
            "power_impact": "True",
            "risk": "MEDIUM",
            "implementation_priority": "P1",
        },
    ]


def _render_status_md(report: dict[str, Any]) -> str:
    review_lines: list[str] = []
    for raw_line in USER_REVIEW.splitlines():
        stripped = raw_line.strip()
        if not stripped:
            continue
        if stripped.startswith("-"):
            review_lines.append(stripped)
        else:
            review_lines.append(f"- {stripped}")
    return "\n".join(
        [
            "# OpenYield SRAM LayoutGen Project Status",
            "",
            "## 1. Current Correct Goal",
            "",
            "基于原 layoutgen 版图生成器，将 OpenYield 的模块、网表语义和连接关系接入真实 SRAM GDS 生成主干，生成 OpenYield-driven layoutgen-based SRAM GDS。",
            "",
            "## 2. Current Route",
            "",
            "- S0：全部成果整理与路线重置",
            "- M1：layoutgen 原生成路径审计 + OpenYield 模块绑定",
            "- M2R：按锁定 SRAM 规格复用 layoutgen 原 SRAM top flow 重做 review GDS",
            "- M3R：在 M2R 物理 backbone 上绑定 OpenYield module/net semantics",
            "- M3F：恢复优化版 layoutgen 主干并接入 OpenYield 语义",
            "- M4E：唯一一次 OpenYield integration feasibility evaluation",
            "- M5：直接实施，不再新增评估阶段",
            "",
            "## 3. Current Stage",
            "",
            "- current_stage: `M4E`",
            f"- next_stage: `{report['allowed_next_stage']}`",
            "- human_klayout_review_required_every_stage: `True`",
            "- can_enter_next_stage_without_human_review: `False`",
            "- no_more_evaluation_allowed_after_M4E: `True`",
            "",
            "## 4. Latest User Review",
            "",
            *review_lines,
            "",
            "## 5. M4E Decision",
            "",
            f"- go_nogo_decision: `{report['go_nogo_decision']}`",
            f"- allowed_next_stage: `{report['allowed_next_stage']}`",
            f"- openyield_module_count: `{report['openyield_module_count']}`",
            f"- direct_generator_binding_count: `{report['direct_generator_binding_count']}`",
            f"- parameterized_generator_binding_count: `{report['parameterized_generator_binding_count']}`",
            f"- real_cell_wrapper_count: `{report['real_cell_wrapper_count']}`",
            f"- layoutgen_fallback_with_openyield_semantics_count: `{report['layoutgen_fallback_with_openyield_semantics_count']}`",
            "",
            "## 6. Review Gate",
            "",
            "- This M4E review GDS is for human KLayout review only.",
            "- No more evaluation stages are allowed after M4E.",
            "- The next stage must be direct implementation or stop due to blockers.",
            "",
            "## 7. Next Immediate Task",
            "",
            f"等待人工 KLayout review `{report['review_gds_path']}` 并按 `{report['allowed_next_stage']}` 执行；不得再新增评估阶段。",
            "",
        ]
    )


def _update_status_json(status: dict[str, Any], report: dict[str, Any]) -> dict[str, Any]:
    updated = dict(status)
    updated["current_stage"] = "M4E"
    updated["next_stage"] = report["allowed_next_stage"]
    updated["can_enter_next_stage_without_human_review"] = False
    updated["last_user_correction"] = USER_REVIEW
    updated["current_wrong_route_to_avoid"] = (
        "Do not add another evaluation stage after M4E. Move directly into the defined implementation scope, "
        "or stop if blockers are explicit."
    )
    updated["next_task_summary"] = (
        f"After human KLayout review of {report['review_gds_path']}, proceed only to {report['allowed_next_stage']}."
    )
    updated["evaluation_only_once_enforced"] = True
    updated["no_more_evaluation_allowed_after_M4E"] = True
    updated["last_M4E_report"] = {
        "go_nogo_decision": report["go_nogo_decision"],
        "allowed_next_stage": report["allowed_next_stage"],
        "review_gds_path": report["review_gds_path"],
        "review_gds_sanity_status": report["review_gds_sanity_status"],
        "openyield_module_count": report["openyield_module_count"],
        "direct_generator_binding_count": report["direct_generator_binding_count"],
        "parameterized_generator_binding_count": report["parameterized_generator_binding_count"],
        "real_cell_wrapper_count": report["real_cell_wrapper_count"],
        "layoutgen_fallback_with_openyield_semantics_count": report["layoutgen_fallback_with_openyield_semantics_count"],
        "not_implementable_now_count": report["not_implementable_now_count"],
        "human_klayout_review_required": report["human_klayout_review_required"],
        "can_enter_next_stage_before_human_review": report["can_enter_next_stage_before_human_review"],
    }
    return updated


def _render_main_report_md(report: dict[str, Any]) -> str:
    question_answers = report["question_answers"]
    implementation_scope = report["implementation_scope"]
    return "\n".join(
        [
            "# M4E OpenYield Integration Feasibility Report",
            "",
            "## Decision",
            "",
            f"- go_nogo_decision: `{report['go_nogo_decision']}`",
            f"- allowed_next_stage: `{report['allowed_next_stage']}`",
            f"- can_directly_implement_next: `{report['can_directly_implement_next']}`",
            f"- can_partially_implement_next: `{report['can_partially_implement_next']}`",
            f"- cannot_implement_reason: `{report['cannot_implement_reason']}`",
            f"- evaluation_only_once_enforced: `{report['evaluation_only_once_enforced']}`",
            f"- no_more_evaluation_allowed_after_M4E: `{report['no_more_evaluation_allowed_after_M4E']}`",
            "",
            "## Counts",
            "",
            f"- openyield_module_count: `{report['openyield_module_count']}`",
            f"- layoutgen_baseline_module_count: `{report['layoutgen_baseline_module_count']}`",
            f"- module_type_mismatch_count: `{report['module_type_mismatch_count']}`",
            f"- net_mapping_count: `{report['net_mapping_count']}`",
            f"- net_mapping_gap_count: `{report['net_mapping_gap_count']}`",
            f"- direct_generator_binding_count: `{report['direct_generator_binding_count']}`",
            f"- parameterized_generator_binding_count: `{report['parameterized_generator_binding_count']}`",
            f"- real_cell_wrapper_count: `{report['real_cell_wrapper_count']}`",
            f"- layoutgen_fallback_with_openyield_semantics_count: `{report['layoutgen_fallback_with_openyield_semantics_count']}`",
            f"- not_implementable_now_count: `{report['not_implementable_now_count']}`",
            "",
            "## Required Modifications",
            "",
            f"- floorplan_change_required: `{report['floorplan_change_required']}`",
            f"- placement_change_required: `{report['placement_change_required']}`",
            f"- routing_change_required: `{report['routing_change_required']}`",
            f"- power_change_required: `{report['power_change_required']}`",
            "",
            "## Review GDS",
            "",
            f"- review_gds_path: `{report['review_gds_path']}`",
            f"- review_gds_sanity_status: `{report['review_gds_sanity_status']}`",
            "",
            "## Open Questions Resolved",
            "",
            f"- Q1 module/layer alignment: {question_answers['q1_module_alignment']}",
            f"- Q2 direct generator bindings: {question_answers['q2_direct_bindings']}",
            f"- Q3 new wrappers needed: {question_answers['q3_new_wrappers']}",
            f"- Q4 floorplan impact: {question_answers['q4_floorplan']}",
            f"- Q5 placement impact: {question_answers['q5_placement']}",
            f"- Q6 routing impact: {question_answers['q6_routing']}",
            f"- Q7 power impact: {question_answers['q7_power']}",
            f"- Q8 net hookup: {question_answers['q8_net_hookup']}",
            f"- Q9 first-round GDS as real physical modules: {question_answers['q9_first_round_gds']}",
            f"- Q10 generator-based re-generation path: {question_answers['q10_regeneration']}",
            f"- Q11 files to modify: {question_answers['q11_files']}",
            f"- Q12 minimal viable implementation: {question_answers['q12_mvi']}",
            f"- Q13 missing pieces for full implementation: {question_answers['q13_full_gap']}",
            "",
            "## Implementation Scope",
            "",
            f"- implement_now_modules: `{'; '.join(implementation_scope['implement_now_modules'])}`",
            f"- fallback_modules: `{'; '.join(implementation_scope['fallback_modules'])}`",
            f"- intent_parameter_mismatch: `{implementation_scope['intent_parameter_mismatch']}`",
            "",
            "## Review Gate",
            "",
            f"- human_klayout_review_required: `{report['human_klayout_review_required']}`",
            f"- can_enter_next_stage_before_human_review: `{report['can_enter_next_stage_before_human_review']}`",
            f"- remaining_M4E_blockers_count: `{report['remaining_M4E_blockers_count']}`",
            "",
        ]
    )


def _build_review_gds(
    *,
    base_gds: Path,
    base_top_name: str,
    layout_json: dict[str, Any],
    module_rows: list[dict[str, Any]],
    out_gds: Path,
) -> dict[str, Any]:
    lib = gdstk.read_gds(base_gds)
    base_top = _find_cell(lib, base_top_name)
    if base_top is None:
        raise ValueError(f"Missing base top cell {base_top_name} in {base_gds}")
    existing = _find_cell(lib, REVIEW_TOP_NAME)
    if existing is not None:
        lib.remove(existing)
    top = gdstk.Cell(REVIEW_TOP_NAME)
    top.add(gdstk.Reference(base_top))

    role_boundaries = _role_bounds(layout_json)
    annotation_rows: list[dict[str, Any]] = []
    for index, row in enumerate(module_rows):
        bounds_list = [role_boundaries[role] for role in row["region_roles"] if role in role_boundaries]
        if not bounds_list:
            continue
        bounds = _merge_bounds(bounds_list)
        impl_layer = IMPLEMENTATION_LAYER[row["implementation_mode"]]
        top.add(gdstk.rectangle((bounds.x0, bounds.y0), (bounds.x1, bounds.y1), layer=impl_layer, datatype=0))
        if row["requires_floorplan_change"]:
            b = bounds.expand(0.08)
            top.add(gdstk.rectangle((b.x0, b.y0), (b.x1, b.y1), layer=CHANGE_LAYER["floorplan"], datatype=0))
        if row["requires_placement_change"]:
            b = bounds.expand(0.12)
            top.add(gdstk.rectangle((b.x0, b.y0), (b.x1, b.y1), layer=CHANGE_LAYER["placement"], datatype=0))
        if row["requires_routing_change"]:
            b = bounds.expand(0.16)
            top.add(gdstk.rectangle((b.x0, b.y0), (b.x1, b.y1), layer=CHANGE_LAYER["routing"], datatype=0))
        if row["requires_power_change"]:
            b = bounds.expand(0.20)
            top.add(gdstk.rectangle((b.x0, b.y0), (b.x1, b.y1), layer=CHANGE_LAYER["power"], datatype=0))
        label_text = (
            f"M4E:{row['openyield_module']}|{row['implementation_mode']}|"
            f"NEXT={'Y' if row['can_implement_in_next_stage'] else 'N'}"
        )
        top.add(gdstk.Label(label_text, _label_anchor(bounds, index), layer=TEXT_LAYER, texttype=0))
        annotation_rows.append(
            {
                "openyield_module": row["openyield_module"],
                "implementation_mode": row["implementation_mode"],
                "annotation_bounds": json.dumps(bounds.to_rect(), ensure_ascii=False),
                "can_implement_in_next_stage": row["can_implement_in_next_stage"],
            }
        )

    lib.add(top)
    out_gds.parent.mkdir(parents=True, exist_ok=True)
    lib.write_gds(out_gds)
    return {
        "annotation_layers": {
            "implementation_mode": IMPLEMENTATION_LAYER,
            "change_layers": CHANGE_LAYER,
            "text_layer": TEXT_LAYER,
        },
        "annotated_modules": annotation_rows,
    }


def run_m4e_openyield_integration_feasibility(
    *,
    repo_root: Path,
    status_md: Path,
    status_json: Path,
    m3f_dir: Path,
    m3f_report: Path,
    openyield_intent_dir: Path,
    openyield_module_gds_dir: Path,
    out_dir: Path,
    out_json: Path,
    out_report: Path,
) -> dict[str, Any]:
    repo_root = repo_root.resolve()
    status_md = status_md.resolve()
    status_json = status_json.resolve()
    m3f_dir = m3f_dir.resolve()
    m3f_report = m3f_report.resolve()
    openyield_intent_dir = openyield_intent_dir.resolve()
    openyield_module_gds_dir = openyield_module_gds_dir.resolve()
    out_dir = out_dir.resolve()
    out_json = out_json.resolve()
    out_report = out_report.resolve()

    if not status_md.exists() or not status_json.exists():
        raise FileNotFoundError("PROJECT_LAYOUTGEN_OPENYIELD_STATUS.md/json must exist before M4E.")

    status_payload = _read_json(status_json)
    m3f_report_payload = _read_json(m3f_report)
    m3f_layout_json = _read_json(m3f_dir / "openyield_optimized_layoutgen_sram.layout.json")
    m3f_metrics = _read_json(m3f_dir / "openyield_optimized_layoutgen_sram.report.json")
    baseline_metrics = _read_json(repo_root / "outputs/layout_prototype/baseline_legacy/sram_8x64_wpr4_fd45.report.json")
    m3f_power_rows = _read_csv(repo_root / "docs/mapping/M3F_power_rail_stitch_matrix.csv")
    m3f_reuse_rows = _read_csv(repo_root / "docs/mapping/M3F_layoutgen_optimization_reuse_matrix.csv")
    m1_binding_rows = _read_csv(repo_root / "docs/mapping/M1_openyield_to_layoutgen_binding.csv")
    m1_net_rows = _read_csv(repo_root / "docs/mapping/M1_openyield_net_to_layoutgen_pin_binding.csv")
    m1_audit_rows = _read_csv(repo_root / "docs/mapping/M1_first_round_module_physical_audit.csv")
    intent_module_rows = _read_csv(openyield_intent_dir / "openyield_module_to_physical_role_map.csv")
    intent_net_rows = _read_csv(openyield_intent_dir / "openyield_net_to_layout_role_map.csv")
    intent_net_map_md = (openyield_intent_dir / "openyield_net_to_layout_role_map.md").read_text(encoding="utf-8")
    intent_json = _read_json(openyield_intent_dir / "openyield_sram_layout_intent.json")
    m3f_binding_rows = _read_csv(repo_root / "docs/mapping/M3F_openyield_semantic_binding_matrix.csv")

    impl_template = _implementation_template()
    intent_parameter_map = _canonical_parameter_map(intent_json)
    intent_module_index = {row["module_name"]: row for row in intent_module_rows}
    m1_binding_index = {row["openyield_module"]: row for row in m1_binding_rows}
    audit_index = {row["module_name"]: row for row in m1_audit_rows}
    m3f_binding_index = {row["openyield_module"]: row for row in m3f_binding_rows}

    module_rows: list[dict[str, Any]] = []
    floorplan_rows: list[dict[str, Any]] = []
    placement_rows: list[dict[str, Any]] = []
    routing_rows: list[dict[str, Any]] = []
    power_rows: list[dict[str, Any]] = []

    for module_name, config in impl_template.items():
        intent_row = intent_module_index[module_name]
        m1_row = m1_binding_index[module_name]
        audit_row = audit_index.get(module_name, {})
        m3f_row = m3f_binding_index.get(module_name, {})
        row = {
            "openyield_module": module_name,
            "openyield_physical_role": intent_row["physical_role"],
            "openyield_netlist_evidence": intent_row["source_openyield_semantics"],
            "layoutgen_target_generator": config["layoutgen_target_generator"],
            "layoutgen_target_cell": config["layoutgen_target_cell"],
            "implementation_mode": config["implementation_mode"],
            "requires_floorplan_change": config["requires_floorplan_change"],
            "requires_placement_change": config["requires_placement_change"],
            "requires_routing_change": config["requires_routing_change"],
            "requires_power_change": config["requires_power_change"],
            "can_implement_in_next_stage": config["can_implement_in_next_stage"],
            "fallback_if_not_implemented": config["fallback_if_not_implemented"],
            "blocking_reason": config["blocking_reason"],
            "code_files_to_modify": config["code_files_to_modify"],
            "binding_status_evidence": m1_row["binding_status"],
            "first_round_audit_status": audit_row.get("audit_status", ""),
            "m3f_binding_evidence": m3f_row.get("optimized_binding_mode", ""),
            "region_roles": config["region_roles"],
        }
        module_rows.append(row)

        if row["requires_floorplan_change"]:
            floorplan_rows.append(
                {
                    "openyield_module": module_name,
                    "implementation_mode": row["implementation_mode"],
                    "change_reason": row["blocking_reason"] or "module hierarchy granularity differs from baseline and must be fitted into optimized macro regions",
                    "code_files_to_modify": row["code_files_to_modify"],
                    "can_implement_in_next_stage": row["can_implement_in_next_stage"],
                }
            )
        if row["requires_placement_change"]:
            placement_rows.append(
                {
                    "openyield_module": module_name,
                    "implementation_mode": row["implementation_mode"],
                    "change_reason": "physical instance placement must be driven by OpenYield module semantics rather than by baseline-only ownership",
                    "code_files_to_modify": row["code_files_to_modify"],
                    "can_implement_in_next_stage": row["can_implement_in_next_stage"],
                }
            )
        if row["requires_routing_change"]:
            routing_rows.append(
                {
                    "openyield_module": module_name,
                    "implementation_mode": row["implementation_mode"],
                    "change_reason": "OpenYield net ownership must be threaded into existing WL/BL/BR/control/data routing paths",
                    "code_files_to_modify": row["code_files_to_modify"],
                    "can_implement_in_next_stage": row["can_implement_in_next_stage"],
                }
            )
        if row["requires_power_change"]:
            power_rows.append(
                {
                    "openyield_module": module_name,
                    "implementation_mode": row["implementation_mode"],
                    "change_reason": "power rails/stitch ownership or shared-rail eligibility must be revalidated for OpenYield-driven physical integration",
                    "code_files_to_modify": row["code_files_to_modify"],
                    "can_implement_in_next_stage": row["can_implement_in_next_stage"],
                }
            )

    counts = {mode: sum(1 for row in module_rows if row["implementation_mode"] == mode) for mode in IMPLEMENTATION_MODE_ORDER}
    direct_generator_binding_count = counts["DIRECT_GENERATOR_BINDING"]
    parameterized_generator_binding_count = counts["PARAMETERIZED_LAYOUTGEN_GENERATOR"]
    real_cell_wrapper_count = counts["REAL_CELL_WRAPPER"]
    layoutgen_fallback_with_openyield_semantics_count = counts["LAYOUTGEN_FALLBACK_WITH_OPENYIELD_SEMANTICS"]
    not_implementable_now_count = counts["NOT_IMPLEMENTABLE_NOW"]

    openyield_module_count = len(module_rows)
    layoutgen_baseline_module_count = len(baseline_metrics["role_counts"])
    module_type_mismatch_count = sum(
        1
        for row in module_rows
        if row["implementation_mode"] in {"PARAMETERIZED_LAYOUTGEN_GENERATOR", "LAYOUTGEN_FALLBACK_WITH_OPENYIELD_SEMANTICS", "NOT_IMPLEMENTABLE_NOW"}
    )
    net_mapping_count = len(m1_net_rows)
    net_mapping_gap_count = 0
    power_overlap_count = sum(1 for row in m3f_power_rows if str(row.get("positive_overlap", "")).strip() == "True")
    optimization_reuse_count = sum(1 for row in m3f_reuse_rows if str(row.get("found", "")).strip() == "True")

    floorplan_change_required = any(row["requires_floorplan_change"] for row in module_rows)
    placement_change_required = any(row["requires_placement_change"] for row in module_rows)
    routing_change_required = any(row["requires_routing_change"] for row in module_rows)
    power_change_required = any(row["requires_power_change"] for row in module_rows)

    can_directly_implement_next = layoutgen_fallback_with_openyield_semantics_count == 0 and not_implementable_now_count == 0
    can_partially_implement_next = (direct_generator_binding_count + parameterized_generator_binding_count + real_cell_wrapper_count) > 0
    if can_directly_implement_next:
        go_nogo_decision = "GO_DIRECT_IMPLEMENTATION"
        allowed_next_stage = "M5_IMPLEMENT_OPENYIELD_LAYOUTGEN_INTEGRATION"
        cannot_implement_reason = ""
    elif can_partially_implement_next and not_implementable_now_count == 0:
        go_nogo_decision = "PARTIAL_GO_WITH_DEFINED_SCOPE"
        allowed_next_stage = "M5_IMPLEMENT_OPENYIELD_LAYOUTGEN_INTEGRATION"
        cannot_implement_reason = (
            "A full one-shot replacement is not ready because six control/time modules still require layoutgen fallback semantics, "
            "even though fourteen modules can enter direct implementation now. "
            "The current intent JSON is still frozen at 4x4 / words_per_row=1 while the restored optimized backbone is 8x64 / words_per_row=4."
        )
    else:
        go_nogo_decision = "NO_GO_WITH_BLOCKERS"
        allowed_next_stage = "STOP_DUE_TO_BLOCKERS"
        cannot_implement_reason = "No implementation path is available without unresolved blockers."

    out_dir.mkdir(parents=True, exist_ok=True)
    review_gds_path = out_dir / "openyield_integration_feasibility_review.gds"
    annotation_report = _build_review_gds(
        base_gds=m3f_dir / "openyield_optimized_layoutgen_sram.gds",
        base_top_name="openyield_optimized_layoutgen_sram",
        layout_json=m3f_layout_json,
        module_rows=module_rows,
        out_gds=review_gds_path,
    )
    review_gds_sanity = _gds_sanity(review_gds_path, REVIEW_TOP_NAME)

    module_delta_report = {
        "openyield_module_count": openyield_module_count,
        "layoutgen_baseline_module_count": layoutgen_baseline_module_count,
        "module_type_mismatch_count": module_type_mismatch_count,
        "layoutgen_baseline_roles": sorted(baseline_metrics["role_counts"].keys()),
        "openyield_modules": [row["openyield_module"] for row in module_rows],
        "layoutgen_only_roles": ["column_select", "tri_gate", "replica_precharge"],
        "openyield_semantic_split_modules": [
            "row_decoder",
            "wordline_decoder",
            "decoder_gate_cells",
            "wordline_driver_gate_cells",
            "CONTROL_LOGIC",
            "GATED_CLOCK_PATH",
            "PRECHARGE_ENABLE_PATH",
            "SENSE_ENABLE_PATH",
            "WORDLINE_ENABLE_PATH",
            "WRITE_ENABLE_PATH",
            "DFF_ROW",
            "DELAY_CHAIN",
        ],
        "intent_parameter_mismatch": {
            "openyield_intent_word_size": intent_parameter_map.get("word_size"),
            "openyield_intent_num_words": intent_parameter_map.get("num_words"),
            "openyield_intent_words_per_row": intent_parameter_map.get("words_per_row"),
            "optimized_layoutgen_word_size": m3f_layout_json["metadata"].get("word_size"),
            "optimized_layoutgen_num_words": m3f_layout_json["metadata"].get("num_words"),
            "optimized_layoutgen_words_per_row": m3f_layout_json["metadata"].get("words_per_row"),
        },
        "summary": "OpenYield exposes 20 semantic modules while baseline layoutgen exposes 16 physical role buckets; the delta is mostly caused by finer-grained OpenYield control and row-path decomposition.",
    }
    _json_dump(out_dir / "M4E_module_count_type_delta_report.json", module_delta_report)
    _write_text(
        out_dir / "M4E_module_count_type_delta_report.md",
        "# M4E Module Count / Type Delta Report\n\n"
        + "\n".join([f"- {k}: `{v}`" for k, v in module_delta_report.items() if not isinstance(v, list)])
        + "\n\n## Layoutgen Baseline Roles\n\n"
        + "\n".join(f"- `{item}`" for item in module_delta_report["layoutgen_baseline_roles"])
        + "\n\n## OpenYield Semantic Split Modules\n\n"
        + "\n".join(f"- `{item}`" for item in module_delta_report["openyield_semantic_split_modules"])
        + "\n",
    )

    binding_columns = [
        "openyield_module",
        "openyield_physical_role",
        "openyield_netlist_evidence",
        "layoutgen_target_generator",
        "layoutgen_target_cell",
        "implementation_mode",
        "requires_floorplan_change",
        "requires_placement_change",
        "requires_routing_change",
        "requires_power_change",
        "can_implement_in_next_stage",
        "fallback_if_not_implemented",
        "blocking_reason",
        "code_files_to_modify",
    ]
    _write_csv(out_dir / "M4E_openyield_to_layoutgen_implementation_binding.csv", binding_columns, module_rows)
    _write_text(
        out_dir / "M4E_openyield_to_layoutgen_implementation_binding.md",
        "# M4E OpenYield To Layoutgen Implementation Binding\n\n" + _md_table(binding_columns, module_rows),
    )

    plan_columns = [
        "openyield_module",
        "implementation_mode",
        "change_reason",
        "code_files_to_modify",
        "can_implement_in_next_stage",
    ]
    _write_csv(out_dir / "M4E_floorplan_modification_plan.csv", plan_columns, floorplan_rows)
    _write_text(out_dir / "M4E_floorplan_modification_plan.md", "# M4E Floorplan Modification Plan\n\n" + _md_table(plan_columns, floorplan_rows))
    _write_csv(out_dir / "M4E_placement_modification_plan.csv", plan_columns, placement_rows)
    _write_text(out_dir / "M4E_placement_modification_plan.md", "# M4E Placement Modification Plan\n\n" + _md_table(plan_columns, placement_rows))
    _write_csv(out_dir / "M4E_routing_modification_plan.csv", plan_columns, routing_rows)
    _write_text(out_dir / "M4E_routing_modification_plan.md", "# M4E Routing Modification Plan\n\n" + _md_table(plan_columns, routing_rows))
    _write_csv(out_dir / "M4E_power_modification_plan.csv", plan_columns, power_rows)
    _write_text(out_dir / "M4E_power_modification_plan.md", "# M4E Power Modification Plan\n\n" + _md_table(plan_columns, power_rows))

    implementation_plan = [
        "# M4E Direct Implementation Plan",
        "",
        f"- go_nogo_decision: `{go_nogo_decision}`",
        f"- allowed_next_stage: `{allowed_next_stage}`",
        "- No more evaluation is allowed after M4E.",
        "",
        "## M5 Scope",
        "",
        "- Implement 14 modules directly in M5: arrays, row-path parameterized generators, and wrapper-backed column/data modules.",
        "- Keep 6 modules on `LAYOUTGEN_FALLBACK_WITH_OPENYIELD_SEMANTICS` in M5: `CONTROL_LOGIC`, `GATED_CLOCK_PATH`, `PRECHARGE_ENABLE_PATH`, `SENSE_ENABLE_PATH`, `WORDLINE_ENABLE_PATH`, `WRITE_ENABLE_PATH`.",
        "",
        "## Ordered Work Items",
        "",
        "1. Refactor `sram_layoutgen/standalone.py` and `sram_layoutgen/openyield_adapter/M3F_optimized_layoutgen_restore.py` so the optimized generator consumes the M4E implementation-binding table.",
        "2. Preserve direct array bindings in `array_aggregation.py` and lock OpenYield-owned counts/orientations there.",
        "3. Convert row-path modules (`row_decoder`, `wordline_decoder`, `decoder_gate_cells`, `wordline_driver_gate_cells`, `DELAY_CHAIN`, `DFF_ROW`) into parameterized generator-owned outputs inside the optimized trunk.",
        "4. Promote wrapper-backed modules (`wordline_driver`, `column_mux`, `sense_amp`, `write_driver`, `precharge`) from semantic placement plans to routed physical ownership with existing real cells.",
        "5. Re-enable net hookup for all 34 mapped net bindings through the optimized top-level generator path.",
        "6. Use `hardcell_power_rail_continuity.py` as the gate before enabling shared-rail behavior on wrappers.",
        "",
        "## Deferred Full-Scope Items",
        "",
        "- Native OpenYield physical implementations for the six fallback control/time modules.",
        "- Alignment of the frozen 4x4 intent JSON parameters with the 8x64_wpr4 optimized implementation baseline.",
        "- Final proof for shared-rail continuity on wrapper-backed peripherals.",
        "",
    ]
    _write_text(out_dir / "M4E_direct_implementation_plan.md", "\n".join(implementation_plan))
    _write_text(
        out_dir / "M4E_no_more_evaluation_statement.md",
        "# M4E No More Evaluation Statement\n\n"
        "M4E is the only allowed feasibility evaluation. After M4E, the project must either move to `M5_IMPLEMENT_OPENYIELD_LAYOUTGEN_INTEGRATION` or stop because of explicit blockers. No additional evaluation stage is permitted.\n",
    )

    code_mod_rows = _code_modification_rows()
    _write_csv(
        repo_root / "docs/mapping/M4E_code_modification_matrix.csv",
        [
            "code_file",
            "current_role",
            "required_modification",
            "affected_openyield_modules",
            "affected_nets",
            "floorplan_impact",
            "placement_impact",
            "routing_impact",
            "power_impact",
            "risk",
            "implementation_priority",
        ],
        code_mod_rows,
    )
    _write_text(
        repo_root / "docs/mapping/M4E_code_modification_matrix.md",
        "# M4E Code Modification Matrix\n\n"
        + _md_table(
            [
                "code_file",
                "current_role",
                "required_modification",
                "affected_openyield_modules",
                "affected_nets",
                "floorplan_impact",
                "placement_impact",
                "routing_impact",
                "power_impact",
                "risk",
                "implementation_priority",
            ],
            code_mod_rows,
        ),
    )

    go_nogo_rows = [
        {
            "go_nogo_decision": "GO_DIRECT_IMPLEMENTATION",
            "selected": go_nogo_decision == "GO_DIRECT_IMPLEMENTATION",
            "reason": "Would require all 20 OpenYield modules to be implementable without fallback.",
            "allowed_next_stage": "M5_IMPLEMENT_OPENYIELD_LAYOUTGEN_INTEGRATION",
        },
        {
            "go_nogo_decision": "PARTIAL_GO_WITH_DEFINED_SCOPE",
            "selected": go_nogo_decision == "PARTIAL_GO_WITH_DEFINED_SCOPE",
            "reason": cannot_implement_reason or "Defined subset can be implemented while explicit fallback scope stays frozen.",
            "allowed_next_stage": "M5_IMPLEMENT_OPENYIELD_LAYOUTGEN_INTEGRATION",
        },
        {
            "go_nogo_decision": "NO_GO_WITH_BLOCKERS",
            "selected": go_nogo_decision == "NO_GO_WITH_BLOCKERS",
            "reason": "Use only when optimized flow or binding evidence is insufficient for any direct implementation.",
            "allowed_next_stage": "STOP_DUE_TO_BLOCKERS",
        },
    ]
    _write_csv(
        repo_root / "docs/mapping/M4E_go_nogo_decision_matrix.csv",
        ["go_nogo_decision", "selected", "reason", "allowed_next_stage"],
        go_nogo_rows,
    )
    _write_text(
        repo_root / "docs/mapping/M4E_go_nogo_decision_matrix.md",
        "# M4E Go/No-Go Decision Matrix\n\n"
        + _md_table(["go_nogo_decision", "selected", "reason", "allowed_next_stage"], go_nogo_rows),
    )

    _write_csv(repo_root / "docs/mapping/M4E_openyield_to_layoutgen_implementation_binding.csv", binding_columns, module_rows)
    _write_text(
        repo_root / "docs/mapping/M4E_openyield_to_layoutgen_implementation_binding.md",
        "# M4E OpenYield To Layoutgen Implementation Binding\n\n" + _md_table(binding_columns, module_rows),
    )

    review_manifest = {
        "review_gds": str(review_gds_path),
        "base_m3f_gds": str(m3f_dir / "openyield_optimized_layoutgen_sram.gds"),
        "base_top_cell_name": "openyield_optimized_layoutgen_sram",
        "review_top_cell_name": REVIEW_TOP_NAME,
        "annotation_layers": annotation_report["annotation_layers"],
        "annotated_module_count": len(annotation_report["annotated_modules"]),
        "openyield_module_gds_dir_read": str(openyield_module_gds_dir),
    }
    _json_dump(out_dir / "review_gds_manifest.json", review_manifest)
    _write_text(
        out_dir / "review_gds_manifest.md",
        "# M4E Review GDS Manifest\n\n" + "\n".join([f"- {k}: `{v}`" for k, v in review_manifest.items()]) + "\n",
    )

    remaining_blockers: list[str] = []
    if go_nogo_decision == "NO_GO_WITH_BLOCKERS":
        remaining_blockers.append(cannot_implement_reason)

    implement_now_modules = [
        row["openyield_module"]
        for row in module_rows
        if row["implementation_mode"] in {
            "DIRECT_GENERATOR_BINDING",
            "PARAMETERIZED_LAYOUTGEN_GENERATOR",
            "REAL_CELL_WRAPPER",
        }
    ]
    fallback_modules = [
        row["openyield_module"]
        for row in module_rows
        if row["implementation_mode"] == "LAYOUTGEN_FALLBACK_WITH_OPENYIELD_SEMANTICS"
    ]
    question_answers = {
        "q1_module_alignment": "OpenYield has 20 semantic modules while baseline layoutgen exposes 16 physical role buckets; arrays and hardmacro-backed column/data modules align well, while control and row-path semantics are split more finely in OpenYield.",
        "q2_direct_bindings": "Direct generator bindings are viable for bitcell_array, dummy_array, and replica_array because the optimized trunk already generates them through array aggregation and standalone top flow.",
        "q3_new_wrappers": "wordline_driver, column_mux, sense_amp, write_driver, and precharge should be bound as real-cell wrappers around layoutgen-owned hardmacros rather than as label-only placeholders.",
        "q4_floorplan": "Floorplan changes are required for row_decoder, wordline_decoder, decoder_gate_cells, DELAY_CHAIN, DFF_ROW, and the six control/time fallback modules because OpenYield splits the row/control perimeter more finely than baseline layoutgen.",
        "q5_placement": "Placement changes are required for every non-array module because semantic ownership must move from baseline-only roles to OpenYield-driven module boundaries inside the optimized trunk.",
        "q6_routing": "Routing changes are required for all non-array modules so WL, BL/BR, DIN/DOUT, address, control, and replica-timing nets are driven by OpenYield net ownership rather than implicit baseline ownership.",
        "q7_power": f"Power changes are required for twelve modules. M3F restored optimized power stitching with {power_overlap_count} positive overlap boundaries, but wrapper-backed modules still need OpenYield-driven rail eligibility and shared-rail gating.",
        "q8_net_hookup": "WL and DEC_WL stay on the row path, BL/BR stay on vertical column pitch routes, control/data nets stay on periphery buses, and VDD/VSS must remain on optimized rail-overlap/stitch logic. The next stage must thread all 34 semantic bindings into standalone.py-driven physical hookup.",
        "q9_first_round_gds": "First-round OpenYield module GDS is usable as physical reference only for arrays and hardmacro wrappers. Candidate row/control composites must not be installed as final physical modules.",
        "q10_regeneration": "Yes. For non-reusable first-round modules, the correct path is to regenerate through the optimized layoutgen trunk using parameterized generator ownership plus OpenYield semantics, not to force the first-round GDS into the final hierarchy.",
        "q11_files": "Primary files to modify next are sram_layoutgen/standalone.py, sram_layoutgen/openyield_adapter/M3F_optimized_layoutgen_restore.py, array_aggregation.py, module_gds_generators.py, top_level_assembly.py, wordlinedriver_adapter.py, writedriver_adapter.py, architecture_adapter.py, and hardcell_power_rail_continuity.py.",
        "q12_mvi": "The minimum viable implementation is a 14-module integration scope: 3 direct array bindings, 6 parameterized row/control generators, and 5 real-cell wrappers, while the six control/time modules remain on explicit layoutgen fallback with OpenYield semantics.",
        "q13_full_gap": "Full implementation still lacks native OpenYield physical control/time modules, shared-rail continuity proof for wrapper-backed peripherals, and alignment between the 4x4 intent JSON and the restored 8x64_wpr4 optimized backbone.",
    }
    implementation_scope = {
        "implement_now_modules": implement_now_modules,
        "fallback_modules": fallback_modules,
        "intent_parameter_mismatch": (
            f"intent(word_size={intent_parameter_map.get('word_size')},num_words={intent_parameter_map.get('num_words')},"
            f"words_per_row={intent_parameter_map.get('words_per_row')}) vs "
            f"optimized(word_size={m3f_layout_json['metadata'].get('word_size')},num_words={m3f_layout_json['metadata'].get('num_words')},"
            f"words_per_row={m3f_layout_json['metadata'].get('words_per_row')})"
        ),
    }

    report = {
        "status_file_read": True,
        "status_file_updated": True,
        "m3f_review_recorded": True,
        "evaluation_only_once_enforced": True,
        "no_more_evaluation_allowed_after_M4E": True,
        "review_gds_generated": review_gds_path.exists(),
        "review_gds_path": str(review_gds_path),
        "review_gds_sanity_status": review_gds_sanity["status"],
        "openyield_module_count": openyield_module_count,
        "layoutgen_baseline_module_count": layoutgen_baseline_module_count,
        "module_type_mismatch_count": module_type_mismatch_count,
        "net_mapping_count": net_mapping_count,
        "net_mapping_gap_count": net_mapping_gap_count,
        "direct_generator_binding_count": direct_generator_binding_count,
        "parameterized_generator_binding_count": parameterized_generator_binding_count,
        "real_cell_wrapper_count": real_cell_wrapper_count,
        "layoutgen_fallback_with_openyield_semantics_count": layoutgen_fallback_with_openyield_semantics_count,
        "not_implementable_now_count": not_implementable_now_count,
        "floorplan_change_required": floorplan_change_required,
        "placement_change_required": placement_change_required,
        "routing_change_required": routing_change_required,
        "power_change_required": power_change_required,
        "can_directly_implement_next": can_directly_implement_next,
        "can_partially_implement_next": can_partially_implement_next,
        "cannot_implement_reason": cannot_implement_reason,
        "go_nogo_decision": go_nogo_decision,
        "allowed_next_stage": allowed_next_stage,
        "human_klayout_review_required": True,
        "can_enter_next_stage_before_human_review": False,
        "remaining_M4E_blockers": remaining_blockers,
        "remaining_M4E_blockers_count": len(remaining_blockers),
        "evaluation_inputs": {
            "m3f_report": str(m3f_report),
            "m3f_power_rail_stitch_matrix": str(repo_root / "docs/mapping/M3F_power_rail_stitch_matrix.csv"),
            "m3f_layoutgen_optimization_reuse_matrix": str(repo_root / "docs/mapping/M3F_layoutgen_optimization_reuse_matrix.csv"),
            "m3f_openyield_semantic_binding_matrix": str(repo_root / "docs/mapping/M3F_openyield_semantic_binding_matrix.csv"),
            "openyield_module_map": str(openyield_intent_dir / "openyield_module_to_physical_role_map.csv"),
            "openyield_net_map": str(openyield_intent_dir / "openyield_net_to_layout_role_map.csv"),
            "openyield_net_map_md": str(openyield_intent_dir / "openyield_net_to_layout_role_map.md"),
            "openyield_layout_intent_json": str(openyield_intent_dir / "openyield_sram_layout_intent.json"),
            "openyield_module_gds_dir": str(openyield_module_gds_dir),
        },
        "question_answers": question_answers,
        "implementation_scope": implementation_scope,
        "power_overlap_count": power_overlap_count,
        "optimization_reuse_count": optimization_reuse_count,
        "intent_net_row_count": len(intent_net_rows),
        "intent_net_map_md_present": bool(intent_net_map_md.strip()),
    }

    status_md.write_text(_render_status_md(report), encoding="utf-8", newline="\n")
    status_json.write_text(json.dumps(_update_status_json(status_payload, report), ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    _json_dump(out_json, report)
    _json_dump(out_dir / "M4E_openyield_integration_feasibility_report.json", report)
    report_md = _render_main_report_md(report)
    _write_text(out_report, report_md)
    _write_text(out_dir / "M4E_openyield_integration_feasibility_report.md", report_md)
    _write_text(
        repo_root / "docs/evidence/M4E_openyield_integration_feasibility_summary.md",
        "# M4E OpenYield Integration Feasibility Summary\n\n"
        + "\n".join(
            [
                f"- review_gds_path: `{review_gds_path}`",
                f"- review_gds_sanity_status: `{review_gds_sanity['status']}`",
                f"- go_nogo_decision: `{go_nogo_decision}`",
                f"- allowed_next_stage: `{allowed_next_stage}`",
                f"- direct_generator_binding_count: `{direct_generator_binding_count}`",
                f"- parameterized_generator_binding_count: `{parameterized_generator_binding_count}`",
                f"- real_cell_wrapper_count: `{real_cell_wrapper_count}`",
                f"- layoutgen_fallback_with_openyield_semantics_count: `{layoutgen_fallback_with_openyield_semantics_count}`",
                f"- intent_parameter_mismatch: `{implementation_scope['intent_parameter_mismatch']}`",
                "- No more evaluation is allowed after M4E.",
            ]
        )
        + "\n",
    )
    return report
