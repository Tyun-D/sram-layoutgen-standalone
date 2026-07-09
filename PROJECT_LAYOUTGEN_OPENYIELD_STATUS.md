# OpenYield SRAM LayoutGen Project Status

## 1. Current Correct Goal

M11BH 已完成 M11B 的人工校验收口。`sense_amp` 通过视觉与标注可读性确认，可进入 `sense_amp-only` 的 M11C smoke substitution；`wordline_driver` 明确保留在后续 wrapper / pin 解析修复范围内，不得进入 M11C。

## 2. Current Stage

- current_stage: `M11BH`
- next_stage: `M11C_SENSE_AMP_ONLY_SMOKE_SUBSTITUTION`
- human_klayout_review_required_every_stage: `True`
- can_enter_next_stage_without_human_review: `True`
- next_stage_allowed: `M11C_SENSE_AMP_ONLY_SMOKE_SUBSTITUTION`

## 3. Latest M11BH Result

- m11b_human_review_completed: `True`
- sense_amp_visual_review_passed: `True`
- sense_amp_ready_for_M11C_after_human_review: `True`
- wordline_driver_excluded_from_M11C: `True`
- ready_for_M11C_modules_after_human_review: `sense_amp`
- not_ready_modules_after_human_review: `wordline_driver`
- remaining_M11B_blockers_before_count: `3`
- remaining_M11B_blockers_after_count: `0`
- can_claim_openyield_module_gds_hardmacro_substitution: `False`
