# Project Industrial Gap Closure Gate

- status: `ADVANCED_WITH_SPECIFIC_BLOCKERS`
- date: `2026-07-30`

## Closed Or Advanced

- 真实服务器 EDA 工具、模型和资产审计已完成。
- 最小可信仿真链路已选定为 `ngspice` 主链、`Xyce` 备选，逻辑仿真保持 `tool-available but asset-blocked` 的保守状态。
- 模块级 SPICE 烟测已真实运行，`9` 个模块通过，`delay_chain` 仍失败。
- 电源正向连通性/拓扑审计在 `3` 个 raw-source-backed 配置上通过。
- 工业级定位、DRC provenance/waiver 政策和项目级证据矩阵已刷新。

## Specific Blockers

- decoder live `24-marker` / `M2-only` 闭合基线与专用 gate 未在当前工作树中找到。
- 可信 Verilog/testbench 资产缺失，无法完成 Level-1 逻辑回归。
- 代表性 SRAM 功能仿真仍缺少审阅过的功能测试平台和 TIME 角色语义闭合。
- post-layout 仿真缺少刷新后的 extraction-rule provenance 与 layout-netlist 绑定。
- 电源负例突变仍缺少 raw-GDS 支撑的几何修改 harness。

## Review Position

- 当前项目已经推进到真实服务器与当前工作树证据允许的边界。
- 可以进入统一人工审核，但不能宣称 decoder、功能仿真、post-layout 或工业签核已经闭合。
