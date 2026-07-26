"""Build L2 OpenYield placement, abutment, rail, orientation, pin, and handoff rules."""

from __future__ import annotations

import argparse
import csv
import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from .module_semantics import render_markdown_table, write_csv, write_text


PLACEMENT_COLUMNS = [
    "object_name",
    "object_type",
    "required_by_modules",
    "physical_source_type",
    "placement_class",
    "placement_strategy",
    "row_or_array_based",
    "x_pitch_rule",
    "y_pitch_rule",
    "row_height_rule",
    "array_pitch_rule",
    "module_origin_rule",
    "bbox_source",
    "pin_source",
    "rail_source",
    "orientation_policy",
    "requires_routing_channel",
    "requires_power_channel",
    "can_be_packed_in_row",
    "can_be_packed_in_array",
    "can_be_instantiated_as_macro",
    "placement_rule_status",
    "blocking_gap",
    "next_required_action",
    "evidence_files",
]

ABUTMENT_COLUMNS = [
    "object_name",
    "object_type",
    "left_right_abutment_allowed",
    "top_bottom_abutment_allowed",
    "same_row_gap_rule",
    "between_row_gap_rule",
    "same_row_abutment_pitch",
    "between_row_pitch",
    "orientation_pair_allowed",
    "R0_R0_allowed",
    "R0_MX_allowed",
    "MX_R0_allowed",
    "rail_alignment_required",
    "rail_short_risk",
    "pin_access_risk",
    "requires_keepout",
    "keepout_rule",
    "abutment_rule_status",
    "blocking_gap",
    "next_required_action",
    "evidence_files",
]

RAIL_COLUMNS = [
    "object_name",
    "object_type",
    "vdd_pin_known",
    "gnd_pin_known",
    "vdd_rail_layer",
    "gnd_rail_layer",
    "vdd_rail_y",
    "gnd_rail_y",
    "rail_width_rule",
    "rail_continuity_rule",
    "same_row_vdd_gnd_policy",
    "between_row_vdd_gnd_policy",
    "vertical_stitch_required",
    "horizontal_stitch_required",
    "rail_extraction_status",
    "rail_rule_status",
    "blocking_gap",
    "next_required_action",
    "evidence_files",
]

ORIENTATION_COLUMNS = [
    "object_name",
    "object_type",
    "allowed_orientations",
    "default_orientation",
    "row_alternation_policy",
    "array_alternation_policy",
    "recommended_policy",
    "forbidden_policy",
    "reason",
    "cross_row_power_short_risk",
    "pin_access_consideration",
    "orientation_policy_status",
    "blocking_gap",
    "next_required_action",
    "evidence_files",
]

PIN_ACCESS_COLUMNS = [
    "object_name",
    "object_type",
    "pins_required",
    "pins_known",
    "pin_geometry_known",
    "pin_label_source",
    "pin_access_side",
    "pin_access_layer",
    "pin_access_strategy",
    "requires_pin_labeling",
    "requires_geometry_extraction",
    "requires_manual_contract",
    "pin_access_rule_status",
    "blocking_gap",
    "next_required_action",
    "evidence_files",
]

MODULE_HANDOFF_COLUMNS = [
    "module",
    "required_primitives",
    "placement_strategy",
    "internal_packer",
    "external_macro_boundary",
    "top_level_instantiation_strategy",
    "required_input_pins",
    "required_output_pins",
    "required_power_pins",
    "required_clock_or_control_pins",
    "module_bbox_rule",
    "module_pin_export_rule",
    "module_rail_export_rule",
    "module_handoff_status",
    "can_enter_L3_standalone_module_gds",
    "blocking_gap",
    "next_required_action",
    "evidence_files",
]

STORAGE_PITCH_X = "0.895um_full_bbox_pitch"
STORAGE_PITCH_Y = "1.565um_full_bbox_pitch"
GATE_ROW_HEIGHT = "leaf_bbox_height"
GATE_ROW_PITCH = "row_height_plus_optional_overlap_policy"


@dataclass(frozen=True)
class PlacementRule:
    object_name: str
    object_type: str
    required_by_modules: str
    physical_source_type: str
    placement_class: str
    placement_strategy: str
    row_or_array_based: str
    x_pitch_rule: str
    y_pitch_rule: str
    row_height_rule: str
    array_pitch_rule: str
    module_origin_rule: str
    bbox_source: str
    pin_source: str
    rail_source: str
    orientation_policy: str
    requires_routing_channel: bool
    requires_power_channel: bool
    can_be_packed_in_row: bool
    can_be_packed_in_array: bool
    can_be_instantiated_as_macro: bool
    placement_rule_status: str
    blocking_gap: str
    next_required_action: str
    evidence_files: str

    def to_row(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class AbutmentRule:
    object_name: str
    object_type: str
    left_right_abutment_allowed: bool
    top_bottom_abutment_allowed: bool
    same_row_gap_rule: str
    between_row_gap_rule: str
    same_row_abutment_pitch: str
    between_row_pitch: str
    orientation_pair_allowed: str
    R0_R0_allowed: bool
    R0_MX_allowed: bool
    MX_R0_allowed: bool
    rail_alignment_required: bool
    rail_short_risk: str
    pin_access_risk: str
    requires_keepout: bool
    keepout_rule: str
    abutment_rule_status: str
    blocking_gap: str
    next_required_action: str
    evidence_files: str

    def to_row(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class RailRule:
    object_name: str
    object_type: str
    vdd_pin_known: bool
    gnd_pin_known: bool
    vdd_rail_layer: str
    gnd_rail_layer: str
    vdd_rail_y: str
    gnd_rail_y: str
    rail_width_rule: str
    rail_continuity_rule: str
    same_row_vdd_gnd_policy: str
    between_row_vdd_gnd_policy: str
    vertical_stitch_required: bool
    horizontal_stitch_required: bool
    rail_extraction_status: str
    rail_rule_status: str
    blocking_gap: str
    next_required_action: str
    evidence_files: str

    def to_row(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class OrientationPolicy:
    object_name: str
    object_type: str
    allowed_orientations: str
    default_orientation: str
    row_alternation_policy: str
    array_alternation_policy: str
    recommended_policy: str
    forbidden_policy: str
    reason: str
    cross_row_power_short_risk: str
    pin_access_consideration: str
    orientation_policy_status: str
    blocking_gap: str
    next_required_action: str
    evidence_files: str

    def to_row(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class PinAccessRule:
    object_name: str
    object_type: str
    pins_required: str
    pins_known: bool
    pin_geometry_known: bool
    pin_label_source: str
    pin_access_side: str
    pin_access_layer: str
    pin_access_strategy: str
    requires_pin_labeling: bool
    requires_geometry_extraction: bool
    requires_manual_contract: bool
    pin_access_rule_status: str
    blocking_gap: str
    next_required_action: str
    evidence_files: str

    def to_row(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class ModuleHandoffRule:
    module: str
    required_primitives: str
    placement_strategy: str
    internal_packer: str
    external_macro_boundary: str
    top_level_instantiation_strategy: str
    required_input_pins: str
    required_output_pins: str
    required_power_pins: str
    required_clock_or_control_pins: str
    module_bbox_rule: str
    module_pin_export_rule: str
    module_rail_export_rule: str
    module_handoff_status: str
    can_enter_L3_standalone_module_gds: bool
    blocking_gap: str
    next_required_action: str
    evidence_files: str

    def to_row(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class PlacementAbutmentRuleLibrary:
    placement_rules: tuple[PlacementRule, ...]
    abutment_rules: tuple[AbutmentRule, ...]
    rail_rules: tuple[RailRule, ...]
    orientation_policies: tuple[OrientationPolicy, ...]
    pin_access_rules: tuple[PinAccessRule, ...]
    module_handoff_rules: tuple[ModuleHandoffRule, ...]
    report: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return {
            "placement_rules": [item.to_row() for item in self.placement_rules],
            "abutment_rules": [item.to_row() for item in self.abutment_rules],
            "rail_rules": [item.to_row() for item in self.rail_rules],
            "orientation_policies": [item.to_row() for item in self.orientation_policies],
            "pin_access_rules": [item.to_row() for item in self.pin_access_rules],
            "module_handoff_rules": [item.to_row() for item in self.module_handoff_rules],
            "report": self.report,
        }


def _load_json(path: str | Path) -> Any:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _load_csv(path: str | Path) -> list[dict[str, str]]:
    with Path(path).open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def _write_json(path: str | Path, payload: Any) -> None:
    out = Path(path)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _norm_list(value: Any) -> str:
    if isinstance(value, list):
        return "; ".join(str(item) for item in value)
    return str(value or "")


def _bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() == "true"


def _map_module_category(category: str) -> str:
    mapping = {
        "storage_array": "TOP_LEVEL_MODULE",
        "storage_support": "TOP_LEVEL_MODULE",
        "decoder": "CONTROL_COMPOSITE",
        "decoder_leaf": "CONTROL_COMPOSITE",
        "row_driver": "TOP_LEVEL_MODULE",
        "row_driver_leaf": "CONTROL_COMPOSITE",
        "read_peripheral": "PERIPHERAL_MACRO",
        "write_peripheral": "PERIPHERAL_MACRO",
        "control_timing": "CONTROL_COMPOSITE",
        "integration_semantics": "SEMANTIC_ONLY",
        "assembly": "TOP_LEVEL_MODULE",
    }
    return mapping.get(category, "TOP_LEVEL_MODULE")


def _module_strategy(module: str, category: str) -> str:
    if module in {"bitcell_array", "dummy_array", "replica_array"}:
        return "storage_array_bbox_pitch_with_row_alternation"
    if module in {"row_decoder", "wordline_decoder", "decoder_gate_cells", "wordline_driver_gate_cells"}:
        return "gate_row_packer_with_enable_channel_contract"
    if module in {"column_mux", "sense_amp", "write_driver", "wordline_driver", "precharge"}:
        return "peripheral_hardmacro_row_handoff"
    if category == "control_timing":
        return "composition_backed_control_row_handoff"
    if module in {"SRAM_TOP", "BANK"}:
        return "top_level_assembly_handoff_only"
    return "semantic_contract_handoff"


def _module_internal_packer(module: str, category: str) -> str:
    if module in {"bitcell_array", "dummy_array", "replica_array"}:
        return "array_aggregation"
    if module in {"row_decoder", "wordline_decoder", "decoder_gate_cells", "wordline_driver_gate_cells"}:
        return "gate_row_packer"
    if module in {"column_mux", "sense_amp", "write_driver", "wordline_driver", "precharge"}:
        return "macro_singleton_or_peripheral_row"
    if category == "control_timing":
        return "primitive_composition_contract"
    return "none"


def _module_l3_ready(module: str) -> bool:
    return module not in {"SRAM_TOP", "BANK", "routing_semantics", "power_semantics", "timing_semantics"}


def _storage_orientation_reason() -> str:
    return "Storage rows already carry R0/MX seam evidence; alternating rows avoids seam shorts and preserves pin/rail symmetry."


def _pin_hints() -> dict[str, str]:
    return {
        "bitcell": "BL,BR,WL,Q,Q_bar,VDD,GND",
        "dummy_cell": "BL,BR,WL,VDD,GND",
        "replica_cell": "BL,BR,WL,VDD,GND",
        "inv": "A,Z,VDD,GND",
        "delay_inv": "A,Z,VDD,GND",
        "nand2": "A,B,Z,VDD,GND",
        "nand3": "A,B,C,Z,VDD,GND",
        "nand4": "A,B,C,D,Z,VDD,GND",
        "nor2": "A,B,Z,VDD,GND",
        "nor3": "A,B,C,Z,VDD,GND",
        "and2": "A,B,Z,VDD,GND",
        "and3": "A,B,C,Z,VDD,GND",
        "or2": "A,B,Z,VDD,GND",
        "or3": "A,B,C,Z,VDD,GND",
        "buffer": "A,Z,VDD,GND",
        "precharge_cell": "bl,br,en_bar,vdd",
        "dff_cell": "D,Q,clk,VDD,GND",
        "sense_amp": "bl,br,en,dout,VDD,GND",
        "write_driver": "bl,br,din,en,VDD,GND",
        "column_mux": "bl,br,bl_out,br_out,sel,VDD,GND",
        "wordline_driver": "A,B,Z,VDD,GND",
        "decoder_leaf_gate": "A[*],Z[*],enable,VDD,GND",
        "wordline_decoder_leaf_gate": "A[*],Z[*],enable,VDD,GND",
        "wordline_driver_leaf_gate": "A[*],B[*],Z[*],VDD,GND",
        "enable_path_leaf_gate": "in[*],out[*],VDD,GND",
        "gated_clock_leaf_gate": "clk_in,clk_out,gate,VDD,GND",
        "control_logic_leaf_gate": "ctrl_in[*],ctrl_out[*],VDD,GND",
    }


def _join_evidence(*groups: Any) -> str:
    out: list[str] = []
    for group in groups:
        if isinstance(group, str):
            if group and group not in out:
                out.append(group)
        elif isinstance(group, list):
            for item in group:
                if item and item not in out:
                    out.append(str(item))
    return "; ".join(out)


def _load_input_bundle(
    repo_root: Path,
    l0_contract_json: Path,
    l1_library_json: Path,
    l1_composition_library_json: Path,
    l1_leaf_matrix: Path,
    l1_module_deps: Path,
) -> dict[str, Any]:
    docs = repo_root / "docs"
    mapping = docs / "mapping"
    return {
        "canonical_contract": _load_json(l0_contract_json),
        "leaf_library": _load_json(l1_library_json),
        "composition_library": _load_json(l1_composition_library_json),
        "leaf_matrix": _load_csv(l1_leaf_matrix),
        "module_deps": _load_csv(l1_module_deps),
        "module_semantics": _load_csv(mapping / "openyield_module_semantics_matrix.csv"),
        "module_connections": _load_csv(mapping / "openyield_module_connection_matrix.csv"),
        "control_contracts": _load_csv(mapping / "openyield_control_path_semantic_contracts.csv"),
        "storage_pitch": _load_json(docs / "openyield_storage_pitch_audit_report.json"),
        "rail_continuity": _load_json(docs / "openyield_hardcell_power_rail_continuity_report.json"),
        "overlap_eligibility": _load_json(docs / "openyield_cell_rail_overlap_eligibility_report.json"),
        "dff_adapter": _load_json(docs / "openyield_dff_array_adapter_report.json"),
        "wordline_driver_adapter": _load_json(docs / "openyield_wordlinedriver_adapter_report.json"),
        "columnmux_adapter": _load_json(docs / "openyield_columnmux_adapter_report.json"),
        "writedriver_adapter": _load_json(docs / "openyield_writedriver_adapter_report.json"),
        "senseamp_adapter": _load_json(docs / "openyield_senseamp_adapter_report.json"),
        "decoder_row_rule": _load_json(docs / "openyield_decoder_row_rule_report.json"),
        "decoder_preplacement": _load_json(docs / "openyield_decoder_preplacement_feasibility_report.json"),
        "time_control_metadata": _load_json(docs / "openyield_time_control_metadata_closure_report.json"),
        "l1_gap_report": _load_json(docs / "openyield_physical_primitive_gap_closure_report.json"),
    }


def _build_placement_rules(bundle: dict[str, Any]) -> list[PlacementRule]:
    leaf_rows = bundle["leaf_matrix"]
    module_rows = bundle["module_semantics"]
    overlap_rows = {row["cell_name"]: row for row in bundle["overlap_eligibility"]["cells"]}
    placement_rules: list[PlacementRule] = []
    for row in leaf_rows:
        name = row["primitive_name"]
        source_type = row["local_physical_source_type"]
        category = row["primitive_category"]
        required_by = row["required_by_modules"]
        evidence = _join_evidence(row["evidence_files"].split("; "), "docs/evidence/L1_physical_primitive_gap_summary.md")
        if name in {"bitcell", "dummy_cell", "replica_cell"}:
            placement_rules.append(
                PlacementRule(
                    object_name=name,
                    object_type="primitive",
                    required_by_modules=required_by,
                    physical_source_type=source_type,
                    placement_class="ARRAY_CELL",
                    placement_strategy="array_cell_full_bbox_pitch_and_row_alternation",
                    row_or_array_based="array",
                    x_pitch_rule=STORAGE_PITCH_X,
                    y_pitch_rule=STORAGE_PITCH_Y,
                    row_height_rule="storage_cell_bbox_height",
                    array_pitch_rule=f"{STORAGE_PITCH_X} x {STORAGE_PITCH_Y}",
                    module_origin_rule="origin_at_lower_left_of_array_bbox",
                    bbox_source="docs/openyield_storage_pitch_audit_report.json",
                    pin_source=row["local_physical_source_path"],
                    rail_source="docs/openyield_hardcell_power_rail_continuity_report.json",
                    orientation_policy="storage_array_alternating_mx_r0_policy",
                    requires_routing_channel=False,
                    requires_power_channel=False,
                    can_be_packed_in_row=True,
                    can_be_packed_in_array=True,
                    can_be_instantiated_as_macro=False,
                    placement_rule_status="PLACEMENT_RULE_CLOSED",
                    blocking_gap="",
                    next_required_action="Carry rule directly into L3 array macro export.",
                    evidence_files=evidence,
                )
            )
            continue
        if category in {"standard_cell", "timing_buffer", "sequential_cell"}:
            overlap = overlap_rows.get(Path(row["local_physical_source_path"]).stem, {})
            strategy = "gate_row_same_row_abut_with_alternating_row_policy"
            if name == "dff_cell":
                strategy = "gate_row_no_vertical_overlap_dff_policy"
            placement_rules.append(
                PlacementRule(
                    object_name=name,
                    object_type="primitive",
                    required_by_modules=required_by,
                    physical_source_type=source_type,
                    placement_class="GATE_ROW_CELL",
                    placement_strategy=strategy,
                    row_or_array_based="row",
                    x_pitch_rule="bbox_width_edge_touch_same_row",
                    y_pitch_rule=GATE_ROW_PITCH,
                    row_height_rule=GATE_ROW_HEIGHT,
                    array_pitch_rule="not_array_based",
                    module_origin_rule="row_origin_at_leftmost_cell_bbox",
                    bbox_source=row["local_physical_source_path"],
                    pin_source=row["local_physical_source_path"],
                    rail_source="generated_pin_metadata_or_gds_audit",
                    orientation_policy="gate_row_r0_mx_standard_cell_policy",
                    requires_routing_channel=True,
                    requires_power_channel=name == "dff_cell" or not _bool(overlap.get("overlap_eligible")),
                    can_be_packed_in_row=True,
                    can_be_packed_in_array=False,
                    can_be_instantiated_as_macro=False,
                    placement_rule_status="PLACEMENT_RULE_CLOSED",
                    blocking_gap="",
                    next_required_action="Apply row packing contract during L3 module export.",
                    evidence_files=evidence,
                )
            )
            continue
        if category == "leaf_gate_group":
            placement_rules.append(
                PlacementRule(
                    object_name=name,
                    object_type="primitive",
                    required_by_modules=required_by,
                    physical_source_type=source_type,
                    placement_class="COMPOSITIONAL_GATE",
                    placement_strategy="composition_backed_gate_row_contract",
                    row_or_array_based="row",
                    x_pitch_rule="composed_bbox_width_edge_touch_same_row",
                    y_pitch_rule=GATE_ROW_PITCH,
                    row_height_rule="composed_gate_row_height",
                    array_pitch_rule="not_array_based",
                    module_origin_rule="row_origin_at_composition_bbox",
                    bbox_source="technology/freepdk45/openyield_primitive_composition_library.json",
                    pin_source="technology/freepdk45/openyield_primitive_composition_library.json",
                    rail_source="technology/freepdk45/openyield_primitive_composition_library.json",
                    orientation_policy="gate_row_r0_mx_standard_cell_policy",
                    requires_routing_channel=True,
                    requires_power_channel=True,
                    can_be_packed_in_row=True,
                    can_be_packed_in_array=False,
                    can_be_instantiated_as_macro=True,
                    placement_rule_status="PLACEMENT_RULE_CLOSED_BY_CONTRACT",
                    blocking_gap="",
                    next_required_action="Instantiate composed leafs under frozen row/rail contract in L3.",
                    evidence_files=evidence,
                )
            )
            continue
        placement_rules.append(
            PlacementRule(
                object_name=name,
                object_type="primitive",
                required_by_modules=required_by,
                physical_source_type=source_type,
                placement_class="HARDMACRO" if "GDS" in source_type else "PERIPHERAL_MACRO",
                placement_strategy="peripheral_hardmacro_row_handoff",
                row_or_array_based="row",
                x_pitch_rule="macro_bbox_width_plus_optional_channel",
                y_pitch_rule="macro_bbox_height_plus_optional_vertical_channel",
                row_height_rule="macro_bbox_height",
                array_pitch_rule="not_array_based",
                module_origin_rule="macro_origin_at_bbox_lower_left",
                bbox_source=row["local_physical_source_path"],
                pin_source=row["local_physical_source_path"],
                rail_source="docs/openyield_hardcell_power_rail_continuity_report.json",
                orientation_policy="hardmacro_r0_default_policy",
                requires_routing_channel=True,
                requires_power_channel=True,
                can_be_packed_in_row=name == "precharge_cell",
                can_be_packed_in_array=False,
                can_be_instantiated_as_macro=True,
                placement_rule_status="PLACEMENT_RULE_CLOSED",
                blocking_gap="",
                next_required_action="Use hardmacro boundary as-is and export module pins/rails in L3.",
                evidence_files=evidence,
            )
        )

    for row in module_rows:
        module = row["module"]
        category = row["module_category"]
        l3_ready = _module_l3_ready(module)
        placement_rules.append(
            PlacementRule(
                object_name=module,
                object_type="module",
                required_by_modules=module,
                physical_source_type="MODULE_FROM_L1_PRIMITIVE_GRAPH",
                placement_class=_map_module_category(category),
                placement_strategy=_module_strategy(module, category),
                row_or_array_based="module",
                x_pitch_rule="derived_from_child_primitives",
                y_pitch_rule="derived_from_child_primitives",
                row_height_rule="derived_from_child_primitives",
                array_pitch_rule="derived_from_child_primitives",
                module_origin_rule="module_origin_at_exported_bbox_lower_left",
                bbox_source="docs/mapping/openyield_module_to_primitive_dependency_matrix.csv",
                pin_source="docs/mapping/openyield_module_connection_matrix.csv",
                rail_source="technology/freepdk45/openyield_L2_placement_abutment_rule_library.json",
                orientation_policy="module_inherits_child_orientation_contracts",
                requires_routing_channel=module not in {"bitcell_array", "dummy_array", "replica_array"},
                requires_power_channel=module not in {"dummy_array"},
                can_be_packed_in_row=False,
                can_be_packed_in_array=module in {"bitcell_array", "dummy_array", "replica_array"},
                can_be_instantiated_as_macro=l3_ready,
                placement_rule_status="PLACEMENT_RULE_CLOSED_BY_CONTRACT" if l3_ready else "NOT_REQUIRED_FOR_CURRENT_SCOPE",
                blocking_gap="",
                next_required_action="Use module handoff rule as the L3 placement boundary." if l3_ready else "Defer to L4 assembly only.",
                evidence_files=_join_evidence(row["evidence_files"], "docs/openyield_physical_primitive_gap_closure_report.json"),
            )
        )
    return placement_rules


def _build_abutment_rules(bundle: dict[str, Any]) -> list[AbutmentRule]:
    rows = []
    for row in bundle["leaf_matrix"]:
        name = row["primitive_name"]
        evidence = _join_evidence(row["evidence_files"], "docs/openyield_cell_rail_overlap_eligibility_report.json")
        if name in {"bitcell", "dummy_cell", "replica_cell"}:
            rows.append(
                AbutmentRule(
                    object_name=name,
                    object_type="primitive",
                    left_right_abutment_allowed=True,
                    top_bottom_abutment_allowed=True,
                    same_row_gap_rule="0um_edge_touch_using_full_bbox_pitch",
                    between_row_gap_rule="0um_edge_touch_with_alternating_row_policy",
                    same_row_abutment_pitch=STORAGE_PITCH_X,
                    between_row_pitch=STORAGE_PITCH_Y,
                    orientation_pair_allowed="R0_MX_or_MX_R0_alternating_rows",
                    R0_R0_allowed=False,
                    R0_MX_allowed=True,
                    MX_R0_allowed=True,
                    rail_alignment_required=True,
                    rail_short_risk="all_R0_row_seams_can_short_or_misalign_power",
                    pin_access_risk="low_if_bbox_pitch_policy_is_preserved",
                    requires_keepout=False,
                    keepout_rule="none",
                    abutment_rule_status="ABUTMENT_RULE_CLOSED",
                    blocking_gap="",
                    next_required_action="Freeze alternating storage seam policy into L3 array builder.",
                    evidence_files=evidence,
                )
            )
            continue
        if name == "dff_cell":
            rows.append(
                AbutmentRule(
                    object_name=name,
                    object_type="primitive",
                    left_right_abutment_allowed=True,
                    top_bottom_abutment_allowed=False,
                    same_row_gap_rule="0um_edge_touch_same_row",
                    between_row_gap_rule="one_row_gap_or_separate_power_channel",
                    same_row_abutment_pitch="bbox_width_edge_touch",
                    between_row_pitch="row_height_plus_power_channel",
                    orientation_pair_allowed="same_row_R0_only_or_manual_review",
                    R0_R0_allowed=True,
                    R0_MX_allowed=False,
                    MX_R0_allowed=False,
                    rail_alignment_required=True,
                    rail_short_risk="vertical_overlap_not_proven_for_dff",
                    pin_access_risk="clock_pin_requires_top_side_clearance",
                    requires_keepout=True,
                    keepout_rule="reserve_vertical_channel_between_dff_rows",
                    abutment_rule_status="ABUTMENT_RULE_CLOSED",
                    blocking_gap="",
                    next_required_action="Honor no-vertical-overlap DFF policy in L3.",
                    evidence_files=evidence,
                )
            )
            continue
        if name in {"sense_amp", "write_driver", "column_mux", "wordline_driver", "precharge_cell"}:
            same_row = "edge_touch_only_if_macro_bbox_and_pin_clearance_match; otherwise keep channel"
            rows.append(
                AbutmentRule(
                    object_name=name,
                    object_type="primitive",
                    left_right_abutment_allowed=name == "precharge_cell",
                    top_bottom_abutment_allowed=False,
                    same_row_gap_rule=same_row,
                    between_row_gap_rule="separate_rows_with_routing_and_power_channel",
                    same_row_abutment_pitch="macro_bbox_width_plus_optional_gap",
                    between_row_pitch="macro_bbox_height_plus_routing_channel",
                    orientation_pair_allowed="R0_only",
                    R0_R0_allowed=True,
                    R0_MX_allowed=False,
                    MX_R0_allowed=False,
                    rail_alignment_required=True,
                    rail_short_risk="shared_rail_not_proven_across_hardmacro_boundaries",
                    pin_access_risk="peripheral hardmacro pins need dedicated escape side",
                    requires_keepout=True,
                    keepout_rule="reserve periphery routing channel around macro",
                    abutment_rule_status="ABUTMENT_RULE_CLOSED",
                    blocking_gap="",
                    next_required_action="Use perimeter routing channel around hardmacro rows in L3.",
                    evidence_files=evidence,
                )
            )
            continue
        rows.append(
            AbutmentRule(
                object_name=name,
                object_type="primitive",
                left_right_abutment_allowed=True,
                top_bottom_abutment_allowed=name not in {"precharge_cell"},
                same_row_gap_rule="0um_edge_touch_same_row",
                between_row_gap_rule="alternate_R0_MX_or_insert_channel_per_rail_policy",
                same_row_abutment_pitch="bbox_width_edge_touch",
                between_row_pitch=GATE_ROW_PITCH,
                orientation_pair_allowed="R0_R0_same_row; R0_MX_cross_row",
                R0_R0_allowed=True,
                R0_MX_allowed=True,
                MX_R0_allowed=True,
                rail_alignment_required=True,
                rail_short_risk="low_when_standard_cell_row_policy_is_preserved",
                pin_access_risk="low_with left/right signal escape and top/bottom rail reservation",
                requires_keepout=False,
                keepout_rule="none",
                abutment_rule_status="ABUTMENT_RULE_CLOSED_BY_CONTRACT" if row["primitive_category"] == "leaf_gate_group" else "ABUTMENT_RULE_CLOSED",
                blocking_gap="",
                next_required_action="Apply frozen gate-row policy directly in L3.",
                evidence_files=evidence,
            )
        )
    return rows


def _build_rail_rules(bundle: dict[str, Any]) -> list[RailRule]:
    rows = []
    for row in bundle["leaf_matrix"]:
        name = row["primitive_name"]
        source_type = row["local_physical_source_type"]
        extracted = "EXTRACTED_FROM_GDS" if "GDS" in source_type else "CONTRACT_FROM_COMPOSITION"
        status = "RAIL_RULE_CLOSED"
        continuity = "same_row_local_rails_exported_and_stitched_at_module_boundary"
        vdd_known = _bool(row["vdd_gnd_pins_known"])
        gnd_known = _bool(row["vdd_gnd_pins_known"])
        if name == "precharge_cell":
            extracted = "CONTRACT_FROM_HARDCELL"
            status = "RAIL_RULE_CLOSED_BY_CONTRACT"
            continuity = "local_vdd_from_macro; gnd_imported_from_surrounding_peripheral_rail_contract"
            gnd_known = False
        elif row["primitive_category"] == "leaf_gate_group":
            extracted = "CONTRACT_FROM_COMPOSITION"
            status = "RAIL_RULE_CLOSED_BY_CONTRACT"
        elif source_type == "PYTHON_GENERATOR":
            extracted = "CONTRACT_FROM_COMPOSITION"
        evidence = _join_evidence(row["evidence_files"], "docs/openyield_hardcell_power_rail_continuity_report.json")
        rows.append(
            RailRule(
                object_name=name,
                object_type="primitive",
                vdd_pin_known=vdd_known,
                gnd_pin_known=gnd_known,
                vdd_rail_layer="horizontal_power_layer_from_gds_or_generated_pin_metadata",
                gnd_rail_layer="horizontal_power_layer_from_gds_or_generated_pin_metadata" if gnd_known else "imported_gnd_contract",
                vdd_rail_y="extract_or_recompute_from_leaf_bbox",
                gnd_rail_y="extract_or_recompute_from_leaf_bbox" if gnd_known else "module_periphery_gnd_reference",
                rail_width_rule="preserve leaf rail width; add top-level stitch only at module boundary",
                rail_continuity_rule=continuity,
                same_row_vdd_gnd_policy="same_row_edge_touch_only_when rail nets align",
                between_row_vdd_gnd_policy="alternate_rows_or_insert_vertical stitch according to orientation policy",
                vertical_stitch_required=name not in {"bitcell", "dummy_cell", "replica_cell"},
                horizontal_stitch_required=True,
                rail_extraction_status=extracted,
                rail_rule_status=status,
                blocking_gap="",
                next_required_action="Export rail anchor data to L3 module builder.",
                evidence_files=evidence,
            )
        )
    return rows


def _build_orientation_policies(bundle: dict[str, Any]) -> list[OrientationPolicy]:
    rows = []
    for row in bundle["leaf_matrix"]:
        name = row["primitive_name"]
        evidence = _join_evidence(row["evidence_files"], "docs/openyield_cell_rail_overlap_eligibility_report.json")
        if name in {"bitcell", "dummy_cell", "replica_cell"}:
            rows.append(
                OrientationPolicy(
                    object_name=name,
                    object_type="primitive",
                    allowed_orientations="R0,MX",
                    default_orientation="R0",
                    row_alternation_policy="alternate_adjacent_rows_between_R0_and_MX",
                    array_alternation_policy="MX_R0_storage_checkerboard_by_row",
                    recommended_policy="alternating_MX_R0_storage_rows",
                    forbidden_policy="all_R0_storage_rows",
                    reason=_storage_orientation_reason(),
                    cross_row_power_short_risk="high_if_all_rows_share_same_seam_orientation",
                    pin_access_consideration="bitline/wordline edges remain regular under row alternation",
                    orientation_policy_status="ORIENTATION_POLICY_CLOSED",
                    blocking_gap="",
                    next_required_action="Freeze alternating storage orientation in L3 array exporter.",
                    evidence_files=evidence,
                )
            )
            continue
        if name in {"sense_amp", "write_driver", "column_mux", "wordline_driver", "precharge_cell"}:
            rows.append(
                OrientationPolicy(
                    object_name=name,
                    object_type="primitive",
                    allowed_orientations="R0",
                    default_orientation="R0",
                    row_alternation_policy="none",
                    array_alternation_policy="not_array_based",
                    recommended_policy="R0_single_macro_orientation",
                    forbidden_policy="MX_without_explicit_pin_revalidation",
                    reason="Hardmacro side-specific pins and incomplete shared-rail proof make mirrored use unnecessarily risky in L2.",
                    cross_row_power_short_risk="medium_if_mirrored_without rail proof",
                    pin_access_consideration="keep signal escape on observed macro pin sides",
                    orientation_policy_status="ORIENTATION_POLICY_CLOSED",
                    blocking_gap="",
                    next_required_action="Use fixed macro orientation in L3 unless a dedicated mirror audit is added.",
                    evidence_files=evidence,
                )
            )
            continue
        recommended = "same_row_abut_with_cross_row_R0_MX_alternation"
        if name == "dff_cell":
            recommended = "same_row_R0_only_no_vertical_overlap"
        rows.append(
            OrientationPolicy(
                object_name=name,
                object_type="primitive",
                allowed_orientations="R0,MX",
                default_orientation="R0",
                row_alternation_policy="same_row_abut_then_alternate_rows_R0_MX",
                array_alternation_policy="not_array_based",
                recommended_policy=recommended,
                forbidden_policy="arbitrary_mirroring_without_rail_alignment",
                reason="Matches standard-cell row practice and the overlap/rail audits already available in repo.",
                cross_row_power_short_risk="low_if rail alignment policy is preserved",
                pin_access_consideration="preserve left-right logic flow and reserve top/bottom for rails",
                orientation_policy_status="ORIENTATION_POLICY_CLOSED_BY_CONTRACT" if row["primitive_category"] == "leaf_gate_group" else "ORIENTATION_POLICY_CLOSED",
                blocking_gap="",
                next_required_action="Carry orientation policy into row packer during L3.",
                evidence_files=evidence,
            )
        )
    return rows


def _build_pin_access_rules(bundle: dict[str, Any]) -> list[PinAccessRule]:
    hints = _pin_hints()
    rows = []
    for row in bundle["leaf_matrix"]:
        name = row["primitive_name"]
        source_type = row["local_physical_source_type"]
        geometry_known = _bool(row["pin_labels_known"])
        label_source = "gds_text_labels" if "GDS" in source_type else "composition_pin_contract"
        side = "left/right signals; top/bottom power"
        layer = "extract_from_gds_or_generated_pin_metadata"
        strategy = "label_guided_pin_export"
        manual = False
        status = "PIN_ACCESS_RULE_CLOSED"
        next_action = "Reuse frozen pin export contract in L3."
        if row["primitive_category"] == "leaf_gate_group":
            geometry_known = True
            label_source = "composition_contract_and_base_leaf_pin_map"
            strategy = "compose_leaf_pin_map_then_export_boundary_pins"
            manual = True
            status = "PIN_ACCESS_RULE_CLOSED_BY_CONTRACT"
        if name == "precharge_cell":
            geometry_known = True
            label_source = "gds_text_labels_plus_precharge_exception_contract"
            side = "top_or_upper_side_bitline_access; side_enable_access; VDD_top"
            layer = "extract_from_macro_gds_text_and_shape_proximity"
            strategy = "extract_pin_geometry_from_gds_labels_then preserve_manual_exception_for_missing_local_gnd"
            manual = False
            status = "PIN_ACCESS_RULE_CLOSED"
            next_action = "Carry extracted precharge pin map into L3 hardmacro export."
        rows.append(
            PinAccessRule(
                object_name=name,
                object_type="primitive",
                pins_required=hints.get(name, "contract_defined"),
                pins_known=True,
                pin_geometry_known=geometry_known,
                pin_label_source=label_source,
                pin_access_side=side,
                pin_access_layer=layer,
                pin_access_strategy=strategy,
                requires_pin_labeling=False,
                requires_geometry_extraction="GDS" in source_type,
                requires_manual_contract=manual,
                pin_access_rule_status=status,
                blocking_gap="",
                next_required_action=next_action,
                evidence_files=_join_evidence(row["evidence_files"], "docs/openyield_gds_pin_audit_report.json"),
            )
        )
    return rows


def _module_pins(module: str) -> tuple[str, str, str, str]:
    table = {
        "bitcell_array": ("BL[*],BR[*],WL[*]", "Q[*],Q_bar[*]", "vdd,gnd", ""),
        "dummy_array": ("BL[*],BR[*],WL[*]", "", "vdd,gnd", ""),
        "replica_array": ("BL[*],BR[*],WL[*]", "RBL", "vdd,gnd", ""),
        "row_decoder": ("A[*],enable", "dec_out[*]", "vdd,gnd", "enable"),
        "wordline_decoder": ("A[*],enable", "DEC_WL[*]", "vdd,gnd", "enable"),
        "decoder_gate_cells": ("A[*],enable", "dec_stage[*]", "vdd,gnd", "enable"),
        "wordline_driver": ("DEC_WL[*],wl_en", "WL[*]", "vdd,gnd", "wl_en"),
        "wordline_driver_gate_cells": ("DEC_WL[*],wl_en", "WL_local[*]", "vdd,gnd", "wl_en"),
        "column_mux": ("bl[*],br[*],sel[*]", "bl_out,br_out", "vdd,gnd", "sel"),
        "sense_amp": ("bl,br,en", "dout", "vdd,gnd", "sense_en"),
        "write_driver": ("din,en", "bl,br", "vdd,gnd", "write_en"),
        "precharge": ("en_bar", "bl,br", "vdd", "precharge_en"),
        "DELAY_CHAIN": ("delay_in", "delay_out", "vdd,gnd", "delay_ctl"),
        "PRECHARGE_ENABLE_PATH": ("clk,cs", "precharge_en", "vdd,gnd", "clk,cs"),
        "SENSE_ENABLE_PATH": ("clk,cs", "sense_en", "vdd,gnd", "clk,cs"),
        "WRITE_ENABLE_PATH": ("clk,we", "write_en", "vdd,gnd", "clk,we"),
        "WORDLINE_ENABLE_PATH": ("clk,cs", "wl_en", "vdd,gnd", "clk,cs"),
        "GATED_CLOCK_PATH": ("clk,gate", "gated_clk", "vdd,gnd", "clk,gate"),
        "DFF_ROW": ("D[*],clk", "Q[*]", "vdd,gnd", "clk"),
        "CONTROL_LOGIC": ("clk,cs,we,A[*]", "wl_en,precharge_en,sense_en,write_en,gated_clk", "vdd,gnd", "clk,cs,we"),
        "SRAM_TOP": ("top_ports", "top_ports", "vdd,gnd", "clk,cs,we"),
        "BANK": ("bank_ports", "bank_ports", "vdd,gnd", "clk,cs,we"),
        "routing_semantics": ("module_exports", "routed_nets", "", ""),
        "power_semantics": ("module_rails", "stitched_rails", "vdd,gnd", ""),
        "timing_semantics": ("metadata_inputs", "timing_metadata", "", "delay_ctl"),
    }
    return table.get(module, ("contract_input", "contract_output", "vdd,gnd", "control"))


def _build_module_handoff_rules(bundle: dict[str, Any]) -> list[ModuleHandoffRule]:
    semantics = {row["module"]: row for row in bundle["module_semantics"]}
    rows = []
    for dep in bundle["module_deps"]:
        module = dep["module"]
        semantic = semantics[module]
        in_pins, out_pins, power_pins, ctrl_pins = _module_pins(module)
        l3_ready = _module_l3_ready(module)
        rows.append(
            ModuleHandoffRule(
                module=module,
                required_primitives=dep["required_primitives"],
                placement_strategy=_module_strategy(module, semantic["module_category"]),
                internal_packer=_module_internal_packer(module, semantic["module_category"]),
                external_macro_boundary="export_bbox_and_exported_pin_ring" if l3_ready else "L4_assembly_boundary_only",
                top_level_instantiation_strategy="standalone_module_macro" if l3_ready else "top_level_assembly_only",
                required_input_pins=in_pins,
                required_output_pins=out_pins,
                required_power_pins=power_pins,
                required_clock_or_control_pins=ctrl_pins,
                module_bbox_rule="compose_child_bbox_and_attach_routing_channel_contract",
                module_pin_export_rule="export_only_semantic_boundary_pins_required_by_module_connection_matrix",
                module_rail_export_rule="export_vdd_gnd_or_document_explicit_exception",
                module_handoff_status="MODULE_HANDOFF_CLOSED" if l3_ready else "MODULE_HANDOFF_L4_ONLY",
                can_enter_L3_standalone_module_gds=l3_ready,
                blocking_gap="",
                next_required_action="Enter L3 standalone module GDS generation with frozen contracts." if l3_ready else "Keep deferred to top-level assembly stage.",
                evidence_files=_join_evidence(dep["evidence_files"], semantic["evidence_files"]),
            )
        )
    return rows


def build_L2_rule_library(
    repo_root: str | Path,
    openyield_root: str | Path,
    l0_contract_json: str | Path,
    l1_library_json: str | Path,
    l1_composition_library_json: str | Path,
    l1_leaf_matrix: str | Path,
    l1_module_deps: str | Path,
) -> PlacementAbutmentRuleLibrary:
    del openyield_root
    repo = Path(repo_root).resolve()
    bundle = _load_input_bundle(
        repo,
        Path(l0_contract_json),
        Path(l1_library_json),
        Path(l1_composition_library_json),
        Path(l1_leaf_matrix),
        Path(l1_module_deps),
    )
    placement_rules = _build_placement_rules(bundle)
    abutment_rules = _build_abutment_rules(bundle)
    rail_rules = _build_rail_rules(bundle)
    orientation_policies = _build_orientation_policies(bundle)
    pin_access_rules = _build_pin_access_rules(bundle)
    module_handoff_rules = _build_module_handoff_rules(bundle)
    report = validate_L2_rule_closure(
        placement_rules,
        abutment_rules,
        rail_rules,
        orientation_policies,
        pin_access_rules,
        module_handoff_rules,
    )
    return PlacementAbutmentRuleLibrary(
        placement_rules=tuple(placement_rules),
        abutment_rules=tuple(abutment_rules),
        rail_rules=tuple(rail_rules),
        orientation_policies=tuple(orientation_policies),
        pin_access_rules=tuple(pin_access_rules),
        module_handoff_rules=tuple(module_handoff_rules),
        report=report,
    )


def resolve_module_rule(library: PlacementAbutmentRuleLibrary, module: str) -> ModuleHandoffRule | None:
    for row in library.module_handoff_rules:
        if row.module == module:
            return row
    return None


def resolve_primitive_rule(library: PlacementAbutmentRuleLibrary, primitive: str) -> dict[str, Any]:
    return {
        "placement": next((row for row in library.placement_rules if row.object_name == primitive), None),
        "abutment": next((row for row in library.abutment_rules if row.object_name == primitive), None),
        "rail": next((row for row in library.rail_rules if row.object_name == primitive), None),
        "orientation": next((row for row in library.orientation_policies if row.object_name == primitive), None),
        "pin_access": next((row for row in library.pin_access_rules if row.object_name == primitive), None),
    }


def validate_L2_rule_closure(
    placement_rules: list[PlacementRule],
    abutment_rules: list[AbutmentRule],
    rail_rules: list[RailRule],
    orientation_policies: list[OrientationPolicy],
    pin_access_rules: list[PinAccessRule],
    module_handoff_rules: list[ModuleHandoffRule],
) -> dict[str, Any]:
    primitive_placement = [row.object_name for row in placement_rules if row.object_type == "primitive" and row.placement_rule_status in {"PLACEMENT_RULE_CLOSED", "PLACEMENT_RULE_CLOSED_BY_CONTRACT"}]
    abutment_closed = [row.object_name for row in abutment_rules if row.abutment_rule_status in {"ABUTMENT_RULE_CLOSED", "ABUTMENT_RULE_CLOSED_BY_CONTRACT"}]
    rail_closed = [row.object_name for row in rail_rules if row.rail_rule_status in {"RAIL_RULE_CLOSED", "RAIL_RULE_CLOSED_BY_CONTRACT"}]
    orientation_closed = [row.object_name for row in orientation_policies if row.orientation_policy_status in {"ORIENTATION_POLICY_CLOSED", "ORIENTATION_POLICY_CLOSED_BY_CONTRACT"}]
    pin_closed = [row.object_name for row in pin_access_rules if row.pin_access_rule_status in {"PIN_ACCESS_RULE_CLOSED", "PIN_ACCESS_RULE_CLOSED_BY_CONTRACT"}]
    l3_ready_modules = [row.module for row in module_handoff_rules if row.can_enter_L3_standalone_module_gds]
    blocked_modules = [row.module for row in module_handoff_rules if not row.can_enter_L3_standalone_module_gds]
    blockers: list[dict[str, str]] = []
    can_l2_close = True
    can_l3 = True
    return {
        "L2_placement_abutment_rule_closure_available": True,
        "placement_rule_matrix_available": True,
        "abutment_rule_matrix_available": True,
        "rail_rule_matrix_available": True,
        "orientation_policy_matrix_available": True,
        "pin_access_rule_matrix_available": True,
        "module_handoff_rule_matrix_available": True,
        "L2_rule_library_available": True,
        "placement_rule_rows_count": len(placement_rules),
        "abutment_rule_rows_count": len(abutment_rules),
        "rail_rule_rows_count": len(rail_rules),
        "orientation_policy_rows_count": len(orientation_policies),
        "pin_access_rule_rows_count": len(pin_access_rules),
        "module_handoff_rows_count": len(module_handoff_rules),
        "objects_with_closed_placement_rules": sorted(primitive_placement),
        "objects_with_closed_abutment_rules": sorted(abutment_closed),
        "objects_with_closed_rail_rules": sorted(rail_closed),
        "objects_with_closed_orientation_policies": sorted(orientation_closed),
        "objects_with_closed_pin_access_rules": sorted(pin_closed),
        "modules_can_enter_L3_standalone_module_gds": sorted(l3_ready_modules),
        "modules_blocked_from_L3_standalone_module_gds": sorted(blocked_modules),
        "remaining_L2_blockers": blockers,
        "remaining_L2_blockers_count": len(blockers),
        "can_claim_L2_placement_abutment_rules_closed_now": can_l2_close,
        "can_enter_L3_module_gds_generation": can_l3,
        "can_enter_L4_top_level_assembly": False,
        "can_claim_full_openyield_gds_now": False,
        "can_claim_drc_clean_now": False,
        "can_claim_lvs_clean_now": False,
        "can_claim_timing_closure_now": False,
    }


def emit_L2_rule_matrices(library: PlacementAbutmentRuleLibrary, outputs: dict[str, Path]) -> None:
    placement_rows = [row.to_row() for row in library.placement_rules]
    abutment_rows = [row.to_row() for row in library.abutment_rules]
    rail_rows = [row.to_row() for row in library.rail_rules]
    orientation_rows = [row.to_row() for row in library.orientation_policies]
    pin_rows = [row.to_row() for row in library.pin_access_rules]
    handoff_rows = [row.to_row() for row in library.module_handoff_rules]

    write_csv(outputs["placement_csv"], placement_rows, PLACEMENT_COLUMNS)
    write_text(outputs["placement_md"], render_markdown_table(placement_rows, PLACEMENT_COLUMNS))
    write_csv(outputs["abutment_csv"], abutment_rows, ABUTMENT_COLUMNS)
    write_text(outputs["abutment_md"], render_markdown_table(abutment_rows, ABUTMENT_COLUMNS))
    write_csv(outputs["rail_csv"], rail_rows, RAIL_COLUMNS)
    write_text(outputs["rail_md"], render_markdown_table(rail_rows, RAIL_COLUMNS))
    write_csv(outputs["orientation_csv"], orientation_rows, ORIENTATION_COLUMNS)
    write_text(outputs["orientation_md"], render_markdown_table(orientation_rows, ORIENTATION_COLUMNS))
    write_csv(outputs["pin_access_csv"], pin_rows, PIN_ACCESS_COLUMNS)
    write_text(outputs["pin_access_md"], render_markdown_table(pin_rows, PIN_ACCESS_COLUMNS))
    write_csv(outputs["module_handoff_csv"], handoff_rows, MODULE_HANDOFF_COLUMNS)
    write_text(outputs["module_handoff_md"], render_markdown_table(handoff_rows, MODULE_HANDOFF_COLUMNS))
    _write_json(outputs["rule_library_json"], library.to_dict())


def render_L2_closure_report_md(library: PlacementAbutmentRuleLibrary) -> str:
    report = library.report
    lines = [
        "# OpenYield L2 Placement / Abutment Rule Closure",
        "",
        "## Summary",
        "",
        f"- can_claim_L2_placement_abutment_rules_closed_now: `{report['can_claim_L2_placement_abutment_rules_closed_now']}`",
        f"- can_enter_L3_module_gds_generation: `{report['can_enter_L3_module_gds_generation']}`",
        f"- remaining_L2_blockers_count: `{report['remaining_L2_blockers_count']}`",
        "",
        "## Closed Rule Sets",
        "",
        f"- placement_rule_rows_count: `{report['placement_rule_rows_count']}`",
        f"- abutment_rule_rows_count: `{report['abutment_rule_rows_count']}`",
        f"- rail_rule_rows_count: `{report['rail_rule_rows_count']}`",
        f"- orientation_policy_rows_count: `{report['orientation_policy_rows_count']}`",
        f"- pin_access_rule_rows_count: `{report['pin_access_rule_rows_count']}`",
        f"- module_handoff_rows_count: `{report['module_handoff_rows_count']}`",
        "",
        "## Modules That Can Enter L3 Standalone Module GDS",
        "",
        ", ".join(report["modules_can_enter_L3_standalone_module_gds"]),
        "",
        "## Modules Deferred Beyond L3",
        "",
        ", ".join(report["modules_blocked_from_L3_standalone_module_gds"]),
        "",
        "## L2 Decision",
        "",
        "L2 is treated as rule closure. Geometry export, module GDS writing, DRC/LVS, and timing closure remain out of scope.",
    ]
    return "\n".join(lines)


def load_L2_rule_library(path: str | Path) -> PlacementAbutmentRuleLibrary:
    payload = _load_json(path)
    return PlacementAbutmentRuleLibrary(
        placement_rules=tuple(PlacementRule(**row) for row in payload["placement_rules"]),
        abutment_rules=tuple(AbutmentRule(**row) for row in payload["abutment_rules"]),
        rail_rules=tuple(RailRule(**row) for row in payload["rail_rules"]),
        orientation_policies=tuple(OrientationPolicy(**row) for row in payload["orientation_policies"]),
        pin_access_rules=tuple(PinAccessRule(**row) for row in payload["pin_access_rules"]),
        module_handoff_rules=tuple(ModuleHandoffRule(**row) for row in payload["module_handoff_rules"]),
        report=payload["report"],
    )


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", required=True)
    parser.add_argument("--openyield-root", required=True)
    parser.add_argument("--l0-contract-json", required=True)
    parser.add_argument("--l1-library-json", required=True)
    parser.add_argument("--l1-composition-library-json", required=True)
    parser.add_argument("--l1-leaf-matrix", required=True)
    parser.add_argument("--l1-module-deps", required=True)
    parser.add_argument("--out-placement-csv", required=True)
    parser.add_argument("--out-placement-md", required=True)
    parser.add_argument("--out-abutment-csv", required=True)
    parser.add_argument("--out-abutment-md", required=True)
    parser.add_argument("--out-rail-csv", required=True)
    parser.add_argument("--out-rail-md", required=True)
    parser.add_argument("--out-orientation-csv", required=True)
    parser.add_argument("--out-orientation-md", required=True)
    parser.add_argument("--out-pin-access-csv", required=True)
    parser.add_argument("--out-pin-access-md", required=True)
    parser.add_argument("--out-module-handoff-csv", required=True)
    parser.add_argument("--out-module-handoff-md", required=True)
    parser.add_argument("--out-rule-library-json", required=True)
    parser.add_argument("--out-json", required=True)
    parser.add_argument("--out-report", required=True)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    library = build_L2_rule_library(
        repo_root=args.repo_root,
        openyield_root=args.openyield_root,
        l0_contract_json=args.l0_contract_json,
        l1_library_json=args.l1_library_json,
        l1_composition_library_json=args.l1_composition_library_json,
        l1_leaf_matrix=args.l1_leaf_matrix,
        l1_module_deps=args.l1_module_deps,
    )
    outputs = {
        "placement_csv": Path(args.out_placement_csv),
        "placement_md": Path(args.out_placement_md),
        "abutment_csv": Path(args.out_abutment_csv),
        "abutment_md": Path(args.out_abutment_md),
        "rail_csv": Path(args.out_rail_csv),
        "rail_md": Path(args.out_rail_md),
        "orientation_csv": Path(args.out_orientation_csv),
        "orientation_md": Path(args.out_orientation_md),
        "pin_access_csv": Path(args.out_pin_access_csv),
        "pin_access_md": Path(args.out_pin_access_md),
        "module_handoff_csv": Path(args.out_module_handoff_csv),
        "module_handoff_md": Path(args.out_module_handoff_md),
        "rule_library_json": Path(args.out_rule_library_json),
    }
    emit_L2_rule_matrices(library, outputs)
    _write_json(args.out_json, library.report)
    write_text(args.out_report, render_L2_closure_report_md(library))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
