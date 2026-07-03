# OpenYield SRAM LayoutGen Project Status

## 1. Current Correct Goal

基于原 layoutgen 版图生成器，将 OpenYield 的模块、网表语义和连接关系接入真实 SRAM GDS 生成主干，生成 OpenYield-driven layoutgen-based SRAM GDS。

## 2. Current Route

- S0：全部成果整理与路线重置
- M1：layoutgen 原生成路径审计 + OpenYield 模块绑定
- M2R：按锁定 SRAM 规格复用 layoutgen 原 SRAM top flow 重做 review GDS
- M3R：在 M2R 物理 backbone 上绑定 OpenYield module/net semantics
- M4：等待人工 KLayout review 后再决定下一阶段

## 3. Current Stage

- current_stage: `M3R`
- next_stage: `M4`
- human_klayout_review_required_every_stage: `True`
- can_enter_next_stage_without_human_review: `False`

## 4. Latest User Review

- M2R physical review: layout is SRAM-like and uses layoutgen top flow, but it still uses layoutgen original cells/modules rather than OpenYield module semantics. first_round_openyield_gds_used_count = 0. Next step must bind OpenYield module/net semantics onto the layoutgen physical SRAM backbone.

## 5. M3R Result

- semantic_bound_gds_generated: `True`
- semantic_bound_gds_path: `/data1/qujh/work/sram_layoutgen_step45_clean/outputs/M3R_openyield_semantic_bound/current_supported_config/openyield_semantic_bound_full_sram.gds`
- top_cell_name: `openyield_semantic_bound_full_sram`
- gds_sanity_status: `GDS_PARSED_SANITY_PASSED`
- m2r_physical_backbone_preserved: `True`
- layoutgen_top_flow_preserved: `True`
- openyield_modules_bound_count: `20`
- openyield_net_bound_count: `34`

## 6. Review Gate

- This M3R GDS is for human KLayout review only.
- Do not claim DRC clean.
- Do not claim LVS clean.
- Do not claim signoff-ready.
- Do not auto-enter the next stage before user review.

## 7. Next Immediate Task

等待人工 KLayout review `/data1/qujh/work/sram_layoutgen_step45_clean/outputs/M3R_openyield_semantic_bound/current_supported_config/openyield_semantic_bound_full_sram.gds`，确认 OpenYield 语义绑定是否符合预期。未经用户确认，不进入下一阶段。
