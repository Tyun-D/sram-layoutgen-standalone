# Interview Technical Evidence: 4 Questions

## 1. 服务器上真实可用的仿真与验证工具是什么，为什么这样选最小可信链路？

- 真实审计到的可用工具见 `docs/SERVER_EDA_TOOL_INVENTORY.csv` 与 `docs/SERVER_SIMULATOR_CAPABILITY_AUDIT.md`。
- 当前最小可信链路是 `ngspice` 主链 + `Xyce` 备选交叉验证，因为它们都在服务器上真实存在且已通过安全版本探测。
- `iverilog` / `verilator` 也是可用工具，但当前项目缺少可信 Verilog 资产，所以逻辑链路仍是 `tool-available but asset-blocked`。
- `delay_chain` 已经按正确的 `9-stage inverting` 合同在 `ngspice` 主链上闭合；`Xyce` 当前只保留为次链兼容性记录。

## 2. Decoder 为什么还不能宣称闭合？

- 当前恢复工作树没有发现用户要求的 live `24-marker` decoder 基线，也没有找到 `M2-only` 逐参数修复回路所依赖的专用 gate、negative suite、marker atlas 和 determinism harness。
- 因此当前不能把历史 decoder 资料当作可执行闭环输入，更不能跳过基线恢复直接宣称 DRC 收敛。
- 项目已经把路径切换到 `REPRODUCIBLE_DECODER_BASELINE_REBUILD`，但仍然缺少可执行的 decoder-specific production gate / determinism / negative-suite 闭环。

## 3. 电源正确性已经证明到什么程度，哪些还没有？

- `docs/POWER_ROUTING_CORRECTNESS_GATE.json` 证明 3 个 raw-source-backed extracted 配置的正向 power topology/connectivity 通过。
- 这些结果覆盖 child endpoint 归属、VDD/VSS 分离、rail 连续性、pin 可达性与组件唯一性。
- 这些结果不等于 `IR drop`、`EM`、动态电源完整性或 foundry signoff；不过本轮已经补上 6 个可执行的 power negative mutation case，并全部触发预期 rejection code。

## 4. 当前平台与工业 SRAM compiler 的差距应该如何诚实表述？

- 强项是开放、可修改、参数传播透明、逻辑到物理绑定可追踪、验证器可扩展、适合教学和研究。
- 工业工具的优势仍然在多工艺/多 bank/多端口覆盖、characterization、PPA 优化、LVS/PEX/STA、IR/EM、长期回归、foundry signoff 和硅验证。
- 因此项目当前最合适的对外表述是 `research/education-oriented evidence-trace platform`, not industrial signoff-complete compiler.

## 2026-07-30 Decoder Rebuild Follow-up

- Q: Did decoder remain a documentation-only blocker?
  A: No. The project now contains an executable decoder rebuild path with a machine gate and negative regressions. The blocker is asset authority: wildcard child pin abstractions and 2663 fresh-run DRC markers, not missing code.
- Q: Why is full SRAM functional simulation still blocked?
  A: Because the project has only partially frozen the top-level control/timing contract. `clk/csb/web` and `TIME` interface fields are bound, but project-owned read/write scheduling and sampling oracles remain unresolved.
