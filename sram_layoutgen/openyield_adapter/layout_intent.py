from __future__ import annotations

import csv
import json
import math
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any


L3_TARGET_MODULES = (
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
)

MODULE_PHYSICAL_ROLE_MAP = {
    "bitcell_array": ("ARRAY_CORE", "ARRAY_PATH"),
    "dummy_array": ("ARRAY_DUMMY", "ARRAY_PATH"),
    "replica_array": ("ARRAY_REPLICA", "ARRAY_PATH"),
    "row_decoder": ("ROW_DECODER", "ROW_PATH"),
    "wordline_decoder": ("ROW_DECODER", "ROW_PATH"),
    "decoder_gate_cells": ("ROW_DECODER", "ROW_PATH"),
    "wordline_driver": ("WORDLINE_DRIVER", "ROW_PATH"),
    "wordline_driver_gate_cells": ("WORDLINE_DRIVER", "ROW_PATH"),
    "precharge": ("COLUMN_PRECHARGE", "COLUMN_PATH"),
    "column_mux": ("COLUMN_MUX", "COLUMN_PATH"),
    "sense_amp": ("SENSE_AMP", "COLUMN_PATH"),
    "write_driver": ("WRITE_DRIVER", "COLUMN_PATH"),
    "CONTROL_LOGIC": ("CONTROL_LOGIC", "CONTROL_PATH"),
    "DELAY_CHAIN": ("DELAY_CHAIN", "CONTROL_PATH"),
    "PRECHARGE_ENABLE_PATH": ("ENABLE_PATH", "CONTROL_PATH"),
    "SENSE_ENABLE_PATH": ("ENABLE_PATH", "CONTROL_PATH"),
    "WRITE_ENABLE_PATH": ("ENABLE_PATH", "CONTROL_PATH"),
    "WORDLINE_ENABLE_PATH": ("ENABLE_PATH", "CONTROL_PATH"),
    "GATED_CLOCK_PATH": ("CLOCK_PATH", "CONTROL_PATH"),
    "DFF_ROW": ("DFF_ROW", "CONTROL_PATH"),
}

NET_CATEGORY_MAP = {
    "address": "ADDRESS",
    "decoder_wordline": "WORDLINE",
    "wordline": "WORDLINE",
    "bitline": "BITLINE",
    "bitline_bar": "BITLINE_BAR",
    "data_in": "DATA_IN",
    "data_out": "DATA_OUT",
    "control": "CONTROL",
    "clock": "CLOCK",
    "power": "POWER",
    "ground": "GROUND",
    "timing_replica": "TIMING_REPLICA",
    "timing": "TIMING_REPLICA",
    "replica": "TIMING_REPLICA",
}

LAYOUT_ROLE_MAP = {
    "ADDRESS": "address_distribution",
    "WORDLINE": "row_pitch_aligned_wordline",
    "BITLINE": "column_pitch_aligned_bitline",
    "BITLINE_BAR": "column_pitch_aligned_bitline_bar",
    "DATA_IN": "write_data_delivery",
    "DATA_OUT": "read_data_observation",
    "CONTROL": "control_enable_distribution",
    "CLOCK": "clock_distribution",
    "POWER": "power_distribution",
    "GROUND": "ground_distribution",
    "TIMING_REPLICA": "replica_timing_distribution",
    "INTERNAL_CONTRACT": "internal_contract_placeholder",
    "UNKNOWN": "unknown_layout_role",
}

EXPECTED_DIRECTION_MAP = {
    "ADDRESS": "periphery_bus",
    "WORDLINE": "horizontal_across_array_rows",
    "BITLINE": "vertical_along_array_columns",
    "BITLINE_BAR": "vertical_along_array_columns",
    "DATA_IN": "periphery_to_column_path",
    "DATA_OUT": "column_path_to_top_io",
    "CONTROL": "periphery_control_spine",
    "CLOCK": "top_clock_spine",
    "POWER": "top_level_rails_and_stitches",
    "GROUND": "top_level_rails_and_stitches",
    "TIMING_REPLICA": "replica_chain_periphery_route",
    "INTERNAL_CONTRACT": "contract_only",
    "UNKNOWN": "unknown",
}

EXPECTED_LAYER_HINT_MAP = {
    "ADDRESS": "control_or_address_bus_layer",
    "WORDLINE": "row_path_and_wordline_distribution_layer",
    "BITLINE": "bitline_stack",
    "BITLINE_BAR": "bitline_stack",
    "DATA_IN": "column_path_input_layer",
    "DATA_OUT": "column_path_output_layer",
    "CONTROL": "control_bus_layer",
    "CLOCK": "clock_distribution_layer",
    "POWER": "power_rail_layers",
    "GROUND": "power_rail_layers",
    "TIMING_REPLICA": "control_timing_layer",
    "INTERNAL_CONTRACT": "contract_only",
    "UNKNOWN": "unknown",
}

POWER_NET_NAMES = ("VDD", "VSS", "GND")


def _json_dump(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8", newline="\n")


def _write_csv(path: Path, fieldnames: list[str], rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def _load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _load_csv_rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def _load_csv_by_key(path: Path, key: str) -> dict[str, dict[str, str]]:
    rows = _load_csv_rows(path)
    return {str(row[key]): row for row in rows}


def _bool_from_str(value: Any) -> bool:
    return str(value).strip().lower() == "true"


def _ceil_log2(value: int) -> int:
    if value <= 1:
        return 0
    return math.ceil(math.log2(value))


def _md_table(columns: list[str], rows: list[dict[str, Any]]) -> str:
    lines = [
        "| " + " | ".join(columns) + " |",
        "| " + " | ".join(["---"] * len(columns)) + " |",
    ]
    for row in rows:
        lines.append("| " + " | ".join(str(row.get(col, "")).replace("\n", "<br>") for col in columns) + " |")
    return "\n".join(lines) + "\n"


@dataclass(frozen=True)
class CanonicalSramLayoutParameters:
    parameters: list[dict[str, Any]]
    supported_scope: dict[str, Any]


@dataclass(frozen=True)
class ArrayTopologyContract:
    summary: dict[str, Any]


@dataclass(frozen=True)
class RowPathIntent:
    summary: dict[str, Any]


@dataclass(frozen=True)
class ColumnPathIntent:
    summary: dict[str, Any]


@dataclass(frozen=True)
class ControlPathIntent:
    summary: dict[str, Any]


@dataclass(frozen=True)
class PowerIntent:
    summary: dict[str, Any]


@dataclass(frozen=True)
class PinIntent:
    summary: dict[str, Any]


@dataclass(frozen=True)
class NetToLayoutRole:
    net_name: str
    net_category: str
    layout_role: str
    source_module: str
    source_pin: str
    target_modules: str
    target_pins: str
    expected_geometry_direction: str
    expected_routing_layer_hint: str
    requires_pitch_alignment: bool
    requires_top_level_routing: bool
    requires_power_stitching: bool
    is_control_signal: bool
    is_wordline: bool
    is_bitline: bool
    is_power: bool
    is_clock: bool
    source_evidence: str
    status: str
    next_required_action: str


@dataclass(frozen=True)
class ModuleToPhysicalRole:
    module_name: str
    physical_role: str
    path_group: str
    source_openyield_semantics: str
    source_existing_gds: str
    source_existing_metadata: str
    uses_candidate_geometry: bool
    uses_contract_pins: bool
    requires_row_pitch_alignment: bool
    requires_column_pitch_alignment: bool
    requires_power_stitching: bool
    requires_top_level_routing: bool
    required_by_structure_complete_gds: bool
    current_readiness_for_R3: str
    current_readiness_for_R4: str
    blocking_gap: str
    next_required_action: str


@dataclass(frozen=True)
class OpenYieldLayoutIntent:
    intent_name: str
    canonical_parameters: CanonicalSramLayoutParameters
    top_level_goal: str
    layout_boundary: str
    source_artifacts: list[str]


class LayoutIntentBuilder:
    def __init__(self, context: dict[str, Any]) -> None:
        self.context = context
        self.repo_root: Path = context["repo_root"]
        self.openyield_root: Path = context["openyield_root"]
        self.out_dir: Path = context["out_dir"]
        self.out_matrix_csv: Path = context["out_matrix_csv"]
        self.out_matrix_md: Path = context["out_matrix_md"]
        self.out_json: Path = context["out_json"]
        self.out_report: Path = context["out_report"]

        self.openram_audit = _load_json(context["openram_audit_json"])
        self.openram_reuse_matrix = _load_csv_rows(context["openram_reuse_matrix"])
        self.canonical_contract = _load_json(context["canonical_contract"])
        self.top_bank_contract = _load_json(context["top_bank_contract"])
        self.parameter_map_rows = _load_csv_rows(context["parameter_map"])
        self.module_connection_rows = _load_csv_rows(context["module_connection_matrix"])
        self.decoder_wordline_contract = _load_json(context["decoder_wordline_contract"])
        self.time_control_contract = _load_json(context["time_control_contract"])
        self.control_path_contract_rows = _load_csv_rows(context["control_path_contracts"])
        self.module_gds_inventory_rows = _load_csv_rows(context["module_gds_inventory"])
        self.module_generator_inventory_rows = _load_csv_rows(context["module_generator_inventory"])

        self.module_gds_inventory = {row["module"]: row for row in self.module_gds_inventory_rows}
        self.module_generator_inventory = {row["module"]: row for row in self.module_generator_inventory_rows}
        self.module_gds_dir: Path = context["module_gds_dir"]

        self.old_candidate_artifacts = {
            "l5_report_json": str(context["l5_report_json"]),
            "l6_report_json": str(context["l6_report_json"]),
            "step8_report_json": str(context["step8_report_json"]),
            "top_candidate_gds": str(context["top_gds"]),
        }

        self.outputs: dict[str, Path] = {}

    def run(self) -> dict[str, Any]:
        canonical = self._build_canonical_parameters()
        module_roles = self._build_module_roles()
        net_roles = self._build_net_roles()
        array_contract = self._build_array_topology_contract(canonical)
        row_path = self._build_row_path_intent(module_roles, canonical)
        column_path = self._build_column_path_intent(module_roles, canonical)
        control_path = self._build_control_path_intent(module_roles, canonical)
        power_intent = self._build_power_intent(module_roles)
        pin_intent = self._build_pin_intent(module_roles)
        layout_intent = self._build_layout_intent(canonical)
        matrix_rows = self._build_layout_intent_matrix()

        self._emit_layout_intent(layout_intent)
        self._emit_array_topology_contract(array_contract)
        self._emit_row_path_intent(row_path)
        self._emit_column_path_intent(column_path)
        self._emit_control_path_intent(control_path)
        self._emit_power_intent(power_intent)
        self._emit_pin_intent(pin_intent)
        self._emit_net_role_map(net_roles)
        self._emit_module_role_map(module_roles)
        self._emit_layout_intent_matrix(matrix_rows)
        self._emit_gap_summary(module_roles, net_roles)

        report = self._build_report(canonical, module_roles, net_roles)
        self._emit_report(report)
        return report

    def _current_supported_defaults(self) -> dict[str, int]:
        return {
            "word_size": 4,
            "num_words": 4,
            "words_per_row": 1,
            "num_rows": 4,
            "num_cols": 4,
            "column_mux_ratio": 1,
        }

    def _build_canonical_parameters(self) -> CanonicalSramLayoutParameters:
        defaults = self._current_supported_defaults()
        num_words = defaults["num_words"]
        word_size = defaults["word_size"]
        words_per_row = defaults["words_per_row"]
        num_rows = defaults["num_rows"]
        num_cols = defaults["num_cols"]
        column_mux_ratio = defaults["column_mux_ratio"]
        num_banks = 1
        num_ports = 1
        row_address_width = _ceil_log2(num_rows)
        column_address_width = _ceil_log2(words_per_row)
        address_width = row_address_width + column_address_width

        supported_scope = {
            "single_bank": True,
            "single_implicit_readwrite_port": True,
            "num_ports_supported": 1,
            "write_mask_supported": False,
            "words_per_row_supported_values": [1, 2],
            "column_mux_ratio_supported_values": [1, 2],
            "multi_bank_supported": False,
            "multi_port_supported": False,
        }
        parameters = [
            {
                "parameter_name": "word_size",
                "value": word_size,
                "source": "DEFAULT_FOR_CURRENT_SUPPORTED_SCOPE",
                "evidence_file": "docs/mapping/openyield_canonical_sram_semantic_contract.json;docs/mapping/openyield_module_gds_inventory.csv",
                "why_it_matters": "Defines data width and column-path bit count for the frozen current-supported layout intent baseline.",
            },
            {
                "parameter_name": "num_words",
                "value": num_words,
                "source": "DEFAULT_FOR_CURRENT_SUPPORTED_SCOPE",
                "evidence_file": "docs/mapping/openyield_canonical_sram_semantic_contract.json",
                "why_it_matters": "Defines logical depth for the frozen current-supported layout intent baseline.",
            },
            {
                "parameter_name": "words_per_row",
                "value": words_per_row,
                "source": "DEFAULT_FOR_CURRENT_SUPPORTED_SCOPE",
                "evidence_file": "docs/mapping/openyield_canonical_sram_semantic_contract.json;docs/mapping/openyield_logical_to_openyield_parameter_map.csv",
                "why_it_matters": "Controls whether column muxing is required in the current-supported layout intent baseline.",
            },
            {
                "parameter_name": "num_rows",
                "value": num_rows,
                "source": "DERIVED_FROM_CONTRACT",
                "evidence_file": "docs/mapping/openyield_logical_to_openyield_parameter_map.csv",
                "why_it_matters": "Determines wordline count and row-path pitch alignment requirements.",
            },
            {
                "parameter_name": "num_cols",
                "value": num_cols,
                "source": "DERIVED_FROM_CONTRACT",
                "evidence_file": "docs/mapping/openyield_logical_to_openyield_parameter_map.csv",
                "why_it_matters": "Determines BL/BR count and column-path pitch alignment requirements.",
            },
            {
                "parameter_name": "column_mux_ratio",
                "value": column_mux_ratio,
                "source": "DERIVED_FROM_CONTRACT",
                "evidence_file": "docs/mapping/openyield_logical_to_openyield_parameter_map.csv",
                "why_it_matters": "Determines whether column_mux is structurally required in the current-supported layout intent baseline.",
            },
            {
                "parameter_name": "num_banks",
                "value": num_banks,
                "source": "DERIVED_FROM_CONTRACT",
                "evidence_file": "docs/mapping/openyield_canonical_sram_semantic_contract.json;docs/mapping/openyield_top_bank_semantic_contract.json",
                "why_it_matters": "Current layout intent stays inside the single-bank semantic scope.",
            },
            {
                "parameter_name": "num_ports",
                "value": num_ports,
                "source": "DERIVED_FROM_CONTRACT",
                "evidence_file": "docs/mapping/openyield_canonical_sram_semantic_contract.json",
                "why_it_matters": "Current layout intent stays inside the single-port semantic scope.",
            },
            {
                "parameter_name": "port_type",
                "value": "single_implicit_readwrite",
                "source": "DERIVED_FROM_CONTRACT",
                "evidence_file": "docs/mapping/openyield_canonical_sram_semantic_contract.json;docs/mapping/openyield_top_bank_semantic_contract.json",
                "why_it_matters": "Explains that a shared csb/web-controlled read/write port model is assumed.",
            },
            {
                "parameter_name": "write_mask_supported",
                "value": False,
                "source": "DERIVED_FROM_CONTRACT",
                "evidence_file": "docs/mapping/openyield_canonical_sram_semantic_contract.json",
                "why_it_matters": "Keeps layout intent inside the current supported scope and avoids unsupported write-mask claims.",
            },
            {
                "parameter_name": "address_width",
                "value": address_width,
                "source": "DERIVED_FROM_CONTRACT",
                "evidence_file": "docs/mapping/openyield_logical_to_openyield_parameter_map.csv",
                "why_it_matters": "Defines top-level address pin count for the current-supported baseline.",
            },
            {
                "parameter_name": "row_address_width",
                "value": row_address_width,
                "source": "DERIVED_FROM_CONTRACT",
                "evidence_file": "docs/mapping/openyield_logical_to_openyield_parameter_map.csv",
                "why_it_matters": "Defines row decoder input width and wordline expansion intent.",
            },
            {
                "parameter_name": "column_address_width",
                "value": column_address_width,
                "source": "DERIVED_FROM_CONTRACT",
                "evidence_file": "docs/mapping/openyield_logical_to_openyield_parameter_map.csv",
                "why_it_matters": "Defines column mux select width in the current-supported scope.",
            },
            {
                "parameter_name": "data_width",
                "value": word_size,
                "source": "DERIVED_FROM_CONTRACT",
                "evidence_file": "docs/mapping/openyield_canonical_sram_semantic_contract.json",
                "why_it_matters": "Defines top-level write and read data bus width.",
            },
            {
                "parameter_name": "supported_scope",
                "value": supported_scope,
                "source": "DERIVED_FROM_CONTRACT",
                "evidence_file": "docs/mapping/openyield_canonical_sram_semantic_contract.json;docs/openyield_layout_generator_architecture_proposal.json",
                "why_it_matters": "Captures the exact boundary of what R1 is defining and what remains out of scope.",
            },
        ]
        return CanonicalSramLayoutParameters(parameters=parameters, supported_scope=supported_scope)

    def _load_module_pins(self, module_name: str) -> list[dict[str, Any]]:
        row = self.module_gds_inventory.get(module_name)
        if row is None:
            return []
        pins_path = Path(row["pins_json_path"])
        if not pins_path.exists():
            return []
        payload = _load_json(pins_path)
        return payload.get("pins", [])

    def _load_module_rail_report(self, module_name: str) -> dict[str, Any]:
        row = self.module_gds_inventory.get(module_name)
        if row is None:
            return {}
        rail_path = Path(row["rail_report_path"])
        if not rail_path.exists():
            return {}
        return _load_json(rail_path)

    def _build_module_roles(self) -> list[ModuleToPhysicalRole]:
        roles: list[ModuleToPhysicalRole] = []
        for module_name in L3_TARGET_MODULES:
            inventory_row = self.module_gds_inventory.get(module_name, {})
            role, path_group = MODULE_PHYSICAL_ROLE_MAP.get(module_name, ("UNKNOWN", "UNKNOWN"))
            generator_row = self.module_generator_inventory.get(module_name, {})
            uses_candidate_geometry = "candidate" in inventory_row.get("generation_strategy", "") or inventory_row.get("uses_composition_generator") == "True"
            uses_contract_pins = _bool_from_str(inventory_row.get("uses_contract_pin_mapping", "False"))
            requires_row_pitch_alignment = role in {"ARRAY_CORE", "ARRAY_DUMMY", "ARRAY_REPLICA", "ROW_DECODER", "WORDLINE_DRIVER"}
            requires_column_pitch_alignment = role in {"ARRAY_CORE", "ARRAY_DUMMY", "ARRAY_REPLICA", "COLUMN_PRECHARGE", "COLUMN_MUX", "SENSE_AMP", "WRITE_DRIVER"}
            requires_power_stitching = _bool_from_str(inventory_row.get("power_pins_present", "False"))
            requires_top_level_routing = role not in {"ARRAY_DUMMY"}

            if role == "UNKNOWN":
                readiness_r3 = "BLOCKED_UNKNOWN_ROLE"
                readiness_r4 = "BLOCKED_UNKNOWN_ROLE"
            elif uses_candidate_geometry:
                readiness_r3 = "READY_WITH_SEMANTIC_ROLE_BUT_REQUIRES_REAL_GENERATOR"
                readiness_r4 = "REQUIRES_ROUTER_AFTER_REAL_GENERATOR"
            elif inventory_row.get("gds_generated") == "True":
                readiness_r3 = "GEOMETRY_AND_METADATA_AVAILABLE_AS_REFERENCE"
                readiness_r4 = "REQUIRES_REAL_TOP_LEVEL_ROUTING_AND_POWER_STITCH"
            else:
                readiness_r3 = "BLOCKED_MISSING_REFERENCE_GEOMETRY"
                readiness_r4 = "BLOCKED_MISSING_REFERENCE_GEOMETRY"

            blocking_gap = inventory_row.get("limitations", "") or generator_row.get("limitations", "")
            if uses_candidate_geometry:
                blocking_gap = "Current module is candidate geometry only; cannot be treated as final physical generator output."
            elif inventory_row.get("gds_generated") != "True":
                blocking_gap = "Reference module GDS is missing."

            next_action = "Use this role in R2/R3 generator decomposition and preserve current metadata as reference only."
            if uses_candidate_geometry:
                next_action = "Replace candidate geometry with R3/R4 generator-owned physical construction while preserving contract pins."
            elif role in {"COLUMN_PRECHARGE", "COLUMN_MUX", "SENSE_AMP", "WRITE_DRIVER"}:
                next_action = "Bind this module to array column pitch and BL/BR routing expectations in R3/R4."
            elif role in {"ROW_DECODER", "WORDLINE_DRIVER"}:
                next_action = "Bind this module to address-width and row-pitch expectations in R3/R4."

            roles.append(
                ModuleToPhysicalRole(
                    module_name=module_name,
                    physical_role=role,
                    path_group=path_group,
                    source_openyield_semantics="docs/mapping/openyield_canonical_sram_semantic_contract.json;docs/mapping/openyield_module_connection_matrix.csv",
                    source_existing_gds=inventory_row.get("gds_path", "NOT_FOUND"),
                    source_existing_metadata=";".join(filter(None, [inventory_row.get("pins_json_path", ""), inventory_row.get("rail_report_path", ""), inventory_row.get("generator_manifest_path", "")])),
                    uses_candidate_geometry=uses_candidate_geometry,
                    uses_contract_pins=uses_contract_pins,
                    requires_row_pitch_alignment=requires_row_pitch_alignment,
                    requires_column_pitch_alignment=requires_column_pitch_alignment,
                    requires_power_stitching=requires_power_stitching,
                    requires_top_level_routing=requires_top_level_routing,
                    required_by_structure_complete_gds=True,
                    current_readiness_for_R3=readiness_r3,
                    current_readiness_for_R4=readiness_r4,
                    blocking_gap=blocking_gap,
                    next_required_action=next_action,
                )
            )
        return roles

    def _category_from_signal(self, row: dict[str, str]) -> str:
        raw = row.get("signal_category", "").strip().lower()
        if _bool_from_str(row.get("is_power", "")):
            if row.get("signal_name", "").upper() in {"GND", "VSS"}:
                return "GROUND"
            return "POWER"
        if _bool_from_str(row.get("is_clock", "")):
            return "CLOCK"
        if _bool_from_str(row.get("is_wordline", "")):
            return "WORDLINE"
        if _bool_from_str(row.get("is_bitline", "")):
            name = row.get("signal_name", "").lower()
            if "blb" in name or "br" in name or "rblb" in name:
                return "BITLINE_BAR"
            return "BITLINE"
        if _bool_from_str(row.get("is_timing_path", "")):
            return "TIMING_REPLICA"
        if _bool_from_str(row.get("is_control", "")):
            return "CONTROL"
        if _bool_from_str(row.get("is_data", "")):
            name = row.get("signal_name", "").lower()
            if "dout" in name or "q" in name:
                return "DATA_OUT"
            return "DATA_IN"
        return NET_CATEGORY_MAP.get(raw, "UNKNOWN")

    def _net_flags(self, category: str) -> tuple[bool, bool, bool, bool, bool]:
        return (
            category == "CONTROL",
            category == "WORDLINE",
            category in {"BITLINE", "BITLINE_BAR"},
            category in {"POWER", "GROUND"},
            category == "CLOCK",
        )

    def _build_net_roles(self) -> list[NetToLayoutRole]:
        rows: list[NetToLayoutRole] = []
        seen: set[tuple[str, str, str]] = set()
        for row in self.module_connection_rows:
            net_name = row["signal_name"]
            category = self._category_from_signal(row)
            is_control, is_wordline, is_bitline, is_power, is_clock = self._net_flags(category)
            key = (net_name, row["source_module"], row["target_module"])
            if key in seen:
                continue
            seen.add(key)
            rows.append(
                NetToLayoutRole(
                    net_name=net_name,
                    net_category=category,
                    layout_role=LAYOUT_ROLE_MAP.get(category, "unknown_layout_role"),
                    source_module=row["source_module"],
                    source_pin=row["source_port_or_signal"],
                    target_modules=row["target_module"],
                    target_pins=row["target_port_or_signal"],
                    expected_geometry_direction=EXPECTED_DIRECTION_MAP.get(category, "unknown"),
                    expected_routing_layer_hint=EXPECTED_LAYER_HINT_MAP.get(category, "unknown"),
                    requires_pitch_alignment=is_wordline or is_bitline,
                    requires_top_level_routing=not is_power,
                    requires_power_stitching=is_power,
                    is_control_signal=is_control,
                    is_wordline=is_wordline,
                    is_bitline=is_bitline,
                    is_power=is_power,
                    is_clock=is_clock,
                    source_evidence=row["evidence_source"],
                    status="MAPPED" if category != "UNKNOWN" else "UNKNOWN_CATEGORY",
                    next_required_action="Preserve this semantic-to-layout mapping in R2/R3 generator interfaces."
                    if category != "UNKNOWN"
                    else "Re-check OpenYield source semantics and add a stable layout role before R2.",
                )
            )

        top_ports = self.top_bank_contract.get("SRAM_TOP", {}).get("ports", {})
        extra_rows = [
            ("clk", "CLOCK", "SRAM_TOP", "clk", "CONTROL_LOGIC;GATED_CLOCK_PATH;DFF_ROW", "clk"),
            ("csb", "CONTROL", "SRAM_TOP", "csb", "CONTROL_LOGIC;DFF_ROW", "csb"),
            ("web", "CONTROL", "SRAM_TOP", "web", "CONTROL_LOGIC;DFF_ROW", "web"),
            ("DIN[i]", "DATA_IN", "SRAM_TOP", "DIN[i]", "DFF_ROW;write_driver", "DIN[i];din"),
            ("DOUT[i]", "DATA_OUT", "sense_amp", "dout", "SRAM_TOP", "DOUT[i]"),
            ("VDD", "POWER", "SRAM_TOP", "VDD", "ALL_MODULES", "VDD"),
            ("VSS", "GROUND", "SRAM_TOP", "VSS", "ALL_MODULES", "GND"),
            ("RBL", "TIMING_REPLICA", "replica_array", "RBL", "DELAY_CHAIN;CONTROL_LOGIC", "rbl;delay_in"),
        ]
        for net_name, category, source_module, source_pin, target_modules, target_pins in extra_rows:
            if any(existing.net_name == net_name for existing in rows):
                continue
            is_control, is_wordline, is_bitline, is_power, is_clock = self._net_flags(category)
            rows.append(
                NetToLayoutRole(
                    net_name=net_name,
                    net_category=category,
                    layout_role=LAYOUT_ROLE_MAP[category],
                    source_module=source_module,
                    source_pin=source_pin,
                    target_modules=target_modules,
                    target_pins=target_pins,
                    expected_geometry_direction=EXPECTED_DIRECTION_MAP[category],
                    expected_routing_layer_hint=EXPECTED_LAYER_HINT_MAP[category],
                    requires_pitch_alignment=is_wordline or is_bitline,
                    requires_top_level_routing=not is_power,
                    requires_power_stitching=is_power,
                    is_control_signal=is_control,
                    is_wordline=is_wordline,
                    is_bitline=is_bitline,
                    is_power=is_power,
                    is_clock=is_clock,
                    source_evidence="docs/mapping/openyield_top_bank_semantic_contract.json;docs/mapping/openyield_module_connection_matrix.csv",
                    status="MAPPED",
                    next_required_action="Preserve this top-level semantic net in the R2/R3 layout intent interfaces.",
                )
            )
        return rows

    def _build_array_topology_contract(self, canonical: CanonicalSramLayoutParameters) -> ArrayTopologyContract:
        bitcell_rail = self._load_module_rail_report("bitcell_array")
        summary = {
            "bitcell_array_role": "SRAM main storage array",
            "dummy_array_role": "Array edge/dummy placeholder used to represent non-active boundary storage context, not final complete boundary proof.",
            "replica_array_role": "Replica timing/reference array feeding timing/control semantics and later replica routing intent.",
            "num_rows_to_wl_relation": "Each physical wordline WL[i] must correspond to exactly one bitcell row in the supported scope.",
            "num_cols_to_bl_relation": "Each physical column contributes one BL and one BR rail; total BL/BR pair count follows num_cols.",
            "row_pitch_source": {
                "value": "existing bitcell_array reference geometry and future R3 array generator pitch model",
                "classification": "already_available_from_existing_metadata",
                "evidence_file": "outputs/openyield_module_gds/bitcell_array/rail_report.json",
            },
            "column_pitch_source": {
                "value": "existing bitcell_array reference geometry and future R3 array generator pitch model",
                "classification": "already_available_from_existing_metadata",
                "evidence_file": "outputs/openyield_module_gds/bitcell_array/rail_report.json",
            },
            "bitline_direction_expectation": {
                "value": "BL/BR vertical along array columns",
                "classification": "learned_from_openram_audit",
                "evidence_file": "docs/openram_gds_generation_audit_report.json",
            },
            "wordline_direction_expectation": {
                "value": "WL horizontal across array rows",
                "classification": "learned_from_openram_audit",
                "evidence_file": "docs/openram_gds_generation_audit_report.json",
            },
            "rail_direction_expectation": {
                "value": "Array rails must be exported as top/bottom or side rail handoff metadata first, then proven by real geometry in R4.",
                "classification": "derived_from_openyield_semantics",
                "evidence_file": "outputs/openyield_module_gds/bitcell_array/rail_report.json;docs/openyield_layout_generator_architecture_proposal.json",
            },
            "dummy_replica_boundary_completeness": {
                "dummy_complete_now": False,
                "replica_complete_now": False,
                "boundary_complete_now": False,
                "classification": "missing_requires_R3_generator_design",
                "why_it_matters": "Current standalone metadata is sufficient for intent definition, but not proof of a complete structure-grade SRAM array wrapper.",
            },
            "already_available_from_existing_metadata": [
                "bitcell_array standalone GDS exists",
                "dummy_array standalone GDS exists",
                "replica_array standalone GDS exists",
                "pins/bbox/rail metadata exist for all three array-related modules",
            ],
            "derived_from_openyield_semantics": [
                "single-bank single-port storage model",
                "num_rows defines WL cardinality",
                "num_cols defines BL/BR cardinality",
            ],
            "learned_from_openram_audit": [
                "Array wrapper needs main array + replica + dummy/boundary semantics",
                "Row pitch and column pitch must be real array-generator outputs in R3",
            ],
            "missing_requires_R3_generator_design": [
                "Real array wrapper generator for complete main/dummy/replica/boundary composition",
                "Real pitch-owned geometry rather than standalone candidate references",
                "Explicit boundary/tap/well implementation policy",
            ],
        }
        return ArrayTopologyContract(summary=summary)

    def _build_row_path_intent(
        self,
        module_roles: list[ModuleToPhysicalRole],
        canonical: CanonicalSramLayoutParameters,
    ) -> RowPathIntent:
        summary = {
            "physical_role": "ROW_PATH",
            "modules": [
                "row_decoder",
                "wordline_decoder",
                "decoder_gate_cells",
                "wordline_driver",
                "wordline_driver_gate_cells",
            ],
            "address_relation": {
                "row_decoder_and_wordline_decoder": "Consume row_address_width bits and expand into decoded row-select intent.",
                "row_address_width": next(item["value"] for item in canonical.parameters if item["parameter_name"] == "row_address_width"),
                "evidence_file": "docs/mapping/openyield_decoder_wordline_semantic_contract.json",
            },
            "wordline_driver_relation": {
                "value": "Wordline driver fanout must match num_rows and every WL[i] must map one-to-one onto a bitcell row.",
                "evidence_file": "docs/mapping/openyield_decoder_wordline_semantic_contract.json;docs/openram_gds_generation_audit_report.json",
            },
            "pitch_alignment_expectation": "Row path geometry must align to bitcell array row pitch before structure-complete SRAM GDS can exist.",
            "routing_expectation": "decoder output -> WL driver input -> WL[i] should remain an explicit R3/R4 routing chain with row-pitch alignment.",
            "current_candidate_geometry_modules": [
                role.module_name for role in module_roles if role.path_group == "ROW_PATH" and role.uses_candidate_geometry
            ],
            "current_hardmacro_reference_modules": [
                role.module_name for role in module_roles if role.path_group == "ROW_PATH" and not role.uses_candidate_geometry
            ],
            "r3_r4_required_work": [
                "R3 must define a real row-path generator boundary for decoder stages and WL driver composition.",
                "R3 must define row-pitch-owned placement anchors relative to ARRAY_CORE.",
                "R4 must define decoder-to-driver and driver-to-WL routing implementation rather than contract-only handoff.",
            ],
        }
        return RowPathIntent(summary=summary)

    def _build_column_path_intent(
        self,
        module_roles: list[ModuleToPhysicalRole],
        canonical: CanonicalSramLayoutParameters,
    ) -> ColumnPathIntent:
        summary = {
            "physical_role": "COLUMN_PATH",
            "modules": [
                "precharge",
                "column_mux",
                "sense_amp",
                "write_driver",
            ],
            "precharge_alignment": "precharge must align to BL/BR column pitch and sit on the bitline-side of the column path.",
            "column_mux_relation": {
                "words_per_row": next(item["value"] for item in canonical.parameters if item["parameter_name"] == "words_per_row"),
                "column_mux_ratio": next(item["value"] for item in canonical.parameters if item["parameter_name"] == "column_mux_ratio"),
                "statement": "column_mux is structurally required only when words_per_row > 1 or column_mux_ratio > 1 in a future supported config.",
                "evidence_file": "docs/mapping/openyield_logical_to_openyield_parameter_map.csv;docs/openram_gds_generation_audit_report.json",
            },
            "sense_amp_relation": "Each sense_amp data output bit belongs to one logical data_out bit after column selection.",
            "write_driver_relation": "Each write_driver data input bit belongs to one logical data_in bit before write enable gating.",
            "pitch_expectation": "Entire column path must be anchored on array column pitch, not on standalone wrapper width.",
            "bitline_routing_expectation": "BL/BR and optional BL_out/BR_out must remain explicit R3/R4 routed nets with column-pitch alignment.",
            "current_hardmacro_metadata_status": "Existing hardmacro wrappers provide reference bbox/pins/rails, but do not yet prove structure-complete column-path composition.",
            "current_candidate_geometry_modules": [
                role.module_name for role in module_roles if role.path_group == "COLUMN_PATH" and role.uses_candidate_geometry
            ],
            "r3_r4_required_work": [
                "R3 must define real column-path composition rules relative to ARRAY_CORE column pitch.",
                "R4 must define BL/BR, mux-select, sense, and write routing ownership.",
                "R4 must define whether spare/replica timing coupling is explicit or out of current scope.",
            ],
        }
        return ColumnPathIntent(summary=summary)

    def _build_control_path_intent(
        self,
        module_roles: list[ModuleToPhysicalRole],
        canonical: CanonicalSramLayoutParameters,
    ) -> ControlPathIntent:
        candidate_modules = [role.module_name for role in module_roles if role.path_group == "CONTROL_PATH" and role.uses_candidate_geometry]
        contract_pin_modules = [role.module_name for role in module_roles if role.path_group == "CONTROL_PATH" and role.uses_contract_pins]
        summary = {
            "physical_role": "CONTROL_PATH",
            "modules": [
                "CONTROL_LOGIC",
                "DELAY_CHAIN",
                "PRECHARGE_ENABLE_PATH",
                "SENSE_ENABLE_PATH",
                "WRITE_ENABLE_PATH",
                "WORDLINE_ENABLE_PATH",
                "GATED_CLOCK_PATH",
                "DFF_ROW",
            ],
            "control_outputs": [
                "precharge_en",
                "sense_en",
                "write_en",
                "wordline_en",
                "gated_clk",
                "delay / replica timing signals",
            ],
            "downstream_expectations": {
                "precharge_en": "precharge",
                "sense_en": "sense_amp",
                "write_en": "write_driver",
                "wordline_en": "wordline_driver",
                "gated_clk": "DFF_ROW and internal enable paths",
                "delay_replica": "PRECHARGE_ENABLE_PATH;SENSE_ENABLE_PATH;WRITE_ENABLE_PATH",
            },
            "delay_chain_layout_expectation": "delay chain and replica timing path remain periphery control-path objects and must preserve causal order before final routing.",
            "current_candidate_geometry_modules": candidate_modules,
            "contract_pin_modules": contract_pin_modules,
            "r4_router_requirements": [
                "control router must connect control outputs into row/column/periphery modules through stable bus ownership",
                "control router must preserve clock/control separation from power stitching",
                "control router must preserve replica timing signals as dedicated semantic routes rather than collapsing them into generic nets",
            ],
            "evidence_file": "docs/mapping/openyield_time_control_decomposition_contract.json;docs/mapping/openyield_control_path_semantic_contracts.csv",
        }
        return ControlPathIntent(summary=summary)

    def _build_power_intent(self, module_roles: list[ModuleToPhysicalRole]) -> PowerIntent:
        module_power = []
        for role in module_roles:
            inventory_row = self.module_gds_inventory.get(role.module_name, {})
            pins = self._load_module_pins(role.module_name)
            pin_names = [str(pin.get("name", "")) for pin in pins]
            module_power.append(
                {
                    "module_name": role.module_name,
                    "has_power_pins": _bool_from_str(inventory_row.get("power_pins_present", "False")),
                    "power_pin_names": [name for name in pin_names if name.upper() in POWER_NET_NAMES or "VDD" in name.upper() or "GND" in name.upper()],
                    "rail_status": inventory_row.get("rail_status", ""),
                    "uses_candidate_geometry": role.uses_candidate_geometry,
                }
            )
        summary = {
            "vdd_net_names": ["VDD"],
            "gnd_net_names": ["GND", "VSS"],
            "module_power_summary": module_power,
            "array_rail_expectation": "ARRAY_CORE, ARRAY_DUMMY, and ARRAY_REPLICA must expose rail directions compatible with later top-level stitching.",
            "row_path_rail_expectation": "ROW_PATH modules need rail continuity aligned with array-facing side placement.",
            "column_path_rail_expectation": "COLUMN_PATH modules need rail continuity aligned with array-facing column pitch placement.",
            "control_path_rail_expectation": "CONTROL_PATH rails remain periphery-distributed and must later stitch into top-level VDD/GND export.",
            "top_level_power_pin_export_expectation": "Top-level VDD/GND pins must be exported by a future R4 power planner using real geometry proof.",
            "power_stitching_owned_by_R4": True,
            "metadata_only_now": [
                "module boundary rails",
                "rail_status fields from standalone module metadata",
            ],
            "requires_real_geometry_proof": [
                "array-to-row-path power continuity",
                "array-to-column-path power continuity",
                "top-level VDD/GND export geometry",
            ],
        }
        return PowerIntent(summary=summary)

    def _build_pin_intent(self, module_roles: list[ModuleToPhysicalRole]) -> PinIntent:
        geometry_backed_modules = []
        contract_only_modules = []
        for role in module_roles:
            pins = self._load_module_pins(role.module_name)
            sources = sorted({str(pin.get("pin_source", "")) for pin in pins if pin.get("pin_source")})
            if sources and all("contract" in source for source in sources):
                contract_only_modules.append(role.module_name)
            elif pins:
                geometry_backed_modules.append(role.module_name)
        summary = {
            "top_level_address_pins": ["A[i]"],
            "top_level_data_input_pins": ["DIN[i]"],
            "top_level_data_output_pins": ["DOUT[i]"],
            "clock_and_control_pins": ["clk", "csb", "web"],
            "power_pins": ["VDD", "GND", "VSS"],
            "internal_module_pins": {
                "wordline": ["WL[i]", "DEC_WL[i]", "wl_en"],
                "bitline": ["BL[i]", "BLB[i]", "BL_out[i]", "BR_out[i]"],
                "control": ["precharge_en", "sense_en", "write_en", "gated_clk", "rbl_delay"],
            },
            "geometry_backed_pin_modules": geometry_backed_modules,
            "contract_pin_modules": contract_only_modules,
            "r4_r5_validation_plan": [
                "R4 validates pin placement ownership and routing reachability",
                "R5 validates exported top-level pins against GDS/LEF/SPICE naming consistency",
            ],
            "naming_consistency_rule": "Pin naming must stay consistent with OpenYield netlist semantics and the canonical semantic contracts.",
        }
        return PinIntent(summary=summary)

    def _build_layout_intent(self, canonical: CanonicalSramLayoutParameters) -> OpenYieldLayoutIntent:
        return OpenYieldLayoutIntent(
            intent_name="openyield_sram_layout_intent",
            canonical_parameters=canonical,
            top_level_goal="Define a self-developed OpenYield SRAM layout intent that future R2/R3 generator stages can consume.",
            layout_boundary=(
                "This intent defines structure, roles, alignment expectations, power and pin contracts. "
                "It does not claim a structure-complete SRAM GDS, DRC clean, LVS clean, timing closure, or signoff readiness."
            ),
            source_artifacts=[
                "docs/openram_gds_generation_audit_report.json",
                "docs/mapping/openram_to_openyield_layoutgen_reuse_matrix.csv",
                "docs/mapping/openyield_canonical_sram_semantic_contract.json",
                "docs/mapping/openyield_module_connection_matrix.csv",
                "docs/mapping/openyield_decoder_wordline_semantic_contract.json",
                "docs/mapping/openyield_time_control_decomposition_contract.json",
                "docs/mapping/openyield_control_path_semantic_contracts.csv",
                "docs/mapping/openyield_module_gds_inventory.csv",
            ],
        )

    def _build_layout_intent_matrix(self) -> list[dict[str, Any]]:
        return [
            {
                "intent_area": "canonical_parameters",
                "artifact": "openyield_sram_layout_intent.json",
                "status": "READY",
                "evidence_source": "docs/mapping/openyield_canonical_sram_semantic_contract.json;docs/mapping/openyield_logical_to_openyield_parameter_map.csv",
                "derived_from_openyield": True,
                "learned_from_openram_audit": True,
                "requires_R2_architecture": True,
                "requires_R3_generator": True,
                "requires_R4_router": False,
                "blocks_structure_complete_gds_if_missing": True,
                "summary": "Canonical parameter and supported-scope baseline for future full SRAM physical generation.",
                "next_required_action": "Use these parameters as the only accepted front-end for R2 generator architecture design.",
            },
            {
                "intent_area": "array_topology",
                "artifact": "openyield_array_topology_contract.json",
                "status": "READY",
                "evidence_source": "docs/openram_gds_generation_audit_report.json;outputs/openyield_module_gds/bitcell_array/rail_report.json",
                "derived_from_openyield": True,
                "learned_from_openram_audit": True,
                "requires_R2_architecture": True,
                "requires_R3_generator": True,
                "requires_R4_router": True,
                "blocks_structure_complete_gds_if_missing": True,
                "summary": "Defines array main/dummy/replica roles and row/column pitch ownership expectations.",
                "next_required_action": "Implement array wrapper ownership and real pitch generation in R3.",
            },
            {
                "intent_area": "row_path",
                "artifact": "openyield_row_path_intent.json",
                "status": "READY",
                "evidence_source": "docs/mapping/openyield_decoder_wordline_semantic_contract.json",
                "derived_from_openyield": True,
                "learned_from_openram_audit": True,
                "requires_R2_architecture": True,
                "requires_R3_generator": True,
                "requires_R4_router": True,
                "blocks_structure_complete_gds_if_missing": True,
                "summary": "Defines decoder/WL driver to array alignment and routing expectations.",
                "next_required_action": "Convert row-path intent into explicit R3 generator modules and R4 routing rules.",
            },
            {
                "intent_area": "column_path",
                "artifact": "openyield_column_path_intent.json",
                "status": "READY",
                "evidence_source": "docs/mapping/openyield_logical_to_openyield_parameter_map.csv;docs/openram_gds_generation_audit_report.json",
                "derived_from_openyield": True,
                "learned_from_openram_audit": True,
                "requires_R2_architecture": True,
                "requires_R3_generator": True,
                "requires_R4_router": True,
                "blocks_structure_complete_gds_if_missing": True,
                "summary": "Defines precharge/mux/sense/write alignment to array column pitch.",
                "next_required_action": "Convert column-path intent into explicit R3 generator modules and R4 routing rules.",
            },
            {
                "intent_area": "control_path",
                "artifact": "openyield_control_path_intent.json",
                "status": "READY",
                "evidence_source": "docs/mapping/openyield_time_control_decomposition_contract.json;docs/mapping/openyield_control_path_semantic_contracts.csv",
                "derived_from_openyield": True,
                "learned_from_openram_audit": True,
                "requires_R2_architecture": True,
                "requires_R3_generator": True,
                "requires_R4_router": True,
                "blocks_structure_complete_gds_if_missing": True,
                "summary": "Defines control/timing outputs, downstream consumers, and replica timing semantics.",
                "next_required_action": "Convert control-path intent into explicit generator and router ownership in R3/R4.",
            },
            {
                "intent_area": "power",
                "artifact": "openyield_power_intent.json",
                "status": "READY",
                "evidence_source": "docs/mapping/openyield_module_gds_inventory.csv",
                "derived_from_openyield": True,
                "learned_from_openram_audit": True,
                "requires_R2_architecture": True,
                "requires_R3_generator": False,
                "requires_R4_router": True,
                "blocks_structure_complete_gds_if_missing": True,
                "summary": "Defines VDD/GND naming, module power availability, and future power-stitch ownership.",
                "next_required_action": "Implement R4 power planner around these contracts.",
            },
            {
                "intent_area": "pins",
                "artifact": "openyield_pin_intent.json",
                "status": "READY",
                "evidence_source": "docs/mapping/openyield_module_gds_inventory.csv;outputs/openyield_module_gds/*/pins.json",
                "derived_from_openyield": True,
                "learned_from_openram_audit": False,
                "requires_R2_architecture": True,
                "requires_R3_generator": False,
                "requires_R4_router": True,
                "blocks_structure_complete_gds_if_missing": True,
                "summary": "Defines top-level and internal pin ownership along with contract-backed vs geometry-backed status.",
                "next_required_action": "Keep pin naming stable through R4/R5 export validation.",
            },
            {
                "intent_area": "net_role_map",
                "artifact": "openyield_net_to_layout_role_map.csv",
                "status": "READY",
                "evidence_source": "docs/mapping/openyield_module_connection_matrix.csv;docs/mapping/openyield_top_bank_semantic_contract.json",
                "derived_from_openyield": True,
                "learned_from_openram_audit": True,
                "requires_R2_architecture": True,
                "requires_R3_generator": True,
                "requires_R4_router": True,
                "blocks_structure_complete_gds_if_missing": True,
                "summary": "Defines the semantic-net to layout-role translation layer.",
                "next_required_action": "Use this as the net-classification input to future generators and routers.",
            },
            {
                "intent_area": "module_role_map",
                "artifact": "openyield_module_to_physical_role_map.csv",
                "status": "READY",
                "evidence_source": "docs/mapping/openyield_module_gds_inventory.csv;docs/mapping/openyield_module_generator_inventory.csv",
                "derived_from_openyield": True,
                "learned_from_openram_audit": True,
                "requires_R2_architecture": True,
                "requires_R3_generator": True,
                "requires_R4_router": True,
                "blocks_structure_complete_gds_if_missing": True,
                "summary": "Maps all 20 L3 modules onto physical roles and future generator/router ownership.",
                "next_required_action": "Freeze these role names before R2 architecture decomposition.",
            },
        ]

    def _intent_json_path(self, name: str) -> Path:
        path = self.out_dir / name
        self.outputs[name] = path
        return path

    def _emit_layout_intent(self, intent: OpenYieldLayoutIntent) -> None:
        json_path = self._intent_json_path("openyield_sram_layout_intent.json")
        md_path = self._intent_json_path("openyield_sram_layout_intent.md")
        _json_dump(json_path, asdict(intent))
        lines = [
            "# OpenYield SRAM Layout Intent",
            "",
            "## Goal",
            "",
            intent.top_level_goal,
            "",
            "## Canonical Parameters",
            "",
        ]
        lines.extend(
            [
                f"- `{entry['parameter_name']}` = `{entry['value']}`",
                f"  source: `{entry['source']}`",
                f"  evidence: `{entry['evidence_file']}`",
            ]
            for entry in intent.canonical_parameters.parameters
        )
        flat_lines = ["# OpenYield SRAM Layout Intent", "", "## Goal", "", intent.top_level_goal, "", "## Canonical Parameters", ""]
        for entry in intent.canonical_parameters.parameters:
            flat_lines.append(f"- `{entry['parameter_name']}` = `{entry['value']}`")
            flat_lines.append(f"source: `{entry['source']}`")
            flat_lines.append(f"evidence: `{entry['evidence_file']}`")
        flat_lines.extend(["", "## Boundary", "", intent.layout_boundary, "", "## Source Artifacts", ""])
        for artifact in intent.source_artifacts:
            flat_lines.append(f"- `{artifact}`")
        _write_text(md_path, "\n".join(flat_lines) + "\n")

    def _emit_array_topology_contract(self, contract: ArrayTopologyContract) -> None:
        json_path = self._intent_json_path("openyield_array_topology_contract.json")
        md_path = self._intent_json_path("openyield_array_topology_contract.md")
        _json_dump(json_path, contract.summary)
        md = [
            "# OpenYield Array Topology Contract",
            "",
            f"- bitcell_array role: {contract.summary['bitcell_array_role']}",
            f"- dummy_array role: {contract.summary['dummy_array_role']}",
            f"- replica_array role: {contract.summary['replica_array_role']}",
            f"- num_rows to WL relation: {contract.summary['num_rows_to_wl_relation']}",
            f"- num_cols to BL relation: {contract.summary['num_cols_to_bl_relation']}",
            "",
            "## Ownership Summary",
            "",
            f"- row pitch source: {contract.summary['row_pitch_source']['value']}",
            f"- column pitch source: {contract.summary['column_pitch_source']['value']}",
            f"- BL/BR expectation: {contract.summary['bitline_direction_expectation']['value']}",
            f"- WL expectation: {contract.summary['wordline_direction_expectation']['value']}",
            f"- rail expectation: {contract.summary['rail_direction_expectation']['value']}",
            "",
            "## Missing For R3",
            "",
        ]
        for item in contract.summary["missing_requires_R3_generator_design"]:
            md.append(f"- {item}")
        _write_text(md_path, "\n".join(md) + "\n")

    def _emit_row_path_intent(self, intent: RowPathIntent) -> None:
        json_path = self._intent_json_path("openyield_row_path_intent.json")
        md_path = self._intent_json_path("openyield_row_path_intent.md")
        _json_dump(json_path, intent.summary)
        md = [
            "# OpenYield Row Path Intent",
            "",
            f"- physical_role: `{intent.summary['physical_role']}`",
            f"- modules: {', '.join(intent.summary['modules'])}",
            f"- row_address_width: `{intent.summary['address_relation']['row_address_width']}`",
            f"- relation: {intent.summary['wordline_driver_relation']['value']}",
            f"- pitch alignment: {intent.summary['pitch_alignment_expectation']}",
            f"- routing expectation: {intent.summary['routing_expectation']}",
            "",
            "## Candidate Geometry Modules",
            "",
        ]
        for module in intent.summary["current_candidate_geometry_modules"]:
            md.append(f"- {module}")
        md.extend(["", "## R3/R4 Required Work", ""])
        for item in intent.summary["r3_r4_required_work"]:
            md.append(f"- {item}")
        _write_text(md_path, "\n".join(md) + "\n")

    def _emit_column_path_intent(self, intent: ColumnPathIntent) -> None:
        json_path = self._intent_json_path("openyield_column_path_intent.json")
        md_path = self._intent_json_path("openyield_column_path_intent.md")
        _json_dump(json_path, intent.summary)
        md = [
            "# OpenYield Column Path Intent",
            "",
            f"- physical_role: `{intent.summary['physical_role']}`",
            f"- modules: {', '.join(intent.summary['modules'])}",
            f"- precharge alignment: {intent.summary['precharge_alignment']}",
            f"- column mux relation: {intent.summary['column_mux_relation']['statement']}",
            f"- pitch expectation: {intent.summary['pitch_expectation']}",
            f"- BL/BR routing expectation: {intent.summary['bitline_routing_expectation']}",
            f"- metadata status: {intent.summary['current_hardmacro_metadata_status']}",
            "",
            "## R3/R4 Required Work",
            "",
        ]
        for item in intent.summary["r3_r4_required_work"]:
            md.append(f"- {item}")
        _write_text(md_path, "\n".join(md) + "\n")

    def _emit_control_path_intent(self, intent: ControlPathIntent) -> None:
        json_path = self._intent_json_path("openyield_control_path_intent.json")
        md_path = self._intent_json_path("openyield_control_path_intent.md")
        _json_dump(json_path, intent.summary)
        md = [
            "# OpenYield Control Path Intent",
            "",
            f"- physical_role: `{intent.summary['physical_role']}`",
            f"- modules: {', '.join(intent.summary['modules'])}",
            "",
            "## Control Outputs",
            "",
        ]
        for item in intent.summary["control_outputs"]:
            md.append(f"- {item}")
        md.extend(["", "## Candidate Geometry Modules", ""])
        for module in intent.summary["current_candidate_geometry_modules"]:
            md.append(f"- {module}")
        md.extend(["", "## Contract Pin Modules", ""])
        for module in intent.summary["contract_pin_modules"]:
            md.append(f"- {module}")
        md.extend(["", "## R4 Router Requirements", ""])
        for item in intent.summary["r4_router_requirements"]:
            md.append(f"- {item}")
        _write_text(md_path, "\n".join(md) + "\n")

    def _emit_power_intent(self, intent: PowerIntent) -> None:
        json_path = self._intent_json_path("openyield_power_intent.json")
        md_path = self._intent_json_path("openyield_power_intent.md")
        _json_dump(json_path, intent.summary)
        rows = [
            {
                "module_name": item["module_name"],
                "has_power_pins": item["has_power_pins"],
                "power_pin_names": ";".join(item["power_pin_names"]),
                "rail_status": item["rail_status"],
                "uses_candidate_geometry": item["uses_candidate_geometry"],
            }
            for item in intent.summary["module_power_summary"]
        ]
        md = [
            "# OpenYield Power Intent",
            "",
            f"- VDD nets: {', '.join(intent.summary['vdd_net_names'])}",
            f"- GND nets: {', '.join(intent.summary['gnd_net_names'])}",
            f"- array rail expectation: {intent.summary['array_rail_expectation']}",
            f"- row path rail expectation: {intent.summary['row_path_rail_expectation']}",
            f"- column path rail expectation: {intent.summary['column_path_rail_expectation']}",
            f"- control path rail expectation: {intent.summary['control_path_rail_expectation']}",
            f"- top-level export expectation: {intent.summary['top_level_power_pin_export_expectation']}",
            "",
            _md_table(["module_name", "has_power_pins", "power_pin_names", "rail_status", "uses_candidate_geometry"], rows),
        ]
        _write_text(md_path, "\n".join(md) + "\n")

    def _emit_pin_intent(self, intent: PinIntent) -> None:
        json_path = self._intent_json_path("openyield_pin_intent.json")
        md_path = self._intent_json_path("openyield_pin_intent.md")
        _json_dump(json_path, intent.summary)
        md = [
            "# OpenYield Pin Intent",
            "",
            f"- top-level address pins: {', '.join(intent.summary['top_level_address_pins'])}",
            f"- top-level data input pins: {', '.join(intent.summary['top_level_data_input_pins'])}",
            f"- top-level data output pins: {', '.join(intent.summary['top_level_data_output_pins'])}",
            f"- clock/control pins: {', '.join(intent.summary['clock_and_control_pins'])}",
            f"- power pins: {', '.join(intent.summary['power_pins'])}",
            "",
            "## Geometry-backed Pin Modules",
            "",
        ]
        for module in intent.summary["geometry_backed_pin_modules"]:
            md.append(f"- {module}")
        md.extend(["", "## Contract Pin Modules", ""])
        for module in intent.summary["contract_pin_modules"]:
            md.append(f"- {module}")
        md.extend(["", "## Validation Plan", ""])
        for item in intent.summary["r4_r5_validation_plan"]:
            md.append(f"- {item}")
        _write_text(md_path, "\n".join(md) + "\n")

    def _emit_net_role_map(self, roles: list[NetToLayoutRole]) -> None:
        csv_path = self._intent_json_path("openyield_net_to_layout_role_map.csv")
        md_path = self._intent_json_path("openyield_net_to_layout_role_map.md")
        rows = [asdict(role) for role in roles]
        fieldnames = list(rows[0].keys()) if rows else []
        _write_csv(csv_path, fieldnames, rows)
        _write_text(md_path, "# OpenYield Net To Layout Role Map\n\n" + _md_table(fieldnames, rows))

    def _emit_module_role_map(self, roles: list[ModuleToPhysicalRole]) -> None:
        csv_path = self._intent_json_path("openyield_module_to_physical_role_map.csv")
        md_path = self._intent_json_path("openyield_module_to_physical_role_map.md")
        rows = [asdict(role) for role in roles]
        fieldnames = list(rows[0].keys()) if rows else []
        _write_csv(csv_path, fieldnames, rows)
        _write_text(md_path, "# OpenYield Module To Physical Role Map\n\n" + _md_table(fieldnames, rows))

    def _emit_layout_intent_matrix(self, rows: list[dict[str, Any]]) -> None:
        fieldnames = [
            "intent_area",
            "artifact",
            "status",
            "evidence_source",
            "derived_from_openyield",
            "learned_from_openram_audit",
            "requires_R2_architecture",
            "requires_R3_generator",
            "requires_R4_router",
            "blocks_structure_complete_gds_if_missing",
            "summary",
            "next_required_action",
        ]
        _write_csv(self.out_matrix_csv, fieldnames, rows)
        _write_text(self.out_matrix_md, "# OpenYield R1 Layout Intent Matrix\n\n" + _md_table(fieldnames, rows))

    def _emit_gap_summary(self, module_roles: list[ModuleToPhysicalRole], net_roles: list[NetToLayoutRole]) -> None:
        out = self.repo_root / "docs/evidence/R1_layout_intent_gap_summary.md"
        unknown_modules = [role.module_name for role in module_roles if role.physical_role == "UNKNOWN"]
        unknown_nets = [role.net_name for role in net_roles if role.net_category == "UNKNOWN"]
        lines = [
            "# R1 Layout Intent Gap Summary",
            "",
            "R1 的目标是定义 layout intent，而不是生成新的 SRAM physical GDS。",
            "",
            "## Boundary",
            "",
            "- 旧 `openyield_top_level_candidate.gds` 只作为边界证据，不再继续补丁式扩展。",
            "- 本轮不 claim structure-complete SRAM GDS、DRC clean、LVS clean、timing closure、signoff-ready。",
            "",
            "## Module Role Gaps",
            "",
        ]
        if unknown_modules:
            for module in unknown_modules:
                lines.append(f"- UNKNOWN module role: {module}")
        else:
            lines.append("- All 20 L3 target modules have non-UNKNOWN physical roles.")
        lines.extend(["", "## Net Role Gaps", ""])
        if unknown_nets:
            for net_name in sorted(set(unknown_nets)):
                lines.append(f"- UNKNOWN net role: {net_name}")
        else:
            lines.append("- No UNKNOWN net roles remain in the current intent map.")
        lines.extend(
            [
                "",
                "## Exact Next Required Action",
                "",
                "- Enter R2 generator architecture design using the canonical parameters, module roles, and net-role map defined by R1.",
            ]
        )
        _write_text(out, "\n".join(lines) + "\n")

    def _build_report(
        self,
        canonical: CanonicalSramLayoutParameters,
        module_roles: list[ModuleToPhysicalRole],
        net_roles: list[NetToLayoutRole],
    ) -> dict[str, Any]:
        artifact_paths = {
            "R1_layout_intent_available": self.out_dir / "openyield_sram_layout_intent.json",
            "canonical_parameters_available": self.out_dir / "openyield_sram_layout_intent.json",
            "array_topology_contract_available": self.out_dir / "openyield_array_topology_contract.json",
            "row_path_intent_available": self.out_dir / "openyield_row_path_intent.json",
            "column_path_intent_available": self.out_dir / "openyield_column_path_intent.json",
            "control_path_intent_available": self.out_dir / "openyield_control_path_intent.json",
            "power_intent_available": self.out_dir / "openyield_power_intent.json",
            "pin_intent_available": self.out_dir / "openyield_pin_intent.json",
            "net_to_layout_role_map_available": self.out_dir / "openyield_net_to_layout_role_map.csv",
            "module_to_physical_role_map_available": self.out_dir / "openyield_module_to_physical_role_map.csv",
            "layout_intent_matrix_available": self.out_matrix_csv,
        }
        unknown_modules = [role.module_name for role in module_roles if role.physical_role == "UNKNOWN"]
        unknown_nets = sorted({role.net_name for role in net_roles if role.net_category == "UNKNOWN"})
        blockers: list[str] = []
        for key, path in artifact_paths.items():
            if not path.exists():
                blockers.append(f"missing_artifact:{path}")
        if unknown_modules:
            blockers.append("unknown_module_roles_present")
        for module in L3_TARGET_MODULES:
            if module not in {role.module_name for role in module_roles}:
                blockers.append(f"missing_module_role:{module}")

        report = {key: path.exists() for key, path in artifact_paths.items()}
        report.update(
            {
                "canonical_parameter_count": len(canonical.parameters),
                "module_physical_role_count": len(module_roles),
                "net_layout_role_count": len(net_roles),
                "unknown_module_role_count": len(unknown_modules),
                "unknown_net_role_count": len(unknown_nets),
                "unknown_net_roles": unknown_nets,
                "remaining_R1_blockers": blockers,
                "remaining_R1_blockers_count": len(blockers),
                "can_claim_R1_layout_intent_defined_now": len(blockers) == 0,
                "can_enter_R2_generator_architecture_design": len(blockers) == 0,
                "can_claim_structure_complete_sram_gds_now": False,
                "can_claim_drc_clean_now": False,
                "can_claim_lvs_clean_now": False,
                "can_claim_timing_closure_now": False,
                "can_claim_signoff_ready_now": False,
            }
        )
        return report

    def _emit_report(self, report: dict[str, Any]) -> None:
        _json_dump(self.out_json, report)
        lines = [
            "# OpenYield R1 Layout Intent Report",
            "",
            f"- R1 layout intent available: `{report['R1_layout_intent_available']}`",
            f"- canonical parameter count: `{report['canonical_parameter_count']}`",
            f"- module physical role count: `{report['module_physical_role_count']}`",
            f"- net layout role count: `{report['net_layout_role_count']}`",
            f"- unknown module role count: `{report['unknown_module_role_count']}`",
            f"- unknown net role count: `{report['unknown_net_role_count']}`",
            f"- remaining blockers count: `{report['remaining_R1_blockers_count']}`",
            f"- can claim R1 layout intent defined now: `{report['can_claim_R1_layout_intent_defined_now']}`",
            f"- can enter R2 generator architecture design: `{report['can_enter_R2_generator_architecture_design']}`",
            "",
            "## Guardrails",
            "",
            f"- can claim structure-complete SRAM GDS now: `{report['can_claim_structure_complete_sram_gds_now']}`",
            f"- can claim DRC clean now: `{report['can_claim_drc_clean_now']}`",
            f"- can claim LVS clean now: `{report['can_claim_lvs_clean_now']}`",
            f"- can claim timing closure now: `{report['can_claim_timing_closure_now']}`",
            f"- can claim signoff ready now: `{report['can_claim_signoff_ready_now']}`",
            "",
            "## Remaining Blockers",
            "",
        ]
        if report["remaining_R1_blockers"]:
            for blocker in report["remaining_R1_blockers"]:
                lines.append(f"- {blocker}")
        else:
            lines.append("- None.")
        lines.extend(["", "## Unknown Net Roles", ""])
        if report["unknown_net_roles"]:
            for net_name in report["unknown_net_roles"]:
                lines.append(f"- {net_name}")
        else:
            lines.append("- None.")
        _write_text(self.out_report, "\n".join(lines) + "\n")
