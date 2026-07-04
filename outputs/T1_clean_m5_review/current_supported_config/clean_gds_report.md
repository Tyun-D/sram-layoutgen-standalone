# T1 Clean Review GDS Report

## Summary

- source_gds_path: `/data1/qujh/work/sram_layoutgen_step45_clean/outputs/M5_openyield_layoutgen_integration/current_supported_config/openyield_layoutgen_integrated_sram.gds`
- clean_gds_path: `/data1/qujh/work/sram_layoutgen_step45_clean/outputs/T1_clean_m5_review/current_supported_config/openyield_layoutgen_integrated_sram_clean_review.gds`
- annotated_debug_gds_path: `/data1/qujh/work/sram_layoutgen_step45_clean/outputs/T1_clean_m5_review/current_supported_config/openyield_layoutgen_integrated_sram_annotated_debug.gds`
- top_cell_name: `openyield_layoutgen_integrated_sram__source_generated`
- gds_sanity_status: `GDS_PARSED_SANITY_PASSED`
- removed_text_count: `74`
- moved_to_debug_layer_count: `0`
- physical_shape_preserved: `True`
- cell_hierarchy_preserved: `True`
- human_klayout_review_required: `True`

## Notes

- Clean review GDS deletes matched M5/OpenYield debug text labels only.
- Annotated debug GDS preserves the original label-bearing view for trace/debug use.
- Label cleanup does not prove OpenYield netlist-to-layout traceability.
