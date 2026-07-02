# OpenYield Layout Generator Architecture Proposal

## Goal

目标不是复刻 OpenRAM，也不是继续修当前 candidate GDS，而是抽取 OpenRAM 中完整 SRAM GDS 生成最关键的机制，并结合 OpenYield 网表/模块语义，构建一个更轻量、更特异、可融入当前项目的自研 SRAM layout generator。

## Evidence Basis

- OpenRAM compiler/top/bank/array/routing/verify 证据：
  - `/data1/qujh/OpenRAM/sram_compiler.py:18-64`
  - `/data1/qujh/OpenRAM/compiler/sram.py:23-158`
  - `/data1/qujh/OpenRAM/compiler/sram_config.py:14-214`
  - `/data1/qujh/OpenRAM/compiler/modules/sram_1bank.py:209-1296`
  - `/data1/qujh/OpenRAM/compiler/modules/bank.py:291-1033`
  - `/data1/qujh/OpenRAM/compiler/modules/port_address.py:159-260`
  - `/data1/qujh/OpenRAM/compiler/modules/port_data.py:193-823`
  - `/data1/qujh/OpenRAM/compiler/base/hierarchy_layout.py:1135-1615`
- 当前仓库已有能力：
  - `/data1/qujh/work/sram_layoutgen_step45_clean/sram_layoutgen/openyield_adapter/module_gds_generators.py:151-1227`
  - `/data1/qujh/work/sram_layoutgen_step45_clean/sram_layoutgen/openyield_adapter/top_level_assembly.py:280-1467`
  - `/data1/qujh/work/sram_layoutgen_step45_clean/sram_layoutgen/gds_writer.py:16-318`

## Proposed Architecture

### 1. OpenYield netlist parser

- `responsibility`：解析 OpenYield 网表语义、模块层次、端口角色、控制路径、bank/array 关系。
- `inputs`：OpenYield netlist、当前 mapping/handoff metadata。
- `outputs`：规范化的 SRAM topology graph。
- `why_it_matters`：当前仓库有 candidate assembly 元数据，但没有 full SRAM physical generation 所需的统一语义前端。

### 2. Canonical SRAM parameter model

- `responsibility`：把 `word_size / num_words / num_banks / words_per_row / ports` 转成 `num_rows / num_cols / col_mux_ratio / address widths / spare policies`。
- `inputs`：parser 输出的语义参数。
- `outputs`：不可变 `CanonicalSramParameters`。
- `why_it_matters`：OpenRAM 的 `sram_config` 证明参数模型必须先统一，否则所有模块都会重复做尺寸推导。
- `scope recommendation`：
  - 首版固定 `single_bank = True`
  - `num_ports_supported = 1`
  - `words_per_row supported = 1 or 2`
  - `column_mux_ratio supported = 1 or 2`

### 3. Module generator registry

- `responsibility`：为 row path、column path、array wrapper、control path、bank、top 分配生成器实现。
- `inputs`：`CanonicalSramParameters`、tech contract、semantic topology。
- `outputs`：模块级 layout object。
- `why_it_matters`：当前 `ModuleGDSGeneratorRegistry` 已证明 registry 模式适合这个项目，但现阶段缺少完整 SRAM 路径级 generator。

### 4. Topology-aware floorplanner

- `responsibility`：负责 `array / row decoder / wordline driver / precharge / sense amp / write driver / control logic` 的相对位置和 bbox 计算。
- `inputs`：模块尺寸、pin/rail 对齐要求、支持范围约束。
- `outputs`：bank/top placement plan。
- `why_it_matters`：OpenRAM 的 `bank.place_instances` 和 `sram_1bank.place_instances` 说明 SRAM floorplan 不是通用 pack 问题，而是拓扑问题。

### 5. SRAM-specialized router

- `responsibility`：只处理 SRAM 特有连线：
  - WL routing
  - BL/BR routing
  - column select routing
  - control routing
  - clock routing
- `inputs`：placement plan、pin locations、preferred layers。
- `outputs`：route shapes 与 via stacks。
- `why_it_matters`：当前不需要一个 OpenRAM 级别的通用 router，但必须有一套确定性的 SRAM 专用 router。

### 6. Power planner

- `responsibility`：统一处理：
  - VDD/GND pin 识别
  - local rails 拼接
  - tap/well contact strategy
  - top-level power export
- `inputs`：模块 rail metadata、tech power contract。
- `outputs`：power rails、power pins、optional stitch plan。
- `why_it_matters`：当前仓库已有 rail metadata 和 stitch plan 习惯，这应成为完整 SRAM flow 的一等结构。

### 7. Pin / label exporter

- `responsibility`：统一生成：
  - top-level logical pins
  - layout pin shapes
  - GDS labels
  - LEF pins
  - LVS-friendly names
- `inputs`：semantic pin contract、placed pin geometry。
- `outputs`：pin database + exported collateral。
- `why_it_matters`：OpenRAM 的经验是 pin naming 一致性必须在生成期建立，不能靠后处理补丁。

### 8. GDS writer

- `responsibility`：把 layout object 序列化为层次化 GDS。
- `inputs`：placed modules、route geometry、pins、labels。
- `outputs`：GDS。
- `why_it_matters`：当前仓库已有 `GDSWriter`，不应替换；应扩其前端 layout schema。

### 9. DRC/LVS hooks

- `responsibility`：提供可选外部验证入口，但不在生成器内部 claim signoff。
- `inputs`：导出的 GDS/SPICE/LEF。
- `outputs`：hook command、reports、artifacts。
- `why_it_matters`：这与当前项目的 capability boundary 保持一致；可验证，但不夸大 claim。

## Recommended Internal Data Flow

1. `OpenYield netlist parser`
2. `Canonical SRAM parameter model`
3. `Module generator registry`
4. `Array / row path / column path / control path generators`
5. `Topology-aware floorplanner`
6. `SRAM-specialized router`
7. `Power planner`
8. `Pin/label exporter`
9. `GDS writer`
10. `Optional DRC/LVS hooks`

## Recommended Implementation Boundaries

### Keep

- `sram_layoutgen/gds_writer.py`
- `sram_layoutgen/lef_writer.py`
- `sram_layoutgen/openram_placement.py`
- `sram_layoutgen/openyield_adapter/module_gds_generators.py` 中的 registry 思路
- `sram_layoutgen/openyield_adapter/top_level_assembly.py` 中的 metadata/report discipline

### Add

- `openyield_semantic_parser.py`
- `canonical_sram_parameters.py`
- `sram_module_registry.py`
- `array_wrapper_generator.py`
- `row_path_generator.py`
- `column_path_generator.py`
- `control_path_generator.py`
- `bank_generator.py`
- `top_level_sram_generator.py`
- `sram_router.py`
- `power_planner.py`
- `pin_exporter.py`

### Do Not Add Yet

- Full generic global router
- Multi-bank support
- Multi-port support
- Automatic timing-closure logic
- Signoff-claiming DRC/LVS closure logic

## Minimum Viable First Full SRAM Physical Generator

建议的第一阶段“完整 SRAM physical generator”最小范围：

- single bank
- single implicit read/write port
- words_per_row = 1 or 2
- column mux ratio = 1 or 2
- no write mask
- no multi-bank stitching
- no multi-port routing

这样可以覆盖当前 OpenYield candidate flow 已经支持的语义边界，同时避免把 OpenRAM 的全部复杂度带入。

## Final Recommendation

最值得沿用的不是 OpenRAM 的全部类结构，而是它的九个核心分层：

1. canonical parameter model
2. array wrapper
3. row path
4. column path
5. control path
6. bank floorplan
7. SRAM-specialized routing
8. pin/export consistency
9. verification hooks

对当前项目来说，最合理的路线是：保留现有 `GDSWriter + registry + evidence/report` 基础设施，新增一个 OpenYield-specific SRAM physical generation core，而不是把 candidate assembly 继续补丁式扩展成完整 SRAM 版图生成器。
