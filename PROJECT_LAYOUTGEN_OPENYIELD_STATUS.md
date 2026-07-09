# OpenYield SRAM LayoutGen Project Status

## 1. Current Correct Goal

M11C 已完成 `sense_amp-only` OpenYield hardmacro smoke substitution。当前只验证一次受控 leaf 替换尝试是否保持 top GDS 可生成、可解析且无明显结构破坏，不扩大到任何其他模块。

## 2. Current Stage

- current_stage: `M11C`
- next_stage: `WAIT_HUMAN_KLAYOUT_REVIEW`
- human_klayout_review_required_every_stage: `True`
- can_enter_next_stage_without_human_review: `False`
- next_stage_allowed: `M11CH_CONFIRM_M11C_HUMAN_REVIEW`

## 3. Latest M11C Result

- substituted_modules: `sense_amp`
- output_gds_path: `outputs/M11C_sense_amp_smoke_substitution/current_supported_config/M11C_sense_amp_substituted_sram.gds`
- output_gds_sanity_status: `GDS_PARSED_SANITY_PASSED`
- top_bbox_match_status: `EXACT_MATCH`
- sense_amp_substitution_smoke_status: `SMOKE_SUBSTITUTION_PASS`
- can_claim_openyield_module_gds_hardmacro_substitution: `False`
