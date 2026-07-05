# OpenYield SRAM LayoutGen Project Status

## 1. Current Correct Goal

先复现并修复用户上传确认的正确 layoutgen golden reference，再以该 golden 为唯一物理目标推进后续修复与最终 OpenYield 集成。

## 2. Current Stage

- current_stage: `M7C`
- next_stage: `M8_REPRODUCE_UPLOADED_GOLDEN_REFERENCE`
- human_klayout_review_required_every_stage: `True`
- can_enter_next_stage_without_human_review: `False`

## 3. Latest Human Review

- User confirmed `outputs/M7_correct_golden_reference/current_supported_config/golden_reference_clean_review.gds` is the correct uploaded golden reference.
- historical_wrong_reference: `outputs/layout_prototype/hybrid_openyield_rail_overlap/hybrid_openyield_rail_overlap.complete.gds` must remain non-golden.
- M7 blocker 1 cleared: human KLayout review of the uploaded golden reference is complete.
- M7 blocker 2 cleared: next repair stage is locked to reproducing the uploaded golden reference rather than the historical hybrid reference.

## 4. M7C Result

- golden_reference_user_confirmed: `True`
- golden_reference_is_now_locked: `True`
- current_golden_reference_path: `outputs/M7_correct_golden_reference/current_supported_config/golden_reference.gds`
- current_golden_reference_clean_review_path: `outputs/M7_correct_golden_reference/current_supported_config/golden_reference_clean_review.gds`
- historical_wrong_reference: `outputs/layout_prototype/hybrid_openyield_rail_overlap/hybrid_openyield_rail_overlap.complete.gds`
- hybrid_openyield_rail_overlap_is_golden: `False`
- new_uploaded_reference_is_golden: `True`
- m7_blockers_before_count: `2`
- m7_blockers_after_count: `0`

## 5. Blocker Clearance

- Human KLayout review of uploaded golden reference is required.
- Next repair stage must reproduce the new uploaded golden reference instead of historical hybrid reference.

## 6. Next Immediate Task

进入 `M8_REPRODUCE_UPLOADED_GOLDEN_REFERENCE`，先复现 `outputs/M7_correct_golden_reference/current_supported_config/golden_reference.gds`。注意：M8 新生成的 GDS 仍然必须等待人工 KLayout review，不能直接跨阶段声称完成。
