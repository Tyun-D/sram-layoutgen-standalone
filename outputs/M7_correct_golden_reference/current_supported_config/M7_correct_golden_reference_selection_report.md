# M7 Correct Golden Reference Selection Report

- uploaded_zip_path: `/data1/qujh/work/sram_layoutgen_step45_clean/external_references/full_layout_collection.zip`
- golden_reference_selected: `True`
- golden_reference_relative_path_in_zip: `full_layout_collection/sram_8x64_wpr4/sram_8x64_wpr4_fd45.complete.gds`
- golden_reference_path: `/data1/qujh/work/sram_layoutgen_step45_clean/outputs/M7_correct_golden_reference/current_supported_config/golden_reference.gds`
- golden_reference_top_cell: `sram_8x64_wpr4_fd45`
- golden_reference_size_bytes: `389826`
- golden_reference_gds_sanity_status: `GDS_PARSED_SANITY_PASSED`
- historical_wrong_reference_path: `/data1/qujh/work/sram_layoutgen_step45_clean/outputs/layout_prototype/hybrid_openyield_rail_overlap/hybrid_openyield_rail_overlap.complete.gds`
- hybrid_openyield_rail_overlap_is_golden: `False`
- new_uploaded_reference_is_golden: `True`

## Selection Basis

- uploaded zip contains multiple layout collections
- current project history targets 8x64_wpr4
- selected candidate is the non-duplicate .complete.gds inside the matching 8x64_wpr4 directory
- candidate score favors complete SRAM-top exports and penalizes debug/integration/architecture/presentation artifacts

## Selection Reasons

- matches current project target 8x64_wpr4
- filename contains complete
- filename contains final/full/top
- filename contains sram
- top cell looks like SRAM top
- contains 8 expected SRAM structure categories
