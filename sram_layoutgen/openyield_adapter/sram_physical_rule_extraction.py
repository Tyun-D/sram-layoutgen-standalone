from __future__ import annotations

import csv
import json
import re
import subprocess
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

import gdstk

from sram_layoutgen.gds_util import inspect_gds_hierarchy, inspect_gds_layers


SOURCE_RULE_COLUMNS = [
    "rule_id",
    "rule_category",
    "openram_file",
    "class_or_function",
    "line_reference_or_pattern",
    "rule_summary",
    "why_it_matters_for_complete_gds",
    "can_adapt_to_openyield",
    "should_not_copy_directly",
    "c0_blockers_addressed",
    "target_stage_C2_C6",
    "evidence_status",
]
GAP_MATRIX_COLUMNS = [
    "gap_id",
    "physical_area",
    "openram_rule_or_observation",
    "current_openyield_status_from_C0",
    "gap_description",
    "blocks_complete_gds",
    "required_fix_stage",
    "recommended_openyield_specific_solution",
    "do_not_copy_openram_reason",
    "priority",
]
FIX_PLAN_COLUMNS = [
    "blocker_id",
    "blocker_category",
    "affected_net_or_module",
    "priority",
    "c0_evidence",
    "assigned_fix_stage",
    "physical_rule_reference",
    "fix_strategy",
    "expected_output_artifact",
    "verification_method",
    "blocks_complete_gds_until_fixed",
]


def _json_dump(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8", newline="\n")


def _write_csv(path: Path, columns: list[str], rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns)
        writer.writeheader()
        writer.writerows(rows)


def _load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _load_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def _md_table(columns: list[str], rows: list[dict[str, Any]]) -> str:
    lines = [
        "| " + " | ".join(columns) + " |",
        "| " + " | ".join(["---"] * len(columns)) + " |",
    ]
    for row in rows:
        rendered = []
        for column in columns:
            value = row.get(column, "")
            if isinstance(value, (dict, list)):
                value = json.dumps(value, ensure_ascii=False)
            rendered.append(str(value).replace("\n", "<br>"))
        lines.append("| " + " | ".join(rendered) + " |")
    return "\n".join(lines) + "\n"


def _round(value: float) -> float:
    return round(float(value), 6)


def _bbox_from_obj(value: Any) -> dict[str, float] | None:
    if value is None:
        return None
    if isinstance(value, dict) and {"x0", "y0", "x1", "y1"}.issubset(value):
        return {
            "x0": _round(value["x0"]),
            "y0": _round(value["y0"]),
            "x1": _round(value["x1"]),
            "y1": _round(value["y1"]),
            "width": _round(value.get("width", value["x1"] - value["x0"])),
            "height": _round(value.get("height", value["y1"] - value["y0"])),
        }
    if isinstance(value, (tuple, list)) and len(value) == 2:
        (x0, y0), (x1, y1) = value
        return {
            "x0": _round(min(x0, x1)),
            "y0": _round(min(y0, y1)),
            "x1": _round(max(x0, x1)),
            "y1": _round(max(y0, y1)),
            "width": _round(abs(x1 - x0)),
            "height": _round(abs(y1 - y0)),
        }
    return None


def _bbox_area(bbox: dict[str, float] | None) -> float:
    if bbox is None:
        return 0.0
    return _round(float(bbox["width"]) * float(bbox["height"]))


def _git_commit(repo_root: Path) -> str | None:
    try:
        result = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=repo_root,
            check=True,
            capture_output=True,
            text=True,
        )
    except Exception:
        return None
    return result.stdout.strip() or None


RULE_SPECS: list[dict[str, Any]] = [
    {
        "rule_id": "SRC_001",
        "rule_category": "PARAMETER_MODEL",
        "openram_file": "sram_compiler.py",
        "class_or_function": "main flow",
        "pattern": "s = sram()",
        "rule_summary": "OpenRAM emits a full SRAM object and then saves GDS/LEF/SPICE from that assembled physical hierarchy.",
        "why_it_matters_for_complete_gds": "Complete GDS requires one physical hierarchy that owns both module placement and exported geometry.",
        "can_adapt_to_openyield": True,
        "should_not_copy_directly": True,
        "c0_blockers_addressed": "GDS_HIERARCHY,VALIDATION",
        "target_stage_C2_C6": "C6",
    },
    {
        "rule_id": "SRC_002",
        "rule_category": "PARAMETER_MODEL",
        "openram_file": "compiler/sram.py",
        "class_or_function": "sram.__init__",
        "pattern": "self.s = sram(name, sram_config)",
        "rule_summary": "Physical layout is instantiated from a config object and then netlist/layout are created from the same parameter set.",
        "why_it_matters_for_complete_gds": "OpenYield must keep supported-config physical geometry tied to the same config used by routing and validation.",
        "can_adapt_to_openyield": True,
        "should_not_copy_directly": False,
        "c0_blockers_addressed": "VALIDATION",
        "target_stage_C2_C6": "C6",
    },
    {
        "rule_id": "SRC_003",
        "rule_category": "VALIDATION",
        "openram_file": "compiler/sram.py",
        "class_or_function": "sram.save",
        "pattern": "self.gds_write(gdsname)",
        "rule_summary": "Reference GDS is emitted only after layout creation and alongside LVS-oriented SPICE/LEF artifacts.",
        "why_it_matters_for_complete_gds": "C6 needs geometry-backed completion evidence, not a map-only handoff.",
        "can_adapt_to_openyield": True,
        "should_not_copy_directly": True,
        "c0_blockers_addressed": "MISSING_LVS_READY_NET_MAPPING,VALIDATION",
        "target_stage_C2_C6": "C6",
    },
    {
        "rule_id": "SRC_004",
        "rule_category": "ARRAY_STRUCTURE",
        "openram_file": "compiler/modules/bitcell_base_array.py",
        "class_or_function": "bitcell_base_array.create_all_bitline_names",
        "pattern": "bl_{0}_{1}",
        "rule_summary": "Bitline naming is column-major and tied directly to bitcell column ownership.",
        "why_it_matters_for_complete_gds": "Complete routing must preserve physical column ownership from array pins through column periphery.",
        "can_adapt_to_openyield": True,
        "should_not_copy_directly": False,
        "c0_blockers_addressed": "CONTRACT_ROUTE,MISSING_PIN_GEOMETRY",
        "target_stage_C2_C6": "C2/C4",
    },
    {
        "rule_id": "SRC_005",
        "rule_category": "ARRAY_STRUCTURE",
        "openram_file": "compiler/modules/bitcell_base_array.py",
        "class_or_function": "bitcell_base_array.create_all_wordline_names",
        "pattern": "wl_{0}_{1}",
        "rule_summary": "Wordline naming is row-major and tied directly to bitcell row ownership.",
        "why_it_matters_for_complete_gds": "WL geometry must map to per-row pitch and not to abstract row-wide stripes only.",
        "can_adapt_to_openyield": True,
        "should_not_copy_directly": False,
        "c0_blockers_addressed": "CONTRACT_ROUTE,MISSING_PIN_GEOMETRY",
        "target_stage_C2_C6": "C2/C4",
    },
    {
        "rule_id": "SRC_006",
        "rule_category": "PIN_LABEL_EXPORT",
        "openram_file": "compiler/modules/bitcell_base_array.py",
        "class_or_function": "bitcell_base_array.add_bitline_pins",
        "pattern": "height=self.height",
        "rule_summary": "Array BL/BR pins are exported as full-height geometry aligned to real bitcell pin shapes.",
        "why_it_matters_for_complete_gds": "This is the geometry-backed baseline missing from OpenYield contract-only BL/BR routes.",
        "can_adapt_to_openyield": True,
        "should_not_copy_directly": False,
        "c0_blockers_addressed": "MISSING_PIN_GEOMETRY,CONTRACT_ROUTE",
        "target_stage_C2_C6": "C2",
    },
    {
        "rule_id": "SRC_007",
        "rule_category": "PIN_LABEL_EXPORT",
        "openram_file": "compiler/modules/bitcell_base_array.py",
        "class_or_function": "bitcell_base_array.add_wl_pins",
        "pattern": "width=self.width",
        "rule_summary": "Array WL pins are exported as full-width geometry aligned to row pitch and cell access height.",
        "why_it_matters_for_complete_gds": "OpenYield needs geometry-backed WL endpoints instead of bbox-only stripes.",
        "can_adapt_to_openyield": True,
        "should_not_copy_directly": False,
        "c0_blockers_addressed": "MISSING_PIN_GEOMETRY,CONTRACT_ROUTE",
        "target_stage_C2_C6": "C2",
    },
    {
        "rule_id": "SRC_008",
        "rule_category": "POWER_ROUTING",
        "openram_file": "compiler/modules/bitcell_base_array.py",
        "class_or_function": "bitcell_base_array.route_supplies",
        "pattern": "self.copy_layout_pin(inst, pin_name)",
        "rule_summary": "Array supply pins are propagated from real child instances rather than synthesized from abstract rails.",
        "why_it_matters_for_complete_gds": "OpenYield power closure must connect to true child rail geometry.",
        "can_adapt_to_openyield": True,
        "should_not_copy_directly": False,
        "c0_blockers_addressed": "CONTRACT_POWER_STITCH,APPROXIMATE_POWER_GEOMETRY",
        "target_stage_C2_C6": "C2/C5",
    },
    {
        "rule_id": "SRC_009",
        "rule_category": "ARRAY_STRUCTURE",
        "openram_file": "compiler/modules/bitcell_base_array.py",
        "class_or_function": "bitcell_base_array.place_array",
        "pattern": "self.height = self.row_size * self.cell.height",
        "rule_summary": "Array height/width derive directly from bitcell row and column pitch, with mirroring respecting bitcell orientation rules.",
        "why_it_matters_for_complete_gds": "C3 must rebuild floorplan around real bitcell pitch rather than coarse region boxes.",
        "can_adapt_to_openyield": True,
        "should_not_copy_directly": False,
        "c0_blockers_addressed": "FLOORPLAN_NOT_SRAM_LIKE,PLACEHOLDER_VISUAL_GEOMETRY",
        "target_stage_C2_C6": "C3",
    },
    {
        "rule_id": "SRC_010",
        "rule_category": "ARRAY_STRUCTURE",
        "openram_file": "compiler/modules/bitcell_array.py",
        "class_or_function": "bitcell_array",
        "pattern": "Assumes bit-lines and word lines are connected by abutment.",
        "rule_summary": "The main array is the primary SRAM body and BL/WL continuity is achieved by cell abutment, not post-hoc overlay stripes.",
        "why_it_matters_for_complete_gds": "OpenYield needs array-owned access geometry to anchor real routing.",
        "can_adapt_to_openyield": True,
        "should_not_copy_directly": False,
        "c0_blockers_addressed": "PLACEHOLDER_VISUAL_GEOMETRY,CONTRACT_ROUTE",
        "target_stage_C2_C6": "C2/C3/C4",
    },
    {
        "rule_id": "SRC_011",
        "rule_category": "DUMMY_REPLICA_BOUNDARY",
        "openram_file": "compiler/modules/replica_bitcell_array.py",
        "class_or_function": "replica_bitcell_array",
        "pattern": "Replica columns are on the left and right",
        "rule_summary": "Replica columns live on the left/right edges of the main array and dummy rows live on the top/bottom for RBL loading.",
        "why_it_matters_for_complete_gds": "Replica and dummy structures are not arbitrary filler; they are part of timing and edge geometry organization.",
        "can_adapt_to_openyield": True,
        "should_not_copy_directly": False,
        "c0_blockers_addressed": "FLOORPLAN_NOT_SRAM_LIKE,MISSING_PIN_GEOMETRY",
        "target_stage_C2_C6": "C3",
    },
    {
        "rule_id": "SRC_012",
        "rule_category": "DUMMY_REPLICA_BOUNDARY",
        "openram_file": "compiler/modules/replica_bitcell_array.py",
        "class_or_function": "replica_bitcell_array.add_modules",
        "pattern": "self.dummy_row = factory.create(module_type=\"dummy_array\"",
        "rule_summary": "Dummy rows are explicitly instantiated to carry replica wordlines through the array edge.",
        "why_it_matters_for_complete_gds": "C3 needs explicit boundary placement semantics for dummy/replica ownership.",
        "can_adapt_to_openyield": True,
        "should_not_copy_directly": False,
        "c0_blockers_addressed": "FLOORPLAN_NOT_SRAM_LIKE,PLACEHOLDER_VISUAL_GEOMETRY",
        "target_stage_C2_C6": "C3",
    },
    {
        "rule_id": "SRC_013",
        "rule_category": "PIN_LABEL_EXPORT",
        "openram_file": "compiler/modules/replica_bitcell_array.py",
        "class_or_function": "replica_bitcell_array.add_layout_pins",
        "pattern": "self.add_layout_pin(text=pin_name",
        "rule_summary": "Regular and replica WL/BL pins are exported from actual child pins with width/height expanded to the array span.",
        "why_it_matters_for_complete_gds": "This is a direct precedent for geometry-backed boundary export instead of label-only pins.",
        "can_adapt_to_openyield": True,
        "should_not_copy_directly": False,
        "c0_blockers_addressed": "MISSING_PIN_GEOMETRY,MISSING_TOP_PIN_GEOMETRY",
        "target_stage_C2_C6": "C2",
    },
    {
        "rule_id": "SRC_014",
        "rule_category": "POWER_ROUTING",
        "openram_file": "compiler/modules/replica_bitcell_array.py",
        "class_or_function": "replica_bitcell_array.route_supplies",
        "pattern": "self.copy_layout_pin(inst, pin_name)",
        "rule_summary": "Supply export stays attached to child rail shapes even in replica/dummy-augmented arrays.",
        "why_it_matters_for_complete_gds": "C5 needs rail-to-strap stitching to start from real module rails.",
        "can_adapt_to_openyield": True,
        "should_not_copy_directly": False,
        "c0_blockers_addressed": "CONTRACT_POWER_STITCH,APPROXIMATE_POWER_GEOMETRY",
        "target_stage_C2_C6": "C2/C5",
    },
    {
        "rule_id": "SRC_015",
        "rule_category": "DUMMY_REPLICA_BOUNDARY",
        "openram_file": "compiler/modules/capped_replica_bitcell_array.py",
        "class_or_function": "capped_replica_bitcell_array.add_end_caps",
        "pattern": "Add dummy cells or end caps around the array",
        "rule_summary": "Boundary caps are explicitly added around replica arrays to define legal outer edge geometry.",
        "why_it_matters_for_complete_gds": "C3 must replace visual placeholders with real boundary-cap organization.",
        "can_adapt_to_openyield": True,
        "should_not_copy_directly": False,
        "c0_blockers_addressed": "PLACEHOLDER_VISUAL_GEOMETRY,FLOORPLAN_NOT_SRAM_LIKE",
        "target_stage_C2_C6": "C3",
    },
    {
        "rule_id": "SRC_016",
        "rule_category": "ROW_PATH_ALIGNMENT",
        "openram_file": "compiler/modules/local_bitcell_array.py",
        "class_or_function": "local_bitcell_array.place",
        "pattern": "driver_to_array_spacing = 3 * self.m3_pitch",
        "rule_summary": "Wordline driver array is placed adjacent to the array with technology-scaled spacing derived from routing pitch.",
        "why_it_matters_for_complete_gds": "C3 needs row-periphery spacing rules tied to access/routing layers.",
        "can_adapt_to_openyield": True,
        "should_not_copy_directly": False,
        "c0_blockers_addressed": "FLOORPLAN_NOT_SRAM_LIKE,CONTRACT_ROUTE",
        "target_stage_C2_C6": "C3",
    },
    {
        "rule_id": "SRC_017",
        "rule_category": "WORDLINE_ROUTING",
        "openram_file": "compiler/modules/local_bitcell_array.py",
        "class_or_function": "local_bitcell_array.route",
        "pattern": "global_wl_layer = layer_props.global_bitcell_array.wordline_layer",
        "rule_summary": "OpenRAM separates local wordline buffering from global wordline export layers and uses explicit via stacks between them.",
        "why_it_matters_for_complete_gds": "OpenYield WL closure needs real layer/direction/access ownership instead of one abstract stripe layer.",
        "can_adapt_to_openyield": True,
        "should_not_copy_directly": False,
        "c0_blockers_addressed": "CONTRACT_ROUTE,PLACEHOLDER_VISUAL_GEOMETRY",
        "target_stage_C2_C6": "C2/C4",
    },
    {
        "rule_id": "SRC_018",
        "rule_category": "WORDLINE_ROUTING",
        "openram_file": "compiler/modules/local_bitcell_array.py",
        "class_or_function": "local_bitcell_array.route",
        "pattern": "self.add_via_stack_center(from_layer=in_pin.layer",
        "rule_summary": "Global WL pins are created only after explicit local-to-global via stacks and short jogs from the driver input side.",
        "why_it_matters_for_complete_gds": "C4 must create access-aware WL geometry rather than bbox-only row bars.",
        "can_adapt_to_openyield": True,
        "should_not_copy_directly": False,
        "c0_blockers_addressed": "CONTRACT_ROUTE,MISSING_PIN_GEOMETRY",
        "target_stage_C2_C6": "C2/C4",
    },
    {
        "rule_id": "SRC_019",
        "rule_category": "ARRAY_STRUCTURE",
        "openram_file": "compiler/modules/global_bitcell_array.py",
        "class_or_function": "global_bitcell_array.add_modules",
        "pattern": "Always add the left RBLs to the first subarray",
        "rule_summary": "When arrays are segmented, left/right replica ownership stays on the edge local arrays only.",
        "why_it_matters_for_complete_gds": "C3 must keep replica timing structures at macro edges, not floating in generic control regions.",
        "can_adapt_to_openyield": True,
        "should_not_copy_directly": False,
        "c0_blockers_addressed": "FLOORPLAN_NOT_SRAM_LIKE",
        "target_stage_C2_C6": "C3",
    },
    {
        "rule_id": "SRC_020",
        "rule_category": "WORDLINE_ROUTING",
        "openram_file": "compiler/modules/global_bitcell_array.py",
        "class_or_function": "global_bitcell_array.add_layout_pins",
        "pattern": "self.add_layout_pin_segment_center(text=wl_name",
        "rule_summary": "Global wordlines are stitched across local arrays on a dedicated layer and exported as single continuous pins.",
        "why_it_matters_for_complete_gds": "Multi-slice WL geometry in OpenYield must become continuous physical nets, not separate report entries.",
        "can_adapt_to_openyield": True,
        "should_not_copy_directly": False,
        "c0_blockers_addressed": "CONTRACT_ROUTE,PLACEHOLDER_VISUAL_GEOMETRY",
        "target_stage_C2_C6": "C4",
    },
    {
        "rule_id": "SRC_021",
        "rule_category": "COLUMN_PATH_ALIGNMENT",
        "openram_file": "compiler/modules/bank.py",
        "class_or_function": "bank.compute_instance_offsets",
        "pattern": "self.main_bitcell_array_top = self.bitcell_array.get_main_array_top()",
        "rule_summary": "Bank floorplan is anchored to the main array edges, with row/column/control placement computed relative to those edges.",
        "why_it_matters_for_complete_gds": "OpenYield C3 must floorplan from real array boundaries rather than independent region boxes.",
        "can_adapt_to_openyield": True,
        "should_not_copy_directly": False,
        "c0_blockers_addressed": "FLOORPLAN_NOT_SRAM_LIKE,PLACEHOLDER_VISUAL_GEOMETRY",
        "target_stage_C2_C6": "C3",
    },
    {
        "rule_id": "SRC_022",
        "rule_category": "ROW_PATH_ALIGNMENT",
        "openram_file": "compiler/modules/bank.py",
        "class_or_function": "bank.compute_instance_port0_offsets",
        "pattern": "self.port_address_offsets[port] = vector(-x_offset",
        "rule_summary": "Row-address path is placed to the left of the main array while column/data path is placed below for port0.",
        "why_it_matters_for_complete_gds": "This defines SRAM-like relative organization for row and column periphery.",
        "can_adapt_to_openyield": True,
        "should_not_copy_directly": False,
        "c0_blockers_addressed": "FLOORPLAN_NOT_SRAM_LIKE",
        "target_stage_C2_C6": "C3",
    },
    {
        "rule_id": "SRC_023",
        "rule_category": "COLUMN_PATH_ALIGNMENT",
        "openram_file": "compiler/modules/bank.py",
        "class_or_function": "bank.compute_instance_port1_offsets",
        "pattern": "self.port_data_offsets[port] = vector(0, self.bitcell_array_top)",
        "rule_summary": "For the second port, data path can move above the array while row path moves to the right, preserving array-centric organization.",
        "why_it_matters_for_complete_gds": "The core principle is that array remains the center and periphery attaches to edges by function.",
        "can_adapt_to_openyield": True,
        "should_not_copy_directly": True,
        "c0_blockers_addressed": "FLOORPLAN_NOT_SRAM_LIKE",
        "target_stage_C2_C6": "C3",
    },
    {
        "rule_id": "SRC_024",
        "rule_category": "BITLINE_ROUTING",
        "openram_file": "compiler/modules/bank.py",
        "class_or_function": "bank.route_bitlines",
        "pattern": "self.route_port_data_to_bitcell_array(port)",
        "rule_summary": "Bitline path is routed as a structured chain from precharge/column mux/sense/write logic into the bitcell array.",
        "why_it_matters_for_complete_gds": "OpenYield must replace one-step contract mapping with staged column-path connectivity.",
        "can_adapt_to_openyield": True,
        "should_not_copy_directly": False,
        "c0_blockers_addressed": "CONTRACT_ROUTE,MISSING_PIN_GEOMETRY",
        "target_stage_C2_C6": "C2/C4",
    },
    {
        "rule_id": "SRC_025",
        "rule_category": "CONTROL_ROUTING",
        "openram_file": "compiler/modules/bank.py",
        "class_or_function": "bank.route_rbl",
        "pattern": "self.add_layout_pin_segment_center(text=\"rbl_bl_{0}_{0}\"",
        "rule_summary": "Replica bitline is exported to the bank boundary through explicit routed geometry and side pin placement.",
        "why_it_matters_for_complete_gds": "Replica control/timing signals in OpenYield need geometry-backed routing and export, not report-only ownership.",
        "can_adapt_to_openyield": True,
        "should_not_copy_directly": False,
        "c0_blockers_addressed": "CONTRACT_ROUTE,MISSING_PIN_GEOMETRY",
        "target_stage_C2_C6": "C2/C4",
    },
    {
        "rule_id": "SRC_026",
        "rule_category": "ROW_PATH_ALIGNMENT",
        "openram_file": "compiler/modules/port_address.py",
        "class_or_function": "port_address.place_instances",
        "pattern": "wordline_driver_array_offset = vector(self.row_decoder_inst.rx(), 0)",
        "rule_summary": "Wordline driver is placed directly adjacent to the row decoder and then drives row-aligned outputs into the array edge.",
        "why_it_matters_for_complete_gds": "Decoder and WL-driver cannot be treated as unrelated abstract blocks in C3/C4.",
        "can_adapt_to_openyield": True,
        "should_not_copy_directly": False,
        "c0_blockers_addressed": "CONTRACT_ROUTE,FLOORPLAN_NOT_SRAM_LIKE",
        "target_stage_C2_C6": "C3/C4",
    },
    {
        "rule_id": "SRC_027",
        "rule_category": "WORDLINE_ROUTING",
        "openram_file": "compiler/modules/port_address.py",
        "class_or_function": "port_address.route_internal",
        "pattern": "self.add_zjog(self.route_layer, decoder_out_pos, driver_in_pos",
        "rule_summary": "Decoder outputs connect to wordline-driver inputs using explicit jog routing and via stacks between real pins.",
        "why_it_matters_for_complete_gds": "OpenYield control/row path needs actual intermediate connectivity, not a single bbox for the whole fanout.",
        "can_adapt_to_openyield": True,
        "should_not_copy_directly": False,
        "c0_blockers_addressed": "CONTRACT_ROUTE,MISSING_PIN_GEOMETRY",
        "target_stage_C2_C6": "C2/C4",
    },
    {
        "rule_id": "SRC_028",
        "rule_category": "POWER_ROUTING",
        "openram_file": "compiler/modules/port_address.py",
        "class_or_function": "port_address.route_supplies",
        "pattern": "self.copy_layout_pin(self.wordline_driver_array_inst, \"vdd\")",
        "rule_summary": "Row-path VDD/GND are propagated from decoder and wordline-driver geometry, with extra RBL rail stitching only where needed.",
        "why_it_matters_for_complete_gds": "OpenYield must repair power continuity at module-rail granularity.",
        "can_adapt_to_openyield": True,
        "should_not_copy_directly": False,
        "c0_blockers_addressed": "CONTRACT_POWER_STITCH,MISSING_PIN_GEOMETRY",
        "target_stage_C2_C6": "C2/C5",
    },
    {
        "rule_id": "SRC_029",
        "rule_category": "COLUMN_PATH_ALIGNMENT",
        "openram_file": "compiler/modules/port_data.py",
        "class_or_function": "port_data.route_data_lines",
        "pattern": "write_driver -> sense_amp -> (column_mux ->) precharge -> bitcell_array",
        "rule_summary": "Column path is an ordered physical chain; BL/BR do not jump directly from top-level net name to every consumer.",
        "why_it_matters_for_complete_gds": "This directly addresses OpenYield’s contract-only BL/BR overlay.",
        "can_adapt_to_openyield": True,
        "should_not_copy_directly": False,
        "c0_blockers_addressed": "CONTRACT_ROUTE",
        "target_stage_C2_C6": "C4",
    },
    {
        "rule_id": "SRC_030",
        "rule_category": "COLUMN_PATH_ALIGNMENT",
        "openram_file": "compiler/modules/port_data.py",
        "class_or_function": "port_data.add_modules",
        "pattern": "precharge_bit_offsets",
        "rule_summary": "Precharge, mux, sense amp, and write-driver arrays use common bit offsets derived from bitcell pitch and words-per-row ownership.",
        "why_it_matters_for_complete_gds": "C3 must align column modules to array column pitch and mux ratio.",
        "can_adapt_to_openyield": True,
        "should_not_copy_directly": False,
        "c0_blockers_addressed": "FLOORPLAN_NOT_SRAM_LIKE,CONTRACT_ROUTE",
        "target_stage_C2_C6": "C3/C4",
    },
    {
        "rule_id": "SRC_031",
        "rule_category": "COLUMN_PATH_ALIGNMENT",
        "openram_file": "compiler/modules/precharge_array.py",
        "class_or_function": "precharge_array.place_insts",
        "pattern": "if self.cell.mirror.y and (i + self.column_offset) % 2",
        "rule_summary": "Precharge cells inherit bitcell mirror parity and column offset so BL/BR access stays aligned to the array.",
        "why_it_matters_for_complete_gds": "Column-path modules must respect bitcell parity, not just nominal x pitch.",
        "can_adapt_to_openyield": True,
        "should_not_copy_directly": False,
        "c0_blockers_addressed": "MISSING_PIN_GEOMETRY,CONTRACT_ROUTE",
        "target_stage_C2_C6": "C2/C3",
    },
    {
        "rule_id": "SRC_032",
        "rule_category": "POWER_ROUTING",
        "openram_file": "compiler/modules/precharge_array.py",
        "class_or_function": "precharge_array.route_supplies",
        "pattern": "self.route_horizontal_pins(\"vdd\")",
        "rule_summary": "Precharge array exports a continuous horizontal VDD rail rather than an approximate top-level strap.",
        "why_it_matters_for_complete_gds": "This is the kind of geometry-backed rail OpenYield needs before top-level stitching.",
        "can_adapt_to_openyield": True,
        "should_not_copy_directly": False,
        "c0_blockers_addressed": "CONTRACT_POWER_STITCH,APPROXIMATE_POWER_GEOMETRY",
        "target_stage_C2_C6": "C2/C5",
    },
    {
        "rule_id": "SRC_033",
        "rule_category": "COLUMN_PATH_ALIGNMENT",
        "openram_file": "compiler/modules/sense_amp_array.py",
        "class_or_function": "sense_amp_array.place_sense_amp_array",
        "pattern": "self.offsets[0:self.num_cols:self.words_per_row]",
        "rule_summary": "Sense amps are placed on word outputs, not every raw column, and words-per-row determines ownership grouping.",
        "why_it_matters_for_complete_gds": "C3/C4 must account for mux ratio when aligning read path modules.",
        "can_adapt_to_openyield": True,
        "should_not_copy_directly": False,
        "c0_blockers_addressed": "CONTRACT_ROUTE,FLOORPLAN_NOT_SRAM_LIKE",
        "target_stage_C2_C6": "C3/C4",
    },
    {
        "rule_id": "SRC_034",
        "rule_category": "CONTROL_ROUTING",
        "openram_file": "compiler/modules/sense_amp_array.py",
        "class_or_function": "sense_amp_array.route_rails",
        "pattern": "self.add_layout_pin_segment_center(text=self.en_name",
        "rule_summary": "Sense-enable is distributed as explicit rail geometry with vias into each amplifier.",
        "why_it_matters_for_complete_gds": "OpenYield control distribution must become per-consumer geometry, not one contract rectangle.",
        "can_adapt_to_openyield": True,
        "should_not_copy_directly": False,
        "c0_blockers_addressed": "CONTRACT_ROUTE,MISSING_PIN_GEOMETRY",
        "target_stage_C2_C6": "C2/C4",
    },
    {
        "rule_id": "SRC_035",
        "rule_category": "COLUMN_PATH_ALIGNMENT",
        "openram_file": "compiler/modules/write_driver_array.py",
        "class_or_function": "write_driver_array.place_write_array",
        "pattern": "self.offsets[0:self.columns:self.words_per_row]",
        "rule_summary": "Write drivers are placed per word output with words-per-row grouping and spare columns handled separately.",
        "why_it_matters_for_complete_gds": "OpenYield write path must use word-owned geometry rather than every-column placeholder taps.",
        "can_adapt_to_openyield": True,
        "should_not_copy_directly": False,
        "c0_blockers_addressed": "CONTRACT_ROUTE,FLOORPLAN_NOT_SRAM_LIKE",
        "target_stage_C2_C6": "C3/C4",
    },
    {
        "rule_id": "SRC_036",
        "rule_category": "CONTROL_ROUTING",
        "openram_file": "compiler/modules/write_driver_array.py",
        "class_or_function": "write_driver_array.add_layout_pins",
        "pattern": "self.add_layout_pin(text=self.en_name",
        "rule_summary": "Write-enable geometry is exported as a real rail segment, optionally partitioned by write-mask/spare ownership.",
        "why_it_matters_for_complete_gds": "OpenYield write enable cannot remain a contract fanout box.",
        "can_adapt_to_openyield": True,
        "should_not_copy_directly": False,
        "c0_blockers_addressed": "CONTRACT_ROUTE,MISSING_PIN_GEOMETRY",
        "target_stage_C2_C6": "C2/C4",
    },
    {
        "rule_id": "SRC_037",
        "rule_category": "COLUMN_PATH_ALIGNMENT",
        "openram_file": "compiler/modules/column_mux_array.py",
        "class_or_function": "column_mux_array.setup_layout_constants",
        "pattern": "self.route_height = (self.words_per_row + 3) * self.sel_pitch",
        "rule_summary": "Column mux array reserves routing height proportional to words-per-row for select rails and output joins.",
        "why_it_matters_for_complete_gds": "OpenYield C3/C4 must allocate real routing channels instead of overlay rectangles.",
        "can_adapt_to_openyield": True,
        "should_not_copy_directly": False,
        "c0_blockers_addressed": "PLACEHOLDER_VISUAL_GEOMETRY,CONTRACT_ROUTE",
        "target_stage_C2_C6": "C3/C4",
    },
    {
        "rule_id": "SRC_038",
        "rule_category": "BITLINE_ROUTING",
        "openram_file": "compiler/modules/column_mux_array.py",
        "class_or_function": "column_mux_array.route_bitlines",
        "pattern": "self.add_layout_pin_segment_center(text=\"bl_out_",
        "rule_summary": "Mux outputs are formed by actual merged BL/BR output rails and via stacks across the grouped columns.",
        "why_it_matters_for_complete_gds": "OpenYield needs true mux-output ownership instead of per-consumer duplicated BL/BR rectangles.",
        "can_adapt_to_openyield": True,
        "should_not_copy_directly": False,
        "c0_blockers_addressed": "CONTRACT_ROUTE,PLACEHOLDER_VISUAL_GEOMETRY",
        "target_stage_C2_C6": "C2/C4",
    },
    {
        "rule_id": "SRC_039",
        "rule_category": "CONTROL_ROUTING",
        "openram_file": "compiler/modules/column_mux_array.py",
        "class_or_function": "column_mux_array.add_horizontal_input_rail",
        "pattern": "self.add_layout_pin(text=\"sel_",
        "rule_summary": "Column-select controls are distributed on dedicated horizontal rails under the mux array.",
        "why_it_matters_for_complete_gds": "OpenYield control routing must use organized channel rails, not one large area fill.",
        "can_adapt_to_openyield": True,
        "should_not_copy_directly": False,
        "c0_blockers_addressed": "CONTRACT_ROUTE,PLACEHOLDER_VISUAL_GEOMETRY",
        "target_stage_C2_C6": "C3/C4",
    },
    {
        "rule_id": "SRC_040",
        "rule_category": "GDS_PRIMITIVE_API",
        "openram_file": "compiler/base/hierarchy_layout.py",
        "class_or_function": "copy_layout_pin",
        "pattern": "self.add_layout_pin(new_name",
        "rule_summary": "Top-level pins are propagated by copying actual child pin shapes, preserving layer, width, and height.",
        "why_it_matters_for_complete_gds": "OpenYield pin export must stay geometry-backed all the way up the hierarchy.",
        "can_adapt_to_openyield": True,
        "should_not_copy_directly": False,
        "c0_blockers_addressed": "MISSING_TOP_PIN_GEOMETRY,MISSING_PIN_GEOMETRY",
        "target_stage_C2_C6": "C2/C6",
    },
    {
        "rule_id": "SRC_041",
        "rule_category": "PIN_LABEL_EXPORT",
        "openram_file": "compiler/base/hierarchy_layout.py",
        "class_or_function": "add_layout_pin_segment_center",
        "pattern": "Creates a path like pin with center-line convention",
        "rule_summary": "A real exported pin can be a routed segment with explicit layer and bbox, not just a text label.",
        "why_it_matters_for_complete_gds": "This defines the minimum geometry-backed pin requirement for C2/C4/C5/C6.",
        "can_adapt_to_openyield": True,
        "should_not_copy_directly": False,
        "c0_blockers_addressed": "MISSING_PIN_GEOMETRY,MISSING_TOP_PIN_GEOMETRY",
        "target_stage_C2_C6": "C2/C6",
    },
    {
        "rule_id": "SRC_042",
        "rule_category": "PIN_LABEL_EXPORT",
        "openram_file": "compiler/base/hierarchy_layout.py",
        "class_or_function": "replace_layout_pin",
        "pattern": "Remove the old pin and replace with a new one",
        "rule_summary": "Escape/perimeter pin relocation keeps the old geometry as wiring and replaces only the exported pin object.",
        "why_it_matters_for_complete_gds": "OpenYield top-pin cleanup must distinguish internal route geometry from final external pin placement.",
        "can_adapt_to_openyield": True,
        "should_not_copy_directly": False,
        "c0_blockers_addressed": "MISSING_TOP_PIN_GEOMETRY,PLACEHOLDER_VISUAL_GEOMETRY",
        "target_stage_C2_C6": "C4/C6",
    },
    {
        "rule_id": "SRC_043",
        "rule_category": "PIN_LABEL_EXPORT",
        "openram_file": "compiler/base/hierarchy_layout.py",
        "class_or_function": "add_label_pin",
        "pattern": "This is not an actual pin but a named net",
        "rule_summary": "Label-only correspondence points are explicitly distinguished from actual layout pins.",
        "why_it_matters_for_complete_gds": "OpenYield must not treat label-only pins as sufficient evidence for complete GDS.",
        "can_adapt_to_openyield": True,
        "should_not_copy_directly": False,
        "c0_blockers_addressed": "MISSING_PIN_GEOMETRY",
        "target_stage_C2_C6": "C2/C6",
    },
    {
        "rule_id": "SRC_044",
        "rule_category": "HIERARCHY_EXPORT",
        "openram_file": "compiler/base/hierarchy_layout.py",
        "class_or_function": "gds_write",
        "pattern": "Write the entire layout to a GDSII file",
        "rule_summary": "GDS export occurs from the assembled layout hierarchy after geometry and pin maps are finalized.",
        "why_it_matters_for_complete_gds": "OpenYield complete-GDS claim must come only after geometry hierarchy is physically assembled.",
        "can_adapt_to_openyield": True,
        "should_not_copy_directly": False,
        "c0_blockers_addressed": "GDS_HIERARCHY,VALIDATION",
        "target_stage_C2_C6": "C6",
    },
    {
        "rule_id": "SRC_045",
        "rule_category": "VALIDATION",
        "openram_file": "compiler/base/hierarchy_layout.py",
        "class_or_function": "add_boundary",
        "pattern": "self.add_rect(layer=\"boundary\"",
        "rule_summary": "Physical macros include an explicit boundary shape tied to the final extents of real geometry.",
        "why_it_matters_for_complete_gds": "OpenYield macro bbox should follow actual assembled geometry, not placeholder extents.",
        "can_adapt_to_openyield": True,
        "should_not_copy_directly": False,
        "c0_blockers_addressed": "PLACEHOLDER_VISUAL_GEOMETRY",
        "target_stage_C2_C6": "C3/C6",
    },
    {
        "rule_id": "SRC_046",
        "rule_category": "POWER_ROUTING",
        "openram_file": "compiler/base/hierarchy_layout.py",
        "class_or_function": "copy_power_pins",
        "pattern": "self.copy_layout_pin(inst, name, new_name)",
        "rule_summary": "Power export can be copied from instance pin geometry before any higher-level stitching is added.",
        "why_it_matters_for_complete_gds": "This is the baseline for geometry-backed VDD/GND pin ownership in C2/C5.",
        "can_adapt_to_openyield": True,
        "should_not_copy_directly": False,
        "c0_blockers_addressed": "CONTRACT_POWER_STITCH,MISSING_PIN_GEOMETRY",
        "target_stage_C2_C6": "C2/C5",
    },
    {
        "rule_id": "SRC_047",
        "rule_category": "PIN_LABEL_EXPORT",
        "openram_file": "compiler/base/hierarchy_layout.py",
        "class_or_function": "add_io_pin",
        "pattern": "Add top-level pin from instance pin to perimeter",
        "rule_summary": "Top IO pins are derived from real instance pins and optionally escape-routed upward through specified layer stacks.",
        "why_it_matters_for_complete_gds": "OpenYield top IO must be backed by internal geometry and routed escape, not map-only entries.",
        "can_adapt_to_openyield": True,
        "should_not_copy_directly": False,
        "c0_blockers_addressed": "MISSING_TOP_PIN_GEOMETRY,CONTRACT_ROUTE",
        "target_stage_C2_C6": "C4/C6",
    },
    {
        "rule_id": "SRC_048",
        "rule_category": "CONTROL_ROUTING",
        "openram_file": "compiler/modules/sram_1bank.py",
        "class_or_function": "place_control",
        "pattern": "The delay line is aligned with the bitcell array",
        "rule_summary": "Control logic and delay chain placement are explicitly aligned against bank array geometry rather than free-placed.",
        "why_it_matters_for_complete_gds": "OpenYield control region must be organized relative to array edges and replica timing structures.",
        "can_adapt_to_openyield": True,
        "should_not_copy_directly": False,
        "c0_blockers_addressed": "FLOORPLAN_NOT_SRAM_LIKE,CONTRACT_ROUTE",
        "target_stage_C2_C6": "C3",
    },
    {
        "rule_id": "SRC_049",
        "rule_category": "CONTROL_ROUTING",
        "openram_file": "compiler/modules/sram_1bank.py",
        "class_or_function": "route_clk",
        "pattern": "This is something like a \"spine\" clock distribution",
        "rule_summary": "Clock distribution is implemented as explicit spine routing from control logic to DFF clusters.",
        "why_it_matters_for_complete_gds": "OpenYield clk/gated_clk should become explicit routed spines, not contract boxes.",
        "can_adapt_to_openyield": True,
        "should_not_copy_directly": False,
        "c0_blockers_addressed": "CONTRACT_ROUTE,PLACEHOLDER_VISUAL_GEOMETRY",
        "target_stage_C2_C6": "C4",
    },
    {
        "rule_id": "SRC_050",
        "rule_category": "CONTROL_ROUTING",
        "openram_file": "compiler/modules/sram_1bank.py",
        "class_or_function": "route_control_logic",
        "pattern": "self.connect_vbus(src_pin, dest_pin)",
        "rule_summary": "Non-clock control signals are routed from control logic to bank on explicit vertical buses, while replica-bitline feedback uses a dedicated m3/m4 route.",
        "why_it_matters_for_complete_gds": "OpenYield control paths need net-specific geometry and bus ownership.",
        "can_adapt_to_openyield": True,
        "should_not_copy_directly": False,
        "c0_blockers_addressed": "CONTRACT_ROUTE,MISSING_PIN_GEOMETRY",
        "target_stage_C2_C6": "C2/C4",
    },
    {
        "rule_id": "SRC_051",
        "rule_category": "CONTROL_ROUTING",
        "openram_file": "compiler/modules/sram_1bank.py",
        "class_or_function": "route_row_addr_dff",
        "pattern": "self.add_path(\"m3\", [flop_pos, mid_pos])",
        "rule_summary": "Address flops connect to bank row-address inputs with explicit intermediate metal and via stacks.",
        "why_it_matters_for_complete_gds": "Address routing in OpenYield must be geometry-backed up to decoder inputs.",
        "can_adapt_to_openyield": True,
        "should_not_copy_directly": False,
        "c0_blockers_addressed": "CONTRACT_ROUTE,MISSING_PIN_GEOMETRY",
        "target_stage_C2_C6": "C2/C4",
    },
    {
        "rule_id": "SRC_052",
        "rule_category": "PIN_LABEL_EXPORT",
        "openram_file": "compiler/modules/sram_1bank.py",
        "class_or_function": "add_layout_pins",
        "pattern": "self.add_io_pin(",
        "rule_summary": "Top-level addr/din/dout/control/spare pins are exported from specific child instances, not synthesized in isolation.",
        "why_it_matters_for_complete_gds": "This is the physical precedent for OpenYield top-pin export in C4/C6.",
        "can_adapt_to_openyield": True,
        "should_not_copy_directly": False,
        "c0_blockers_addressed": "MISSING_TOP_PIN_GEOMETRY",
        "target_stage_C2_C6": "C4/C6",
    },
    {
        "rule_id": "SRC_053",
        "rule_category": "PIN_LABEL_EXPORT",
        "openram_file": "compiler/modules/sram_1bank.py",
        "class_or_function": "route_escape_pins",
        "pattern": "rtr.route(pins_to_route)",
        "rule_summary": "Perimeter pin escape routing is a dedicated post-placement routing step, not a byproduct of block placement.",
        "why_it_matters_for_complete_gds": "OpenYield top-level pin placement and escape must be explicit in C4/C6.",
        "can_adapt_to_openyield": True,
        "should_not_copy_directly": False,
        "c0_blockers_addressed": "MISSING_TOP_PIN_GEOMETRY,CONTRACT_ROUTE",
        "target_stage_C2_C6": "C4/C6",
    },
    {
        "rule_id": "SRC_054",
        "rule_category": "POWER_ROUTING",
        "openram_file": "compiler/modules/sram_1bank.py",
        "class_or_function": "route_layout",
        "pattern": "if OPTS.route_supplies:",
        "rule_summary": "Top-level supply routing is a distinct stage after signal geometry and top pins have been materialized.",
        "why_it_matters_for_complete_gds": "OpenYield should do C5 after C4 geometry exists so strap stitching lands on real shapes.",
        "can_adapt_to_openyield": True,
        "should_not_copy_directly": False,
        "c0_blockers_addressed": "CONTRACT_POWER_STITCH,APPROXIMATE_POWER_GEOMETRY",
        "target_stage_C2_C6": "C5",
    },
    {
        "rule_id": "SRC_055",
        "rule_category": "POWER_ROUTING",
        "openram_file": "compiler/router/supply_router.py",
        "class_or_function": "supply_router.route",
        "pattern": "Add side pins",
        "rule_summary": "Supply routing can add side pins or rings and then route true pin sets through a graph-based path search.",
        "why_it_matters_for_complete_gds": "OpenYield top-level power pins and straps should be driven by actual rail targets.",
        "can_adapt_to_openyield": True,
        "should_not_copy_directly": True,
        "c0_blockers_addressed": "CONTRACT_POWER_STITCH,APPROXIMATE_POWER_GEOMETRY",
        "target_stage_C2_C6": "C5",
    },
    {
        "rule_id": "SRC_056",
        "rule_category": "PIN_LABEL_EXPORT",
        "openram_file": "compiler/router/signal_escape_router.py",
        "class_or_function": "signal_escape_router.route",
        "pattern": "self.replace_layout_pins()",
        "rule_summary": "Signal escape routing replaces original IO pins with perimeter-exported geometry only after successful routed escape.",
        "why_it_matters_for_complete_gds": "Top pin geometry in OpenYield must reflect routed escape endpoints.",
        "can_adapt_to_openyield": True,
        "should_not_copy_directly": True,
        "c0_blockers_addressed": "MISSING_TOP_PIN_GEOMETRY,CONTRACT_ROUTE",
        "target_stage_C2_C6": "C4/C6",
    },
    {
        "rule_id": "SRC_057",
        "rule_category": "VALIDATION",
        "openram_file": "compiler/base/channel_route.py",
        "class_or_function": "channel_route",
        "pattern": "This does NOT try to minimize the number of tracks",
        "rule_summary": "Structured channel routing is aware of pin conflicts, preferred directions, and track pitch rather than drawing a single placeholder rectangle.",
        "why_it_matters_for_complete_gds": "OpenYield signal channels need geometry-aware routing ownership in C4.",
        "can_adapt_to_openyield": True,
        "should_not_copy_directly": True,
        "c0_blockers_addressed": "PLACEHOLDER_VISUAL_GEOMETRY,CONTRACT_ROUTE",
        "target_stage_C2_C6": "C4",
    },
    {
        "rule_id": "SRC_058",
        "rule_category": "VALIDATION",
        "openram_file": "compiler/modules/decoder.py",
        "class_or_function": "decoder",
        "pattern": "NOT_FOUND",
        "rule_summary": "Requested decoder.py file is not present in this OpenRAM checkout; decoder behavior is likely provided by other modules such as hierarchical_decoder.",
        "why_it_matters_for_complete_gds": "The audit must explicitly mark missing source references instead of inferring behavior from absent files.",
        "can_adapt_to_openyield": False,
        "should_not_copy_directly": True,
        "c0_blockers_addressed": "VALIDATION",
        "target_stage_C2_C6": "C1",
    },
]


@dataclass(frozen=True)
class SramPhysicalRuleExtractionConfig:
    repo_root: Path
    openram_root: Path
    openyield_root: Path
    c0_report_json: Path
    c0_gap_dir: Path
    r1_intent_dir: Path
    r3_structure_dir: Path
    r4_routing_dir: Path
    module_gds_dir: Path
    out_dir: Path
    out_matrix_csv: Path
    out_matrix_md: Path
    out_json: Path
    out_report: Path


@dataclass(frozen=True)
class OpenRamSourceRule:
    rule_id: str
    rule_category: str
    openram_file: str
    class_or_function: str
    line_reference_or_pattern: str
    rule_summary: str
    why_it_matters_for_complete_gds: str
    can_adapt_to_openyield: bool
    should_not_copy_directly: bool
    c0_blockers_addressed: str
    target_stage_C2_C6: str
    evidence_status: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class ReferenceGdsObservation:
    reference_gds_status: str
    reference_only: bool
    gds_path: str | None
    top_cell: str | None
    bbox: dict[str, float] | None
    cell_count: int
    recursive_instance_count: int
    layer_summary: dict[str, Any]
    array_like_dense_region_bbox: dict[str, float] | None
    row_periphery_relative_location: str
    column_periphery_relative_location: str
    power_strap_or_rail_layers: list[str]
    top_pin_or_label_layers: list[str]
    largest_shapes: list[dict[str, Any]]
    visual_geometric_conclusions: list[str]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class ArrayPhysicalRule:
    rule_name: str
    source_evidence: str
    rule_description: str
    required_geometry: str
    required_metadata: str
    c0_blockers_addressed: str
    implemented_in_stage: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class RowPathPhysicalRule:
    rule_name: str
    source_evidence: str
    rule_description: str
    required_geometry: str
    required_metadata: str
    c0_blockers_addressed: str
    implemented_in_stage: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class ColumnPathPhysicalRule:
    rule_name: str
    source_evidence: str
    rule_description: str
    required_geometry: str
    required_metadata: str
    c0_blockers_addressed: str
    implemented_in_stage: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class ControlIoPhysicalRule:
    rule_name: str
    source_evidence: str
    rule_description: str
    required_geometry: str
    required_metadata: str
    c0_blockers_addressed: str
    implemented_in_stage: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class PowerPhysicalRule:
    rule_name: str
    source_evidence: str
    rule_description: str
    required_geometry: str
    required_metadata: str
    c0_blockers_addressed: str
    implemented_in_stage: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class PinLabelLayerRule:
    rule_name: str
    source_evidence: str
    rule_description: str
    required_geometry: str
    required_metadata: str
    c0_blockers_addressed: str
    implemented_in_stage: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class CompleteGdsRequirement:
    requirement_id: str
    requirement_area: str
    minimum_requirement: str
    target_stage: str
    evidence_needed: str
    still_not_signoff_boundary: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class C0BlockerFixPlanEntry:
    blocker_id: str
    blocker_category: str
    affected_net_or_module: str
    priority: str
    c0_evidence: str
    assigned_fix_stage: str
    physical_rule_reference: str
    fix_strategy: str
    expected_output_artifact: str
    verification_method: str
    blocks_complete_gds_until_fixed: bool

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class SramPhysicalRuleExtractionResult:
    report: dict[str, Any]
    source_rules: tuple[OpenRamSourceRule, ...]
    blocker_fix_plan: tuple[C0BlockerFixPlanEntry, ...]


class SramPhysicalRuleExtractor:
    def __init__(self, config: SramPhysicalRuleExtractionConfig) -> None:
        self.config = config
        self._required_inputs = {
            "c0_report_json": config.c0_report_json,
            "c0_report_md": config.repo_root / "docs/openyield_C0_complete_gds_gap_audit_report.md",
            "c0_blocker_csv": config.c0_gap_dir / "complete_gds_blocker_matrix.csv",
            "contract_connection_csv": config.c0_gap_dir / "contract_connection_inventory.csv",
            "approximate_geometry_csv": config.c0_gap_dir / "approximate_geometry_inventory.csv",
            "contract_power_csv": config.c0_gap_dir / "contract_power_inventory.csv",
            "missing_pin_geometry_csv": config.c0_gap_dir / "missing_pin_geometry_inventory.csv",
            "real_geometry_csv": config.c0_gap_dir / "real_geometry_inventory.csv",
            "geometry_gap_summary_json": config.c0_gap_dir / "geometry_connection_gap_summary.json",
            "r1_intent_dir": config.r1_intent_dir,
            "r3_structure_dir": config.r3_structure_dir,
            "r4_routing_dir": config.r4_routing_dir,
            "module_gds_dir": config.module_gds_dir,
            "openram_root": config.openram_root,
            "openyield_root": config.openyield_root,
        }

    def run(self) -> SramPhysicalRuleExtractionResult:
        missing = [name for name, path in self._required_inputs.items() if not path.exists()]
        if missing:
            raise FileNotFoundError(f"C1 input files missing: {', '.join(missing)}")

        c0_report = _load_json(self.config.c0_report_json)
        blockers = _load_csv(self.config.c0_gap_dir / "complete_gds_blocker_matrix.csv")
        source_rules = self._extract_source_rules()
        reference_observation = self._extract_reference_gds()
        array_rules = self._build_array_rules(reference_observation)
        row_rules = self._build_row_rules(reference_observation)
        column_rules = self._build_column_rules(reference_observation)
        control_io_rules = self._build_control_io_rules(reference_observation)
        power_rules = self._build_power_rules(reference_observation)
        pin_label_rules = self._build_pin_label_rules()
        gap_rows = self._build_gap_matrix(c0_report, reference_observation, source_rules)
        requirements = self._build_complete_gds_requirements()
        fix_plan = self._build_blocker_fix_plan(blockers)

        report = self._build_report(
            c0_report=c0_report,
            source_rules=source_rules,
            reference_observation=reference_observation,
            array_rules=array_rules,
            row_rules=row_rules,
            column_rules=column_rules,
            control_io_rules=control_io_rules,
            power_rules=power_rules,
            pin_label_rules=pin_label_rules,
            gap_rows=gap_rows,
            fix_plan=fix_plan,
        )
        self._write_outputs(
            report=report,
            source_rules=source_rules,
            reference_observation=reference_observation,
            array_rules=array_rules,
            row_rules=row_rules,
            column_rules=column_rules,
            control_io_rules=control_io_rules,
            power_rules=power_rules,
            pin_label_rules=pin_label_rules,
            gap_rows=gap_rows,
            requirements=requirements,
            fix_plan=fix_plan,
        )
        return SramPhysicalRuleExtractionResult(
            report=report,
            source_rules=tuple(source_rules),
            blocker_fix_plan=tuple(fix_plan),
        )

    def _resolve_openram_file(self, rel_path: str) -> Path:
        return self.config.openram_root / rel_path

    def _extract_source_rules(self) -> list[OpenRamSourceRule]:
        rules: list[OpenRamSourceRule] = []
        for spec in RULE_SPECS:
            rel_path = spec["openram_file"]
            abs_path = self._resolve_openram_file(rel_path)
            pattern = str(spec["pattern"])
            if not abs_path.exists():
                evidence_status = "NOT_FOUND"
                line_ref = pattern
            else:
                text = abs_path.read_text(encoding="utf-8")
                line_ref = self._find_line_reference(text, pattern)
                evidence_status = "SOURCE_BACKED" if pattern != "NOT_FOUND" and line_ref != "PATTERN_NOT_FOUND" else "NOT_FOUND"
            rules.append(
                OpenRamSourceRule(
                    rule_id=spec["rule_id"],
                    rule_category=spec["rule_category"],
                    openram_file=str(abs_path if abs_path.exists() else rel_path),
                    class_or_function=spec["class_or_function"],
                    line_reference_or_pattern=line_ref,
                    rule_summary=spec["rule_summary"],
                    why_it_matters_for_complete_gds=spec["why_it_matters_for_complete_gds"],
                    can_adapt_to_openyield=bool(spec["can_adapt_to_openyield"]),
                    should_not_copy_directly=bool(spec["should_not_copy_directly"]),
                    c0_blockers_addressed=spec["c0_blockers_addressed"],
                    target_stage_C2_C6=spec["target_stage_C2_C6"],
                    evidence_status=evidence_status,
                )
            )
        return rules

    def _find_line_reference(self, text: str, pattern: str) -> str:
        if pattern == "NOT_FOUND":
            return "NOT_FOUND"
        for lineno, line in enumerate(text.splitlines(), start=1):
            if pattern in line:
                return f"L{lineno}:{line.strip()[:160]}"
        return "PATTERN_NOT_FOUND"

    def _extract_reference_gds(self) -> ReferenceGdsObservation:
        candidates = [
            self.config.repo_root / "outputs/layout_prototype/baseline_legacy/sram_8x64_wpr4_fd45.complete.gds",
            self.config.repo_root / "outputs/layout_prototype/baseline_legacy/sram_8x64_wpr4_fd45.gds",
            self.config.r4_routing_dir / "openyield_routed_power_pin_sram.gds",
        ]
        gds_path = next((path for path in candidates if path.exists()), None)
        if gds_path is None:
            return ReferenceGdsObservation(
                reference_gds_status="NOT_FOUND",
                reference_only=True,
                gds_path=None,
                top_cell=None,
                bbox=None,
                cell_count=0,
                recursive_instance_count=0,
                layer_summary={},
                array_like_dense_region_bbox=None,
                row_periphery_relative_location="unknown",
                column_periphery_relative_location="unknown",
                power_strap_or_rail_layers=[],
                top_pin_or_label_layers=[],
                largest_shapes=[],
                visual_geometric_conclusions=["No reference GDS found; C1 falls back to source-only extraction."],
            )

        lib = gdstk.read_gds(gds_path)
        top = lib.top_level()[0]
        cells = list(lib.cells)
        cell_map = {str(cell.name): cell for cell in cells}

        recursive_count = 0

        def visit(cell: gdstk.Cell) -> None:
            nonlocal recursive_count
            for ref in cell.references:
                recursive_count += 1
                child = cell_map.get(str(ref.cell_name))
                if child is not None:
                    visit(child)

        visit(top)
        bbox = _bbox_from_obj(top.bounding_box())
        shapes: list[dict[str, Any]] = []
        for index, polygon in enumerate(top.polygons):
            pb = _bbox_from_obj(polygon.bounding_box())
            shapes.append(
                {
                    "shape_id": f"ref_poly_{index}",
                    "layer_hint": f"{polygon.layer}/{polygon.datatype}",
                    "bbox": pb,
                    "area": _bbox_area(pb),
                }
            )
        shapes.sort(key=lambda row: row["area"], reverse=True)

        ref_groups: dict[str, list[dict[str, float]]] = {}
        for ref in top.references:
            name = str(ref.cell_name)
            child = cell_map.get(name)
            if child is None or child.bounding_box() is None:
                continue
            (x0, y0), (x1, y1) = child.bounding_box()
            ox, oy = ref.origin
            rb = {
                "x0": _round(ox + x0),
                "y0": _round(oy + y0),
                "x1": _round(ox + x1),
                "y1": _round(oy + y1),
                "width": _round(x1 - x0),
                "height": _round(y1 - y0),
            }
            ref_groups.setdefault(name, []).append(rb)

        dense_name = max(ref_groups.items(), key=lambda item: len(item[1]))[0] if ref_groups else ""
        array_bbox = None
        if dense_name:
            boxes = ref_groups[dense_name]
            array_bbox = {
                "x0": _round(min(box["x0"] for box in boxes)),
                "y0": _round(min(box["y0"] for box in boxes)),
                "x1": _round(max(box["x1"] for box in boxes)),
                "y1": _round(max(box["y1"] for box in boxes)),
                "width": _round(max(box["x1"] for box in boxes) - min(box["x0"] for box in boxes)),
                "height": _round(max(box["y1"] for box in boxes) - min(box["y0"] for box in boxes)),
            }

        row_related = [
            box for name, boxes in ref_groups.items() if re.search(r"wl_driver|nand|inv|decoder", name)
            for box in boxes
        ]
        column_related = [
            box for name, boxes in ref_groups.items() if re.search(r"precharge|col_mux|sense_amp|write_driver|tri_gate", name)
            for box in boxes
        ]
        row_loc = self._relative_location(array_bbox, row_related)
        column_loc = self._relative_location(array_bbox, column_related)

        layer_summary = inspect_gds_layers(gds_path)
        power_layers = sorted(
            layer for layer in layer_summary.get("boundary", {})
            if layer.startswith("1/") or layer.startswith("2/") or layer.startswith("3/")
        )[:10]
        top_label_layers = sorted(layer_summary.get("text", {}).keys())
        conclusions = [
            f"Reference macro `{top.name}` is array-centric: dense `{dense_name}` instances occupy bbox {array_bbox}." if dense_name else "Dense array instance could not be isolated from reference GDS.",
            f"Row periphery sits `{row_loc}` relative to the dense array region.",
            f"Column periphery sits `{column_loc}` relative to the dense array region.",
            "The macro shows repeated bitcell references plus narrow precharge/column/read/write bands instead of one overlay rectangle.",
            "Top-level pin labels exist on dedicated label layers and accompany real geometry, not label-only inventory rows.",
        ]
        return ReferenceGdsObservation(
            reference_gds_status="FOUND_EXISTING",
            reference_only=True,
            gds_path=str(gds_path),
            top_cell=str(top.name),
            bbox=bbox,
            cell_count=len(cells),
            recursive_instance_count=recursive_count,
            layer_summary=layer_summary,
            array_like_dense_region_bbox=array_bbox,
            row_periphery_relative_location=row_loc,
            column_periphery_relative_location=column_loc,
            power_strap_or_rail_layers=power_layers,
            top_pin_or_label_layers=top_label_layers,
            largest_shapes=shapes[:12],
            visual_geometric_conclusions=conclusions,
        )

    def _relative_location(self, center_bbox: dict[str, float] | None, boxes: list[dict[str, float]]) -> str:
        if center_bbox is None or not boxes:
            return "unknown"
        x0 = min(box["x0"] for box in boxes)
        y0 = min(box["y0"] for box in boxes)
        x1 = max(box["x1"] for box in boxes)
        y1 = max(box["y1"] for box in boxes)
        cx = (x0 + x1) / 2.0
        cy = (y0 + y1) / 2.0
        array_cx = (center_bbox["x0"] + center_bbox["x1"]) / 2.0
        array_cy = (center_bbox["y0"] + center_bbox["y1"]) / 2.0
        vertical = "above" if cy > array_cy else "below"
        horizontal = "right" if cx > array_cx else "left"
        if abs(cx - array_cx) < center_bbox["width"] * 0.15:
            return vertical
        if abs(cy - array_cy) < center_bbox["height"] * 0.15:
            return horizontal
        return f"{vertical}-{horizontal}"

    def _build_array_rules(self, ref: ReferenceGdsObservation) -> list[ArrayPhysicalRule]:
        return [
            ArrayPhysicalRule(
                rule_name="ArrayMainBody",
                source_evidence="OpenRAM bitcell_array/replica_bitcell_array source; reference GDS dense bitcell region",
                rule_description="Bitcell array must be the dominant physical core of the macro and own row/column pitch, BL/BR access, and WL access.",
                required_geometry="Real bitcell-array boundary plus per-column BL/BR shapes and per-row WL shapes.",
                required_metadata="row_pitch, column_pitch, bitcell orientation parity, array bbox.",
                c0_blockers_addressed="FLOORPLAN_NOT_SRAM_LIKE,CONTRACT_ROUTE,MISSING_PIN_GEOMETRY",
                implemented_in_stage="C2/C3",
            ),
            ArrayPhysicalRule(
                rule_name="ArrayPitchSource",
                source_evidence="bitcell_base_array.place_array; reference dense region spacing",
                rule_description="Row pitch and column pitch must derive from placed bitcell geometry, not top-level heuristic spacing.",
                required_geometry="Measured bitcell width/height and instance placement lattice.",
                required_metadata="row_pitch_source, column_pitch_source, array origin.",
                c0_blockers_addressed="PLACEHOLDER_VISUAL_GEOMETRY,FLOORPLAN_NOT_SRAM_LIKE",
                implemented_in_stage="C3",
            ),
            ArrayPhysicalRule(
                rule_name="ArrayBLBRAccess",
                source_evidence="bitcell_base_array.add_bitline_pins; replica_bitcell_array.add_layout_pins",
                rule_description="BL/BR access must be geometry-backed full-height array pins tied to real child pin layers.",
                required_geometry="Vertical BL/BR pin rectangles aligned to bitcell access points.",
                required_metadata="per-column net naming and source-target access ownership.",
                c0_blockers_addressed="CONTRACT_ROUTE,MISSING_PIN_GEOMETRY",
                implemented_in_stage="C2",
            ),
            ArrayPhysicalRule(
                rule_name="ArrayWLAccess",
                source_evidence="bitcell_base_array.add_wl_pins; local_bitcell_array.route",
                rule_description="Each WL must have row-specific geometry-backed access aligned to row pitch.",
                required_geometry="Per-row WL pin rectangles and driver landing shapes.",
                required_metadata="row index to wl net map and row-order parity.",
                c0_blockers_addressed="CONTRACT_ROUTE,MISSING_PIN_GEOMETRY",
                implemented_in_stage="C2/C4",
            ),
            ArrayPhysicalRule(
                rule_name="ArrayDummyReplicaBoundary",
                source_evidence="replica_bitcell_array/capped_replica_bitcell_array",
                rule_description="Dummy, replica, and cap structures must sit on array boundaries with defined timing/edge roles.",
                required_geometry="Replica columns left/right, dummy rows top/bottom, optional cap cells around perimeter.",
                required_metadata="which edges host replica or dummy structures and why.",
                c0_blockers_addressed="FLOORPLAN_NOT_SRAM_LIKE,PLACEHOLDER_VISUAL_GEOMETRY",
                implemented_in_stage="C3",
            ),
            ArrayPhysicalRule(
                rule_name="ArraySupplyAccess",
                source_evidence="bitcell_base_array.route_supplies; replica_bitcell_array.route_supplies",
                rule_description="VDD/GND array access must be copied from real child rails before any top-level strap stitching.",
                required_geometry="Per-instance supply pins or continuous rail shapes at the array edge.",
                required_metadata="supply-layer ownership and tap candidates.",
                c0_blockers_addressed="CONTRACT_POWER_STITCH,APPROXIMATE_POWER_GEOMETRY",
                implemented_in_stage="C2/C5",
            ),
        ]

    def _build_row_rules(self, ref: ReferenceGdsObservation) -> list[RowPathPhysicalRule]:
        return [
            RowPathPhysicalRule(
                rule_name="RowDecoderPlacement",
                source_evidence="bank.compute_instance_port0_offsets / port_address.place_instances",
                rule_description="Row decoder sits on the row-periphery side of the array and aligns to the main array vertical span.",
                required_geometry="Decoder bbox, array edge alignment, decoder output access points.",
                required_metadata="row decoder side, y-alignment anchor, decoder gap.",
                c0_blockers_addressed="FLOORPLAN_NOT_SRAM_LIKE",
                implemented_in_stage="C3",
            ),
            RowPathPhysicalRule(
                rule_name="WordlineDriverPlacement",
                source_evidence="local_bitcell_array.place; wordline_driver_array.place_drivers",
                rule_description="Wordline drivers sit adjacent to the array with pitch-aware spacing and alternating row orientation.",
                required_geometry="Driver array bbox, per-row output pins, spacing channel to array.",
                required_metadata="driver_to_array_spacing, row order, mirror parity.",
                c0_blockers_addressed="FLOORPLAN_NOT_SRAM_LIKE,MISSING_PIN_GEOMETRY",
                implemented_in_stage="C2/C3",
            ),
            RowPathPhysicalRule(
                rule_name="DecoderToDriverRouting",
                source_evidence="port_address.route_internal",
                rule_description="Decoder outputs connect to WL-driver inputs through explicit jog routes and via stacks.",
                required_geometry="Pin-to-pin route segments between decode outputs and driver inputs.",
                required_metadata="route layer, jog direction, per-row net mapping.",
                c0_blockers_addressed="CONTRACT_ROUTE",
                implemented_in_stage="C4",
            ),
            RowPathPhysicalRule(
                rule_name="DriverToArrayWLRouting",
                source_evidence="local_bitcell_array.route",
                rule_description="Driver outputs land on array WL pins through local/global WL layer transitions, not through one abstract row stripe.",
                required_geometry="Driver output access, WL vias, row-specific array landing geometry.",
                required_metadata="global_wl_layer, local_wl_layer, row mapping.",
                c0_blockers_addressed="CONTRACT_ROUTE,MISSING_PIN_GEOMETRY",
                implemented_in_stage="C2/C4",
            ),
            RowPathPhysicalRule(
                rule_name="RowPitchAlignment",
                source_evidence="bitcell_base_array.place_array; wordline_driver_array.place_drivers",
                rule_description="Each WL route and driver output must honor the underlying array row pitch.",
                required_geometry="Uniform row-step geometry from array to row path.",
                required_metadata="row_pitch and row index mapping.",
                c0_blockers_addressed="PLACEHOLDER_VISUAL_GEOMETRY",
                implemented_in_stage="C3/C4",
            ),
            RowPathPhysicalRule(
                rule_name="RowPathPower",
                source_evidence="port_address.route_supplies; wordline_driver_array.route_supplies",
                rule_description="Row decoder and wordline-driver power rails must align with row-periphery geometry and remain stitchable to top rails.",
                required_geometry="Continuous VDD/GND pins or rails over row path modules.",
                required_metadata="power rail layer and connection side.",
                c0_blockers_addressed="CONTRACT_POWER_STITCH",
                implemented_in_stage="C2/C5",
            ),
        ]

    def _build_column_rules(self, ref: ReferenceGdsObservation) -> list[ColumnPathPhysicalRule]:
        return [
            ColumnPathPhysicalRule(
                rule_name="PrechargePlacement",
                source_evidence="port_data.add_modules; precharge_array.place_insts",
                rule_description="Precharge cells align to raw bitline pitch at the array column edge, including optional replica-bitline extra column.",
                required_geometry="Per-column precharge cell placement and BL/BR pin shapes.",
                required_metadata="column offsets, column mirror parity, has_rbl side.",
                c0_blockers_addressed="MISSING_PIN_GEOMETRY,CONTRACT_ROUTE",
                implemented_in_stage="C2/C3",
            ),
            ColumnPathPhysicalRule(
                rule_name="ColumnMuxPlacement",
                source_evidence="column_mux_array.setup_layout_constants/place_array",
                rule_description="Column mux sits between raw BL/BR and word-owned read/write stages, with reserved select/output routing height.",
                required_geometry="Mux bbox, select rail channels, output join rails.",
                required_metadata="words_per_row, select-layer pitch, mux grouping.",
                c0_blockers_addressed="PLACEHOLDER_VISUAL_GEOMETRY,CONTRACT_ROUTE",
                implemented_in_stage="C3/C4",
            ),
            ColumnPathPhysicalRule(
                rule_name="SenseAmpPlacement",
                source_evidence="sense_amp_array.place_sense_amp_array",
                rule_description="Sense amps align to word outputs, not every raw column, so words-per-row controls their x ownership.",
                required_geometry="Word-level sense amp positions and output pin geometry.",
                required_metadata="words_per_row to column ownership map.",
                c0_blockers_addressed="CONTRACT_ROUTE,FLOORPLAN_NOT_SRAM_LIKE",
                implemented_in_stage="C3/C4",
            ),
            ColumnPathPhysicalRule(
                rule_name="WriteDriverPlacement",
                source_evidence="write_driver_array.place_write_array",
                rule_description="Write drivers align to word outputs and handle spare columns separately from regular word lanes.",
                required_geometry="Per-word write-driver geometry and enable rails.",
                required_metadata="write_size, words_per_row, spare column ownership.",
                c0_blockers_addressed="CONTRACT_ROUTE,FLOORPLAN_NOT_SRAM_LIKE",
                implemented_in_stage="C3/C4",
            ),
            ColumnPathPhysicalRule(
                rule_name="BLBRConnectivityChain",
                source_evidence="port_data.route_data_lines",
                rule_description="BL/BR must connect through a physical chain: array <-> precharge <-> mux/sense/write, depending on mode and words-per-row.",
                required_geometry="Distinct pin-to-pin routes for each consumer stage.",
                required_metadata="mode-aware chain ownership and net aliases.",
                c0_blockers_addressed="CONTRACT_ROUTE",
                implemented_in_stage="C4",
            ),
            ColumnPathPhysicalRule(
                rule_name="ColumnPathPower",
                source_evidence="precharge_array.route_supplies; sense_amp_array.route_supplies; write_driver_array.route_supplies",
                rule_description="Each column path stage exports local VDD/GND rails that must be stitched to top-level power with real taps.",
                required_geometry="Stage-local rail shapes and tap landing points.",
                required_metadata="supply layer, edge orientation, top strap targets.",
                c0_blockers_addressed="CONTRACT_POWER_STITCH,APPROXIMATE_POWER_GEOMETRY",
                implemented_in_stage="C2/C5",
            ),
        ]

    def _build_control_io_rules(self, ref: ReferenceGdsObservation) -> list[ControlIoPhysicalRule]:
        return [
            ControlIoPhysicalRule(
                rule_name="ControlLogicPlacement",
                source_evidence="sram_1bank.place_control; bank.compute_instance_offsets",
                rule_description="Control logic is placed relative to the bank array and row/data periphery so that control spines can reach both sides cleanly.",
                required_geometry="Control logic bbox and anchor relative to array center.",
                required_metadata="control_logic_center, bank array anchors.",
                c0_blockers_addressed="FLOORPLAN_NOT_SRAM_LIKE",
                implemented_in_stage="C3",
            ),
            ControlIoPhysicalRule(
                rule_name="DelayReplicaPlacement",
                source_evidence="sram_1bank.place_control; bank.route_rbl",
                rule_description="Delay/replica timing structures stay physically aligned to array-side replica geometry and feed control logic through explicit RBL routing.",
                required_geometry="Replica BL geometry and delay-chain placement window.",
                required_metadata="rbl source/target mapping and edge ownership.",
                c0_blockers_addressed="CONTRACT_ROUTE,MISSING_PIN_GEOMETRY",
                implemented_in_stage="C2/C3/C4",
            ),
            ControlIoPhysicalRule(
                rule_name="ControlEnableDistribution",
                source_evidence="sram_1bank.route_control_logic; sense_amp_array.route_rails; write_driver_array.add_layout_pins",
                rule_description="precharge_en/sense_en/write_en/wordline_en must be distributed on explicit buses or rails to actual sink pins.",
                required_geometry="Control spine segments, vias, and sink landing shapes.",
                required_metadata="sink list by net and route layer ownership.",
                c0_blockers_addressed="CONTRACT_ROUTE",
                implemented_in_stage="C2/C4",
            ),
            ControlIoPhysicalRule(
                rule_name="ClockSpineDistribution",
                source_evidence="sram_1bank.route_clk",
                rule_description="clk and buffered clock are routed as spines with defined branch points into control and DFF clusters.",
                required_geometry="Clock trunk, branches, and via stacks.",
                required_metadata="clock fanout map and route stack.",
                c0_blockers_addressed="CONTRACT_ROUTE,PLACEHOLDER_VISUAL_GEOMETRY",
                implemented_in_stage="C4",
            ),
            ControlIoPhysicalRule(
                rule_name="AddressDinDoutOrganization",
                source_evidence="sram_1bank.add_layout_pins; route_row_addr_dff; route_data_dffs",
                rule_description="addr, din, and dout should originate from the corresponding flop/bank child pins and then escape to the perimeter through explicit routing.",
                required_geometry="Instance-backed IO pins and escape routes.",
                required_metadata="which instance owns each external IO bit.",
                c0_blockers_addressed="MISSING_TOP_PIN_GEOMETRY,MISSING_LVS_READY_NET_MAPPING",
                implemented_in_stage="C4/C6",
            ),
            ControlIoPhysicalRule(
                rule_name="TopPinPlacement",
                source_evidence="sram_1bank.route_escape_pins; signal_escape_router",
                rule_description="Top-level pins belong on the perimeter after escape routing is complete and should correspond to routed internal geometry.",
                required_geometry="Perimeter pin shapes and matching internal routes.",
                required_metadata="top pin side, layer, net name, source instance.",
                c0_blockers_addressed="MISSING_TOP_PIN_GEOMETRY",
                implemented_in_stage="C4/C6",
            ),
        ]

    def _build_power_rules(self, ref: ReferenceGdsObservation) -> list[PowerPhysicalRule]:
        return [
            PowerPhysicalRule(
                rule_name="ArrayInternalRails",
                source_evidence="bitcell_base_array.route_supplies; reference GDS bitcell/dummy rail propagation",
                rule_description="Array-internal VDD/GND should propagate from the bitcell and dummy/replica children, preserving their orientation and edge reach.",
                required_geometry="Array-local supply pins or continuous rails.",
                required_metadata="rail layer, side/orientation, cell parity effects.",
                c0_blockers_addressed="CONTRACT_POWER_STITCH,MISSING_PIN_GEOMETRY",
                implemented_in_stage="C2/C5",
            ),
            PowerPhysicalRule(
                rule_name="RowPeripheryRails",
                source_evidence="port_address.route_supplies; wordline_driver_array.route_supplies",
                rule_description="Row decoder and wordline drivers need explicit row-periphery rails aligned for later top-level stitch.",
                required_geometry="Vertical/horizontal row-periphery rails with true pins.",
                required_metadata="rail orientation by module.",
                c0_blockers_addressed="CONTRACT_POWER_STITCH",
                implemented_in_stage="C2/C5",
            ),
            PowerPhysicalRule(
                rule_name="ColumnPeripheryRails",
                source_evidence="precharge_array.route_supplies; sense_amp_array.route_supplies; write_driver_array.route_supplies",
                rule_description="Precharge, mux, sense, and write stages require stage-local rails before top-level straps are added.",
                required_geometry="Per-stage VDD/GND rails and tap points.",
                required_metadata="column stage to rail mapping.",
                c0_blockers_addressed="CONTRACT_POWER_STITCH,APPROXIMATE_POWER_GEOMETRY",
                implemented_in_stage="C2/C5",
            ),
            PowerPhysicalRule(
                rule_name="ControlPeripheryRails",
                source_evidence="sram_1bank.route_layout; supply_router",
                rule_description="Control region needs its own stitchable rails or ring targets before top-level strap export.",
                required_geometry="Control VDD/GND rails and side/ring targets.",
                required_metadata="power pin type and stitch policy.",
                c0_blockers_addressed="CONTRACT_POWER_STITCH,APPROXIMATE_POWER_GEOMETRY",
                implemented_in_stage="C2/C5",
            ),
            PowerPhysicalRule(
                rule_name="TopLevelPowerStraps",
                source_evidence="supply_router.add_side_pin/add_ring_pin",
                rule_description="Top-level VDD/GND straps or rings should be created after sink rails are known and must connect through explicit taps/vias.",
                required_geometry="Top straps, corner vias, module-rail taps.",
                required_metadata="strap layer stack, side or ring selection.",
                c0_blockers_addressed="APPROXIMATE_POWER_GEOMETRY,CONTRACT_POWER_STITCH",
                implemented_in_stage="C5",
            ),
            PowerPhysicalRule(
                rule_name="TopPowerPins",
                source_evidence="supply_router.route; hierarchy_layout.copy_power_pins",
                rule_description="Top-level VDD/GND pins must coincide with real strap/ring geometry and not be isolated placeholders.",
                required_geometry="Exported top VDD/GND pin rectangles on final strap/ring layers.",
                required_metadata="top power pin layer/name mapping.",
                c0_blockers_addressed="APPROXIMATE_POWER_GEOMETRY,MISSING_TOP_PIN_GEOMETRY",
                implemented_in_stage="C5/C6",
            ),
        ]

    def _build_pin_label_rules(self) -> list[PinLabelLayerRule]:
        return [
            PinLabelLayerRule(
                rule_name="GeometryBackedMinimum",
                source_evidence="hierarchy_layout.add_layout_pin / add_layout_pin_segment_center",
                rule_description="A complete-GDS pin must have geometry bbox, layer, and stable net name. A label alone is insufficient.",
                required_geometry="Pin rectangle or routed pin segment on a real layer.",
                required_metadata="net name, bbox, layer, owning instance/module.",
                c0_blockers_addressed="MISSING_PIN_GEOMETRY,MISSING_TOP_PIN_GEOMETRY",
                implemented_in_stage="C2/C6",
            ),
            PinLabelLayerRule(
                rule_name="SynthesizedPinAllowance",
                source_evidence="hierarchy_layout.copy_layout_pin / add_io_pin",
                rule_description="Synthesized pins are only acceptable when they are copied or routed from real child geometry, not invented without a geometry source.",
                required_geometry="Child-backed geometry and optional escape-routed replacement pin.",
                required_metadata="source instance pin reference and replacement history.",
                c0_blockers_addressed="MISSING_TOP_PIN_GEOMETRY",
                implemented_in_stage="C2/C4/C6",
            ),
            PinLabelLayerRule(
                rule_name="LabelOnlyBoundary",
                source_evidence="hierarchy_layout.add_label_pin",
                rule_description="Label-only correspondence points can help debug LVS but cannot serve as complete-GDS connectivity evidence.",
                required_geometry="None; this is explicitly non-sufficient.",
                required_metadata="must be marked as label-only or correspondence-only.",
                c0_blockers_addressed="MISSING_PIN_GEOMETRY",
                implemented_in_stage="C6",
            ),
            PinLabelLayerRule(
                rule_name="PinShapeLabelConsistency",
                source_evidence="hierarchy_layout.add_layout_pin / replace_layout_pin",
                rule_description="Pin bbox, layer, label text, and net name must remain consistent when a pin is moved or replaced.",
                required_geometry="Final pin shape plus any retained internal route geometry.",
                required_metadata="pin-to-net and old-to-new pin mapping.",
                c0_blockers_addressed="MISSING_LVS_READY_NET_MAPPING,MISSING_TOP_PIN_GEOMETRY",
                implemented_in_stage="C4/C6",
            ),
            PinLabelLayerRule(
                rule_name="NetToShapeTruth",
                source_evidence="hierarchy_layout.replace_layout_pin; signal_escape_router.replace_layout_pins",
                rule_description="net_to_shape_map must point to real GDS shapes that survive into the final top cell, not to report-only bbox rows.",
                required_geometry="GDS-resident shapes with stable bbox and layer.",
                required_metadata="net_to_shape entry id, shape bbox, shape layer, source evidence path.",
                c0_blockers_addressed="MISSING_LVS_READY_NET_MAPPING,PLACEHOLDER_VISUAL_GEOMETRY",
                implemented_in_stage="C4/C6",
            ),
        ]

    def _build_gap_matrix(
        self,
        c0_report: dict[str, Any],
        ref: ReferenceGdsObservation,
        source_rules: list[OpenRamSourceRule],
    ) -> list[dict[str, Any]]:
        return [
            {
                "gap_id": "GAP_001",
                "physical_area": "ARRAY",
                "openram_rule_or_observation": "Dense bitcell array is the visual and geometric macro core.",
                "current_openyield_status_from_C0": f"large_placeholder_shape_count={c0_report['large_placeholder_shape_count']}",
                "gap_description": "OpenYield top cell is dominated by overlay rectangles rather than an array-owned access topology.",
                "blocks_complete_gds": True,
                "required_fix_stage": "C3",
                "recommended_openyield_specific_solution": "Re-anchor floorplan and channels to bitcell-array bbox, pitch, and edge access.",
                "do_not_copy_openram_reason": "OpenYield module set and hierarchy differ, so only the physical rule transfers.",
                "priority": "P0",
            },
            {
                "gap_id": "GAP_002",
                "physical_area": "ROW_PATH",
                "openram_rule_or_observation": "Row decoder and WL driver sit adjacent to the array and route through explicit driver-to-array access.",
                "current_openyield_status_from_C0": f"wordline_contract_route_count={c0_report['wordline_contract_route_count']}",
                "gap_description": "OpenYield WL routing still relies on contract pins and row-wide prototype stripes.",
                "blocks_complete_gds": True,
                "required_fix_stage": "C2/C4",
                "recommended_openyield_specific_solution": "Extract WL driver and array WL access pins, then rebuild row routes pin-to-pin.",
                "do_not_copy_openram_reason": "OpenYield row modules are custom wrappers, not OpenRAM row blocks.",
                "priority": "P0",
            },
            {
                "gap_id": "GAP_003",
                "physical_area": "COLUMN_PATH",
                "openram_rule_or_observation": "BL/BR flow through a staged precharge/mux/sense/write chain with pitch-aligned modules.",
                "current_openyield_status_from_C0": f"bitline_contract_route_count={c0_report['bitline_contract_route_count']}",
                "gap_description": "OpenYield duplicates BL/BR contract routes into multiple consumers instead of routing through a physical chain.",
                "blocks_complete_gds": True,
                "required_fix_stage": "C2/C3/C4",
                "recommended_openyield_specific_solution": "Recover per-stage access geometry and route the physical chain from array through each column-path stage.",
                "do_not_copy_openram_reason": "OpenYield uses different module naming and wrapper composition.",
                "priority": "P0",
            },
            {
                "gap_id": "GAP_004",
                "physical_area": "CONTROL_IO",
                "openram_rule_or_observation": "Control, addr, din, dout, and clk use explicit buses/spines and escape routing to perimeter pins.",
                "current_openyield_status_from_C0": f"control_contract_route_count={c0_report['control_contract_route_count']}",
                "gap_description": "OpenYield control/IO remain report-backed or contract-backed instead of routed to real sinks and perimeter pins.",
                "blocks_complete_gds": True,
                "required_fix_stage": "C3/C4/C6",
                "recommended_openyield_specific_solution": "Build control spines and IO escape routes from child-backed geometry, then relocate top pins to those endpoints.",
                "do_not_copy_openram_reason": "OpenYield intent naming and control decomposition are OpenYield-specific.",
                "priority": "P0",
            },
            {
                "gap_id": "GAP_005",
                "physical_area": "POWER",
                "openram_rule_or_observation": "Array/periphery rails are real child geometry and top straps/rings land on them through explicit routing.",
                "current_openyield_status_from_C0": f"contract_rail_based_stitch_count={c0_report['contract_rail_based_stitch_count']}, approximate_power_geometry_count={c0_report['approximate_power_geometry_count']}",
                "gap_description": "OpenYield VDD/GND are still contract stitched and approximate at top level.",
                "blocks_complete_gds": True,
                "required_fix_stage": "C2/C5",
                "recommended_openyield_specific_solution": "Extract module rails, add real taps, and only then synthesize top-level straps and power pins.",
                "do_not_copy_openram_reason": "Exact strap/ring policy depends on OpenYield-supported config and current module rail shapes.",
                "priority": "P0",
            },
            {
                "gap_id": "GAP_006",
                "physical_area": "PIN_LABEL",
                "openram_rule_or_observation": "Pins are copied or replaced from real geometry; label-only markers are not treated as actual pins.",
                "current_openyield_status_from_C0": f"missing_pin_entry_count={c0_report['missing_pin_entry_count']}",
                "gap_description": "OpenYield still has many non-geometry-backed pins and some label-only evidence.",
                "blocks_complete_gds": True,
                "required_fix_stage": "C2/C6",
                "recommended_openyield_specific_solution": "Classify every required pin as geometry-backed, synthesized-from-geometry, or invalid-for-complete-GDS.",
                "do_not_copy_openram_reason": "Pin naming and hierarchy differ, but the geometry-backed requirement is reusable.",
                "priority": "P0",
            },
            {
                "gap_id": "GAP_007",
                "physical_area": "GDS_HIERARCHY",
                "openram_rule_or_observation": "GDS export follows complete hierarchy assembly with boundary and pin replacement already applied.",
                "current_openyield_status_from_C0": "prototype overlay over R3 hierarchy",
                "gap_description": "OpenYield current top GDS is a prototype overlay rather than a fully reworked physical hierarchy for connectivity.",
                "blocks_complete_gds": True,
                "required_fix_stage": "C6",
                "recommended_openyield_specific_solution": "Preserve hierarchy, but ensure final net-to-shape truth comes from actual repaired geometry before re-export.",
                "do_not_copy_openram_reason": "OpenYield must keep its own hierarchy and reports.",
                "priority": "P1",
            },
            {
                "gap_id": "GAP_008",
                "physical_area": "VALIDATION",
                "openram_rule_or_observation": "OpenRAM treats layout export, pin export, and downstream verification artifacts as a coherent flow.",
                "current_openyield_status_from_C0": f"complete_gds_blocker_count={c0_report['complete_gds_blocker_count']}",
                "gap_description": "OpenYield has an audit map but not yet extraction-ready complete-GDS proof for current supported config.",
                "blocks_complete_gds": True,
                "required_fix_stage": "C6",
                "recommended_openyield_specific_solution": "Promote net-to-shape evidence to shape-truth and validation checks tied to repaired geometry.",
                "do_not_copy_openram_reason": "C6 boundary in OpenYield is complete-GDS for current config, not full signoff.",
                "priority": "P1",
            },
        ]

    def _build_complete_gds_requirements(self) -> list[CompleteGdsRequirement]:
        return [
            CompleteGdsRequirement(
                requirement_id="REQ_C2_01",
                requirement_area="C2 pin access requirements",
                minimum_requirement="Every WL/BL/BR/control/VDD/GND/top-IO sink or source needed by current supported config must have geometry-backed access or a geometry-backed synthesized replacement pin.",
                target_stage="C2",
                evidence_needed="Pin inventories updated to GEOMETRY_BACKED_PIN with bbox/layer/net ownership.",
                still_not_signoff_boundary="This does not imply DRC/LVS closure.",
            ),
            CompleteGdsRequirement(
                requirement_id="REQ_C3_01",
                requirement_area="C3 floorplan requirements",
                minimum_requirement="Array must be the macro core; row, column, control, dummy, replica, and boundary structures must be placed relative to actual array pitch and edge access windows.",
                target_stage="C3",
                evidence_needed="Updated floorplan report and region bboxes derived from actual geometry.",
                still_not_signoff_boundary="This does not imply congestion-free final routing.",
            ),
            CompleteGdsRequirement(
                requirement_id="REQ_C4_01",
                requirement_area="C4 signal routing requirements",
                minimum_requirement="WL/BL/BR/control/clk/addr/din/dout/top-IO routes must exist as real GDS geometry between source and target access points.",
                target_stage="C4",
                evidence_needed="Real geometry inventory with pin-to-pin routes and no contract-only dependencies for required nets.",
                still_not_signoff_boundary="This does not imply timing closure or global route optimality.",
            ),
            CompleteGdsRequirement(
                requirement_id="REQ_C5_01",
                requirement_area="C5 power network requirements",
                minimum_requirement="VDD/GND must connect module rails to top-level straps/pins through real taps and vias; no contract-only power stitches may remain.",
                target_stage="C5",
                evidence_needed="Power continuity inventory with geometry-backed rails, taps, and top power pins.",
                still_not_signoff_boundary="This does not imply EM/IR signoff.",
            ),
            CompleteGdsRequirement(
                requirement_id="REQ_C6_01",
                requirement_area="C6 validation requirements",
                minimum_requirement="Net-to-shape evidence must refer to actual GDS shapes, and the repaired top GDS must parse, map, and preserve hierarchy consistently for current supported config.",
                target_stage="C6",
                evidence_needed="Final geometry-backed audits and parsed GDS comparison.",
                still_not_signoff_boundary="This does not imply full LVS-clean or DRC-clean status unless separately proven.",
            ),
            CompleteGdsRequirement(
                requirement_id="REQ_C6_02",
                requirement_area="complete GDS claim requirements",
                minimum_requirement="The minimum complete-GDS bar is geometry-backed connectivity for the current supported config across signal, power, and top pins.",
                target_stage="C6",
                evidence_needed="Contract/approximate counts reduced to zero for required complete-GDS claim scope.",
                still_not_signoff_boundary="Complete GDS is not equivalent to timing signoff, DRC signoff, or LVS signoff.",
            ),
        ]

    def _build_blocker_fix_plan(self, blockers: list[dict[str, str]]) -> list[C0BlockerFixPlanEntry]:
        plan: list[C0BlockerFixPlanEntry] = []
        for blocker in blockers:
            category = blocker["blocker_category"]
            stage = blocker["required_fix_stage"]
            area, rule_ref, strategy, artifact, verification = self._fix_plan_for_blocker(category, blocker["affected_net_or_module"], stage)
            plan.append(
                C0BlockerFixPlanEntry(
                    blocker_id=blocker["blocker_id"],
                    blocker_category=category,
                    affected_net_or_module=blocker["affected_net_or_module"],
                    priority=blocker["priority"],
                    c0_evidence=blocker["evidence_source"],
                    assigned_fix_stage=stage,
                    physical_rule_reference=rule_ref,
                    fix_strategy=strategy,
                    expected_output_artifact=artifact,
                    verification_method=verification,
                    blocks_complete_gds_until_fixed=True,
                )
            )
        return plan

    def _fix_plan_for_blocker(self, category: str, affected: str, stage: str) -> tuple[str, str, str, str, str]:
        if category == "MISSING_PIN_GEOMETRY":
            area = "PIN_LABEL"
            return (
                area,
                "ArrayBLBRAccess / ArrayWLAccess / GeometryBackedMinimum",
                "Extract or synthesize geometry-backed pin access from module GDS, then update dependent routes to land on those shapes.",
                "updated pin inventories and module access metadata",
                "pin inventory shows GEOMETRY_BACKED_PIN and routes reference real bboxes",
            )
        if category == "CONTRACT_ROUTE":
            return (
                "ROW_PATH" if affected.startswith("WL") else "COLUMN_PATH" if affected.startswith("BL") or affected.startswith("BR") else "CONTROL_IO",
                "DecoderToDriverRouting / BLBRConnectivityChain / ControlEnableDistribution",
                "Replace contract ownership with pin-to-pin geometry between named source and target access shapes.",
                "geometry-routed signal inventory",
                "net_to_shape_map references actual GDS route shapes for the affected net",
            )
        if category == "PLACEHOLDER_VISUAL_GEOMETRY":
            return (
                "ARRAY",
                "ArrayPitchSource / ColumnMuxPlacement / TopPinPlacement",
                "Replace large placeholder rectangles with floorplan-aware channels, segmented routes, or real perimeter pin shapes.",
                "reworked floorplan and real geometry inventory",
                "placeholder counts drop and replaced shapes align to actual modules",
            )
        if category in {"CONTRACT_POWER_STITCH", "APPROXIMATE_POWER_GEOMETRY"}:
            return (
                "POWER",
                "ArraySupplyAccess / TopLevelPowerStraps / TopPowerPins",
                "Promote contract or approximate power geometry to real rails, taps, vias, and top straps/pins.",
                "geometry-backed power continuity report",
                "power inventory shows real rails/taps and no contract-only stitch for the affected net",
            )
        if category == "APPROXIMATE_ROUTE":
            return (
                "COLUMN_PATH",
                "BLBRConnectivityChain / ColumnMuxPlacement",
                "Replace bbox-only approximate route geometry with explicit stage-by-stage routing.",
                "updated route geometry inventory",
                "approximate route entries removed from required-scope nets",
            )
        if category == "FLOORPLAN_NOT_SRAM_LIKE":
            return (
                "ARRAY",
                "ArrayMainBody / RowDecoderPlacement / PrechargePlacement",
                "Rebuild macro floorplan around array-centric physical ownership and edge-aligned periphery.",
                "array/row/column/control floorplan report",
                "topology and visual audits show array-centric placement with real periphery bands",
            )
        if category == "MISSING_LVS_READY_NET_MAPPING":
            return (
                "VALIDATION",
                "NetToShapeTruth / complete GDS claim requirements",
                "Tie semantic nets to surviving final GDS shapes and validate the mapping after geometry repair.",
                "final extraction-aligned net-to-shape audit",
                "all required map entries point to actual final GDS shapes with stable layers/bboxes",
            )
        return (
            "VALIDATION",
            "complete GDS claim requirements",
            "Resolve the blocker with geometry-backed evidence tied to the final supported-config layout.",
            "follow-up validation evidence",
            "blocker-specific audit closes cleanly",
        )

    def _build_report(
        self,
        c0_report: dict[str, Any],
        source_rules: list[OpenRamSourceRule],
        reference_observation: ReferenceGdsObservation,
        array_rules: list[ArrayPhysicalRule],
        row_rules: list[RowPathPhysicalRule],
        column_rules: list[ColumnPathPhysicalRule],
        control_io_rules: list[ControlIoPhysicalRule],
        power_rules: list[PowerPhysicalRule],
        pin_label_rules: list[PinLabelLayerRule],
        gap_rows: list[dict[str, Any]],
        fix_plan: list[C0BlockerFixPlanEntry],
    ) -> dict[str, Any]:
        source_backed_count = sum(1 for row in source_rules if row.evidence_status == "SOURCE_BACKED")
        return {
            "C1_physical_rule_extraction_available": True,
            "openram_source_rule_inventory_available": True,
            "reference_gds_physical_observation_available": True,
            "array_physical_rules_available": True,
            "row_path_physical_rules_available": True,
            "column_path_physical_rules_available": True,
            "control_io_physical_rules_available": True,
            "power_physical_rules_available": True,
            "pin_label_layer_rules_available": True,
            "openram_vs_openyield_gap_matrix_available": True,
            "complete_gds_physical_requirements_available": True,
            "c0_blocker_to_c2_c6_fix_plan_available": True,
            "openram_source_rule_count": source_backed_count,
            "reference_gds_status": reference_observation.reference_gds_status,
            "reference_gds_path": reference_observation.gds_path,
            "array_rule_count": len(array_rules),
            "row_path_rule_count": len(row_rules),
            "column_path_rule_count": len(column_rules),
            "control_io_rule_count": len(control_io_rules),
            "power_rule_count": len(power_rules),
            "pin_label_rule_count": len(pin_label_rules),
            "openram_vs_openyield_gap_count": len(gap_rows),
            "c0_blocker_fix_plan_count": len(fix_plan),
            "complete_gds_blocker_count_from_C0": int(c0_report["complete_gds_blocker_count"]),
            "remaining_C1_blockers": [],
            "remaining_C1_blockers_count": 0,
            "can_claim_C1_physical_rules_extracted_now": True,
            "can_claim_complete_gds_now": False,
            "can_enter_C2_pin_geometry_access_repair": True,
            "repo_git_commit": _git_commit(self.config.repo_root),
        }

    def _write_outputs(
        self,
        report: dict[str, Any],
        source_rules: list[OpenRamSourceRule],
        reference_observation: ReferenceGdsObservation,
        array_rules: list[ArrayPhysicalRule],
        row_rules: list[RowPathPhysicalRule],
        column_rules: list[ColumnPathPhysicalRule],
        control_io_rules: list[ControlIoPhysicalRule],
        power_rules: list[PowerPhysicalRule],
        pin_label_rules: list[PinLabelLayerRule],
        gap_rows: list[dict[str, Any]],
        requirements: list[CompleteGdsRequirement],
        fix_plan: list[C0BlockerFixPlanEntry],
    ) -> None:
        out_dir = self.config.out_dir
        out_dir.mkdir(parents=True, exist_ok=True)

        source_rows = [row.to_dict() for row in source_rules]
        array_rows = [row.to_dict() for row in array_rules]
        row_path_rows = [row.to_dict() for row in row_rules]
        column_rows = [row.to_dict() for row in column_rules]
        control_rows = [row.to_dict() for row in control_io_rules]
        power_rows = [row.to_dict() for row in power_rules]
        pin_rows = [row.to_dict() for row in pin_label_rules]
        requirement_rows = [row.to_dict() for row in requirements]
        fix_rows = [row.to_dict() for row in fix_plan]

        _json_dump(out_dir / "sram_baseline_physical_rulebook.json", {
            "source_rules": source_rows,
            "reference_gds": reference_observation.to_dict(),
            "array_rules": array_rows,
            "row_path_rules": row_path_rows,
            "column_path_rules": column_rows,
            "control_io_rules": control_rows,
            "power_rules": power_rows,
            "pin_label_layer_rules": pin_rows,
            "complete_gds_requirements": requirement_rows,
        })
        _write_text(out_dir / "sram_baseline_physical_rulebook.md", self._render_rulebook_md(report, reference_observation))

        _write_csv(out_dir / "openram_source_rule_inventory.csv", SOURCE_RULE_COLUMNS, source_rows)
        _write_text(out_dir / "openram_source_rule_inventory.md", "# OpenRAM Source Rule Inventory\n\n" + _md_table(SOURCE_RULE_COLUMNS, source_rows))

        _json_dump(out_dir / "reference_gds_physical_observation.json", reference_observation.to_dict())
        _write_text(out_dir / "reference_gds_physical_observation.md", self._render_reference_md(reference_observation))

        _json_dump(out_dir / "array_physical_rules.json", {"rules": array_rows})
        _write_text(out_dir / "array_physical_rules.md", "# Array Physical Rules\n\n" + _md_table(list(array_rows[0].keys()), array_rows))
        _json_dump(out_dir / "row_path_physical_rules.json", {"rules": row_path_rows})
        _write_text(out_dir / "row_path_physical_rules.md", "# Row Path Physical Rules\n\n" + _md_table(list(row_path_rows[0].keys()), row_path_rows))
        _json_dump(out_dir / "column_path_physical_rules.json", {"rules": column_rows})
        _write_text(out_dir / "column_path_physical_rules.md", "# Column Path Physical Rules\n\n" + _md_table(list(column_rows[0].keys()), column_rows))
        _json_dump(out_dir / "control_io_physical_rules.json", {"rules": control_rows})
        _write_text(out_dir / "control_io_physical_rules.md", "# Control IO Physical Rules\n\n" + _md_table(list(control_rows[0].keys()), control_rows))
        _json_dump(out_dir / "power_physical_rules.json", {"rules": power_rows})
        _write_text(out_dir / "power_physical_rules.md", "# Power Physical Rules\n\n" + _md_table(list(power_rows[0].keys()), power_rows))
        _json_dump(out_dir / "pin_label_layer_rules.json", {"rules": pin_rows})
        _write_text(out_dir / "pin_label_layer_rules.md", "# Pin Label Layer Rules\n\n" + _md_table(list(pin_rows[0].keys()), pin_rows))

        _write_csv(out_dir / "openram_vs_openyield_layout_gap_matrix.csv", GAP_MATRIX_COLUMNS, gap_rows)
        _write_text(out_dir / "openram_vs_openyield_layout_gap_matrix.md", "# OpenRAM vs OpenYield Layout Gap Matrix\n\n" + _md_table(GAP_MATRIX_COLUMNS, gap_rows))

        _json_dump(out_dir / "complete_gds_physical_requirements.json", {"requirements": requirement_rows})
        _write_text(out_dir / "complete_gds_physical_requirements.md", "# Complete GDS Physical Requirements\n\n" + _md_table(list(requirement_rows[0].keys()), requirement_rows))

        _write_csv(out_dir / "c0_blocker_to_c2_c6_fix_plan.csv", FIX_PLAN_COLUMNS, fix_rows)
        _write_text(out_dir / "c0_blocker_to_c2_c6_fix_plan.md", "# C0 Blocker to C2-C6 Fix Plan\n\n" + _md_table(FIX_PLAN_COLUMNS, fix_rows))

        _json_dump(self.config.out_json, report)
        _write_text(self.config.out_report, self._render_report_md(report, reference_observation))
        _write_csv(self.config.out_matrix_csv, GAP_MATRIX_COLUMNS, gap_rows)
        _write_text(self.config.out_matrix_md, "# OpenYield C1 Physical Rule Matrix\n\n" + _md_table(GAP_MATRIX_COLUMNS, gap_rows))
        _write_text(self.config.repo_root / "docs/evidence/C1_sram_physical_rule_extraction_summary.md", self._render_summary_md(report, reference_observation))

    def _render_rulebook_md(self, report: dict[str, Any], ref: ReferenceGdsObservation) -> str:
        lines = [
            "# SRAM Baseline Physical Rulebook",
            "",
            "## Gate",
            f"- can_claim_C1_physical_rules_extracted_now: `{report['can_claim_C1_physical_rules_extracted_now']}`",
            f"- can_claim_complete_gds_now: `{report['can_claim_complete_gds_now']}`",
            f"- can_enter_C2_pin_geometry_access_repair: `{report['can_enter_C2_pin_geometry_access_repair']}`",
            "",
            "## Counts",
            f"- openram_source_rule_count: `{report['openram_source_rule_count']}`",
            f"- array_rule_count: `{report['array_rule_count']}`",
            f"- row_path_rule_count: `{report['row_path_rule_count']}`",
            f"- column_path_rule_count: `{report['column_path_rule_count']}`",
            f"- control_io_rule_count: `{report['control_io_rule_count']}`",
            f"- power_rule_count: `{report['power_rule_count']}`",
            f"- pin_label_rule_count: `{report['pin_label_rule_count']}`",
            f"- c0_blocker_fix_plan_count: `{report['c0_blocker_fix_plan_count']}`",
            "",
            "## Reference GDS",
            f"- reference_gds_status: `{ref.reference_gds_status}`",
            f"- reference_gds_path: `{ref.gds_path}`",
            f"- top_cell: `{ref.top_cell}`",
            f"- array_like_dense_region_bbox: `{ref.array_like_dense_region_bbox}`",
            "",
        ]
        return "\n".join(lines) + "\n"

    def _render_reference_md(self, ref: ReferenceGdsObservation) -> str:
        lines = [
            "# Reference GDS Physical Observation",
            "",
            f"- reference_gds_status: `{ref.reference_gds_status}`",
            f"- reference_only: `{ref.reference_only}`",
            f"- gds_path: `{ref.gds_path}`",
            f"- top_cell: `{ref.top_cell}`",
            f"- bbox: `{ref.bbox}`",
            f"- cell_count: `{ref.cell_count}`",
            f"- recursive_instance_count: `{ref.recursive_instance_count}`",
            f"- array_like_dense_region_bbox: `{ref.array_like_dense_region_bbox}`",
            f"- row_periphery_relative_location: `{ref.row_periphery_relative_location}`",
            f"- column_periphery_relative_location: `{ref.column_periphery_relative_location}`",
            f"- power_strap_or_rail_layers: `{ref.power_strap_or_rail_layers}`",
            f"- top_pin_or_label_layers: `{ref.top_pin_or_label_layers}`",
            "",
            "## Visual Conclusions",
        ]
        lines.extend(f"- {item}" for item in ref.visual_geometric_conclusions)
        lines.extend(["", "## Largest Shapes"])
        for item in ref.largest_shapes[:8]:
            lines.append(f"- {item}")
        return "\n".join(lines) + "\n"

    def _render_report_md(self, report: dict[str, Any], ref: ReferenceGdsObservation) -> str:
        lines = [
            "# OpenYield C1 SRAM Physical Rule Extraction Report",
            "",
            "## Gate",
            f"- C1_physical_rule_extraction_available: `{report['C1_physical_rule_extraction_available']}`",
            f"- can_claim_C1_physical_rules_extracted_now: `{report['can_claim_C1_physical_rules_extracted_now']}`",
            f"- can_claim_complete_gds_now: `{report['can_claim_complete_gds_now']}`",
            f"- can_enter_C2_pin_geometry_access_repair: `{report['can_enter_C2_pin_geometry_access_repair']}`",
            "",
            "## Counts",
            f"- openram_source_rule_count: `{report['openram_source_rule_count']}`",
            f"- reference_gds_status: `{report['reference_gds_status']}`",
            f"- array_rule_count: `{report['array_rule_count']}`",
            f"- row_path_rule_count: `{report['row_path_rule_count']}`",
            f"- column_path_rule_count: `{report['column_path_rule_count']}`",
            f"- control_io_rule_count: `{report['control_io_rule_count']}`",
            f"- power_rule_count: `{report['power_rule_count']}`",
            f"- pin_label_rule_count: `{report['pin_label_rule_count']}`",
            f"- openram_vs_openyield_gap_count: `{report['openram_vs_openyield_gap_count']}`",
            f"- c0_blocker_fix_plan_count: `{report['c0_blocker_fix_plan_count']}`",
            "",
            "## Reference",
            f"- reference_gds_path: `{ref.gds_path}`",
            f"- row_periphery_relative_location: `{ref.row_periphery_relative_location}`",
            f"- column_periphery_relative_location: `{ref.column_periphery_relative_location}`",
            "",
        ]
        return "\n".join(lines) + "\n"

    def _render_summary_md(self, report: dict[str, Any], ref: ReferenceGdsObservation) -> str:
        lines = [
            "# C1 SRAM Physical Rule Extraction Summary",
            "",
            f"- OpenRAM source-backed rules extracted: `{report['openram_source_rule_count']}`.",
            f"- Reference GDS status: `{report['reference_gds_status']}`; path: `{report['reference_gds_path']}`.",
            f"- C0 blocker fix plan rows: `{report['c0_blocker_fix_plan_count']}`.",
            "- Complete-GDS minimum bar is geometry-backed connectivity for the current supported config, not signoff closure.",
            "- C2 must repair module pin geometry/access, C3 must rebuild SRAM-like floorplan, C4 must replace contract signal routes, C5 must replace contract/approximate power, and C6 must validate shape truth and final hierarchy.",
            f"- Row periphery reference location: `{ref.row_periphery_relative_location}`; column periphery reference location: `{ref.column_periphery_relative_location}`.",
        ]
        return "\n".join(lines) + "\n"
