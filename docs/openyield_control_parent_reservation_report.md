# OpenYield Parent Control Reservation Audit

This report records the decoder 2.2um wordline requirement as a parent-level metadata reservation. It does not prove physical floorplan space, legal placement, or routing.

## Parent Reservation Summary

- reservation_name: `PARENT_CONTROL_ROW_DECODER_WORDLINE_2P2_RESERVATION`
- source_requirement: `DECODER_WORDLINE_CHANNEL_2P2_REQUIREMENT`
- extra_width_required: `0.2`
- reservation_policy: `parent_metadata_side_channel_reservation`
- parent_reservation_recorded: `True`

## Affected Parent Windows

| name | type | affected | required_update | old_width | new_width | delta |
| --- | --- | --- | --- | --- | --- | --- |
| CLOCK_ENTRY_WINDOW | parent_control_window | False | False | 2.0 | 2.0 | 0.0 |
| ADDR_TO_DECODER_WINDOW | parent_control_window | True | True | 2.0 | 2.2 | 0.2 |
| DATA_TO_WRITEDRIVER_WINDOW | parent_control_window | False | False | 2.0 | 2.0 | 0.0 |
| DECODER_INPUT_ANCHOR | control_anchor | True | True | None | None | 0.2 |
| WRITEDRIVER_INPUT_ANCHOR | control_anchor | False | False | None | None | 0.0 |
| DECODER_CASCADE_ENVELOPE | decoder_envelope | True | True | 4.0 | 4.2 | 0.2 |
| WORDLINE_OUTPUT_HANDOFF_WINDOW_GROUP_0 | decoder_handoff_window | True | True | 2.0 | 2.2 | 0.2 |
| WORDLINE_OUTPUT_HANDOFF_WINDOW_GROUP_1 | decoder_handoff_window | True | True | 2.0 | 2.2 | 0.2 |
| WORDLINE_OUTPUT_HANDOFF_WINDOW_GROUP_2 | decoder_handoff_window | True | True | 2.0 | 2.2 | 0.2 |
| WORDLINE_OUTPUT_HANDOFF_WINDOW_GROUP_3 | decoder_handoff_window | True | True | 2.0 | 2.2 | 0.2 |
| ENABLE_BUS_HANDOFF_WINDOW | decoder_handoff_window | False | False | None | None | 0.0 |

## Parent Keepout Requirement

```json
[
  {
    "keepout_name": "PARENT_DECODER_WORDLINE_CHANNEL_RESERVATION_2P2",
    "purpose": "reserve_decoder_to_wordlinedriver_metadata_channel",
    "reserved_width": 2.2,
    "extra_width_over_baseline": 0.2,
    "source": "Step 6.20",
    "applies_to": [
      "WORDLINE_OUTPUT_HANDOFF_WINDOW_GROUP_0",
      "WORDLINE_OUTPUT_HANDOFF_WINDOW_GROUP_1",
      "WORDLINE_OUTPUT_HANDOFF_WINDOW_GROUP_2",
      "WORDLINE_OUTPUT_HANDOFF_WINDOW_GROUP_3"
    ],
    "metadata_only": true,
    "keepout_enforced_in_layout": false,
    "physical_routing_proven": false
  }
]
```

## Floorplan Compatibility Checks

```json
{
  "parent_reservation_available": true,
  "parent_reservation_conflict_found": false,
  "decoder_envelope_update_required": true,
  "control_window_update_required": true,
  "clock_window_affected": false,
  "addr_to_decoder_window_affected": true,
  "data_to_writedriver_window_affected": false,
  "dff_row_conflict_found": false,
  "writedriver_anchor_conflict_found": false,
  "physical_floorplan_space_proven": false,
  "parent_floorplan_reservation_required": true,
  "compatibility_status": "metadata_reservation_required_space_unproven"
}
```

## Budget / Margin Summary

```json
{
  "base_wordline_channel_width": 2.0,
  "recommended_wordline_channel_width": 2.2,
  "wordline_required_width": 2.0,
  "old_margin": 0.0,
  "new_margin": 0.2,
  "new_risk_level": "pass_low_margin",
  "margin_still_low": true
}
```

## Risk Flags

```json
{
  "parent_reservation_required": true,
  "physical_parent_space_proven": false,
  "metadata_reservation_only": true,
  "wordline_margin_still_low": true,
  "control_window_metadata_update_required": true,
  "decoder_envelope_metadata_update_required": true,
  "routing_unproven": true,
  "placement_unproven": true,
  "shared_rail_disabled": true,
  "physical_decoder_placement_blocked": true
}
```

## Recommended Parent Policy

`record_parent_2p2_wordline_reservation_and_close_decoder_metadata`

## Blockers

- Parent reservation is metadata-only and does not prove physical floorplan space.
- ADDR_TO_DECODER_WINDOW and DECODER_CASCADE_ENVELOPE need synchronized metadata updates before any later physical planning step.
- Clock/data-side windows remain logically unaffected but are still unproven as physical channels.
- Decoder physical prototype and placement remain blocked.

## Step 6.22 Recommendation

Next, close decoder metadata and pivot to remaining TIME/control subblocks, unless the project explicitly wants to open a broader parent floorplan reservation study.

