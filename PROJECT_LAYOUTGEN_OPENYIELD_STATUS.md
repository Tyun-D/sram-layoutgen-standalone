# OpenYield SRAM LayoutGen Project Status

## 1. Current Correct Goal

先复现并修复用户上传确认的正确 layoutgen golden reference，再以该 golden 为唯一物理目标推进后续修复与最终 OpenYield 集成。

## 2. Current Stage

- current_stage: `M8`
- next_stage: `WAIT_HUMAN_KLAYOUT_REVIEW`
- human_klayout_review_required_every_stage: `True`
- can_enter_next_stage_without_human_review: `False`

## 3. Latest M8 Result

- golden_reference_path: `outputs/M7_correct_golden_reference/current_supported_config/golden_reference.gds`
- reproduced_gds_path: `outputs/M8_reproduce_uploaded_golden/current_supported_config/layoutgen_reproduced_from_uploaded_golden.gds`
- reference_vs_reproduced_geometry_match: `STRUCTURAL_MATCH_WITH_GEOMETRY_DELTA`
- column_mux_real_check_passed: `True`
- power_rail_overlap_real_check_passed: `True`
- human_klayout_review_required: `True`

## 4. Next Immediate Task

人工 KLayout 对比 `outputs/M8_reproduce_uploaded_golden/current_supported_config/layoutgen_reproduced_from_uploaded_golden_clean_review.gds` 与 `outputs/M7_correct_golden_reference/current_supported_config/golden_reference.gds`。在此之前不得进入 M9。
