# OpenYield SRAM LayoutGen Project Status

## 1. Current Correct Goal

M11D 已完成对 M11C `sense_amp-only` smoke substitution 的后分析。当前已机器证明这是一次真实的 leaf 指纹替换，但 claim 边界仍只允许 `sense_amp-only smoke substitution attempted/pass`，不扩大到 full OpenYield module GDS hardmacro substitution、DRC clean、LVS clean 或 signoff-ready。

## 2. Current Stage

- current_stage: `M11D`
- next_stage: `M11W_WORDLINE_DRIVER_WRAPPER_PIN_REPAIR`
- human_klayout_review_required_every_stage: `True`
- can_enter_next_stage_without_human_review: `True`
- next_stage_allowed: `M11W_WORDLINE_DRIVER_WRAPPER_PIN_REPAIR`

## 3. M11D Post Analysis

- real_substitution_proof_status: `PASS_GEOMETRY_FINGERPRINT_MATCH`
- openyield_sense_amp_fingerprint_found_in_M11C: `True`
- top_bbox_match_status: `EXACT_MATCH`
- hierarchy_delta_status: `ONLY_SENSE_AMP_LEAF_FINGERPRINT_CHANGED`
- unexpected_non_sense_amp_change_count: `0`
- machine_verified_item_count: `28`
- human_review_required_item_count: `0`
- sense_amp_substitution_analysis_status: `PASS_REAL_SUBSTITUTION_PROVEN`
- sense_amp_substitution_risk_level: `MEDIUM`
- recommended_next_stage: `M11W_WORDLINE_DRIVER_WRAPPER_PIN_REPAIR`
- can_claim_sense_amp_smoke_substitution_passed: `True`
- can_claim_openyield_module_gds_hardmacro_substitution: `False`
- can_claim_drc_clean: `False`
- can_claim_lvs_clean: `False`
- can_claim_signoff_ready: `False`
