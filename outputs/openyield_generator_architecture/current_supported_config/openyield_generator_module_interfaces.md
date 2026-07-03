# OpenYield Generator Module Interfaces

## OpenYieldIntentLoader

### Inputs

{
  "openyield_sram_layout_intent.json": "canonical parameters and supported scope",
  "array_topology_contract": "array role and pitch semantics",
  "row_path_intent": "row path responsibilities",
  "column_path_intent": "column path responsibilities",
  "control_path_intent": "control path responsibilities",
  "power_intent": "VDD/GND ownership and stitching expectations",
  "pin_intent": "top-level and internal pin naming contracts"
}

### Outputs

{
  "LoadedLayoutIntent": {
    "canonical_parameters": "list of parameter definitions from R1",
    "path_intents": [
      "array",
      "row",
      "column",
      "control"
    ],
    "power_intent": "module power summary and rail expectations",
    "pin_intent": "IO/control/power pin naming contracts"
  }
}

### Notes

- This is the only generator front door.
- No OpenRAM config parsing is allowed here.

## CanonicalSramParameterModel

### Inputs

{
  "LoadedLayoutIntent": "normalized R1 intent bundle"
}

### Outputs

{
  "rows": 4,
  "cols": 4,
  "word_size": 4,
  "num_words": 4,
  "words_per_row": 1,
  "column_mux_ratio": 1,
  "address_width": 2,
  "row_address_width": 2,
  "column_address_width": 0,
  "physical_pitch_requirements": {
    "row_pitch": "owned by BitcellArrayPhysicalGenerator output",
    "column_pitch": "owned by BitcellArrayPhysicalGenerator output"
  }
}

### Notes

- Model must stay parameterized beyond the 4x4 baseline.

## PhysicalModuleRegistry

### Inputs

{
  "module_to_physical_role_map": "R1 physical role ownership",
  "module_gds_inventory": "existing GDS and metadata inventory",
  "generator_inventory": "existing standalone generator inventory"
}

### Outputs

{
  "available_hardmacros": [
    "column_mux",
    "precharge",
    "sense_amp",
    "wordline_driver",
    "write_driver"
  ],
  "candidate_geometry_modules": [
    "CONTROL_LOGIC",
    "DELAY_CHAIN",
    "DFF_ROW",
    "GATED_CLOCK_PATH",
    "PRECHARGE_ENABLE_PATH",
    "SENSE_ENABLE_PATH",
    "WORDLINE_ENABLE_PATH",
    "WRITE_ENABLE_PATH",
    "decoder_gate_cells",
    "row_decoder",
    "wordline_decoder",
    "wordline_driver_gate_cells"
  ],
  "modules_requiring_new_generator": [
    "bitcell_array_wrapper",
    "row_periphery_composer",
    "column_periphery_composer",
    "control_periphery_composer",
    "sram_topology_floorplanner",
    "wordline_router",
    "bitline_router",
    "control_router",
    "power_planner",
    "pin_label_exporter",
    "net_to_shape_mapper",
    "instance_mapper"
  ],
  "module_physical_roles": {
    "bitcell_array": "ARRAY_CORE",
    "dummy_array": "ARRAY_DUMMY",
    "replica_array": "ARRAY_REPLICA",
    "row_decoder": "ROW_DECODER",
    "wordline_decoder": "ROW_DECODER",
    "decoder_gate_cells": "ROW_DECODER",
    "wordline_driver": "WORDLINE_DRIVER",
    "wordline_driver_gate_cells": "WORDLINE_DRIVER",
    "column_mux": "COLUMN_MUX",
    "sense_amp": "SENSE_AMP",
    "write_driver": "WRITE_DRIVER",
    "precharge": "COLUMN_PRECHARGE",
    "DELAY_CHAIN": "DELAY_CHAIN",
    "PRECHARGE_ENABLE_PATH": "ENABLE_PATH",
    "SENSE_ENABLE_PATH": "ENABLE_PATH",
    "WRITE_ENABLE_PATH": "ENABLE_PATH",
    "WORDLINE_ENABLE_PATH": "ENABLE_PATH",
    "GATED_CLOCK_PATH": "CLOCK_PATH",
    "DFF_ROW": "DFF_ROW",
    "CONTROL_LOGIC": "CONTROL_LOGIC"
  }
}

### Notes

- Registry outputs drive reuse decisions and implementation priority.

## SRAMTopologyFloorplanner

### Inputs

{
  "CanonicalSramParameterModel": "canonical rows/cols/mux/pitch requirements",
  "ArrayTopologyContract": "array wrapper constraints",
  "RowPathIntent": "row path constraints",
  "ColumnPathIntent": "column path constraints",
  "ControlPathIntent": "control path constraints",
  "PhysicalModuleRegistry": "module implementation availability"
}

### Outputs

{
  "array_region": "ARRAY_CORE and boundary wrapper region",
  "row_periphery_region": "decoder and WL driver region",
  "column_periphery_region": "precharge/mux/sense/write region",
  "control_region": "control logic and timing region",
  "power_region": "reserved top-level power channels",
  "top_bbox": "generator-owned final bounding box",
  "placement_plan": "region-level and instance-level placement intent"
}

### Notes

- Floorplanner owns adjacency and reserved channels, not just XY placement.

## R3 Generators

### Inputs

{
  "BitcellArrayPhysicalGenerator": "array wrapper composition rules",
  "RowPeripheryPhysicalGenerator": "row periphery composition rules",
  "ColumnPeripheryPhysicalGenerator": "column periphery composition rules",
  "ControlPeripheryPhysicalGenerator": "control region composition rules"
}

### Outputs

{
  "structure_complete_module_layouts": "module-level geometry bundles",
  "placement-ready module geometry": "placed region-local module geometry",
  "pitch-aligned boundaries": "array/row/column alignment surfaces"
}

### Notes

- R3 stops at structure-complete prototype geometry, before full routing closure.

## R4 Routers

### Inputs

{
  "WordlineRouter": "row path to array routing ownership",
  "BitlineRouter": "column path to array routing ownership",
  "ControlRouter": "control spine routing ownership",
  "PowerPlanner": "power distribution ownership"
}

### Outputs

{
  "wordline_routes": "WL driver to array row routes",
  "bitline_routes": "BL/BR and column-path routes",
  "control_routes": "control and timing routes",
  "power_routes": "VDD/GND distribution routes",
  "net_to_shape_map": "semantic net to geometry mapping"
}

### Notes

- R4 adds routing, power, and pin proof on top of the R3 structure.

## PinLabelExporter

### Inputs

{
  "pin_intent": "top-level IO/control/power naming contract",
  "routes": "route-backed geometry or pin shapes"
}

### Outputs

{
  "top_level_pin_shapes": "geometry-backed pin shapes",
  "top_level_labels": "text labels aligned to pin intent",
  "pin_export_report": "pin coverage and naming audit"
}

### Notes

- Pin export must not rely on contract-only placeholders once R4 is implemented.

## GDSBackend

### Inputs

{
  "generator_layout_objects": "generator-owned hierarchy objects",
  "pin_shapes": "final pin geometry"
}

### Outputs

{
  "structure_complete_sram_gds": "R3 or R4 GDS artifact depending on implemented stage"
}

### Notes

- Must reuse the project GDS backend instead of OpenRAM save().

## ValidationHookManager

### Inputs

{
  "generated_artifacts": "placement, routes, pins, gds, evidence metadata"
}

### Outputs

{
  "sanity_report": "basic structural checks",
  "topology_validation_report": "region and hierarchy checks",
  "routing_audit": "route coverage status",
  "power_audit": "VDD/GND distribution status",
  "pin_audit": "pin naming and reachability status"
}

### Notes

- Validation hooks must preserve False signoff claims until later evidence exists.
