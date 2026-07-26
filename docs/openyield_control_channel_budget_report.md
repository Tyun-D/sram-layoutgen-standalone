# OpenYield Control Channel Budget Report

This is a metadata-only channel budget and side-geometry audit. It does not modify standalone.py, routing, or the GDS writer.

## Summary

- addr_width: `5`
- data_width: `4`
- channel_width: `2.0`
- clock_channel_width: `2.0`
- route_pitch: `0.2`
- route_margin: `0.2`
- row_to_decoder_metadata_budget_pass: `True`
- row_to_write_driver_metadata_budget_pass: `True`
- clock_channel_metadata_budget_pass: `True`
- decoder_side_geometry_proven: `False`
- write_driver_side_pin_known: `True`
- physical_routing_proven: `False`
- clock_skew_checked: `False`
- safe_for_channel_budget_metadata: `True`
- can_enter_physical_row_placement: `False`
- can_enter_standalone_control_placement: `False`

## Channel Budgets

| channel | required_tracks | estimated_required_width | available_width | budget_pass | source_side | sink_side | physical_access_proven | physical_routing_proven |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| CLOCK_CHANNEL | 2 | 0.8 | 2.0 | True | control_side | control_facing_row_side | False | False |
| ADDR_TO_DECODER_CHANNEL | 5 | 1.4 | 2.0 | True | row_output_side_toward_decoder | decoder_input_side | False | False |
| DATA_TO_WRITEDRIVER_CHANNEL | 4 | 1.2000000000000002 | 2.0 | True | row_output_side_toward_write_driver | write_driver_input_side | True | False |

## Channel Details

```json
[
  {
    "channel_name": "CLOCK_CHANNEL",
    "source_block": "TIME/control side",
    "sink_block": "ADDR_DFF_ROW + DATA_DFF_ROW",
    "source_side_hint": "control_side",
    "sink_side_hint": "control_facing_row_side",
    "source_pins_or_nets": [
      "clk_buf",
      "future_control_net"
    ],
    "sink_pins_or_nets": [
      "ADDR_DFF_ROW.clk",
      "DATA_DFF_ROW.clk"
    ],
    "channel_width_um": 2.0,
    "required_tracks": 2,
    "estimated_required_width": 0.8,
    "available_width": 2.0,
    "metadata_budget_pass": true,
    "physical_access_proven": false,
    "physical_routing_proven": false,
    "notes": [
      "Known clock net is clk_buf.",
      "One extra future control track is reserved conservatively for gated/control-side clock distribution planning."
    ],
    "known_clock_nets": 1,
    "reserved_future_control_tracks": 1,
    "clock_tree_generated": false,
    "clock_skew_checked": false
  },
  {
    "channel_name": "ADDR_TO_DECODER_CHANNEL",
    "source_block": "ADDR_DFF_ROW",
    "sink_block": "DECODER_CASCADE",
    "source_side_hint": "row_output_side_toward_decoder",
    "sink_side_hint": "decoder_input_side",
    "source_pins_or_nets": [
      "addr_q[0]",
      "addr_q[1]",
      "addr_q[2]",
      "addr_q[3]",
      "addr_q[4]"
    ],
    "sink_pins_or_nets": [
      "A[0]",
      "A[1]",
      "A[2]",
      "A[3]",
      "A[4]"
    ],
    "channel_width_um": 2.0,
    "required_tracks": 5,
    "estimated_required_width": 1.4,
    "available_width": 2.0,
    "metadata_budget_pass": true,
    "physical_access_proven": false,
    "physical_routing_proven": false,
    "notes": [
      "DECODER_CASCADE remains a hierarchical decoder block, not a single hard macro pin-proven leaf.",
      "Decoder side geometry is still metadata-only in this step."
    ],
    "decoder_side_geometry_proven": false,
    "decoder_channel_budget_is_metadata_only": true
  },
  {
    "channel_name": "DATA_TO_WRITEDRIVER_CHANNEL",
    "source_block": "DATA_DFF_ROW",
    "sink_block": "WRITEDRIVER",
    "source_side_hint": "row_output_side_toward_write_driver",
    "sink_side_hint": "write_driver_input_side",
    "source_pins_or_nets": [
      "din_q[0]",
      "din_q[1]",
      "din_q[2]",
      "din_q[3]"
    ],
    "sink_pins_or_nets": [
      "DIN[0]",
      "DIN[1]",
      "DIN[2]",
      "DIN[3]"
    ],
    "channel_width_um": 2.0,
    "required_tracks": 4,
    "estimated_required_width": 1.2000000000000002,
    "available_width": 2.0,
    "metadata_budget_pass": true,
    "physical_access_proven": true,
    "physical_routing_proven": false,
    "notes": [
      "write_driver GDS audit shows DIN/EN on the bottom side and BL/BLB on the top side.",
      "The input-side pin location is known, but the interconnect from DATA_DFF_ROW is still not physically routed."
    ],
    "write_driver_side_pin_known": true,
    "write_driver_channel_physical_route_proven": false
  }
]
```

## Blockers

- Channel budgets are metadata-only; no physical route or via plan is proven.
- Decoder side geometry is not pin-proven at hardcell level.
- Clock skew and real clock tree distribution remain unchecked.
- No row-abutment, rail-sharing, or integrated control-row routing proof exists yet.

## Step 6.6 Recommendation

- Next, bind decoder-side and write-driver-side budget hints to explicit local geometry windows or placement keepouts before any physical control-row placement smoke.
