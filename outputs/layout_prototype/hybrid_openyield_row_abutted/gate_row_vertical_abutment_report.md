# Gate Row Vertical Abutment Report

- old_gds: `/data1/qujh/work/sram_layoutgen_step45_clean/outputs/layout_prototype/hybrid_openyield_compacted/hybrid_openyield_compacted.gds`
- new_gds: `/data1/qujh/work/sram_layoutgen_step45_clean/outputs/layout_prototype/hybrid_openyield_row_abutted/hybrid_openyield_row_abutted.gds`
- old_has_extra_interrow_power_stripe: `True`
- new_has_extra_interrow_power_stripe: `False`
- old_vertical_gap_um: `None`
- new_vertical_gap_um: `0.0`
- row_count: `16`
- rows_with_R0: `8`
- rows_with_MX: `8`
- rail_boundary_matches: `15`
- rail_boundary_mismatches: `0`
- vertical_abutment_pass: `True`

## Notes

- old average intra-row gap is not reconstructed numerically from the previous GDS; the previous compacted result visibly inserted inter-row stitch shapes.
- new gate rows are packed with x_next = x_current + cell_width.
- routing still legacy
- gate placement compacted
- routing compaction not yet performed
