# Final Technical Report

## 1. 项目背景与目标

本项目目标是将 OpenYield 的 SRAM 网表语义、模块层次和控制路径逐步映射到本地 layoutgen，最终生成 OpenYield-driven SRAM top-level candidate GDS。

## 2. 技术路线

- L0：OpenYield 网表语义层
- L1：物理基元层
- L2：拼接 / 排布 / 电源轨规则层
- L3：模块级 generator + standalone GDS
- L4：top-level SRAM candidate GDS assembly
- L5：basic validation
- L6：DRC marker triage
- Step 7：final repair planning
- Step 8：final handoff

Step 8 是本轮固定终点，不再新增层次。

## 3. 当前支持范围

- single_bank = True
- single implicit read/write port = True
- num_ports_supported = 1
- write_mask_supported = False
- words_per_row supported = 1 or 2
- column_mux_ratio supported = 1 or 2

不支持：

- multi_bank
- multi_port
- write_mask
- write_size
- words_per_row > 2
- column_mux_ratio > 2

## 4. L0–L6 阶段成果

- L0：已建立 OpenYield SRAM semantic contract，并冻结当前 scope 的语义边界。
- L1：已建立当前 scope 所需 physical primitive source closure。
- L2：已冻结 placement / abutment / rail / handoff 规则库。
- L3：20 个 target modules 已生成 standalone module GDS，并带有 manifest / pins / bbox / rail metadata。
- L4：已完成 top-level SRAM candidate GDS assembly，并导出 manifest 与 placement metadata。
- L5：basic validation 已通过，remaining_L5_basic_validation_blockers_count = 0。
- L6：DRC marker 共 24687 个，且已完成 100% 分类。

## 5. 当前最终交付物

- top-level candidate GDS：`outputs/openyield_top_level_assembly/current_supported_config/openyield_top_level_candidate.gds`
- module GDS directory：`outputs/openyield_module_gds`
- top-level assembly directory：`outputs/openyield_top_level_assembly/current_supported_config`
- validation directory：`outputs/openyield_validation/current_supported_config`
- DRC triage directory：`outputs/openyield_drc_triage/current_supported_config`
- project closure directory：`outputs/openyield_project_closure/current_supported_config`
- final handoff directory：`outputs/openyield_final_handoff/current_supported_config`

## 6. 当前可以 claim 的成果

- OpenYield 语义到本地 layoutgen 的映射已建立。
- 当前 scope 支持 single-bank、single-port、words_per_row 1/2。
- 20 个 L3 target modules 已生成 standalone module GDS。
- 20 个模块均有 generator manifest / pins / bbox / rail metadata。
- top-level SRAM candidate GDS 已生成。
- top-level GDS hierarchy 完整。
- top-level GDS 可解析。
- 20 个 required modules 全部实例化。
- L5 basic validation 已通过，remaining_L5_basic_validation_blockers_count=0。
- DRC marker 已完成 100% 分类，coverage=1.0。
- 已形成后续 DRC 修复优先级计划。

## 7. 当前不能 claim 的内容

- DRC markers = 24687，尚未清零。 当前不能 claim DRC clean。
- 当前 top-level GDS 是 candidate layout，不是 signoff layout。 当前终点是可交付候选态，不是可流片版图。
- 部分模块使用 candidate geometry。 这些模块会阻塞 DRC/LVS/timing/signoff claim。
- 部分模块使用 contract pins。 这些模块适合 basic validation，但不适合 DRC/LVS signoff。
- LVS blocked by missing netlist。 当前不能 claim LVS clean。
- timing 仍是 metadata / smoke 级别。 当前不能 claim timing closure。
- 当前仅覆盖 single-bank / single-port / limited words_per_row。 更广 scope 仍未进入当前交付态。
- multi-bank / multi-port / write mask / larger mux ratio 仍 unsupported。 这些功能需要新增独立实现阶段。
- DRC marker 分类依赖当前 deck、当前 GDS 和当前 marker parser，不代表最终物理收敛。 后续若更换 deck 或 source geometry，分类比例可能变化。

## 8. DRC marker 分类结果

- total = 24687
- classified = 24687
- coverage = 1.0

- LAYER_MAP_OR_DRC_DECK_INTERPRETATION: 12012
- CONTRACT_PIN_GEOMETRY_PLACEHOLDER: 11944
- CANDIDATE_GEOMETRY_INTERNAL: 666
- MODULE_INTERNAL_HARDMACRO: 49
- MODULE_WRAPPER_IMPORT: 16

## 9. 后续修复计划

后续若继续深入，应沿用 Step 7 final repair plan 的顺序：先处理 P1 `LAYER_MAP_OR_DRC_DECK_INTERPRETATION`，再处理 P4 `CONTRACT_PIN_GEOMETRY_PLACEHOLDER`，然后处理 P3 `CANDIDATE_GEOMETRY_INTERNAL`，并分别补做 hardmacro internal audit 与 wrapper import review。

## 10. 结论

本项目 v1.0 已实现 OpenYield-driven SRAM top-level candidate GDS 自动生成，并完成 basic validation、DRC marker 分类和最终修复计划。当前交付物是 candidate GDS，不是 DRC/LVS/timing signoff-ready GDS。
