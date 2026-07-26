# OpenYield Decoder Output Handoff Budget Audit

This is a metadata-only handoff and downstream access budget audit. It does not modify standalone.py, placement, routing, or the GDS writer.

## Summary

- decoder_output_handoff_budget_available: `True`
- can_enter_decoder_generated_block_planning: `True`
- can_enter_physical_decoder_placement: `False`
- can_enter_very_limited_control_row_smoke: `False`

## Level1 Wordline Handoff Summary

| stage | required_tracks | estimated_required_width | available_width | budget_pass |
| --- | --- | --- | --- | --- |
| DEC_1_0 | 8 | 2.0 | 2.0 | True |
| DEC_1_1 | 8 | 2.0 | 2.0 | True |
| DEC_1_2 | 8 | 2.0 | 2.0 | True |
| DEC_1_3 | 8 | 2.0 | 2.0 | True |

## Enable Handoff Summary

```json
{
  "required_tracks": 4,
  "estimated_required_width": 1.2,
  "available_width": 2.0,
  "metadata_budget_pass": true
}
```

## Handoff Windows

| window | source_stage | outputs | targets | bbox | budget_pass |
| --- | --- | --- | --- | --- | --- |
| WORDLINE_OUTPUT_HANDOFF_WINDOW_GROUP_0 | DEC_1_0 | 8 | 8 | (27.0, 0.0)-(29.0, 12.52) | True |
| WORDLINE_OUTPUT_HANDOFF_WINDOW_GROUP_1 | DEC_1_1 | 8 | 8 | (27.0, 12.52)-(29.0, 25.04) | True |
| WORDLINE_OUTPUT_HANDOFF_WINDOW_GROUP_2 | DEC_1_2 | 8 | 8 | (27.0, 25.04)-(29.0, 37.56) | True |
| WORDLINE_OUTPUT_HANDOFF_WINDOW_GROUP_3 | DEC_1_3 | 8 | 8 | (27.0, 37.56)-(29.0, 50.08) | True |
| ENABLE_BUS_HANDOFF_WINDOW | DEC_0_0 | 4 | 4 | (27.0, 0.0)-(29.0, 1.48) | True |

## Consistency Checks

```json
{
  "all_wordline_outputs_have_handoff_budget": true,
  "all_consumed_enable_outputs_have_handoff_budget": true,
  "unused_enable_outputs_not_routed": true,
  "wordline_handoff_budget_pass": true,
  "enable_handoff_budget_pass": true,
  "handoff_windows_available": true,
  "consumer_access_targets_available": true,
  "output_contract_to_handoff_consistent": true,
  "handoff_target_conflict_found": false,
  "physical_routing_proven": false
}
```

## Blockers

- Handoff windows and access targets are metadata proxies, not routed geometry.
- Decoder level1 enable targets do not yet have physical pin-side proof.
- Wordline-driver access targets rely on adapter metadata and do not prove full channel legality.

## Step 6.17 Recommendation

Next, summarize decoder generated-block metadata planning by stitching stage templates, output contracts, and handoff budgets into a single pre-placement planning report.

