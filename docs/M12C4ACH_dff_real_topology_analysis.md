# M12C4ACH DFF Real Topology Analysis

本文件只依据当前 OpenYield 源码、M12C4R2 锁定的 source-exact 连接矩阵、以及实例绑定表生成。未使用经验补全。

## Part 1：DFF 源定义

- DFF 源文件路径: `/data1/qujh/work/external/OpenYield/sram_compiler/subcircuits/time_generate.py`
- DFF class 名称: `class dff(BaseSubcircuit)`
- DFF 逻辑子模块定义位置: `time_generate.py:185-255`
- DFF 顶层实例化位置:
  - `time_generate.py:275` `self.dff1 = dff(...)` in `class DFF_BUF`
  - `time_generate.py:432` `self.dff_addr = dff(...)` in `class ADDR_DFF`
  - `time_generate.py:470` `self.dff_data = dff(...)` in `class DATA_DFF`
- DFF 内部 child 原型创建顺序:
  1. `self.inv_dff = Pinv(...)` at `time_generate.py:202`
  2. `self.trans_dff = TransmissionGate(...)` at `time_generate.py:205`
- DFF 内部实例化顺序 (`add_dff`)：
  1. `inv1_clk` at `time_generate.py:216` -> `PINV` -> `["VDD", "VSS", "CLK", "CLKB"]`
  2. `inv2_D` at `time_generate.py:220` -> `PINV` -> `["VDD", "VSS", "D", "D_b"]`
  3. `tg1` at `time_generate.py:223` -> `TRANSMISSION_GATE` -> `["VDD", "VSS", "D_b", "z1", "CLK", "CLKB"]`
  4. `inv3` at `time_generate.py:227` -> `PINV` -> `["VDD", "VSS", "z1", "z2"]`
  5. `inv4` at `time_generate.py:231` -> `PINV` -> `["VDD", "VSS", "z2", "z3"]`
  6. `tg2` at `time_generate.py:234` -> `TRANSMISSION_GATE` -> `["VDD", "VSS", "z3", "z1", "CLKB", "CLK"]`
  7. `inv5` at `time_generate.py:239` -> `PINV` -> `["VDD", "VSS", "z2", "z4"]`
  8. `tg3` at `time_generate.py:242` -> `TRANSMISSION_GATE` -> `["VDD", "VSS", "z4", "z5", "CLKB", "CLK"]`
  9. `inv6` at `time_generate.py:246` -> `PINV` -> `["VDD", "VSS", "z5", "Q"]`
  10. `inv7` at `time_generate.py:250` -> `PINV` -> `["VDD", "VSS", "Q", "QB"]`
  11. `tg4` at `time_generate.py:254` -> `TRANSMISSION_GATE` -> `["VDD", "VSS", "QB", "z5", "CLK", "CLKB"]`

## Part 2：完整实例连接表

| instance | type | input pins | output pins | connected nets |
|---|---|---|---|---|
| inv1_clk | PINV | A | Z | VDD->VDD; VSS->VSS; A->CLK; Z->CLKB |
| inv2_D | PINV | A | Z | VDD->VDD; VSS->VSS; A->D; Z->D_b |
| tg1 | TRANSMISSION_GATE | CTR_P,CTR_N | IN,OUT (bidirectional) | VDD->VDD; VSS->VSS; IN->D_b; OUT->z1; CTR_P->CLK; CTR_N->CLKB |
| inv3 | PINV | A | Z | VDD->VDD; VSS->VSS; A->z1; Z->z2 |
| inv4 | PINV | A | Z | VDD->VDD; VSS->VSS; A->z2; Z->z3 |
| tg2 | TRANSMISSION_GATE | CTR_P,CTR_N | IN,OUT (bidirectional) | VDD->VDD; VSS->VSS; IN->z3; OUT->z1; CTR_P->CLKB; CTR_N->CLK |
| inv5 | PINV | A | Z | VDD->VDD; VSS->VSS; A->z2; Z->z4 |
| tg3 | TRANSMISSION_GATE | CTR_P,CTR_N | IN,OUT (bidirectional) | VDD->VDD; VSS->VSS; IN->z4; OUT->z5; CTR_P->CLKB; CTR_N->CLK |
| inv6 | PINV | A | Z | VDD->VDD; VSS->VSS; A->z5; Z->Q |
| inv7 | PINV | A | Z | VDD->VDD; VSS->VSS; A->Q; Z->QB |
| tg4 | TRANSMISSION_GATE | CTR_P,CTR_N | IN,OUT (bidirectional) | VDD->VDD; VSS->VSS; IN->QB; OUT->z5; CTR_P->CLK; CTR_N->CLKB |

逐实例精确 pin -> net 映射：

### inv1_clk (PINV)
- `VDD -> VDD`
- `VSS -> VSS`
- `A -> CLK`
- `Z -> CLKB`

### inv2_D (PINV)
- `VDD -> VDD`
- `VSS -> VSS`
- `A -> D`
- `Z -> D_b`

### tg1 (TRANSMISSION_GATE)
- `VDD -> VDD`
- `VSS -> VSS`
- `IN -> D_b`
- `OUT -> z1`
- `CTR_P -> CLK`
- `CTR_N -> CLKB`

### inv3 (PINV)
- `VDD -> VDD`
- `VSS -> VSS`
- `A -> z1`
- `Z -> z2`

### inv4 (PINV)
- `VDD -> VDD`
- `VSS -> VSS`
- `A -> z2`
- `Z -> z3`

### tg2 (TRANSMISSION_GATE)
- `VDD -> VDD`
- `VSS -> VSS`
- `IN -> z3`
- `OUT -> z1`
- `CTR_P -> CLKB`
- `CTR_N -> CLK`

### inv5 (PINV)
- `VDD -> VDD`
- `VSS -> VSS`
- `A -> z2`
- `Z -> z4`

### tg3 (TRANSMISSION_GATE)
- `VDD -> VDD`
- `VSS -> VSS`
- `IN -> z4`
- `OUT -> z5`
- `CTR_P -> CLKB`
- `CTR_N -> CLK`

### inv6 (PINV)
- `VDD -> VDD`
- `VSS -> VSS`
- `A -> z5`
- `Z -> Q`

### inv7 (PINV)
- `VDD -> VDD`
- `VSS -> VSS`
- `A -> Q`
- `Z -> QB`

### tg4 (TRANSMISSION_GATE)
- `VDD -> VDD`
- `VSS -> VSS`
- `IN -> QB`
- `OUT -> z5`
- `CTR_P -> CLK`
- `CTR_N -> CLKB`

## Part 3：内部节点连接关系

OpenYield 当前 DFF 源码实际使用 `z1, z2, z3, z4, z5` 命名。以下直接使用真实 net name。

### VDD
连接：
- `inv1_clk.VDD`
- `inv2_D.VDD`
- `tg1.VDD`
- `inv3.VDD`
- `inv4.VDD`
- `tg2.VDD`
- `inv5.VDD`
- `tg3.VDD`
- `inv6.VDD`
- `inv7.VDD`
- `tg4.VDD`

### VSS
连接：
- `inv1_clk.VSS`
- `inv2_D.VSS`
- `tg1.VSS`
- `inv3.VSS`
- `inv4.VSS`
- `tg2.VSS`
- `inv5.VSS`
- `tg3.VSS`
- `inv6.VSS`
- `inv7.VSS`
- `tg4.VSS`

### D
连接：
- `inv2_D.A`

### Q
连接：
- `inv6.Z`
- `inv7.A`

### CLK
连接：
- `inv1_clk.A`
- `tg1.CTR_P`
- `tg2.CTR_N`
- `tg3.CTR_N`
- `tg4.CTR_P`

### CLKB
连接：
- `inv1_clk.Z`
- `tg1.CTR_N`
- `tg2.CTR_P`
- `tg3.CTR_P`
- `tg4.CTR_N`

### D_b
连接：
- `inv2_D.Z`
- `tg1.IN`

### z1
连接：
- `tg1.OUT`
- `inv3.A`
- `tg2.OUT`

### z2
连接：
- `inv3.Z`
- `inv4.A`
- `inv5.A`

### z3
连接：
- `inv4.Z`
- `tg2.IN`

### z4
连接：
- `inv5.Z`
- `tg3.IN`

### z5
连接：
- `tg3.OUT`
- `inv6.A`
- `tg4.OUT`

### QB
连接：
- `inv7.Z`
- `tg4.IN`

## Part 4：基于真实连接的 ASCII Topology

OpenYield uses real net names z1, z2, z3, z4, z5 in the current DFF source.

Clock/control path:
CLK
|- inv1_clk.A
|- tg1.CTR_P
|- tg2.CTR_N
|- tg3.CTR_N
`- tg4.CTR_P

CLKB
|- inv1_clk.Z
|- tg1.CTR_N
|- tg2.CTR_P
|- tg3.CTR_P
`- tg4.CTR_N

D data path and master-side loop:
D
`- inv2_D.A
   inv2_D.Z -> D_b
D_b
`- tg1.IN
   tg1.OUT -> z1
z1
|- inv3.A
`- tg2.OUT
   inv3.Z -> z2
z2
|- inv4.A
`- inv5.A
   inv4.Z -> z3
z3
`- tg2.IN
   tg2.OUT -> z1

Slave-side path and feedback:
z4
`- tg3.IN
   tg3.OUT -> z5
z5
|- inv6.A
`- tg4.OUT
   inv6.Z -> Q
Q
|- top.Q
`- inv7.A
   inv7.Z -> QB
QB
`- tg4.IN
   tg4.OUT -> z5

## Part 5：针对当前 OpenYield DFF 的版图人工检查指南

### 1. 哪些节点应该在版图中相连
- `VDD` 必须连接: `inv1_clk.VDD`, `inv2_D.VDD`, `tg1.VDD`, `inv3.VDD`, `inv4.VDD`, `tg2.VDD`, `inv5.VDD`, `tg3.VDD`, `inv6.VDD`, `inv7.VDD`, `tg4.VDD`
- `VSS` 必须连接: `inv1_clk.VSS`, `inv2_D.VSS`, `tg1.VSS`, `inv3.VSS`, `inv4.VSS`, `tg2.VSS`, `inv5.VSS`, `tg3.VSS`, `inv6.VSS`, `inv7.VSS`, `tg4.VSS`
- `D` 必须连接: `inv2_D.A`
- `Q` 必须连接: `inv6.Z`, `inv7.A`
- `CLK` 必须连接: `inv1_clk.A`, `tg1.CTR_P`, `tg2.CTR_N`, `tg3.CTR_N`, `tg4.CTR_P`
- `CLKB` 必须连接: `inv1_clk.Z`, `tg1.CTR_N`, `tg2.CTR_P`, `tg3.CTR_P`, `tg4.CTR_N`
- `D_b` 必须连接: `inv2_D.Z`, `tg1.IN`
- `z1` 必须连接: `tg1.OUT`, `inv3.A`, `tg2.OUT`
- `z2` 必须连接: `inv3.Z`, `inv4.A`, `inv5.A`
- `z3` 必须连接: `inv4.Z`, `tg2.IN`
- `z4` 必须连接: `inv5.Z`, `tg3.IN`
- `z5` 必须连接: `tg3.OUT`, `inv6.A`, `tg4.OUT`
- `QB` 必须连接: `inv7.Z`, `tg4.IN`

### 2. 哪些节点必须隔离
- `CLK` 与 `CLKB` 必须隔离。
- `D` 与 `Q` 必须隔离。
- `D_b`, `z1`, `z2`, `z3`, `z4`, `z5`, `QB` 彼此不能错误合并，除非同一真实 net。
- `VDD` / `VSS` 必须只连接各自电源节点，不得与任何信号 net 合并。

### 3. 哪些是反馈路径
- 主锁存反馈: `z1 <- tg2.OUT`, `z3 -> tg2.IN`，其中 `z1` 同时连 `inv3.A`，`z3` 同时连 `inv4.Z`。
- 从 `Q` 侧返回的反馈: `Q -> inv7.A -> QB -> tg4.IN`, 且 `tg4.OUT -> z5`。

### 4. 哪些是时钟控制路径
- `CLK` 控制端点: `inv1_clk.A`, `tg1.CTR_P`, `tg2.CTR_N`, `tg3.CTR_N`, `tg4.CTR_P`。
- `CLKB` 控制端点: `inv1_clk.Z`, `tg1.CTR_N`, `tg2.CTR_P`, `tg3.CTR_P`, `tg4.CTR_N`。
- 人工检查时必须确认四个 TG 的控制端没有接反：
  - `tg1`: `CTR_P=CLK`, `CTR_N=CLKB`
  - `tg2`: `CTR_P=CLKB`, `CTR_N=CLK`
  - `tg3`: `CTR_P=CLKB`, `CTR_N=CLK`
  - `tg4`: `CTR_P=CLK`, `CTR_N=CLKB`

### 5. 哪些金属连接如果错误会导致短路或拓扑破坏
- 如果把 `CLK` 和 `CLKB` 金属并到一起，会同时破坏 `tg1/tg2/tg3/tg4` 的控制。
- 如果把 `D_b`、`z1`、`z2`、`z3` 合并，会直接破坏主锁存器。
- 如果把 `z4`、`z5`、`Q`、`QB` 合并，会直接破坏从锁存器和输出极性。
- 如果把 `Q` 与 `D` 合并，会形成输入输出直短。
- 如果把任一 `TG.IN` 与 `TG.OUT` 之外的错误信号相连，会改变透明路径或反馈路径。
- 如果把任一 child `VDD`/`VSS` rail 借作信号通路，会形成 power-signal short。

## Part 6：验证来源

source_files_used:
- OpenYield 源码文件: `/data1/qujh/work/external/OpenYield/sram_compiler/subcircuits/time_generate.py`
  - `dff` 定义和 `dff.add_dff` 真实实例连接来源
  - `TransmissionGate` 定义用于 DFF TG child 原型
- OpenYield 源码文件: `/data1/qujh/work/external/OpenYield/sram_compiler/subcircuits/standard_cell.py`
  - `Pinv` 定义用于 DFF inverter child 原型
- OpenYield 源码文件: `/data1/qujh/work/external/OpenYield/sram_compiler/subcircuits/base_subcircuit.py`
- 本项目 topology 结果: `/data1/qujh/work/sram_layoutgen_step45_clean/docs/mapping/M12C4R2_all_branch_source_net_connection_matrix.csv`
- 本项目 DFF net contract: `/data1/qujh/work/sram_layoutgen_step45_clean/outputs/M12C4R2_dff_source_binding_gate/current_supported_config/M12C4R2_dff_net_contract.json`
- 本项目 DFF binding matrix: `/data1/qujh/work/sram_layoutgen_step45_clean/outputs/M12C4R2_dff_source_binding_gate/current_supported_config/M12C4R2_dff_instance_binding_matrix.csv`
- 使用的源码函数/方法:
  - `dff.__init__`
  - `dff.add_dff`
  - `DFF_BUF.add_dff_buf`
  - `ADDR_DFF.add_addr_dff_array`
  - `DATA_DFF.add_data_dff_array`
  - `BaseSubcircuit.X` 调用序列作为实例连接来源
- OpenYield commit SHA: `1c34428d8b913963c4971d093b1a7c2df97a2509`
- 当前 sram_layoutgen commit SHA: `25101b4436d1fb3f9f9577646085971fc33820c6`
- 未使用额外 topology JSON 或 SPICE 文件来补全 DFF 内部连接；当前结论直接来自 OpenYield 源码 `dff.add_dff` 的 `BaseSubcircuit.X` 调用，以及 M12C4R2 已提取矩阵的交叉核对。

如果后续需要确认更高层 TIME 中 DFF 的使用上下文，当前文件已足够定位 DFF 定义和 ARRAY/TIME 中的 DFF 模板实例化位置；本分析未使用任何经验性补全。
