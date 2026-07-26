# OpenRAM SRAM GDS Generation Audit Report

## Scope

本轮只做代码审计与学习清单整理，不修改 OpenRAM，也不为当前 `sram_layoutgen` 新增 SRAM GDS 生成代码。所有结论仅基于本地实际检查到的文件、类、函数和调用链；未找到的内容明确写为 `NOT_FOUND`。

## 1. OpenRAM 完整 SRAM GDS 生成入口审计

### 1.1 config 如何进入 compiler

- 入口文件是 `/data1/qujh/OpenRAM/sram_compiler.py:18-64`。
- 主流程是：
  - `openram.parse_args()` 读取命令行。
  - `openram.init_openram(config_file=args[0])` 载入配置文件。
  - `openram.setup_bitcell()` 建立 bitcell 相关全局配置。
  - `from openram import sram`
  - `s = sram()`
  - `s.save()`
- `why_it_matters`：配置并不是直接传给某个 bank/layout 类，而是先进入全局 `OPTS`，之后由 `compiler/sram.py` 汇总生成 SRAM 对象。

### 1.2 SRAM top class 在哪里

- `evidence_file`: `/data1/qujh/OpenRAM/compiler/sram.py:23-58`
- `class_or_function`: `class sram.__init__`
- 实际 top wrapper 是 `compiler/sram.py` 的 `class sram`。
- 该类会在没有显式 `sram_config` 时，用 `OPTS.word_size / num_words / num_banks / words_per_row / write_size` 构造 `sram_config`，随后导入 `openram.modules.sram_1bank` 并实例化 `self.s = sram_1bank(...)`。
- `why_it_matters`：真正的物理 top 不是 CLI 文件，而是 `compiler/sram.py` 里的 wrapper + `modules/sram_1bank.py` 的实现类。

### 1.3 bank class 在哪里

- `evidence_file`: `/data1/qujh/OpenRAM/compiler/modules/bank.py:18`
- `class_or_function`: `class bank`
- `why_it_matters`：这是 OpenRAM 把 bitcell array、port_data、port_address、column decoder 组装成单 bank SRAM physical bank 的核心类。

### 1.4 GDS writer 在哪里调用

- `evidence_file`: `/data1/qujh/OpenRAM/compiler/sram.py:99-158`
- `class_or_function`: `sram.save`
- 在 `save()` 中，backend 开启时会调用 `self.gds_write(gdsname)`，再调用 `lef_write`。
- `evidence_file`: `/data1/qujh/OpenRAM/compiler/base/hierarchy_layout.py:1431-1492`
- `class_or_function`: `layout.gds_write_file`, `layout.gds_write`
- 实际 GDS 递归展开和写盘在 `hierarchy_layout.py` 内部完成，依赖 `gdsMill.Gds2writer`。
- `why_it_matters`：layout 创建和 GDS 写出是分离的；`create_layout()` 负责几何，`gds_write()` 负责层次化序列化。

### 1.5 生成完整 GDS 的主调用链

1. `/data1/qujh/OpenRAM/sram_compiler.py:18-64` `main`
2. `/data1/qujh/OpenRAM/compiler/sram.py:23-58` `sram.__init__`
3. `/data1/qujh/OpenRAM/compiler/sram_config.py:77-149` `compute_sizes / recompute_sizes`
4. `/data1/qujh/OpenRAM/compiler/modules/sram_1bank.py:209-243` `sram_1bank.create_layout`
5. `/data1/qujh/OpenRAM/compiler/modules/bank.py:114-148` `bank.route_layout`
6. `bank` 下游调用 `port_address / port_data / bitcell_array` 等模块的 `create_layout`
7. `/data1/qujh/OpenRAM/compiler/sram.py:99-158` `sram.save`
8. `/data1/qujh/OpenRAM/compiler/base/hierarchy_layout.py:1473-1492` `gds_write`

`why_it_matters`：这条链路明确区分了参数推导、层次化模块搭建、layout 构造、最终 GDS 导出四个阶段。

## 2. 参数模型审计

### 2.1 关键参数与推导位置

- `evidence_file`: `/data1/qujh/OpenRAM/compiler/sram_config.py:14-149`
- `class_or_function`: `class sram_config`, `compute_sizes`, `recompute_sizes`
- 参数入口：
  - `word_size`
  - `num_words`
  - `num_banks`
  - `words_per_row`
  - `write_size`
  - `num_spare_rows`
  - `num_spare_cols`
- 物理维度推导：
  - `num_words_per_bank = num_words / num_banks`
  - `num_cols = words_per_row * word_size`
  - `num_rows = (num_words_per_bank / words_per_row) + num_spare_rows`
  - `col_addr_size = log2(words_per_row)`
  - `row_addr_size = ceil(log2(num_rows))`
  - `bank_addr_size = col_addr_size + row_addr_size`
- `why_it_matters`：OpenRAM 把“语义参数 -> 物理阵列维度 -> 地址位宽”压缩在一个 canonical config 中，这是最值得抽取的机制之一。

### 2.2 column mux ratio / words_per_row 如何决定

- `evidence_file`: `/data1/qujh/OpenRAM/compiler/sram_config.py:151-184`
- `class_or_function`: `estimate_words_per_row`
- 当 `words_per_row` 未指定时，OpenRAM先用 bitcell 面积估算接近方形的 bank，再从 `[1, 2, 4, 8, 16]` 中选择接近目标列复用比的值。
- `why_it_matters`：这是把逻辑容量转成物理长宽比的启发式，而不是把 `words_per_row` 当孤立参数。

### 2.3 ports 如何进入参数模型

- `evidence_file`: `/data1/qujh/OpenRAM/compiler/sram_config.py:185-214`
- `class_or_function`: `setup_multiport_constants`
- 通过 `OPTS.num_rw_ports / num_w_ports / num_r_ports` 派生：
  - `readwrite_ports`
  - `write_ports`
  - `read_ports`
  - `all_ports`
- `why_it_matters`：port 类型不是散落在各模块里的布尔分支，而是由统一配置模型向下游模块广播。

## 3. bitcell array 审计

### 3.1 bitcell 如何实例化

- `evidence_file`: `/data1/qujh/OpenRAM/compiler/modules/bitcell_array.py:13-63`
- `class_or_function`: `class bitcell_array`, `create_instances`
- `bitcell_array` 通过 `factory.create(module_type=OPTS.bitcell)` 获取 bitcell，并在 `(row, col)` 双循环内实例化。
- `evidence_file`: `/data1/qujh/OpenRAM/compiler/modules/bitcell_base_array.py:60-72`
- `class_or_function`: `get_bitcell_pins`
- 每个 bitcell 的连接按列绑定 BL/BR，按行绑定 WL，再拼上 `vdd/gnd`。
- `why_it_matters`：OpenRAM 的 array 构造不是“平面画图”，而是先有严格的 pin naming contract。

### 3.2 dummy / replica / boundary 如何处理

- `evidence_file`: `/data1/qujh/OpenRAM/compiler/modules/replica_bitcell_array.py:73-120`
- `class_or_function`: `add_modules`
- `replica_bitcell_array` 在主阵列两侧加 `replica_column`，并在上下增加 `dummy_row` 以承载 replica WL 负载。
- `evidence_file`: `/data1/qujh/OpenRAM/compiler/modules/replica_bitcell_array.py:278-301`
- `class_or_function`: `add_replica_columns`
- replica 列和 dummy row 的相对位置按 left/right RBL 规则显式放置。
- `evidence_file`: `/data1/qujh/OpenRAM/compiler/modules/capped_replica_bitcell_array.py:69-116`
- `class_or_function`: `add_modules`
- `capped_replica_bitcell_array` 在 replica array 外层再包 row/col cap 或 dummy array。
- `evidence_file`: `/data1/qujh/OpenRAM/compiler/modules/capped_replica_bitcell_array.py:273-296`
- `class_or_function`: `add_end_caps`
- 顶/底/左/右 cap 的镜像和 offset 会按 RBL 与主阵列 parity 调整。
- `why_it_matters`：OpenRAM 的完整 SRAM 物理阵列不是“主 bitcell array”一个对象，而是主阵列 + replica + dummy + cap 的包装层次。

### 3.3 row pitch / column pitch 如何获得

- `evidence_file`: `/data1/qujh/OpenRAM/compiler/modules/bitcell_base_array.py:172-198`
- `class_or_function`: `place_array`
- 行列 pitch 直接采用 `self.cell.height` / `self.cell.width`，并根据镜像规则放置。
- `evidence_file`: `/data1/qujh/OpenRAM/compiler/modules/bitcell_base_array.py:200-205`
- `class_or_function`: `get_column_offsets`
- 列物理偏移来自已放置实例的 `lx()`。
- `why_it_matters`：行列 pitch 不是单独查 tech rule，而是以 bitcell 实际版图 bbox 作为阵列 pitch 真值。

### 3.4 BL/BR/WL/VDD/GND 如何定义和导出

- `evidence_file`: `/data1/qujh/OpenRAM/compiler/modules/bitcell_base_array.py:26-59`
- `class_or_function`: `create_all_bitline_names`, `create_all_wordline_names`, `add_pins`
- 逻辑 pin 命名在 base array 统一生成。
- `evidence_file`: `/data1/qujh/OpenRAM/compiler/modules/bitcell_base_array.py:118-157`
- `class_or_function`: `add_bitline_pins`, `add_wl_pins`, `route_supplies`
- BL/BR 以整列纵向 pin 导出，WL 以整行横向 pin 导出，电源通过 `copy_layout_pin` 向上复制。
- `why_it_matters`：阵列对外暴露的是“整列/整行”接口，而不是单元级 pin。

## 4. row decoder / wordline driver 审计

### 4.1 decoder 如何生成

- `evidence_file`: `/data1/qujh/OpenRAM/compiler/modules/port_address.py:159-189`
- `class_or_function`: `add_modules`
- `port_address` 创建 `decoder` 和 `wordline_driver_array`。
- `evidence_file`: `/data1/qujh/OpenRAM/compiler/modules/port_address.py:191-205`
- `class_or_function`: `create_row_decoder`
- 地址输入 `addr_i` 接到 row decoder，输出 `dec_out_i`。
- `why_it_matters`：地址路径被封装成单独 `port_address` 模块，而不是散落在 bank 顶层。

### 4.2 WL driver 如何生成

- `evidence_file`: `/data1/qujh/OpenRAM/compiler/modules/wordline_buffer_array.py:48-63`
- `class_or_function`: `add_modules`
- `wordline_buffer_array` 使用 `inv_dec`，尺寸与 `cols` 相关。
- `evidence_file`: `/data1/qujh/OpenRAM/compiler/modules/port_address.py:220-234`
- `class_or_function`: `create_wordline_driver`
- `dec_out_i -> wl_i`，同时引入 `wl_en`。
- `why_it_matters`：WL driver 大小与列负载耦合，而不是固定单元。

### 4.3 decoder/WL driver 如何与 array row 对齐

- `evidence_file`: `/data1/qujh/OpenRAM/compiler/modules/port_address.py:236-260`
- `class_or_function`: `place_instances`
- decoder 放左侧原点，wordline driver array 紧贴其右侧；若有 RBL driver，再靠外侧放置。
- `evidence_file`: `/data1/qujh/OpenRAM/compiler/modules/bank.py:862-899`
- `class_or_function`: `route_port_address_out`
- `port_address` 的 `wl_i` 输出通过中间 jog 连接到 bitcell array 的对应 wordline pin。
- `why_it_matters`：这里体现了“逻辑顺序一致 + 物理侧向对接”的 row 对齐策略。

### 4.4 地址线和 WL 如何连接

- `evidence_file`: `/data1/qujh/OpenRAM/compiler/modules/port_address.py:116-157`
- `class_or_function`: `route_internal`
- `decode_i -> in_i` 经 `add_zjog` 和 `add_via_stack_center` 连接；`wl_en` 也会接入 WL driver 和可选 RBL driver。
- `why_it_matters`：OpenRAM 明确区分了“decoder 内部输出到 driver 输入”和“driver 输出到 array WL”两段路径。

## 5. column path 审计

### 5.1 precharge / column mux / sense amp / write driver 如何组织

- `evidence_file`: `/data1/qujh/OpenRAM/compiler/modules/port_data.py:193-266`
- `class_or_function`: `add_modules`
- `port_data` 统一创建：
  - `precharge_array`
  - `sense_amp_array`
  - `column_mux_array`
  - `write_driver_array`
  - `write_mask_and_array`
- `why_it_matters`：column path 在 OpenRAM 中不是 bank 直接手搓，而是专门由 `port_data` 聚合。

### 5.2 它们如何与 bitcell column / BL / BR 对齐

- `evidence_file`: `/data1/qujh/OpenRAM/compiler/modules/port_data.py:438-479`
- `class_or_function`: `compute_instance_offsets`, `place_instances`
- column path 模块按固定垂直次序堆叠：
  - write mask
  - write driver
  - sense amp
  - column mux
  - precharge
- `evidence_file`: `/data1/qujh/OpenRAM/compiler/modules/port_data.py:553-618`
- `class_or_function`: `route_sense_amp_to_column_mux_or_precharge_array`
- 根据是否存在 column mux、是否有 spare col、是否双口，选择 `connect_bitlines` 或 `channel_route_bitlines`。
- `evidence_file`: `/data1/qujh/OpenRAM/compiler/modules/port_data.py:620-799`
- `class_or_function`: `route_write_driver_to_column_mux_or_precharge_array`
- 写路径同样按 mux/非 mux 两种拓扑连接。
- `why_it_matters`：column path 对齐的核心不是模块名，而是统一使用 `bit_offsets` 和 bitline pin contract。

### 5.3 words_per_row / mux ratio 如何影响布局

- `evidence_file`: `/data1/qujh/OpenRAM/compiler/modules/port_data.py:326-349`
- `class_or_function`: `create_column_mux_array`
- 只有 `col_addr_size > 0` 时才创建 column mux。
- `evidence_file`: `/data1/qujh/OpenRAM/compiler/modules/port_data.py:352-378`
- `class_or_function`: `create_sense_amp_array`
- `words_per_row == 1` 时 sense amp 直接接 `bl_i/br_i`；否则接 `bl_out_i/br_out_i`。
- `evidence_file`: `/data1/qujh/OpenRAM/compiler/modules/port_data.py:380-415`
- `class_or_function`: `create_write_driver_array`
- 写驱动在 `words_per_row > 1` 时同样接 mux 输出端。
- `why_it_matters`：column mux ratio 不是后处理 routing 选项，而是决定端口阵列连接拓扑的一级参数。

## 6. control logic 审计

### 6.1 control logic 生成哪些信号

- `evidence_file`: `/data1/qujh/OpenRAM/compiler/modules/control_logic.py:102-132`
- `class_or_function`: `setup_signal_busses`
- 标准 `control_logic` 输出包含：
  - `s_en`
  - `w_en`
  - `p_en_bar`
  - `wl_en`
  - `clk_buf`
- 内部 bus 还含 `rbl_bl_delay`, `gated_clk_bar`, `gated_clk_buf`, `we`, `we_bar`, `cs` 等。
- `why_it_matters`：外围控制不是只生成一两个 enable，而是把时序相关中间节点也显式建模。

### 6.2 delay chain / replica bitline 如何参与

- `evidence_file`: `/data1/qujh/OpenRAM/compiler/modules/control_logic.py:194-214`
- `class_or_function`: `create_delay`, `route_delay`
- 标准控制逻辑把 `rbl_bl` 接入 delay chain，生成 `rbl_bl_delay`，再参与 `p_en_bar` / `s_en` 等时序控制。
- `evidence_file`: `/data1/qujh/OpenRAM/compiler/modules/control_logic_delay.py:37-101`
- `class_or_function`: `add_modules`
- `control_logic_delay` 变体不依赖 RBL，而是使用 `multi_delay_chain` 和多阶段 glitch/delay pinout。
- `why_it_matters`：OpenRAM 至少有两种控制风格，说明“控制逻辑”应是可替换策略，而不是硬编码单实现。

### 6.3 control signals 如何连接外围模块

- `evidence_file`: `/data1/qujh/OpenRAM/compiler/modules/bank.py:677-719`
- `class_or_function`: `route_central_bus`
- bank 在 bitcell array 两侧建立垂直 central bus。
- `evidence_file`: `/data1/qujh/OpenRAM/compiler/modules/bank.py:1003-1033`
- `class_or_function`: `route_control_lines`
- control bus 通过 `p_en_bar / w_en / s_en` 连接到 `port_data`。
- `why_it_matters`：bank 内部已经出现专门的“控制分发骨架”，不只是普通点对点线。

## 7. floorplan 审计

### 7.1 bank 内部相对位置

- `evidence_file`: `/data1/qujh/OpenRAM/compiler/modules/bank.py:291-303`
- `class_or_function`: `place_instances`
- bank 会依次放置：
  - `bitcell_array`
  - `port_data`
  - `port_address`
  - `column_decoder`
- `evidence_file`: `/data1/qujh/OpenRAM/compiler/modules/bank.py:444-483`
- `class_or_function`: `place_port_data`
- `port_data` 上下分布，偶数 port 用 `MX`，奇数 port 用 `R0`。
- `evidence_file`: `/data1/qujh/OpenRAM/compiler/modules/bank.py:488-519`
- `class_or_function`: `place_port_address`
- `port_address` 左右分布，偶数 port `R0`，奇数 port `MY`。
- `why_it_matters`：bank floorplan 是明确的四象限布局，而不是任意 pack。

### 7.2 top-level SRAM 内部相对位置

- `evidence_file`: `/data1/qujh/OpenRAM/compiler/modules/sram_1bank.py:782-909`
- `class_or_function`: `place_instances`, `place_control`, `place_row_addr_dffs`, `place_dffs`
- `sram_1bank` 把 bank 放在原点；control logic 放在 bank 左侧或右侧外缘；row address DFF 放在 control logic 上方；col/data/wmask DFF 放在 bank 下方或上方通道区。
- `why_it_matters`：OpenRAM 的 top-level floorplan 有一套固定的 SRAM-specific 相对位置策略，不是通用 block placer。

### 7.3 spacing / offset / bbox 如何计算

- `evidence_file`: `/data1/qujh/OpenRAM/compiler/modules/bank.py:305-359`
- `class_or_function`: `compute_sizes`
- central bus width、decoder gap、column address bus width 都先算出来，再驱动 placement。
- `evidence_file`: `/data1/qujh/OpenRAM/compiler/modules/bank.py:639-675`
- `class_or_function`: `setup_routing_constraints`
- top-level `core_bbox`、`width`、`height` 基于所有实例的 `lx/rx/by/uy` 统计得到。
- `evidence_file`: `/data1/qujh/OpenRAM/compiler/base/hierarchy_layout.py:280-382`
- `class_or_function`: `find_lowest_coords`, `find_highest_coords`, `offset_all_coordinates`
- 整体 bbox 由实例、对象、pin 一起决定，并在最终阶段归一化到原点。
- `why_it_matters`：OpenRAM 的 bbox 是放置和 routing 后的结果，而不是预设常量。

## 8. routing 审计

### 8.1 signal routing API

- `evidence_file`: `/data1/qujh/OpenRAM/compiler/base/hierarchy_layout.py:1135-1319`
- `class_or_function`: `add_layout_pin`, `add_label_pin`, `add_label`, `add_path`, `add_wire`, `add_via`, `add_via_center`, `add_via_stack_center`
- `why_it_matters`：这些 primitive API 是所有模块布局和连线的基础抽象。

### 8.2 bus routing

- `evidence_file`: `/data1/qujh/OpenRAM/compiler/base/hierarchy_layout.py:1563-1615`
- `class_or_function`: `create_vertical_bus`, `create_horizontal_bus`, `create_bus`
- `why_it_matters`：bus 不是逐线手搓，而是统一按 pitch 生成，可同时返回可寻址 pin map。

### 8.3 channel routing

- `evidence_file`: `/data1/qujh/OpenRAM/compiler/base/channel_route.py:72-260`
- `class_or_function`: `class channel_route.route`
- 基于 interval overlap 和 vertical conflict graph 分配 trunk track。
- `why_it_matters`：OpenRAM 对中等复杂度并行连线使用专门 channel router，而不是只靠直连 jog。

### 8.4 wordline / bitline / control routing

- `evidence_file`: `/data1/qujh/OpenRAM/compiler/modules/bank.py:852-899`
- `class_or_function`: `route_port_address_out`
- wordline routing：driver 到 array WL。
- `evidence_file`: `/data1/qujh/OpenRAM/compiler/modules/bank.py:719-756`
- `class_or_function`: `route_port_data_to_bitcell_array`
- bitline routing：array 到 `port_data`。
- `evidence_file`: `/data1/qujh/OpenRAM/compiler/modules/bank.py:1003-1033`
- `class_or_function`: `route_control_lines`
- control routing：central bus 到 `port_data`。
- `why_it_matters`：不同网络类型有不同 routing 策略，不适合放进一个通用函数里。

### 8.5 via/contact handling

- `evidence_file`: `/data1/qujh/OpenRAM/compiler/base/route.py:21-147`
- `class_or_function`: `class route`
- 普通 rectilinear route 会自动在层变化处补 contact/via。
- `evidence_file`: `/data1/qujh/OpenRAM/compiler/base/hierarchy_layout.py:1303-1375`
- `class_or_function`: `add_via_stack_center`
- 跨多层 via stack 由公共 helper 生成。
- `why_it_matters`：via 处理需要被一等公民化，不应在模块代码中重复算 enclosure。

## 9. power routing 审计

### 9.1 VDD/GND pin 如何识别

- `evidence_file`: `/data1/qujh/OpenRAM/compiler/modules/bitcell_base_array.py:49-59`
- `class_or_function`: `add_pins`
- 阵列层统一声明 `vdd/gnd`。
- `evidence_file`: `/data1/qujh/OpenRAM/compiler/modules/bank.py:598-621`
- `class_or_function`: `route_supplies`
- bank 从 `bitcell_array / port_address / port_data / column_decoder` 复制 `vdd/gnd`，若 bitcell 有 `vpb/vnb` 则映射到 `vdd/gnd`。
- `why_it_matters`：供电识别同时依赖通用 pin 名和 bitcell 特有 body-bias pin。

### 9.2 rails 如何拼接 / top-level power 如何导出

- `evidence_file`: `/data1/qujh/OpenRAM/compiler/modules/capped_replica_bitcell_array.py:318-373`
- `class_or_function`: `route_supplies`
- 外围 cap/dummy 单元通过 side rail 拼接 `vdd/gnd`，并按 bitcell 声明的 `vdd_dir/gnd_dir` 选择水平或垂直导出方式。
- `evidence_file`: `/data1/qujh/OpenRAM/compiler/modules/sram_1bank.py:245-320`
- `class_or_function`: `route_supplies`
- top-level SRAM 可调用 `supply_router` 自动把 `vdd/gnd` 接到边界或 ring。
- `why_it_matters`：OpenRAM 不只复制电源 pin，还提供面向顶层导出的自动供电路由钩子。

### 9.3 tap / well contact 如何处理

- `evidence_file`: `/data1/qujh/OpenRAM/compiler/base/hierarchy_layout.py:231-259`
- `class_or_function`: `setup_contacts`
- tech active stack、nwell/pwell contact 会预构建为公共 contact 模块。
- `evidence_file`: `/data1/qujh/OpenRAM/compiler/modules/capped_replica_bitcell_array.py:69-116`
- `class_or_function`: `add_modules`
- 外围 row/col cap 与 dummy array 是 well/tap 边界组织的一部分。
- `why_it_matters`：tap/well contact 不是附属小修，而是阵列 wrapper 的组成部分。

## 10. pin / label / LEF / LVS 审计

### 10.1 top-level pin / GDS label 如何生成

- `evidence_file`: `/data1/qujh/OpenRAM/compiler/modules/sram_1bank.py:983-1053`
- `class_or_function`: `add_layout_pins`
- top-level SRAM 把 bank/control/DFF pin 上抬为芯片级 pin。
- `evidence_file`: `/data1/qujh/OpenRAM/compiler/base/hierarchy_layout.py:1160-1185`
- `class_or_function`: `add_label_pin`, `add_label`
- 必要时可以加 LVS correspondence label。
- `why_it_matters`：pin geometry 和调试 label 是两个不同层面的输出。

### 10.2 LEF pin 如何生成

- `evidence_file`: `/data1/qujh/OpenRAM/compiler/base/lef.py:70-185`
- `class_or_function`: `lef_write`, `lef_write_pin`
- LEF 直接遍历 `self.pins` 和 `self.get_pins(name)` 输出方向、用途、RECT/POLYGON。
- `why_it_matters`：LEF 抽象依赖 layout pin 数据结构一致性，而不是独立再生成一套 pin 定义。

### 10.3 SPICE netlist 如何对应 / LVS 命名一致性如何维护

- `evidence_file`: `/data1/qujh/OpenRAM/compiler/modules/bitcell_base_array.py:60-72`
- `class_or_function`: `get_bitcell_pins`
- 版图实例连接名与 netlist 连接名在实例创建时已对齐。
- `evidence_file`: `/data1/qujh/OpenRAM/compiler/modules/sram_1bank.py:145-207`
- `class_or_function`: `create_modules`, `connect_inst`
- top-level 实例连接使用统一 pin name contract。
- `why_it_matters`：LVS 一致性的核心不是后处理 rename，而是实例化时就保持命名合同一致。

## 11. DRC/LVS flow 审计

### 11.1 DRC/LVS 如何调用

- `evidence_file`: `/data1/qujh/OpenRAM/compiler/base/hierarchy_design.py:50-79`
- `class_or_function`: `DRC_LVS`
- 模块在 layout 完成后可直接写临时 SPICE/GDS，然后调用 `verify.run_drc/run_lvs`。
- `evidence_file`: `/data1/qujh/OpenRAM/compiler/verify/__init__.py:41-63`
- `class_or_function`: verification backend dispatch
- 具体 backend 可选 `klayout / magic / calibre / assura / none`。
- `why_it_matters`：验证流是 hook 化的，但入口 API 保持统一。

### 11.2 错误如何记录

- `evidence_file`: `/data1/qujh/OpenRAM/compiler/verify/klayout.py:26-99`
- `class_or_function`: `write_drc_script`, `run_drc`
- KLayout flow 会生成 `.lydrc` 脚本、`run_drc.sh`，并解析 report。
- `evidence_file`: `/data1/qujh/OpenRAM/compiler/verify/magic.py:67-315`
- `class_or_function`: `write_drc_script`, `run_drc`, `write_lvs_script`, `run_lvs`
- Magic flow 会生成 shell 脚本，并从标准输出/报告中统计错误数。
- `why_it_matters`：验证错误并不只存在内存中，而是通过脚本和报告文件留下可复查证据。

### 11.3 DRC/LVS 与 GDS/netlist 的关系

- `evidence_file`: `/data1/qujh/OpenRAM/compiler/base/hierarchy_design.py:61-71`
- `class_or_function`: `DRC_LVS`
- DRC/LVS 输入始终是临时导出的 GDS + LVS SPICE。
- `why_it_matters`：验证对象是“当前 layout 导出的外部工件”，不是内部对象图本身。

## 12. 可复用机制清单

### 12.1 must learn

1. `sram_config` 的 canonical 参数推导。
2. `sram_factory` 的模块注册与缓存复用。
3. `bitcell_base_array` 的统一 pin naming / pitch / placement contract。
4. `replica_bitcell_array + capped_replica_bitcell_array` 的 wrapper 化阵列封装。
5. `local_bitcell_array + global_bitcell_array` 的层次化 WL/局部阵列切分。
6. `port_address` 把 decoder + WL driver 组合成独立 address path。
7. `port_data` 把 precharge/mux/sense/write 组合成独立 column path。
8. `bank` 的 quadrant floorplan + central bus 模型。
9. `hierarchy_layout` 的 primitive + bus + via stack API。
10. `verify` 的统一 DRC/LVS hook。

### 12.2 can adapt

1. `supply_router` / `signal_escape_router` 的边界导出思路。
2. `lef.py` 的从 layout pin 自动生成 LEF 抽象。
3. channel router 的 conflict-graph 思路。
4. delay-chain-based control logic 作为策略插件。
5. replica WL 负载补偿机制。

### 12.3 should not copy

1. `OPTS` 全局状态驱动的强耦合架构。
2. 构造函数里直接跑 `DRC_LVS()` 的模式。
3. layout / verification / characterization 全塞进 `save()` 的大一统流程。
4. 针对多口/多银行的广泛条件分支，如果当前 OpenYield scope 不需要。
5. 过多依赖 tech-specific custom cell 属性名与动态 import 字符串。
6. 手工 placement heuristic 深嵌在类方法中的写法。
7. 把 full general-purpose router 作为第一阶段目标。
8. 直接照搬 OpenRAM 的 replica timing/control 假设。
9. 用 library cell 名称约定隐式传递语义。
10. 把 LEF/LVS 命名一致性留到后处理修补。

### 12.4 replace with OpenYield-specific logic

1. 用 OpenYield netlist/module semantics 替代 OpenRAM 的 `OPTS` 驱动实例化。
2. 用 OpenYield current scope 的 `single-bank/single-port/words_per_row 1|2` 约束简化架构。
3. 用现有 `module_gds_generators` registry 经验构建 SRAM module generator registry。
4. 用现有 `top_level_assembly` 的 contract-pin / rail metadata 思路替代 OpenRAM 的隐式 pin alias。
5. 用当前项目的 evidence/report discipline 把验证、限制、handoff 一并标准化。

## 13. 自研 OpenYield layout generator 建议架构

### 13.1 当前仓库已有能力

- `evidence_file`: `/data1/qujh/work/sram_layoutgen_step45_clean/sram_layoutgen/openyield_adapter/module_gds_generators.py:151-1227`
- `class_or_function`: `ModuleGDSGenerationPlan`, `ModuleLayoutGenerator`, `ModuleGDSGeneratorRegistry`, `run_module_gds_generation`
- 已有模块级 generator registry 和 standalone module GDS 生成能力。
- `evidence_file`: `/data1/qujh/work/sram_layoutgen_step45_clean/sram_layoutgen/openyield_adapter/top_level_assembly.py:280-1467`
- `class_or_function`: `OpenYieldTopLevelAssembler`
- 已有 candidate top-level assembly、routing handoff、rail stitch plan、pin map 构建能力。
- `evidence_file`: `/data1/qujh/work/sram_layoutgen_step45_clean/sram_layoutgen/gds_writer.py:16-318`
- `class_or_function`: `GDSWriter`
- 已有自研 GDS writer。

### 13.2 当前仓库尚未发现的完整 SRAM physical generator 核心

- 完整 SRAM top physical generator class：`NOT_FOUND`
- 完整 SRAM bank physical generator class：`NOT_FOUND`
- SRAM-specialized router：`NOT_FOUND`
- full DRC/LVS orchestration for generated SRAM physical GDS：`NOT_FOUND`
- `why_it_matters`：当前仓库已经有 L3/L4 candidate 组装能力，但没有 OpenRAM 意义上的完整 SRAM physical generation flow。

### 13.3 建议模块划分

1. `OpenYield netlist parser`
   - 解析 OpenYield 网表、模块层次、端口角色、控制路径语义。
2. `Canonical SRAM parameter model`
   - 统一推导 `word_size / num_words / words_per_row / num_rows / num_cols / addr bits / mux ratio`。
3. `Module generator registry`
   - 复用当前 registry 经验，但升级为 SRAM path-aware registry。
4. `Topology-aware floorplanner`
   - 专门处理 `array / row path / column path / control` 四大块相对位置。
5. `SRAM-specialized router`
   - 区分 WL、BL/BR、column select、control、clock，不做通用全局路由器。
6. `Power planner`
   - 统一处理 rail 拼接、tap/well/contact、top-level VDD/GND 导出。
7. `Pin/label exporter`
   - 同步生成 top pin、GDS label、LEF pin、LVS-friendly naming。
8. `GDS writer`
   - 复用当前 `GDSWriter`，但需要支持更完整的 layout object schema。
9. `DRC/LVS hooks`
   - 仅提供外部 hook，不把 closure/signoff 逻辑塞进生成器内核。

### 13.4 总结结论

- OpenRAM 的完整 SRAM GDS 生成流程是“参数模型 -> 层次化模块生成 -> 专用 floorplan/routing -> GDS/LEF/SPICE 导出 -> DRC/LVS hook”。
- 当前 `sram_layoutgen` 已拥有模块 registry、candidate top assembly、自研 GDS writer，但还没有完整 SRAM physical generator。
- 后续最合理路线不是复制 OpenRAM，而是抽取其 canonical 参数模型、array/port/bank 拆分方式、SRAM-specialized floorplan/routing 原语，再用 OpenYield 语义重建更轻量的自研生成器。
