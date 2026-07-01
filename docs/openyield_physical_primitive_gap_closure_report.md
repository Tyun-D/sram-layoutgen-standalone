# OpenYield Physical Primitive Gap Closure Report

This pass closes L1 physical-source blockers by contract-backed composition or hardmacro pin-contract freezing. It does not claim module GDS, full SRAM GDS, DRC, LVS, or timing closure.

## Gates

- remaining_L1_blockers_count: `0`
- can_claim_L1_physical_primitives_closed_now: `True`
- can_enter_L2_placement_abutment_rule_closure: `True`
- can_enter_L3_module_gds_generation: `False`
- can_claim_full_openyield_gds_now: `False`

## What Closed

- `nand3` and `and3` now have explicit composition-backed Python physical-source contracts.
- `and2` and `buffer` are promoted from fallback-only to composition-backed generator contracts.
- `enable_path_leaf_gate`, `gated_clock_leaf_gate`, and `control_logic_leaf_gate` are promoted from candidate-SPICE-only to composition-backed physical sources derived from the frozen TIME contracts.
- `decoder_leaf_gate`, `wordline_decoder_leaf_gate`, and `wordline_driver_leaf_gate` are promoted from grouping-only fallback to composition-backed generator contracts.
- `precharge_cell` is treated as hardmacro-backed with pin contract + bbox closed for L1, while geometry refinement is explicitly deferred to L2.

## Remaining Work Moved To L2

- `and2`
- `and3`
- `buffer`
- `control_logic_leaf_gate`
- `decoder_leaf_gate`
- `delay_inv`
- `dff_cell`
- `enable_path_leaf_gate`
- `gated_clock_leaf_gate`
- `inv`
- `nand2`
- `nand3`
- `nand4`
- `nor2`
- `precharge_cell`
- `wordline_decoder_leaf_gate`
- `wordline_driver`
- `wordline_driver_leaf_gate`

## Remaining L1 Blockers

- none
