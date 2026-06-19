# OpenYield Decoder Handoff Relief Audit

This is a metadata-only relief audit for the tight decoder wordline handoff budget. It does not modify placement, routing, standalone.py, or the GDS writer.

## Baseline Wordline Budget

```json
{
  "option_name": "baseline_current_wordline_budget",
  "grouping_policy": "current_8_outputs_per_stage",
  "stage_order_policy": "current_level1_order",
  "tracks_per_group": 8,
  "route_pitch": 0.2,
  "route_margin": 0.2,
  "required_width": 2.0,
  "available_width": 2.0,
  "margin": 0.0,
  "budget_pass": true,
  "risk": "high_or_tight",
  "safe_for_metadata_planning": true,
  "safe_for_physical_routing": false
}
```

## Candidate Width Sweep

| candidate_width | required_width | margin | budget_pass | risk_level |
| --- | --- | --- | --- | --- |
| 2.0 | 2.0 | 0.0 | True | tight_zero_margin |
| 2.2 | 2.0 | 0.2 | True | pass_low_margin |
| 2.4 | 2.0 | 0.4 | True | pass_moderate_margin |
| 2.6 | 2.0 | 0.6 | True | pass_moderate_margin |
| 3.0 | 2.0 | 1.0 | True | pass_moderate_margin |

## Split Grouping Analysis

```json
[
  {
    "option_name": "split_8_into_2x4",
    "grouping_policy": "split_8_into_2x4",
    "tracks_per_subgroup": 4,
    "required_width": 1.2,
    "available_width": 2.0,
    "margin": 0.8,
    "budget_pass": true,
    "risk_level": "pass_moderate_margin",
    "additional_windows_required": true,
    "stage_output_contract_consistency": true,
    "wordline_output_handoff_consistency": true,
    "split_grouping_metadata_possible": true,
    "split_grouping_requires_extra_window_count": true,
    "physical_routing_proven": false
  },
  {
    "option_name": "split_8_into_4x2",
    "grouping_policy": "split_8_into_4x2",
    "tracks_per_subgroup": 2,
    "required_width": 0.8,
    "available_width": 2.0,
    "margin": 1.2,
    "budget_pass": true,
    "risk_level": "pass_moderate_margin",
    "additional_windows_required": true,
    "stage_output_contract_consistency": true,
    "wordline_output_handoff_consistency": true,
    "split_grouping_metadata_possible": true,
    "split_grouping_requires_extra_window_count": true,
    "physical_routing_proven": false
  }
]
```

## Staggered Output Analysis

```json
[
  {
    "option_name": "staggered_output_handoff",
    "tracks_per_window": 4,
    "window_count_increase": 2,
    "required_width": 1.2,
    "available_width": 2.0,
    "margin": 0.8,
    "metadata_budget_pass": true,
    "risk_level": "pass_moderate_margin",
    "requires_output_order_change": false,
    "requires_stage_window_relayout": true,
    "physical_routing_proven": false
  },
  {
    "option_name": "staggered_output_handoff",
    "tracks_per_window": 2,
    "window_count_increase": 4,
    "required_width": 0.8,
    "available_width": 2.0,
    "margin": 1.2,
    "metadata_budget_pass": true,
    "risk_level": "pass_moderate_margin",
    "requires_output_order_change": false,
    "requires_stage_window_relayout": true,
    "physical_routing_proven": false
  }
]
```

## Recommended Strategy

- recommended_handoff_relief_strategy: `metadata_channel_widening_to_2p2`
- recommended_min_wordline_channel_width: `2.2`
- recommended_margin: `0.2`

## Mapping Preservation Checks

```json
{
  "truth_table_binding_preserved": true,
  "output_contracts_preserved": true,
  "wordline_global_mapping_preserved": true,
  "wordline_driver_handoff_preserved": true,
  "unused_enable_outputs_not_routed": true,
  "output_mapping_preserved": true,
  "physical_routing_proven": false
}
```

## Blockers

- All relief options remain metadata-only and do not prove routing legality.
- Widened metadata channel width does not create a legal routed channel by itself.
- Split or staggered windows would require extra planning windows and stage/window relayout metadata.
- Physical decoder prototype remains blocked even when positive metadata margin exists.

## Step 6.20 Recommendation

Next, if the team wants to keep the current semantic grouping, promote the 2.2um metadata channel width requirement into the next decoder planning step and audit whether the broader control-row floorplan can reserve that space.

