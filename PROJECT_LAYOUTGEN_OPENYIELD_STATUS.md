# OpenYield SRAM LayoutGen Project Status

## 1. Current Correct Goal

M11CH 已完成对 M11C `sense_amp-only` smoke substitution 的人工收口确认。当前只允许 claim `sense_amp-only smoke substitution attempted/pass`，不扩大到任何其他模块，也不声称 full OpenYield module GDS hardmacro substitution、DRC clean、LVS clean 或 signoff-ready。

## 2. Current Stage

- current_stage: `M11CH`
- next_stage: `M11D_POST_SENSE_AMP_SUBSTITUTION_ANALYSIS_OR_NEXT_SAFE_CANDIDATE_PLANNING`
- human_klayout_review_required_every_stage: `True`
- can_enter_next_stage_without_human_review: `True`
- next_stage_allowed: `M11D_POST_SENSE_AMP_SUBSTITUTION_ANALYSIS_OR_NEXT_SAFE_CANDIDATE_PLANNING`

## 3. M11CH Human Review Closure

- m11c_human_review_completed: `True`
- m11c_sense_amp_visual_review_passed: `True`
- m11c_sense_amp_annotation_readable: `True`
- m11c_sense_amp_nearby_power_routing_not_visually_broken: `True`
- substituted_modules: `sense_amp`
- excluded_modules_confirmed: `True`
- remaining_M11C_blockers_before_count: `3`
- remaining_M11C_blockers_after_count: `0`
- can_claim_sense_amp_smoke_substitution_attempted: `True`
- can_claim_sense_amp_smoke_substitution_passed: `True`
- can_claim_openyield_module_gds_hardmacro_substitution: `False`
- can_claim_drc_clean: `False`
- can_claim_lvs_clean: `False`
- can_claim_signoff_ready: `False`
