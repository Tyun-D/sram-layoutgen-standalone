# OpenYield DFF Array Placement Report

This is a metadata-only placement plan. It does not change standalone.py, routing, or the GDS writer.

## Summary

- address DFF count: `5`
- data DFF count: `4`
- placement count: `9`
- safe_for_physical_mapping: `True`
- safe_for_shared_rail: `False`
- row_placement_ready: `metadata_only`
- dff_array_can_enter_metadata_placement: `True`
- dff_array_can_enter_standalone_placement: `False`
- pitch_x_legal_for_bbox: `False`
- overlap_risk_if_physically_placed: `True`

## BBox Estimate

- local DFF bbox: `{"x0": 0.0, "y0": -0.0999999999999994, "x1": 2.8599999999999826, "y1": 2.5699999999999843}`
- plan bbox: `{"x0": 0.0, "y0": 0.0, "x1": 6.859999999999983, "y1": 6.339999999999967, "width": 6.859999999999983, "height": 6.339999999999967}`

## Example Placements

| instance | array | bit | x | y | orientation | d | clk | q | consumer |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Xaddr_dff_b0 | ADDR_DFF | 0 | 0.0 | 0.0 | R0 | addr[0] | clk_buf | addr_q[0] | DECODER_CASCADE.A[0] |
| Xaddr_dff_b1 | ADDR_DFF | 1 | 1.0 | 0.0 | R0 | addr[1] | clk_buf | addr_q[1] | DECODER_CASCADE.A[1] |
| Xaddr_dff_b2 | ADDR_DFF | 2 | 2.0 | 0.0 | R0 | addr[2] | clk_buf | addr_q[2] | DECODER_CASCADE.A[2] |
| Xaddr_dff_b3 | ADDR_DFF | 3 | 3.0 | 0.0 | R0 | addr[3] | clk_buf | addr_q[3] | DECODER_CASCADE.A[3] |
| Xaddr_dff_b4 | ADDR_DFF | 4 | 4.0 | 0.0 | R0 | addr[4] | clk_buf | addr_q[4] | DECODER_CASCADE.A[4] |
| Xdata_dff_b0 | DATA_DFF | 0 | 0.0 | 3.6699999999999835 | R0 | din[0] | clk_buf | din_q[0] | WRITEDRIVER.DIN[0] |

## Notes

- This report is metadata-only and does not connect the plan to standalone placement.
- No routing, clock tree, shared rail, or row abutment proof is performed here.
- A supplied pitch_x smaller than the DFF bbox width is still reported, but flagged as a physical overlap risk.
