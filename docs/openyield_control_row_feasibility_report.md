# OpenYield Control Row Feasibility Report

This is a metadata-only feasibility audit. It does not modify standalone.py, routing, or the GDS writer.

## Summary

- addr_width: `5`
- data_width: `4`
- local DFF bbox: `{"x0": 0.0, "y0": -0.0999999999999994, "x1": 2.8599999999999826, "y1": 2.5699999999999843}`
- minimum_no_overlap_pitch_x: `2.8599999999999826`
- recommended_pitch_x_with_margin: `3.0599999999999827`
- pitch_margin_um: `0.2`
- pitch_margin_policy: `conservative_spacing_margin`
- clock_entry_side: `control_side`
- safe_for_control_row_metadata_feasibility: `True`
- can_enter_physical_row_placement: `False`
- can_enter_standalone_control_placement: `False`

## Row Feasibility

| row | bits | pitch_x | row_height | clock_entry_side | consumer | channel_reserved | channel_width_um | physical_routing_proven |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| ADDR_DFF_ROW | 5 | 3.0599999999999827 | 2.6699999999999835 | control_side | DECODER_CASCADE.A[i] | True | 2.0 | False |
| DATA_DFF_ROW | 4 | 3.0599999999999827 | 2.6699999999999835 | control_side | WRITEDRIVER.DIN[i] | True | 2.0 | False |

## Channel Reservations

```json
{
  "clock_channel": {
    "clock_source": "TIME.clk_buf",
    "clock_sink_rows": [
      "ADDR_DFF_ROW",
      "DATA_DFF_ROW"
    ],
    "clock_entry_side": "control_side",
    "clock_channel_reserved": true,
    "clock_channel_width_um": 2.0,
    "clock_channel_is_metadata_only": true,
    "clock_channel_physical_routing_proven": false,
    "clock_tree_generated": false,
    "clock_routing_changed": false,
    "clock_skew_checked": false
  },
  "row_to_decoder_channel": {
    "source_row": "ADDR_DFF_ROW",
    "sink_block": "DECODER_CASCADE",
    "nets": [
      "addr_q[0]",
      "addr_q[1]",
      "addr_q[2]",
      "addr_q[3]",
      "addr_q[4]"
    ],
    "relative_position_hint": "ADDR_DFF_ROW near decoder input side",
    "channel_reserved": true,
    "channel_width_um": 2.0,
    "physical_routing_proven": false
  },
  "row_to_write_driver_channel": {
    "source_row": "DATA_DFF_ROW",
    "sink_block": "WRITEDRIVER",
    "nets": [
      "din_q[0]",
      "din_q[1]",
      "din_q[2]",
      "din_q[3]"
    ],
    "relative_position_hint": "DATA_DFF_ROW near write driver input side",
    "channel_reserved": true,
    "channel_width_um": 2.0,
    "physical_routing_proven": false
  }
}
```

## Blocking Items

- Clock channel is metadata-only; no physical clock route or skew proof exists.
- Row-to-decoder channel is reserved only in metadata; addr_q routing is not physically proven.
- Row-to-write-driver channel is reserved only in metadata; din_q routing is not physically proven.
- Row rail sharing / shared rail policy is still disabled.
- Control-row abutment and integration with surrounding control logic remain unproven.

## Step 6.5 Recommendation

- Next, prove control-row channel usage against decoder/write-driver side geometry and define a physical reservation model before attempting standalone control placement.
