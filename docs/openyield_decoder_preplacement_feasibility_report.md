# OpenYield Decoder Pre-Placement Feasibility Audit

This report builds a bounded metadata-only pre-placement feasibility model. It does not create legal placement, routed geometry, or GDS.

## Model Summary

- model_name: `DECODER_CASCADE_PREPLACEMENT_FEASIBILITY_MODEL`
- source_plan: `DECODER_CASCADE_GENERATED_BLOCK_PLAN`
- bounded_preplacement_model_available: `True`
- metadata_stage_packing_consistent: `True`
- can_enter_decoder_preplacement_feasibility: `True`
- can_enter_decoder_physical_prototype: `False`
- can_enter_physical_decoder_placement: `False`
- can_enter_very_limited_control_row_smoke: `False`

## Stage Row Prototypes

| row | stage | level | bbox | metadata_only |
| --- | --- | --- | --- | --- |
| DECODER_PREPLACE_ROW_DEC_0_0 | DEC_0_0 | 0 | (0.0, 0.0)-(44.7275, 1.565) | True |
| DECODER_PREPLACE_ROW_DEC_1_0 | DEC_1_0 | 1 | (0.0, 5.13)-(44.7275, 6.695) | True |
| DECODER_PREPLACE_ROW_DEC_1_1 | DEC_1_1 | 1 | (0.0, 8.26)-(44.7275, 9.825) | True |
| DECODER_PREPLACE_ROW_DEC_1_2 | DEC_1_2 | 1 | (0.0, 11.39)-(44.7275, 12.955) | True |
| DECODER_PREPLACE_ROW_DEC_1_3 | DEC_1_3 | 1 | (0.0, 14.52)-(44.7275, 16.085) | True |

## Spacing / Overlap Checks

```json
{
  "bbox_proxy_overlap_checks": {
    "stage_row_overlap_found": false,
    "stage_row_gap_satisfied": true,
    "bbox_proxy_conflict_found": false,
    "overlap_pairs": [],
    "metadata_only": true
  },
  "handoff_window_overlap_checks": {
    "handoff_window_overlap_found": false,
    "enable_bus_window_overlap_found": false,
    "metadata_only": true
  }
}
```

## Budget Margins

```json
{
  "wordline_handoff_group_count": 4,
  "wordline_outputs": 32,
  "wordline_group_required_width": 2.0,
  "wordline_group_available_width": 2.0,
  "wordline_handoff_budget_pass": true,
  "wordline_handoff_budget_is_tight": true,
  "wordline_handoff_margin": 0.0,
  "wordline_handoff_risk": "high_or_tight",
  "consumed_enable_outputs": 4,
  "unused_enable_outputs": 4,
  "enable_required_width": 1.2,
  "enable_available_width": 2.0,
  "enable_handoff_budget_pass": true,
  "enable_handoff_margin": 0.8,
  "unused_enable_outputs_not_routed": true,
  "physical_routing_proven": false
}
```

## Power / Rail Feasibility

```json
{
  "decoder_power_policy": "local_horizontal_vdd_gnd_only_no_shared_rail",
  "leaf_power_metadata_complete": true,
  "stage_power_policy_available": true,
  "rail_continuity_proven": false,
  "safe_for_shared_rail": false,
  "composite_rail_continuity_proven": false,
  "power_feasibility_metadata_pass": true,
  "power_physical_proven": false,
  "shared_rail_enabled": false
}
```

## Risk Flags

```json
{
  "tight_wordline_budget": true,
  "zero_wordline_budget_margin": true,
  "stage_bbox_is_proxy": true,
  "handoff_windows_are_proxy": true,
  "internal_routing_unproven": true,
  "rail_continuity_unproven": true,
  "level1_enable_target_pin_side_unproven": true,
  "physical_decoder_placement_blocked": true
}
```

## Blockers

- Pre-placement rows are bbox proxies only and are not legal physical placement.
- Wordline handoff budget has zero margin and must be treated as high-risk/tight.
- Composite internal routing remains unproven inside decoder stages.
- Rail continuity and shared-rail safety remain unproven.
- Enable-bus and wordline handoff windows are metadata channels, not routed geometry.
- Level1 enable target physical pin-side proof is still missing.

## Step 6.19 Recommendation

Next, audit whether the tight wordline handoff can be relieved at the metadata level by alternative channel budgeting or stage/output ordering before any decoder physical prototype is attempted.

