# Netlist-to-Layout Goal

## Goal

在已锁定的 layoutgen golden flow 上，把 OpenYield 网表语义、模块候选、配置、floorplan、placement、routing、power 和验证证据收敛成可追溯的 netlist-to-layout 资产闭环。

## Ten Required Assets

- `NETLIST_SEMANTICS`: 网表 / module / instance / net / pin 连接语义 [COMPLETE]
- `PHYSICAL_IMPLEMENTATION_LIBRARY`: 模块物理实现库，包括 layoutgen cell、OpenYield module GDS、hardmacro 候选 [PARTIAL]
- `PIN_BBOX_RAIL_METADATA`: pin / bbox / rail / layer / access metadata [PARTIAL]
- `SRAM_CONFIGURATION`: SRAM 参数配置，包括 word_size、num_words、words_per_row、rows、cols、mux ratio [PARTIAL]
- `FLOORPLAN_RULES`: floorplan 规则，包括 array、row path、column path、control、top pin 区域 [PARTIAL]
- `PLACEMENT_RULES`: placement / abutment / orientation / pitch 对齐规则 [PARTIAL]
- `ROUTING_RULES`: WL、BL/BR、control、data、addr、enable 等 routing 规则 [PARTIAL]
- `POWER_PLAN`: VDD/GND rail overlap、stitch、abutment、top power pin 策略 [PARTIAL]
- `GDS_GENERATION_FLOW`: GDS generator / layoutgen golden flow / write_standalone 入口 [COMPLETE]
- `VERIFICATION_AND_TRACE`: GDS sanity、golden diff、module/net trace、DRC/LVS feasibility、人工 KLayout review [PARTIAL]

## Reuse Boundary

- 必须复用 M7 golden reference、M8R exact-match flow、M9 binding matrices、M10 source-backed trace、M11 config variation evidence、T1 inventory。
- 不能把 access_module、floorplan_proxy、historical hybrid reference、access-view complete SRAM prototype 当作最终物理实现依据。
## Current Gate State

- M11H 已确认 M11 config-aware translator v3。
- 该确认不扩大 claim 边界到 full raw OpenYield netlist compiler。
- 下一阶段允许进入 `M11A_MODULE_GDS_QUALIFICATION`。
## Current Qualification Stage

- M11A 正在对 `outputs/openyield_module_gds/` 的 20 个模块做 hardmacro 资格审查。
- 本阶段只确认 DIRECT_HARDMACRO_REPLACE / CONSTRAINT_EXTRACTION_ONLY / SEMANTIC_REFERENCE_ONLY / REJECTED 分类，不做完整 SRAM top 替换。
- 下一阶段需要先做 `M11B_PIN_BBOX_RAIL_METADATA_EXTRACTION`，之后才允许尝试 selective substitution。
## Current Smoke Substitution Stage

- M11C 只允许做 `sense_amp` 的一次 hardmacro smoke substitution。
- 本阶段不替换 `wordline_driver`、`column_mux`、`write_driver`、`CONTROL_LOGIC` 或任何其他模块。
- 本阶段只验证替换尝试是否能保持 layoutgen golden flow 的顶层 GDS 可生成、可解析且无明显结构破坏。
## Current Wordline Driver Smoke Substitution Stage

- M11C2 只允许做 `wordline_driver` 的一次隔离 wrapper hardmacro smoke substitution。
- 本阶段从 `M8R` locked baseline 出发，不叠加 `sense_amp` 结果，也不替换 `column_mux`、`write_driver`、`CONTROL_LOGIC` 或其他模块。
- 本阶段只验证替换是否真实进入 SRAM hierarchy、top GDS 是否仍可生成/可解析，以及是否需要后续人工 KLayout 收口。

## Current OpenRAM / OpenYield Alignment Stage

- M12O 先建立 `OpenRAM full reference`、`layoutgen golden`、`OpenYield/self-netlist semantics` 的三方对齐关系，再决定是否继续 M11V2 或进入参数化实现。
- 该阶段替代直接推进 `M11V2`，因为 OpenYield 仍未锁定单一权威完整 SRAM top netlist，CONTROL_LOGIC 差异和参数映射规则也还未定稿。
- 在 `M12N_LOCK_OPENYIELD_AUTHORITATIVE_NETLIST` 完成前，不能 claim 自研网表驱动完整 GDS 生成已完成。
- 当前推荐下一阶段：`M12N_LOCK_OPENYIELD_AUTHORITATIVE_NETLIST`。

## Current OpenYield Authority Lock Stage

- M12N 负责锁定 OpenYield 中真正可代表 SRAM 网表/网表生成链的 authority source，而不是继续模块替换或继续把 testbench 当作 layout authority。
- 当前已证明可以通过 Python generator 生成 sample SPICE/testbench netlist，但这仍不是可直接驱动 custom netlist-to-layout 的纯 SRAM top authority。
- 当前推荐下一阶段：`M12C_CONTROL_LOGIC_GAP_DEFINITION`。

## Current Clean Top Gate

- M12N2R 只做 TIME 角色证据修正与 gate 收口，不生成新的 GDS，不开始 CONTROL_LOGIC 物理实现，也不替换新模块。
- OpenYield 当前锁定版本：`1c34428d8b913963c4971d093b1a7c2df97a2509`；版本匹配：`True`；worktree clean：`True`。
- 最新 OpenYield 主源码证明 TIME 位于 `sram_compiler/subcircuits/`，属于网表设计电路，不属于独立测试激励。
- CONTROL_LOGIC 网表来源已锁定，但 CONTROL_LOGIC 物理实现、映射、DRC/LVS/signoff 仍未完成。
- 当前 TIME 角色结论：`ON_CHIP_CONTROL_LOGIC`。
- 当前推荐下一阶段：`M12C_CONTROL_LOGIC_GAP_DEFINITION`。

## Current Control Logic Gap Definition Stage

- M12C 只定义 OpenYield TIME / CONTROL_LOGIC 从网表到物理实现的缺口与映射计划，不实际完成新的 CONTROL_LOGIC 版图。
- M12N2R gate 已通过：`True`；TIME 角色：`ON_CHIP_CONTROL_LOGIC`。
- operation 拓扑审计结果：`READ_WRITE_SUPERSET_CANONICAL`；canonical topology：`READ_WRITE_SUPERSET`。
- 现有 physical cells 已盘点：ready=`15`，partial=`3`，reference_only=`1`，missing=`3`。
- 当前不能 claim CONTROL_LOGIC physical ready：`False`；custom netlist-driven layout generation：`False`。
- 当前推荐下一阶段：`M12C2_CONTROL_LOGIC_PHYSICAL_LIBRARY_QUALIFICATION`。

## M12C2 Qualification Goal

- Qualify only trusted reusable control-library cells.
- Exclude device-model names, debug-only composites, and false size aliases from later assembly claims.
- Locked next stage: `M12C3_CONTROL_LOGIC_PRIMITIVE_LAYOUT_GENERATOR_PLAN`

## M12C3 Primitive Generator Architecture Goal

- M12C2 只证明 qualification audit complete，不证明 reusable library ready。
- M12C3 锁定 FreePDK45-aware primitive generator architecture、tech contract、parameter naming/cache contract 和实现顺序。
- 当前 direct reuse count 仍为 `0`，不能 claim CONTROL_LOGIC physical ready。
- 若 trusted backend 不支持完整 width/length 参数化，则本轮不得生成 smoke GDS。
- 当前推荐下一阶段：`M12C3A_IMPLEMENT_PARAMETERIZED_DEVICE_AND_GATE_GENERATOR`。

## M12C3R Correction Gate

- M12C3R 先修正 primitive dimension units、source-derived physical variants、canonical naming 和 fixed 50 nm channel-length contract，再进入 OpenRAM adapter 实现。
- 原 M12C3 naming contract 已被 `SUPERSEDED_BY_M12C3R`。
- 不得再把 PINV1 等 logical alias 当作 physical variant identity。
- 当前 arbitrary channel length 不支持，但不阻塞 FreePDK45 V1，因为当前需求全部为 50 nm。
- 当前推荐下一阶段：`M12C3A_IMPLEMENT_PARAMETERIZED_DEVICE_AND_GATE_GENERATOR`。

## M12C3A Primitive Generator

- M12C3R correction gate passed and M12C3A concrete primitive generation completed.
- concrete drive scales 16x16: `{'address_bits': 4, 'clk_dff_count': 22, 'ref_dff_count': 22, 'clk_drive_scale': 1.0, 'pre_col_scale': 0.26153846153846155, 'pre_pmos_scale': 1.0, 'pre_drive_scale': 1, 'w_en_scale': 1, 'resolved_scales': {'pdrive': 1.0, 'pdrive2_for_pre': 1, 'w_en_scale': 1}}`
- concrete drive scales 64x8: `{'address_bits': 6, 'clk_dff_count': 16, 'ref_dff_count': 22, 'clk_drive_scale': 1.0, 'pre_col_scale': 0.13846153846153847, 'pre_pmos_scale': 4.0, 'pre_drive_scale': 1, 'w_en_scale': 1, 'resolved_scales': {'pdrive': 1.0, 'pdrive2_for_pre': 1, 'w_en_scale': 1}}`
- generated physical variants: `10` total, `9` PINV plus `1` TRANSMISSION_GATE.
- per-cell DRC total markers: `0`
- deterministic regeneration verified: `True`
- human review gate remains required: `True`
- next stage: `M12C3AH_PRIMITIVE_SMOKE_VISUAL_REVIEW`

## M12C3A3 Repair Constraint

- Scope remains limited to Transmission Gate repair evidence and does not authorize DFF, PNAND, AND, delay chain, TIME, CONTROL_LOGIC, or final SRAM generation.
- `CONTROL_LOGIC physical ready`, `LVS clean`, and `signoff ready` remain false claims.

## M12C3A4 Label Cleanup Gate

- Before composite generation, primitive reusable exports must present exactly one canonical top-level pin label per net and no leaked internal terminal text.
- This stage does not change any transistor/contact/well/implant/poly/metal geometry and does not claim LVS or signoff closure.
