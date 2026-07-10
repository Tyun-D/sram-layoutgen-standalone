# OpenYield SRAM LayoutGen Project Status

## 1. Current Correct Goal

M11W 已完成 `wordline_driver` wrapper / D/G/S pin metadata 修复。当前仍不声称 full OpenYield module GDS hardmacro substitution、DRC clean、LVS clean 或 signoff-ready。

## 2. Current Stage

- current_stage: `M11W`
- next_stage: `M11C2_WORDLINE_DRIVER_SMOKE_SUBSTITUTION`
- human_klayout_review_required_every_stage: `True`
- can_enter_next_stage_without_human_review: `True`
- next_stage_allowed: `M11C2_WORDLINE_DRIVER_SMOKE_SUBSTITUTION`

## 3. M11W Wordline Driver Repair

- repair_strategy_used: `STRATEGY_B_WRAPPER_PIN_EXPOSURE`
- dgs_pins_resolved: `True`
- unresolved_pin_count: `0`
- wrapper_generated: `True`
- wrapper_required_after: `False`
- routing_safe_after_repair: `True`
- wordline_driver_ready_for_smoke_substitution: `True`
- next_stage_allowed: `M11C2_WORDLINE_DRIVER_SMOKE_SUBSTITUTION`
- can_claim_wordline_driver_pin_repair_completed: `True`
- can_claim_wordline_driver_smoke_substitution_ready: `True`
- can_claim_openyield_module_gds_hardmacro_substitution: `False`
- can_claim_drc_clean: `False`
- can_claim_lvs_clean: `False`
- can_claim_signoff_ready: `False`
