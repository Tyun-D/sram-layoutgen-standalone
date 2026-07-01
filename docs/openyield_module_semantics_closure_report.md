# OpenYield Module Semantics Closure Report

This is the L0 netlist-semantics closure report. It is source-backed and intentionally stops before physical primitive or GDS closure.

## Scope Summary

- modules covered: `25`
- parameters covered: `20`
- connections covered: `26`
- config-variation rows: `7`
- layoutgen mapping rows: `22`

## Required Answers

1. OpenYield SRAM 的模块层次是什么？
OpenYield 当前没有显式 `SRAM_TOP`/`BANK` 类，真实层次来自 `Sram6TCoreTestbench.create_testbench()`：`bitcell_array` + `replica_array` + 可选 `dummy_array` + `CONTROL_LOGIC(TIME)` + `row_decoder` + `wordline_driver` + `precharge/column_mux/sense_amp/write_driver`。

2. 哪些模块是所有 SRAM 规格都需要的？
`bitcell_array, replica_array, row_decoder, wordline_driver, CONTROL_LOGIC, DELAY_CHAIN`。

3. 哪些模块是参数相关或可选的？
`dummy_array, column_mux, sense_amp, write_driver, DFF_ROW, PRECHARGE_ENABLE_PATH, SENSE_ENABLE_PATH, WRITE_ENABLE_PATH, WORDLINE_ENABLE_PATH, GATED_CLOCK_PATH`。

4. 不同 word_size / num_words / words_per_row 下，哪些模块数量或结构变化？
OpenYield 源码没有命名的 `word_size` / `num_words` / `words_per_row` 参数，当前只有 `num_rows` / `num_cols` / `choose_columnmux`。因此这三类逻辑规格变化在 L0 只能标记为“需要额外语义约定”，不能假设为源码内建规则。

5. 地址如何进入 decoder？
地址 `A[i]` 先进入 `ADDR_DFF`，形成 `A_dff[i]`，然后由 `create_decoder()` 把 `A_dff[i]` 送入 `DECODER_CASCADE`。

6. decoder 如何驱动 wordline driver？
`DECODER_CASCADE` 输出 `DEC_WL[i]`，`create_wl_driver()` 把该信号接到 `WORDLINEDRIVER.A`，同时把 `WL_EN` 接到 `WORDLINEDRIVER.B`，最终输出 `WL[i]`。

7. bitcell array、precharge、column mux、sense amp、write driver 之间如何连接？
读路径：`precharge -> BL/BLB -> column_mux(optional) -> sense_amp`。写路径：`DIN -> DATA_DFF -> write_driver -> BL/BLB -> bitcell_array`。当 `choose_columnmux=False` 时，`sense_amp` 直接接 `BL/BLB`。

8. control logic、delay chain、replica、DFF row、gated clock 的语义关系是什么？
`CONTROL_LOGIC(TIME)` 负责地址/数据 DFF、片选与写使能寄存、门控时钟、WL 使能，以及从 `replica_array` 的 `RBL` 经 `DELAY_CHAIN` 导出的 `rbl_delay/rbl_delay_bar`，进一步生成 `PRE/s_en/w_en`。

9. OpenYield 中的模块语义与当前 layoutgen 的模块对应关系是什么？
存储阵列、dummy、replica、wordline_driver、column_mux、sense_amp、write_driver 都有本地 counterpart。`TIME/control paths/decoder composite` 仍以 metadata/proxy/adapter 形式存在，未变成真正可摆放的统一本地模块。

10. 进入下一层 physical primitive closure 前，还缺哪些 L0 语义信息？
缺口主要在三个地方：一是逻辑规格参数和 OpenYield 行列参数之间的正式映射；二是 `TIME` 复合控制块的稳定分解边界；三是 decoder/control-path/local-routing 的 canonical naming contract。

## Module Status

- SEMANTICS_CLOSED modules: `bitcell_array, column_mux, dummy_array, precharge, replica_array, row_decoder, sense_amp, wordline_driver, write_driver`
- SOURCE_FOUND_PORTS_KNOWN modules: `DELAY_CHAIN, DFF_ROW, power_semantics`
- SOURCE_FOUND_CONNECTIONS_UNRESOLVED modules: `GATED_CLOCK_PATH, PRECHARGE_ENABLE_PATH, SENSE_ENABLE_PATH, WORDLINE_ENABLE_PATH, WRITE_ENABLE_PATH, wordline_decoder`
- PARAMETER_RULE_UNRESOLVED modules: `none`
- LOCAL_MAPPING_UNRESOLVED modules: `BANK, routing_semantics`
- NOT_FOUND_IN_OPENYIELD modules: `none`

## L0 Blocking Gaps

- OpenYield has no explicit SRAM_TOP/BANK hierarchy class; top-level SRAM semantics currently live in the transient testbench assembly path.
- There is no named OpenYield parameter set for word_size/num_words/words_per_row/num_banks/num_ports/write_mask; current source is row/column oriented instead.
- TIME is a composite control/timing generator, not a flat module, so control-path physical boundaries remain semantic-only.
- Column-mux ratio is not a first-class parameter; the current source hard-codes mux_in=2 when choose_columnmux is enabled.
- Decoder-to-wordline-driver integration is source-backed, but local layoutgen still treats decoder/control logic as metadata or proxy placement in several places.

## Recommended Next Step After L0

Do not enter full L1 closure yet. First freeze the canonical SRAM semantic contract: top-level ports, row/column/count formulas, control-path decomposition boundaries, and the authoritative mapping from OpenYield row/column semantics to local layoutgen word_size/rows/cols terminology.

## Key Derived Rules

- `num_rows`: `global.yaml num_rows; row address bits = ceil(log2(num_rows)); replica rows = num_rows+1; dummy-column rows = num_rows+3`
- `num_cols`: `global.yaml num_cols; data DFF width = num_cols; write-driver count = num_cols; read SA count = num_cols or num_cols/2 with mux`
- `addr_size`: `addr_size = ceil(log2(num_rows)) in current source`
- `column_mux_ratio`: `When choose_columnmux is true, testbench hard-codes mux_in=2; otherwise the path behaves as ratio 1.`
- `delay_chain_related_parameters`: `DelayChain is fixed 9-stage/4-load; WenDelayChain is instantiated only for write with num_rows=16 and num_cols=512, stages=6, loads_per_stage=4.`

## Representative Module Rows

| module | module_category | openyield_source_found | openyield_source_path | openyield_class_or_function | openyield_netlist_source | role_in_sram | ports_or_nodes | input_signals | output_signals | power_pins | clock_or_timing_signals | connected_upstream_modules | connected_downstream_modules | instance_count_rule | parameter_dependencies | is_parameterized | is_required_for_all_sram_configs | is_optional_or_config_dependent | local_layoutgen_counterpart | local_layoutgen_path | semantic_mapping_status | semantic_gap | next_required_action | evidence_files |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| SRAM_TOP | assembly | True | sram_compiler/testbenches/sram_6t_core_testbench.py | Sram6TCoreTestbench.create_testbench | PySpice testbench assembly | Implicit top-level SRAM assembly root for one-bank simulations and optimization entrypoints. | VDD,VSS,clk,csb,web,A[i],DIN[i],BL[i],BLB[i],WL[i],RBL,RBLB,control nets | clk,csb,web,A[i],DIN[i] | WL[i],BL[i],BLB[i],RBL,RBLB,SA_Q[*],SA_QB[*],control nets | VDD,VSS | clk,clk_buf,gated_clk_bar,gated_clk_buf,rbl_delay,rbl_delay_bar |  | BANK;CONTROL_LOGIC;row_decoder;wordline_driver;bitcell_array;replica_array;column_mux;sense_amp;write_driver;precharge | 1 implicit assembly per simulation | num_rows;num_cols;choose_columnmux;operation | True | True | False | hybrid/standalone top semantic contract | sram_layoutgen/netlist_writer.py | SOURCE_FOUND_PORTS_PARTIAL | OpenYield top assembly is a transient testbench, not a reusable top-level SRAM subckt/macro contract. | Freeze a canonical top-level SRAM interface independent of transient stimulus plumbing. | sram_compiler/testbenches/sram_6t_core_testbench.py;main_sram.py |
| bitcell_array | storage_array | True | sram_compiler/subcircuits/sram_6t_core.py | Sram6TCore | PySpice SubCircuitFactory | Physical storage core holding all normal SRAM cells. | VDD,VSS,BL[i],BLB[i],WL[i] | WL[i],BL[i],BLB[i] | shared bitline discharge/storage behavior | VDD,VSS | WL transitions, read/write bitline events | wordline_driver;precharge;write_driver | sense_amp;column_mux;replica_array coupling | num_rows * num_cols cells | num_rows;num_cols;sram_cell_type | True | True | False | storage array aggregation | sram_layoutgen/openyield_adapter/array_aggregation.py | SEMANTICS_CLOSED |  | Carry these row/column semantics unchanged into L1 primitive tiling. | sram_compiler/subcircuits/sram_6t_core.py;docs/mapping/openyield_netlist_to_gds_readiness_matrix.csv |
| row_decoder | decoder | True | sram_compiler/subcircuits/decoder.py | DECODER3_8;DECODER_CASCADE | PySpice hierarchical decoder | Decodes registered row address bits into one-hot decoder wordline intents. | VDD,VSS,EN,A0..A2,WL0..WL7 and cascade A[i],WL[i] | A[i],EN | WL[i] one-hot outputs | VDD,VSS | Address-dependent decode propagation | DFF_ROW;CONTROL_LOGIC | wordline_driver | DECODER3_8 groups of 8; cascade depth = ceil(ceil(log2(num_rows))/3) | num_rows;row_addr_size | True | True | False | decoder contracts / proxy rows | sram_layoutgen/openyield_adapter/decoder_row_rules.py;sram_layoutgen/openyield_adapter/decoder_output_contracts.py | SEMANTICS_CLOSED |  | Carry decoder bit ordering and enable cascading rules into the local semantic contract. | sram_compiler/subcircuits/decoder.py;docs/openyield_module_contracts.md |
| wordline_driver | row_driver | True | sram_compiler/subcircuits/wordline_driver.py | WordlineDriver | PySpice SubCircuitFactory | Boosts decoder output plus WL enable into the physical WL rail. | VDD,VSS,A,B,Z | A(decoder_input),B(wordline_enable) | Z(WL) | VDD,VSS | WL enable timing | row_decoder;CONTROL_LOGIC | bitcell_array;replica_array via RWL analogue | one instance per physical row | num_rows;num_cols | True | True | False | wordline driver adapter | sram_layoutgen/openyield_adapter/wordlinedriver_adapter.py | SEMANTICS_CLOSED |  | Preserve A/B/Z active-high semantics as the authoritative local mapping. | sram_compiler/subcircuits/wordline_driver.py;docs/openyield_wordlinedriver_adapter_report.md |
| column_mux | read_peripheral | True | sram_compiler/subcircuits/mux_and_sa.py;sram_compiler/testbenches/sram_6t_core_testbench.py | ColumnMux;Sram6TCoreTestbench.create_read_periphery | PySpice SubCircuitFactory + testbench group instantiation | Selects one of multiple BL/BLB pairs onto a sense-amp input pair. | VDD,VSS,SA_IN,SA_INB,SEL[i],SELB[i],BL[i],BLB[i] | SEL/SELB,BL[i],BLB[i] | SA_IN,SA_INB | VDD,VSS | SEL pulse timing | precharge;bitcell_array | sense_amp | If choose_columnmux is false, not instantiated; else group count = num_cols / 2 in current source. | choose_columnmux;num_cols;column_mux_ratio | True | False | True | column mux adapter | sram_layoutgen/openyield_adapter/columnmux_adapter.py;sram_layoutgen/openyield_adapter/columnmux_placement.py | SEMANTICS_CLOSED |  | Keep explicit note that current source proves only ratio-2 mux groups. | sram_compiler/subcircuits/mux_and_sa.py;sram_compiler/testbenches/sram_6t_core_testbench.py |
| sense_amp | read_peripheral | True | sram_compiler/subcircuits/mux_and_sa.py;sram_compiler/testbenches/sram_6t_core_testbench.py | SenseAmp;Sram6TCoreTestbench.create_read_periphery | PySpice SubCircuitFactory + per-group instantiation | Differential read sense amplifier with enable. | VDD,VSS,EN,IN,INB,Q,QB | EN,IN,INB | Q,QB | VDD,VSS | s_en | column_mux or bitcell_array | D_latch / readout path | Without mux: one per column; with mux: one per selected group. | choose_columnmux;num_cols | True | False | True | architecture adapter | sram_layoutgen/openyield_adapter/architecture_adapter.py;sram_layoutgen/openyield_adapter/senseamp_placement.py | SEMANTICS_CLOSED |  | Retain explicit Q/QB vs local single-ended dout mismatch note in the mapping layer. | sram_compiler/subcircuits/mux_and_sa.py;docs/openyield_senseamp_adapter_report.md |
| write_driver | write_peripheral | True | sram_compiler/subcircuits/precharge_and_write_driver.py;sram_compiler/testbenches/sram_6t_core_testbench.py | WriteDriver;Sram6TCoreTestbench.create_write_periphery | PySpice SubCircuitFactory + per-column instantiation | Drives BL/BLB for writes under write enable. | VDD,VSS,EN,DIN,BL,BLB | EN,DIN | BL,BLB | VDD,VSS | w_en | DFF_ROW;CONTROL_LOGIC | bitcell_array | one per physical column | num_cols | True | False | True | write driver adapter | sram_layoutgen/openyield_adapter/writedriver_adapter.py;sram_layoutgen/openyield_adapter/writedriver_placement.py | SEMANTICS_CLOSED |  | Carry EN/DIN/BL/BLB semantics unchanged into local contracts. | sram_compiler/subcircuits/precharge_and_write_driver.py;sram_compiler/testbenches/sram_6t_core_testbench.py |
| CONTROL_LOGIC | control_timing | True | sram_compiler/subcircuits/time_generate.py | TIME | Composite TIME subcircuit | Central composite block that latches controls, generates gated clocks, wordline enable, precharge enable, sense enable, and write enable. | VDD,VSS,clk,csb,web,clk_buf,clk_bar,cs_bar,cs,we_bar,we,gated_clk_bar,gated_clk_buf,wl_en,A[i],A_dff[i],DIN[i],DIN_dff[i],rbl,rbl_delay,rbl_delay_bar,s_en,w_en,PRE | clk,csb,web,A[i],DIN[i],rbl | clk_buf,clk_bar,cs_bar,cs,we_bar,we,gated_clk_bar,gated_clk_buf,wl_en,rbl_delay,rbl_delay_bar,s_en,w_en,PRE,A_dff[i],DIN_dff[i] | VDD,VSS | all internal control/timing nets | SRAM_TOP;replica_array | DFF_ROW;GATED_CLOCK_PATH;WORDLINE_ENABLE_PATH;PRECHARGE_ENABLE_PATH;SENSE_ENABLE_PATH;WRITE_ENABLE_PATH | one TIME block per top assembly | num_rows;num_cols;operation;control_timing_related_parameters | True | True | False | control decomposition metadata | sram_layoutgen/openyield_adapter/control_decomposition.py | SOURCE_FOUND_PORTS_PARTIAL | TIME mixes reusable control logic with transient stimulus assumptions and local layoutgen has no direct physical counterpart. | Freeze TIME decomposition into stable subcontracts before L1. | sram_compiler/subcircuits/time_generate.py;docs/openyield_time_control_decomposition_report.md |

## Connection Coverage Snapshot

| source_module | source_port_or_signal | target_module | target_port_or_signal | signal_name | signal_category | direction | is_power | is_clock | is_control | is_data | is_bitline | is_wordline | is_timing_path | evidence_source | confidence | unresolved_reason |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| SRAM_TOP | A[i] | DFF_ROW | A[i] | A[i] | address | input_to_register | False | False | False | False | False | False | False | sram_compiler/subcircuits/time_generate.py:501-537;sram_compiler/testbenches/sram_6t_core_testbench.py:1025-1040 | HIGH |  |
| DFF_ROW | A_dff[i] | row_decoder | A[i] | A_dff[i] | address | registered_address_to_decoder | False | False | False | False | False | False | False | sram_compiler/testbenches/sram_6t_core_testbench.py:336-384 | HIGH |  |
| row_decoder | WL[i] | wordline_driver | A | DEC_WL[i] | decoder_wordline | decoder_to_driver | False | False | True | False | False | True | False | sram_compiler/testbenches/sram_6t_core_testbench.py:375-426 | HIGH |  |
| CONTROL_LOGIC | wl_en | wordline_driver | B | WL_EN | control_enable | control_to_driver | False | False | True | False | False | False | True | sram_compiler/subcircuits/time_generate.py:640-657;sram_compiler/testbenches/sram_6t_core_testbench.py:416-421 | HIGH |  |
| wordline_driver | Z | bitcell_array | WL[i] | WL[i] | wordline | driver_to_array | False | False | True | False | False | True | True | sram_compiler/testbenches/sram_6t_core_testbench.py:416-421;978-982 | HIGH |  |
| bitcell_array | BL[i]/BLB[i] | precharge | BL/BLB | BL[i];BLB[i] | bitline | shared_bitline | False | False | False | False | True | False | False | sram_compiler/testbenches/sram_6t_core_testbench.py:461-473 | HIGH |  |
| precharge | BL/BLB | column_mux | BL[i]/BLB[i] | BL[i];BLB[i] | bitline | precharged_bitline_to_mux | False | False | False | False | True | False | False | sram_compiler/testbenches/sram_6t_core_testbench.py:497-512 | HIGH |  |
| column_mux | SA_IN/SA_INB | sense_amp | IN/INB | SA_IN[*];SA_INB[*] | read_data | mux_to_sense | False | False | False | True | False | False | False | sram_compiler/testbenches/sram_6t_core_testbench.py:567-589 | HIGH |  |
| bitcell_array | BL[i]/BLB[i] | sense_amp | IN/INB | BL[i];BLB[i] | read_data | direct_array_to_sense | False | False | False | True | True | False | False | sram_compiler/testbenches/sram_6t_core_testbench.py:579-589 | HIGH |  |
| sense_amp | Q/QB | SRAM_TOP | dout path | SA_Q[*];SA_QB[*] | read_data | sense_to_output | False | False | False | True | False | False | False | sram_compiler/testbenches/sram_6t_core_testbench.py:551-589;428-442 | MEDIUM | OpenYield top-level output is modeled through D_latch/observation nodes rather than a macro pin list. |
| SRAM_TOP | DIN[i] | DFF_ROW | DIN[i] | DIN[i] | write_data | input_to_register | False | False | False | True | False | False | False | sram_compiler/subcircuits/time_generate.py:507-555;sram_compiler/testbenches/sram_6t_core_testbench.py:625-646 | HIGH |  |
| DFF_ROW | DIN_dff[i] | write_driver | DIN | DIN_dff[i] | write_data | registered_data_to_driver | False | False | False | True | False | False | False | sram_compiler/testbenches/sram_6t_core_testbench.py:612-623 | HIGH |  |

## Variation Coverage Snapshot

| variation_axis | openyield_parameter | module_types_unchanged | instance_count_changes | structure_changes | routing_or_timing_changes | openyield_source_evidence | layoutgen_support_status | unresolved_gap |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| word_size changes | word_size | Module families stay conceptually the same only if local logic treats word_size as a derived alias. | not_source_backed | No explicit OpenYield structure rule because word_size is not a named parameter. | Read/write/sense path fanout would change if word_size is mapped onto num_cols or mux grouping. | not_found_in_source | partial_local_support_only | OpenYield source does not define word_size. |
| num_words changes | num_words | No direct OpenYield rule. | not_source_backed | No explicit OpenYield structure rule because num_words is not a named parameter. | Would affect decoder depth if mapped onto num_rows, but the mapping is external to source. | not_found_in_source | partial_local_support_only | Need a canonical num_words <-> num_rows/column_mux mapping. |
| words_per_row changes | words_per_row | Storage/peripheral module types stay the same if muxing semantics are generalized. | Potential sense_amp/column_mux group count changes. | Current source has only direct columns or hard-coded 2:1 mux behavior. | Would alter column select routing and read fanout timing. | sram_compiler/testbenches/sram_6t_core_testbench.py:475-549 | partial_local_support_only | No first-class words_per_row parameter exists. |
| addr_size changes | addr_size | Decoder, TIME, DFF_ROW, wordline driver families remain the same. | Address DFF count and decoder WL count scale with ceil(log2(num_rows)). | Decoder cascade depth changes when num_rows crosses powers of two / groups of eight. | Clock load and decoder enable fanout change. | sram_compiler/subcircuits/decoder.py:133-230;sram_compiler/subcircuits/time_generate.py:417-437 | supported_as_num_rows_derivative |  |
| column mux ratio changes | column_mux_ratio | bitcell_array/precharge/write_driver families stay the same. | sense_amp and column_mux instance counts change from num_cols to num_cols/ratio. | Current source only proves ratio 1 or 2 behavior. | SEL/SELB routing, sense fanout, and read timing paths change. | sram_compiler/testbenches/sram_6t_core_testbench.py:475-589 | partial_local_support_only | Need explicit parameterization beyond hard-coded mux_in=2. |
| write mask / write size changes | write_mask | not_source_backed | not_source_backed | No source-backed write-mask structure exists. | No source-backed write-mask routing or timing exists. | not_found_in_source | unsupported | OpenYield source has no write mask semantics. |
| port count changes | num_ports | not_source_backed | not_source_backed | No source-backed multi-port structure exists. | No source-backed multi-port routing/timing exists. | not_found_in_source | unsupported | OpenYield current source is effectively one implicit read/write port. |

## Layoutgen Mapping Snapshot

| openyield_module | openyield_source_path | local_layoutgen_module | local_layoutgen_path | mapping_type | mapping_status | known_aliases | semantic_mismatch | next_required_action |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| SRAM_TOP | sram_compiler/testbenches/sram_6t_core_testbench.py | standalone top assembly | sram_layoutgen/netlist_writer.py | PARTIAL_MATCH | metadata_only | top assembly;hybrid prototype | Local top uses word_size/rows/cols abstraction; OpenYield top is transient testbench assembly. | Freeze a canonical top-level SRAM semantic contract. |
| BANK | sram_compiler/testbenches/sram_6t_core_testbench.py |  | not_found | NO_LOCAL_COUNTERPART | unresolved | single implicit bank | No explicit BANK abstraction exists in either OpenYield source or current standalone flow. | Keep one-bank assumption until a bank object is introduced. |
| bitcell_array | sram_compiler/subcircuits/sram_6t_core.py | storage aggregation plan | sram_layoutgen/openyield_adapter/array_aggregation.py | PARTIAL_MATCH | mapped | SRAM_6T_CORE_*;cell_1rw array | OpenYield exposes a hierarchical subckt; local flow places imported hardcells. | Retain bitcell-array semantic aliasing. |
| dummy_array | sram_compiler/subcircuits/dummy_row_or_column.py | dummy aggregation plan | sram_layoutgen/openyield_adapter/array_aggregation.py | DIRECT_MATCH | mapped | Dummy_Row;Dummy_Column | Local flow currently uses only side dummy columns in standalone integration. | Document dummy-row omission if top-level floorplan excludes it. |
| replica_array | sram_compiler/subcircuits/replica_column.py | replica aggregation plan | sram_layoutgen/openyield_adapter/array_aggregation.py | DIRECT_MATCH | mapped | Replica_Column | Replica coupling to control timing is still metadata-only. | Keep RWL/RBL semantics explicit. |
| row_decoder | sram_compiler/subcircuits/decoder.py | decoder proxy plan | sram_layoutgen/openyield_adapter/decoder_row_rules.py | PARTIAL_MATCH | mapped_proxy_only | DECODER3_8;DECODER_CASCADE | Local flow has decoder metadata and proxy placement, not full assembled decoder routing. | Complete decoder composite contract. |
| wordline_decoder | sram_compiler/subcircuits/decoder.py;sram_compiler/subcircuits/wordline_driver.py | decoder output contracts | sram_layoutgen/openyield_adapter/decoder_output_contracts.py | PARTIAL_MATCH | mapped_proxy_only | row_decoder_to_wldriver | Wordline handoff is metadata-only. | Freeze handoff pin-side conventions before L1. |
| decoder_gate_cells | sram_compiler/subcircuits/standard_cell.py | gate-row packing | sram_layoutgen/openyield_adapter/gate_row_packer.py | ALIAS_MATCH | mapped | gen_inv;gen_nand2;gen_nand4 | OpenYield leaf gates are generic logic; local uses replacement macro aliases. | Keep alias list stable. |
| wordline_driver | sram_compiler/subcircuits/wordline_driver.py | wordline driver adapter | sram_layoutgen/openyield_adapter/wordlinedriver_adapter.py | DIRECT_MATCH | mapped | WORDLINEDRIVER;gen_wl_driver | Local macro is a hardcell replacement, not the literal transistor-level OpenYield subckt. | Preserve A/B/Z semantic contract. |
| wordline_driver_gate_cells | sram_compiler/subcircuits/wordline_driver.py;sram_compiler/subcircuits/standard_cell.py | gate-row packing | sram_layoutgen/openyield_adapter/gate_row_packer.py | PARTIAL_MATCH | mapped_proxy_only | PNAND2;Pinv | Leaf factoring exists, but assembled routing is not closed. | Keep leaf-vs-composite distinction explicit. |
| column_mux | sram_compiler/subcircuits/mux_and_sa.py | column mux adapter | sram_layoutgen/openyield_adapter/columnmux_adapter.py | ALIAS_MATCH | mapped | COLUMNMUX*;gen_col_mux | OpenYield mux may expose OUTB/SELB semantics that require repaired alias metadata. | Keep repaired alias evidence tied to this mapping. |
| sense_amp | sram_compiler/subcircuits/mux_and_sa.py | sense amp architecture adapter | sram_layoutgen/openyield_adapter/architecture_adapter.py | PARTIAL_MATCH | mapped_with_qb_drop | SENSEAMP | Local hardcell is single-ended; OpenYield exposes Q/QB. | Keep QB treatment explicit in the read-path contract. |
