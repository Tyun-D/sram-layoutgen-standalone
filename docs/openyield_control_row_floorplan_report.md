# OpenYield Control Row Floorplan Report

This is a metadata-only control-row floorplan. It does not modify standalone.py, routing, or the GDS writer.

## Summary

- addr_width: `5`
- data_width: `4`
- local DFF bbox: `{"x0": 0.0, "y0": -0.0999999999999994, "x1": 2.8599999999999826, "y1": 2.5699999999999843}`
- recommended pitch_x: `2.8599999999999826`
- recommended row height: `2.6699999999999835`
- recommended row gap: `2.6699999999999835`
- recommended_pitch_avoids_bbox_overlap: `True`
- selected pitch policy: `bbox_width`
- selected pitch_x: `2.8599999999999826`
- placement count: `9`
- physical pitch legality: `True`
- overlap risk: `False`
- safe_for_metadata_floorplan: `True`
- can_enter_physical_row_placement: `False`
- can_enter_standalone_control_placement: `False`

## Row Summaries

| row | array | bits | clock | input | output | consumer | hint | origin | pitch_x | row_height |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| ADDR_DFF_ROW | ADDR_DFF | 5 | clk_buf | addr[i] | addr_q[i] | DECODER_CASCADE.A[i] | near_decoder_input_side | (0.0, 0.0) | 2.8599999999999826 | 2.6699999999999835 |
| DATA_DFF_ROW | DATA_DFF | 4 | clk_buf | din[i] | din_q[i] | WRITEDRIVER.DIN[i] | near_write_driver_input_side | (0.0, 5.339999999999967) | 2.8599999999999826 | 2.6699999999999835 |

## Clock Domain Metadata

```json
{
  "clock_source": "TIME.clk_buf",
  "clock_sink_rows": [
    "ADDR_DFF_ROW",
    "DATA_DFF_ROW"
  ],
  "clock_tree_generated": false,
  "clock_routing_changed": false,
  "clock_skew_checked": false
}
```

## Relative Placement Hints

- ADDR_DFF_ROW should be placed between TIME/control and DECODER_CASCADE.
- DATA_DFF_ROW should be placed between TIME/control and WRITEDRIVER input side.
- Clock input should enter both rows from the control/TIME side.
- No physical routing is generated in this step.

## Pitch Regression Check

- pitch_x=1.0 legal: `False`
- pitch_x=1.0 overlap risk: `True`

## Example Placements

| instance | row | bit | x | y | orientation | d | clk | q | consumer | physical_pitch_legal |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Xaddr_dff_b0 | ADDR_DFF_ROW | 0 | 0.0 | 0.0 | R0 | addr[0] | clk_buf | addr_q[0] | DECODER_CASCADE.A[0] | True |
| Xaddr_dff_b1 | ADDR_DFF_ROW | 1 | 2.8599999999999826 | 0.0 | R0 | addr[1] | clk_buf | addr_q[1] | DECODER_CASCADE.A[1] | True |
| Xaddr_dff_b2 | ADDR_DFF_ROW | 2 | 5.719999999999965 | 0.0 | R0 | addr[2] | clk_buf | addr_q[2] | DECODER_CASCADE.A[2] | True |
| Xaddr_dff_b3 | ADDR_DFF_ROW | 3 | 8.579999999999949 | 0.0 | R0 | addr[3] | clk_buf | addr_q[3] | DECODER_CASCADE.A[3] | True |
| Xaddr_dff_b4 | ADDR_DFF_ROW | 4 | 11.43999999999993 | 0.0 | R0 | addr[4] | clk_buf | addr_q[4] | DECODER_CASCADE.A[4] | True |
| Xdata_dff_b0 | DATA_DFF_ROW | 0 | 0.0 | 5.339999999999967 | R0 | din[0] | clk_buf | din_q[0] | WRITEDRIVER.DIN[0] | True |

## Notes

- This step stays metadata-only and does not place control rows into standalone.
- Recommended pitch uses the DFF bbox width by default because that is the minimum conservative no-overlap estimate available here.
- Clock domain metadata records source and sink rows only; no clock tree, routing, or skew proof is claimed.
- Row abutment, rail sharing, and integrated control routing remain unproven.
