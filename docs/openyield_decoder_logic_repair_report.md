# OpenYield Decoder Logic Repair Audit

This is a metadata-only audit for missing PNAND3 / AND3 decoder leaves. It does not modify placement, routing, standalone.py, or the GDS writer.

## Summary

- direct PNAND3 exists: `False`
- direct AND3 exists: `False`
- decoder_logic_repair_options_available: `True`
- recommended_decoder_logic_strategy: `metadata_composite_nand2_inv`
- pnand3_composite_metadata_available: `True`
- and3_composite_metadata_available: `True`
- gen_nand4_proxy_only: `True`
- gen_nand4_safe_for_physical_substitution: `False`
- can_enter_decoder_generated_block_planning: `True`
- can_enter_physical_decoder_placement: `False`
- can_enter_very_limited_control_row_smoke: `False`

## Repair Options

| option | status | safe_metadata | safe_physical | logic_equivalence | required_cells | notes |
| --- | --- | --- | --- | --- | --- | --- |
| direct_pnand3_and3_macro | unavailable | False | False | None | {} | No direct local gen_nand3 / PNAND3 hard macro was found in technology/freepdk45/gds_lib or sp_lib.; No direct local AND3 hard macro was found either. |
| gen_nand4_as_pnand3_proxy | limited_proxy_only | limited_proxy_only | False | None | {} | A 4-input NAND could serve only as an upper-bound metadata proxy if an unused input is tied high.; That unused-input tie policy is not proven in local GDS/SPICE metadata.; Missing label/power metadata keeps this option out of physical placement. |
| pnand3_from_nand2_inv | metadata_composite_candidate | True | False | True | {"gen_nand2": 2, "gen_inv": 1} | Metadata proof uses ab_n=NAND2(A,B), ab=INV(ab_n), z=NAND2(ab,C), so z=~(A&B&C).; This proves logical equivalence only; it does not prove internal routing, legal row packing, or power-rail legality. |
| and3_from_nand2_inv | metadata_composite_candidate | True | False | True | {"gen_nand2": 2, "gen_inv": 2} | Metadata proof uses ab_n=NAND2(A,B), ab=INV(ab_n), abc_n=NAND2(ab,C), z=INV(abc_n).; This proves logical equivalence only; it does not prove internal routing, legal row packing, or power-rail legality. |
| keep_and3_generated_logic_unresolved | fallback | True | False | None | {} | This keeps decoder planning conservative and avoids overclaiming any leaf repair.; It preserves row-rule metadata but blocks physical decoder smoke until macro repair/proof exists. |

## Stage / Cascade Count Impact

| option | per_stage_gen_inv | per_stage_gen_nand2 | per_stage_gen_nand4 | per_stage_proxy_cell_count | cascade_gen_inv | cascade_gen_nand2 | cascade_gen_nand4 | cascade_proxy_cell_count |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| direct_pnand3_and3_macro | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| gen_nand4_as_pnand3_proxy | 19 | 0 | 8 | 27 | 95 | 0 | 40 | 135 |
| pnand3_from_nand2_inv | 19 | 24 | 0 | 43 | 95 | 120 | 0 | 215 |
| and3_from_nand2_inv | 27 | 24 | 0 | 51 | 135 | 120 | 0 | 255 |
| keep_and3_generated_logic_unresolved | 11 | 8 | 0 | 27 | 55 | 40 | 0 | 135 |

## Blocker Audit

| option | pin blockers | power blockers | internal net blockers | rail blockers | unused input blockers | physical blockers |
| --- | --- | --- | --- | --- | --- | --- |
| direct_pnand3_and3_macro | - | - | - | - | - | physical_row_placement_unproven; internal_routing_unproven; shared_rail_forbidden; direct_leaf_macro_missing |
| gen_nand4_as_pnand3_proxy | gen_nand4_label_metadata_incomplete | gen_nand4_power_metadata_incomplete | unused_input_logic_polarity_unproven; proxy_internal_net_routing_unproven | power_metadata_incomplete; rail_continuity_not_proven; shared_rail_not_allowed_for_decoder_generated_logic | unused_input_tie_policy_not_proven | physical_row_placement_unproven; internal_routing_unproven; shared_rail_forbidden |
| pnand3_from_nand2_inv | - | - | composite_internal_nets_need_routing_convention; composite_row_packing_unproven | rail_continuity_not_proven; shared_rail_not_allowed_for_decoder_generated_logic; rail_continuity_not_proven; shared_rail_not_allowed_for_decoder_generated_logic | - | physical_row_placement_unproven; internal_routing_unproven; shared_rail_forbidden |
| and3_from_nand2_inv | - | - | composite_internal_nets_need_routing_convention; composite_row_packing_unproven | rail_continuity_not_proven; shared_rail_not_allowed_for_decoder_generated_logic; rail_continuity_not_proven; shared_rail_not_allowed_for_decoder_generated_logic | - | physical_row_placement_unproven; internal_routing_unproven; shared_rail_forbidden |
| keep_and3_generated_logic_unresolved | - | - | pnand3_leaf_unresolved | - | - | physical_row_placement_unproven; internal_routing_unproven; shared_rail_forbidden; decoder_logic_leaf_still_missing |

## Blockers

- Direct PNAND3 / AND3 local hard macros are still absent.
- gen_nand4 remains only a limited metadata proxy because label, power, polarity, and unused-input tie proof are incomplete.
- Composite gen_nand2 + gen_inv logic equivalence is metadata-proven, but physical row routing and rail legality are still unproven.
- Decoder generated-block planning can continue, but physical decoder placement and control-row smoke remain blocked.

## Step 6.12 Recommendation

- Refine composite decoder-leaf metadata next: add internal-net and pin-side conventions for the gen_nand2/gen_inv composition before any placement-oriented decoder prototype.
