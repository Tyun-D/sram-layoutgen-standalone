# OpenYield Decoder Composite Leaf Convention Audit

This is a metadata-only audit for composite decoder leaves built from `gen_nand2` and `gen_inv`. It does not modify placement, routing, standalone.py, or the GDS writer.

## Summary

- recommended_decoder_logic_strategy: `metadata_composite_nand2_inv`
- decoder_composite_leaf_conventions_available: `True`
- pnand3_composite_convention_available: `True`
- and3_composite_convention_available: `True`
- leaf_pin_metadata_complete: `True`
- leaf_power_metadata_complete: `True`
- composite_internal_net_routing_proven: `False`
- composite_rail_continuity_proven: `False`
- can_enter_decoder_generated_block_planning: `True`
- can_enter_physical_decoder_placement: `False`
- can_enter_very_limited_control_row_smoke: `False`

## Leaf Macro Reference

```json
{
  "gen_nand2": {
    "leaf_macro": "gen_nand2",
    "leaf_bbox": {
      "x0": -0.08,
      "y0": -0.08,
      "x1": 0.9575,
      "y1": 1.4000000000000001
    },
    "leaf_width": 1.0375,
    "leaf_height": 1.4800000000000002
  },
  "gen_inv": {
    "leaf_macro": "gen_inv",
    "leaf_bbox": {
      "x0": -0.08,
      "y0": -0.08,
      "x1": 0.7425,
      "y1": 1.4000000000000001
    },
    "leaf_width": 0.8225,
    "leaf_height": 1.4800000000000002
  }
}
```

## Composite Leaf Conventions

| convention | target_logic | internal_nets | leaf_order | pin_side | bbox_proxy | keepout | safe_metadata | safe_physical |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| PNAND3_COMPOSITE_NAND2_INV | pnand3 | ab_n, ab | gen_nand2, gen_inv, gen_nand2 | {"input_side": "west", "output_side": "east", "power_side_vdd": "top", "power_side_gnd": "bottom", "internal_nets_inside_bbox": "required"} | {"bbox_proxy_policy": "horizontal_leaf_chain", "bbox_proxy_width": 3.2975, "bbox_proxy_height": 1.48, "internal_gap": 0.2, "bbox_proxy_is_metadata_only": true} | {"keepout_name": "PNAND3_INTERNAL_KEEPOUT", "target_convention": "PNAND3_COMPOSITE_NAND2_INV", "purpose": "reserve_internal_net_channel", "x0": 0.0, "y0": 0.0, "x1": 3.2975, "y1": 1.48, "reserved_internal_nets": ["ab_n", "ab"], "metadata_only": true, "keepout_enforced_in_layout": false, "physical_routing_proven": false} | True | False |
| AND3_COMPOSITE_NAND2_INV | and3 | ab_n, ab, abc_n | gen_nand2, gen_inv, gen_nand2, gen_inv | {"input_side": "west", "output_side": "east", "power_side_vdd": "top", "power_side_gnd": "bottom", "internal_nets_inside_bbox": "required"} | {"bbox_proxy_policy": "horizontal_leaf_chain", "bbox_proxy_width": 4.32, "bbox_proxy_height": 1.48, "internal_gap": 0.2, "bbox_proxy_is_metadata_only": true} | {"keepout_name": "AND3_INTERNAL_KEEPOUT", "target_convention": "AND3_COMPOSITE_NAND2_INV", "purpose": "reserve_internal_net_channel", "x0": 0.0, "y0": 0.0, "x1": 4.32, "y1": 1.48, "reserved_internal_nets": ["ab_n", "ab", "abc_n"], "metadata_only": true, "keepout_enforced_in_layout": false, "physical_routing_proven": false} | True | False |

## Stage Impact Refresh

```json
{
  "per_stage_gen_inv": 27,
  "per_stage_gen_nand2": 24,
  "per_stage_composite_and3": 8,
  "per_stage_composite_pnand3": 0,
  "per_stage_total_leafs": 51,
  "cascade_total_gen_inv": 135,
  "cascade_total_gen_nand2": 120,
  "cascade_total_composite_and3": 40,
  "cascade_total_leafs": 255,
  "stage_formula": "3x Pinv + 8x AND2 + 8x AND3_COMPOSITE_NAND2_INV"
}
```

## Blockers

- Composite pin and power conventions are available, but internal net routing is still metadata-only.
- Composite rail continuity is not proven, so shared rail remains disabled.
- BBox proxy and keepout are planning aids only, not legal placement proof.
- Physical decoder placement and control-row smoke remain blocked.

## Step 6.13 Recommendation

- Bind these composite leaf conventions into decoder-stage metadata templates next, including per-stage pin slots and internal-net reservation rules.
