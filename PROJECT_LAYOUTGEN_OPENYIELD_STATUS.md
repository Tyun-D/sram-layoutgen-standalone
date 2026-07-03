# OpenYield SRAM LayoutGen Project Status

## 1. Current Correct Goal

基于原 layoutgen 版图生成器，将 OpenYield 的模块、网表语义和连接关系接入真实 SRAM GDS 生成主干，生成 OpenYield-driven layoutgen-based SRAM GDS。

## 2. Current Route

- S0：全部成果整理与路线重置
- M1：layoutgen 原生成路径审计 + OpenYield 模块绑定
- M2R：按锁定 SRAM 规格复用 layoutgen 原 SRAM top flow 重做 review GDS
- M3：等待人工 KLayout review 后再决定下一阶段

## 3. Current Stage

- current_stage: `M2R`
- next_stage: `M3`
- human_klayout_review_required_every_stage: `True`
- can_enter_next_stage_without_human_review: `False`

## 4. Latest User Correction

- M2 physical review failed because modules were freely scattered, SRAM spec was not locked, layoutgen top-level generation rules were not followed, and the result did not resemble a complete SRAM macro.

## 5. M2R Result

- locked_sram_spec_available: `True`
- layoutgen_top_flow_trace_available: `True`
- layoutgen_top_flow_used: `True`
- arbitrary_module_scatter_used: `False`
- full_sram_review_gds_generated: `True`
- full_sram_review_gds_path: `/data1/qujh/work/sram_layoutgen_step45_clean/outputs/test_M2R_full_sram_regen/current_supported_config/openyield_layoutgen_full_sram_M2R.gds`
- top_cell_name: `openyield_layoutgen_full_sram_M2R`
- gds_sanity_status: `GDS_PARSED_SANITY_PASSED`

## 6. Review Gate

- This M2R GDS is for human KLayout review only.
- Do not claim DRC clean.
- Do not claim LVS clean.
- Do not claim signoff-ready.
- Do not auto-enter M3 before user review.

## 7. Next Immediate Task

等待人工 KLayout review `/data1/qujh/work/sram_layoutgen_step45_clean/outputs/test_M2R_full_sram_regen/current_supported_config/openyield_layoutgen_full_sram_M2R.gds`。未经用户确认，不进入下一阶段。
