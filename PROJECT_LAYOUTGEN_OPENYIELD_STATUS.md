# OpenYield SRAM LayoutGen Project Status

## 1. Current Correct Goal

M11B 已对 `sense_amp` 和 `wordline_driver` 做深度 machine-first pin/bbox/rail metadata 提取。当前仅 `sense_amp` 具备进入受控 M11C smoke substitution 的条件，`wordline_driver` 仍需先补齐 wrapper pin 物理几何。

## 2. Current Stage

- current_stage: `M11B`
- next_stage: `WAIT_HUMAN_KLAYOUT_REVIEW`
- human_klayout_review_required_every_stage: `True`
- can_enter_next_stage_without_human_review: `False`
- next_stage_allowed: `M11C_SELECTIVE_HARDMACRO_SUBSTITUTION_SMOKE_FOR_READY_MODULES`

## 3. Latest M11B Result

- candidate_modules_processed: `sense_amp, wordline_driver`
- ready_for_M11C_modules: `sense_amp`
- not_ready_modules: `wordline_driver`
- review_gds_path: `outputs/M11B_pin_bbox_rail_metadata/current_supported_config/M11B_pin_bbox_rail_metadata_review.gds`
- review_gds_sanity_status: `GDS_PARSED_SANITY_PASSED`
- can_claim_openyield_module_gds_hardmacro_substitution: `False`
