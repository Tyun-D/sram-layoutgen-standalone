# OpenYield / OpenRAM 网表差异侦查报告

## 0. 本轮范围

本轮只做更新与侦查：检查 git 状态、拉取 OpenYield、扫描候选网表、静态解析 OpenRAM SPICE 与 OpenYield PySpice 子电路语义，并检查当前版图生成器结构。没有重构主生成流程，也没有删除已有文件。

## 1. 仓库状态与 OpenYield 版本

- 根目录 git status：`not a git repository at workspace root`
- `deliverables/sram_layoutgen_standalone` 有既有未提交修改，未清理、未覆盖；详见报告末尾“未提交修改”。
- OpenYield path: `third_party/OpenYield`
- OpenYield commit: `1c34428d8b913963c4971d093b1a7c2df97a2509`
- OpenYield branch: `main`
- OpenYield status after pull: `clean`
- pull result: `fast-forward to 1c34428d8b913963c4971d093b1a7c2df97a2509`

## 2. 网表候选文件

新版 OpenYield 已删除旧 `sim/*/*.sp` 示例 deck；当前仓库里可直接扫描到的 OpenYield SPICE 文件主要是 `tran_models/models_*.spice` 和 `size_optimization/model_lib/models.spice`。SRAM/memory/peripheral 的网表语义主要存在于 `sram_compiler/subcircuits/*.py` 和 `sram_compiler/testbenches/*.py`，由 PySpice 动态生成。

| group | path | ext | size_bytes | score |
| --- | --- | --- | --- | --- |
| current_layoutgen | deliverables/sram_layoutgen_standalone/build/klayout_hook_2x16/sram_2x16_wpr1_standalone_freepdk45.sp | .sp | 3455 | 12 |
| current_layoutgen | deliverables/sram_layoutgen_standalone/build/signoff_spice_2x16/sram_2x16_wpr1_standalone_freepdk45.sp | .sp | 3455 | 12 |
| current_layoutgen | deliverables/sram_layoutgen_standalone/build/signoff_spice_8x64/sram_8x64_wpr4_standalone_freepdk45.sp | .sp | 28517 | 9 |
| current_layoutgen | deliverables/sram_layoutgen_standalone/build/address_complete_2x16/sram_2x16_wpr1_fd45.sp | .sp | 11394 | 8 |
| current_layoutgen | deliverables/sram_layoutgen_standalone/build/audit_report_32x16/sram_16x32_wpr2_fd45.sp | .sp | 42741 | 8 |
| current_layoutgen | deliverables/sram_layoutgen_standalone/build/codex_bus_pitch_2x16/sram_2x16_wpr1_fd45.sp | .sp | 11582 | 8 |
| current_layoutgen | deliverables/sram_layoutgen_standalone/build/codex_clean_2x16/sram_2x16_wpr1_fd45.sp | .sp | 11582 | 8 |
| current_layoutgen | deliverables/sram_layoutgen_standalone/build/codex_connectivity_2x16/sram_2x16_wpr1_fd45.sp | .sp | 11582 | 8 |
| current_layoutgen | deliverables/sram_layoutgen_standalone/build/codex_control_guides_2x16/sram_2x16_wpr1_fd45.sp | .sp | 11582 | 8 |
| current_layoutgen | deliverables/sram_layoutgen_standalone/build/codex_drawn_routes_2x16/sram_2x16_wpr1_fd45.sp | .sp | 11582 | 8 |
| current_layoutgen | deliverables/sram_layoutgen_standalone/build/codex_final_2x16/sram_2x16_wpr1_fd45.sp | .sp | 11582 | 8 |
| current_layoutgen | deliverables/sram_layoutgen_standalone/build/codex_layer_audit_2x16/sram_2x16_wpr1_fd45.sp | .sp | 11582 | 8 |
| current_layoutgen | deliverables/sram_layoutgen_standalone/build/codex_local_tracks_2x16/sram_2x16_wpr1_fd45.sp | .sp | 11582 | 8 |
| current_layoutgen | deliverables/sram_layoutgen_standalone/build/codex_local_tracks_rowcompact_2x16/sram_2x16_wpr1_fd45.sp | .sp | 11582 | 8 |
| current_layoutgen | deliverables/sram_layoutgen_standalone/build/codex_local_tracks_safe2_2x16/sram_2x16_wpr1_fd45.sp | .sp | 11582 | 8 |
| current_layoutgen | deliverables/sram_layoutgen_standalone/build/codex_local_tracks_safe_2x16/sram_2x16_wpr1_fd45.sp | .sp | 11582 | 8 |
| current_layoutgen | deliverables/sram_layoutgen_standalone/build/codex_pin_access_2x16/sram_2x16_wpr1_fd45.sp | .sp | 11582 | 8 |
| current_layoutgen | deliverables/sram_layoutgen_standalone/build/codex_pin_access_routes2_2x16/sram_2x16_wpr1_fd45.sp | .sp | 11582 | 8 |
| current_layoutgen | deliverables/sram_layoutgen_standalone/build/codex_pin_access_routes_2x16/sram_2x16_wpr1_fd45.sp | .sp | 11582 | 8 |
| current_layoutgen | deliverables/sram_layoutgen_standalone/build/codex_promoted_routes_2x16/sram_2x16_wpr1_fd45.sp | .sp | 11582 | 8 |
| current_layoutgen | deliverables/sram_layoutgen_standalone/build/codex_regression_sweep/2x16_wpr1/sram_2x16_wpr1_fd45.sp | .sp | 11582 | 8 |
| current_layoutgen | deliverables/sram_layoutgen_standalone/build/codex_regression_sweep_colsel_cond/2x16_wpr1/sram_2x16_wpr1_fd45.sp | .sp | 11582 | 8 |
| current_layoutgen | deliverables/sram_layoutgen_standalone/build/codex_regression_sweep_colsel_wpr4plus/2x16_wpr1/sram_2x16_wpr1_fd45.sp | .sp | 11582 | 8 |
| current_layoutgen | deliverables/sram_layoutgen_standalone/build/codex_regression_sweep_rowdecode_gap/2x16_wpr1/sram_2x16_wpr1_fd45.sp | .sp | 11582 | 8 |
| current_layoutgen | deliverables/sram_layoutgen_standalone/build/codex_regression_sweep_trackalgo/2x16_wpr1/sram_2x16_wpr1_fd45.sp | .sp | 11582 | 8 |
| current_layoutgen | deliverables/sram_layoutgen_standalone/build/codex_regression_sweep_trackalgo_pruned/2x16_wpr1/sram_2x16_wpr1_fd45.sp | .sp | 11582 | 8 |
| current_layoutgen | deliverables/sram_layoutgen_standalone/build/codex_rowtrack_final_2x16/sram_2x16_wpr1_fd45.sp | .sp | 11582 | 8 |
| current_layoutgen | deliverables/sram_layoutgen_standalone/build/codex_smoke_2x16/sram_2x16_wpr1_fd45.sp | .sp | 11582 | 8 |
| current_layoutgen | deliverables/sram_layoutgen_standalone/build/compact_margin_32x16/sram_16x32_wpr2_fd45.sp | .sp | 42755 | 8 |
| current_layoutgen | deliverables/sram_layoutgen_standalone/build/complete_structured_2x16/sram_2x16_wpr1_fd45.sp | .sp | 11394 | 8 |
| current_layoutgen | deliverables/sram_layoutgen_standalone/build/full_layout_collection/_all_gds_and_reports/sram_2x16_wpr1__sram_2x16_wpr1_fd45.sp | .sp | 11322 | 8 |
| current_layoutgen | deliverables/sram_layoutgen_standalone/build/full_layout_collection/_all_gds_and_reports/sram_32x16_wpr1__sram_32x16_wpr1_fd45.sp | .sp | 46726 | 8 |
| current_layoutgen | deliverables/sram_layoutgen_standalone/build/full_layout_collection/sram_2x16_wpr1/sram_2x16_wpr1_fd45.sp | .sp | 11322 | 8 |
| current_layoutgen | deliverables/sram_layoutgen_standalone/build/full_layout_collection/sram_32x16_wpr1/sram_32x16_wpr1_fd45.sp | .sp | 46726 | 8 |
| current_layoutgen | deliverables/sram_layoutgen_standalone/build/full_periphery_2x16/sram_2x16_wpr1_fd45.sp | .sp | 5878 | 8 |
| current_layoutgen | deliverables/sram_layoutgen_standalone/build/full_sram_suite_final/2x16/sram_2x16_wpr1_fd45.sp | .sp | 11394 | 8 |
| current_layoutgen | deliverables/sram_layoutgen_standalone/build/global_pack_32x16/sram_16x32_wpr2_fd45.sp | .sp | 42755 | 8 |
| current_layoutgen | deliverables/sram_layoutgen_standalone/build/labeled_2x16/sram_2x16_wpr1_fd45.sp | .sp | 5878 | 8 |
| current_layoutgen | deliverables/sram_layoutgen_standalone/build/lane_route_32x16/sram_16x32_wpr2_fd45.sp | .sp | 42755 | 8 |
| current_layoutgen | deliverables/sram_layoutgen_standalone/build/occupancy_probe_32x16/sram_16x32_wpr2_fd45.sp | .sp | 42755 | 8 |
| current_layoutgen | deliverables/sram_layoutgen_standalone/build/periphery_plus_2x16/sram_2x16_wpr1_fd45.sp | .sp | 10272 | 8 |
| current_layoutgen | deliverables/sram_layoutgen_standalone/build/periphery_plus_clean2_2x16/sram_2x16_wpr1_fd45.sp | .sp | 10272 | 8 |
| current_layoutgen | deliverables/sram_layoutgen_standalone/build/periphery_plus_clean_2x16/sram_2x16_wpr1_fd45.sp | .sp | 10272 | 8 |
| current_layoutgen | deliverables/sram_layoutgen_standalone/build/pin_access_32x16/sram_16x32_wpr2_fd45.sp | .sp | 42755 | 8 |
| current_layoutgen | deliverables/sram_layoutgen_standalone/build/row_fold_32x16/sram_16x32_wpr2_fd45.sp | .sp | 42755 | 8 |
| current_layoutgen | deliverables/sram_layoutgen_standalone/build/semantic_32x16/sram_16x32_wpr2_fd45.sp | .sp | 42755 | 8 |
| current_layoutgen | deliverables/sram_layoutgen_standalone/build/semantic_addr_q_32x16/sram_16x32_wpr2_fd45.sp | .sp | 42755 | 8 |
| current_layoutgen | deliverables/sram_layoutgen_standalone/build/semantic_control_dff_32x16/sram_16x32_wpr2_fd45.sp | .sp | 42741 | 8 |
| current_layoutgen | deliverables/sram_layoutgen_standalone/build/semantic_reloc_32x16/sram_16x32_wpr2_fd45.sp | .sp | 42755 | 8 |
| current_layoutgen | deliverables/sram_layoutgen_standalone/build/semantic_reloc_apply_32x16/sram_16x32_wpr2_fd45.sp | .sp | 42755 | 8 |
| current_layoutgen | deliverables/sram_layoutgen_standalone/build/signoff_hook_final_2x16/sram_2x16_wpr1_fd45.sp | .sp | 3423 | 8 |
| current_layoutgen | deliverables/sram_layoutgen_standalone/build/signoff_namefix_2x16/sram_2x16_wpr1_fd45.sp | .sp | 3423 | 8 |
| current_layoutgen | deliverables/sram_layoutgen_standalone/build/smoke_2x16/sram_2x16_wpr1_fd45.sp | .sp | 11394 | 8 |
| current_layoutgen | deliverables/sram_layoutgen_standalone/build/codex_regression_sweep/16x16_wpr1/sram_16x16_wpr1_fd45.sp | .sp | 27774 | 7 |
| current_layoutgen | deliverables/sram_layoutgen_standalone/build/codex_regression_sweep_colsel_cond/16x16_wpr1/sram_16x16_wpr1_fd45.sp | .sp | 27774 | 7 |
| current_layoutgen | deliverables/sram_layoutgen_standalone/build/codex_regression_sweep_colsel_wpr4plus/16x16_wpr1/sram_16x16_wpr1_fd45.sp | .sp | 27774 | 7 |
| current_layoutgen | deliverables/sram_layoutgen_standalone/build/codex_regression_sweep_rowdecode_gap/16x16_wpr1/sram_16x16_wpr1_fd45.sp | .sp | 27774 | 7 |
| current_layoutgen | deliverables/sram_layoutgen_standalone/build/codex_regression_sweep_trackalgo/16x16_wpr1/sram_16x16_wpr1_fd45.sp | .sp | 27774 | 7 |
| current_layoutgen | deliverables/sram_layoutgen_standalone/build/codex_regression_sweep_trackalgo_pruned/16x16_wpr1/sram_16x16_wpr1_fd45.sp | .sp | 27774 | 7 |
| current_layoutgen | deliverables/sram_layoutgen_standalone/build/full_layout_collection/_all_gds_and_reports/sram_16x16_wpr1__sram_16x16_wpr1_fd45.sp | .sp | 27542 | 7 |
| current_layoutgen | deliverables/sram_layoutgen_standalone/build/full_layout_collection/sram_16x16_wpr1/sram_16x16_wpr1_fd45.sp | .sp | 27542 | 7 |
| current_layoutgen | deliverables/sram_layoutgen_standalone/technology/freepdk45/sp_lib/cell_1rw.sp | .sp | 359 | 7 |
| current_layoutgen | deliverables/sram_layoutgen_standalone/technology/freepdk45/sp_lib/cell_2rw.sp | .sp | 571 | 7 |
| current_layoutgen | deliverables/sram_layoutgen_standalone/technology/freepdk45/sp_lib/dff.sp | .sp | 1647 | 7 |
| current_layoutgen | deliverables/sram_layoutgen_standalone/technology/freepdk45/sp_lib/dummy_cell_1rw.sp | .sp | 385 | 7 |
| current_layoutgen | deliverables/sram_layoutgen_standalone/technology/freepdk45/sp_lib/dummy_cell_2rw.sp | .sp | 605 | 7 |
| current_layoutgen | deliverables/sram_layoutgen_standalone/technology/freepdk45/sp_lib/replica_cell_1rw.sp | .sp | 357 | 7 |
| current_layoutgen | deliverables/sram_layoutgen_standalone/technology/freepdk45/sp_lib/replica_cell_2rw.sp | .sp | 567 | 7 |
| current_layoutgen | deliverables/sram_layoutgen_standalone/technology/freepdk45/sp_lib/sense_amp.sp | .sp | 607 | 7 |
| current_layoutgen | deliverables/sram_layoutgen_standalone/technology/freepdk45/sp_lib/tri_gate.sp | .sp | 405 | 7 |
| current_layoutgen | deliverables/sram_layoutgen_standalone/technology/freepdk45/sp_lib/write_driver.sp | .sp | 866 | 7 |
| current_layoutgen | deliverables/sram_layoutgen_standalone/build/addr_isolation_audit_16x32/sram_16x32_wpr2_fd45.sp | .sp | 42741 | 5 |
| current_layoutgen | deliverables/sram_layoutgen_standalone/build/addr_isolation_audit_4x32/sram_4x32_wpr2_fd45.sp | .sp | 17291 | 5 |
| current_layoutgen | deliverables/sram_layoutgen_standalone/build/addr_isolation_audit_sweep/4x32_wpr1/sram_4x32_wpr1_fd45.sp | .sp | 21849 | 5 |
| current_layoutgen | deliverables/sram_layoutgen_standalone/build/addr_isolation_audit_sweep/4x32_wpr2/sram_4x32_wpr2_fd45.sp | .sp | 17291 | 5 |
| current_layoutgen | deliverables/sram_layoutgen_standalone/build/addr_isolation_audit_sweep/8x64_wpr4/sram_8x64_wpr4_fd45.sp | .sp | 40926 | 5 |
| current_layoutgen | deliverables/sram_layoutgen_standalone/build/address_complete_8x64/sram_8x64_wpr4_fd45.sp | .sp | 40407 | 5 |
| current_layoutgen | deliverables/sram_layoutgen_standalone/build/aggressive_floorplan_repack_16x32/sram_16x32_wpr2_fd45.sp | .sp | 42741 | 5 |
| current_layoutgen | deliverables/sram_layoutgen_standalone/build/aggressive_floorplan_repack_4x32/sram_4x32_wpr2_fd45.sp | .sp | 17291 | 5 |
| current_layoutgen | deliverables/sram_layoutgen_standalone/build/aggressive_floorplan_repack_sweep/4x32_wpr1/sram_4x32_wpr1_fd45.sp | .sp | 21849 | 5 |

## 3. 本次用于对比的主文件

- OpenRAM primary SPICE: `build/openram_gds_only_2x16/openram_sram_2x16_1rw_freepdk45.sp`
- OpenRAM secondary/reference SPICE: `compiler/tests/golden/sram_2_16_1_freepdk45.sp`
- OpenYield SPICE/model files: `third_party/OpenYield/tran_models/models_FF.spice, third_party/OpenYield/tran_models/models_FS.spice, third_party/OpenYield/tran_models/models_SF.spice, third_party/OpenYield/tran_models/models_SS.spice, third_party/OpenYield/tran_models/models_TT.spice, third_party/OpenYield/size_optimization/model_lib/models.spice`
- OpenYield SRAM/peripheral PySpice sources: `third_party/OpenYield/sram_compiler/subcircuits/*.py`, `third_party/OpenYield/sram_compiler/testbenches/*.py`

## 4. 顶层端口对比

- OpenRAM primary top: `openram_sram_2x16_1rw_freepdk45`
- OpenRAM primary top ports: `din0[0], din0[1], addr0[0], addr0[1], addr0[2], addr0[3], csb0, web0, clk0, dout0[0], dout0[1], vdd, gnd`
- OpenRAM secondary top: `testsram`

| port category | OpenRAM top | OpenYield PySpice modules | note |
| --- | --- | --- | --- |
| address | addr0[0], addr0[1], addr0[2], addr0[3] | A0, A1, A2 | 需要按语义映射，不能只按名字匹配。 |
| bitline | - | BL, BLB, BLB{i}, BL{i} | OpenYield 子电路内部端口，OpenRAM 顶层通常不直接暴露。 |
| clock | clk0 | CLK | 需要按语义映射，不能只按名字匹配。 |
| control | - | EN, ENB | OpenYield 控制信号更细，包括 EN/ENB/wl_en/pre/s_en/w_en 等内部时序控制。 |
| data_in | din0[0], din0[1] | DIN | 需要按语义映射，不能只按名字匹配。 |
| data_out | dout0[0], dout0[1] | OUT, Q, QB, out | 需要按语义映射，不能只按名字匹配。 |
| ground | gnd | VSS | OpenYield 使用 VDD/VSS；OpenRAM/当前 layoutgen 多用 vdd/gnd，需要别名映射。 |
| other | csb0, web0 | A, B, C, CTR_N, CTR_P, D, IN, INB, RBL, RBLB, Z, in | 需要按语义映射，不能只按名字匹配。 |
| power | vdd | VDD | 需要按语义映射，不能只按名字匹配。 |
| wordline | - | WL, WL0, WL1, WL2, WL3, WL4, WL5, WL6, WL7, WL{i} | OpenYield 子电路内部端口，OpenRAM 顶层通常不直接暴露。 |

## 5. 模块层次对比

| aspect | OpenRAM | OpenYield | migration implication |
| --- | --- | --- | --- |
| top module | openram_sram_2x16_1rw_freepdk45 | OpenYield 没有提交固定 top .SUBCKT；由 `Sram6TCoreMcTestbench` 动态组装 `Circuit('SRAM_6T_Core_Testbench')` | 需要新增 PySpice/netlist emitter 或运行 OpenYield 生成 deck 后再做一对一 top 对比 |
| top ports | din0[0], din0[1], addr0[0], addr0[1], addr0[2], addr0[3], csb0, web0, clk0, dout0[0], dout0[1], vdd, gnd | 子电路端口以 VDD/VSS/BL/BLB/WL/EN/DIN/ADDR 等分散出现 | 需要建立 top pin canonicalization: vdd/VDD, gnd/VSS, addr/A*, din/DIN, dout/Q/QB |
| bitcell array | `openram_sram_2x16_1rw_freepdk45_bitcell_array`: ports=22, instances=32, types=openram_sram_2x16_1rw_freepdk45_pbitcell:32 | Sram6TCore: VDD,VSS, BLi, BLBi, WLi；可启用 equivalent model real_cell_mode | OpenYield 支持等效单元/RC；现有 layoutgen 只实例化真实 hardcell 阵列 |
| control logic | `openram_sram_2x16_1rw_freepdk45_control_logic_rw`: ports=11, instances=12, types=openram_sram_2x16_1rw_freepdk45_pinv_3:2, openram_sram_2x16_1rw_freepdk45_pand2:2, openram_sram_2x16_1rw_freepdk45_dff_buf_array:1, openram_sram_2x16_1rw_freepdk45_pdriver_0:1, openram_sram_2x16_1rw_freepdk45_pdriver_1:1, openram_sram_2x16_1rw_freepdk45_pand3:1, openram_sram_2x16_1rw_freepdk45_pand3_0:1, openram_sram_2x16_1rw_freepdk45_delay_chain:1, ... (+2) | OpenYield TIME 模块包含 addr/data DFF、gated clock、wl_en、rbl_delay、wen_delay、w_en/s_en/pre | OpenYield 控制逻辑更接近仿真时序，需要先映射控制信号 contract |
| peripherals | `openram_sram_2x16_1rw_freepdk45_port_data`: ports=15, instances=3, types=openram_sram_2x16_1rw_freepdk45_precharge_array:1, openram_sram_2x16_1rw_freepdk45_sense_amp_array:1, openram_sram_2x16_1rw_freepdk45_write_driver_array:1; `openram_sram_2x16_1rw_freepdk45_port_address`: ports=24, instances=3, types=openram_sram_2x16_1rw_freepdk45_hierarchical_decoder:1, openram_sram_2x16_1rw_freepdk45_wordline_driver_array:1, openram_sram_2x16_1rw_freepdk45_and2_dec_0:1 | PRECHARGE, WRITEDRIVER, COLUMNMUX, SENSEAMP, DECODER_CASCADE, WORDLINEDRIVER | 模块语义相近但端口顺序/控制极性/电源名不同 |

### OpenRAM parsed subckt overview

| subckt | ports | instances | mos | instance_types |
| --- | --- | --- | --- | --- |
| openram_sram_2x16_1rw_freepdk45_delay_chain | 4 | 45 | 0 | openram_sram_2x16_1rw_freepdk45_pinv_10:45 |
| openram_sram_2x16_1rw_freepdk45_bitcell_array | 22 | 32 | 0 | openram_sram_2x16_1rw_freepdk45_pbitcell:32 |
| dff | 5 | 22 | 22 | NMOS_VTG:11, PMOS_VTG:11 |
| openram_sram_2x16_1rw_freepdk45_dummy_array_2 | 23 | 19 | 0 | openram_sram_2x16_1rw_freepdk45_dummy_pbitcell:19 |
| openram_sram_2x16_1rw_freepdk45_dummy_array_3 | 23 | 19 | 0 | openram_sram_2x16_1rw_freepdk45_dummy_pbitcell:19 |
| openram_sram_2x16_1rw_freepdk45_hierarchical_decoder | 22 | 18 | 0 | openram_sram_2x16_1rw_freepdk45_and2_dec:16, openram_sram_2x16_1rw_freepdk45_hierarchical_predecode2x4:2 |
| openram_sram_2x16_1rw_freepdk45_replica_column | 21 | 17 | 0 | openram_sram_2x16_1rw_freepdk45_replica_pbitcell:17 |
| openram_sram_2x16_1rw_freepdk45_wordline_driver_array | 35 | 16 | 0 | openram_sram_2x16_1rw_freepdk45_wordline_driver:16 |
| openram_sram_2x16_1rw_freepdk45_control_logic_rw | 11 | 12 | 0 | openram_sram_2x16_1rw_freepdk45_pinv_3:2, openram_sram_2x16_1rw_freepdk45_pand2:2, openram_sram_2x16_1rw_freepdk45_dff_buf_array:1, openram_sram_2x16_1rw_freepdk45_pdriver_0:1, openram_sram_2x16_1rw_freepdk45_pdriver_1:1, openram_sram_2x16_1rw_freepdk45_pand3:1, openram_sram_2x16_1rw_freepdk45_pand3_0:1, openram_sram_2x16_1rw_freepdk45_delay_chain:1, openram_sram_2x16_1rw_freepdk45_pnand2_1:1, openram_sram_2x16_1rw_freepdk45_pdriver_4:1 |
| write_driver | 6 | 12 | 12 | pmos_vtg:6, nmos_vtg:6 |
| sense_amp | 6 | 11 | 11 | pmos_vtg:6, nmos_vtg:5 |
| openram_sram_2x16_1rw_freepdk45_hierarchical_predecode2x4 | 8 | 6 | 0 | openram_sram_2x16_1rw_freepdk45_and2_dec:4, openram_sram_2x16_1rw_freepdk45_pinv:2 |
| openram_sram_2x16_1rw_freepdk45_pbitcell | 5 | 6 | 6 | nmos_vtg:4, pmos_vtg:2 |
| openram_sram_2x16_1rw_freepdk45_pbitcell_0 | 5 | 6 | 6 | nmos_vtg:4, pmos_vtg:2 |
| openram_sram_2x16_1rw_freepdk45_pbitcell_1 | 5 | 6 | 6 | nmos_vtg:4, pmos_vtg:2 |
| openram_sram_2x16_1rw_freepdk45_pnand3_0 | 6 | 6 | 6 | pmos_vtg:3, nmos_vtg:3 |
| openram_sram_2x16_1rw_freepdk45_capped_replica_bitcell_array | 25 | 5 | 0 | openram_sram_2x16_1rw_freepdk45_replica_bitcell_array:1, openram_sram_2x16_1rw_freepdk45_dummy_array_1:1, openram_sram_2x16_1rw_freepdk45_dummy_array_0:1, openram_sram_2x16_1rw_freepdk45_dummy_array_2:1, openram_sram_2x16_1rw_freepdk45_dummy_array_3:1 |
| openram_sram_2x16_1rw_freepdk45 | 13 | 4 | 0 | openram_sram_2x16_1rw_freepdk45_bank:1, openram_sram_2x16_1rw_freepdk45_control_logic_rw:1, openram_sram_2x16_1rw_freepdk45_row_addr_dff:1, openram_sram_2x16_1rw_freepdk45_data_dff:1 |
| openram_sram_2x16_1rw_freepdk45_pdriver_0 | 4 | 4 | 0 | openram_sram_2x16_1rw_freepdk45_pinv_5:1, openram_sram_2x16_1rw_freepdk45_pinv_6:1, openram_sram_2x16_1rw_freepdk45_pinv_7:1, openram_sram_2x16_1rw_freepdk45_pinv_8:1 |
| openram_sram_2x16_1rw_freepdk45_pnand2 | 5 | 4 | 4 | pmos_vtg:2, nmos_vtg:2 |
| openram_sram_2x16_1rw_freepdk45_pnand2_0 | 5 | 4 | 4 | pmos_vtg:2, nmos_vtg:2 |
| openram_sram_2x16_1rw_freepdk45_pnand2_1 | 5 | 4 | 4 | pmos_vtg:2, nmos_vtg:2 |
| openram_sram_2x16_1rw_freepdk45_row_addr_dff | 11 | 4 | 0 | dff:4 |
| openram_sram_2x16_1rw_freepdk45_bank | 15 | 3 | 0 | openram_sram_2x16_1rw_freepdk45_capped_replica_bitcell_array:1, openram_sram_2x16_1rw_freepdk45_port_data:1, openram_sram_2x16_1rw_freepdk45_port_address:1 |
| openram_sram_2x16_1rw_freepdk45_dff_buf_0 | 6 | 3 | 0 | dff:1, openram_sram_2x16_1rw_freepdk45_pinv_0:1, openram_sram_2x16_1rw_freepdk45_pinv_1:1 |
| openram_sram_2x16_1rw_freepdk45_dummy_array_0 | 9 | 3 | 0 | openram_sram_2x16_1rw_freepdk45_dummy_pbitcell:3 |
| openram_sram_2x16_1rw_freepdk45_dummy_array_1 | 9 | 3 | 0 | openram_sram_2x16_1rw_freepdk45_dummy_pbitcell:3 |
| openram_sram_2x16_1rw_freepdk45_port_address | 24 | 3 | 0 | openram_sram_2x16_1rw_freepdk45_hierarchical_decoder:1, openram_sram_2x16_1rw_freepdk45_wordline_driver_array:1, openram_sram_2x16_1rw_freepdk45_and2_dec_0:1 |
| openram_sram_2x16_1rw_freepdk45_port_data | 15 | 3 | 0 | openram_sram_2x16_1rw_freepdk45_precharge_array:1, openram_sram_2x16_1rw_freepdk45_sense_amp_array:1, openram_sram_2x16_1rw_freepdk45_write_driver_array:1 |
| openram_sram_2x16_1rw_freepdk45_precharge_0 | 4 | 3 | 3 | pmos_vtg:3 |
| openram_sram_2x16_1rw_freepdk45_precharge_array | 8 | 3 | 0 | openram_sram_2x16_1rw_freepdk45_precharge_0:3 |
| openram_sram_2x16_1rw_freepdk45_replica_bitcell_array | 25 | 3 | 0 | openram_sram_2x16_1rw_freepdk45_bitcell_array:1, openram_sram_2x16_1rw_freepdk45_replica_column:1, openram_sram_2x16_1rw_freepdk45_dummy_array:1 |
| openram_sram_2x16_1rw_freepdk45_and2_dec | 5 | 2 | 0 | openram_sram_2x16_1rw_freepdk45_pnand2:1, openram_sram_2x16_1rw_freepdk45_pinv:1 |
| openram_sram_2x16_1rw_freepdk45_and2_dec_0 | 5 | 2 | 0 | openram_sram_2x16_1rw_freepdk45_pnand2:1, openram_sram_2x16_1rw_freepdk45_pinv:1 |
| openram_sram_2x16_1rw_freepdk45_data_dff | 7 | 2 | 0 | dff:2 |
| openram_sram_2x16_1rw_freepdk45_dff_buf_array | 9 | 2 | 0 | openram_sram_2x16_1rw_freepdk45_dff_buf_0:2 |
| openram_sram_2x16_1rw_freepdk45_dummy_array | 7 | 2 | 0 | openram_sram_2x16_1rw_freepdk45_dummy_pbitcell:2 |
| openram_sram_2x16_1rw_freepdk45_pand2 | 5 | 2 | 0 | openram_sram_2x16_1rw_freepdk45_pnand2_0:1, openram_sram_2x16_1rw_freepdk45_pdriver:1 |
| openram_sram_2x16_1rw_freepdk45_pand3 | 6 | 2 | 0 | openram_sram_2x16_1rw_freepdk45_pnand3_0:1, openram_sram_2x16_1rw_freepdk45_pdriver_2:1 |
| openram_sram_2x16_1rw_freepdk45_pand3_0 | 6 | 2 | 0 | openram_sram_2x16_1rw_freepdk45_pnand3_0:1, openram_sram_2x16_1rw_freepdk45_pdriver_3:1 |
| openram_sram_2x16_1rw_freepdk45_pdriver_1 | 4 | 2 | 0 | openram_sram_2x16_1rw_freepdk45_pinv_5:1, openram_sram_2x16_1rw_freepdk45_pinv_7:1 |
| openram_sram_2x16_1rw_freepdk45_pdriver_4 | 4 | 2 | 0 | openram_sram_2x16_1rw_freepdk45_pinv_5:2 |
| openram_sram_2x16_1rw_freepdk45_pinv | 4 | 2 | 2 | pmos_vtg:1, nmos_vtg:1 |
| openram_sram_2x16_1rw_freepdk45_pinv_0 | 4 | 2 | 2 | pmos_vtg:1, nmos_vtg:1 |
| openram_sram_2x16_1rw_freepdk45_pinv_1 | 4 | 2 | 2 | pmos_vtg:1, nmos_vtg:1 |
| openram_sram_2x16_1rw_freepdk45_pinv_10 | 4 | 2 | 2 | pmos_vtg:1, nmos_vtg:1 |
| openram_sram_2x16_1rw_freepdk45_pinv_2 | 4 | 2 | 2 | pmos_vtg:1, nmos_vtg:1 |
| openram_sram_2x16_1rw_freepdk45_pinv_3 | 4 | 2 | 2 | pmos_vtg:1, nmos_vtg:1 |
| openram_sram_2x16_1rw_freepdk45_pinv_5 | 4 | 2 | 2 | pmos_vtg:1, nmos_vtg:1 |
| openram_sram_2x16_1rw_freepdk45_pinv_6 | 4 | 2 | 2 | pmos_vtg:1, nmos_vtg:1 |
| openram_sram_2x16_1rw_freepdk45_pinv_7 | 4 | 2 | 2 | pmos_vtg:1, nmos_vtg:1 |
| openram_sram_2x16_1rw_freepdk45_pinv_8 | 4 | 2 | 2 | pmos_vtg:1, nmos_vtg:1 |
| openram_sram_2x16_1rw_freepdk45_pinv_9 | 4 | 2 | 2 | pmos_vtg:1, nmos_vtg:1 |
| openram_sram_2x16_1rw_freepdk45_sense_amp_array | 9 | 2 | 0 | sense_amp:2 |
| openram_sram_2x16_1rw_freepdk45_wordline_driver | 5 | 2 | 0 | openram_sram_2x16_1rw_freepdk45_pnand2:1, openram_sram_2x16_1rw_freepdk45_pinv:1 |
| openram_sram_2x16_1rw_freepdk45_write_driver_array | 9 | 2 | 0 | write_driver:2 |
| openram_sram_2x16_1rw_freepdk45_dummy_pbitcell | 5 | 1 | 0 | openram_sram_2x16_1rw_freepdk45_pbitcell_1:1 |
| openram_sram_2x16_1rw_freepdk45_pdriver | 4 | 1 | 0 | openram_sram_2x16_1rw_freepdk45_pinv_2:1 |
| openram_sram_2x16_1rw_freepdk45_pdriver_2 | 4 | 1 | 0 | openram_sram_2x16_1rw_freepdk45_pinv_9:1 |
| openram_sram_2x16_1rw_freepdk45_pdriver_3 | 4 | 1 | 0 | openram_sram_2x16_1rw_freepdk45_pinv_6:1 |
| openram_sram_2x16_1rw_freepdk45_replica_pbitcell | 5 | 1 | 0 | openram_sram_2x16_1rw_freepdk45_pbitcell_0:1 |

### OpenYield PySpice module overview

| role | source | class | NAME | NODES | M calls | X calls |
| --- | --- | --- | --- | --- | --- | --- |
| decoder | third_party/OpenYield/sram_compiler/subcircuits/decoder.py | DECODER3_8 | 'DECODER3_8' | ('VDD', 'VSS', 'EN', 'A0', 'A1', 'A2', 'WL0', 'WL1', 'WL2', 'WL3', 'WL4', 'WL5', 'WL6', 'WL7') | 0 | 5 |
| decoder | third_party/OpenYield/sram_compiler/subcircuits/decoder.py | DECODER_CASCADE | 'DECODER_CASCADE' | nodes | 0 | 1 |
| dummy row/column | third_party/OpenYield/sram_compiler/subcircuits/dummy_row_or_column.py | Dummy_Cell | 'Dummy_CELL' | ('VDD', 'VSS', 'BL', 'BLB', 'WL') | 6 | 0 |
| dummy row/column | third_party/OpenYield/sram_compiler/subcircuits/dummy_row_or_column.py | Dummy_Column | f'sram_{num_rows + 3}x1_Dummy_column' | ('VDD', 'VSS', 'BL', 'BLB', *[f'WL{i}' for i in range(num_rows + 3)]) | 0 | 1 |
| dummy row/column | third_party/OpenYield/sram_compiler/subcircuits/dummy_row_or_column.py | Dummy_Row | f'sram_1x{num_cols + 1}_Dummy_row' | ('VDD', 'VSS', *[f'BL{i}' for i in range(num_cols + 1)], *[f'BLB{i}' for i in range(num_cols + 1)], 'WL') | 0 | 1 |
| column mux | third_party/OpenYield/sram_compiler/subcircuits/mux_and_sa.py | ColumnMux | f'COLUMNMUX{num_in}' | tuple(nodes) | 6 | 0 |
| column mux | third_party/OpenYield/sram_compiler/subcircuits/mux_and_sa.py | SenseAmp | 'SENSEAMP' | ('VDD', 'VSS', 'EN', 'IN', 'INB', 'Q', 'QB') | 7 | 0 |
| precharge | third_party/OpenYield/sram_compiler/subcircuits/precharge_and_write_driver.py | Precharge | 'PRECHARGE' | ('VDD', 'ENB', 'BL', 'BLB') | 3 | 0 |
| precharge | third_party/OpenYield/sram_compiler/subcircuits/precharge_and_write_driver.py | WriteDriver | 'WRITEDRIVER' | ('VDD', 'VSS', 'EN', 'DIN', 'BL', 'BLB') | 12 | 0 |
| replica column | third_party/OpenYield/sram_compiler/subcircuits/replica_column.py | Replica_Cell | 'Replica_CELL' | ('VDD', 'VSS', 'RBL', 'RBLB', 'WL') | 16 | 0 |
| replica column | third_party/OpenYield/sram_compiler/subcircuits/replica_column.py | Replica_Column | f'sram_{num_rows + 1}x1_replica_column' | ('VDD', 'VSS', 'RBL', 'RBLB', *[f'WL{i}' for i in range(num_rows + 1)]) | 0 | 1 |
| 10T bitcell array | third_party/OpenYield/sram_compiler/subcircuits/sram_10t_core.py | Sram10TCell | 'SRAM_10T_CELL' | ('VDD', 'VSS', 'BL', 'BLB', 'WL') | 10 | 0 |
| 10T bitcell array | third_party/OpenYield/sram_compiler/subcircuits/sram_10t_core.py | Sram10TCore | f'SRAM_10T_CORE_{num_rows}x{num_cols}' | ('VDD', 'VSS', *[f'BL{i}' for i in range(num_cols)], *[f'BLB{i}' for i in range(num_cols)], *[f'WL{i}' for i in range(num_rows)]) | 0 | 1 |
| bitcell array | third_party/OpenYield/sram_compiler/subcircuits/sram_6t_core.py | Sram6TCell | 'SRAM_6T_CELL' | ('VDD', 'VSS', 'BL', 'BLB', 'WL') | 6 | 0 |
| bitcell array | third_party/OpenYield/sram_compiler/subcircuits/sram_6t_core.py | Sram6TCore | f'SRAM_6T_CORE_{num_rows}x{num_cols}' | ('VDD', 'VSS', *[f'BL{i}' for i in range(num_cols)], *[f'BLB{i}' for i in range(num_cols)], *[f'WL{i}' for i in range(num_rows)]) | 0 | 1 |
| control/timing logic | third_party/OpenYield/sram_compiler/subcircuits/time_generate.py | TransmissionGate | 'TRANSMISSION_GATE' | ('VDD', 'VSS', 'IN', 'OUT', 'CTR_P', 'CTR_N') | 2 | 0 |
| control/timing logic | third_party/OpenYield/sram_compiler/subcircuits/time_generate.py | pdrive | 'pdrive' | ('VDD', 'VSS', 'A', 'Z') | 0 | 4 |
| control/timing logic | third_party/OpenYield/sram_compiler/subcircuits/time_generate.py | pdrive2_for_pre | 'pdrive2_for_pre' | ('VDD', 'VSS', 'A', 'Z') | 0 | 2 |
| control/timing logic | third_party/OpenYield/sram_compiler/subcircuits/time_generate.py | wl_pdrive | 'wl_pdrive' | ('VDD', 'VSS', 'A', 'Z') | 0 | 2 |
| control/timing logic | third_party/OpenYield/sram_compiler/subcircuits/time_generate.py | dff | 'DFF' | ('VDD', 'VSS', 'D', 'Q', 'CLK') | 0 | 11 |
| control/timing logic | third_party/OpenYield/sram_compiler/subcircuits/time_generate.py | DFF_BUF | 'DFF_BUF' | ('VDD', 'VSS', 'D', 'Q', 'QB', 'CLK') | 0 | 3 |
| control/timing logic | third_party/OpenYield/sram_compiler/subcircuits/time_generate.py | DelayChain | 'delay_chain' | ('VDD', 'VSS', 'in', 'out') | 0 | 6 |
| control/timing logic | third_party/OpenYield/sram_compiler/subcircuits/time_generate.py | WenDelayChain | 'wen_delay_chain' | ('VDD', 'VSS', 'in', 'out') | 0 | 2 |
| control/timing logic | third_party/OpenYield/sram_compiler/subcircuits/time_generate.py | ADDR_DFF | 'ADDR_DFF' | nodes | 0 | 1 |
| control/timing logic | third_party/OpenYield/sram_compiler/subcircuits/time_generate.py | DATA_DFF | 'DATA_DFF' | nodes | 0 | 1 |
| control/timing logic | third_party/OpenYield/sram_compiler/subcircuits/time_generate.py | TIME | 'TIME' | nodes | 0 | 17 |
| wordline driver | third_party/OpenYield/sram_compiler/subcircuits/wordline_driver.py | WordlineDriver | 'WORDLINEDRIVER' | ('VDD', 'VSS', 'A', 'B', 'Z') | 0 | 2 |
| testbench/top circuit assembly | third_party/OpenYield/sram_compiler/testbenches/base_testbench.py | BaseTestbench |  |  | 0 | 0 |
| sense amplifier | third_party/OpenYield/sram_compiler/testbenches/parameter_factor.py | SenseAmpFactory |  |  | 0 | 0 |
| column mux | third_party/OpenYield/sram_compiler/testbenches/parameter_factor.py | ColumnMuxFactory |  |  | 0 | 0 |
| precharge | third_party/OpenYield/sram_compiler/testbenches/parameter_factor.py | PrechargeFactory |  |  | 0 | 0 |
| write driver | third_party/OpenYield/sram_compiler/testbenches/parameter_factor.py | WriteDriverFactory |  |  | 0 | 0 |
| wordline driver | third_party/OpenYield/sram_compiler/testbenches/parameter_factor.py | WordlineDriverFactory |  |  | 0 | 0 |
| testbench/top circuit assembly | third_party/OpenYield/sram_compiler/testbenches/parameter_factor.py | Sram6TCellFactory |  |  | 0 | 0 |
| testbench/top circuit assembly | third_party/OpenYield/sram_compiler/testbenches/parameter_factor.py | Sram6TCoreFactory |  |  | 0 | 0 |
| decoder | third_party/OpenYield/sram_compiler/testbenches/parameter_factor.py | DecoderCascadeFactory |  |  | 0 | 0 |
| dummy row/column | third_party/OpenYield/sram_compiler/testbenches/parameter_factor.py | DummyColumnFactory |  |  | 0 | 0 |
| dummy row/column | third_party/OpenYield/sram_compiler/testbenches/parameter_factor.py | DummyRowFactory |  |  | 0 | 0 |
| replica column | third_party/OpenYield/sram_compiler/testbenches/parameter_factor.py | ReplicaColumnFactory |  |  | 0 | 0 |
| control/timing logic | third_party/OpenYield/sram_compiler/testbenches/parameter_factor.py | TIMEFactory |  |  | 0 | 0 |
| testbench/top circuit assembly | third_party/OpenYield/sram_compiler/testbenches/parameter_factor.py | Sram10TCellFactory |  |  | 0 | 0 |
| testbench/top circuit assembly | third_party/OpenYield/sram_compiler/testbenches/parameter_factor.py | Sram10TCoreFactory |  |  | 0 | 0 |
| bitcell array | third_party/OpenYield/sram_compiler/testbenches/sram_6t_core_MC_testbench.py | Sram6TCoreMcTestbench |  |  | 0 | 0 |
| bitcell array | third_party/OpenYield/sram_compiler/testbenches/sram_6t_core_testbench.py | Sram6TCoreTestbench |  |  | 2 | 20 |

## 6. 外围电路差异

- bitcell array：OpenRAM primary SPICE 是已展开/层次化 `.SUBCKT`，可直接看到 `cell_6t`/`cell_1rw`、dummy、replica、bitline load 等实例；OpenYield 用 `Sram6TCore` 动态生成 `SRAM_6T_CORE_{rows}x{cols}`，端口为 `VDD/VSS/BLi/BLBi/WLi`，还支持 `real_cell_mode` 把非目标单元替换成等效 RC/功耗模型。
- wordline/decoder：OpenRAM 有 row decoder、wordline driver、replica bitline 等成熟层次；OpenYield 有 `DECODER3_8`、`DECODER_CASCADE`、`WORDLINEDRIVER`，端口和控制使能为 `EN/A0/A1/A2/WL*` 风格。
- precharge：OpenRAM 当前 hardcell/生成器常用 `bl/br/en/vdd/gnd` 或 `BL/BR/EN` 风格；OpenYield `PRECHARGE` 端口是 `VDD, ENB, BL, BLB`，没有显式 VSS，控制极性为 ENB。
- sense/write：OpenRAM/当前 layoutgen 的 `sense_amp/write_driver/tri_gate` 已有 GDS hardcell；OpenYield `SENSEAMP` 输出 `Q/QB`，`WRITEDRIVER` 使用 `EN/DIN/BL/BLB`，需要重新定义 dout/tri-state 映射。
- control/timing：OpenYield `TIME` 模块比当前 layoutgen 的简化 control glue 更丰富，含 addr/data DFF、clk buffer、gated clock、wl_en、rbl_delay、wen_delay、w_en、s_en、pre 等；这是后续最大差异点。
- power：OpenRAM 和当前 layoutgen 多为 `vdd/gnd`；OpenYield 源码统一使用 `VDD/VSS`。必须先做 power alias 和 pin order normalization。

## 7. 当前版图生成器缺失能力

- 缺少 OpenYield PySpice/生成后 SPICE 的通用解析器；当前 `NetlistWriter` 是输出器，不是输入解析器。
- 缺少 netlist-module-to-GDS-cell contract resolver，不能把 `WRITEDRIVER`、`PRECHARGE`、`TIME` 等自动映射到现有 hardcell/replacement macro。
- 缺少端口别名/极性系统，例如 `VSS->gnd`、`BLB->br`、`ENB->pchg_en`、`Q/QB->dout_int/tri`。
- 缺少控制逻辑综合/物理约束层：OpenYield 的 `TIME`/delay/wen/s_en/pre 不应直接硬塞进现有 routes，需要先转成 architecture contract。
- 缺少可聚合单元抽象，当前虽然使用 hardcell bbox/TEXT pin 和 abutment helper，但没有统一 footprint、rail sharing、abutment legality 数据结构。

## 8. 当前版图生成器结构检查

当前生成器主要是 spec/metadata/hardcell contract 驱动，结构在 standalone.py 和 netlist_writer.py 中程序化硬编码；尚不是 OpenYield/OpenRAM SPICE netlist 驱动的通用 layout compiler。

| file | role | classes | functions | hardcoded evidence |
| --- | --- | --- | --- | --- |
| deliverables/sram_layoutgen_standalone/sram_layoutgen/standalone.py | 主 floorplan/placement/routing/report 生成入口 | StandaloneSpec | package_root, default_pdk_root, load_bundled_freepdk45, build_layout, write_standalone, _aggressive_floorplan_repack_audit, _collect_architecture_modules, _audit_architecture, _audit_structural_consistency, _audit_geometry, _logical_instance_bbox, _gap_distribution_summary, _audit_wl_path_physical, _audit_row_peripheral_placement, ... (+27) | row_logic_plan, add_hard_array, words_per_row |
| deliverables/sram_layoutgen_standalone/sram_layoutgen/netlist_writer.py | 当前 structural SPICE 输出器，不读取外部网表 | NetlistWriter | _spice_path, _generated_stdcell_subckts | xbit_r, xprecharge, xwrite, xwl_driver, words_per_row |
| deliverables/sram_layoutgen_standalone/sram_layoutgen/geometry.py | LayoutDB、Instance、CellArray、Shape、Pin 数据结构 | Point, Rect, Shape, Pin, Instance, CellArray, LayoutDB | rect_from_center | - |
| deliverables/sram_layoutgen_standalone/sram_layoutgen/gds_writer.py | GDS 导出和 hardcell SREF 实例化 | GDSWriter | _read_gds_structures, _gds_xy_scale, _gds_db_unit_microns, _parse_gds_real8, _structure_dependency_closure, _structure_references, _strip_gds_text_elements, _snap_structure_xy, _merge_rectangles, _merge_pair | - |
| deliverables/sram_layoutgen_standalone/sram_layoutgen/tech.py | PDK layer/cell/replacement macro contract 加载 | LayerRule, ViaRule, CellAbstract, Tech | load_tech, _read_layer_map, _default_layer_map, _freepdk45_cells, _replacement_macro_specs, _freepdk45_reference_files | - |
| deliverables/sram_layoutgen_standalone/sram_layoutgen/openram_placement.py | OpenRAM-style origin/mirror/bbox placement helper | - | array_mirror, sref_origin_for_bbox, openram_sref_origin, placed_bbox_from_openram_origin, mirror_rect_in_cell, place_local_rect, place_local_point | - |
| deliverables/sram_layoutgen_standalone/sram_layoutgen/verifier.py | DRC-lite/overlap/spacing verification | DRCViolation, DRCResult, Verifier | - | - |
| deliverables/sram_layoutgen_standalone/sram_layoutgen/correctness.py | semantic connectivity / port / power audit | - | audit_layout_correctness, _audit_semantic_connectivity, _audit_port_placement, _audit_power_grid, _audit_row_side_power, _audit_array_power_stitching, _audit_global_power_consistency, _audit_power_junction_topology, _audit_array_top_bottom_boundary, _audit_well_substrate_ties, _audit_array_boundary_and_tap_decision, _audit_visual_power_topology_warnings, _used_storage_family_cells, _cell_layer_evidence, ... (+32) | - |
| deliverables/sram_layoutgen_standalone/sram_layoutgen/occupancy.py | 空白区域和优化目标分析 | OccupancyRegion | analyze_floorplan_occupancy, find_optimization_targets, write_occupancy_svg, analyze_two_zone_floorplan_compaction, write_two_zone_floorplan_svg, _matching_empty_region, _lower_middle_void_regions, _nearest_region_summaries, _two_zone_moved_modules, _two_zone_candidates, _two_zone_objective, _floorplan_groups, _core_left_shift_feasibility, _bottom_boundary_compaction_feasibility, ... (+24) | - |
| deliverables/sram_layoutgen_standalone/technology/freepdk45/replacement_macros.json | FreePDK45 replacement macro manifest | - | - | - |

后续重点修改位置：

- `sram_layoutgen/netlist_writer.py`：保留输出器，新增并行的 `netlist_parser.py` / `openyield_netlist_adapter.py`，不要把解析塞进 writer。
- `sram_layoutgen/standalone.py`：后续应把硬编码 array/peripheral/control placement 拆成 netlist contract -> module plan -> placement plan。
- `sram_layoutgen/tech.py` 与 `technology/freepdk45/replacement_macros.json`：扩展 module alias、pin alias、power alias、abutment metadata。
- `sram_layoutgen/geometry.py`：扩展 CellFootprint、PinAccess、AbutmentRule、PowerRailMetadata、PlacementRow/ColumnRule。
- `sram_layoutgen/correctness.py` / `verifier.py`：把 semantic connectivity audit 的预期来源改成 netlist contract。

## 9. 可聚合设计初步方案

建议先设计以下数据结构，再动 placement：

- `CellFootprint`：cell name、logical bbox、physical bbox、origin convention、legal mirrors、site width/height、blockage layers。
- `PinLocation` / `PinAccess`：pin name、net alias、layer、rect/point、direction、access side、preferred track、must_connect。
- `PowerRailMetadata`：VDD/VSS rail layer、rail y/x interval、rail width、rail phase、can_share_with、strap points、tap requirement。
- `AbutmentRule`：left/right/top/bottom compatibility、min gap、allowed overlap layers、shared rail rule、well/implant continuity rule、pin collision rule。
- `PlacementRowRule`：row height、site pitch、legal cell classes、power rail orientation、mirror alternation、row endcap/tap policy。
- `PlacementColumnRule`：bitline/wordline pitch coupling、column mux/sense/write alignment anchors、vertical rail sharing policy。
- `ModuleContract`：netlist module name、canonical role、pin aliases、GDS cell candidates、required neighbors、routing obligations。

可聚合目标应按顺序推进：先标准化 footprint/pin/power rail metadata，再支持同类单元一维 abutment，最后做二维 aggregation 和 shared rail DRC audit。

## 10. 后续建议顺序

1. 先做 OpenYield 网表/源码语义解析器：生成 `ModuleContract`，解析 PySpice `NAME/NODES/self.M/self.X/circuit.X`，必要时在有环境时运行 OpenYield 产生 `.sp` deck。
2. 建立 OpenRAM/OpenYield/current-layoutgen 的 canonical port/module 字典：power、bitline、wordline、addr、data、precharge、sense、write、decoder、time/control。
3. 扩展 `replacement_macros.json` 为 module alias + pin alias + footprint/power metadata，而不是立刻改 placement。
4. 设计可聚合单元抽象并为现有 hardcells 回填 footprint/rail/abutment 信息。
5. 最后才改 `standalone.py` 的 placement/routing，让它从 contract 驱动，而不是继续按固定结构写死。

结论：建议第二步先做 OpenYield 网表解析器和 canonical contract，而不是先做可聚合单元抽象。原因是聚合规则必须知道要聚合哪些模块、端口和电源轨；这些应先由 OpenYield/OpenRAM 网表差异分析定义清楚。

## 11. 未提交修改快照

根目录不是 git 仓库；`deliverables/sram_layoutgen_standalone` 的 git status 如下，本轮未清理这些文件：

```text
M examples/run_regression_sweep.py
 M sram_layoutgen/netlist_writer.py
 M sram_layoutgen/occupancy.py
 M sram_layoutgen/standalone.py
 M sram_layoutgen/verifier.py
?? docs/LAYOUT_ROUTING_REVIEW_AND_ALGORITHM.md
?? "docs/SRAM\347\211\210\345\233\276\347\224\237\346\210\220\345\231\250\351\230\266\346\256\265\346\200\247\350\277\233\345\261\225\346\212\245\345\221\212.docx"
?? "docs/SRAM\347\211\210\345\233\276\347\224\237\346\210\220\345\231\250\351\230\266\346\256\265\346\200\247\350\277\233\345\261\225\346\212\245\345\221\212.md"
?? docs/openyield_documentation_summary.md
?? docs/openyield_file_purpose_table.md
?? docs/openyield_full_file_deep_analysis.md
?? docs/openyield_full_file_index.csv
?? docs/openyield_full_file_index.json
?? docs/openyield_integration_smoke_test_report.md
?? docs/openyield_migration_plan.md
?? docs/openyield_migration_priority_table.md
?? docs/openyield_module_inventory.md
?? docs/openyield_openram_netlist_candidates.csv
?? docs/openyield_openram_netlist_diff_report.json
?? docs/openyield_openram_netlist_diff_report.md
?? docs/openyield_python_api_summary.md
?? docs/openyield_python_callgraph.json
?? docs/openyield_python_dependency_graph.dot
?? docs/openyield_python_dependency_graph.svg
?? docs/openyield_sim_metric_index.json
?? docs/openyield_sim_output_format_analysis.md
?? docs/openyield_spice_model_testbench_analysis.md
?? docs/openyield_spice_subckt_index.json
?? docs/openyield_yaml_config_analysis.md
?? docs/openyield_yaml_key_index.json
?? docs/sram_address_bus_isolation_audit_report.md
?? docs/sram_aggressive_floorplan_repack_report.md
?? docs/sram_architecture_contract.md
?? docs/sram_column_select_physical_audit_report.md
?? docs/sram_generator_audit_report.md
?? docs/sram_generator_contract_check_report.md
?? docs/sram_openram_style_wl_driver_column_report.md
?? docs/sram_peripheral_abutment_array_power_report.md
?? docs/sram_power_junction_boundary_tap_report.md
?? docs/sram_read_column_path_audit_report.md
?? docs/sram_row_power_wl_integrity_audit_report.md
?? docs/sram_two_zone_floorplan_compaction_report.md
?? scripts/analyze_openyield_full.py
?? scripts/openyield_openram_netlist_diff.py
?? sram_layoutgen/architecture_contract.py
?? sram_layoutgen/correctness.py
?? sram_layoutgen/openyield_adapter/
```

## 12. 实际执行命令

```text
git status --short  # repo root, failed because root is not a git repo
git status --short  # deliverables/sram_layoutgen_standalone
git -C third_party/OpenYield rev-parse/status
git -C third_party/OpenYield pull --ff-only
rg --files -g '*.sp' -g '*.spi' -g '*.spice' -g '*.cdl' -g '*.v' -g '*.sv'
rg --files third_party/OpenYield
static Python/SPICE scan via scripts/openyield_openram_netlist_diff.py
```