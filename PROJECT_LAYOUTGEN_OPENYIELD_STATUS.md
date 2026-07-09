# OpenYield SRAM LayoutGen Project Status

## 1. Current Correct Goal

M11A 已对 20 个 OpenYield module GDS 做资格审查，确认可用于 direct replacement 的候选、只能提取约束的候选，以及仍只能作为语义参考的模块；下一步必须进入 M11B metadata extraction。

## 2. Current Stage

- current_stage: `M11A`
- next_stage: `WAIT_HUMAN_KLAYOUT_REVIEW`
- human_klayout_review_required_every_stage: `True`
- can_enter_next_stage_without_human_review: `False`
- next_stage_allowed: `M11B_PIN_BBOX_RAIL_METADATA_EXTRACTION`

## 3. Latest M11A Result

- module_gds_count: `20`
- direct_hardmacro_replace_count: `4`
- constraint_extraction_only_count: `4`
- semantic_reference_only_count: `12`
- rejected_count: `0`
- first_substitution_candidates: `column_mux, sense_amp, wordline_driver, write_driver`
- review_gds_path: `outputs/M11A_module_gds_qualification/current_supported_config/module_gds_qualification_review.gds`
- review_gds_sanity_status: `GDS_PARSED_SANITY_PASSED`
- can_claim_openyield_module_gds_hardmacro_substitution: `False`
- next_stage_allowed: `M11B_PIN_BBOX_RAIL_METADATA_EXTRACTION`
