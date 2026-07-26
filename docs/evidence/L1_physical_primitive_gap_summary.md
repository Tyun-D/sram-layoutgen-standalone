# L1 Physical Primitive Gap Summary

## First-round Blockers

- `nand3` and `and3` were `SOURCE_ONLY`.
- `enable_path_leaf_gate`, `gated_clock_leaf_gate`, and `control_logic_leaf_gate` were `CANDIDATE_SPICE_ONLY`.
- `and2`, `buffer`, and decoder/driver leaf groups were fallback-only without a promoted composition source.
- `precharge_cell` still carried a hardmacro pin-contract readiness gap.

## This-pass Closure

1. `nand3` is closed by a composition-backed Python source contract using a `nand4`-derived generator policy with one input tied high.
2. `and3` is closed by explicit `nand3 + inv` composition policy.
3. `and2` and `buffer` are promoted to explicit composition-backed generator contracts.
4. `enable_path_leaf_gate`, `gated_clock_leaf_gate`, and `control_logic_leaf_gate` are closed by TIME-contract-derived composition sources rather than candidate SPICE only.
5. `precharge_cell` is closed as L1-ready through hardmacro GDS + pin contract + bbox, with geometry refinement deferred to L2.

## What Moves To L2

- Abutment/orientation rules for composition-backed leaves.
- Rail stitch and local row-packing rules for control/decode paths.
- Precharge pin-geometry refinement and detailed rail extraction.

## Why L2 Is Now Allowed

- remaining_L1_blockers_count: `0`
- can_enter_L2_placement_abutment_rule_closure: `True`
- Every required primitive in the current L0-supported scope now has an explicit local physical source: existing GDS, hardmacro GDS, Python generator, or composition-backed Python generator contract.

## Why L3 Is Still Blocked

- Module GDS composition, row packing, abutment, rail stitching, and final geometry proof remain L2/L3 work.
- This pass does not claim full OpenYield GDS, DRC, LVS, or timing closure.
