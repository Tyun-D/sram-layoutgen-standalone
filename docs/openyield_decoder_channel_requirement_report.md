# OpenYield Decoder Channel Requirement Audit

This report propagates the 2.2um wordline channel recommendation as a metadata-only decoder planning requirement. It does not prove legal routing, placement, or floorplan closure.

## Requirement Summary

- requirement_name: `DECODER_WORDLINE_CHANNEL_2P2_REQUIREMENT`
- source_strategy: `metadata_channel_widening_to_2p2`
- base_width: `2.0`
- recommended_width: `2.2`
- required_width: `2.0`
- recommended_margin: `0.2`

## Affected Windows

| window | old_width | new_width | delta | old_margin | new_margin | risk_before | risk_after |
| --- | --- | --- | --- | --- | --- | --- | --- |
| WORDLINE_OUTPUT_HANDOFF_WINDOW_GROUP_0 | 2.0 | 2.2 | 0.2 | 0.0 | 0.2 | tight_zero_margin | pass_low_margin |
| WORDLINE_OUTPUT_HANDOFF_WINDOW_GROUP_1 | 2.0 | 2.2 | 0.2 | 0.0 | 0.2 | tight_zero_margin | pass_low_margin |
| WORDLINE_OUTPUT_HANDOFF_WINDOW_GROUP_2 | 2.0 | 2.2 | 0.2 | 0.0 | 0.2 | tight_zero_margin | pass_low_margin |
| WORDLINE_OUTPUT_HANDOFF_WINDOW_GROUP_3 | 2.0 | 2.2 | 0.2 | 0.0 | 0.2 | tight_zero_margin | pass_low_margin |

## Updated Budget Summary

```json
{
  "base_wordline_channel_width": 2.0,
  "recommended_wordline_channel_width": 2.2,
  "wordline_required_width": 2.0,
  "old_wordline_margin": 0.0,
  "new_wordline_margin": 0.2,
  "old_risk_level": "tight_zero_margin",
  "new_risk_level": "pass_low_margin",
  "recommended_wordline_channel_width_recorded": true
}
```

## Floorplan Compatibility Checks

```json
{
  "stage_row_overlap_found": false,
  "handoff_window_overlap_found": false,
  "enable_bus_window_overlap_found": false,
  "control_keepout_conflict_found": false,
  "bbox_proxy_conflict_found": false,
  "metadata_only": true
}
```

## Control Geometry Compatibility

```json
{
  "control_geometry_window_compatibility_checked": true,
  "decoder_wordline_channel_requires_floorplan_update": true,
  "control_window_metadata_update_required": true,
  "extra_width_required": 0.2,
  "extra_width_available_or_assumed": "unknown",
  "compatibility_status": "requires_parent_floorplan_reservation",
  "safe_for_metadata_requirement_propagation": true,
  "safe_for_physical_floorplan_claim": false,
  "control_window_policy": "metadata_expand_wordline_windows",
  "referenced_windows": [
    "CLOCK_ENTRY_WINDOW",
    "ADDR_TO_DECODER_WINDOW",
    "DATA_TO_WRITEDRIVER_WINDOW",
    "DECODER_INPUT_ANCHOR",
    "WRITEDRIVER_INPUT_ANCHOR",
    "DECODER_CASCADE_ENVELOPE"
  ]
}
```

## Enable Channel Impact

```json
{
  "enable_channel_width": 2.0,
  "enable_required_width": 1.2,
  "enable_margin": 0.8,
  "enable_handoff_budget_pass": true,
  "enable_channel_unchanged": true,
  "unused_enable_outputs_not_routed": true,
  "enable_channel_impact": "none_in_metadata_model"
}
```

## Risk Flags

```json
{
  "metadata_requirement_propagated": true,
  "positive_wordline_margin_available": true,
  "wordline_margin_still_low": true,
  "physical_routing_proven": false,
  "parent_floorplan_reservation_required": true,
  "floorplan_space_proven": false,
  "handoff_windows_are_proxy": true,
  "stage_bbox_is_proxy": true,
  "rail_continuity_unproven": true,
  "physical_decoder_placement_blocked": true
}
```

## Recommended Next Decoder Policy

`record_2p2_wordline_channel_requirement_and_stop_decoder_physical_push`

## Blockers

- The 2.2um channel is only a propagated metadata reservation, not a legal routed channel.
- Broader parent floorplan space for the extra 0.2um is not physically proven.
- Control geometry windows and decoder envelope would need synchronized metadata updates.
- Physical decoder prototype and placement remain blocked even after positive metadata margin is recorded.

## Step 6.21 Recommendation

Next, audit the parent control-row reservation model: determine where the extra 0.2um can be carved out in the broader control/decoder side plan without changing physical placement yet.

