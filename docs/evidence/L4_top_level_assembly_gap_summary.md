# L4 Top-Level Assembly Gap Summary

## Current Candidate

- Generated top-level candidate: `/data1/qujh/work/sram_layoutgen_step45_clean/outputs/openyield_top_level_assembly/current_supported_config/openyield_top_level_candidate.gds`
- Top-level GDS sanity: `GDS_PARSED_SANITY_PASSED`
- Top-level bbox: `{'x0': 0.0, 'y0': 0.0, 'x1': 43.715, 'y1': 25.26, 'width': 43.715, 'height': 25.26}`

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
