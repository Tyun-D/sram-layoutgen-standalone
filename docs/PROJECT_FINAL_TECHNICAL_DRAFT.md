# Project Final Technical Draft

## 研究目标
在不重写既有正式 GDS 或伪造外部权威的前提下，闭合项目级事实盘点、参数体系、证据索引和报告材料缺口。

## 总体架构
项目由 OpenRAM 参考基线、简化版 layoutgen 物理生成路径、OpenYield 语义网表/模块合同权威源，以及 Team B 的正式九单元物理库共同构成。

## 可定制参数体系
当前 formal config inventory 共 `10` 行，source-backed variation `3`，locked baseline `1`，degraded historical `6`。

## Team B 九单元
Team B 九单元已完成正式 GDS、machine gate、negative suite、integration、owner human review，并已并入主线。

## Decoder
decoder 当前状态为 `BLOCKED_TECHNICAL`。Team B formal AND2/AND3 去除了一个旧 leaf blocker，但 decoder 仍停留在 metadata-only preplacement 和 output-handoff 阶段。

## Multi-bank
multi-bank 当前状态为 `FUNCTIONAL_TOP_LEVEL_BLOCKED_BY_MISSING_AUTHORITY`。当前 canonical bank contract 只支持单 bank，不能编造 bank-select/control netlist。

## 验证体系
项目目前能可靠宣称的验证范围是：真实 GDS、内部 DRC、connectivity、foreign-net、negative tests、determinism、以及明确记录的人工作图审核。外部 LVS/PEX/signoff 仍未闭合。

## 局限与未来工作
不得宣称 `PROJECT_COMPLETE`、`FINAL_RELEASE`、`TAPEOUT_READY`、`FOUNDRY_SIGNOFF` 或 `SILICON_PROVEN`。

## 作者贡献与 AI 边界
曲珈豪负责全部版图相关工作；OpenYield 网表设计、电路结构优化、电路级优化由其他组员负责。Codex/AI 仅用于代码辅助、自动化验证和报告整理，关键结论仍以真实源码、GDS 与验证证据闭合。
