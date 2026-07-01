# OpenYield L2 Placement / Abutment Rule Closure

## Summary

- can_claim_L2_placement_abutment_rules_closed_now: `True`
- can_enter_L3_module_gds_generation: `True`
- remaining_L2_blockers_count: `0`

## Closed Rule Sets

- placement_rule_rows_count: `52`
- abutment_rule_rows_count: `27`
- rail_rule_rows_count: `27`
- orientation_policy_rows_count: `27`
- pin_access_rule_rows_count: `27`
- module_handoff_rows_count: `25`

## Modules That Can Enter L3 Standalone Module GDS

CONTROL_LOGIC, DELAY_CHAIN, DFF_ROW, GATED_CLOCK_PATH, PRECHARGE_ENABLE_PATH, SENSE_ENABLE_PATH, WORDLINE_ENABLE_PATH, WRITE_ENABLE_PATH, bitcell_array, column_mux, decoder_gate_cells, dummy_array, precharge, replica_array, row_decoder, sense_amp, wordline_decoder, wordline_driver, wordline_driver_gate_cells, write_driver

## Modules Deferred Beyond L3

BANK, SRAM_TOP, power_semantics, routing_semantics, timing_semantics

## L2 Decision

L2 is treated as rule closure. Geometry export, module GDS writing, DRC/LVS, and timing closure remain out of scope.
