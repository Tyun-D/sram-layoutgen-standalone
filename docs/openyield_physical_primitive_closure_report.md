# OpenYield Physical Primitive Closure Report

This is the first L1 pass. It inventories leaf physical evidence but does not modify placement, routing, or module GDS generation.

## Gates

- primitive_rows_count: `27`
- module_dependency_rows_count: `25`
- can_claim_L1_physical_primitives_closed_now: `False`
- can_enter_L2_placement_abutment_rule_closure: `False`
- can_enter_L3_module_gds_generation: `False`
- can_claim_full_openyield_gds_now: `False`

## Required Answers

1. L0 contracts derive `27` primitives.
2. Existing GDS primitives: `bitcell, dff_cell, dummy_cell, replica_cell, sense_amp, write_driver, column_mux, delay_inv, inv, nand2, precharge_cell, wordline_driver`.
3. Python generator primitives: `nand4, nor2`.
4. Candidate SPICE only primitives: `control_logic_leaf_gate, enable_path_leaf_gate, gated_clock_leaf_gate`.
5. OpenYield source only primitives: `and3, nand3`.
6. Metadata/fallback only primitives: `and2, buffer, decoder_leaf_gate, wordline_decoder_leaf_gate, wordline_driver_leaf_gate`.
7. Missing physical source primitives: `nor3, or2, or3`.
8. Missing pin/bbox/rail completeness: `and2, and3, buffer, control_logic_leaf_gate, decoder_leaf_gate, enable_path_leaf_gate, gated_clock_leaf_gate, nand3, nor3, or2, or3, wordline_decoder_leaf_gate, wordline_driver_leaf_gate`.
9. Missing abutment rule closure: `and2, and3, buffer, column_mux, control_logic_leaf_gate, decoder_leaf_gate, delay_inv, dff_cell, enable_path_leaf_gate, gated_clock_leaf_gate, inv, nand2, nand3, nand4, nor2, nor3, or2, or3, precharge_cell, sense_amp, wordline_decoder_leaf_gate, wordline_driver, wordline_driver_leaf_gate, write_driver`.
10. Standalone module GDS now: `DELAY_CHAIN, DFF_ROW, bitcell_array, column_mux, dummy_array, sense_amp, wordline_driver, write_driver`.
11. Blocked modules: `BANK, CONTROL_LOGIC, GATED_CLOCK_PATH, PRECHARGE_ENABLE_PATH, SENSE_ENABLE_PATH, SRAM_TOP, WORDLINE_ENABLE_PATH, WRITE_ENABLE_PATH, decoder_gate_cells, power_semantics, precharge, replica_array, routing_semantics, row_decoder, timing_semantics, wordline_decoder, wordline_driver_gate_cells`.
12. L2 still needs: `and3:SOURCE_ONLY:OpenYield source exists but no local GDS/generator/fallback physical source is available.; control_logic_leaf_gate:CANDIDATE_SPICE_ONLY:Only candidate SPICE evidence exists; no local physical generator or GDS is available.; enable_path_leaf_gate:CANDIDATE_SPICE_ONLY:Only candidate SPICE evidence exists; no local physical generator or GDS is available.; gated_clock_leaf_gate:CANDIDATE_SPICE_ONLY:Only candidate SPICE evidence exists; no local physical generator or GDS is available.; nand3:SOURCE_ONLY:OpenYield source exists but no local GDS/generator/fallback physical source is available.`.
13. Can enter L2: `False`.
14. Can enter L3: `False`.
