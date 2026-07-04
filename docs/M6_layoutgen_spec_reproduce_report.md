# M6 Layoutgen Spec Reproduce Report

## Summary

- status_file_read: `True`
- status_file_updated: `True`
- locked_spec_available: `True`
- top_cell_name: `layoutgen_optimized_reproduced_sram`
- layoutgen_optimized_reproduced_sram_gds_path: `/data1/qujh/work/sram_layoutgen_step45_clean/outputs/M6_layoutgen_spec_reproduce/current_supported_config/layoutgen_optimized_reproduced_sram.gds`
- layoutgen_optimized_reproduced_sram_clean_review_gds_path: `/data1/qujh/work/sram_layoutgen_step45_clean/outputs/M6_layoutgen_spec_reproduce/current_supported_config/layoutgen_optimized_reproduced_sram_clean_review.gds`
- layoutgen_optimized_reproduced_sram_spec_annotated_gds_path: `/data1/qujh/work/sram_layoutgen_step45_clean/outputs/M6_layoutgen_spec_reproduce/current_supported_config/layoutgen_optimized_reproduced_sram_spec_annotated.gds`
- gds_sanity_status: `GDS_PARSED_SANITY_PASSED`
- power_rail_overlap_restored: `True`
- column_mux_present: `True`
- reference_comparison_match: `True`

## Notes

- M6 regenerates the layout from a parameter-locked standalone layoutgen path.
- M6 does not continue the M5 text-label semantic export flow.
- M6 does not claim DRC/LVS/signoff.
