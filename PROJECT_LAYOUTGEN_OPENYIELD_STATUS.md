# OpenYield SRAM LayoutGen Project Status

## 1. Current Correct Goal

M11H 已确认 M11 clean review GDS 与 locked golden reference 保持 EXACT_MATCH，并正式锁定 config-aware translator v3 的 claim 边界；下一步进入 M11A module GDS qualification。

## 2. Current Stage

- current_stage: `M11H`
- next_stage: `WAIT_HUMAN_KLAYOUT_REVIEW`
- human_klayout_review_required_every_stage: `True`
- can_enter_next_stage_without_human_review: `False`
- next_stage_allowed: `M11A_MODULE_GDS_QUALIFICATION`

## 3. Latest M11H Result

- m11_clean_gds_user_review_passed: `True`
- m11_config_aware_translator_v3_confirmed: `True`
- can_claim_config_aware_translator_v3: `True`
- can_claim_full_raw_netlist_compiler: `False`
- capacity_config_fallback_used_after_M11: `True`
- fallback_eliminated_by_M11: `False`
- variation_support_added: `True`
- supported_variations: `8x64_wpr4, 4x32_wpr2, 16x16_wpr1`
- reference_vs_m11_geometry_match: `EXACT_MATCH`
- next_stage_allowed: `M11A_MODULE_GDS_QUALIFICATION`
