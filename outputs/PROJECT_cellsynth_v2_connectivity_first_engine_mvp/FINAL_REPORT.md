# PASS_OPENYIELD_CELLSYNTH_V2_CONNECTIVITY_FIRST_ENGINE_MVP

## Summary
- Generated cell: `DFF_V2_CONNECTIVITY_BASELINE`
- Golden graph: 22 MOS, 13 nets
- Level1 connectivity: `PASS`
- DRC: `PASS`
- LVS: `PASS`
- PEX: `PEX_UNAVAILABLE`
- Formal SRAM top modified: `false`

## Old 9.1017um2 Failure
The old `DFF_TOPO_SHARED_00_7_TRAIL` is now a negative regression: `ELECTRICALLY_INVALID`.  It extracts only `['NWELL', 'PWELL']` as pins and has disconnected gate/body/source-drain connectivity relative to the golden graph.

## First Valid Cell
- GDS: `/tmp/qujh_delay_chain_scratch/storage_relief_20260725/worktrees/project_mainline_inventory_20260726/outputs/PROJECT_cellsynth_v2_connectivity_first_engine_mvp/15_FIRST_VALID_CELL/DFF_V2_CONNECTIVITY_BASELINE.gds`
- SHA256: `9eae09d28a1f3eac6d00b6fc825f88580e5b62392fa222788dbda0addd4e4183`
- bbox area: `566.9040 um^2`
- extracted MOS: `22`
- extracted pins: `['CLK', 'D', 'Q', 'VDD', 'VSS']`

## Gates
```json
{
  "BODY_TIE_GATE": "PASS",
  "CONTACT_SYNTHESIS_GATE": "PASS",
  "EXTRACTED_TOPOLOGY_FUNCTION_GATE": "SKIPPED_MODEL_WRAPPER_REQUIRED",
  "FIRST_VALID_CELL_DRC_GATE": "PASS",
  "FIRST_VALID_CELL_LVS_GATE": "PASS",
  "FORMULATION_V2_GATE": "PASS",
  "GOLDEN_GRAPH_GATE": "PASS",
  "LAYERED_ROUTER_GATE": "PASS",
  "LEVEL1_CONNECTIVITY_GATE": "PASS",
  "NEGATIVE_REGRESSION_GATE": "PASS",
  "OD_CONTOUR_ENGINE_GATE": "PASS",
  "PIN_SYNTHESIS_GATE": "PASS",
  "SYMBOLIC_CELL_GATE": "PASS",
  "path": "/tmp/qujh_delay_chain_scratch/storage_relief_20260725/worktrees/project_mainline_inventory_20260726/docs/cellsynth_v2/CELLSYNTH_V2_OPTIMIZER_FORMULATION_V2.md"
}
```
