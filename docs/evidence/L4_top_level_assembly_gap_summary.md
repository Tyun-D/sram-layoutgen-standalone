# L4 Top-Level Assembly Gap Summary

## Current Candidate

- Generated top-level candidate: `/data1/qujh/work/sram_layoutgen_step45_clean/outputs/openyield_top_level_assembly/current_supported_config/openyield_top_level_candidate.gds`
- Top-level GDS sanity: `GDS_PARSED_SANITY_PASSED`
- Top-level bbox: `{'x0': 0.025, 'y0': 0.0, 'x1': 43.716, 'y1': 25.259999999999998, 'width': 43.691, 'height': 25.259999999999998}`

## Hierarchy Export Repair

- The first L4 top-level candidate was not a complete hierarchy export: integrated module tops could still reference missing leaf cells, and same-name wrapper/source cells could collapse into self-reference.
- The repaired L4 exporter now performs complete hierarchical import into the top-level GDS library instead of only writing direct module references.
- Imported module hierarchies are namespaced with module-local prefixes so that same-name leaf cells from different module GDS files cannot overwrite each other.
- Wrapper/source self-reference collisions are redirected to the correct external hierarchy during import.
- Current hierarchy diagnosis for the repaired top-level GDS reports:
  - `missing_referenced_cells_count=0`
  - `self_reference_count=0`
  - `cycle_count=0`

## Instantiated L3 Modules

- Instantiated modules: `row_decoder, dummy_array, bitcell_array, replica_array, precharge, column_mux, wordline_decoder, sense_amp, decoder_gate_cells, wordline_driver, write_driver, wordline_driver_gate_cells, CONTROL_LOGIC, DFF_ROW, DELAY_CHAIN, GATED_CLOCK_PATH, WORDLINE_ENABLE_PATH, PRECHARGE_ENABLE_PATH, SENSE_ENABLE_PATH, WRITE_ENABLE_PATH`
- Candidate geometry modules: `CONTROL_LOGIC, DELAY_CHAIN, DFF_ROW, GATED_CLOCK_PATH, PRECHARGE_ENABLE_PATH, SENSE_ENABLE_PATH, WORDLINE_ENABLE_PATH, WRITE_ENABLE_PATH, decoder_gate_cells, row_decoder, wordline_decoder, wordline_driver_gate_cells`
- Contract pin modules: `CONTROL_LOGIC, DELAY_CHAIN, DFF_ROW, GATED_CLOCK_PATH, PRECHARGE_ENABLE_PATH, SENSE_ENABLE_PATH, WORDLINE_ENABLE_PATH, WRITE_ENABLE_PATH, bitcell_array, decoder_gate_cells, dummy_array, precharge, replica_array, row_decoder, wordline_decoder, wordline_driver_gate_cells`

## Rail Stitch Plan

- Rail plan entries: `2`
- Strategy: module-boundary rails feed a deterministic top-level spine with vertical drops; verification remains deferred to L5.

## Routing Handoff

- Routing handoff entries: `26`
- Status policy: top-level inter-module connections are emitted as routing handoff metadata and remain detailed-routing work for L5.

## L5 Gate

- can_enter_L5_validation: `True`
- remaining_L4_blockers_count: `0`
