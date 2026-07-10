# OpenYield SRAM LayoutGen Project Status

## 1. Current Correct Goal

M11V 已完成对 isolated `sense_amp` 与 `wordline_driver` smoke substitutions 的 routing / power / connectivity verification deepening。当前只确认二者未显示出新的 substitution-specific risk，但 baseline routing/power cleanliness 仍未被证明，因此不能直接扩大到 full hardmacro substitution、routing clean、power clean、DRC clean、LVS clean 或 signoff-ready。

## 2. Current Stage

- current_stage: `M11V`
- next_stage: `M11V2_DEEPER_CONNECTIVITY_EXTRACTION`
- human_klayout_review_required_every_stage: `True`
- can_enter_next_stage_without_human_review: `True`
- next_stage_allowed: `M11V2_DEEPER_CONNECTIVITY_EXTRACTION`

## 3. M11V Verification Result

- verification_status: `INCONCLUSIVE`
- verification_risk_level: `MEDIUM`
- baseline_power_risk_level: `MEDIUM_BASELINE_LIMITED`
- baseline_routing_risk_level: `HIGH_BASELINE_LIMITED`
- sense_amp_incremental_risk_level: `LOW_INCREMENTAL_RISK`
- wordline_driver_incremental_risk_level: `LOW_INCREMENTAL_RISK`
- recommended_next_stage: `M11V2_DEEPER_CONNECTIVITY_EXTRACTION`
- can_claim_openyield_module_gds_hardmacro_substitution: `False`
- can_claim_routing_clean: `False`
- can_claim_power_clean: `False`
- can_claim_drc_clean: `False`
- can_claim_lvs_clean: `False`
- can_claim_signoff_ready: `False`
