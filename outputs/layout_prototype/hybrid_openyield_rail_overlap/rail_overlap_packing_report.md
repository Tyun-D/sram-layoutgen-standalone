# Gate Row Vertical Abutment Report

- old_gds: `/data1/qujh/work/sram_layoutgen_step45_clean/outputs/layout_prototype/hybrid_openyield_rail_abutted/hybrid_openyield_rail_abutted.gds`
- new_gds: `/data1/qujh/work/sram_layoutgen_step45_clean/outputs/layout_prototype/hybrid_openyield_rail_overlap/hybrid_openyield_rail_overlap.gds`
- actual_interrow_rail_gap_um: `0.0`
- same_net_rail_touch_or_overlap_pass: `True`
- diff_net_short_found: `False`
- real_vertical_abutment_pass: `True`

## Notes

- old average intra-row gap is not reconstructed numerically from the previous GDS; the previous compacted result visibly inserted inter-row stitch shapes.
- new gate rows are packed with real GDS bbox x/y abutment and real rail geometry when available.
- same_net power overlap is only applied when real GDS geometry proves safe overlap depth.
- routing still legacy
- gate placement compacted
- routing compaction not yet performed
