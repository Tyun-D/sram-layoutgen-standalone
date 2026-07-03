# OpenYield SRAM LayoutGen Project Status

## 1. Current Correct Goal

基于原 layoutgen 版图生成器，将 OpenYield 的模块、网表语义和连接关系接入真实 SRAM GDS 生成主干，生成 OpenYield-driven layoutgen-based SRAM GDS。

## 2. Current Route

- S0：全部成果整理与路线重置
- M1：layoutgen 原生成路径审计 + OpenYield 模块绑定
- M2R：按锁定 SRAM 规格复用 layoutgen 原 SRAM top flow 重做 review GDS
- M3R：在 M2R 物理 backbone 上绑定 OpenYield module/net semantics
- M3F：恢复优化版 layoutgen 主干并接入 OpenYield 语义
- M4E：唯一一次 OpenYield integration feasibility evaluation
- M5：OpenYield integration into optimized layoutgen flow

## 3. Current Stage

- current_stage: `M5`
- next_stage: `WAIT_HUMAN_KLAYOUT_REVIEW`
- human_klayout_review_required_every_stage: `True`
- can_enter_next_stage_without_human_review: `False`
- no_more_evaluation_allowed_after_M4E: `True`

## 4. M5 Result

- integrated_gds_path: `/data1/qujh/work/sram_layoutgen_step45_clean/outputs/M5_openyield_layoutgen_integration/current_supported_config/openyield_layoutgen_integrated_sram.gds`
- top_cell_name: `openyield_layoutgen_integrated_sram`
- gds_sanity_status: `GDS_PARSED_SANITY_PASSED`
- openyield_modules_implemented_count: `20`
- openyield_nets_implemented_count: `34`
- optimized_power_rail_stitch_preserved: `True`

## 5. Review Gate

- This M5 GDS is for human KLayout review only.
- No more feasibility/evaluation stage is allowed after M4E.
- Do not claim DRC clean.
- Do not claim LVS clean.
- Do not claim signoff-ready.

## 6. Next Immediate Task

等待人工 KLayout review `/data1/qujh/work/sram_layoutgen_step45_clean/outputs/M5_openyield_layoutgen_integration/current_supported_config/openyield_layoutgen_integrated_sram.gds`，确认 OpenYield module/net 实施接入 optimized layoutgen backbone 的整体方向。未经用户确认，不进入下一阶段。
