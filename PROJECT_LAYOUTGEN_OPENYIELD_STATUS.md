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
- M5：直接实施，不再新增评估阶段

## 3. Current Stage

- current_stage: `M4E`
- next_stage: `M5_IMPLEMENT_OPENYIELD_LAYOUTGEN_INTEGRATION`
- human_klayout_review_required_every_stage: `True`
- can_enter_next_stage_without_human_review: `False`
- no_more_evaluation_allowed_after_M4E: `True`

## 4. Latest User Review

- M3F review:
- optimized layoutgen flow has been restored;
- power rail stitching / rail overlap flow has been recovered;
- current GDS has reached the previous layoutgen optimization level;
- but it still mainly uses original layoutgen modules;
- next goal is to integrate OpenYield netlist-defined modules into the layoutgen physical generator;
- because OpenYield module count/type/pin/connection may differ from layoutgen baseline, floorplan / placement / routing / power code may need modification;
- only one feasibility evaluation is allowed before direct implementation.

## 5. M4E Decision

- go_nogo_decision: `PARTIAL_GO_WITH_DEFINED_SCOPE`
- allowed_next_stage: `M5_IMPLEMENT_OPENYIELD_LAYOUTGEN_INTEGRATION`
- openyield_module_count: `20`
- direct_generator_binding_count: `3`
- parameterized_generator_binding_count: `6`
- real_cell_wrapper_count: `5`
- layoutgen_fallback_with_openyield_semantics_count: `6`

## 6. Review Gate

- This M4E review GDS is for human KLayout review only.
- No more evaluation stages are allowed after M4E.
- The next stage must be direct implementation or stop due to blockers.

## 7. Next Immediate Task

等待人工 KLayout review `/data1/qujh/work/sram_layoutgen_step45_clean/outputs/M4E_openyield_integration_eval/current_supported_config/openyield_integration_feasibility_review.gds` 并按 `M5_IMPLEMENT_OPENYIELD_LAYOUTGEN_INTEGRATION` 执行；不得再新增评估阶段。
