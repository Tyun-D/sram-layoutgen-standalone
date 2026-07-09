# OpenYield SRAM LayoutGen Project Status

## 1. Current Correct Goal

M11AR 已把 M11A 的人工 review 修正收敛进 hardmacro 资格结果。当前只保留 `sense_amp` 与 `wordline_driver` 作为进入 M11B 的优先候选，`column_mux` 与 `write_driver` 已降级，不能直接进行模块替换。

## 2. Current Stage

- current_stage: `M11AR`
- next_stage: `WAIT_HUMAN_KLAYOUT_REVIEW`
- human_klayout_review_required_every_stage: `True`
- can_enter_next_stage_without_human_review: `False`
- next_stage_allowed: `M11B_PIN_BBOX_RAIL_METADATA_EXTRACTION_FOR_SENSE_AMP_AND_WORDLINE_DRIVER`

## 3. Latest M11AR Result

- human_review_applied: `True`
- unknown_golden_region_markers_are_real_modules: `False`
- direct_hardmacro_replace_count_before: `4`
- direct_hardmacro_replace_count_after: `2`
- first_substitution_candidates_after: `sense_amp, wordline_driver`
- downgraded_modules: `column_mux, write_driver`
- can_claim_openyield_module_gds_hardmacro_substitution: `False`
- next_stage_allowed: `M11B_PIN_BBOX_RAIL_METADATA_EXTRACTION_FOR_SENSE_AMP_AND_WORDLINE_DRIVER`
