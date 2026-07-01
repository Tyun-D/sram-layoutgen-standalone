"""OpenYield L1 physical primitive closure helpers.

This module converts the frozen L0 semantic contracts into a concrete L1 leaf
primitive inventory.  It stays readonly with respect to physical generation:
the goal is to classify what already exists locally, what is generator-backed,
and what still has only source/candidate/fallback evidence.
"""

from __future__ import annotations

import csv
import importlib.util
import json
import math
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from sram_layoutgen.gds_util import inspect_gds_layers, inspect_gds_text_records, measure_gds_bbox
from sram_layoutgen.stdcell import GENERATED_CELLS

from .module_semantics import render_markdown_table, write_csv, write_text


LOCAL_SOURCE_TYPES = {
    "EXISTING_GDS",
    "HARDMACRO_GDS",
    "PYTHON_GENERATOR",
    "CANDIDATE_SPICE_ONLY",
    "SOURCE_ONLY",
    "METADATA_ONLY",
    "FALLBACK_ONLY",
    "MISSING",
}

READINESS_LEVELS = {
    "LEAF_GDS_READY",
    "HARDMACRO_GDS_READY",
    "PYTHON_GENERATOR_READY",
    "GDS_EXISTS_NEEDS_PIN_RAIL_EXTRACTION",
    "GDS_EXISTS_NEEDS_ABUTMENT_RULE",
    "SPICE_ONLY_NEEDS_LAYOUT_GENERATOR",
    "SOURCE_ONLY_NEEDS_PHYSICAL_GENERATOR",
    "METADATA_ONLY_NEEDS_PHYSICAL_SOURCE",
    "FALLBACK_ONLY",
    "MISSING_PHYSICAL_SOURCE",
    "BLOCKED",
}

PRIMITIVE_COLUMNS = [
    "primitive_name",
    "primitive_category",
    "required_by_modules",
    "openyield_source_found",
    "openyield_source_path",
    "openyield_class_or_function",
    "ports_or_nodes_known",
    "transistor_sizing_known",
    "local_physical_source_type",
    "local_physical_source_path",
    "existing_gds_found",
    "python_generator_found",
    "candidate_spice_found",
    "bbox_known",
    "pin_labels_known",
    "vdd_gnd_pins_known",
    "rail_geometry_known",
    "left_right_abutment_rule",
    "top_bottom_abutment_rule",
    "orientation_policy",
    "row_height_or_pitch_known",
    "pdk_drc_rule_source_known",
    "usable_for_module_gds_generation",
    "usable_for_top_level_gds_generation",
    "readiness_level",
    "blocking_gap",
    "next_required_action",
    "evidence_files",
]

MODULE_DEP_COLUMNS = [
    "module",
    "required_primitives",
    "ready_primitives",
    "not_ready_primitives",
    "all_primitives_ready",
    "module_can_generate_standalone_gds_now",
    "module_can_generate_top_level_gds_now",
    "blocking_primitive_gaps",
    "next_required_action",
    "evidence_files",
]

DEFAULT_REQUIRED_MODULES = [
    "SRAM_TOP",
    "BANK",
    "bitcell_array",
    "dummy_array",
    "replica_array",
    "row_decoder",
    "wordline_decoder",
    "decoder_gate_cells",
    "wordline_driver",
    "wordline_driver_gate_cells",
    "column_mux",
    "sense_amp",
    "write_driver",
    "precharge",
    "DELAY_CHAIN",
    "PRECHARGE_ENABLE_PATH",
    "SENSE_ENABLE_PATH",
    "WRITE_ENABLE_PATH",
    "WORDLINE_ENABLE_PATH",
    "GATED_CLOCK_PATH",
    "DFF_ROW",
    "CONTROL_LOGIC",
    "routing_semantics",
    "power_semantics",
    "timing_semantics",
]


@dataclass(frozen=True)
class PrimitiveSpec:
    primitive_name: str
    primitive_category: str
    required_by_modules: tuple[str, ...]
    openyield_source_path: str
    openyield_class_or_function: str
    ports_or_nodes_known: bool
    transistor_sizing_known: bool
    local_macro_candidates: tuple[str, ...] = ()
    preferred_local_macro: str | None = None
    python_generator_macro: str | None = None
    candidate_spice_patterns: tuple[str, ...] = ()
    fallback_source_path: str | None = None
    metadata_source_path: str | None = None
    ports_hint: str = ""
    notes: str = ""


PRIMITIVE_SPECS: tuple[PrimitiveSpec, ...] = (
    PrimitiveSpec(
        "bitcell",
        "storage_cell",
        ("SRAM_TOP", "BANK", "bitcell_array", "routing_semantics", "power_semantics"),
        "sram_compiler/subcircuits/sram_6t_core.py",
        "Sram6TCell",
        True,
        True,
        local_macro_candidates=("cell_1rw",),
        preferred_local_macro="cell_1rw",
        ports_hint="VDD,VSS,BL,BLB,WL",
    ),
    PrimitiveSpec(
        "dummy_cell",
        "storage_cell",
        ("SRAM_TOP", "BANK", "dummy_array", "power_semantics"),
        "sram_compiler/subcircuits/dummy_row_or_column.py",
        "Dummy_Cell/Dummy_Row/Dummy_Column",
        True,
        True,
        local_macro_candidates=("dummy_cell_1rw",),
        preferred_local_macro="dummy_cell_1rw",
        ports_hint="VDD,VSS,BL,BLB,WL",
    ),
    PrimitiveSpec(
        "replica_cell",
        "storage_cell",
        ("SRAM_TOP", "BANK", "replica_array", "timing_semantics", "power_semantics"),
        "sram_compiler/subcircuits/replica_column.py",
        "Replica_Cell",
        True,
        True,
        local_macro_candidates=("replica_cell_1rw",),
        preferred_local_macro="replica_cell_1rw",
        ports_hint="VDD,VSS,RBL,RBLB,WL",
    ),
    PrimitiveSpec(
        "inv",
        "standard_cell",
        ("row_decoder", "wordline_decoder", "decoder_gate_cells", "PRECHARGE_ENABLE_PATH", "SENSE_ENABLE_PATH", "WRITE_ENABLE_PATH", "WORDLINE_ENABLE_PATH", "GATED_CLOCK_PATH", "CONTROL_LOGIC", "timing_semantics", "power_semantics"),
        "sram_compiler/subcircuits/standard_cell.py",
        "Pinv",
        True,
        True,
        local_macro_candidates=("gen_inv", "openram_replacements/gen_inv"),
        preferred_local_macro="openram_replacements/gen_inv",
        python_generator_macro="gen_inv",
        ports_hint="VDD,VSS,A,Z",
    ),
    PrimitiveSpec(
        "delay_inv",
        "timing_buffer",
        ("DELAY_CHAIN", "WRITE_ENABLE_PATH", "CONTROL_LOGIC", "timing_semantics", "SRAM_TOP", "BANK"),
        "sram_compiler/subcircuits/time_generate.py;sram_compiler/subcircuits/standard_cell.py",
        "DelayChain/WenDelayChain + Pinv",
        True,
        True,
        local_macro_candidates=("gen_delay_inv", "openram_replacements/gen_delay_inv"),
        preferred_local_macro="openram_replacements/gen_delay_inv",
        python_generator_macro="gen_delay_inv",
        candidate_spice_patterns=("gen_delay_inv_candidate.sp", "delay_chain"),
        ports_hint="VDD,VSS,A,Z",
    ),
    PrimitiveSpec(
        "nand2",
        "standard_cell",
        ("wordline_driver", "wordline_driver_gate_cells", "GATED_CLOCK_PATH", "CONTROL_LOGIC", "decoder_leaf_gate", "wordline_driver_leaf_gate", "gated_clock_leaf_gate", "control_logic_leaf_gate"),
        "sram_compiler/subcircuits/standard_cell.py",
        "PNAND2",
        True,
        True,
        local_macro_candidates=("gen_nand2", "openram_replacements/gen_nand2"),
        preferred_local_macro="openram_replacements/gen_nand2",
        python_generator_macro="gen_nand2",
        ports_hint="VDD,VSS,A,B,Z",
    ),
    PrimitiveSpec(
        "nand3",
        "standard_cell",
        ("row_decoder", "wordline_decoder", "PRECHARGE_ENABLE_PATH", "SENSE_ENABLE_PATH", "WRITE_ENABLE_PATH", "CONTROL_LOGIC", "timing_semantics"),
        "sram_compiler/subcircuits/standard_cell.py",
        "PNAND3",
        True,
        True,
        ports_hint="VDD,VSS,A,B,C,Z",
    ),
    PrimitiveSpec(
        "nand4",
        "standard_cell",
        (),
        "not_found_in_openyield_source",
        "not_found_in_openyield_source",
        False,
        False,
        local_macro_candidates=("gen_nand4",),
        preferred_local_macro="gen_nand4",
        python_generator_macro="gen_nand4",
        ports_hint="VDD,VSS,A,B,C,D,Z",
        notes="Local layoutgen fallback only; not referenced by current OpenYield L0 contracts.",
    ),
    PrimitiveSpec(
        "nor2",
        "standard_cell",
        (),
        "not_found_in_openyield_source",
        "not_found_in_openyield_source",
        False,
        False,
        local_macro_candidates=("gen_nor2",),
        preferred_local_macro="gen_nor2",
        python_generator_macro="gen_nor2",
        ports_hint="VDD,VSS,A,B,Z",
        notes="Local layoutgen fallback only; not referenced by current OpenYield L0 contracts.",
    ),
    PrimitiveSpec(
        "nor3",
        "standard_cell",
        (),
        "not_found_in_openyield_source",
        "not_found_in_openyield_source",
        False,
        False,
        ports_hint="VDD,VSS,A,B,C,Z",
        notes="No local OpenYield-backed or layoutgen-backed source found.",
    ),
    PrimitiveSpec(
        "and2",
        "compound_gate",
        ("GATED_CLOCK_PATH", "CONTROL_LOGIC"),
        "sram_compiler/subcircuits/standard_cell.py",
        "AND2",
        True,
        True,
        fallback_source_path="sram_layoutgen/stdcell.py::gen_nand2 + gen_inv composition",
        ports_hint="VDD,VSS,A,B,Z",
    ),
    PrimitiveSpec(
        "and3",
        "compound_gate",
        ("row_decoder", "wordline_decoder", "PRECHARGE_ENABLE_PATH", "SENSE_ENABLE_PATH", "WRITE_ENABLE_PATH", "CONTROL_LOGIC", "gated_clock_leaf_gate", "enable_path_leaf_gate", "control_logic_leaf_gate"),
        "sram_compiler/subcircuits/standard_cell.py",
        "AND3",
        True,
        True,
        ports_hint="VDD,VSS,A,B,C,Z",
    ),
    PrimitiveSpec(
        "or2",
        "compound_gate",
        (),
        "not_found_in_openyield_source",
        "not_found_in_openyield_source",
        False,
        False,
        ports_hint="VDD,VSS,A,B,Z",
    ),
    PrimitiveSpec(
        "or3",
        "compound_gate",
        (),
        "not_found_in_openyield_source",
        "not_found_in_openyield_source",
        False,
        False,
        ports_hint="VDD,VSS,A,B,C,Z",
    ),
    PrimitiveSpec(
        "buffer",
        "buffer",
        ("WORDLINE_ENABLE_PATH", "CONTROL_LOGIC", "gated_clock_leaf_gate"),
        "sram_compiler/subcircuits/standard_cell.py;sram_compiler/subcircuits/time_generate.py",
        "Pbuff/pdrive/wl_pdrive/pdrive2_for_pre",
        True,
        True,
        fallback_source_path="sram_layoutgen/stdcell.py::gen_inv chain",
        ports_hint="VDD,VSS,A,Z",
    ),
    PrimitiveSpec(
        "precharge_cell",
        "peripheral_cell",
        ("SRAM_TOP", "BANK", "precharge", "replica_array", "PRECHARGE_ENABLE_PATH", "routing_semantics", "power_semantics", "timing_semantics"),
        "sram_compiler/subcircuits/precharge_and_write_driver.py",
        "Precharge",
        True,
        True,
        local_macro_candidates=("gen_precharge", "openram_replacements/gen_precharge"),
        preferred_local_macro="openram_replacements/gen_precharge",
        python_generator_macro="gen_precharge",
        candidate_spice_patterns=("precharge_candidate", "precharge_smoke"),
        ports_hint="VDD,ENB,BL,BLB",
    ),
    PrimitiveSpec(
        "dff_cell",
        "sequential_cell",
        ("SRAM_TOP", "BANK", "DFF_ROW", "CONTROL_LOGIC", "GATED_CLOCK_PATH", "timing_semantics"),
        "sram_compiler/subcircuits/time_generate.py",
        "dff/DFF_BUF/ADDR_DFF/DATA_DFF",
        True,
        True,
        local_macro_candidates=("dff",),
        preferred_local_macro="dff",
        ports_hint="VDD,VSS,D,Q,CLK",
    ),
    PrimitiveSpec(
        "sense_amp",
        "peripheral_cell",
        ("SRAM_TOP", "BANK", "sense_amp", "SENSE_ENABLE_PATH", "routing_semantics", "timing_semantics", "power_semantics"),
        "sram_compiler/subcircuits/mux_and_sa.py",
        "SenseAmp",
        True,
        True,
        local_macro_candidates=("sense_amp",),
        preferred_local_macro="sense_amp",
        ports_hint="VDD,VSS,EN,IN,INB,Q,QB",
    ),
    PrimitiveSpec(
        "write_driver",
        "peripheral_cell",
        ("SRAM_TOP", "BANK", "write_driver", "WRITE_ENABLE_PATH", "routing_semantics", "timing_semantics", "power_semantics"),
        "sram_compiler/subcircuits/precharge_and_write_driver.py",
        "WriteDriver",
        True,
        True,
        local_macro_candidates=("write_driver",),
        preferred_local_macro="write_driver",
        ports_hint="VDD,VSS,EN,DIN,BL,BLB",
    ),
    PrimitiveSpec(
        "column_mux",
        "peripheral_cell",
        ("SRAM_TOP", "BANK", "column_mux", "routing_semantics", "timing_semantics", "power_semantics"),
        "sram_compiler/subcircuits/mux_and_sa.py",
        "ColumnMux",
        True,
        True,
        local_macro_candidates=("gen_col_mux", "openram_replacements/gen_col_mux", "openyield_repaired/gen_col_mux_vdd_labeled"),
        preferred_local_macro="openyield_repaired/gen_col_mux_vdd_labeled",
        python_generator_macro="gen_col_mux",
        ports_hint="VDD,VSS,SA_IN,SA_INB,SELx,BLx,BLBx",
    ),
    PrimitiveSpec(
        "wordline_driver",
        "peripheral_cell",
        ("SRAM_TOP", "BANK", "wordline_driver", "wordline_driver_gate_cells", "routing_semantics", "timing_semantics", "power_semantics"),
        "sram_compiler/subcircuits/wordline_driver.py",
        "WordlineDriver",
        True,
        True,
        local_macro_candidates=("gen_wl_driver", "openram_replacements/gen_wl_driver"),
        preferred_local_macro="openram_replacements/gen_wl_driver",
        python_generator_macro="gen_wl_driver",
        ports_hint="VDD,VSS,A,B,Z",
    ),
    PrimitiveSpec(
        "decoder_leaf_gate",
        "leaf_gate_group",
        ("row_decoder", "decoder_gate_cells"),
        "sram_compiler/subcircuits/decoder.py;sram_compiler/subcircuits/standard_cell.py",
        "DECODER3_8/DECODER_CASCADE + Pinv/AND2/AND3",
        True,
        True,
        fallback_source_path="docs/mapping/openyield_decoder_wordline_semantic_contract.md",
        metadata_source_path="docs/mapping/openyield_decoder_wordline_semantic_contract.json",
        ports_hint="A_dff -> decode leaves -> WL_pre/WL",
    ),
    PrimitiveSpec(
        "wordline_decoder_leaf_gate",
        "leaf_gate_group",
        ("wordline_decoder",),
        "sram_compiler/subcircuits/decoder.py",
        "DECODER_CASCADE",
        True,
        True,
        fallback_source_path="docs/mapping/openyield_decoder_wordline_semantic_contract.md",
        metadata_source_path="docs/mapping/openyield_decoder_wordline_semantic_contract.json",
        ports_hint="A_dff -> DEC_WL",
    ),
    PrimitiveSpec(
        "wordline_driver_leaf_gate",
        "leaf_gate_group",
        ("wordline_driver_gate_cells",),
        "sram_compiler/subcircuits/wordline_driver.py",
        "WordlineDriver + PNAND2 + Pinv",
        True,
        True,
        fallback_source_path="sram_layoutgen/stdcell.py::gen_wl_driver",
        ports_hint="A,B -> Z",
    ),
    PrimitiveSpec(
        "enable_path_leaf_gate",
        "leaf_gate_group",
        ("PRECHARGE_ENABLE_PATH", "SENSE_ENABLE_PATH", "WRITE_ENABLE_PATH", "WORDLINE_ENABLE_PATH"),
        "sram_compiler/subcircuits/time_generate.py",
        "wl_pdrive/pdrive2_for_pre/AND3/Pinv/WenDelayChain",
        True,
        True,
        candidate_spice_patterns=("precharge_enable", "sense_enable_path", "wordline_enable_path", "write_enable_path"),
        metadata_source_path="docs/mapping/openyield_control_path_semantic_contracts.csv",
        ports_hint="control inputs -> WL_EN/PRE/S_EN/W_EN",
    ),
    PrimitiveSpec(
        "gated_clock_leaf_gate",
        "leaf_gate_group",
        ("GATED_CLOCK_PATH",),
        "sram_compiler/subcircuits/time_generate.py",
        "clkbuf/Pinv/AND2",
        True,
        True,
        candidate_spice_patterns=("gated_clock_path",),
        metadata_source_path="docs/mapping/openyield_control_path_semantic_contracts.csv",
        ports_hint="clk/cs -> gated_clk_buf/gated_clk_bar",
    ),
    PrimitiveSpec(
        "control_logic_leaf_gate",
        "leaf_gate_group",
        ("CONTROL_LOGIC",),
        "sram_compiler/subcircuits/time_generate.py",
        "TIME composite leafs",
        True,
        True,
        candidate_spice_patterns=("dff_row_candidate_contract",),
        metadata_source_path="docs/mapping/openyield_time_control_decomposition_contract.json",
        ports_hint="clk/csb/web/address/data -> internal control enables",
    ),
)


MODULE_TO_PRIMITIVES: dict[str, list[str]] = {
    "SRAM_TOP": ["bitcell", "dummy_cell", "replica_cell", "precharge_cell", "column_mux", "sense_amp", "write_driver", "wordline_driver", "dff_cell", "delay_inv", "inv", "nand2", "nand3", "and3"],
    "BANK": ["bitcell", "dummy_cell", "replica_cell", "precharge_cell", "column_mux", "sense_amp", "write_driver", "wordline_driver", "dff_cell", "delay_inv", "inv", "nand2", "nand3", "and3"],
    "bitcell_array": ["bitcell"],
    "dummy_array": ["dummy_cell"],
    "replica_array": ["replica_cell", "precharge_cell"],
    "row_decoder": ["inv", "nand3", "and3", "decoder_leaf_gate"],
    "wordline_decoder": ["inv", "nand3", "and3", "wordline_decoder_leaf_gate"],
    "decoder_gate_cells": ["inv", "nand3", "and2", "and3", "decoder_leaf_gate"],
    "wordline_driver": ["wordline_driver", "nand2", "inv"],
    "wordline_driver_gate_cells": ["wordline_driver_leaf_gate", "nand2", "inv"],
    "column_mux": ["column_mux"],
    "sense_amp": ["sense_amp"],
    "write_driver": ["write_driver"],
    "precharge": ["precharge_cell"],
    "DELAY_CHAIN": ["delay_inv"],
    "PRECHARGE_ENABLE_PATH": ["enable_path_leaf_gate", "nand3", "buffer", "precharge_cell"],
    "SENSE_ENABLE_PATH": ["enable_path_leaf_gate", "nand3", "buffer"],
    "WRITE_ENABLE_PATH": ["enable_path_leaf_gate", "nand3", "delay_inv"],
    "WORDLINE_ENABLE_PATH": ["enable_path_leaf_gate", "buffer", "inv"],
    "GATED_CLOCK_PATH": ["gated_clock_leaf_gate", "dff_cell", "and2", "inv"],
    "DFF_ROW": ["dff_cell"],
    "CONTROL_LOGIC": ["control_logic_leaf_gate", "dff_cell", "delay_inv", "buffer", "nand3", "and2", "and3", "inv"],
    "routing_semantics": ["bitcell", "precharge_cell", "column_mux", "sense_amp", "write_driver", "wordline_driver"],
    "power_semantics": ["bitcell", "dummy_cell", "replica_cell", "dff_cell", "inv", "nand2", "delay_inv", "precharge_cell", "column_mux", "sense_amp", "write_driver", "wordline_driver"],
    "timing_semantics": ["dff_cell", "delay_inv", "buffer", "nand3", "and3", "precharge_cell", "sense_amp", "write_driver", "wordline_driver"],
}


def load_json(path: str | Path) -> dict[str, Any]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def load_csv_rows(path: str | Path) -> list[dict[str, str]]:
    with Path(path).open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def build_l1_physical_primitive_report(
    repo_root: str | Path,
    openyield_root: str | Path,
    l0_contract_json: str | Path,
    l0_control_contracts: str | Path,
    l0_time_contract: str | Path,
    l0_decoder_contract: str | Path,
) -> dict[str, Any]:
    repo = Path(repo_root).resolve()
    openyield = Path(openyield_root).resolve()
    canonical = load_json(repo / l0_contract_json)
    time_contract = load_json(repo / l0_time_contract)
    decoder_contract = load_json(repo / l0_decoder_contract)
    control_rows = load_csv_rows(repo / l0_control_contracts)

    required_modules = list(DEFAULT_REQUIRED_MODULES)
    rows = build_primitive_rows(repo, openyield)
    module_rows = build_module_dependency_rows(rows, required_modules)
    report = build_report(repo, openyield, canonical, time_contract, decoder_contract, control_rows, rows, module_rows)
    return {
        "primitive_rows": rows,
        "module_dependency_rows": module_rows,
        "report": report,
        "leaf_library": build_leaf_library_json(repo, rows),
    }


def build_primitive_rows(repo: Path, openyield_root: Path) -> list[dict[str, Any]]:
    candidate_files = _candidate_spice_index(repo)
    rows: list[dict[str, Any]] = []
    for spec in PRIMITIVE_SPECS:
        source_found = spec.openyield_source_path != "not_found_in_openyield_source" and all(
            (openyield_root / part).exists() for part in spec.openyield_source_path.split(";")
        )
        candidate_matches = [str(path.relative_to(repo)).replace("\\", "/") for path in candidate_files if any(pattern in path.name or pattern in str(path) for pattern in spec.candidate_spice_patterns)]
        gds_info = _resolve_local_macro(repo, spec)
        generator_found = bool(spec.python_generator_macro and spec.python_generator_macro in GENERATED_CELLS)

        local_source_type = _classify_local_source_type(spec, gds_info, generator_found, candidate_matches)
        bbox_known = bool(gds_info.get("bbox_known") or generator_found)
        pin_labels_known = bool(gds_info.get("pin_labels_known") or generator_found)
        vdd_gnd_known = bool(gds_info.get("vdd_gnd_pins_known") or generator_found)
        rail_known = bool(gds_info.get("rail_geometry_known") or generator_found)
        left_rule, top_rule, orientation = _abutment_policy(spec, gds_info, generator_found)
        readiness = _classify_readiness(spec, local_source_type, gds_info, generator_found)
        usable_module = readiness in {"LEAF_GDS_READY", "HARDMACRO_GDS_READY", "PYTHON_GENERATOR_READY"} and spec.primitive_name not in {
            "precharge_cell",
            "decoder_leaf_gate",
            "wordline_decoder_leaf_gate",
            "wordline_driver_leaf_gate",
            "enable_path_leaf_gate",
            "gated_clock_leaf_gate",
            "control_logic_leaf_gate",
        }
        usable_top = usable_module and not (
            "manual" in left_rule.lower()
            or "manual" in top_rule.lower()
            or "pending" in left_rule.lower()
            or "pending" in top_rule.lower()
        )
        blocking_gap = _blocking_gap(spec, local_source_type, gds_info, generator_found)
        next_action = _next_action(spec, local_source_type, readiness, blocking_gap)
        evidence_files = _evidence_files(spec, gds_info, candidate_matches)

        rows.append({
            "primitive_name": spec.primitive_name,
            "primitive_category": spec.primitive_category,
            "required_by_modules": ";".join(spec.required_by_modules),
            "openyield_source_found": source_found,
            "openyield_source_path": spec.openyield_source_path,
            "openyield_class_or_function": spec.openyield_class_or_function,
            "ports_or_nodes_known": spec.ports_or_nodes_known,
            "transistor_sizing_known": spec.transistor_sizing_known,
            "local_physical_source_type": local_source_type,
            "local_physical_source_path": gds_info.get("local_source_path") or spec.fallback_source_path or spec.metadata_source_path or "",
            "existing_gds_found": bool(gds_info.get("existing_gds_found")),
            "python_generator_found": generator_found,
            "candidate_spice_found": bool(candidate_matches),
            "bbox_known": bbox_known,
            "pin_labels_known": pin_labels_known,
            "vdd_gnd_pins_known": vdd_gnd_known,
            "rail_geometry_known": rail_known,
            "left_right_abutment_rule": left_rule,
            "top_bottom_abutment_rule": top_rule,
            "orientation_policy": orientation,
            "row_height_or_pitch_known": bool(gds_info.get("row_height_or_pitch_known") or generator_found),
            "pdk_drc_rule_source_known": True,
            "usable_for_module_gds_generation": usable_module,
            "usable_for_top_level_gds_generation": usable_top,
            "readiness_level": readiness,
            "blocking_gap": blocking_gap,
            "next_required_action": next_action,
            "evidence_files": ";".join(evidence_files),
        })
    return rows


def build_module_dependency_rows(
    primitive_rows: list[dict[str, Any]],
    required_modules: list[str],
) -> list[dict[str, Any]]:
    primitive_by_name = {row["primitive_name"]: row for row in primitive_rows}
    ready_for_module_levels = {"LEAF_GDS_READY", "HARDMACRO_GDS_READY", "PYTHON_GENERATOR_READY"}
    ready_for_l2_source_types = {"EXISTING_GDS", "HARDMACRO_GDS", "PYTHON_GENERATOR", "FALLBACK_ONLY"}
    rows: list[dict[str, Any]] = []
    for module in required_modules:
        primitives = MODULE_TO_PRIMITIVES.get(module, [])
        ready = []
        not_ready = []
        can_top = True
        blockers = []
        for name in primitives:
            row = primitive_by_name[name]
            if row["readiness_level"] in ready_for_module_levels:
                ready.append(name)
            else:
                not_ready.append(name)
                blockers.append(f"{name}:{row['readiness_level']}")
            if not row["usable_for_top_level_gds_generation"]:
                can_top = False
        all_ready = all(primitive_by_name[name]["local_physical_source_type"] in ready_for_l2_source_types for name in primitives)
        module_standalone = all(primitive_by_name[name]["usable_for_module_gds_generation"] for name in primitives) if primitives else False
        module_top = module_standalone and can_top
        rows.append({
            "module": module,
            "required_primitives": ";".join(primitives),
            "ready_primitives": ";".join(sorted(ready)),
            "not_ready_primitives": ";".join(sorted(not_ready)),
            "all_primitives_ready": all_ready,
            "module_can_generate_standalone_gds_now": module_standalone,
            "module_can_generate_top_level_gds_now": module_top,
            "blocking_primitive_gaps": ";".join(blockers),
            "next_required_action": (
                "Proceed to L2 abutment/rail closure."
                if module_top
                else "Resolve primitive physical source or fallback first."
                if not all_ready
                else "Primitive inventory exists, but module still needs L2/L3 abutment or composition closure."
            ),
            "evidence_files": _module_evidence_files(primitives, primitive_by_name),
        })
    return rows


def build_report(
    repo: Path,
    openyield_root: Path,
    canonical_contract: dict[str, Any],
    time_contract: dict[str, Any],
    decoder_contract: dict[str, Any],
    control_rows: list[dict[str, str]],
    primitive_rows: list[dict[str, Any]],
    module_rows: list[dict[str, Any]],
) -> dict[str, Any]:
    gate = build_gate_summary(primitive_rows, module_rows)
    report = {
        "scope": "L1_openyield_physical_primitive_closure_first_pass",
        "repo_root": str(repo),
        "openyield_root": str(openyield_root),
        "canonical_contract_scope": canonical_contract.get("scope", {}),
        "time_control_objects": [item.get("semantic_object") for item in control_rows],
        "decoder_contract_leaves": decoder_contract.get("leaf_contracts", []),
        "primitive_rows": primitive_rows,
        "module_dependency_rows": module_rows,
        **gate,
        "summary": {
            "question_1_total_primitives": len(primitive_rows),
            "question_2_existing_gds": gate["existing_gds_primitives"] + gate["hardmacro_gds_primitives"],
            "question_3_python_generators": gate["python_generator_primitives"],
            "question_4_candidate_spice_only": gate["candidate_spice_only_primitives"],
            "question_5_source_only": gate["source_only_primitives"],
            "question_6_metadata_or_fallback_only": gate["metadata_only_primitives"] + gate["fallback_only_primitives"],
            "question_7_missing_physical_source": gate["missing_physical_source_primitives"],
            "question_8_pin_bbox_rail_incomplete": gate["pin_bbox_rail_incomplete_primitives"],
            "question_9_abutment_rule_incomplete": gate["abutment_rule_incomplete_primitives"],
            "question_10_modules_standalone_gds": gate["modules_can_generate_standalone_gds_now"],
            "question_11_modules_blocked": gate["modules_blocked_from_standalone_gds"],
            "question_12_l2_missing": gate["remaining_L1_blockers"],
            "question_13_can_enter_L2": gate["can_enter_L2_placement_abutment_rule_closure"],
            "question_14_can_enter_L3": gate["can_enter_L3_module_gds_generation"],
        },
    }
    return report


def build_leaf_library_json(repo: Path, primitive_rows: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "library_name": "openyield_leaf_physical_library",
        "technology": "freepdk45",
        "primitive_count": len(primitive_rows),
        "primitives": [
            {
                "name": row["primitive_name"],
                "category": row["primitive_category"],
                "local_physical_source_type": row["local_physical_source_type"],
                "local_physical_source_path": row["local_physical_source_path"],
                "readiness_level": row["readiness_level"],
                "bbox_known": row["bbox_known"],
                "pin_labels_known": row["pin_labels_known"],
                "vdd_gnd_pins_known": row["vdd_gnd_pins_known"],
                "rail_geometry_known": row["rail_geometry_known"],
                "usable_for_module_gds_generation": row["usable_for_module_gds_generation"],
                "usable_for_top_level_gds_generation": row["usable_for_top_level_gds_generation"],
                "evidence_files": row["evidence_files"].split(";") if row["evidence_files"] else [],
            }
            for row in primitive_rows
        ],
        "source_notes": [
            "L1 first pass is readonly and does not generate new GDS.",
            "Rows may prefer OpenRAM replacement or repaired macros when default gds_lib labels are incomplete.",
            "Composite control-leaf groups remain metadata/fallback classifications unless a concrete local leaf macro exists.",
        ],
    }


def build_gate_summary(primitive_rows: list[dict[str, Any]], module_rows: list[dict[str, Any]]) -> dict[str, Any]:
    existing = [row["primitive_name"] for row in primitive_rows if row["local_physical_source_type"] == "EXISTING_GDS"]
    hardmacro = [row["primitive_name"] for row in primitive_rows if row["local_physical_source_type"] == "HARDMACRO_GDS"]
    pygen = [row["primitive_name"] for row in primitive_rows if row["local_physical_source_type"] == "PYTHON_GENERATOR"]
    spice = [row["primitive_name"] for row in primitive_rows if row["local_physical_source_type"] == "CANDIDATE_SPICE_ONLY"]
    source = [row["primitive_name"] for row in primitive_rows if row["local_physical_source_type"] == "SOURCE_ONLY"]
    meta = [row["primitive_name"] for row in primitive_rows if row["local_physical_source_type"] == "METADATA_ONLY"]
    fallback = [row["primitive_name"] for row in primitive_rows if row["local_physical_source_type"] == "FALLBACK_ONLY"]
    missing = [row["primitive_name"] for row in primitive_rows if row["local_physical_source_type"] == "MISSING"]

    pin_bbox_rail_incomplete = [
        row["primitive_name"]
        for row in primitive_rows
        if not (row["bbox_known"] and row["pin_labels_known"] and row["vdd_gnd_pins_known"] and row["rail_geometry_known"])
    ]
    abutment_incomplete = [
        row["primitive_name"]
        for row in primitive_rows
        if "manual" in row["left_right_abutment_rule"].lower()
        or "manual" in row["top_bottom_abutment_rule"].lower()
        or "pending" in row["left_right_abutment_rule"].lower()
        or "pending" in row["top_bottom_abutment_rule"].lower()
        or row["readiness_level"] in {
            "GDS_EXISTS_NEEDS_ABUTMENT_RULE",
            "GDS_EXISTS_NEEDS_PIN_RAIL_EXTRACTION",
        }
    ]
    modules_standalone = [row["module"] for row in module_rows if row["module_can_generate_standalone_gds_now"]]
    modules_blocked = [row["module"] for row in module_rows if not row["module_can_generate_standalone_gds_now"]]
    modules_top = [row["module"] for row in module_rows if row["module_can_generate_top_level_gds_now"]]
    modules_top_blocked = [row["module"] for row in module_rows if not row["module_can_generate_top_level_gds_now"]]

    required_primitive_rows = [row for row in primitive_rows if row["required_by_modules"]]
    unsupported_sources = {"SOURCE_ONLY", "CANDIDATE_SPICE_ONLY", "METADATA_ONLY", "MISSING"}
    remaining_blockers = [
        f"{row['primitive_name']}:{row['local_physical_source_type']}:{row['blocking_gap']}"
        for row in required_primitive_rows
        if row["local_physical_source_type"] in unsupported_sources
    ]

    can_l1 = len(remaining_blockers) == 0
    return {
        "physical_primitive_closure_available": True,
        "leaf_physical_readiness_matrix_available": True,
        "module_to_primitive_dependency_matrix_available": True,
        "leaf_physical_library_available": True,
        "primitive_rows_count": len(primitive_rows),
        "module_dependency_rows_count": len(module_rows),
        "existing_gds_primitives": sorted(existing),
        "hardmacro_gds_primitives": sorted(hardmacro),
        "python_generator_primitives": sorted(pygen),
        "candidate_spice_only_primitives": sorted(spice),
        "source_only_primitives": sorted(source),
        "metadata_only_primitives": sorted(meta),
        "fallback_only_primitives": sorted(fallback),
        "missing_physical_source_primitives": sorted(missing),
        "pin_bbox_rail_incomplete_primitives": sorted(pin_bbox_rail_incomplete),
        "abutment_rule_incomplete_primitives": sorted(abutment_incomplete),
        "modules_can_generate_standalone_gds_now": sorted(modules_standalone),
        "modules_blocked_from_standalone_gds": sorted(modules_blocked),
        "modules_can_generate_top_level_gds_now": sorted(modules_top),
        "modules_blocked_from_top_level_gds": sorted(modules_top_blocked),
        "remaining_L1_blockers": sorted(remaining_blockers),
        "remaining_L1_blockers_count": len(remaining_blockers),
        "can_claim_L1_physical_primitives_closed_now": can_l1,
        "can_enter_L2_placement_abutment_rule_closure": can_l1,
        "can_enter_L3_module_gds_generation": False,
        "can_claim_full_openyield_gds_now": False,
        "can_claim_drc_clean_now": False,
        "can_claim_lvs_clean_now": False,
        "can_claim_timing_closure_now": False,
    }


def write_l1_outputs(
    out_csv: str | Path,
    out_md: str | Path,
    out_module_csv: str | Path,
    out_module_md: str | Path,
    out_json: str | Path,
    out_report: str | Path,
    library_json: str | Path,
    primitive_rows: list[dict[str, Any]],
    module_rows: list[dict[str, Any]],
    report: dict[str, Any],
    leaf_library: dict[str, Any],
) -> None:
    write_csv(out_csv, primitive_rows, PRIMITIVE_COLUMNS)
    write_text(out_md, render_markdown_table(primitive_rows, PRIMITIVE_COLUMNS))
    write_csv(out_module_csv, module_rows, MODULE_DEP_COLUMNS)
    write_text(out_module_md, render_markdown_table(module_rows, MODULE_DEP_COLUMNS))
    Path(out_json).write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    write_text(out_report, render_report_md(report))
    Path(library_json).write_text(json.dumps(leaf_library, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def render_report_md(report: dict[str, Any]) -> str:
    summary = report["summary"]
    return "\n".join(
        [
            "# OpenYield Physical Primitive Closure Report",
            "",
            "This is the first L1 pass. It inventories leaf physical evidence but does not modify placement, routing, or module GDS generation.",
            "",
            "## Gates",
            "",
            f"- primitive_rows_count: `{report['primitive_rows_count']}`",
            f"- module_dependency_rows_count: `{report['module_dependency_rows_count']}`",
            f"- can_claim_L1_physical_primitives_closed_now: `{report['can_claim_L1_physical_primitives_closed_now']}`",
            f"- can_enter_L2_placement_abutment_rule_closure: `{report['can_enter_L2_placement_abutment_rule_closure']}`",
            f"- can_enter_L3_module_gds_generation: `{report['can_enter_L3_module_gds_generation']}`",
            f"- can_claim_full_openyield_gds_now: `{report['can_claim_full_openyield_gds_now']}`",
            "",
            "## Required Answers",
            "",
            f"1. L0 contracts derive `{summary['question_1_total_primitives']}` primitives.",
            f"2. Existing GDS primitives: `{', '.join(summary['question_2_existing_gds']) or 'none'}`.",
            f"3. Python generator primitives: `{', '.join(summary['question_3_python_generators']) or 'none'}`.",
            f"4. Candidate SPICE only primitives: `{', '.join(summary['question_4_candidate_spice_only']) or 'none'}`.",
            f"5. OpenYield source only primitives: `{', '.join(summary['question_5_source_only']) or 'none'}`.",
            f"6. Metadata/fallback only primitives: `{', '.join(summary['question_6_metadata_or_fallback_only']) or 'none'}`.",
            f"7. Missing physical source primitives: `{', '.join(summary['question_7_missing_physical_source']) or 'none'}`.",
            f"8. Missing pin/bbox/rail completeness: `{', '.join(summary['question_8_pin_bbox_rail_incomplete']) or 'none'}`.",
            f"9. Missing abutment rule closure: `{', '.join(summary['question_9_abutment_rule_incomplete']) or 'none'}`.",
            f"10. Standalone module GDS now: `{', '.join(summary['question_10_modules_standalone_gds']) or 'none'}`.",
            f"11. Blocked modules: `{', '.join(summary['question_11_modules_blocked']) or 'none'}`.",
            f"12. L2 still needs: `{'; '.join(summary['question_12_l2_missing']) or 'none'}`.",
            f"13. Can enter L2: `{summary['question_13_can_enter_L2']}`.",
            f"14. Can enter L3: `{summary['question_14_can_enter_L3']}`.",
            "",
        ]
    )


def write_l1_evidence(
    repo: Path,
    report: dict[str, Any],
) -> None:
    summary_path = repo / "docs/evidence/L1_physical_primitive_gap_summary.md"
    lines = [
        "# L1 Physical Primitive Gap Summary",
        "",
        "## First-pass Conclusion",
        "",
        f"- can_claim_L1_physical_primitives_closed_now: `{report['can_claim_L1_physical_primitives_closed_now']}`",
        f"- can_enter_L2_placement_abutment_rule_closure: `{report['can_enter_L2_placement_abutment_rule_closure']}`",
        f"- can_enter_L3_module_gds_generation: `{report['can_enter_L3_module_gds_generation']}`",
        "",
        "## Main Blockers",
        "",
    ]
    if report["remaining_L1_blockers"]:
        lines.extend(f"- `{item}`" for item in report["remaining_L1_blockers"])
    else:
        lines.append("- none")
    lines.extend(
        [
            "",
            "## Needed Evidence Or Generators",
            "",
            "- For `nand3` and `and3`: add a local physical source, either replacement GDS, a Python generator, or an explicit compositional fallback that the GDS writer can instantiate as a stable leaf.",
            "- For control/decode leaf groups that remain metadata or candidate-only: freeze whether they decompose into existing local cells or need dedicated hardmacros.",
            "- For primitives that already have GDS but incomplete abutment metadata: close L2 left/right and top/bottom stitching rules rather than rediscovering leaf semantics.",
            "",
        ]
    )
    write_text(summary_path, "\n".join(lines))

    timeline = repo / "docs/evidence/evidence_timeline.md"
    milestone = repo / "docs/evidence/milestone_summary.md"
    with timeline.open("a", encoding="utf-8") as handle:
        handle.write("\n- 2026-07-02: Generated OpenYield L1 physical primitive readiness inventory and module-to-primitive dependency matrix.\n")
    with milestone.open("a", encoding="utf-8") as handle:
        handle.write("\n- L1 first pass: primitive inventory frozen; L2 gate depends on remaining physical-source blockers.\n")


def create_evidence_package(repo: Path) -> Path:
    pkg_dir = Path("/data1/qujh/work/download_packages")
    pkg_dir.mkdir(parents=True, exist_ok=True)
    import time

    stamp = time.strftime("%Y%m%d_%H%M%S")
    pkg = pkg_dir / f"openyield_L1_physical_primitive_evidence_{stamp}.tar.gz"
    targets = [
        "docs/mapping/openyield_leaf_physical_readiness_matrix.csv",
        "docs/mapping/openyield_leaf_physical_readiness_matrix.md",
        "docs/mapping/openyield_module_to_primitive_dependency_matrix.csv",
        "docs/mapping/openyield_module_to_primitive_dependency_matrix.md",
        "docs/openyield_physical_primitive_closure_report.md",
        "docs/openyield_physical_primitive_closure_report.json",
        "docs/evidence/L1_physical_primitive_gap_summary.md",
        "technology/freepdk45/openyield_leaf_physical_library.json",
        "docs/mapping/openyield_canonical_sram_semantic_contract.json",
        "docs/mapping/openyield_time_control_decomposition_contract.json",
        "docs/mapping/openyield_control_path_semantic_contracts.csv",
        "docs/mapping/openyield_decoder_wordline_semantic_contract.json",
        "/tmp/openyield_L1_gds_files.txt",
        "/tmp/openyield_L1_technology_files.txt",
        "/tmp/openyield_L1_candidate_spice_files.txt",
    ]
    import tarfile

    with tarfile.open(pkg, "w:gz") as tar:
        for item in targets:
            path = Path(item)
            if path.exists():
                tar.add(path, arcname=item.lstrip("/"))
    return pkg


def _candidate_spice_index(repo: Path) -> list[Path]:
    root = repo / "docs/candidate_spice"
    if not root.exists():
        return []
    return sorted(path for path in root.rglob("*") if path.is_file())


def _resolve_local_macro(repo: Path, spec: PrimitiveSpec) -> dict[str, Any]:
    ordered = []
    if spec.preferred_local_macro:
        ordered.append(spec.preferred_local_macro)
    ordered.extend(candidate for candidate in spec.local_macro_candidates if candidate not in ordered)
    for candidate in ordered:
        path = _macro_path(repo, candidate)
        if path and path.exists():
            return _gds_metadata_for_path(repo, path, candidate, spec)
    return {
        "existing_gds_found": False,
        "local_source_path": "",
        "bbox_known": False,
        "pin_labels_known": False,
        "vdd_gnd_pins_known": False,
        "rail_geometry_known": False,
        "row_height_or_pitch_known": False,
        "labels": [],
    }


def _macro_path(repo: Path, candidate: str) -> Path | None:
    if candidate.startswith("openram_replacements/"):
        return repo / "technology/freepdk45/gds_lib" / f"{candidate}.gds"
    if candidate.startswith("openyield_repaired/"):
        return repo / "technology/freepdk45/gds_lib" / f"{candidate}.gds"
    return repo / "technology/freepdk45/gds_lib" / f"{candidate}.gds"


def _gds_metadata_for_path(repo: Path, path: Path, candidate: str, spec: PrimitiveSpec) -> dict[str, Any]:
    bbox = measure_gds_bbox(path)
    labels = inspect_gds_text_records(path)
    label_texts = sorted({str(item["text"]).strip() for item in labels if str(item.get("text") or "").strip()})
    lower = {item.lower() for item in label_texts}
    vdd = "vdd" in lower
    gnd = "gnd" in lower
    pin_labels_known = bool(label_texts)
    rail_known = vdd and gnd
    layers = inspect_gds_layers(path)
    return {
        "existing_gds_found": True,
        "local_source_path": str(path.relative_to(repo)).replace("\\", "/"),
        "bbox_known": bbox is not None,
        "bbox": bbox.to_dict() if bbox else None,
        "pin_labels_known": pin_labels_known,
        "vdd_gnd_pins_known": vdd and gnd,
        "rail_geometry_known": rail_known,
        "row_height_or_pitch_known": bbox is not None,
        "labels": label_texts,
        "layers": layers,
        "macro_candidate": candidate,
        "has_replacement_like_variant": "openram_replacements/" in candidate or "openyield_repaired/" in candidate,
        "gds_variant_kind": "repaired" if "openyield_repaired/" in candidate else "replacement" if "openram_replacements/" in candidate else "default",
    }


def _classify_local_source_type(
    spec: PrimitiveSpec,
    gds_info: dict[str, Any],
    generator_found: bool,
    candidate_matches: list[str],
) -> str:
    if gds_info.get("existing_gds_found"):
        if gds_info.get("has_replacement_like_variant"):
            return "HARDMACRO_GDS"
        if generator_found and not gds_info.get("pin_labels_known"):
            return "PYTHON_GENERATOR"
        return "EXISTING_GDS"
    if generator_found:
        return "PYTHON_GENERATOR"
    if candidate_matches:
        return "CANDIDATE_SPICE_ONLY"
    if spec.fallback_source_path:
        return "FALLBACK_ONLY"
    if spec.metadata_source_path:
        return "METADATA_ONLY"
    if spec.openyield_source_path != "not_found_in_openyield_source":
        return "SOURCE_ONLY"
    return "MISSING"


def _classify_readiness(
    spec: PrimitiveSpec,
    local_source_type: str,
    gds_info: dict[str, Any],
    generator_found: bool,
) -> str:
    if local_source_type == "HARDMACRO_GDS":
        if gds_info.get("pin_labels_known") and gds_info.get("vdd_gnd_pins_known"):
            return "HARDMACRO_GDS_READY"
        return "GDS_EXISTS_NEEDS_PIN_RAIL_EXTRACTION"
    if local_source_type == "EXISTING_GDS":
        if gds_info.get("pin_labels_known") and gds_info.get("vdd_gnd_pins_known"):
            return "LEAF_GDS_READY"
        return "GDS_EXISTS_NEEDS_PIN_RAIL_EXTRACTION"
    if local_source_type == "PYTHON_GENERATOR":
        return "PYTHON_GENERATOR_READY"
    if local_source_type == "CANDIDATE_SPICE_ONLY":
        return "SPICE_ONLY_NEEDS_LAYOUT_GENERATOR"
    if local_source_type == "SOURCE_ONLY":
        return "SOURCE_ONLY_NEEDS_PHYSICAL_GENERATOR"
    if local_source_type == "METADATA_ONLY":
        return "METADATA_ONLY_NEEDS_PHYSICAL_SOURCE"
    if local_source_type == "FALLBACK_ONLY":
        return "FALLBACK_ONLY"
    return "MISSING_PHYSICAL_SOURCE"


def _blocking_gap(spec: PrimitiveSpec, local_source_type: str, gds_info: dict[str, Any], generator_found: bool) -> str:
    if local_source_type == "SOURCE_ONLY":
        return "OpenYield source exists but no local GDS/generator/fallback physical source is available."
    if local_source_type == "CANDIDATE_SPICE_ONLY":
        return "Only candidate SPICE evidence exists; no local physical generator or GDS is available."
    if local_source_type == "METADATA_ONLY":
        return "Only metadata/contracts exist; no physical macro or generator is available."
    if local_source_type == "MISSING":
        return "No OpenYield source-backed or local physical source was found."
    if local_source_type in {"EXISTING_GDS", "HARDMACRO_GDS"} and not gds_info.get("pin_labels_known"):
        return "GDS exists but pin labels are incomplete; abstract generator or manual extraction is still needed."
    if spec.primitive_name == "precharge_cell":
        return "Local precharge macro inventory exists, but OpenYield source uses VDD/ENB/BL/BLB while local fallbacks still need final pin-contract validation."
    if spec.primitive_name in {"decoder_leaf_gate", "wordline_decoder_leaf_gate", "wordline_driver_leaf_gate", "enable_path_leaf_gate", "gated_clock_leaf_gate", "control_logic_leaf_gate"}:
        return "This leaf is only frozen as a semantic grouping; physical composition still needs L2/L3 implementation policy."
    return ""


def _next_action(spec: PrimitiveSpec, local_source_type: str, readiness: str, blocking_gap: str) -> str:
    if local_source_type in {"SOURCE_ONLY", "CANDIDATE_SPICE_ONLY", "METADATA_ONLY", "MISSING"}:
        return "Add a concrete local physical source: replacement GDS, Python generator, or explicit compositional fallback."
    if local_source_type == "FALLBACK_ONLY":
        return "Decide whether the fallback remains compositional or should be promoted to a dedicated physical leaf."
    if readiness == "PYTHON_GENERATOR_READY":
        return "Keep the generator path available and close abutment/orientation rules in L2."
    if readiness in {"LEAF_GDS_READY", "HARDMACRO_GDS_READY"}:
        return "Close abutment, rail-stitch, and orientation policy in L2 before claiming module/top-level GDS."
    if blocking_gap:
        return "Resolve the remaining pin/rail extraction gap before L2."
    return "No immediate action."


def _abutment_policy(spec: PrimitiveSpec, gds_info: dict[str, Any], generator_found: bool) -> tuple[str, str, str]:
    if spec.primitive_name in {"bitcell", "dummy_cell", "replica_cell"}:
        return (
            "full_bbox_pitch_only_until_storage_abutment_review",
            "R0_MX_storage_row_policy_full_bbox_pitch",
            "storage_array_rows_use_R0_MX_row_alternation",
        )
    if spec.primitive_name in {"sense_amp", "write_driver", "column_mux"}:
        return (
            "manual_side_pin_spacing_review_required",
            "manual_side_rail_review_required",
            "R0_preferred_pending_side_pin_routing_review",
        )
    if spec.primitive_name in {"inv", "delay_inv", "nand2", "nand4", "nor2", "precharge_cell", "wordline_driver"}:
        if gds_info.get("vdd_gnd_pins_known") or generator_found:
            return (
                "generated_gate_row_edge_to_edge_pending_L2_compaction_policy",
                "top_vdd_bottom_gnd_or_abstract_gate_row_policy",
                "R0_MX_gate_row_policy",
            )
        return (
            "pin_rail_extraction_pending_before_abutment",
            "pin_rail_extraction_pending_before_abutment",
            "orientation_pending_pin_extraction",
        )
    if spec.primitive_name == "dff_cell":
        return (
            "no_vertical_overlap_dff_domain_policy",
            "top_vdd_bottom_gnd_dff_rows_pending_L2",
            "R0_MX_dff_rows_subject_to_no_vertical_overlap_policy",
        )
    return (
        "manual_leaf_composition_policy_required",
        "manual_leaf_composition_policy_required",
        "orientation_defined_after_leaf_composition_policy",
    )


def _evidence_files(spec: PrimitiveSpec, gds_info: dict[str, Any], candidate_matches: list[str]) -> list[str]:
    files = []
    for part in spec.openyield_source_path.split(";"):
        if part and part != "not_found_in_openyield_source":
            files.append(part)
    if gds_info.get("local_source_path"):
        files.append(str(gds_info["local_source_path"]))
    if spec.metadata_source_path:
        files.append(spec.metadata_source_path)
    if spec.fallback_source_path:
        files.append(spec.fallback_source_path)
    files.extend(candidate_matches[:3])
    if spec.primitive_name in {"bitcell", "dummy_cell", "replica_cell"}:
        files.append("docs/openyield_storage_pitch_audit_report.md")
    if spec.primitive_name in {"inv", "delay_inv", "nand2", "precharge_cell", "column_mux", "wordline_driver", "sense_amp", "write_driver", "dff_cell"}:
        files.append("docs/openyield_hardcell_power_rail_continuity_report.md")
    return sorted(dict.fromkeys(files))


def _module_evidence_files(primitives: list[str], primitive_by_name: dict[str, dict[str, Any]]) -> str:
    files: list[str] = []
    for name in primitives:
        row = primitive_by_name[name]
        if row["evidence_files"]:
            files.extend(row["evidence_files"].split(";"))
    return ";".join(sorted(dict.fromkeys(files)))
