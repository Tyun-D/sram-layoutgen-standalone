# M3F Comparison With M2R And Optimized Reference

- m3r_failure_summary: `M3R review failed/partially failed:
- OpenYield semantics were mostly exported as text labels.
- Physical cells remained layoutgen original cells.
- first_round_openyield_gds_reused_count = 0.
- Optimized layoutgen rail-overlap / power-rail stitching flow was not restored.
- Do not proceed to final validation before restoring optimized layoutgen generation flow.`
- m2r_used_baseline_layoutgen: `True`
- m3r_preserved_m2r_baseline_backbone: `True`
- optimized_reference_name: `hybrid_openyield_rail_overlap`
- optimized_reference_gds: `/data1/qujh/work/sram_layoutgen_step45_clean/outputs/layout_prototype/hybrid_openyield_rail_overlap/hybrid_openyield_rail_overlap.complete.gds`
- optimized_reference_report_found: `True`
- conclusion: `M3F restores the optimized layoutgen rail-overlap / abutment flow and keeps the SRAM-like macro body, unlike M3R's label-heavy baseline-backbone preservation route.`

## M2R Vs Reference

- m2r_width_um: `22.75`
- reference_macro_width_um: `42.77249999999998`
- reference_macro_height_um: `47.34500000000001`
- reference_power_overlap_enabled: `True`
- reference_storage_policy: `alternating_mx`

## M3F Vs M2R

- m2r_macro_width_um: `36.6225`
- m2r_macro_height_um: `45.95`
- m3f_macro_width_um: `42.77249999999998`
- m3f_macro_height_um: `47.34500000000001`
- m2r_gds_size_bytes: `226768`
- m3f_gds_size_bytes: `223892`
- m2r_storage_policy: `all_r0`
- m3f_storage_policy: `alternating_mx`
- m2r_power_overlap_enabled: `False`
- m3f_power_overlap_enabled: `True`

## M3F Vs Optimized Reference

- reference_width_um: `42.77249999999998`
- reference_height_um: `47.34500000000001`
- m3f_width_um: `42.77249999999998`
- m3f_height_um: `47.34500000000001`
- reference_positive_overlap_count: `15`
- m3f_positive_overlap_count: `15`
- reference_vertical_policy: `same_net_power_rail_overlap_packing`
- m3f_vertical_policy: `same_net_power_rail_overlap_packing`
