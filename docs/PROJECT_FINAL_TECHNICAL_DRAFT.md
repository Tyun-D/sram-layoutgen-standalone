# Project Final Technical Draft

## 研究目标
在不重写既有正式 GDS、不过度宣称工业能力、也不伪造外部权威的前提下，闭合项目级事实盘点、服务器真实能力审计、验证证据索引和人工审核包缺口。

## 总体架构
项目由 OpenRAM 参考基线、简化版 layoutgen 物理生成路径、OpenYield 语义网表/模块合同权威源，以及 Team B 的正式九单元物理库共同构成。本轮再审计额外补上了服务器工具、SPICE 烟测、电源拓扑和 DRC provenance/waiver 证据链。

## 可定制参数体系
当前 formal config inventory 共 `10` 行，source-backed variation `3`，locked baseline `1`，degraded historical `6`。

## 服务器真实能力
服务器当前真实可用且已记录版本/能力边界的开源 EDA 工具包括 `ngspice`、`Xyce`、`iverilog`、`vvp`、`verilator`、`klayout`、`magic`、`yosys`、`openroad`。因此项目当前最小可信仿真链路应建立在 `ngspice` 主链、`Xyce` 交叉验证，以及“若找到可信 Verilog 再启用 Icarus/Verilator”的保守选择之上。

## Team B 九单元
Team B 九单元已完成正式 GDS、machine gate、negative suite、integration、owner human review，并已并入主线。

## Decoder
decoder 当前状态为 `REBUILD_SELECTED_BUT_BLOCKED_BY_MISSING_EXECUTABLE_DECODER_GATE`。最终恢复取证仍未找回用户要求的 live `24-marker`、`M2-only`、`EN = horizontal_m3_bus`、`WL*_pre = vertical_m2_link` 历史基线，因此项目已经明确放弃“把当前新结果冒充历史 24-marker 版本”的路径，转入 `REPRODUCIBLE_DECODER_BASELINE_REBUILD`。但当前仓库仍然缺少 decoder-specific production gate、determinism、negative suite 与 marker-delta repair loop，所以 rebuild 只是正确方向，不等于已经具备可执行闭环。

## Multi-bank
multi-bank 当前状态为 `FUNCTIONAL_TOP_LEVEL_BLOCKED_BY_MISSING_AUTHORITY`。当前 canonical bank contract 只支持单 bank，不能编造 bank-select/control netlist。

## 验证体系
项目目前能可靠宣称的验证范围是：真实 GDS、内部 DRC、connectivity、foreign-net、negative tests、determinism、明确记录的人工作图审核，以及本轮新增的真实服务器工具审计、模块级 SPICE 烟测、电源正向拓扑审计、6 项电源负例 mutation 审计和 DRC provenance/waiver 审计。外部 LVS/PEX/signoff 仍未闭合。

## 仿真闭环状态
模块级逻辑仿真目前不是工具缺失，而是资产缺失：服务器有 `iverilog`/`verilator`，但当前工作树没有发现可信项目级 Verilog/testbench。晶体管级最小真实链路已经建立在 `ngspice` 上，并由 `Xyce` 保留为交叉验证备选；当前 `PNAND2`、`PNAND3`、`AND2`、`AND3`、`pdrive`、`wl_pdrive`、`pdrive2_for_pre`、`delay_chain`、`DFF`、`DFF_BUF` 都已在 `ngspice` 主链烟测通过，其中 `delay_chain` 已按 `9-stage loaded inverter chain` 的正确合同闭合。代表性 SRAM 功能仿真仍因缺少 project-owned functional TB 和 `clk/csb/web/TIME` 语义冻结而阻塞；post-layout 仿真仍因刷新后的 extraction-rule / LVS / PEX provenance 不足而阻塞。

## 电源正确性与 DRC provenance
基于 3 个 raw-source-backed extracted 报告配置的正向电源连通性/拓扑检查已经通过；此外，6 项 copied power-report bundle 负例 mutation 现在也能触发预期 rejection code，证明 validator 至少能拒绝缺失 rail、缺失 power via、child power pin 断开、VDD/VSS short 和 power-to-signal 接触这类错误。但这些结果仍不等于 IR drop、EM 或动态电源完整性 signoff。DRC provenance/waiver 审计当前结论为 `approved waiver count = 0`，项目正式目标仍是 `0 unapproved markers`，且在未恢复 decoder live baseline 前不得对 decoder 历史 marker 作 waiver 宣告。

## 工业级定位
当前平台最可辩护的优势是开放、可修改、参数传播透明、逻辑到物理绑定可追踪、验证器和负例可扩展、适合教学与研究。不得声称本平台在 PPA、可靠性、LVS/PEX/STA、IR/EM、foundry signoff 或硅验证能力上优于工业 SRAM compiler。

## 局限与未来工作
不得宣称 `PROJECT_COMPLETE`、`FINAL_RELEASE`、`TAPEOUT_READY`、`FOUNDRY_SIGNOFF` 或 `SILICON_PROVEN`。当前统一人工审核前仍保留五类明确 blocker：`trusted Verilog assets missing`、`project-owned SRAM functional TB binding missing`、`decoder executable rebuild gate missing`、`post-layout extraction provenance missing`、`remote push blocked by TLS/network failure`。

关于 `OWNER_A_LOGICAL_DATA_MODEL_V1`，当前仅采用保守表述：相关逻辑数据模型由项目团队共同完成，具体个人分工和 canonical source 尚未进一步核实；现有证据用于成果追溯，不作为源码已正式回收或主线已合并的证明。

## 作者贡献与 AI 边界
曲珈豪负责全部版图相关工作；OpenYield 网表设计、电路结构优化、电路级优化由其他组员负责。Codex/AI 仅用于代码辅助、自动化验证和报告整理，关键结论仍以真实源码、GDS 与验证证据闭合。
