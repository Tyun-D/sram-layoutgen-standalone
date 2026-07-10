# OpenYield SRAM LayoutGen Project Status

## 1. Current Correct Goal

M11C2 已完成 `wordline_driver-only` OpenYield wrapper hardmacro smoke substitution。当前只验证一次隔离的 in-hierarchy 替换尝试是否保持 top GDS 可生成、可解析且无明显结构破坏，不叠加 `sense_amp` 或扩大到其他模块。

## 2. Current Stage

- current_stage: `M11C2`
- next_stage: `WAIT_HUMAN_KLAYOUT_REVIEW`
- human_klayout_review_required_every_stage: `True`
- can_enter_next_stage_without_human_review: `False`
- next_stage_allowed: `M11C2H_CONFIRM_M11C2_HUMAN_REVIEW`

## 3. Latest M11C2 Result

- substituted_modules: `wordline_driver`
- output_gds_path: `outputs/M11C2_wordline_driver_smoke_substitution/current_supported_config/M11C2_wordline_driver_substituted_sram.gds`
- output_gds_sanity_status: `GDS_PARSED_SANITY_PASSED`
- top_bbox_match_status: `EXACT_MATCH`
- real_substitution_proof_status: `PASS_WRAPPER_DGS_GEOMETRY_MATCH`
- wordline_driver_substitution_smoke_status: `SMOKE_SUBSTITUTION_PASS`
- can_claim_openyield_module_gds_hardmacro_substitution: `False`
