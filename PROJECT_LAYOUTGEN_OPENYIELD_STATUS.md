# OpenYield SRAM LayoutGen Project Status

## 1. Current Correct Goal

基于原 layoutgen 版图生成器，将 OpenYield 的模块、网表语义和连接关系接入真实 SRAM GDS 生成主干，生成 OpenYield-driven layoutgen-based SRAM GDS。

## 2. Current Route

- S0：全部成果整理与路线重置
- M1：layoutgen 原生成路径审计 + OpenYield 模块绑定
- M2：生成第一版 layoutgen-based OpenYield SRAM full trial review GDS
- M3：等待人工 KLayout review 后再决定是否进入真实 routing/power closure

## 3. Current Stage

- current_stage: `M2`
- next_stage: `M3`
- human_klayout_review_required_every_stage: `True`
- can_enter_next_stage_without_human_review: `False`

## 4. M2 Result

- full_sram_review_gds_generated: `True`
- full_sram_review_gds_path: `/data1/qujh/work/sram_layoutgen_step45_clean/outputs/test_M2_layoutgen_full_trial/current_supported_config/openyield_layoutgen_full_trial_sram.gds`
- full_sram_review_gds_size_bytes: `362474`
- top_cell_name: `openyield_layoutgen_full_trial_sram`
- gds_sanity_status: `GDS_PARSED_SANITY_PASSED`
- modules_placed_count: `20`
- temporary_wrapper_count: `12`
- layoutgen_real_generator_used_count: `8`
- first_round_openyield_gds_used_count: `8`

## 5. Review Gate

- This M2 GDS is for human KLayout review only.
- Do not claim DRC clean.
- Do not claim LVS clean.
- Do not claim signoff-ready.
- Do not auto-enter M3 before user review.

## 6. Next Immediate Task

等待人工 KLayout review `/data1/qujh/work/sram_layoutgen_step45_clean/outputs/test_M2_layoutgen_full_trial/current_supported_config/openyield_layoutgen_full_trial_sram.gds`。未经用户确认，不进入 M3。
