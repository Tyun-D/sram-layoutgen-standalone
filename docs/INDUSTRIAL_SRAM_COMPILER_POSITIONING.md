# Industrial SRAM Compiler Positioning

## Current Platform Strengths

- 开放和可修改: 当前项目源码、脚本、GDS 生成路径与审计脚本都可检查和修改。
- 参数传播透明: `docs/FORMAL_SRAM_CONFIG_INVENTORY.*` 与当前新增的 server/simulation audits 让配置到网表/报告的传播可追踪。
- 逻辑到物理绑定可追踪: `outputs/M12N2_clean_openyield_sram_top/*`、`outputs/M7_correct_golden_reference/*` 和 `docs/FINAL_REPORT_SECTION_EVIDENCE_MATRIX.*` 提供源到网表/版图/报告的绑定证据。
- 验证器和负例可扩展: 当前仓库已有 Team B negative harness、DFF negative suite、以及本轮新增的 simulation/power audit skeleton，可继续扩展。
- 适合教学与研究: 可直接查看网表、布局、规则、报告与自动化脚本，便于解释设计取舍和验证边界。

## Industrial Tool Advantages

- 多工艺 / 多 Bank / 多端口: 当前项目仍只在有限 FreePDK45 / 单 bank 边界内有可信证据；工业编译器通常覆盖更多工艺与更复杂端口组织。
- characterization: 工业工具通常自带稳定的 Liberty/时序/功耗 characterization 流程；当前项目没有同等级 characterization 闭环。
- PPA 优化: 工业编译器通常做深度面积/性能/功耗优化；当前项目不得宣称 PPA 优于工业工具。
- LVS / PEX / STA: 当前 worktree 没有刷新到可宣称的完整工业级 signoff 流程。
- IR / EM: 当前仅有 power connectivity / topology 正向证据，不等于 IR drop 或 EM signoff。
- 长期回归: 当前有局部自动化，但没有工业级多年维护的回归覆盖面与稳定性。
- foundry signoff: 当前项目不能宣称 foundry signoff。
- 硅验证: 当前项目不能宣称 silicon proven。

## Conservative Positioning

- 当前平台更适合作为开放研究型 SRAM generator / layout-audit / evidence-trace 平台。
- 当前平台不应宣称在 PPA、可靠性、签核或量产成熟度上优于工业 SRAM compiler。
- 当前最强的可辩护定位是: `open, inspectable, traceable, and extensible for education/research`, not `industrial signoff complete`.
