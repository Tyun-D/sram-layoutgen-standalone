# OpenYield SRAM LayoutGen Project Status

## 1. Current Correct Goal

先复现并修复用户上传确认的正确 layoutgen golden reference，再以该 golden 为唯一物理目标推进后续修复与最终 OpenYield 集成。

## 2. Current Stage

- current_stage: `M7`
- next_stage: `WAIT_HUMAN_KLAYOUT_REVIEW`
- human_klayout_review_required_every_stage: `True`
- can_enter_next_stage_without_human_review: `False`

## 3. Latest Human Review

- hybrid_openyield_rail_overlap.complete.gds was proven reproducible, but user confirmed it is still not the correct layoutgen result.
- The true correct layoutgen result is local to the user's Windows machine:
-   E:\njust\keyan\SRAM Compiler_V2\OpenRAM-stable\deliverables\sram_layoutgen_standalone\build\full_layout_collection.zip
- After upload, the server-side golden reference zip is:
-   external_references/full_layout_collection.zip
- From now on, hybrid_openyield_rail_overlap.complete.gds must be treated as historical wrong reference, not golden reference.

## 4. M7 Result

- uploaded_zip_path: `/data1/qujh/work/sram_layoutgen_step45_clean/external_references/full_layout_collection.zip`
- golden_reference_path: `/data1/qujh/work/sram_layoutgen_step45_clean/outputs/M7_correct_golden_reference/current_supported_config/golden_reference.gds`
- golden_reference_clean_review_path: `/data1/qujh/work/sram_layoutgen_step45_clean/outputs/M7_correct_golden_reference/current_supported_config/golden_reference_clean_review.gds`
- golden_reference_top_cell: `sram_8x64_wpr4_fd45`
- hybrid_openyield_rail_overlap_is_golden: `False`
- new_uploaded_reference_is_golden: `True`

## 5. Next Immediate Task

先进行人工 KLayout review：`/data1/qujh/work/sram_layoutgen_step45_clean/outputs/M7_correct_golden_reference/current_supported_config/golden_reference_clean_review.gds`。后续所有修复必须对比 `/data1/qujh/work/sram_layoutgen_step45_clean/outputs/M7_correct_golden_reference/current_supported_config/golden_reference.gds`，不得再以 `hybrid_openyield_rail_overlap.complete.gds` 作为 golden。
