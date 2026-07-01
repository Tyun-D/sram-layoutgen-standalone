# L1 Physical Primitive Gap Summary

## First-pass Conclusion

- can_claim_L1_physical_primitives_closed_now: `False`
- can_enter_L2_placement_abutment_rule_closure: `False`
- can_enter_L3_module_gds_generation: `False`

## Main Blockers

- `and3:SOURCE_ONLY:OpenYield source exists but no local GDS/generator/fallback physical source is available.`
- `control_logic_leaf_gate:CANDIDATE_SPICE_ONLY:Only candidate SPICE evidence exists; no local physical generator or GDS is available.`
- `enable_path_leaf_gate:CANDIDATE_SPICE_ONLY:Only candidate SPICE evidence exists; no local physical generator or GDS is available.`
- `gated_clock_leaf_gate:CANDIDATE_SPICE_ONLY:Only candidate SPICE evidence exists; no local physical generator or GDS is available.`
- `nand3:SOURCE_ONLY:OpenYield source exists but no local GDS/generator/fallback physical source is available.`

## Needed Evidence Or Generators

- For `nand3` and `and3`: add a local physical source, either replacement GDS, a Python generator, or an explicit compositional fallback that the GDS writer can instantiate as a stable leaf.
- For control/decode leaf groups that remain metadata or candidate-only: freeze whether they decompose into existing local cells or need dedicated hardmacros.
- For primitives that already have GDS but incomplete abutment metadata: close L2 left/right and top/bottom stitching rules rather than rediscovering leaf semantics.
