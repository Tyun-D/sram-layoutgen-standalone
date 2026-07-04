# OpenYield SRAM LayoutGen Project Status

## 1. Current Correct Goal

基于原 layoutgen 版图生成器，将 OpenYield 的模块、网表语义和连接关系接入真实 SRAM GDS 生成主干，生成 OpenYield-driven layoutgen-based SRAM GDS。

## 2. Current Stage

- current_stage: `M6R`
- next_stage: `WAIT_HUMAN_KLAYOUT_REVIEW`
- human_klayout_review_required_every_stage: `True`
- can_enter_next_stage_without_human_review: `False`

## 3. Latest Human Review

- Generated GDS still looks like previous non-overlap result.
- Power rails are not visibly overlapped/stiched.
- MUX is not visibly generated/placed as expected.
- Report fields power_rail_overlap_restored=True, column_mux_present=True, reference_comparison_match=True are not trusted.
- Must reference and reproduce hybrid_openyield_rail_overlap.complete.gds exactly.

## 4. M6R Result

- reference_copy_for_review_gds: `/data1/qujh/work/sram_layoutgen_step45_clean/outputs/M6R_reference_locked_reproduce/current_supported_config/reference_copy_for_review.gds`
- m6_previous_output_for_review_gds: `/data1/qujh/work/sram_layoutgen_step45_clean/outputs/M6R_reference_locked_reproduce/current_supported_config/m6_previous_output_for_review.gds`
- reproduced_review_gds: `/data1/qujh/work/sram_layoutgen_step45_clean/outputs/M6R_reference_locked_reproduce/current_supported_config/layoutgen_hybrid_reproduced_M6R.gds`
- reproduced_clean_review_gds: `/data1/qujh/work/sram_layoutgen_step45_clean/outputs/M6R_reference_locked_reproduce/current_supported_config/layoutgen_hybrid_reproduced_M6R_clean_review.gds`
- m6_previous_matches_reference: `False`
- reproduced_matches_reference: `True`

## 5. Next Immediate Task

等待人工 KLayout review `/data1/qujh/work/sram_layoutgen_step45_clean/outputs/M6R_reference_locked_reproduce/current_supported_config/layoutgen_hybrid_reproduced_M6R_clean_review.gds` 与 `/data1/qujh/work/sram_layoutgen_step45_clean/outputs/M6R_reference_locked_reproduce/current_supported_config/reference_copy_for_review.gds` 的对照结果；在此之前不进入下一阶段。
