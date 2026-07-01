"""OpenYield L0 SRAM module-semantics closure helpers.

This module is intentionally metadata-oriented.  It captures the current
source-backed understanding of how OpenYield assembles an SRAM at the semantic
netlist level, then exports stable rows for reports and CSV/Markdown matrices.
"""

from __future__ import annotations

import csv
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any


SEMANTIC_MAPPING_STATUSES = {
    "SEMANTICS_CLOSED",
    "SOURCE_FOUND_PORTS_KNOWN",
    "SOURCE_FOUND_PORTS_PARTIAL",
    "SOURCE_FOUND_CONNECTIONS_UNRESOLVED",
    "PARAMETER_RULE_UNRESOLVED",
    "LOCAL_MAPPING_UNRESOLVED",
    "NOT_FOUND_IN_OPENYIELD",
    "BLOCKED",
}

MODULE_COLUMNS = [
    "module",
    "module_category",
    "openyield_source_found",
    "openyield_source_path",
    "openyield_class_or_function",
    "openyield_netlist_source",
    "role_in_sram",
    "ports_or_nodes",
    "input_signals",
    "output_signals",
    "power_pins",
    "clock_or_timing_signals",
    "connected_upstream_modules",
    "connected_downstream_modules",
    "instance_count_rule",
    "parameter_dependencies",
    "is_parameterized",
    "is_required_for_all_sram_configs",
    "is_optional_or_config_dependent",
    "local_layoutgen_counterpart",
    "local_layoutgen_path",
    "semantic_mapping_status",
    "semantic_gap",
    "next_required_action",
    "evidence_files",
]

PARAMETER_COLUMNS = [
    "parameter",
    "meaning",
    "openyield_source_path",
    "used_by_modules",
    "affects_instance_count",
    "affects_geometry",
    "affects_routing",
    "affects_timing",
    "derivation_rule",
    "example_values",
    "unknown_or_unresolved",
    "next_required_action",
]

CONNECTION_COLUMNS = [
    "source_module",
    "source_port_or_signal",
    "target_module",
    "target_port_or_signal",
    "signal_name",
    "signal_category",
    "direction",
    "is_power",
    "is_clock",
    "is_control",
    "is_data",
    "is_bitline",
    "is_wordline",
    "is_timing_path",
    "evidence_source",
    "confidence",
    "unresolved_reason",
]

VARIATION_COLUMNS = [
    "variation_axis",
    "openyield_parameter",
    "module_types_unchanged",
    "instance_count_changes",
    "structure_changes",
    "routing_or_timing_changes",
    "openyield_source_evidence",
    "layoutgen_support_status",
    "unresolved_gap",
]

LAYOUTGEN_MAPPING_COLUMNS = [
    "openyield_module",
    "openyield_source_path",
    "local_layoutgen_module",
    "local_layoutgen_path",
    "mapping_type",
    "mapping_status",
    "known_aliases",
    "semantic_mismatch",
    "next_required_action",
]


@dataclass(frozen=True)
class ModuleSpec:
    module: str
    module_category: str
    openyield_source_path: str
    openyield_class_or_function: str
    openyield_netlist_source: str
    role_in_sram: str
    ports_or_nodes: str
    input_signals: str
    output_signals: str
    power_pins: str
    clock_or_timing_signals: str
    connected_upstream_modules: str
    connected_downstream_modules: str
    instance_count_rule: str
    parameter_dependencies: str
    is_parameterized: bool
    is_required_for_all_sram_configs: bool
    is_optional_or_config_dependent: bool
    local_layoutgen_counterpart: str
    local_layoutgen_path: str
    semantic_mapping_status: str
    semantic_gap: str
    next_required_action: str
    evidence_files: tuple[str, ...]


def build_l0_semantics_report(repo_root: str | Path, openyield_root: str | Path) -> dict[str, Any]:
    repo = Path(repo_root).resolve()
    openyield = Path(openyield_root).resolve()

    module_rows = build_module_semantics_rows(repo, openyield)
    parameter_rows = build_parameter_dependency_rows()
    connection_rows = build_connection_rows()
    variation_rows = build_variation_rows()
    mapping_rows = build_layoutgen_mapping_rows(repo)

    status_buckets: dict[str, list[str]] = {status: [] for status in SEMANTIC_MAPPING_STATUSES}
    for row in module_rows:
        status_buckets[row["semantic_mapping_status"]].append(row["module"])

    report = {
        "scope": "L0_openyield_module_semantics_closure",
        "repo_root": str(repo),
        "openyield_root": str(openyield),
        "module_count": len(module_rows),
        "parameter_count": len(parameter_rows),
        "connection_count": len(connection_rows),
        "variation_count": len(variation_rows),
        "layoutgen_mapping_count": len(mapping_rows),
        "status_buckets": {key: sorted(value) for key, value in status_buckets.items() if value},
        "semantics_closed_modules": sorted(status_buckets["SEMANTICS_CLOSED"]),
        "source_found_ports_known_modules": sorted(status_buckets["SOURCE_FOUND_PORTS_KNOWN"]),
        "source_found_connections_unresolved_modules": sorted(status_buckets["SOURCE_FOUND_CONNECTIONS_UNRESOLVED"]),
        "parameter_rule_unresolved_modules": sorted(status_buckets["PARAMETER_RULE_UNRESOLVED"]),
        "local_mapping_unresolved_modules": sorted(status_buckets["LOCAL_MAPPING_UNRESOLVED"]),
        "not_found_in_openyield_modules": sorted(status_buckets["NOT_FOUND_IN_OPENYIELD"]),
        "l0_blocking_gaps": [
            "OpenYield has no explicit SRAM_TOP/BANK hierarchy class; top-level SRAM semantics currently live in the transient testbench assembly path.",
            "There is no named OpenYield parameter set for word_size/num_words/words_per_row/num_banks/num_ports/write_mask; current source is row/column oriented instead.",
            "TIME is a composite control/timing generator, not a flat module, so control-path physical boundaries remain semantic-only.",
            "Column-mux ratio is not a first-class parameter; the current source hard-codes mux_in=2 when choose_columnmux is enabled.",
            "Decoder-to-wordline-driver integration is source-backed, but local layoutgen still treats decoder/control logic as metadata or proxy placement in several places.",
        ],
        "recommended_next_step_after_l0": (
            "Do not enter full L1 closure yet. First freeze the canonical SRAM semantic contract: "
            "top-level ports, row/column/count formulas, control-path decomposition boundaries, and "
            "the authoritative mapping from OpenYield row/column semantics to local layoutgen word_size/rows/cols terminology."
        ),
        "key_questions_answered": {
            "module_hierarchy": (
                "OpenYield SRAM is assembled in Sram6TCoreTestbench.create_testbench(): "
                "bitcell array + replica column + optional dummy structures + TIME control/timing + "
                "decoder + wordline drivers + read/write peripherals."
            ),
            "always_required_modules": [
                "bitcell_array",
                "replica_array",
                "row_decoder",
                "wordline_driver",
                "CONTROL_LOGIC",
                "DELAY_CHAIN",
            ],
            "parameter_or_config_dependent_modules": [
                "dummy_array",
                "column_mux",
                "sense_amp",
                "write_driver",
                "DFF_ROW",
                "PRECHARGE_ENABLE_PATH",
                "SENSE_ENABLE_PATH",
                "WRITE_ENABLE_PATH",
                "WORDLINE_ENABLE_PATH",
                "GATED_CLOCK_PATH",
            ],
            "top_level_note": (
                "OpenYield does not expose a dedicated SRAM_TOP or BANK class. Those semantics are implicit "
                "in one-bank testbench assembly and optimization wrappers."
            ),
        },
    }
    return {
        "report": report,
        "module_rows": module_rows,
        "parameter_rows": parameter_rows,
        "connection_rows": connection_rows,
        "variation_rows": variation_rows,
        "layoutgen_mapping_rows": mapping_rows,
        "connection_graph": build_connection_graph(connection_rows),
    }


def build_module_semantics_rows(repo_root: Path, openyield_root: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for spec in _module_specs():
        source_found = _openyield_path_exists(openyield_root, spec.openyield_source_path)
        local_found = _repo_path_exists(repo_root, spec.local_layoutgen_path)
        if spec.semantic_mapping_status not in SEMANTIC_MAPPING_STATUSES:
            raise ValueError(f"invalid semantic status for {spec.module}: {spec.semantic_mapping_status}")
        row = {
            "module": spec.module,
            "module_category": spec.module_category,
            "openyield_source_found": source_found,
            "openyield_source_path": spec.openyield_source_path,
            "openyield_class_or_function": spec.openyield_class_or_function,
            "openyield_netlist_source": spec.openyield_netlist_source,
            "role_in_sram": spec.role_in_sram,
            "ports_or_nodes": spec.ports_or_nodes,
            "input_signals": spec.input_signals,
            "output_signals": spec.output_signals,
            "power_pins": spec.power_pins,
            "clock_or_timing_signals": spec.clock_or_timing_signals,
            "connected_upstream_modules": spec.connected_upstream_modules,
            "connected_downstream_modules": spec.connected_downstream_modules,
            "instance_count_rule": spec.instance_count_rule,
            "parameter_dependencies": spec.parameter_dependencies,
            "is_parameterized": spec.is_parameterized,
            "is_required_for_all_sram_configs": spec.is_required_for_all_sram_configs,
            "is_optional_or_config_dependent": spec.is_optional_or_config_dependent,
            "local_layoutgen_counterpart": spec.local_layoutgen_counterpart,
            "local_layoutgen_path": spec.local_layoutgen_path if local_found else f"{spec.local_layoutgen_path} [missing]",
            "semantic_mapping_status": spec.semantic_mapping_status,
            "semantic_gap": spec.semantic_gap,
            "next_required_action": spec.next_required_action,
            "evidence_files": ";".join(spec.evidence_files),
        }
        rows.append(row)
    return rows


def build_parameter_dependency_rows() -> list[dict[str, Any]]:
    return [
        _parameter("word_size", "logical data width at the SRAM interface", "not_found_in_source", "SRAM_TOP;BANK;column_mux;sense_amp;write_driver;DFF_ROW", False, True, True, True, "not_found_in_source", "", "OpenYield compiler source is organized around num_rows/num_cols, not a separate word_size parameter.", "Define canonical mapping from local word_size to OpenYield num_cols and optional column mux grouping."),
        _parameter("num_words", "logical word count at the SRAM interface", "not_found_in_source", "SRAM_TOP;BANK;row_decoder", False, True, True, True, "not_found_in_source", "", "No named num_words parameter exists in the current OpenYield source.", "Derive num_words only after deciding how num_rows and column muxing map to logical words."),
        _parameter("words_per_row", "logical packing ratio for multiple words per physical row", "not_found_in_source", "column_mux;wordline_decoder", False, True, True, True, "not_found_in_source", "", "No words_per_row parameter exists in source.", "Create an explicit contract if layoutgen wants words_per_row semantics."),
        _parameter("num_rows", "physical row count", "sram_compiler/config_yaml/global.yaml;sram_compiler/subcircuits/decoder.py;sram_compiler/subcircuits/time_generate.py", "bitcell_array;dummy_array;replica_array;row_decoder;wordline_driver;CONTROL_LOGIC;DELAY_CHAIN", True, True, True, True, "global.yaml num_rows; row address bits = ceil(log2(num_rows)); replica rows = num_rows+1; dummy-column rows = num_rows+3", "16;32;64", "", "Treat num_rows as the primary row-count parameter in the L0 contract."),
        _parameter("num_cols", "physical column count", "sram_compiler/config_yaml/global.yaml;sram_compiler/subcircuits/time_generate.py;sram_compiler/testbenches/sram_6t_core_testbench.py", "bitcell_array;dummy_array;column_mux;sense_amp;write_driver;wordline_driver;CONTROL_LOGIC", True, True, True, True, "global.yaml num_cols; data DFF width = num_cols; write-driver count = num_cols; read SA count = num_cols or num_cols/2 with mux", "16;32;512", "", "Treat num_cols as the primary bitline-count parameter in the L0 contract."),
        _parameter("addr_size", "top-level address width", "sram_compiler/subcircuits/time_generate.py;sram_compiler/testbenches/sram_6t_core_testbench.py", "SRAM_TOP;CONTROL_LOGIC;row_decoder", False, False, True, True, "addr_size = ceil(log2(num_rows)) in current source", "4 for num_rows=16", "Current source derives address width only from num_rows, so column address is not separated.", "Decide whether layoutgen needs a logical addr_size separate from physical row decode width."),
        _parameter("row_addr_size", "row decoder address width", "sram_compiler/subcircuits/decoder.py", "row_decoder;wordline_decoder;CONTROL_LOGIC", False, False, True, True, "row_addr_size = ceil(log2(num_rows))", "4 for num_rows=16", "", "Reuse the derived formula in the canonical contract."),
        _parameter("col_addr_size", "column-select address width", "not_found_in_source", "column_mux;CONTROL_LOGIC", False, False, True, True, "not_found_in_source", "", "No named col_addr_size parameter exists; column select is currently driven by SEL pulses in the testbench.", "If logical column muxing becomes first-class, add an explicit derived col_addr_size contract."),
        _parameter("write_size", "masked write granularity", "not_found_in_source", "write_driver;DFF_ROW", False, False, False, False, "not_found_in_source", "", "No masked-write granularity parameter exists in source.", "Leave unsupported in L0."),
        _parameter("write_mask", "write-mask enable presence", "not_found_in_source", "write_driver;CONTROL_LOGIC", False, False, False, False, "not_found_in_source", "", "No write-mask control signals are defined.", "Leave unsupported in L0."),
        _parameter("wmask", "write-mask bus", "not_found_in_source", "write_driver;CONTROL_LOGIC", False, False, False, False, "not_found_in_source", "", "No wmask bus is present.", "Leave unsupported in L0."),
        _parameter("num_banks", "bank count", "not_found_in_source", "BANK;SRAM_TOP", False, True, True, True, "not_found_in_source", "", "OpenYield current source models one implicit bank only.", "Do not claim banked SRAM support."),
        _parameter("num_ports", "port count", "not_found_in_source", "SRAM_TOP;CONTROL_LOGIC", False, True, True, True, "not_found_in_source", "", "No generic num_ports parameter exists.", "Keep single-port semantic assumption."),
        _parameter("read_ports", "read port count", "not_found_in_source", "sense_amp;column_mux;CONTROL_LOGIC", False, False, False, False, "not_found_in_source", "", "Read operations exist, but no read_ports parameter is defined.", "Keep single read path only."),
        _parameter("write_ports", "write port count", "not_found_in_source", "write_driver;CONTROL_LOGIC", False, False, False, False, "not_found_in_source", "", "Write operations exist, but no write_ports parameter is defined.", "Keep single write path only."),
        _parameter("readwrite_ports", "read/write combined port count", "not_found_in_source", "SRAM_TOP;CONTROL_LOGIC", False, False, False, False, "not_found_in_source", "", "Operations are mode-switched in one shared testbench, not modeled as port-count parameters.", "Keep one shared read/write port semantic."),
        _parameter("column_mux_ratio", "columns per sense-amp group", "not_found_in_source", "column_mux;sense_amp;CONTROL_LOGIC", True, True, True, True, "When choose_columnmux is true, testbench hard-codes mux_in=2; otherwise the path behaves as ratio 1.", "1;2", "Not a named OpenYield parameter; current ratio is an implicit testbench rule.", "Promote the implicit mux_in rule into an explicit adapter contract before L1."),
        _parameter("replica_related_parameters", "replica sizing and row extension rules", "sram_compiler/subcircuits/replica_column.py;sram_compiler/testbenches/sram_6t_core_testbench.py", "replica_array;DELAY_CHAIN;CONTROL_LOGIC", True, True, True, True, "Replica_Column rows = num_rows+1; driven by RWL plus WL[0:num_rows-1].", "num_rows=16 -> 17 replica rows", "", "Freeze the replica row-count and RWL semantics as part of the L0 contract."),
        _parameter("delay_chain_related_parameters", "delay-chain stage and fanout controls", "sram_compiler/subcircuits/time_generate.py", "DELAY_CHAIN;WRITE_ENABLE_PATH;SENSE_ENABLE_PATH", False, True, False, True, "DelayChain is fixed 9-stage/4-load; WenDelayChain is instantiated only for write with num_rows=16 and num_cols=512, stages=6, loads_per_stage=4.", "default chain; 16x512 write special case", "Current source uses mostly hard-coded constants rather than configurable parameters.", "Separate fixed-source constants from future layoutgen tunables."),
        _parameter("control_timing_related_parameters", "control enable sizing and timing scaling rules", "sram_compiler/subcircuits/time_generate.py;sram_compiler/testbenches/parameter_factor.py", "CONTROL_LOGIC;PRECHARGE_ENABLE_PATH;SENSE_ENABLE_PATH;WRITE_ENABLE_PATH;WORDLINE_ENABLE_PATH;GATED_CLOCK_PATH", False, True, True, True, "clk_drive_scale, w_en_scale, pre_drive_scale derive from num_rows/num_cols; csb/web/clk pulses come from testbench stimulus.", "w_en_scale=ceil(num_cols/64)", "Stimulus timing and composite control sizing are mixed in the same implementation.", "Split stimulus-only behavior from reusable control semantics before L1."),
    ]


def build_connection_rows() -> list[dict[str, Any]]:
    return [
        _connection("SRAM_TOP", "A[i]", "DFF_ROW", "A[i]", "A[i]", "address", "input_to_register", False, False, False, False, False, False, False, "sram_compiler/subcircuits/time_generate.py:501-537;sram_compiler/testbenches/sram_6t_core_testbench.py:1025-1040", "HIGH", ""),
        _connection("DFF_ROW", "A_dff[i]", "row_decoder", "A[i]", "A_dff[i]", "address", "registered_address_to_decoder", False, False, False, False, False, False, False, "sram_compiler/testbenches/sram_6t_core_testbench.py:336-384", "HIGH", ""),
        _connection("row_decoder", "WL[i]", "wordline_driver", "A", "DEC_WL[i]", "decoder_wordline", "decoder_to_driver", False, False, True, False, False, True, False, "sram_compiler/testbenches/sram_6t_core_testbench.py:375-426", "HIGH", ""),
        _connection("CONTROL_LOGIC", "wl_en", "wordline_driver", "B", "WL_EN", "control_enable", "control_to_driver", False, False, True, False, False, False, True, "sram_compiler/subcircuits/time_generate.py:640-657;sram_compiler/testbenches/sram_6t_core_testbench.py:416-421", "HIGH", ""),
        _connection("wordline_driver", "Z", "bitcell_array", "WL[i]", "WL[i]", "wordline", "driver_to_array", False, False, True, False, False, True, True, "sram_compiler/testbenches/sram_6t_core_testbench.py:416-421;978-982", "HIGH", ""),
        _connection("bitcell_array", "BL[i]/BLB[i]", "precharge", "BL/BLB", "BL[i];BLB[i]", "bitline", "shared_bitline", False, False, False, False, True, False, False, "sram_compiler/testbenches/sram_6t_core_testbench.py:461-473", "HIGH", ""),
        _connection("precharge", "BL/BLB", "column_mux", "BL[i]/BLB[i]", "BL[i];BLB[i]", "bitline", "precharged_bitline_to_mux", False, False, False, False, True, False, False, "sram_compiler/testbenches/sram_6t_core_testbench.py:497-512", "HIGH", ""),
        _connection("column_mux", "SA_IN/SA_INB", "sense_amp", "IN/INB", "SA_IN[*];SA_INB[*]", "read_data", "mux_to_sense", False, False, False, True, False, False, False, "sram_compiler/testbenches/sram_6t_core_testbench.py:567-589", "HIGH", ""),
        _connection("bitcell_array", "BL[i]/BLB[i]", "sense_amp", "IN/INB", "BL[i];BLB[i]", "read_data", "direct_array_to_sense", False, False, False, True, True, False, False, "sram_compiler/testbenches/sram_6t_core_testbench.py:579-589", "HIGH", ""),
        _connection("sense_amp", "Q/QB", "SRAM_TOP", "dout path", "SA_Q[*];SA_QB[*]", "read_data", "sense_to_output", False, False, False, True, False, False, False, "sram_compiler/testbenches/sram_6t_core_testbench.py:551-589;428-442", "MEDIUM", "OpenYield top-level output is modeled through D_latch/observation nodes rather than a macro pin list."),
        _connection("SRAM_TOP", "DIN[i]", "DFF_ROW", "DIN[i]", "DIN[i]", "write_data", "input_to_register", False, False, False, True, False, False, False, "sram_compiler/subcircuits/time_generate.py:507-555;sram_compiler/testbenches/sram_6t_core_testbench.py:625-646", "HIGH", ""),
        _connection("DFF_ROW", "DIN_dff[i]", "write_driver", "DIN", "DIN_dff[i]", "write_data", "registered_data_to_driver", False, False, False, True, False, False, False, "sram_compiler/testbenches/sram_6t_core_testbench.py:612-623", "HIGH", ""),
        _connection("CONTROL_LOGIC", "w_en", "write_driver", "EN", "w_en", "control_enable", "control_to_write", False, False, True, False, False, False, True, "sram_compiler/subcircuits/time_generate.py:687-705;sram_compiler/testbenches/sram_6t_core_testbench.py:619", "HIGH", ""),
        _connection("write_driver", "BL/BLB", "bitcell_array", "BL[i]/BLB[i]", "BL[i];BLB[i]", "bitline", "write_driver_to_array", False, False, False, True, True, False, False, "sram_compiler/testbenches/sram_6t_core_testbench.py:613-623;978-982", "HIGH", ""),
        _connection("replica_array", "RBL/RBLB", "DELAY_CHAIN", "in", "rbl", "timing_sense", "replica_to_delay", False, False, True, False, True, False, True, "sram_compiler/subcircuits/time_generate.py:659-676;sram_compiler/testbenches/sram_6t_core_testbench.py:143-197", "HIGH", ""),
        _connection("DELAY_CHAIN", "out", "SENSE_ENABLE_PATH", "input", "rbl_delay", "timing_control", "delay_to_sense_enable", False, False, True, False, False, False, True, "sram_compiler/subcircuits/time_generate.py:705-720", "HIGH", ""),
        _connection("DELAY_CHAIN", "out_bar", "WRITE_ENABLE_PATH", "input", "rbl_delay_bar", "timing_control", "delay_to_write_enable", False, False, True, False, False, False, True, "sram_compiler/subcircuits/time_generate.py:666-705", "HIGH", ""),
        _connection("CONTROL_LOGIC", "PRE", "precharge", "ENB", "PRE", "control_enable", "control_to_precharge", False, False, True, False, False, False, True, "sram_compiler/subcircuits/time_generate.py:735-756;sram_compiler/testbenches/sram_6t_core_testbench.py:463-472", "HIGH", ""),
        _connection("CONTROL_LOGIC", "s_en", "sense_amp", "EN", "s_en", "control_enable", "control_to_sense", False, False, True, False, False, False, True, "sram_compiler/subcircuits/time_generate.py:705-720;sram_compiler/testbenches/sram_6t_core_testbench.py:573-587", "HIGH", ""),
        _connection("CONTROL_LOGIC", "clk_buf", "DFF_ROW", "CLK", "clk_buf", "clock", "buffered_clock_to_dff", False, True, True, False, False, False, True, "sram_compiler/subcircuits/time_generate.py:523-607", "HIGH", ""),
        _connection("CONTROL_LOGIC", "gated_clk_bar/gated_clk_buf", "GATED_CLOCK_PATH", "internal gates", "gated_clk_bar;gated_clk_buf", "clock_control", "internal_clock_gating", False, True, True, False, False, False, True, "sram_compiler/subcircuits/time_generate.py:608-639", "HIGH", ""),
        _connection("CONTROL_LOGIC", "wl_en", "WORDLINE_ENABLE_PATH", "derived output", "wl_en", "control_enable", "internal_enable_generation", False, False, True, False, False, False, True, "sram_compiler/subcircuits/time_generate.py:640-657", "HIGH", ""),
        _connection("CONTROL_LOGIC", "PRE", "PRECHARGE_ENABLE_PATH", "derived output", "PRE", "control_enable", "internal_enable_generation", False, False, True, False, False, False, True, "sram_compiler/subcircuits/time_generate.py:735-756", "HIGH", ""),
        _connection("CONTROL_LOGIC", "w_en", "WRITE_ENABLE_PATH", "derived output", "w_en", "control_enable", "internal_enable_generation", False, False, True, False, False, False, True, "sram_compiler/subcircuits/time_generate.py:687-705", "HIGH", ""),
        _connection("CONTROL_LOGIC", "s_en", "SENSE_ENABLE_PATH", "derived output", "s_en", "control_enable", "internal_enable_generation", False, False, True, False, False, False, True, "sram_compiler/subcircuits/time_generate.py:705-720", "HIGH", ""),
        _connection("VDD/GND", "VDD/VSS", "all_modules", "power pins", "VDD;VSS", "power", "global_power_distribution", True, False, False, False, False, False, False, "sram_compiler/subcircuits/base_subcircuit.py:10;sram_compiler/testbenches/sram_6t_core_testbench.py:861-863", "HIGH", ""),
    ]


def build_variation_rows() -> list[dict[str, Any]]:
    return [
        _variation("word_size changes", "word_size", "Module families stay conceptually the same only if local logic treats word_size as a derived alias.", "not_source_backed", "No explicit OpenYield structure rule because word_size is not a named parameter.", "Read/write/sense path fanout would change if word_size is mapped onto num_cols or mux grouping.", "not_found_in_source", "partial_local_support_only", "OpenYield source does not define word_size."),
        _variation("num_words changes", "num_words", "No direct OpenYield rule.", "not_source_backed", "No explicit OpenYield structure rule because num_words is not a named parameter.", "Would affect decoder depth if mapped onto num_rows, but the mapping is external to source.", "not_found_in_source", "partial_local_support_only", "Need a canonical num_words <-> num_rows/column_mux mapping."),
        _variation("words_per_row changes", "words_per_row", "Storage/peripheral module types stay the same if muxing semantics are generalized.", "Potential sense_amp/column_mux group count changes.", "Current source has only direct columns or hard-coded 2:1 mux behavior.", "Would alter column select routing and read fanout timing.", "sram_compiler/testbenches/sram_6t_core_testbench.py:475-549", "partial_local_support_only", "No first-class words_per_row parameter exists."),
        _variation("addr_size changes", "addr_size", "Decoder, TIME, DFF_ROW, wordline driver families remain the same.", "Address DFF count and decoder WL count scale with ceil(log2(num_rows)).", "Decoder cascade depth changes when num_rows crosses powers of two / groups of eight.", "Clock load and decoder enable fanout change.", "sram_compiler/subcircuits/decoder.py:133-230;sram_compiler/subcircuits/time_generate.py:417-437", "supported_as_num_rows_derivative", ""),
        _variation("column mux ratio changes", "column_mux_ratio", "bitcell_array/precharge/write_driver families stay the same.", "sense_amp and column_mux instance counts change from num_cols to num_cols/ratio.", "Current source only proves ratio 1 or 2 behavior.", "SEL/SELB routing, sense fanout, and read timing paths change.", "sram_compiler/testbenches/sram_6t_core_testbench.py:475-589", "partial_local_support_only", "Need explicit parameterization beyond hard-coded mux_in=2."),
        _variation("write mask / write size changes", "write_mask", "not_source_backed", "not_source_backed", "No source-backed write-mask structure exists.", "No source-backed write-mask routing or timing exists.", "not_found_in_source", "unsupported", "OpenYield source has no write mask semantics."),
        _variation("port count changes", "num_ports", "not_source_backed", "not_source_backed", "No source-backed multi-port structure exists.", "No source-backed multi-port routing/timing exists.", "not_found_in_source", "unsupported", "OpenYield current source is effectively one implicit read/write port."),
    ]


def build_layoutgen_mapping_rows(repo_root: Path) -> list[dict[str, Any]]:
    mappings = [
        _mapping("SRAM_TOP", "sram_compiler/testbenches/sram_6t_core_testbench.py", "standalone top assembly", "sram_layoutgen/netlist_writer.py", "PARTIAL_MATCH", "metadata_only", "top assembly;hybrid prototype", "Local top uses word_size/rows/cols abstraction; OpenYield top is transient testbench assembly.", "Freeze a canonical top-level SRAM semantic contract."),
        _mapping("BANK", "sram_compiler/testbenches/sram_6t_core_testbench.py", "", "", "NO_LOCAL_COUNTERPART", "unresolved", "single implicit bank", "No explicit BANK abstraction exists in either OpenYield source or current standalone flow.", "Keep one-bank assumption until a bank object is introduced."),
        _mapping("bitcell_array", "sram_compiler/subcircuits/sram_6t_core.py", "storage aggregation plan", "sram_layoutgen/openyield_adapter/array_aggregation.py", "PARTIAL_MATCH", "mapped", "SRAM_6T_CORE_*;cell_1rw array", "OpenYield exposes a hierarchical subckt; local flow places imported hardcells.", "Retain bitcell-array semantic aliasing."),
        _mapping("dummy_array", "sram_compiler/subcircuits/dummy_row_or_column.py", "dummy aggregation plan", "sram_layoutgen/openyield_adapter/array_aggregation.py", "DIRECT_MATCH", "mapped", "Dummy_Row;Dummy_Column", "Local flow currently uses only side dummy columns in standalone integration.", "Document dummy-row omission if top-level floorplan excludes it."),
        _mapping("replica_array", "sram_compiler/subcircuits/replica_column.py", "replica aggregation plan", "sram_layoutgen/openyield_adapter/array_aggregation.py", "DIRECT_MATCH", "mapped", "Replica_Column", "Replica coupling to control timing is still metadata-only.", "Keep RWL/RBL semantics explicit."),
        _mapping("row_decoder", "sram_compiler/subcircuits/decoder.py", "decoder proxy plan", "sram_layoutgen/openyield_adapter/decoder_row_rules.py", "PARTIAL_MATCH", "mapped_proxy_only", "DECODER3_8;DECODER_CASCADE", "Local flow has decoder metadata and proxy placement, not full assembled decoder routing.", "Complete decoder composite contract."),
        _mapping("wordline_decoder", "sram_compiler/subcircuits/decoder.py;sram_compiler/subcircuits/wordline_driver.py", "decoder output contracts", "sram_layoutgen/openyield_adapter/decoder_output_contracts.py", "PARTIAL_MATCH", "mapped_proxy_only", "row_decoder_to_wldriver", "Wordline handoff is metadata-only.", "Freeze handoff pin-side conventions before L1."),
        _mapping("decoder_gate_cells", "sram_compiler/subcircuits/standard_cell.py", "gate-row packing", "sram_layoutgen/openyield_adapter/gate_row_packer.py", "ALIAS_MATCH", "mapped", "gen_inv;gen_nand2;gen_nand4", "OpenYield leaf gates are generic logic; local uses replacement macro aliases.", "Keep alias list stable."),
        _mapping("wordline_driver", "sram_compiler/subcircuits/wordline_driver.py", "wordline driver adapter", "sram_layoutgen/openyield_adapter/wordlinedriver_adapter.py", "DIRECT_MATCH", "mapped", "WORDLINEDRIVER;gen_wl_driver", "Local macro is a hardcell replacement, not the literal transistor-level OpenYield subckt.", "Preserve A/B/Z semantic contract."),
        _mapping("wordline_driver_gate_cells", "sram_compiler/subcircuits/wordline_driver.py;sram_compiler/subcircuits/standard_cell.py", "gate-row packing", "sram_layoutgen/openyield_adapter/gate_row_packer.py", "PARTIAL_MATCH", "mapped_proxy_only", "PNAND2;Pinv", "Leaf factoring exists, but assembled routing is not closed.", "Keep leaf-vs-composite distinction explicit."),
        _mapping("column_mux", "sram_compiler/subcircuits/mux_and_sa.py", "column mux adapter", "sram_layoutgen/openyield_adapter/columnmux_adapter.py", "ALIAS_MATCH", "mapped", "COLUMNMUX*;gen_col_mux", "OpenYield mux may expose OUTB/SELB semantics that require repaired alias metadata.", "Keep repaired alias evidence tied to this mapping."),
        _mapping("sense_amp", "sram_compiler/subcircuits/mux_and_sa.py", "sense amp architecture adapter", "sram_layoutgen/openyield_adapter/architecture_adapter.py", "PARTIAL_MATCH", "mapped_with_qb_drop", "SENSEAMP", "Local hardcell is single-ended; OpenYield exposes Q/QB.", "Keep QB treatment explicit in the read-path contract."),
        _mapping("write_driver", "sram_compiler/subcircuits/precharge_and_write_driver.py", "write driver adapter", "sram_layoutgen/openyield_adapter/writedriver_adapter.py", "DIRECT_MATCH", "mapped", "WRITEDRIVER", "Local macro is hardcell-backed rather than literal transistor netlist.", "Preserve EN/DIN/BL/BLB semantics."),
        _mapping("precharge", "sram_compiler/subcircuits/precharge_and_write_driver.py", "gen_precharge fallback", "sram_layoutgen/netlist_writer.py", "LEGACY_FALLBACK", "partially_mapped", "PRECHARGE;gen_precharge", "Local flow still uses legacy precharge naming and active-high EN abstraction in some places.", "Normalize active-low PRE/ENB semantics."),
        _mapping("DELAY_CHAIN", "sram_compiler/subcircuits/time_generate.py", "delay timing metadata consumer", "sram_layoutgen/openyield_adapter/delay_chain_timing_metadata.py", "PARTIAL_MATCH", "metadata_only", "delay_chain;gen_delay_inv", "Local flow models a leaf inverter macro and timing metadata, not the full chain topology.", "Keep chain topology in metadata until control placement exists."),
        _mapping("PRECHARGE_ENABLE_PATH", "sram_compiler/subcircuits/time_generate.py", "", "", "NO_LOCAL_COUNTERPART", "unresolved", "PRE path", "No explicit local control-path object exists.", "Create a dedicated control-path semantic object before physical planning."),
        _mapping("SENSE_ENABLE_PATH", "sram_compiler/subcircuits/time_generate.py", "", "", "NO_LOCAL_COUNTERPART", "unresolved", "s_en path", "No explicit local control-path object exists.", "Create a dedicated control-path semantic object before physical planning."),
        _mapping("WRITE_ENABLE_PATH", "sram_compiler/subcircuits/time_generate.py", "", "", "NO_LOCAL_COUNTERPART", "unresolved", "w_en path", "No explicit local control-path object exists.", "Create a dedicated control-path semantic object before physical planning."),
        _mapping("WORDLINE_ENABLE_PATH", "sram_compiler/subcircuits/time_generate.py", "", "", "NO_LOCAL_COUNTERPART", "unresolved", "wl_en path", "No explicit local control-path object exists.", "Create a dedicated control-path semantic object before physical planning."),
        _mapping("GATED_CLOCK_PATH", "sram_compiler/subcircuits/time_generate.py", "", "", "NO_LOCAL_COUNTERPART", "unresolved", "gated_clk path", "No explicit local control-path object exists.", "Create a dedicated control-path semantic object before physical planning."),
        _mapping("DFF_ROW", "sram_compiler/subcircuits/time_generate.py", "DFF array adapter", "sram_layoutgen/openyield_adapter/dff_array_adapter.py", "PARTIAL_MATCH", "metadata_only", "ADDR_DFF;DATA_DFF;dff", "Local flow audits DFF leaf compatibility and row metadata, not full integrated control rows.", "Freeze DFF row packing contract."),
        _mapping("CONTROL_LOGIC", "sram_compiler/subcircuits/time_generate.py", "control decomposition metadata", "sram_layoutgen/openyield_adapter/control_decomposition.py", "PARTIAL_MATCH", "metadata_only", "TIME", "TIME is composite and not directly placeable in local flow.", "Keep composite control decomposition authoritative at L0."),
    ]
    rows = []
    for row in mappings:
        payload = dict(row)
        local_path = str(payload["local_layoutgen_path"])
        if local_path and local_path != "not_found" and not _repo_path_exists(repo_root, local_path):
            payload["mapping_status"] = f"{payload['mapping_status']}_path_missing"
        rows.append(payload)
    return rows


def build_connection_graph(connection_rows: list[dict[str, Any]]) -> dict[str, Any]:
    nodes = sorted({row["source_module"] for row in connection_rows} | {row["target_module"] for row in connection_rows})
    return {
        "nodes": [{"id": node} for node in nodes],
        "edges": [
            {
                "source": row["source_module"],
                "target": row["target_module"],
                "signal": row["signal_name"],
                "category": row["signal_category"],
                "confidence": row["confidence"],
            }
            for row in connection_rows
        ],
    }


def render_markdown_table(rows: list[dict[str, Any]], columns: list[str]) -> str:
    header = "| " + " | ".join(columns) + " |"
    sep = "| " + " | ".join("---" for _ in columns) + " |"
    body = []
    for row in rows:
        body.append("| " + " | ".join(_escape_md(row.get(column, "")) for column in columns) + " |")
    return "\n".join([header, sep, *body])


def write_csv(path: str | Path, rows: list[dict[str, Any]], columns: list[str]) -> None:
    out = Path(path)
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns)
        writer.writeheader()
        for row in rows:
            writer.writerow({column: _stringify(row.get(column, "")) for column in columns})


def write_text(path: str | Path, text: str) -> None:
    out = Path(path)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(text.rstrip() + "\n", encoding="utf-8")


def _stringify(value: Any) -> str:
    if isinstance(value, bool):
        return "True" if value else "False"
    if value is None:
        return ""
    return str(value)


def _openyield_path_exists(root: Path, rel_path: str) -> bool:
    if not rel_path or rel_path == "not_found_in_source":
        return False
    for part in rel_path.split(";"):
        path = part.split(":")[0].strip()
        if path and (root / path).exists():
            return True
    return False


def _repo_path_exists(root: Path, rel_path: str) -> bool:
    if not rel_path or rel_path == "not_found":
        return False
    for part in rel_path.split(";"):
        path = part.strip()
        if path and (root / path).exists():
            return True
    return False


def _escape_md(value: Any) -> str:
    text = _stringify(value)
    return text.replace("|", "\\|").replace("\n", "<br>")


def _parameter(
    parameter: str,
    meaning: str,
    source: str,
    used_by: str,
    affects_instance_count: bool,
    affects_geometry: bool,
    affects_routing: bool,
    affects_timing: bool,
    derivation_rule: str,
    example_values: str,
    unknown_or_unresolved: str,
    next_required_action: str,
) -> dict[str, Any]:
    return {
        "parameter": parameter,
        "meaning": meaning,
        "openyield_source_path": source,
        "used_by_modules": used_by,
        "affects_instance_count": affects_instance_count,
        "affects_geometry": affects_geometry,
        "affects_routing": affects_routing,
        "affects_timing": affects_timing,
        "derivation_rule": derivation_rule,
        "example_values": example_values,
        "unknown_or_unresolved": unknown_or_unresolved,
        "next_required_action": next_required_action,
    }


def _connection(
    source_module: str,
    source_port_or_signal: str,
    target_module: str,
    target_port_or_signal: str,
    signal_name: str,
    signal_category: str,
    direction: str,
    is_power: bool,
    is_clock: bool,
    is_control: bool,
    is_data: bool,
    is_bitline: bool,
    is_wordline: bool,
    is_timing_path: bool,
    evidence_source: str,
    confidence: str,
    unresolved_reason: str,
) -> dict[str, Any]:
    return {
        "source_module": source_module,
        "source_port_or_signal": source_port_or_signal,
        "target_module": target_module,
        "target_port_or_signal": target_port_or_signal,
        "signal_name": signal_name,
        "signal_category": signal_category,
        "direction": direction,
        "is_power": is_power,
        "is_clock": is_clock,
        "is_control": is_control,
        "is_data": is_data,
        "is_bitline": is_bitline,
        "is_wordline": is_wordline,
        "is_timing_path": is_timing_path,
        "evidence_source": evidence_source,
        "confidence": confidence,
        "unresolved_reason": unresolved_reason,
    }


def _variation(
    variation_axis: str,
    parameter: str,
    unchanged: str,
    instance_count_changes: str,
    structure_changes: str,
    routing_or_timing_changes: str,
    evidence: str,
    layoutgen_support_status: str,
    unresolved_gap: str,
) -> dict[str, Any]:
    return {
        "variation_axis": variation_axis,
        "openyield_parameter": parameter,
        "module_types_unchanged": unchanged,
        "instance_count_changes": instance_count_changes,
        "structure_changes": structure_changes,
        "routing_or_timing_changes": routing_or_timing_changes,
        "openyield_source_evidence": evidence,
        "layoutgen_support_status": layoutgen_support_status,
        "unresolved_gap": unresolved_gap,
    }


def _mapping(
    openyield_module: str,
    openyield_source_path: str,
    local_layoutgen_module: str,
    local_layoutgen_path: str,
    mapping_type: str,
    mapping_status: str,
    known_aliases: str,
    semantic_mismatch: str,
    next_required_action: str,
) -> dict[str, Any]:
    return {
        "openyield_module": openyield_module,
        "openyield_source_path": openyield_source_path,
        "local_layoutgen_module": local_layoutgen_module,
        "local_layoutgen_path": local_layoutgen_path or "not_found",
        "mapping_type": mapping_type,
        "mapping_status": mapping_status,
        "known_aliases": known_aliases,
        "semantic_mismatch": semantic_mismatch,
        "next_required_action": next_required_action,
    }


def _module_specs() -> list[ModuleSpec]:
    return [
        ModuleSpec("SRAM_TOP", "assembly", "sram_compiler/testbenches/sram_6t_core_testbench.py", "Sram6TCoreTestbench.create_testbench", "PySpice testbench assembly", "Implicit top-level SRAM assembly root for one-bank simulations and optimization entrypoints.", "VDD,VSS,clk,csb,web,A[i],DIN[i],BL[i],BLB[i],WL[i],RBL,RBLB,control nets", "clk,csb,web,A[i],DIN[i]", "WL[i],BL[i],BLB[i],RBL,RBLB,SA_Q[*],SA_QB[*],control nets", "VDD,VSS", "clk,clk_buf,gated_clk_bar,gated_clk_buf,rbl_delay,rbl_delay_bar", "", "BANK;CONTROL_LOGIC;row_decoder;wordline_driver;bitcell_array;replica_array;column_mux;sense_amp;write_driver;precharge", "1 implicit assembly per simulation", "num_rows;num_cols;choose_columnmux;operation", True, True, False, "hybrid/standalone top semantic contract", "sram_layoutgen/netlist_writer.py", "SOURCE_FOUND_PORTS_PARTIAL", "OpenYield top assembly is a transient testbench, not a reusable top-level SRAM subckt/macro contract.", "Freeze a canonical top-level SRAM interface independent of transient stimulus plumbing.", ("sram_compiler/testbenches/sram_6t_core_testbench.py", "main_sram.py")),
        ModuleSpec("BANK", "assembly", "sram_compiler/testbenches/sram_6t_core_testbench.py", "Sram6TCoreTestbench.create_testbench", "Implicit single-bank assembly", "Single-bank SRAM semantic wrapper implicit in the current one-array testbench flow.", "VDD,VSS,BL[i],BLB[i],WL[i],RBL,RBLB,local control nets", "A[i],DIN[i],clk,csb,web", "WL[i],BL[i],BLB[i],RBL,RBLB", "VDD,VSS", "clk_buf,gated_clk_bar,gated_clk_buf", "SRAM_TOP", "bitcell_array;replica_array;precharge;column_mux;sense_amp;write_driver", "1 implicit bank", "num_rows;num_cols", True, True, False, "", "", "LOCAL_MAPPING_UNRESOLVED", "Neither OpenYield nor current layoutgen exposes an explicit BANK object; the hierarchy is only implicit.", "Keep the current one-bank assumption explicit and avoid claiming bank-scalable hierarchy.", ("sram_compiler/testbenches/sram_6t_core_testbench.py",)),
        ModuleSpec("bitcell_array", "storage_array", "sram_compiler/subcircuits/sram_6t_core.py", "Sram6TCore", "PySpice SubCircuitFactory", "Physical storage core holding all normal SRAM cells.", "VDD,VSS,BL[i],BLB[i],WL[i]", "WL[i],BL[i],BLB[i]", "shared bitline discharge/storage behavior", "VDD,VSS", "WL transitions, read/write bitline events", "wordline_driver;precharge;write_driver", "sense_amp;column_mux;replica_array coupling", "num_rows * num_cols cells", "num_rows;num_cols;sram_cell_type", True, True, False, "storage array aggregation", "sram_layoutgen/openyield_adapter/array_aggregation.py", "SEMANTICS_CLOSED", "", "Carry these row/column semantics unchanged into L1 primitive tiling.", ("sram_compiler/subcircuits/sram_6t_core.py", "docs/mapping/openyield_netlist_to_gds_readiness_matrix.csv")),
        ModuleSpec("dummy_array", "storage_support", "sram_compiler/subcircuits/dummy_row_or_column.py", "Dummy_Row;Dummy_Column", "PySpice SubCircuitFactory", "Optional storage-boundary dummy structures for edge conditions and matching.", "VDD,VSS,BL/BLB or BL[i]/BLB[i],WL or WL[i]", "shared BL/BLB or WL", "dummy bitline/wordline loading only", "VDD,VSS", "same WL/BL events as storage edge", "SRAM_TOP;BANK", "bitcell_array boundary environment", "Dummy_Column has num_rows+3 cells; Dummy_Row has num_cols+1 cells; currently instantiation is commented out in top assembly.", "num_rows;num_cols", True, False, True, "storage array aggregation", "sram_layoutgen/openyield_adapter/array_aggregation.py", "SEMANTICS_CLOSED", "Top-level OpenYield assembly comments out dummy-row/column instantiation, so usage is config/workflow dependent rather than always-on.", "Keep dummy semantics but record that top-level usage is optional in current source path.", ("sram_compiler/subcircuits/dummy_row_or_column.py", "sram_compiler/testbenches/sram_6t_core_testbench.py")),
        ModuleSpec("replica_array", "storage_support", "sram_compiler/subcircuits/replica_column.py", "Replica_Column", "PySpice SubCircuitFactory", "Replica bitline/wordline structure feeding delay-based control timing.", "VDD,VSS,RBL,RBLB,WL[i]", "RWL and WL[i] loading", "RBL/RBLB timing response", "VDD,VSS", "RBL,rbl_delay,rbl_delay_bar", "SRAM_TOP;CONTROL_LOGIC", "DELAY_CHAIN;PRECHARGE_ENABLE_PATH;SENSE_ENABLE_PATH;WRITE_ENABLE_PATH", "num_rows+1 replica cells", "num_rows;num_cols;sram_cell_type", True, True, False, "replica aggregation plan", "sram_layoutgen/openyield_adapter/array_aggregation.py", "SEMANTICS_CLOSED", "", "Keep RWL/RBL semantics as first-class L0 contract terms.", ("sram_compiler/subcircuits/replica_column.py", "sram_compiler/testbenches/sram_6t_core_testbench.py")),
        ModuleSpec("row_decoder", "decoder", "sram_compiler/subcircuits/decoder.py", "DECODER3_8;DECODER_CASCADE", "PySpice hierarchical decoder", "Decodes registered row address bits into one-hot decoder wordline intents.", "VDD,VSS,EN,A0..A2,WL0..WL7 and cascade A[i],WL[i]", "A[i],EN", "WL[i] one-hot outputs", "VDD,VSS", "Address-dependent decode propagation", "DFF_ROW;CONTROL_LOGIC", "wordline_driver", "DECODER3_8 groups of 8; cascade depth = ceil(ceil(log2(num_rows))/3)", "num_rows;row_addr_size", True, True, False, "decoder contracts / proxy rows", "sram_layoutgen/openyield_adapter/decoder_row_rules.py;sram_layoutgen/openyield_adapter/decoder_output_contracts.py", "SEMANTICS_CLOSED", "", "Carry decoder bit ordering and enable cascading rules into the local semantic contract.", ("sram_compiler/subcircuits/decoder.py", "docs/openyield_module_contracts.md")),
        ModuleSpec("wordline_decoder", "decoder", "sram_compiler/testbenches/sram_6t_core_testbench.py;sram_compiler/subcircuits/wordline_driver.py", "Sram6TCoreTestbench.create_decoder;create_wl_driver", "Assembly connection between decoder and WL driver", "Composite decoder-to-wordline-driver handoff layer.", "DEC_WL[i],WL_EN -> WL[i]", "DEC_WL[i],WL_EN", "WL[i]", "VDD,VSS", "WL_EN; decoder propagation", "row_decoder;CONTROL_LOGIC", "wordline_driver;bitcell_array", "one driver per row", "num_rows;num_cols", True, True, False, "decoder output handoff metadata", "sram_layoutgen/openyield_adapter/decoder_output_contracts.py", "SOURCE_FOUND_CONNECTIONS_UNRESOLVED", "Source proves handoff semantics, but local layoutgen still treats this boundary as metadata/proxy rather than a closed routed composite.", "Freeze a canonical decoder-output to WL-driver pin/side contract before L1.", ("sram_compiler/testbenches/sram_6t_core_testbench.py", "docs/openyield_decoder_output_contract_report.md")),
        ModuleSpec("decoder_gate_cells", "decoder_leaf", "sram_compiler/subcircuits/decoder.py;sram_compiler/subcircuits/standard_cell.py", "AND2;AND3;Pinv inside DECODER3_8", "Hierarchical gate composition", "Leaf logic cells composing the decoder.", "VDD,VSS,A,B,C,Z", "decoder internal nets", "decoder internal nets", "VDD,VSS", "decoder internal logic delay", "row_decoder", "row_decoder", "Scales with number of decode terms and cascade groups", "num_rows", True, True, False, "gate-row packing", "sram_layoutgen/openyield_adapter/gate_row_packer.py", "SOURCE_FOUND_PORTS_PARTIAL", "Leaf presence is known, but exact composite grouping/routing ownership is still local-flow specific.", "Keep a separate leaf-cell inventory distinct from assembled decoder semantics.", ("sram_compiler/subcircuits/decoder.py", "sram_compiler/subcircuits/standard_cell.py")),
        ModuleSpec("wordline_driver", "row_driver", "sram_compiler/subcircuits/wordline_driver.py", "WordlineDriver", "PySpice SubCircuitFactory", "Boosts decoder output plus WL enable into the physical WL rail.", "VDD,VSS,A,B,Z", "A(decoder_input),B(wordline_enable)", "Z(WL)", "VDD,VSS", "WL enable timing", "row_decoder;CONTROL_LOGIC", "bitcell_array;replica_array via RWL analogue", "one instance per physical row", "num_rows;num_cols", True, True, False, "wordline driver adapter", "sram_layoutgen/openyield_adapter/wordlinedriver_adapter.py", "SEMANTICS_CLOSED", "", "Preserve A/B/Z active-high semantics as the authoritative local mapping.", ("sram_compiler/subcircuits/wordline_driver.py", "docs/openyield_wordlinedriver_adapter_report.md")),
        ModuleSpec("wordline_driver_gate_cells", "row_driver_leaf", "sram_compiler/subcircuits/wordline_driver.py;sram_compiler/subcircuits/standard_cell.py", "PNAND2;Pinv inside WordlineDriver", "Hierarchical gate composition", "Leaf logic cells used to build the wordline driver.", "VDD,VSS,A,B,Z", "decoder_input;wordline_enable", "wl", "VDD,VSS", "WL drive delay", "wordline_driver", "wordline_driver", "one NAND2 + one inverter per WL driver", "num_rows;num_cols", True, True, False, "gate-row packing", "sram_layoutgen/openyield_adapter/gate_row_packer.py", "SOURCE_FOUND_PORTS_PARTIAL", "Leaf factoring is known, but local flow closes only the assembled WORDLINEDRIVER semantic contract.", "Keep leaf-vs-composite wordline-driver semantics separate.", ("sram_compiler/subcircuits/wordline_driver.py",)),
        ModuleSpec("column_mux", "read_peripheral", "sram_compiler/subcircuits/mux_and_sa.py;sram_compiler/testbenches/sram_6t_core_testbench.py", "ColumnMux;Sram6TCoreTestbench.create_read_periphery", "PySpice SubCircuitFactory + testbench group instantiation", "Selects one of multiple BL/BLB pairs onto a sense-amp input pair.", "VDD,VSS,SA_IN,SA_INB,SEL[i],SELB[i],BL[i],BLB[i]", "SEL/SELB,BL[i],BLB[i]", "SA_IN,SA_INB", "VDD,VSS", "SEL pulse timing", "precharge;bitcell_array", "sense_amp", "If choose_columnmux is false, not instantiated; else group count = num_cols / 2 in current source.", "choose_columnmux;num_cols;column_mux_ratio", True, False, True, "column mux adapter", "sram_layoutgen/openyield_adapter/columnmux_adapter.py;sram_layoutgen/openyield_adapter/columnmux_placement.py", "SEMANTICS_CLOSED", "", "Keep explicit note that current source proves only ratio-2 mux groups.", ("sram_compiler/subcircuits/mux_and_sa.py", "sram_compiler/testbenches/sram_6t_core_testbench.py")),
        ModuleSpec("sense_amp", "read_peripheral", "sram_compiler/subcircuits/mux_and_sa.py;sram_compiler/testbenches/sram_6t_core_testbench.py", "SenseAmp;Sram6TCoreTestbench.create_read_periphery", "PySpice SubCircuitFactory + per-group instantiation", "Differential read sense amplifier with enable.", "VDD,VSS,EN,IN,INB,Q,QB", "EN,IN,INB", "Q,QB", "VDD,VSS", "s_en", "column_mux or bitcell_array", "D_latch / readout path", "Without mux: one per column; with mux: one per selected group.", "choose_columnmux;num_cols", True, False, True, "architecture adapter", "sram_layoutgen/openyield_adapter/architecture_adapter.py;sram_layoutgen/openyield_adapter/senseamp_placement.py", "SEMANTICS_CLOSED", "", "Retain explicit Q/QB vs local single-ended dout mismatch note in the mapping layer.", ("sram_compiler/subcircuits/mux_and_sa.py", "docs/openyield_senseamp_adapter_report.md")),
        ModuleSpec("write_driver", "write_peripheral", "sram_compiler/subcircuits/precharge_and_write_driver.py;sram_compiler/testbenches/sram_6t_core_testbench.py", "WriteDriver;Sram6TCoreTestbench.create_write_periphery", "PySpice SubCircuitFactory + per-column instantiation", "Drives BL/BLB for writes under write enable.", "VDD,VSS,EN,DIN,BL,BLB", "EN,DIN", "BL,BLB", "VDD,VSS", "w_en", "DFF_ROW;CONTROL_LOGIC", "bitcell_array", "one per physical column", "num_cols", True, False, True, "write driver adapter", "sram_layoutgen/openyield_adapter/writedriver_adapter.py;sram_layoutgen/openyield_adapter/writedriver_placement.py", "SEMANTICS_CLOSED", "", "Carry EN/DIN/BL/BLB semantics unchanged into local contracts.", ("sram_compiler/subcircuits/precharge_and_write_driver.py", "sram_compiler/testbenches/sram_6t_core_testbench.py")),
        ModuleSpec("precharge", "read_peripheral", "sram_compiler/subcircuits/precharge_and_write_driver.py;sram_compiler/testbenches/sram_6t_core_testbench.py", "Precharge;Sram6TCoreTestbench.create_read_periphery", "PySpice SubCircuitFactory + per-column instantiation", "Precharges and equalizes BL/BLB pairs through an active-low enable input.", "VDD,ENB,BL,BLB", "ENB", "precharged BL/BLB", "VDD", "PRE", "CONTROL_LOGIC", "bitcell_array;column_mux;sense_amp", "Read path: one per physical column plus one replica-column precharge; write path: replica only in current source.", "num_rows;num_cols;operation", True, False, True, "precharge fallback / control candidate contract", "sram_layoutgen/netlist_writer.py;sram_layoutgen/openyield_adapter/control_path_candidate_generation.py", "SEMANTICS_CLOSED", "Local flow still mixes legacy `gen_precharge` naming with OpenYield active-low PRE semantics, but the L0 behavior is source-backed and understood.", "Keep PRE as active-low / ENB semantic in the canonical contract.", ("sram_compiler/subcircuits/precharge_and_write_driver.py", "sram_compiler/testbenches/sram_6t_core_testbench.py")),
        ModuleSpec("DELAY_CHAIN", "control_timing", "sram_compiler/subcircuits/time_generate.py", "DelayChain;WenDelayChain", "PySpice control/timing subcircuit", "Replica-bitline delay model used to generate read/write control timing.", "VDD,VSS,in,out", "rbl or rbl_delay_bar", "rbl_delay or delayed w_en input", "VDD,VSS", "rbl_delay,rbl_delay_bar", "replica_array;CONTROL_LOGIC", "SENSE_ENABLE_PATH;WRITE_ENABLE_PATH;PRECHARGE_ENABLE_PATH", "DelayChain always one per top assembly; WenDelayChain only for write and num_rows=16,num_cols=512.", "num_rows;num_cols;operation;delay_chain_related_parameters", True, True, False, "delay-chain metadata consumer", "sram_layoutgen/openyield_adapter/delay_chain_timing_metadata.py", "SOURCE_FOUND_PORTS_KNOWN", "Local flow consumes delay-chain metadata and leaf delay macros, but not the full assembled chain topology.", "Keep chain topology and special-case WenDelayChain rule explicit before L1.", ("sram_compiler/subcircuits/time_generate.py", "docs/openyield_delay_chain_timing_metadata_report.md")),
        ModuleSpec("PRECHARGE_ENABLE_PATH", "control_timing", "sram_compiler/subcircuits/time_generate.py", "TIME.pre path logic", "Internal TIME composite path", "Generates PRE from gated clock, replica delay, and wl_en_bar conditions.", "gated_clk_buf,rbl_delay,wl_en_bar -> PRE_UNBUF -> PRE", "gated_clk_buf,rbl_delay,wl_en_bar", "PRE", "VDD,VSS", "rbl_delay;wl_en_bar", "CONTROL_LOGIC;DELAY_CHAIN", "precharge", "one logical path per top assembly", "num_rows;num_cols;control_timing_related_parameters", True, True, False, "", "", "SOURCE_FOUND_CONNECTIONS_UNRESOLVED", "The source-backed Boolean/timing relation is known, but there is no isolated local object or physical decomposition boundary.", "Create a dedicated control-path semantic object and truth table before L1.", ("sram_compiler/subcircuits/time_generate.py", "docs/mapping/openyield_control_timing_mapping.csv")),
        ModuleSpec("SENSE_ENABLE_PATH", "control_timing", "sram_compiler/subcircuits/time_generate.py", "TIME.s_en path logic", "Internal TIME composite path", "Generates sense_amp enable from replica delay, gated clock bar, and we_bar.", "rbl_delay,gated_clk_bar,we_bar -> s_en", "rbl_delay,gated_clk_bar,we_bar", "s_en", "VDD,VSS", "rbl_delay;gated_clk_bar", "CONTROL_LOGIC;DELAY_CHAIN", "sense_amp", "one logical path per top assembly", "num_rows;num_cols;control_timing_related_parameters", True, True, False, "", "", "SOURCE_FOUND_CONNECTIONS_UNRESOLVED", "Boolean relation is source-backed, but local mapping is still candidate-contract only.", "Capture this as a standalone control-path semantic contract.", ("sram_compiler/subcircuits/time_generate.py", "docs/mapping/openyield_control_timing_mapping.csv")),
        ModuleSpec("WRITE_ENABLE_PATH", "control_timing", "sram_compiler/subcircuits/time_generate.py", "TIME.w_en path logic", "Internal TIME composite path", "Generates write enable from delay, gated clock bar, and WE.", "rbl_delay_bar or rbl_delay_bar_wen,gated_clk_bar,we -> w_en", "rbl_delay_bar,gated_clk_bar,we", "w_en", "VDD,VSS", "rbl_delay_bar;rbl_delay_bar_wen", "CONTROL_LOGIC;DELAY_CHAIN", "write_driver", "one logical path per top assembly", "num_rows;num_cols;operation;delay_chain_related_parameters", True, True, False, "", "", "SOURCE_FOUND_CONNECTIONS_UNRESOLVED", "Special-case WenDelayChain injection for 16x512 write mode is source-backed but not generalized.", "Freeze the special case and decide whether it remains source-compatible or becomes a tunable rule.", ("sram_compiler/subcircuits/time_generate.py", "docs/mapping/openyield_control_timing_mapping.csv")),
        ModuleSpec("WORDLINE_ENABLE_PATH", "control_timing", "sram_compiler/subcircuits/time_generate.py", "TIME.wl_en path logic", "Internal TIME composite path", "Generates wl_en and wl_en_bar from gated clock bar.", "gated_clk_bar -> wl_en -> wl_en_bar", "gated_clk_bar", "wl_en,wl_en_bar", "VDD,VSS", "gated_clk_bar", "CONTROL_LOGIC;GATED_CLOCK_PATH", "wordline_driver;PRECHARGE_ENABLE_PATH", "one logical path per top assembly", "num_rows;num_cols;control_timing_related_parameters", True, True, False, "", "", "SOURCE_FOUND_CONNECTIONS_UNRESOLVED", "Relation is clear in source, but local control-row decomposition still treats it as metadata only.", "Make wl_en polarity and downstream consumers part of the frozen L0 contract.", ("sram_compiler/subcircuits/time_generate.py", "docs/mapping/openyield_control_timing_mapping.csv")),
        ModuleSpec("GATED_CLOCK_PATH", "control_timing", "sram_compiler/subcircuits/time_generate.py", "TIME.gated clock logic", "Internal TIME composite path", "Builds gated_clk_bar and gated_clk_buf from cs plus clock polarity signals.", "cs,clk_bar -> gated_clk_bar; cs,clk_buf -> gated_clk_buf", "cs,clk_bar,clk_buf", "gated_clk_bar,gated_clk_buf", "VDD,VSS", "clk_buf,clk_bar,gated_clk_bar,gated_clk_buf", "CONTROL_LOGIC;DFF_ROW", "WORDLINE_ENABLE_PATH;SENSE_ENABLE_PATH;WRITE_ENABLE_PATH;PRECHARGE_ENABLE_PATH", "one logical path per top assembly", "num_rows;num_cols;control_timing_related_parameters", True, True, False, "", "", "SOURCE_FOUND_CONNECTIONS_UNRESOLVED", "Clock gating semantics are source-backed, but no dedicated local control-path object exists.", "Split clock-gating semantics from generic TIME composite notes.", ("sram_compiler/subcircuits/time_generate.py", "docs/mapping/openyield_control_timing_mapping.csv")),
        ModuleSpec("DFF_ROW", "control_timing", "sram_compiler/subcircuits/time_generate.py", "ADDR_DFF;DATA_DFF;DFF_BUF;dff", "Composite DFF arrays inside TIME", "Registered address/data capture layer feeding decoder and write driver.", "VDD,VSS,CLK,A[i],A_dff[i],DIN[i],DIN_dff[i],csb/cs,web/we", "clk_buf,A[i],DIN[i],csb,web", "A_dff[i],DIN_dff[i],cs,we,cs_bar,we_bar", "VDD,VSS", "clk,clk_buf", "SRAM_TOP;CONTROL_LOGIC", "row_decoder;write_driver;GATED_CLOCK_PATH", "ADDR_DFF count = ceil(log2(num_rows)); DATA_DFF count = num_cols only for write/read&write; CS/WE each use one DFF_BUF.", "num_rows;num_cols;operation", True, True, False, "DFF array adapter", "sram_layoutgen/openyield_adapter/dff_array_adapter.py;sram_layoutgen/openyield_adapter/dff_array_placement.py", "SOURCE_FOUND_PORTS_KNOWN", "Leaf DFF compatibility is audited, but integrated control-row placement remains metadata-only.", "Freeze row-count formulas and per-domain meanings before L1.", ("sram_compiler/subcircuits/time_generate.py", "docs/openyield_dff_array_adapter_report.md")),
        ModuleSpec("CONTROL_LOGIC", "control_timing", "sram_compiler/subcircuits/time_generate.py", "TIME", "Composite TIME subcircuit", "Central composite block that latches controls, generates gated clocks, wordline enable, precharge enable, sense enable, and write enable.", "VDD,VSS,clk,csb,web,clk_buf,clk_bar,cs_bar,cs,we_bar,we,gated_clk_bar,gated_clk_buf,wl_en,A[i],A_dff[i],DIN[i],DIN_dff[i],rbl,rbl_delay,rbl_delay_bar,s_en,w_en,PRE", "clk,csb,web,A[i],DIN[i],rbl", "clk_buf,clk_bar,cs_bar,cs,we_bar,we,gated_clk_bar,gated_clk_buf,wl_en,rbl_delay,rbl_delay_bar,s_en,w_en,PRE,A_dff[i],DIN_dff[i]", "VDD,VSS", "all internal control/timing nets", "SRAM_TOP;replica_array", "DFF_ROW;GATED_CLOCK_PATH;WORDLINE_ENABLE_PATH;PRECHARGE_ENABLE_PATH;SENSE_ENABLE_PATH;WRITE_ENABLE_PATH", "one TIME block per top assembly", "num_rows;num_cols;operation;control_timing_related_parameters", True, True, False, "control decomposition metadata", "sram_layoutgen/openyield_adapter/control_decomposition.py", "SOURCE_FOUND_PORTS_PARTIAL", "TIME mixes reusable control logic with transient stimulus assumptions and local layoutgen has no direct physical counterpart.", "Freeze TIME decomposition into stable subcontracts before L1.", ("sram_compiler/subcircuits/time_generate.py", "docs/openyield_time_control_decomposition_report.md")),
        ModuleSpec("routing_semantics", "integration_semantics", "sram_compiler/testbenches/sram_6t_core_testbench.py", "create_read_periphery;create_write_periphery;create_decoder;create_wl_driver", "Assembly-level connectivity semantics", "Logical connection obligations between arrays, peripherals, and control paths before physical routing exists.", "BL/BLB buses, WL buses, address buses, data buses, control nets", "all inter-module nets", "all inter-module nets", "VDD,VSS", "rbl_delay family;gated clocks", "all functional modules", "all functional modules", "scales with every parameterized module count", "num_rows;num_cols;choose_columnmux", True, True, False, "standalone structural netlist", "sram_layoutgen/netlist_writer.py", "LOCAL_MAPPING_UNRESOLVED", "Local standalone routing semantics still use a separate legacy abstraction and are not yet frozen to OpenYield contracts.", "Replace ad hoc local naming with canonical L0 net semantics before L1.", ("sram_compiler/testbenches/sram_6t_core_testbench.py", "sram_layoutgen/netlist_writer.py")),
        ModuleSpec("power_semantics", "integration_semantics", "sram_compiler/subcircuits/base_subcircuit.py;sram_compiler/testbenches/sram_6t_core_testbench.py", "BaseSubcircuit;create_testbench", "Global supply convention", "Common VDD/VSS power convention shared by all OpenYield subcircuits.", "VDD,VSS or VDD-only in PRECHARGE", "global supplies", "global supplies", "VDD,VSS", "", "SRAM_TOP", "all modules", "global across all instances", "num_rows;num_cols only through fanout", True, True, False, "rail continuity metadata", "sram_layoutgen/openyield_adapter/hardcell_power_rail_continuity.py", "SOURCE_FOUND_PORTS_KNOWN", "Power naming is clear, but global shared-rail continuity across all local domains is not yet proven.", "Keep VDD/VSS naming canonical and defer physical continuity claims to later layers.", ("sram_compiler/subcircuits/base_subcircuit.py", "docs/openyield_hardcell_power_rail_continuity_report.md")),
        ModuleSpec("timing_semantics", "integration_semantics", "sram_compiler/subcircuits/time_generate.py;sram_compiler/testbenches/sram_6t_core_MC_testbench.py", "TIME;MC timing measurements", "Composite control timing + measurement semantics", "Semantic timing model for read/write sequencing and measurement points.", "clk,csb,web,rbl,rbl_delay,rbl_delay_bar,w_en,s_en,PRE,WL[i],BL[i],SA_Q[*]", "stimulus clocks/controls and replica timing nodes", "measured delays and enables", "VDD,VSS", "all control/timing nets", "CONTROL_LOGIC;DELAY_CHAIN;replica_array", "all timed read/write peripherals", "one timing semantic set per operation mode", "num_rows;num_cols;operation;delay_chain_related_parameters", True, True, False, "timing metadata consumer", "sram_layoutgen/openyield_adapter/timing_metadata_consumer.py", "SOURCE_FOUND_PORTS_PARTIAL", "Source gives mixed circuit semantics and transient-measurement semantics rather than a clean reusable timing contract.", "Split reusable enable ordering from simulator-only pulse definitions before L1.", ("sram_compiler/subcircuits/time_generate.py", "sram_compiler/testbenches/sram_6t_core_MC_testbench.py")),
    ]

