# OpenYield SRAM LayoutGen Project Status

## 1. Current Correct Goal

基于原 layoutgen 版图生成器，将 OpenYield 的模块、网表语义和连接关系接入真实 SRAM GDS 生成主干，生成 OpenYield-driven layoutgen-based SRAM GDS。

## 2. Current Route

- S0：全部成果整理与路线重置
- M1：layoutgen 原生成路径审计 + OpenYield 模块绑定
- M2R：按锁定 SRAM 规格复用 layoutgen 原 SRAM top flow 重做 review GDS
- M3R：在 M2R 物理 backbone 上绑定 OpenYield module/net semantics
- M3F：恢复优化版 layoutgen 主干并接入 OpenYield 语义
- M4：等待人工 KLayout review 后再决定下一阶段

## 3. Current Stage

- current_stage: `M3F`
- next_stage: `M4`
- human_klayout_review_required_every_stage: `True`
- can_enter_next_stage_without_human_review: `False`

## 4. Latest User Review

- M3R review failed/partially failed:
- - OpenYield semantics were mostly exported as text labels.
- - Physical cells remained layoutgen original cells.
- - first_round_openyield_gds_reused_count = 0.
- - Optimized layoutgen rail-overlap / power-rail stitching flow was not restored.
- - Do not proceed to final validation before restoring optimized layoutgen generation flow.

## 5. M3F Result

- optimized_layoutgen_flow_found: `True`
- optimized_layoutgen_reference_gds_found: `True`
- optimized_power_rail_stitch_flow_used: `True`
- power_rail_stitch_restored: `True`
- full_sram_review_gds_path: `/data1/qujh/work/sram_layoutgen_step45_clean/outputs/M3F_optimized_layoutgen_restore/current_supported_config/openyield_optimized_layoutgen_sram.gds`
- top_cell_name: `openyield_optimized_layoutgen_sram`
- gds_sanity_status: `GDS_PARSED_SANITY_PASSED`

## 6. Review Gate

- This M3F GDS is for human KLayout review only.
- Do not claim DRC clean.
- Do not claim LVS clean.
- Do not claim signoff-ready.
- Do not auto-enter the next stage before user review.

## 7. Next Immediate Task

等待人工 KLayout review `/data1/qujh/work/sram_layoutgen_step45_clean/outputs/M3F_optimized_layoutgen_restore/current_supported_config/openyield_optimized_layoutgen_sram.gds`，确认优化版 rail-overlap/power-stitch 恢复和 OpenYield 语义绑定是否满足预期。未经用户确认，不进入下一阶段。
