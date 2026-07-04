# OpenYield SRAM LayoutGen Project Status

## 1. Current Correct Goal

基于原 layoutgen 版图生成器，将 OpenYield 的模块、网表语义和连接关系接入真实 SRAM GDS 生成主干，生成 OpenYield-driven layoutgen-based SRAM GDS。

## 2. Current Stage

- current_stage: `M6`
- next_stage: `WAIT_HUMAN_KLAYOUT_REVIEW`
- human_klayout_review_required_every_stage: `True`
- can_enter_next_stage_without_human_review: `False`

## 3. Latest Human Review

- clean GDS only removed debug labels from M5, but did not regenerate the layout;
- generated GDS does not match the user's previous optimized layoutgen result;
- bitcell power rails do not visibly overlap/stitch as expected;
- column mux is not correctly visible/represented;
- SRAM generation lacks explicit parameter specification;
- future GDS generation must be parameter-locked before layout generation.

## 4. M6 Result

- locked_spec_path: `/data1/qujh/work/sram_layoutgen_step45_clean/outputs/M6_layoutgen_spec_reproduce/current_supported_config/SRAM_SPEC.json`
- reproduced_gds_path: `/data1/qujh/work/sram_layoutgen_step45_clean/outputs/M6_layoutgen_spec_reproduce/current_supported_config/layoutgen_optimized_reproduced_sram.gds`
- top_cell_name: `layoutgen_optimized_reproduced_sram`
- gds_sanity_status: `GDS_PARSED_SANITY_PASSED`
- power_rail_overlap_restored: `True`
- column_mux_present: `True`
- reference_comparison_match: `True`

## 5. Next Immediate Task

等待人工 KLayout review `/data1/qujh/work/sram_layoutgen_step45_clean/outputs/M6_layoutgen_spec_reproduce/current_supported_config/layoutgen_optimized_reproduced_sram_clean_review.gds` 与 reference 对比结果；在此之前不进入下一阶段。
