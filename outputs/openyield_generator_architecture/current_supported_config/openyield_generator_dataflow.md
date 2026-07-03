# OpenYield Generator Dataflow

OpenYield semantic contracts
        ↓
R1 layout intent
        ↓
CanonicalSramParameterModel
        ↓
PhysicalModuleRegistry
        ↓
Array / row / column / control generators
        ↓
SRAMTopologyFloorplanner
        ↓
WL / BL / control / power routing
        ↓
PinLabelExporter
        ↓
GDSBackend
        ↓
ValidationHookManager

## Stages

### OpenYield semantic contracts

- inputs: `OpenYield netlist semantics; OpenYield module/connection contracts`
- outputs: `R1 layout intent inputs`
- classification: `openyield_origin`

### R1 layout intent

- inputs: `openyield_sram_layout_intent; array/row/column/control/power/pin intent`
- outputs: `generator-consumable semantic/physical contracts`
- classification: `r1_rule_surface`

### CanonicalSramParameterModel

- inputs: `LoadedLayoutIntent`
- outputs: `rows; cols; address widths; pitch requirements`
- classification: `derived_parameter_model`

### PhysicalModuleRegistry

- inputs: `module role map; GDS inventory; generator inventory`
- outputs: `reuse decisions; implementation ownership`
- classification: `reuse_and_binding`

### Array / row / column / control generators

- inputs: `parameter model; path intents; registry`
- outputs: `structure-complete module layouts; alignment boundaries`
- classification: `generator_owned_physical_composition`

### SRAMTopologyFloorplanner

- inputs: `module layouts; topology constraints`
- outputs: `placement_plan; top_bbox; regions`
- classification: `array_centric_floorplan`

### WL / BL / control / power routing

- inputs: `placement_plan; net role map; power intent`
- outputs: `signal/power routes; net_to_shape_map`
- classification: `r4_route_and_power_layer`

### PinLabelExporter

- inputs: `pin intent; routes; placement`
- outputs: `pin shapes; labels; pin report`
- classification: `pin_export_layer`

### GDSBackend

- inputs: `generator-owned hierarchy and pin geometry`
- outputs: `structure_complete_sram_gds`
- classification: `serialization_backend`

### ValidationHookManager

- inputs: `gds; placement; route; pin; power metadata`
- outputs: `sanity/topology/routing/power/pin audits`
- classification: `evidence_and_gate_layer`

## OpenYield Inputs

- Semantic contracts define SRAM function and naming.
- R1 layout intent defines path-group responsibilities and alignment expectations.
- Pin intent exposes top-level pins: clk, csb, web plus addr/din/dout buses.

## R1 Rules

- Each physical wordline WL[i] must correspond to exactly one bitcell row in the supported scope.
- Row path geometry must align to bitcell array row pitch before structure-complete SRAM GDS can exist.
- Entire column path must be anchored on array column pitch, not on standalone wrapper width.
- control router must connect control outputs into row/column/periphery modules through stable bus ownership
- Top-level VDD/GND pins must be exported by a future R4 power planner using real geometry proof.

## Learned From OpenRAM

- Canonical parameter normalization precedes layout generation.
- Array, row path, column path, and control path are distinct generator boundaries.
- Floorplanning and routing are SRAM-specific, not generic top-level patching.
- GDS serialization is separated from geometry construction.

## OpenYield-Specific

- R1 layout intent is the generator contract, not an OpenRAM config mirror.
- OpenYield net names and module physical roles remain visible through net-to-shape mapping.
- Existing candidate assembly artifacts are treated only as reusable metadata or cautionary examples.

## Legacy Candidate Limits

- old top_level_candidate.gds is a non-authoritative legacy artifact and cannot define the new generator architecture
- old candidate-only placement strategy is not promoted into the new floorplanner
- contract-pin-only assumptions remain insufficient for R3 structure-complete or R4 route-backed proof

## R3/R4 To R5 Support

- R3 emits structure-complete hierarchy and instance ownership for later verification intake.
- R4 adds route-backed net, power, and pin evidence needed by R5 validation.
- ValidationHookManager and NetToShapeMapper form the handoff surface for later DRC/LVS/pin audits without claiming closure now.
