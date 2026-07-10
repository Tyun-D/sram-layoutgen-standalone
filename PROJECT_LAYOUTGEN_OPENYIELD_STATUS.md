# OpenYield SRAM LayoutGen Project Status

## 1. Current Correct Goal

M11C2H 已完成对 M11C2 `wordline_driver-only` smoke substitution 的人工收口确认。当前只允许 claim `wordline_driver-only smoke substitution attempted/pass`，但必须保留 routing/power cleanliness caveat；不扩大到任何其他模块，也不声称 full OpenYield module GDS hardmacro substitution、routing clean、power clean、DRC clean、LVS clean 或 signoff-ready。

## 2. Current Stage

- current_stage: `M11C2H`
- next_stage: `M11V_ROUTING_POWER_CONNECTIVITY_VERIFICATION_DEEPENING`
- human_klayout_review_required_every_stage: `True`
- can_enter_next_stage_without_human_review: `True`
- next_stage_allowed: `M11V_ROUTING_POWER_CONNECTIVITY_VERIFICATION_DEEPENING`

## 3. M11C2H Human Review Closure

- m11c2_human_review_completed: `True`
- m11c2_wordline_driver_visual_review_passed: `True`
- m11c2_wordline_driver_annotation_readable: `True`
- m11c2_wordline_driver_nearby_power_routing_review_status: `INCONCLUSIVE_BASELINE_ROUTING_LIMITED`
- m11c2_no_obvious_new_break_reported_by_human: `True`
- m11c2_nearby_power_routing_visually_confirmed_clean: `False`
- substituted_modules: `wordline_driver`
- excluded_modules_confirmed: `True`
- remaining_M11C2_blockers_before_count: `3`
- remaining_M11C2_blockers_after_count: `0`
- can_claim_wordline_driver_smoke_substitution_attempted: `True`
- can_claim_wordline_driver_smoke_substitution_passed: `True`
- can_claim_openyield_module_gds_hardmacro_substitution: `False`
- can_claim_routing_clean: `False`
- can_claim_power_clean: `False`
- can_claim_drc_clean: `False`
- can_claim_lvs_clean: `False`
- can_claim_signoff_ready: `False`
