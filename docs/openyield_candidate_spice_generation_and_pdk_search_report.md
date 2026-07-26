# OpenYield Candidate SPICE Generation And PDK Search Report

- Scope: `candidate_spice_generation_and_pdk_model_search`
- Repo root: `E:\njust\keyan\SRAM Compiler_V2\OpenRAM-stable\deliverables\sram_layoutgen_step45_clean`

## Audit Summary

```json
{
  "pdk_model_search_completed": true,
  "candidate_spice_generation_available": true,
  "gen_delay_inv_candidate_spice_emitted": true,
  "delay_chain_symbolic_tb_emitted": true,
  "device_model_include_found": true,
  "nmos_vtg_bound": true,
  "pmos_vtg_bound": true,
  "needs_model_alias_mapping": false,
  "can_run_candidate_spice_now": false,
  "can_run_delay_chain_testbench_now": false,
  "can_claim_delay_proof_now": false,
  "can_claim_timing_closure_now": false,
  "needs_teacher_or_project_provider": false,
  "can_enter_candidate_spice_syntax_check": true,
  "can_enter_pvt_corner_definition": true,
  "can_enter_delay_chain_smoke_simulation": false,
  "can_enter_physical_timing_closure_now": false,
  "can_enter_physical_routing_now": false,
  "can_enter_physical_placement_now": false,
  "can_generate_time_control_gds_now": false,
  "can_modify_standalone_now": false
}
```

## Searched PDK Directories

- `E:\njust\keyan\SRAM Compiler_V2\OpenRAM-stable\technology\freepdk45`
- `E:\njust\keyan\SRAM Compiler_V2\OpenRAM-stable\deliverables\sram_layoutgen_step45_clean\technology\freepdk45`

## Device Model Search Results

| file_path | matched_keyword | line | excerpt | candidate_model_type | usable_include | notes |
| --- | --- | --- | --- | --- | --- | --- |
| E:\njust\keyan\SRAM Compiler_V2\OpenRAM-stable\technology\freepdk45\models\hspice_ff.include | NMOS_VTG | 2 | .inc '$PDK_DIR/ncsu_basekit/models/hspice/tran_models/models_ff/NMOS_VTG.inc | corner_include | True | Corner include references NMOS_VTG / PMOS_VTG. |
| E:\njust\keyan\SRAM Compiler_V2\OpenRAM-stable\technology\freepdk45\models\hspice_ff.include | PMOS_VTG | 3 | .inc '$PDK_DIR/ncsu_basekit/models/hspice/tran_models/models_ff/PMOS_VTG.inc | corner_include | True | Corner include references NMOS_VTG / PMOS_VTG. |
| E:\njust\keyan\SRAM Compiler_V2\OpenRAM-stable\technology\freepdk45\models\hspice_ff.include | nmos | 5 | .inc '$PDK_DIR/ncsu_basekit/models/hspice/tran_models/models_ff/NMOS_VTL.inc | corner_include | True | Corner include references NMOS_VTG / PMOS_VTG. |
| E:\njust\keyan\SRAM Compiler_V2\OpenRAM-stable\technology\freepdk45\models\hspice_ff.include | pmos | 6 | .inc '$PDK_DIR/ncsu_basekit/models/hspice/tran_models/models_ff/PMOS_VTL.inc | corner_include | True | Corner include references NMOS_VTG / PMOS_VTG. |
| E:\njust\keyan\SRAM Compiler_V2\OpenRAM-stable\technology\freepdk45\models\hspice_ff.include | nmos | 8 | .inc '$PDK_DIR/ncsu_basekit/models/hspice/tran_models/models_ff/NMOS_VTH.inc | corner_include | True | Corner include references NMOS_VTG / PMOS_VTG. |
| E:\njust\keyan\SRAM Compiler_V2\OpenRAM-stable\technology\freepdk45\models\hspice_ff.include | pmos | 9 | .inc '$PDK_DIR/ncsu_basekit/models/hspice/tran_models/models_ff/PMOS_VTH.inc | corner_include | True | Corner include references NMOS_VTG / PMOS_VTG. |
| E:\njust\keyan\SRAM Compiler_V2\OpenRAM-stable\technology\freepdk45\models\hspice_ff.include | nmos | 11 | .inc '$PDK_DIR/ncsu_basekit/models/hspice/tran_models/models_ff/NMOS_THKOX.inc | corner_include | True | Corner include references NMOS_VTG / PMOS_VTG. |
| E:\njust\keyan\SRAM Compiler_V2\OpenRAM-stable\technology\freepdk45\models\hspice_ff.include | pmos | 12 | .inc '$PDK_DIR/ncsu_basekit/models/hspice/tran_models/models_ff/PMOS_THKOX.inc | corner_include | True | Corner include references NMOS_VTG / PMOS_VTG. |
| E:\njust\keyan\SRAM Compiler_V2\OpenRAM-stable\technology\freepdk45\models\hspice_nom.include | NMOS_VTG | 2 | .inc '$PDK_DIR/ncsu_basekit/models/hspice/tran_models/models_nom/NMOS_VTG.inc | corner_include | True | Corner include references NMOS_VTG / PMOS_VTG. |
| E:\njust\keyan\SRAM Compiler_V2\OpenRAM-stable\technology\freepdk45\models\hspice_nom.include | PMOS_VTG | 3 | .inc '$PDK_DIR/ncsu_basekit/models/hspice/tran_models/models_nom/PMOS_VTG.inc | corner_include | True | Corner include references NMOS_VTG / PMOS_VTG. |
| E:\njust\keyan\SRAM Compiler_V2\OpenRAM-stable\technology\freepdk45\models\hspice_nom.include | nmos | 5 | .inc '$PDK_DIR/ncsu_basekit/models/hspice/tran_models/models_nom/NMOS_VTL.inc | corner_include | True | Corner include references NMOS_VTG / PMOS_VTG. |
| E:\njust\keyan\SRAM Compiler_V2\OpenRAM-stable\technology\freepdk45\models\hspice_nom.include | pmos | 6 | .inc '$PDK_DIR/ncsu_basekit/models/hspice/tran_models/models_nom/PMOS_VTL.inc | corner_include | True | Corner include references NMOS_VTG / PMOS_VTG. |
| E:\njust\keyan\SRAM Compiler_V2\OpenRAM-stable\technology\freepdk45\models\hspice_nom.include | nmos | 8 | .inc '$PDK_DIR/ncsu_basekit/models/hspice/tran_models/models_nom/NMOS_VTH.inc | corner_include | True | Corner include references NMOS_VTG / PMOS_VTG. |
| E:\njust\keyan\SRAM Compiler_V2\OpenRAM-stable\technology\freepdk45\models\hspice_nom.include | pmos | 9 | .inc '$PDK_DIR/ncsu_basekit/models/hspice/tran_models/models_nom/PMOS_VTH.inc | corner_include | True | Corner include references NMOS_VTG / PMOS_VTG. |
| E:\njust\keyan\SRAM Compiler_V2\OpenRAM-stable\technology\freepdk45\models\hspice_nom.include | nmos | 11 | .inc '$PDK_DIR/ncsu_basekit/models/hspice/tran_models/models_nom/NMOS_THKOX.inc | corner_include | True | Corner include references NMOS_VTG / PMOS_VTG. |
| E:\njust\keyan\SRAM Compiler_V2\OpenRAM-stable\technology\freepdk45\models\hspice_nom.include | pmos | 12 | .inc '$PDK_DIR/ncsu_basekit/models/hspice/tran_models/models_nom/PMOS_THKOX.inc | corner_include | True | Corner include references NMOS_VTG / PMOS_VTG. |
| E:\njust\keyan\SRAM Compiler_V2\OpenRAM-stable\technology\freepdk45\models\hspice_ss.include | NMOS_VTG | 2 | .inc '$PDK_DIR/ncsu_basekit/models/hspice/tran_models/models_ss/NMOS_VTG.inc | corner_include | True | Corner include references NMOS_VTG / PMOS_VTG. |
| E:\njust\keyan\SRAM Compiler_V2\OpenRAM-stable\technology\freepdk45\models\hspice_ss.include | PMOS_VTG | 3 | .inc '$PDK_DIR/ncsu_basekit/models/hspice/tran_models/models_ss/PMOS_VTG.inc | corner_include | True | Corner include references NMOS_VTG / PMOS_VTG. |
| E:\njust\keyan\SRAM Compiler_V2\OpenRAM-stable\technology\freepdk45\models\hspice_ss.include | nmos | 5 | .inc '$PDK_DIR/ncsu_basekit/models/hspice/tran_models/models_ss/NMOS_VTL.inc | corner_include | True | Corner include references NMOS_VTG / PMOS_VTG. |
| E:\njust\keyan\SRAM Compiler_V2\OpenRAM-stable\technology\freepdk45\models\hspice_ss.include | pmos | 6 | .inc '$PDK_DIR/ncsu_basekit/models/hspice/tran_models/models_ss/PMOS_VTL.inc | corner_include | True | Corner include references NMOS_VTG / PMOS_VTG. |
| E:\njust\keyan\SRAM Compiler_V2\OpenRAM-stable\technology\freepdk45\models\hspice_ss.include | nmos | 8 | .inc '$PDK_DIR/ncsu_basekit/models/hspice/tran_models/models_ss/NMOS_VTH.inc | corner_include | True | Corner include references NMOS_VTG / PMOS_VTG. |
| E:\njust\keyan\SRAM Compiler_V2\OpenRAM-stable\technology\freepdk45\models\hspice_ss.include | pmos | 9 | .inc '$PDK_DIR/ncsu_basekit/models/hspice/tran_models/models_ss/PMOS_VTH.inc | corner_include | True | Corner include references NMOS_VTG / PMOS_VTG. |
| E:\njust\keyan\SRAM Compiler_V2\OpenRAM-stable\technology\freepdk45\models\hspice_ss.include | nmos | 11 | .inc '$PDK_DIR/ncsu_basekit/models/hspice/tran_models/models_ss/NMOS_THKOX.inc | corner_include | True | Corner include references NMOS_VTG / PMOS_VTG. |
| E:\njust\keyan\SRAM Compiler_V2\OpenRAM-stable\technology\freepdk45\models\hspice_ss.include | pmos | 12 | .inc '$PDK_DIR/ncsu_basekit/models/hspice/tran_models/models_ss/PMOS_THKOX.inc | corner_include | True | Corner include references NMOS_VTG / PMOS_VTG. |
| E:\njust\keyan\SRAM Compiler_V2\OpenRAM-stable\technology\freepdk45\sp_lib\cell_1rw.sp | NMOS_VTG | 4 | MM0 Q_bar Q gnd gnd NMOS_VTG W=205.00n L=50n | transistor_netlist_usage | False | Netlist instance usage proves model names are expected by project SPICE. |
| E:\njust\keyan\SRAM Compiler_V2\OpenRAM-stable\technology\freepdk45\sp_lib\cell_1rw.sp | PMOS_VTG | 5 | MM4 Q_bar Q vdd vdd PMOS_VTG W=90n L=50n | transistor_netlist_usage | False | Netlist instance usage proves model names are expected by project SPICE. |
| E:\njust\keyan\SRAM Compiler_V2\OpenRAM-stable\technology\freepdk45\sp_lib\cell_1rw.sp | NMOS_VTG | 8 | MM1 Q Q_bar gnd gnd NMOS_VTG W=205.00n L=50n | transistor_netlist_usage | False | Netlist instance usage proves model names are expected by project SPICE. |
| E:\njust\keyan\SRAM Compiler_V2\OpenRAM-stable\technology\freepdk45\sp_lib\cell_1rw.sp | PMOS_VTG | 9 | MM5 Q Q_bar vdd vdd PMOS_VTG W=90n L=50n | transistor_netlist_usage | False | Netlist instance usage proves model names are expected by project SPICE. |
| E:\njust\keyan\SRAM Compiler_V2\OpenRAM-stable\technology\freepdk45\sp_lib\cell_1rw.sp | NMOS_VTG | 12 | MM3 bl wl Q gnd NMOS_VTG W=135.00n L=50n | transistor_netlist_usage | False | Netlist instance usage proves model names are expected by project SPICE. |
| E:\njust\keyan\SRAM Compiler_V2\OpenRAM-stable\technology\freepdk45\sp_lib\cell_1rw.sp | NMOS_VTG | 13 | MM2 br wl Q_bar gnd NMOS_VTG W=135.00n L=50n | transistor_netlist_usage | False | Netlist instance usage proves model names are expected by project SPICE. |
| E:\njust\keyan\SRAM Compiler_V2\OpenRAM-stable\technology\freepdk45\sp_lib\cell_2rw.sp | NMOS_VTG | 3 | MM9 RA_to_R_right wl1 br1 gnd NMOS_VTG W=180.0n L=50n m=1 | transistor_netlist_usage | False | Netlist instance usage proves model names are expected by project SPICE. |
| E:\njust\keyan\SRAM Compiler_V2\OpenRAM-stable\technology\freepdk45\sp_lib\cell_2rw.sp | NMOS_VTG | 4 | MM8 RA_to_R_right Q gnd gnd NMOS_VTG W=180.0n L=50n m=1 | transistor_netlist_usage | False | Netlist instance usage proves model names are expected by project SPICE. |
| E:\njust\keyan\SRAM Compiler_V2\OpenRAM-stable\technology\freepdk45\sp_lib\cell_2rw.sp | NMOS_VTG | 5 | MM7 RA_to_R_left Q_bar gnd gnd NMOS_VTG W=180.0n L=50n m=1 | transistor_netlist_usage | False | Netlist instance usage proves model names are expected by project SPICE. |
| E:\njust\keyan\SRAM Compiler_V2\OpenRAM-stable\technology\freepdk45\sp_lib\cell_2rw.sp | NMOS_VTG | 6 | MM6 RA_to_R_left wl1 bl1 gnd NMOS_VTG W=180.0n L=50n m=1 | transistor_netlist_usage | False | Netlist instance usage proves model names are expected by project SPICE. |
| E:\njust\keyan\SRAM Compiler_V2\OpenRAM-stable\technology\freepdk45\sp_lib\cell_2rw.sp | NMOS_VTG | 7 | MM5 Q wl0 bl0 gnd NMOS_VTG W=135.00n L=50n m=1 | transistor_netlist_usage | False | Netlist instance usage proves model names are expected by project SPICE. |
| E:\njust\keyan\SRAM Compiler_V2\OpenRAM-stable\technology\freepdk45\sp_lib\cell_2rw.sp | NMOS_VTG | 8 | MM4 Q_bar wl0 br0 gnd NMOS_VTG W=135.00n L=50n m=1 | transistor_netlist_usage | False | Netlist instance usage proves model names are expected by project SPICE. |
| E:\njust\keyan\SRAM Compiler_V2\OpenRAM-stable\technology\freepdk45\sp_lib\cell_2rw.sp | NMOS_VTG | 9 | MM1 Q Q_bar gnd gnd NMOS_VTG W=205.0n L=50n m=1 | transistor_netlist_usage | False | Netlist instance usage proves model names are expected by project SPICE. |
| E:\njust\keyan\SRAM Compiler_V2\OpenRAM-stable\technology\freepdk45\sp_lib\cell_2rw.sp | NMOS_VTG | 10 | MM0 Q_bar Q gnd gnd NMOS_VTG W=205.0n L=50n m=1 | transistor_netlist_usage | False | Netlist instance usage proves model names are expected by project SPICE. |
| E:\njust\keyan\SRAM Compiler_V2\OpenRAM-stable\technology\freepdk45\sp_lib\cell_2rw.sp | PMOS_VTG | 11 | MM3 Q Q_bar vdd vdd PMOS_VTG W=90n L=50n m=1 | transistor_netlist_usage | False | Netlist instance usage proves model names are expected by project SPICE. |
| E:\njust\keyan\SRAM Compiler_V2\OpenRAM-stable\technology\freepdk45\sp_lib\cell_2rw.sp | PMOS_VTG | 12 | MM2 Q_bar Q vdd vdd PMOS_VTG W=90n L=50n m=1 | transistor_netlist_usage | False | Netlist instance usage proves model names are expected by project SPICE. |
| E:\njust\keyan\SRAM Compiler_V2\OpenRAM-stable\technology\freepdk45\sp_lib\dff.sp | NMOS_VTG | 8 | MM21 Q a_66_6# gnd gnd NMOS_VTG L=5e-08 W=5e-07 | transistor_netlist_usage | False | Netlist instance usage proves model names are expected by project SPICE. |
| E:\njust\keyan\SRAM Compiler_V2\OpenRAM-stable\technology\freepdk45\sp_lib\dff.sp | NMOS_VTG | 9 | MM19 a_76_6# a_2_6# a_66_6# gnd NMOS_VTG L=5e-08 W=2.5e-07 | transistor_netlist_usage | False | Netlist instance usage proves model names are expected by project SPICE. |
| E:\njust\keyan\SRAM Compiler_V2\OpenRAM-stable\technology\freepdk45\sp_lib\dff.sp | NMOS_VTG | 10 | MM20 gnd Q a_76_6# gnd NMOS_VTG L=5e-08 W=2.5e-07 | transistor_netlist_usage | False | Netlist instance usage proves model names are expected by project SPICE. |
| E:\njust\keyan\SRAM Compiler_V2\OpenRAM-stable\technology\freepdk45\sp_lib\dff.sp | NMOS_VTG | 11 | MM18 a_66_6# clk a_61_6# gnd NMOS_VTG L=5e-08 W=2.5e-07 | transistor_netlist_usage | False | Netlist instance usage proves model names are expected by project SPICE. |
| E:\njust\keyan\SRAM Compiler_V2\OpenRAM-stable\technology\freepdk45\sp_lib\dff.sp | NMOS_VTG | 12 | MM17 a_61_6# a_34_4# gnd gnd NMOS_VTG L=5e-08 W=2.5e-07 | transistor_netlist_usage | False | Netlist instance usage proves model names are expected by project SPICE. |
| E:\njust\keyan\SRAM Compiler_V2\OpenRAM-stable\technology\freepdk45\sp_lib\dff.sp | NMOS_VTG | 13 | MM10 gnd clk a_2_6# gnd NMOS_VTG L=5e-08 W=5e-07 | transistor_netlist_usage | False | Netlist instance usage proves model names are expected by project SPICE. |
| E:\njust\keyan\SRAM Compiler_V2\OpenRAM-stable\technology\freepdk45\sp_lib\dff.sp | NMOS_VTG | 14 | MM16 a_34_4# a_22_6# gnd gnd NMOS_VTG L=5e-08 W=2.5e-07 | transistor_netlist_usage | False | Netlist instance usage proves model names are expected by project SPICE. |
| E:\njust\keyan\SRAM Compiler_V2\OpenRAM-stable\technology\freepdk45\sp_lib\dff.sp | NMOS_VTG | 15 | MM15 gnd a_34_4# a_31_6# gnd NMOS_VTG L=5e-08 W=2.5e-07 | transistor_netlist_usage | False | Netlist instance usage proves model names are expected by project SPICE. |
| E:\njust\keyan\SRAM Compiler_V2\OpenRAM-stable\technology\freepdk45\sp_lib\dff.sp | NMOS_VTG | 16 | MM14 a_31_6# clk a_22_6# gnd NMOS_VTG L=5e-08 W=2.5e-07 | transistor_netlist_usage | False | Netlist instance usage proves model names are expected by project SPICE. |
| E:\njust\keyan\SRAM Compiler_V2\OpenRAM-stable\technology\freepdk45\sp_lib\dff.sp | NMOS_VTG | 17 | MM13 a_22_6# a_2_6# a_17_6# gnd NMOS_VTG L=5e-08 W=2.5e-07 | transistor_netlist_usage | False | Netlist instance usage proves model names are expected by project SPICE. |
| E:\njust\keyan\SRAM Compiler_V2\OpenRAM-stable\technology\freepdk45\sp_lib\dff.sp | NMOS_VTG | 18 | MM12 a_17_6# D gnd gnd NMOS_VTG L=5e-08 W=2.5e-07 | transistor_netlist_usage | False | Netlist instance usage proves model names are expected by project SPICE. |
| E:\njust\keyan\SRAM Compiler_V2\OpenRAM-stable\technology\freepdk45\sp_lib\dff.sp | PMOS_VTG | 19 | MM11 Q a_66_6# vdd vdd PMOS_VTG L=5e-08 W=1e-06 | transistor_netlist_usage | False | Netlist instance usage proves model names are expected by project SPICE. |
| E:\njust\keyan\SRAM Compiler_V2\OpenRAM-stable\technology\freepdk45\sp_lib\dff.sp | PMOS_VTG | 20 | MM9 vdd Q a_76_84# vdd PMOS_VTG L=5e-08 W=2.5e-07 | transistor_netlist_usage | False | Netlist instance usage proves model names are expected by project SPICE. |
| E:\njust\keyan\SRAM Compiler_V2\OpenRAM-stable\technology\freepdk45\sp_lib\dff.sp | PMOS_VTG | 21 | MM8 a_76_84# clk a_66_6# vdd PMOS_VTG L=5e-08 W=2.5e-07 | transistor_netlist_usage | False | Netlist instance usage proves model names are expected by project SPICE. |
| E:\njust\keyan\SRAM Compiler_V2\OpenRAM-stable\technology\freepdk45\sp_lib\dff.sp | PMOS_VTG | 22 | MM7 a_66_6# a_2_6# a_61_74# vdd PMOS_VTG L=5e-08 W=5e-07 | transistor_netlist_usage | False | Netlist instance usage proves model names are expected by project SPICE. |
| E:\njust\keyan\SRAM Compiler_V2\OpenRAM-stable\technology\freepdk45\sp_lib\dff.sp | PMOS_VTG | 23 | MM6 a_61_74# a_34_4# vdd vdd PMOS_VTG L=5e-08 W=5e-07 | transistor_netlist_usage | False | Netlist instance usage proves model names are expected by project SPICE. |
| E:\njust\keyan\SRAM Compiler_V2\OpenRAM-stable\technology\freepdk45\sp_lib\dff.sp | PMOS_VTG | 24 | MM0 vdd clk a_2_6# vdd PMOS_VTG L=5e-08 W=1e-06 | transistor_netlist_usage | False | Netlist instance usage proves model names are expected by project SPICE. |
| E:\njust\keyan\SRAM Compiler_V2\OpenRAM-stable\technology\freepdk45\sp_lib\dff.sp | PMOS_VTG | 25 | MM5 a_34_4# a_22_6# vdd vdd PMOS_VTG L=5e-08 W=5e-07 | transistor_netlist_usage | False | Netlist instance usage proves model names are expected by project SPICE. |
| E:\njust\keyan\SRAM Compiler_V2\OpenRAM-stable\technology\freepdk45\sp_lib\dff.sp | PMOS_VTG | 26 | MM4 vdd a_34_4# a_31_74# vdd PMOS_VTG L=5e-08 W=5e-07 | transistor_netlist_usage | False | Netlist instance usage proves model names are expected by project SPICE. |
| E:\njust\keyan\SRAM Compiler_V2\OpenRAM-stable\technology\freepdk45\sp_lib\dff.sp | PMOS_VTG | 27 | MM3 a_31_74# a_2_6# a_22_6# vdd PMOS_VTG L=5e-08 W=5e-07 | transistor_netlist_usage | False | Netlist instance usage proves model names are expected by project SPICE. |
| E:\njust\keyan\SRAM Compiler_V2\OpenRAM-stable\technology\freepdk45\sp_lib\dff.sp | PMOS_VTG | 28 | MM2 a_22_6# clk a_17_74# vdd PMOS_VTG L=5e-08 W=5e-07 | transistor_netlist_usage | False | Netlist instance usage proves model names are expected by project SPICE. |
| E:\njust\keyan\SRAM Compiler_V2\OpenRAM-stable\technology\freepdk45\sp_lib\dff.sp | PMOS_VTG | 29 | MM1 a_17_74# D vdd vdd PMOS_VTG L=5e-08 W=5e-07 | transistor_netlist_usage | False | Netlist instance usage proves model names are expected by project SPICE. |
| E:\njust\keyan\SRAM Compiler_V2\OpenRAM-stable\technology\freepdk45\sp_lib\dummy_cell_1rw.sp | NMOS_VTG | 4 | MM0 Q_bar Q gnd gnd NMOS_VTG W=205.00n L=50n | transistor_netlist_usage | False | Netlist instance usage proves model names are expected by project SPICE. |
| E:\njust\keyan\SRAM Compiler_V2\OpenRAM-stable\technology\freepdk45\sp_lib\dummy_cell_1rw.sp | PMOS_VTG | 5 | MM4 Q_bar Q vdd vdd PMOS_VTG W=90n L=50n | transistor_netlist_usage | False | Netlist instance usage proves model names are expected by project SPICE. |
| E:\njust\keyan\SRAM Compiler_V2\OpenRAM-stable\technology\freepdk45\sp_lib\dummy_cell_1rw.sp | NMOS_VTG | 8 | MM1 Q Q_bar gnd gnd NMOS_VTG W=205.00n L=50n | transistor_netlist_usage | False | Netlist instance usage proves model names are expected by project SPICE. |
| E:\njust\keyan\SRAM Compiler_V2\OpenRAM-stable\technology\freepdk45\sp_lib\dummy_cell_1rw.sp | PMOS_VTG | 9 | MM5 Q Q_bar vdd vdd PMOS_VTG W=90n L=50n | transistor_netlist_usage | False | Netlist instance usage proves model names are expected by project SPICE. |
| E:\njust\keyan\SRAM Compiler_V2\OpenRAM-stable\technology\freepdk45\sp_lib\dummy_cell_1rw.sp | NMOS_VTG | 12 | MM3 bl_noconn wl Q gnd NMOS_VTG W=135.00n L=50n | transistor_netlist_usage | False | Netlist instance usage proves model names are expected by project SPICE. |
| E:\njust\keyan\SRAM Compiler_V2\OpenRAM-stable\technology\freepdk45\sp_lib\dummy_cell_1rw.sp | NMOS_VTG | 13 | MM2 br_noconn wl Q_bar gnd NMOS_VTG W=135.00n L=50n | transistor_netlist_usage | False | Netlist instance usage proves model names are expected by project SPICE. |
| E:\njust\keyan\SRAM Compiler_V2\OpenRAM-stable\technology\freepdk45\sp_lib\dummy_cell_2rw.sp | NMOS_VTG | 3 | MM9 RA_to_R_right wl1 br1_noconn gnd NMOS_VTG W=180.0n L=50n m=1 | transistor_netlist_usage | False | Netlist instance usage proves model names are expected by project SPICE. |
| E:\njust\keyan\SRAM Compiler_V2\OpenRAM-stable\technology\freepdk45\sp_lib\dummy_cell_2rw.sp | NMOS_VTG | 4 | MM8 RA_to_R_right Q gnd gnd NMOS_VTG W=180.0n L=50n m=1 | transistor_netlist_usage | False | Netlist instance usage proves model names are expected by project SPICE. |
| E:\njust\keyan\SRAM Compiler_V2\OpenRAM-stable\technology\freepdk45\sp_lib\dummy_cell_2rw.sp | NMOS_VTG | 5 | MM7 RA_to_R_left Q_bar gnd gnd NMOS_VTG W=180.0n L=50n m=1 | transistor_netlist_usage | False | Netlist instance usage proves model names are expected by project SPICE. |
| E:\njust\keyan\SRAM Compiler_V2\OpenRAM-stable\technology\freepdk45\sp_lib\dummy_cell_2rw.sp | NMOS_VTG | 6 | MM6 RA_to_R_left wl1 bl1_noconn gnd NMOS_VTG W=180.0n L=50n m=1 | transistor_netlist_usage | False | Netlist instance usage proves model names are expected by project SPICE. |
| E:\njust\keyan\SRAM Compiler_V2\OpenRAM-stable\technology\freepdk45\sp_lib\dummy_cell_2rw.sp | NMOS_VTG | 7 | MM5 Q wl0 bl0_noconn gnd NMOS_VTG W=135.00n L=50n m=1 | transistor_netlist_usage | False | Netlist instance usage proves model names are expected by project SPICE. |
| E:\njust\keyan\SRAM Compiler_V2\OpenRAM-stable\technology\freepdk45\sp_lib\dummy_cell_2rw.sp | NMOS_VTG | 8 | MM4 Q_bar wl0 br0_noconn gnd NMOS_VTG W=135.00n L=50n m=1 | transistor_netlist_usage | False | Netlist instance usage proves model names are expected by project SPICE. |
| E:\njust\keyan\SRAM Compiler_V2\OpenRAM-stable\technology\freepdk45\sp_lib\dummy_cell_2rw.sp | NMOS_VTG | 9 | MM1 Q Q_bar gnd gnd NMOS_VTG W=205.0n L=50n m=1 | transistor_netlist_usage | False | Netlist instance usage proves model names are expected by project SPICE. |
| E:\njust\keyan\SRAM Compiler_V2\OpenRAM-stable\technology\freepdk45\sp_lib\dummy_cell_2rw.sp | NMOS_VTG | 10 | MM0 Q_bar Q gnd gnd NMOS_VTG W=205.0n L=50n m=1 | transistor_netlist_usage | False | Netlist instance usage proves model names are expected by project SPICE. |
| E:\njust\keyan\SRAM Compiler_V2\OpenRAM-stable\technology\freepdk45\sp_lib\dummy_cell_2rw.sp | PMOS_VTG | 11 | MM3 Q Q_bar vdd vdd PMOS_VTG W=90n L=50n m=1 | transistor_netlist_usage | False | Netlist instance usage proves model names are expected by project SPICE. |
| E:\njust\keyan\SRAM Compiler_V2\OpenRAM-stable\technology\freepdk45\sp_lib\dummy_cell_2rw.sp | PMOS_VTG | 12 | MM2 Q_bar Q vdd vdd PMOS_VTG W=90n L=50n m=1 | transistor_netlist_usage | False | Netlist instance usage proves model names are expected by project SPICE. |
| E:\njust\keyan\SRAM Compiler_V2\OpenRAM-stable\technology\freepdk45\sp_lib\replica_cell_1rw.sp | NMOS_VTG | 4 | MM0 vdd Q gnd gnd NMOS_VTG W=205.00n L=50n | transistor_netlist_usage | False | Netlist instance usage proves model names are expected by project SPICE. |
| E:\njust\keyan\SRAM Compiler_V2\OpenRAM-stable\technology\freepdk45\sp_lib\replica_cell_1rw.sp | PMOS_VTG | 5 | MM4 vdd Q vdd vdd PMOS_VTG W=90n L=50n | transistor_netlist_usage | False | Netlist instance usage proves model names are expected by project SPICE. |
| E:\njust\keyan\SRAM Compiler_V2\OpenRAM-stable\technology\freepdk45\sp_lib\replica_cell_1rw.sp | NMOS_VTG | 8 | MM1 Q vdd gnd gnd NMOS_VTG W=205.00n L=50n | transistor_netlist_usage | False | Netlist instance usage proves model names are expected by project SPICE. |
| E:\njust\keyan\SRAM Compiler_V2\OpenRAM-stable\technology\freepdk45\sp_lib\replica_cell_1rw.sp | PMOS_VTG | 9 | MM5 Q vdd vdd vdd PMOS_VTG W=90n L=50n | transistor_netlist_usage | False | Netlist instance usage proves model names are expected by project SPICE. |
| E:\njust\keyan\SRAM Compiler_V2\OpenRAM-stable\technology\freepdk45\sp_lib\replica_cell_1rw.sp | NMOS_VTG | 12 | MM3 bl wl Q gnd NMOS_VTG W=135.00n L=50n | transistor_netlist_usage | False | Netlist instance usage proves model names are expected by project SPICE. |
| E:\njust\keyan\SRAM Compiler_V2\OpenRAM-stable\technology\freepdk45\sp_lib\replica_cell_1rw.sp | NMOS_VTG | 13 | MM2 br wl vdd gnd NMOS_VTG W=135.00n L=50n | transistor_netlist_usage | False | Netlist instance usage proves model names are expected by project SPICE. |
| E:\njust\keyan\SRAM Compiler_V2\OpenRAM-stable\technology\freepdk45\sp_lib\replica_cell_2rw.sp | NMOS_VTG | 3 | MM9 RA_to_R_right wl1 br1 gnd NMOS_VTG W=180.0n L=50n m=1 | transistor_netlist_usage | False | Netlist instance usage proves model names are expected by project SPICE. |
| E:\njust\keyan\SRAM Compiler_V2\OpenRAM-stable\technology\freepdk45\sp_lib\replica_cell_2rw.sp | NMOS_VTG | 4 | MM8 RA_to_R_right Q gnd gnd NMOS_VTG W=180.0n L=50n m=1 | transistor_netlist_usage | False | Netlist instance usage proves model names are expected by project SPICE. |
| E:\njust\keyan\SRAM Compiler_V2\OpenRAM-stable\technology\freepdk45\sp_lib\replica_cell_2rw.sp | NMOS_VTG | 5 | MM7 RA_to_R_left vdd gnd gnd NMOS_VTG W=180.0n L=50n m=1 | transistor_netlist_usage | False | Netlist instance usage proves model names are expected by project SPICE. |
| E:\njust\keyan\SRAM Compiler_V2\OpenRAM-stable\technology\freepdk45\sp_lib\replica_cell_2rw.sp | NMOS_VTG | 6 | MM6 RA_to_R_left wl1 bl1 gnd NMOS_VTG W=180.0n L=50n m=1 | transistor_netlist_usage | False | Netlist instance usage proves model names are expected by project SPICE. |
| E:\njust\keyan\SRAM Compiler_V2\OpenRAM-stable\technology\freepdk45\sp_lib\replica_cell_2rw.sp | NMOS_VTG | 7 | MM5 Q wl0 bl0 gnd NMOS_VTG W=135.00n L=50n m=1 | transistor_netlist_usage | False | Netlist instance usage proves model names are expected by project SPICE. |
| E:\njust\keyan\SRAM Compiler_V2\OpenRAM-stable\technology\freepdk45\sp_lib\replica_cell_2rw.sp | NMOS_VTG | 8 | MM4 vdd wl0 br0 gnd NMOS_VTG W=135.00n L=50n m=1 | transistor_netlist_usage | False | Netlist instance usage proves model names are expected by project SPICE. |
| E:\njust\keyan\SRAM Compiler_V2\OpenRAM-stable\technology\freepdk45\sp_lib\replica_cell_2rw.sp | NMOS_VTG | 9 | MM1 Q vdd gnd gnd NMOS_VTG W=205.0n L=50n m=1 | transistor_netlist_usage | False | Netlist instance usage proves model names are expected by project SPICE. |
| E:\njust\keyan\SRAM Compiler_V2\OpenRAM-stable\technology\freepdk45\sp_lib\replica_cell_2rw.sp | NMOS_VTG | 10 | MM0 vdd Q gnd gnd NMOS_VTG W=205.0n L=50n m=1 | transistor_netlist_usage | False | Netlist instance usage proves model names are expected by project SPICE. |
| E:\njust\keyan\SRAM Compiler_V2\OpenRAM-stable\technology\freepdk45\sp_lib\replica_cell_2rw.sp | PMOS_VTG | 11 | MM3 Q vdd vdd vdd PMOS_VTG W=90n L=50n m=1 | transistor_netlist_usage | False | Netlist instance usage proves model names are expected by project SPICE. |
| E:\njust\keyan\SRAM Compiler_V2\OpenRAM-stable\technology\freepdk45\sp_lib\replica_cell_2rw.sp | PMOS_VTG | 12 | MM2 vdd Q vdd vdd PMOS_VTG W=90n L=50n m=1 | transistor_netlist_usage | False | Netlist instance usage proves model names are expected by project SPICE. |
| E:\njust\keyan\SRAM Compiler_V2\OpenRAM-stable\technology\freepdk45\sp_lib\sense_amp.sp | PMOS_VTG | 3 | M_1 dint net_1 vdd vdd pmos_vtg w=540.0n l=50.0n | transistor_netlist_usage | False | Netlist instance usage proves model names are expected by project SPICE. |
| E:\njust\keyan\SRAM Compiler_V2\OpenRAM-stable\technology\freepdk45\sp_lib\sense_amp.sp | PMOS_VTG | 4 | M_3 net_1 dint vdd vdd pmos_vtg w=540.0n l=50.0n | transistor_netlist_usage | False | Netlist instance usage proves model names are expected by project SPICE. |
| E:\njust\keyan\SRAM Compiler_V2\OpenRAM-stable\technology\freepdk45\sp_lib\sense_amp.sp | NMOS_VTG | 5 | M_2 dint net_1 net_2 gnd nmos_vtg w=270.0n l=50.0n | transistor_netlist_usage | False | Netlist instance usage proves model names are expected by project SPICE. |
| E:\njust\keyan\SRAM Compiler_V2\OpenRAM-stable\technology\freepdk45\sp_lib\sense_amp.sp | NMOS_VTG | 6 | M_8 net_1 dint net_2 gnd nmos_vtg w=270.0n l=50.0n | transistor_netlist_usage | False | Netlist instance usage proves model names are expected by project SPICE. |
| E:\njust\keyan\SRAM Compiler_V2\OpenRAM-stable\technology\freepdk45\sp_lib\sense_amp.sp | PMOS_VTG | 7 | M_5 bl en dint vdd pmos_vtg w=720.0n l=50.0n | transistor_netlist_usage | False | Netlist instance usage proves model names are expected by project SPICE. |
| E:\njust\keyan\SRAM Compiler_V2\OpenRAM-stable\technology\freepdk45\sp_lib\sense_amp.sp | PMOS_VTG | 8 | M_6 br en net_1 vdd pmos_vtg w=720.0n l=50.0n | transistor_netlist_usage | False | Netlist instance usage proves model names are expected by project SPICE. |
| E:\njust\keyan\SRAM Compiler_V2\OpenRAM-stable\technology\freepdk45\sp_lib\sense_amp.sp | NMOS_VTG | 9 | M_7 net_2 en gnd gnd nmos_vtg w=270.0n l=50.0n | transistor_netlist_usage | False | Netlist instance usage proves model names are expected by project SPICE. |
| E:\njust\keyan\SRAM Compiler_V2\OpenRAM-stable\technology\freepdk45\sp_lib\sense_amp.sp | PMOS_VTG | 11 | M_9 dout_bar dint vdd vdd pmos_vtg w=180.0n l=50.0n | transistor_netlist_usage | False | Netlist instance usage proves model names are expected by project SPICE. |
| E:\njust\keyan\SRAM Compiler_V2\OpenRAM-stable\technology\freepdk45\sp_lib\sense_amp.sp | NMOS_VTG | 12 | M_10 dout_bar dint gnd gnd nmos_vtg w=90.0n l=50.0n | transistor_netlist_usage | False | Netlist instance usage proves model names are expected by project SPICE. |
| E:\njust\keyan\SRAM Compiler_V2\OpenRAM-stable\technology\freepdk45\sp_lib\sense_amp.sp | PMOS_VTG | 13 | M_11 dout dout_bar vdd vdd pmos_vtg w=540.0n l=50.0n | transistor_netlist_usage | False | Netlist instance usage proves model names are expected by project SPICE. |
| E:\njust\keyan\SRAM Compiler_V2\OpenRAM-stable\technology\freepdk45\sp_lib\sense_amp.sp | NMOS_VTG | 14 | M_12 dout dout_bar gnd gnd nmos_vtg w=270.0n l=50.0n | transistor_netlist_usage | False | Netlist instance usage proves model names are expected by project SPICE. |
| E:\njust\keyan\SRAM Compiler_V2\OpenRAM-stable\technology\freepdk45\sp_lib\tri_gate.sp | NMOS_VTG | 3 | M_1 net_2 in_inv gnd gnd NMOS_VTG W=180.000000n L=50.000000n | transistor_netlist_usage | False | Netlist instance usage proves model names are expected by project SPICE. |
| E:\njust\keyan\SRAM Compiler_V2\OpenRAM-stable\technology\freepdk45\sp_lib\tri_gate.sp | NMOS_VTG | 4 | M_2 out en net_2 gnd NMOS_VTG W=180.000000n L=50.000000n | transistor_netlist_usage | False | Netlist instance usage proves model names are expected by project SPICE. |
| E:\njust\keyan\SRAM Compiler_V2\OpenRAM-stable\technology\freepdk45\sp_lib\tri_gate.sp | PMOS_VTG | 5 | M_3 net_3 in_inv vdd vdd PMOS_VTG W=360.000000n L=50.000000n | transistor_netlist_usage | False | Netlist instance usage proves model names are expected by project SPICE. |
| E:\njust\keyan\SRAM Compiler_V2\OpenRAM-stable\technology\freepdk45\sp_lib\tri_gate.sp | PMOS_VTG | 6 | M_4 out en_bar net_3 vdd PMOS_VTG W=360.000000n L=50.000000n | transistor_netlist_usage | False | Netlist instance usage proves model names are expected by project SPICE. |
| E:\njust\keyan\SRAM Compiler_V2\OpenRAM-stable\technology\freepdk45\sp_lib\tri_gate.sp | PMOS_VTG | 7 | M_5 in_inv in vdd vdd PMOS_VTG W=180.000000n L=50.000000n | transistor_netlist_usage | False | Netlist instance usage proves model names are expected by project SPICE. |
| E:\njust\keyan\SRAM Compiler_V2\OpenRAM-stable\technology\freepdk45\sp_lib\tri_gate.sp | NMOS_VTG | 8 | M_6 in_inv in gnd gnd NMOS_VTG W=90.000000n L=50.000000n | transistor_netlist_usage | False | Netlist instance usage proves model names are expected by project SPICE. |
| E:\njust\keyan\SRAM Compiler_V2\OpenRAM-stable\technology\freepdk45\sp_lib\write_driver.sp | PMOS_VTG | 4 | minP bl_bar din vdd vdd pmos_vtg w=360.000000n l=50.000000n | transistor_netlist_usage | False | Netlist instance usage proves model names are expected by project SPICE. |
| E:\njust\keyan\SRAM Compiler_V2\OpenRAM-stable\technology\freepdk45\sp_lib\write_driver.sp | NMOS_VTG | 5 | minN bl_bar din gnd gnd nmos_vtg w=180.000000n l=50.000000n | transistor_netlist_usage | False | Netlist instance usage proves model names are expected by project SPICE. |
| E:\njust\keyan\SRAM Compiler_V2\OpenRAM-stable\technology\freepdk45\sp_lib\write_driver.sp | PMOS_VTG | 6 | moutP en_bar en vdd vdd pmos_vtg w=360.000000n l=50.000000n | transistor_netlist_usage | False | Netlist instance usage proves model names are expected by project SPICE. |
| E:\njust\keyan\SRAM Compiler_V2\OpenRAM-stable\technology\freepdk45\sp_lib\write_driver.sp | NMOS_VTG | 7 | moutN en_bar en gnd gnd nmos_vtg w=180.000000n l=50.000000n | transistor_netlist_usage | False | Netlist instance usage proves model names are expected by project SPICE. |
| E:\njust\keyan\SRAM Compiler_V2\OpenRAM-stable\technology\freepdk45\sp_lib\write_driver.sp | PMOS_VTG | 10 | mout0P int1 bl_bar vdd vdd pmos_vtg w=360.000000n l=50.000000n | transistor_netlist_usage | False | Netlist instance usage proves model names are expected by project SPICE. |
| E:\njust\keyan\SRAM Compiler_V2\OpenRAM-stable\technology\freepdk45\sp_lib\write_driver.sp | PMOS_VTG | 11 | mout0P2 bl en_bar int1 vdd pmos_vtg w=360.000000n l=50.000000n | transistor_netlist_usage | False | Netlist instance usage proves model names are expected by project SPICE. |
| E:\njust\keyan\SRAM Compiler_V2\OpenRAM-stable\technology\freepdk45\sp_lib\write_driver.sp | NMOS_VTG | 12 | mout0N bl en int2 gnd nmos_vtg w=180.000000n l=50.000000n | transistor_netlist_usage | False | Netlist instance usage proves model names are expected by project SPICE. |
| E:\njust\keyan\SRAM Compiler_V2\OpenRAM-stable\technology\freepdk45\sp_lib\write_driver.sp | NMOS_VTG | 13 | mout0N2 int2 bl_bar gnd gnd nmos_vtg w=180.000000n l=50.000000n | transistor_netlist_usage | False | Netlist instance usage proves model names are expected by project SPICE. |
| E:\njust\keyan\SRAM Compiler_V2\OpenRAM-stable\technology\freepdk45\sp_lib\write_driver.sp | PMOS_VTG | 16 | mout1P int3 din vdd vdd pmos_vtg w=360.000000n l=50.000000n | transistor_netlist_usage | False | Netlist instance usage proves model names are expected by project SPICE. |
| E:\njust\keyan\SRAM Compiler_V2\OpenRAM-stable\technology\freepdk45\sp_lib\write_driver.sp | PMOS_VTG | 17 | mout1P2 br en_bar int3 vdd pmos_vtg w=360.000000n l=50.000000n | transistor_netlist_usage | False | Netlist instance usage proves model names are expected by project SPICE. |
| E:\njust\keyan\SRAM Compiler_V2\OpenRAM-stable\technology\freepdk45\sp_lib\write_driver.sp | NMOS_VTG | 18 | mout1N br en int4 gnd nmos_vtg w=180.000000n l=50.000000n | transistor_netlist_usage | False | Netlist instance usage proves model names are expected by project SPICE. |
| E:\njust\keyan\SRAM Compiler_V2\OpenRAM-stable\technology\freepdk45\sp_lib\write_driver.sp | NMOS_VTG | 19 | mout1N2 int4 din gnd gnd nmos_vtg w=180.000000n l=50.000000n | transistor_netlist_usage | False | Netlist instance usage proves model names are expected by project SPICE. |
| E:\njust\keyan\SRAM Compiler_V2\OpenRAM-stable\technology\freepdk45\tf\README.txt | freepdk45 | 1 | These technology files are from the FreePDK45nm design kit. | metadata_or_reference | False | Reference match. |
| E:\njust\keyan\SRAM Compiler_V2\OpenRAM-stable\technology\freepdk45\tf\README.txt | freepdk45 | 47 | FreePDK45.lyp is converted automatically from the .tf using: | metadata_or_reference | False | Reference match. |
| E:\njust\keyan\SRAM Compiler_V2\OpenRAM-stable\technology\freepdk45\tf\README.txt | freepdk45 | 50 | klayout -z -rd tf_file=FreePDK45.tf -rd lyp_file=FreePDK45.lyp | metadata_or_reference | False | Reference match. |
| E:\njust\keyan\SRAM Compiler_V2\OpenRAM-stable\technology\freepdk45\tf\README.txt | freepdk45 | 54 | glade_freepdk45.py is a script for Glade: | metadata_or_reference | False | Reference match. |
| E:\njust\keyan\SRAM Compiler_V2\OpenRAM-stable\technology\freepdk45\tf\README.txt | freepdk45 | 57 | glade -script ~/openram/technology/freepdk45/tf/glade_freepdk45.py -gds file.gds | metadata_or_reference | False | Reference match. |
| E:\njust\keyan\SRAM Compiler_V2\OpenRAM-stable\technology\freepdk45\models\tran_models\models_ff\NMOS_THKOX.inc | nmos | 1 | * Customized PTM 45 NMOS: ff | metadata_or_reference | True | Reference match. |
| E:\njust\keyan\SRAM Compiler_V2\OpenRAM-stable\technology\freepdk45\models\tran_models\models_ff\NMOS_THKOX.inc | .model | 3 | .model  NMOS_THKOX  nmos  level = 54 | metadata_or_reference | True | Reference match. |
| E:\njust\keyan\SRAM Compiler_V2\OpenRAM-stable\technology\freepdk45\models\tran_models\models_ff\NMOS_VTG.inc | nmos | 1 | * Customized PTM 45 NMOS ff | metadata_or_reference | True | Reference match. |
| E:\njust\keyan\SRAM Compiler_V2\OpenRAM-stable\technology\freepdk45\models\tran_models\models_ff\NMOS_VTG.inc | NMOS_VTG | 3 | .model  NMOS_VTG  nmos  level = 54 | device_model_definition | True | Direct model definition. |
| E:\njust\keyan\SRAM Compiler_V2\OpenRAM-stable\technology\freepdk45\models\tran_models\models_ff\NMOS_VTH.inc | nmos | 1 | * Customized PTM 45 NMOS NMOS_VTH ff | metadata_or_reference | True | Reference match. |
| E:\njust\keyan\SRAM Compiler_V2\OpenRAM-stable\technology\freepdk45\models\tran_models\models_ff\NMOS_VTH.inc | .model | 3 | .model  NMOS_VTH  nmos  level = 54 | metadata_or_reference | True | Reference match. |
| E:\njust\keyan\SRAM Compiler_V2\OpenRAM-stable\technology\freepdk45\models\tran_models\models_ff\NMOS_VTL.inc | nmos | 1 | * Customized PTM 45 NMOS ff | metadata_or_reference | True | Reference match. |
| E:\njust\keyan\SRAM Compiler_V2\OpenRAM-stable\technology\freepdk45\models\tran_models\models_ff\NMOS_VTL.inc | .model | 3 | .model  NMOS_VTL  nmos  level = 54 | metadata_or_reference | True | Reference match. |
| E:\njust\keyan\SRAM Compiler_V2\OpenRAM-stable\technology\freepdk45\models\tran_models\models_ff\PMOS_THKOX.inc | pmos | 1 | * Customized PTM 45 PMOS: ff | metadata_or_reference | True | Reference match. |
| E:\njust\keyan\SRAM Compiler_V2\OpenRAM-stable\technology\freepdk45\models\tran_models\models_ff\PMOS_THKOX.inc | .model | 3 | .model  PMOS_THKOX  pmos  level = 54 | metadata_or_reference | True | Reference match. |
| E:\njust\keyan\SRAM Compiler_V2\OpenRAM-stable\technology\freepdk45\models\tran_models\models_ff\PMOS_VTG.inc | PMOS_VTG | 1 | * Customized PTM 45 PMOS PMOS_VTG ff | metadata_or_reference | True | Reference match. |
| E:\njust\keyan\SRAM Compiler_V2\OpenRAM-stable\technology\freepdk45\models\tran_models\models_ff\PMOS_VTG.inc | PMOS_VTG | 3 | .model  PMOS_VTG  pmos  level = 54 | device_model_definition | True | Direct model definition. |
| E:\njust\keyan\SRAM Compiler_V2\OpenRAM-stable\technology\freepdk45\models\tran_models\models_ff\PMOS_VTH.inc | pmos | 1 | * Customized PTM 45 PMOS PMOS_VTH ff | metadata_or_reference | True | Reference match. |
| E:\njust\keyan\SRAM Compiler_V2\OpenRAM-stable\technology\freepdk45\models\tran_models\models_ff\PMOS_VTH.inc | .model | 3 | .model  PMOS_VTH  pmos  level = 54 | metadata_or_reference | True | Reference match. |
| E:\njust\keyan\SRAM Compiler_V2\OpenRAM-stable\technology\freepdk45\models\tran_models\models_ff\PMOS_VTL.inc | pmos | 1 | * Customized PTM 45 PMOS ff | metadata_or_reference | True | Reference match. |
| E:\njust\keyan\SRAM Compiler_V2\OpenRAM-stable\technology\freepdk45\models\tran_models\models_ff\PMOS_VTL.inc | .model | 3 | .model  PMOS_VTL  pmos  level = 54 | metadata_or_reference | True | Reference match. |
| E:\njust\keyan\SRAM Compiler_V2\OpenRAM-stable\technology\freepdk45\models\tran_models\models_nom\NMOS_THKOX.inc | nmos | 1 | * Customized PTM 45 NMOS NMOS_THKOX | metadata_or_reference | True | Reference match. |
| E:\njust\keyan\SRAM Compiler_V2\OpenRAM-stable\technology\freepdk45\models\tran_models\models_nom\NMOS_THKOX.inc | .model | 3 | .model  NMOS_THKOX  nmos  level = 54 | metadata_or_reference | True | Reference match. |
| E:\njust\keyan\SRAM Compiler_V2\OpenRAM-stable\technology\freepdk45\models\tran_models\models_nom\NMOS_VTG.inc | nmos | 1 | * Customized PTM 45 NMOS nom | metadata_or_reference | True | Reference match. |
| E:\njust\keyan\SRAM Compiler_V2\OpenRAM-stable\technology\freepdk45\models\tran_models\models_nom\NMOS_VTG.inc | NMOS_VTG | 3 | .model  NMOS_VTG  nmos  level = 54 | device_model_definition | True | Direct model definition. |
| E:\njust\keyan\SRAM Compiler_V2\OpenRAM-stable\technology\freepdk45\models\tran_models\models_nom\NMOS_VTH.inc | nmos | 1 | * Customized PTM 45 NMOS NMOS_VTH | metadata_or_reference | True | Reference match. |
| E:\njust\keyan\SRAM Compiler_V2\OpenRAM-stable\technology\freepdk45\models\tran_models\models_nom\NMOS_VTH.inc | .model | 3 | .model  NMOS_VTH  nmos  level = 54 | metadata_or_reference | True | Reference match. |
| E:\njust\keyan\SRAM Compiler_V2\OpenRAM-stable\technology\freepdk45\models\tran_models\models_nom\NMOS_VTL.inc | nmos | 1 | * Customized PTM 45 NMOS nom | metadata_or_reference | True | Reference match. |
| E:\njust\keyan\SRAM Compiler_V2\OpenRAM-stable\technology\freepdk45\models\tran_models\models_nom\NMOS_VTL.inc | .model | 3 | .model  NMOS_VTL  nmos  level = 54 | metadata_or_reference | True | Reference match. |
| E:\njust\keyan\SRAM Compiler_V2\OpenRAM-stable\technology\freepdk45\models\tran_models\models_nom\PMOS_THKOX.inc | pmos | 1 | * Customized PTM 45 PMOS PMOS_THKOX | metadata_or_reference | True | Reference match. |
| E:\njust\keyan\SRAM Compiler_V2\OpenRAM-stable\technology\freepdk45\models\tran_models\models_nom\PMOS_THKOX.inc | .model | 3 | .model  PMOS_THKOX  pmos  level = 54 | metadata_or_reference | True | Reference match. |
| E:\njust\keyan\SRAM Compiler_V2\OpenRAM-stable\technology\freepdk45\models\tran_models\models_nom\PMOS_VTG.inc | PMOS_VTG | 1 | * Customized PTM 45 PMOS PMOS_VTG | metadata_or_reference | True | Reference match. |
| E:\njust\keyan\SRAM Compiler_V2\OpenRAM-stable\technology\freepdk45\models\tran_models\models_nom\PMOS_VTG.inc | PMOS_VTG | 3 | .model  PMOS_VTG  pmos  level = 54 | device_model_definition | True | Direct model definition. |
| E:\njust\keyan\SRAM Compiler_V2\OpenRAM-stable\technology\freepdk45\models\tran_models\models_nom\PMOS_VTH.inc | pmos | 1 | * Customized PTM 45 PMOS PMOS_VTH | metadata_or_reference | True | Reference match. |
| E:\njust\keyan\SRAM Compiler_V2\OpenRAM-stable\technology\freepdk45\models\tran_models\models_nom\PMOS_VTH.inc | .model | 3 | .model  PMOS_VTH  pmos  level = 54 | metadata_or_reference | True | Reference match. |
| E:\njust\keyan\SRAM Compiler_V2\OpenRAM-stable\technology\freepdk45\models\tran_models\models_nom\PMOS_VTL.inc | pmos | 1 | * Customized PTM 45 PMOS | metadata_or_reference | True | Reference match. |
| E:\njust\keyan\SRAM Compiler_V2\OpenRAM-stable\technology\freepdk45\models\tran_models\models_nom\PMOS_VTL.inc | .model | 3 | .model  PMOS_VTL  pmos  level = 54 | metadata_or_reference | True | Reference match. |
| E:\njust\keyan\SRAM Compiler_V2\OpenRAM-stable\technology\freepdk45\models\tran_models\models_ss\NMOS_THKOX.inc | nmos | 1 | * Customized PTM 45 NMOS: ss | metadata_or_reference | True | Reference match. |
| E:\njust\keyan\SRAM Compiler_V2\OpenRAM-stable\technology\freepdk45\models\tran_models\models_ss\NMOS_THKOX.inc | .model | 3 | .model  NMOS_THKOX  nmos  level = 54 | metadata_or_reference | True | Reference match. |
| E:\njust\keyan\SRAM Compiler_V2\OpenRAM-stable\technology\freepdk45\models\tran_models\models_ss\NMOS_VTG.inc | nmos | 1 | * Customized PTM 45 NMOS ss | metadata_or_reference | True | Reference match. |
| E:\njust\keyan\SRAM Compiler_V2\OpenRAM-stable\technology\freepdk45\models\tran_models\models_ss\NMOS_VTG.inc | NMOS_VTG | 3 | .model  NMOS_VTG  nmos  level = 54 | device_model_definition | True | Direct model definition. |
| E:\njust\keyan\SRAM Compiler_V2\OpenRAM-stable\technology\freepdk45\models\tran_models\models_ss\NMOS_VTH.inc | nmos | 1 | * Customized PTM 45 NMOS NMOS_VTH ss | metadata_or_reference | True | Reference match. |
| E:\njust\keyan\SRAM Compiler_V2\OpenRAM-stable\technology\freepdk45\models\tran_models\models_ss\NMOS_VTH.inc | .model | 3 | .model  NMOS_VTH  nmos  level = 54 | metadata_or_reference | True | Reference match. |
| E:\njust\keyan\SRAM Compiler_V2\OpenRAM-stable\technology\freepdk45\models\tran_models\models_ss\NMOS_VTL.inc | nmos | 1 | * Customized PTM 45 NMOS ss | metadata_or_reference | True | Reference match. |
| E:\njust\keyan\SRAM Compiler_V2\OpenRAM-stable\technology\freepdk45\models\tran_models\models_ss\NMOS_VTL.inc | .model | 3 | .model  NMOS_VTL  nmos  level = 54 | metadata_or_reference | True | Reference match. |
| E:\njust\keyan\SRAM Compiler_V2\OpenRAM-stable\technology\freepdk45\models\tran_models\models_ss\PMOS_THKOX.inc | pmos | 1 | * Customized PTM 45 PMOS: ss | metadata_or_reference | True | Reference match. |
| E:\njust\keyan\SRAM Compiler_V2\OpenRAM-stable\technology\freepdk45\models\tran_models\models_ss\PMOS_THKOX.inc | .model | 3 | .model  PMOS_THKOX  pmos  level = 54 | metadata_or_reference | True | Reference match. |
| E:\njust\keyan\SRAM Compiler_V2\OpenRAM-stable\technology\freepdk45\models\tran_models\models_ss\PMOS_VTG.inc | PMOS_VTG | 1 | * Customized PTM 45 PMOS PMOS_VTG ss | metadata_or_reference | True | Reference match. |
| E:\njust\keyan\SRAM Compiler_V2\OpenRAM-stable\technology\freepdk45\models\tran_models\models_ss\PMOS_VTG.inc | PMOS_VTG | 3 | .model  PMOS_VTG  pmos  level = 54 | device_model_definition | True | Direct model definition. |
| E:\njust\keyan\SRAM Compiler_V2\OpenRAM-stable\technology\freepdk45\models\tran_models\models_ss\PMOS_VTH.inc | pmos | 1 | * Customized PTM 45 PMOS PMOS_VTH | metadata_or_reference | True | Reference match. |
| E:\njust\keyan\SRAM Compiler_V2\OpenRAM-stable\technology\freepdk45\models\tran_models\models_ss\PMOS_VTH.inc | .model | 3 | .model  PMOS_VTH  pmos  level = 54 | metadata_or_reference | True | Reference match. |
| E:\njust\keyan\SRAM Compiler_V2\OpenRAM-stable\technology\freepdk45\models\tran_models\models_ss\PMOS_VTL.inc | pmos | 1 | * Customized PTM 45 PMOS ss | metadata_or_reference | True | Reference match. |
| E:\njust\keyan\SRAM Compiler_V2\OpenRAM-stable\technology\freepdk45\models\tran_models\models_ss\PMOS_VTL.inc | .model | 3 | .model  PMOS_VTL  pmos  level = 54 | metadata_or_reference | True | Reference match. |
| E:\njust\keyan\SRAM Compiler_V2\OpenRAM-stable\deliverables\sram_layoutgen_step45_clean\technology\freepdk45\sp_lib\cell_1rw.sp | NMOS_VTG | 4 | MM0 Q_bar Q gnd gnd NMOS_VTG W=205.00n L=50n | transistor_netlist_usage | False | Netlist instance usage proves model names are expected by project SPICE. |
| E:\njust\keyan\SRAM Compiler_V2\OpenRAM-stable\deliverables\sram_layoutgen_step45_clean\technology\freepdk45\sp_lib\cell_1rw.sp | PMOS_VTG | 5 | MM4 Q_bar Q vdd vdd PMOS_VTG W=90n L=50n | transistor_netlist_usage | False | Netlist instance usage proves model names are expected by project SPICE. |
| E:\njust\keyan\SRAM Compiler_V2\OpenRAM-stable\deliverables\sram_layoutgen_step45_clean\technology\freepdk45\sp_lib\cell_1rw.sp | NMOS_VTG | 8 | MM1 Q Q_bar gnd gnd NMOS_VTG W=205.00n L=50n | transistor_netlist_usage | False | Netlist instance usage proves model names are expected by project SPICE. |
| E:\njust\keyan\SRAM Compiler_V2\OpenRAM-stable\deliverables\sram_layoutgen_step45_clean\technology\freepdk45\sp_lib\cell_1rw.sp | PMOS_VTG | 9 | MM5 Q Q_bar vdd vdd PMOS_VTG W=90n L=50n | transistor_netlist_usage | False | Netlist instance usage proves model names are expected by project SPICE. |
| E:\njust\keyan\SRAM Compiler_V2\OpenRAM-stable\deliverables\sram_layoutgen_step45_clean\technology\freepdk45\sp_lib\cell_1rw.sp | NMOS_VTG | 12 | MM3 bl wl Q gnd NMOS_VTG W=135.00n L=50n | transistor_netlist_usage | False | Netlist instance usage proves model names are expected by project SPICE. |
| E:\njust\keyan\SRAM Compiler_V2\OpenRAM-stable\deliverables\sram_layoutgen_step45_clean\technology\freepdk45\sp_lib\cell_1rw.sp | NMOS_VTG | 13 | MM2 br wl Q_bar gnd NMOS_VTG W=135.00n L=50n | transistor_netlist_usage | False | Netlist instance usage proves model names are expected by project SPICE. |
| E:\njust\keyan\SRAM Compiler_V2\OpenRAM-stable\deliverables\sram_layoutgen_step45_clean\technology\freepdk45\sp_lib\cell_2rw.sp | NMOS_VTG | 3 | MM9 RA_to_R_right wl1 br1 gnd NMOS_VTG W=180.0n L=50n m=1 | transistor_netlist_usage | False | Netlist instance usage proves model names are expected by project SPICE. |
| E:\njust\keyan\SRAM Compiler_V2\OpenRAM-stable\deliverables\sram_layoutgen_step45_clean\technology\freepdk45\sp_lib\cell_2rw.sp | NMOS_VTG | 4 | MM8 RA_to_R_right Q gnd gnd NMOS_VTG W=180.0n L=50n m=1 | transistor_netlist_usage | False | Netlist instance usage proves model names are expected by project SPICE. |
| E:\njust\keyan\SRAM Compiler_V2\OpenRAM-stable\deliverables\sram_layoutgen_step45_clean\technology\freepdk45\sp_lib\cell_2rw.sp | NMOS_VTG | 5 | MM7 RA_to_R_left Q_bar gnd gnd NMOS_VTG W=180.0n L=50n m=1 | transistor_netlist_usage | False | Netlist instance usage proves model names are expected by project SPICE. |
| E:\njust\keyan\SRAM Compiler_V2\OpenRAM-stable\deliverables\sram_layoutgen_step45_clean\technology\freepdk45\sp_lib\cell_2rw.sp | NMOS_VTG | 6 | MM6 RA_to_R_left wl1 bl1 gnd NMOS_VTG W=180.0n L=50n m=1 | transistor_netlist_usage | False | Netlist instance usage proves model names are expected by project SPICE. |
| E:\njust\keyan\SRAM Compiler_V2\OpenRAM-stable\deliverables\sram_layoutgen_step45_clean\technology\freepdk45\sp_lib\cell_2rw.sp | NMOS_VTG | 7 | MM5 Q wl0 bl0 gnd NMOS_VTG W=135.00n L=50n m=1 | transistor_netlist_usage | False | Netlist instance usage proves model names are expected by project SPICE. |
| E:\njust\keyan\SRAM Compiler_V2\OpenRAM-stable\deliverables\sram_layoutgen_step45_clean\technology\freepdk45\sp_lib\cell_2rw.sp | NMOS_VTG | 8 | MM4 Q_bar wl0 br0 gnd NMOS_VTG W=135.00n L=50n m=1 | transistor_netlist_usage | False | Netlist instance usage proves model names are expected by project SPICE. |
| E:\njust\keyan\SRAM Compiler_V2\OpenRAM-stable\deliverables\sram_layoutgen_step45_clean\technology\freepdk45\sp_lib\cell_2rw.sp | NMOS_VTG | 9 | MM1 Q Q_bar gnd gnd NMOS_VTG W=205.0n L=50n m=1 | transistor_netlist_usage | False | Netlist instance usage proves model names are expected by project SPICE. |
| E:\njust\keyan\SRAM Compiler_V2\OpenRAM-stable\deliverables\sram_layoutgen_step45_clean\technology\freepdk45\sp_lib\cell_2rw.sp | NMOS_VTG | 10 | MM0 Q_bar Q gnd gnd NMOS_VTG W=205.0n L=50n m=1 | transistor_netlist_usage | False | Netlist instance usage proves model names are expected by project SPICE. |
| E:\njust\keyan\SRAM Compiler_V2\OpenRAM-stable\deliverables\sram_layoutgen_step45_clean\technology\freepdk45\sp_lib\cell_2rw.sp | PMOS_VTG | 11 | MM3 Q Q_bar vdd vdd PMOS_VTG W=90n L=50n m=1 | transistor_netlist_usage | False | Netlist instance usage proves model names are expected by project SPICE. |
| E:\njust\keyan\SRAM Compiler_V2\OpenRAM-stable\deliverables\sram_layoutgen_step45_clean\technology\freepdk45\sp_lib\cell_2rw.sp | PMOS_VTG | 12 | MM2 Q_bar Q vdd vdd PMOS_VTG W=90n L=50n m=1 | transistor_netlist_usage | False | Netlist instance usage proves model names are expected by project SPICE. |
| E:\njust\keyan\SRAM Compiler_V2\OpenRAM-stable\deliverables\sram_layoutgen_step45_clean\technology\freepdk45\sp_lib\dff.sp | NMOS_VTG | 8 | MM21 Q a_66_6# gnd gnd NMOS_VTG L=5e-08 W=5e-07 | transistor_netlist_usage | False | Netlist instance usage proves model names are expected by project SPICE. |
| E:\njust\keyan\SRAM Compiler_V2\OpenRAM-stable\deliverables\sram_layoutgen_step45_clean\technology\freepdk45\sp_lib\dff.sp | NMOS_VTG | 9 | MM19 a_76_6# a_2_6# a_66_6# gnd NMOS_VTG L=5e-08 W=2.5e-07 | transistor_netlist_usage | False | Netlist instance usage proves model names are expected by project SPICE. |
| E:\njust\keyan\SRAM Compiler_V2\OpenRAM-stable\deliverables\sram_layoutgen_step45_clean\technology\freepdk45\sp_lib\dff.sp | NMOS_VTG | 10 | MM20 gnd Q a_76_6# gnd NMOS_VTG L=5e-08 W=2.5e-07 | transistor_netlist_usage | False | Netlist instance usage proves model names are expected by project SPICE. |
| E:\njust\keyan\SRAM Compiler_V2\OpenRAM-stable\deliverables\sram_layoutgen_step45_clean\technology\freepdk45\sp_lib\dff.sp | NMOS_VTG | 11 | MM18 a_66_6# clk a_61_6# gnd NMOS_VTG L=5e-08 W=2.5e-07 | transistor_netlist_usage | False | Netlist instance usage proves model names are expected by project SPICE. |
| E:\njust\keyan\SRAM Compiler_V2\OpenRAM-stable\deliverables\sram_layoutgen_step45_clean\technology\freepdk45\sp_lib\dff.sp | NMOS_VTG | 12 | MM17 a_61_6# a_34_4# gnd gnd NMOS_VTG L=5e-08 W=2.5e-07 | transistor_netlist_usage | False | Netlist instance usage proves model names are expected by project SPICE. |
| E:\njust\keyan\SRAM Compiler_V2\OpenRAM-stable\deliverables\sram_layoutgen_step45_clean\technology\freepdk45\sp_lib\dff.sp | NMOS_VTG | 13 | MM10 gnd clk a_2_6# gnd NMOS_VTG L=5e-08 W=5e-07 | transistor_netlist_usage | False | Netlist instance usage proves model names are expected by project SPICE. |
| E:\njust\keyan\SRAM Compiler_V2\OpenRAM-stable\deliverables\sram_layoutgen_step45_clean\technology\freepdk45\sp_lib\dff.sp | NMOS_VTG | 14 | MM16 a_34_4# a_22_6# gnd gnd NMOS_VTG L=5e-08 W=2.5e-07 | transistor_netlist_usage | False | Netlist instance usage proves model names are expected by project SPICE. |
| E:\njust\keyan\SRAM Compiler_V2\OpenRAM-stable\deliverables\sram_layoutgen_step45_clean\technology\freepdk45\sp_lib\dff.sp | NMOS_VTG | 15 | MM15 gnd a_34_4# a_31_6# gnd NMOS_VTG L=5e-08 W=2.5e-07 | transistor_netlist_usage | False | Netlist instance usage proves model names are expected by project SPICE. |
| E:\njust\keyan\SRAM Compiler_V2\OpenRAM-stable\deliverables\sram_layoutgen_step45_clean\technology\freepdk45\sp_lib\dff.sp | NMOS_VTG | 16 | MM14 a_31_6# clk a_22_6# gnd NMOS_VTG L=5e-08 W=2.5e-07 | transistor_netlist_usage | False | Netlist instance usage proves model names are expected by project SPICE. |
| E:\njust\keyan\SRAM Compiler_V2\OpenRAM-stable\deliverables\sram_layoutgen_step45_clean\technology\freepdk45\sp_lib\dff.sp | NMOS_VTG | 17 | MM13 a_22_6# a_2_6# a_17_6# gnd NMOS_VTG L=5e-08 W=2.5e-07 | transistor_netlist_usage | False | Netlist instance usage proves model names are expected by project SPICE. |
| E:\njust\keyan\SRAM Compiler_V2\OpenRAM-stable\deliverables\sram_layoutgen_step45_clean\technology\freepdk45\sp_lib\dff.sp | NMOS_VTG | 18 | MM12 a_17_6# D gnd gnd NMOS_VTG L=5e-08 W=2.5e-07 | transistor_netlist_usage | False | Netlist instance usage proves model names are expected by project SPICE. |
| E:\njust\keyan\SRAM Compiler_V2\OpenRAM-stable\deliverables\sram_layoutgen_step45_clean\technology\freepdk45\sp_lib\dff.sp | PMOS_VTG | 19 | MM11 Q a_66_6# vdd vdd PMOS_VTG L=5e-08 W=1e-06 | transistor_netlist_usage | False | Netlist instance usage proves model names are expected by project SPICE. |
| E:\njust\keyan\SRAM Compiler_V2\OpenRAM-stable\deliverables\sram_layoutgen_step45_clean\technology\freepdk45\sp_lib\dff.sp | PMOS_VTG | 20 | MM9 vdd Q a_76_84# vdd PMOS_VTG L=5e-08 W=2.5e-07 | transistor_netlist_usage | False | Netlist instance usage proves model names are expected by project SPICE. |
| E:\njust\keyan\SRAM Compiler_V2\OpenRAM-stable\deliverables\sram_layoutgen_step45_clean\technology\freepdk45\sp_lib\dff.sp | PMOS_VTG | 21 | MM8 a_76_84# clk a_66_6# vdd PMOS_VTG L=5e-08 W=2.5e-07 | transistor_netlist_usage | False | Netlist instance usage proves model names are expected by project SPICE. |
| E:\njust\keyan\SRAM Compiler_V2\OpenRAM-stable\deliverables\sram_layoutgen_step45_clean\technology\freepdk45\sp_lib\dff.sp | PMOS_VTG | 22 | MM7 a_66_6# a_2_6# a_61_74# vdd PMOS_VTG L=5e-08 W=5e-07 | transistor_netlist_usage | False | Netlist instance usage proves model names are expected by project SPICE. |
| E:\njust\keyan\SRAM Compiler_V2\OpenRAM-stable\deliverables\sram_layoutgen_step45_clean\technology\freepdk45\sp_lib\dff.sp | PMOS_VTG | 23 | MM6 a_61_74# a_34_4# vdd vdd PMOS_VTG L=5e-08 W=5e-07 | transistor_netlist_usage | False | Netlist instance usage proves model names are expected by project SPICE. |
| E:\njust\keyan\SRAM Compiler_V2\OpenRAM-stable\deliverables\sram_layoutgen_step45_clean\technology\freepdk45\sp_lib\dff.sp | PMOS_VTG | 24 | MM0 vdd clk a_2_6# vdd PMOS_VTG L=5e-08 W=1e-06 | transistor_netlist_usage | False | Netlist instance usage proves model names are expected by project SPICE. |
| E:\njust\keyan\SRAM Compiler_V2\OpenRAM-stable\deliverables\sram_layoutgen_step45_clean\technology\freepdk45\sp_lib\dff.sp | PMOS_VTG | 25 | MM5 a_34_4# a_22_6# vdd vdd PMOS_VTG L=5e-08 W=5e-07 | transistor_netlist_usage | False | Netlist instance usage proves model names are expected by project SPICE. |
| E:\njust\keyan\SRAM Compiler_V2\OpenRAM-stable\deliverables\sram_layoutgen_step45_clean\technology\freepdk45\sp_lib\dff.sp | PMOS_VTG | 26 | MM4 vdd a_34_4# a_31_74# vdd PMOS_VTG L=5e-08 W=5e-07 | transistor_netlist_usage | False | Netlist instance usage proves model names are expected by project SPICE. |
| E:\njust\keyan\SRAM Compiler_V2\OpenRAM-stable\deliverables\sram_layoutgen_step45_clean\technology\freepdk45\sp_lib\dff.sp | PMOS_VTG | 27 | MM3 a_31_74# a_2_6# a_22_6# vdd PMOS_VTG L=5e-08 W=5e-07 | transistor_netlist_usage | False | Netlist instance usage proves model names are expected by project SPICE. |
| E:\njust\keyan\SRAM Compiler_V2\OpenRAM-stable\deliverables\sram_layoutgen_step45_clean\technology\freepdk45\sp_lib\dff.sp | PMOS_VTG | 28 | MM2 a_22_6# clk a_17_74# vdd PMOS_VTG L=5e-08 W=5e-07 | transistor_netlist_usage | False | Netlist instance usage proves model names are expected by project SPICE. |
| E:\njust\keyan\SRAM Compiler_V2\OpenRAM-stable\deliverables\sram_layoutgen_step45_clean\technology\freepdk45\sp_lib\dff.sp | PMOS_VTG | 29 | MM1 a_17_74# D vdd vdd PMOS_VTG L=5e-08 W=5e-07 | transistor_netlist_usage | False | Netlist instance usage proves model names are expected by project SPICE. |
| E:\njust\keyan\SRAM Compiler_V2\OpenRAM-stable\deliverables\sram_layoutgen_step45_clean\technology\freepdk45\sp_lib\dummy_cell_1rw.sp | NMOS_VTG | 4 | MM0 Q_bar Q gnd gnd NMOS_VTG W=205.00n L=50n | transistor_netlist_usage | False | Netlist instance usage proves model names are expected by project SPICE. |
| E:\njust\keyan\SRAM Compiler_V2\OpenRAM-stable\deliverables\sram_layoutgen_step45_clean\technology\freepdk45\sp_lib\dummy_cell_1rw.sp | PMOS_VTG | 5 | MM4 Q_bar Q vdd vdd PMOS_VTG W=90n L=50n | transistor_netlist_usage | False | Netlist instance usage proves model names are expected by project SPICE. |
| E:\njust\keyan\SRAM Compiler_V2\OpenRAM-stable\deliverables\sram_layoutgen_step45_clean\technology\freepdk45\sp_lib\dummy_cell_1rw.sp | NMOS_VTG | 8 | MM1 Q Q_bar gnd gnd NMOS_VTG W=205.00n L=50n | transistor_netlist_usage | False | Netlist instance usage proves model names are expected by project SPICE. |
| E:\njust\keyan\SRAM Compiler_V2\OpenRAM-stable\deliverables\sram_layoutgen_step45_clean\technology\freepdk45\sp_lib\dummy_cell_1rw.sp | PMOS_VTG | 9 | MM5 Q Q_bar vdd vdd PMOS_VTG W=90n L=50n | transistor_netlist_usage | False | Netlist instance usage proves model names are expected by project SPICE. |
| E:\njust\keyan\SRAM Compiler_V2\OpenRAM-stable\deliverables\sram_layoutgen_step45_clean\technology\freepdk45\sp_lib\dummy_cell_1rw.sp | NMOS_VTG | 12 | MM3 bl_noconn wl Q gnd NMOS_VTG W=135.00n L=50n | transistor_netlist_usage | False | Netlist instance usage proves model names are expected by project SPICE. |
| E:\njust\keyan\SRAM Compiler_V2\OpenRAM-stable\deliverables\sram_layoutgen_step45_clean\technology\freepdk45\sp_lib\dummy_cell_1rw.sp | NMOS_VTG | 13 | MM2 br_noconn wl Q_bar gnd NMOS_VTG W=135.00n L=50n | transistor_netlist_usage | False | Netlist instance usage proves model names are expected by project SPICE. |
| E:\njust\keyan\SRAM Compiler_V2\OpenRAM-stable\deliverables\sram_layoutgen_step45_clean\technology\freepdk45\sp_lib\dummy_cell_2rw.sp | NMOS_VTG | 3 | MM9 RA_to_R_right wl1 br1_noconn gnd NMOS_VTG W=180.0n L=50n m=1 | transistor_netlist_usage | False | Netlist instance usage proves model names are expected by project SPICE. |
| E:\njust\keyan\SRAM Compiler_V2\OpenRAM-stable\deliverables\sram_layoutgen_step45_clean\technology\freepdk45\sp_lib\dummy_cell_2rw.sp | NMOS_VTG | 4 | MM8 RA_to_R_right Q gnd gnd NMOS_VTG W=180.0n L=50n m=1 | transistor_netlist_usage | False | Netlist instance usage proves model names are expected by project SPICE. |
| E:\njust\keyan\SRAM Compiler_V2\OpenRAM-stable\deliverables\sram_layoutgen_step45_clean\technology\freepdk45\sp_lib\dummy_cell_2rw.sp | NMOS_VTG | 5 | MM7 RA_to_R_left Q_bar gnd gnd NMOS_VTG W=180.0n L=50n m=1 | transistor_netlist_usage | False | Netlist instance usage proves model names are expected by project SPICE. |
| E:\njust\keyan\SRAM Compiler_V2\OpenRAM-stable\deliverables\sram_layoutgen_step45_clean\technology\freepdk45\sp_lib\dummy_cell_2rw.sp | NMOS_VTG | 6 | MM6 RA_to_R_left wl1 bl1_noconn gnd NMOS_VTG W=180.0n L=50n m=1 | transistor_netlist_usage | False | Netlist instance usage proves model names are expected by project SPICE. |
| E:\njust\keyan\SRAM Compiler_V2\OpenRAM-stable\deliverables\sram_layoutgen_step45_clean\technology\freepdk45\sp_lib\dummy_cell_2rw.sp | NMOS_VTG | 7 | MM5 Q wl0 bl0_noconn gnd NMOS_VTG W=135.00n L=50n m=1 | transistor_netlist_usage | False | Netlist instance usage proves model names are expected by project SPICE. |
| E:\njust\keyan\SRAM Compiler_V2\OpenRAM-stable\deliverables\sram_layoutgen_step45_clean\technology\freepdk45\sp_lib\dummy_cell_2rw.sp | NMOS_VTG | 8 | MM4 Q_bar wl0 br0_noconn gnd NMOS_VTG W=135.00n L=50n m=1 | transistor_netlist_usage | False | Netlist instance usage proves model names are expected by project SPICE. |
| E:\njust\keyan\SRAM Compiler_V2\OpenRAM-stable\deliverables\sram_layoutgen_step45_clean\technology\freepdk45\sp_lib\dummy_cell_2rw.sp | NMOS_VTG | 9 | MM1 Q Q_bar gnd gnd NMOS_VTG W=205.0n L=50n m=1 | transistor_netlist_usage | False | Netlist instance usage proves model names are expected by project SPICE. |
| E:\njust\keyan\SRAM Compiler_V2\OpenRAM-stable\deliverables\sram_layoutgen_step45_clean\technology\freepdk45\sp_lib\dummy_cell_2rw.sp | NMOS_VTG | 10 | MM0 Q_bar Q gnd gnd NMOS_VTG W=205.0n L=50n m=1 | transistor_netlist_usage | False | Netlist instance usage proves model names are expected by project SPICE. |
| E:\njust\keyan\SRAM Compiler_V2\OpenRAM-stable\deliverables\sram_layoutgen_step45_clean\technology\freepdk45\sp_lib\dummy_cell_2rw.sp | PMOS_VTG | 11 | MM3 Q Q_bar vdd vdd PMOS_VTG W=90n L=50n m=1 | transistor_netlist_usage | False | Netlist instance usage proves model names are expected by project SPICE. |
| E:\njust\keyan\SRAM Compiler_V2\OpenRAM-stable\deliverables\sram_layoutgen_step45_clean\technology\freepdk45\sp_lib\dummy_cell_2rw.sp | PMOS_VTG | 12 | MM2 Q_bar Q vdd vdd PMOS_VTG W=90n L=50n m=1 | transistor_netlist_usage | False | Netlist instance usage proves model names are expected by project SPICE. |
| E:\njust\keyan\SRAM Compiler_V2\OpenRAM-stable\deliverables\sram_layoutgen_step45_clean\technology\freepdk45\sp_lib\replica_cell_1rw.sp | NMOS_VTG | 4 | MM0 vdd Q gnd gnd NMOS_VTG W=205.00n L=50n | transistor_netlist_usage | False | Netlist instance usage proves model names are expected by project SPICE. |
| E:\njust\keyan\SRAM Compiler_V2\OpenRAM-stable\deliverables\sram_layoutgen_step45_clean\technology\freepdk45\sp_lib\replica_cell_1rw.sp | PMOS_VTG | 5 | MM4 vdd Q vdd vdd PMOS_VTG W=90n L=50n | transistor_netlist_usage | False | Netlist instance usage proves model names are expected by project SPICE. |
| E:\njust\keyan\SRAM Compiler_V2\OpenRAM-stable\deliverables\sram_layoutgen_step45_clean\technology\freepdk45\sp_lib\replica_cell_1rw.sp | NMOS_VTG | 8 | MM1 Q vdd gnd gnd NMOS_VTG W=205.00n L=50n | transistor_netlist_usage | False | Netlist instance usage proves model names are expected by project SPICE. |
| E:\njust\keyan\SRAM Compiler_V2\OpenRAM-stable\deliverables\sram_layoutgen_step45_clean\technology\freepdk45\sp_lib\replica_cell_1rw.sp | PMOS_VTG | 9 | MM5 Q vdd vdd vdd PMOS_VTG W=90n L=50n | transistor_netlist_usage | False | Netlist instance usage proves model names are expected by project SPICE. |
| E:\njust\keyan\SRAM Compiler_V2\OpenRAM-stable\deliverables\sram_layoutgen_step45_clean\technology\freepdk45\sp_lib\replica_cell_1rw.sp | NMOS_VTG | 12 | MM3 bl wl Q gnd NMOS_VTG W=135.00n L=50n | transistor_netlist_usage | False | Netlist instance usage proves model names are expected by project SPICE. |
| E:\njust\keyan\SRAM Compiler_V2\OpenRAM-stable\deliverables\sram_layoutgen_step45_clean\technology\freepdk45\sp_lib\replica_cell_1rw.sp | NMOS_VTG | 13 | MM2 br wl vdd gnd NMOS_VTG W=135.00n L=50n | transistor_netlist_usage | False | Netlist instance usage proves model names are expected by project SPICE. |
| E:\njust\keyan\SRAM Compiler_V2\OpenRAM-stable\deliverables\sram_layoutgen_step45_clean\technology\freepdk45\sp_lib\replica_cell_2rw.sp | NMOS_VTG | 3 | MM9 RA_to_R_right wl1 br1 gnd NMOS_VTG W=180.0n L=50n m=1 | transistor_netlist_usage | False | Netlist instance usage proves model names are expected by project SPICE. |
| E:\njust\keyan\SRAM Compiler_V2\OpenRAM-stable\deliverables\sram_layoutgen_step45_clean\technology\freepdk45\sp_lib\replica_cell_2rw.sp | NMOS_VTG | 4 | MM8 RA_to_R_right Q gnd gnd NMOS_VTG W=180.0n L=50n m=1 | transistor_netlist_usage | False | Netlist instance usage proves model names are expected by project SPICE. |
| E:\njust\keyan\SRAM Compiler_V2\OpenRAM-stable\deliverables\sram_layoutgen_step45_clean\technology\freepdk45\sp_lib\replica_cell_2rw.sp | NMOS_VTG | 5 | MM7 RA_to_R_left vdd gnd gnd NMOS_VTG W=180.0n L=50n m=1 | transistor_netlist_usage | False | Netlist instance usage proves model names are expected by project SPICE. |
| E:\njust\keyan\SRAM Compiler_V2\OpenRAM-stable\deliverables\sram_layoutgen_step45_clean\technology\freepdk45\sp_lib\replica_cell_2rw.sp | NMOS_VTG | 6 | MM6 RA_to_R_left wl1 bl1 gnd NMOS_VTG W=180.0n L=50n m=1 | transistor_netlist_usage | False | Netlist instance usage proves model names are expected by project SPICE. |
| E:\njust\keyan\SRAM Compiler_V2\OpenRAM-stable\deliverables\sram_layoutgen_step45_clean\technology\freepdk45\sp_lib\replica_cell_2rw.sp | NMOS_VTG | 7 | MM5 Q wl0 bl0 gnd NMOS_VTG W=135.00n L=50n m=1 | transistor_netlist_usage | False | Netlist instance usage proves model names are expected by project SPICE. |
| E:\njust\keyan\SRAM Compiler_V2\OpenRAM-stable\deliverables\sram_layoutgen_step45_clean\technology\freepdk45\sp_lib\replica_cell_2rw.sp | NMOS_VTG | 8 | MM4 vdd wl0 br0 gnd NMOS_VTG W=135.00n L=50n m=1 | transistor_netlist_usage | False | Netlist instance usage proves model names are expected by project SPICE. |
| E:\njust\keyan\SRAM Compiler_V2\OpenRAM-stable\deliverables\sram_layoutgen_step45_clean\technology\freepdk45\sp_lib\replica_cell_2rw.sp | NMOS_VTG | 9 | MM1 Q vdd gnd gnd NMOS_VTG W=205.0n L=50n m=1 | transistor_netlist_usage | False | Netlist instance usage proves model names are expected by project SPICE. |
| E:\njust\keyan\SRAM Compiler_V2\OpenRAM-stable\deliverables\sram_layoutgen_step45_clean\technology\freepdk45\sp_lib\replica_cell_2rw.sp | NMOS_VTG | 10 | MM0 vdd Q gnd gnd NMOS_VTG W=205.0n L=50n m=1 | transistor_netlist_usage | False | Netlist instance usage proves model names are expected by project SPICE. |
| E:\njust\keyan\SRAM Compiler_V2\OpenRAM-stable\deliverables\sram_layoutgen_step45_clean\technology\freepdk45\sp_lib\replica_cell_2rw.sp | PMOS_VTG | 11 | MM3 Q vdd vdd vdd PMOS_VTG W=90n L=50n m=1 | transistor_netlist_usage | False | Netlist instance usage proves model names are expected by project SPICE. |
| E:\njust\keyan\SRAM Compiler_V2\OpenRAM-stable\deliverables\sram_layoutgen_step45_clean\technology\freepdk45\sp_lib\replica_cell_2rw.sp | PMOS_VTG | 12 | MM2 vdd Q vdd vdd PMOS_VTG W=90n L=50n m=1 | transistor_netlist_usage | False | Netlist instance usage proves model names are expected by project SPICE. |
| E:\njust\keyan\SRAM Compiler_V2\OpenRAM-stable\deliverables\sram_layoutgen_step45_clean\technology\freepdk45\sp_lib\sense_amp.sp | PMOS_VTG | 3 | M_1 dint net_1 vdd vdd pmos_vtg w=540.0n l=50.0n | transistor_netlist_usage | False | Netlist instance usage proves model names are expected by project SPICE. |
| E:\njust\keyan\SRAM Compiler_V2\OpenRAM-stable\deliverables\sram_layoutgen_step45_clean\technology\freepdk45\sp_lib\sense_amp.sp | PMOS_VTG | 4 | M_3 net_1 dint vdd vdd pmos_vtg w=540.0n l=50.0n | transistor_netlist_usage | False | Netlist instance usage proves model names are expected by project SPICE. |
| E:\njust\keyan\SRAM Compiler_V2\OpenRAM-stable\deliverables\sram_layoutgen_step45_clean\technology\freepdk45\sp_lib\sense_amp.sp | NMOS_VTG | 5 | M_2 dint net_1 net_2 gnd nmos_vtg w=270.0n l=50.0n | transistor_netlist_usage | False | Netlist instance usage proves model names are expected by project SPICE. |
| E:\njust\keyan\SRAM Compiler_V2\OpenRAM-stable\deliverables\sram_layoutgen_step45_clean\technology\freepdk45\sp_lib\sense_amp.sp | NMOS_VTG | 6 | M_8 net_1 dint net_2 gnd nmos_vtg w=270.0n l=50.0n | transistor_netlist_usage | False | Netlist instance usage proves model names are expected by project SPICE. |
| E:\njust\keyan\SRAM Compiler_V2\OpenRAM-stable\deliverables\sram_layoutgen_step45_clean\technology\freepdk45\sp_lib\sense_amp.sp | PMOS_VTG | 7 | M_5 bl en dint vdd pmos_vtg w=720.0n l=50.0n | transistor_netlist_usage | False | Netlist instance usage proves model names are expected by project SPICE. |
| E:\njust\keyan\SRAM Compiler_V2\OpenRAM-stable\deliverables\sram_layoutgen_step45_clean\technology\freepdk45\sp_lib\sense_amp.sp | PMOS_VTG | 8 | M_6 br en net_1 vdd pmos_vtg w=720.0n l=50.0n | transistor_netlist_usage | False | Netlist instance usage proves model names are expected by project SPICE. |
| E:\njust\keyan\SRAM Compiler_V2\OpenRAM-stable\deliverables\sram_layoutgen_step45_clean\technology\freepdk45\sp_lib\sense_amp.sp | NMOS_VTG | 9 | M_7 net_2 en gnd gnd nmos_vtg w=270.0n l=50.0n | transistor_netlist_usage | False | Netlist instance usage proves model names are expected by project SPICE. |
| E:\njust\keyan\SRAM Compiler_V2\OpenRAM-stable\deliverables\sram_layoutgen_step45_clean\technology\freepdk45\sp_lib\sense_amp.sp | PMOS_VTG | 11 | M_9 dout_bar dint vdd vdd pmos_vtg w=180.0n l=50.0n | transistor_netlist_usage | False | Netlist instance usage proves model names are expected by project SPICE. |
| E:\njust\keyan\SRAM Compiler_V2\OpenRAM-stable\deliverables\sram_layoutgen_step45_clean\technology\freepdk45\sp_lib\sense_amp.sp | NMOS_VTG | 12 | M_10 dout_bar dint gnd gnd nmos_vtg w=90.0n l=50.0n | transistor_netlist_usage | False | Netlist instance usage proves model names are expected by project SPICE. |
| E:\njust\keyan\SRAM Compiler_V2\OpenRAM-stable\deliverables\sram_layoutgen_step45_clean\technology\freepdk45\sp_lib\sense_amp.sp | PMOS_VTG | 13 | M_11 dout dout_bar vdd vdd pmos_vtg w=540.0n l=50.0n | transistor_netlist_usage | False | Netlist instance usage proves model names are expected by project SPICE. |
| E:\njust\keyan\SRAM Compiler_V2\OpenRAM-stable\deliverables\sram_layoutgen_step45_clean\technology\freepdk45\sp_lib\sense_amp.sp | NMOS_VTG | 14 | M_12 dout dout_bar gnd gnd nmos_vtg w=270.0n l=50.0n | transistor_netlist_usage | False | Netlist instance usage proves model names are expected by project SPICE. |
| E:\njust\keyan\SRAM Compiler_V2\OpenRAM-stable\deliverables\sram_layoutgen_step45_clean\technology\freepdk45\sp_lib\tri_gate.sp | NMOS_VTG | 3 | M_1 net_2 in_inv gnd gnd NMOS_VTG W=180.000000n L=50.000000n | transistor_netlist_usage | False | Netlist instance usage proves model names are expected by project SPICE. |
| E:\njust\keyan\SRAM Compiler_V2\OpenRAM-stable\deliverables\sram_layoutgen_step45_clean\technology\freepdk45\sp_lib\tri_gate.sp | NMOS_VTG | 4 | M_2 out en net_2 gnd NMOS_VTG W=180.000000n L=50.000000n | transistor_netlist_usage | False | Netlist instance usage proves model names are expected by project SPICE. |
| E:\njust\keyan\SRAM Compiler_V2\OpenRAM-stable\deliverables\sram_layoutgen_step45_clean\technology\freepdk45\sp_lib\tri_gate.sp | PMOS_VTG | 5 | M_3 net_3 in_inv vdd vdd PMOS_VTG W=360.000000n L=50.000000n | transistor_netlist_usage | False | Netlist instance usage proves model names are expected by project SPICE. |
| E:\njust\keyan\SRAM Compiler_V2\OpenRAM-stable\deliverables\sram_layoutgen_step45_clean\technology\freepdk45\sp_lib\tri_gate.sp | PMOS_VTG | 6 | M_4 out en_bar net_3 vdd PMOS_VTG W=360.000000n L=50.000000n | transistor_netlist_usage | False | Netlist instance usage proves model names are expected by project SPICE. |
| E:\njust\keyan\SRAM Compiler_V2\OpenRAM-stable\deliverables\sram_layoutgen_step45_clean\technology\freepdk45\sp_lib\tri_gate.sp | PMOS_VTG | 7 | M_5 in_inv in vdd vdd PMOS_VTG W=180.000000n L=50.000000n | transistor_netlist_usage | False | Netlist instance usage proves model names are expected by project SPICE. |
| E:\njust\keyan\SRAM Compiler_V2\OpenRAM-stable\deliverables\sram_layoutgen_step45_clean\technology\freepdk45\sp_lib\tri_gate.sp | NMOS_VTG | 8 | M_6 in_inv in gnd gnd NMOS_VTG W=90.000000n L=50.000000n | transistor_netlist_usage | False | Netlist instance usage proves model names are expected by project SPICE. |
| E:\njust\keyan\SRAM Compiler_V2\OpenRAM-stable\deliverables\sram_layoutgen_step45_clean\technology\freepdk45\sp_lib\write_driver.sp | PMOS_VTG | 4 | minP bl_bar din vdd vdd pmos_vtg w=360.000000n l=50.000000n | transistor_netlist_usage | False | Netlist instance usage proves model names are expected by project SPICE. |
| E:\njust\keyan\SRAM Compiler_V2\OpenRAM-stable\deliverables\sram_layoutgen_step45_clean\technology\freepdk45\sp_lib\write_driver.sp | NMOS_VTG | 5 | minN bl_bar din gnd gnd nmos_vtg w=180.000000n l=50.000000n | transistor_netlist_usage | False | Netlist instance usage proves model names are expected by project SPICE. |
| E:\njust\keyan\SRAM Compiler_V2\OpenRAM-stable\deliverables\sram_layoutgen_step45_clean\technology\freepdk45\sp_lib\write_driver.sp | PMOS_VTG | 6 | moutP en_bar en vdd vdd pmos_vtg w=360.000000n l=50.000000n | transistor_netlist_usage | False | Netlist instance usage proves model names are expected by project SPICE. |
| E:\njust\keyan\SRAM Compiler_V2\OpenRAM-stable\deliverables\sram_layoutgen_step45_clean\technology\freepdk45\sp_lib\write_driver.sp | NMOS_VTG | 7 | moutN en_bar en gnd gnd nmos_vtg w=180.000000n l=50.000000n | transistor_netlist_usage | False | Netlist instance usage proves model names are expected by project SPICE. |
| E:\njust\keyan\SRAM Compiler_V2\OpenRAM-stable\deliverables\sram_layoutgen_step45_clean\technology\freepdk45\sp_lib\write_driver.sp | PMOS_VTG | 10 | mout0P int1 bl_bar vdd vdd pmos_vtg w=360.000000n l=50.000000n | transistor_netlist_usage | False | Netlist instance usage proves model names are expected by project SPICE. |
| E:\njust\keyan\SRAM Compiler_V2\OpenRAM-stable\deliverables\sram_layoutgen_step45_clean\technology\freepdk45\sp_lib\write_driver.sp | PMOS_VTG | 11 | mout0P2 bl en_bar int1 vdd pmos_vtg w=360.000000n l=50.000000n | transistor_netlist_usage | False | Netlist instance usage proves model names are expected by project SPICE. |
| E:\njust\keyan\SRAM Compiler_V2\OpenRAM-stable\deliverables\sram_layoutgen_step45_clean\technology\freepdk45\sp_lib\write_driver.sp | NMOS_VTG | 12 | mout0N bl en int2 gnd nmos_vtg w=180.000000n l=50.000000n | transistor_netlist_usage | False | Netlist instance usage proves model names are expected by project SPICE. |
| E:\njust\keyan\SRAM Compiler_V2\OpenRAM-stable\deliverables\sram_layoutgen_step45_clean\technology\freepdk45\sp_lib\write_driver.sp | NMOS_VTG | 13 | mout0N2 int2 bl_bar gnd gnd nmos_vtg w=180.000000n l=50.000000n | transistor_netlist_usage | False | Netlist instance usage proves model names are expected by project SPICE. |
| E:\njust\keyan\SRAM Compiler_V2\OpenRAM-stable\deliverables\sram_layoutgen_step45_clean\technology\freepdk45\sp_lib\write_driver.sp | PMOS_VTG | 16 | mout1P int3 din vdd vdd pmos_vtg w=360.000000n l=50.000000n | transistor_netlist_usage | False | Netlist instance usage proves model names are expected by project SPICE. |
| E:\njust\keyan\SRAM Compiler_V2\OpenRAM-stable\deliverables\sram_layoutgen_step45_clean\technology\freepdk45\sp_lib\write_driver.sp | PMOS_VTG | 17 | mout1P2 br en_bar int3 vdd pmos_vtg w=360.000000n l=50.000000n | transistor_netlist_usage | False | Netlist instance usage proves model names are expected by project SPICE. |
| E:\njust\keyan\SRAM Compiler_V2\OpenRAM-stable\deliverables\sram_layoutgen_step45_clean\technology\freepdk45\sp_lib\write_driver.sp | NMOS_VTG | 18 | mout1N br en int4 gnd nmos_vtg w=180.000000n l=50.000000n | transistor_netlist_usage | False | Netlist instance usage proves model names are expected by project SPICE. |
| E:\njust\keyan\SRAM Compiler_V2\OpenRAM-stable\deliverables\sram_layoutgen_step45_clean\technology\freepdk45\sp_lib\write_driver.sp | NMOS_VTG | 19 | mout1N2 int4 din gnd gnd nmos_vtg w=180.000000n l=50.000000n | transistor_netlist_usage | False | Netlist instance usage proves model names are expected by project SPICE. |

## Device Model Binding Decision

```json
{
  "has_nmos_vtg_model": true,
  "has_pmos_vtg_model": true,
  "has_generic_nmos_pmos_model": true,
  "has_model_include_file": true,
  "has_lib_corner_file": true,
  "device_model_include_found": true,
  "nmos_vtg_bound": true,
  "pmos_vtg_bound": true,
  "can_bind_openyield_model_names_directly": true,
  "needs_model_alias_mapping": false,
  "needs_teacher_or_pdk_confirmation": false,
  "needs_teacher_or_project_provider": false,
  "preferred_corner_include": "E:\\njust\\keyan\\SRAM Compiler_V2\\OpenRAM-stable\\technology\\freepdk45\\models\\hspice_nom.include",
  "available_corner_includes": [
    "E:\\njust\\keyan\\SRAM Compiler_V2\\OpenRAM-stable\\technology\\freepdk45\\models\\hspice_nom.include",
    "E:\\njust\\keyan\\SRAM Compiler_V2\\OpenRAM-stable\\technology\\freepdk45\\models\\hspice_ff.include",
    "E:\\njust\\keyan\\SRAM Compiler_V2\\OpenRAM-stable\\technology\\freepdk45\\models\\hspice_ss.include"
  ],
  "direct_model_include_paths": {
    "TT": [
      "E:\\njust\\keyan\\SRAM Compiler_V2\\OpenRAM-stable\\technology\\freepdk45\\models\\tran_models\\models_nom\\PMOS_VTG.inc",
      "E:\\njust\\keyan\\SRAM Compiler_V2\\OpenRAM-stable\\technology\\freepdk45\\models\\tran_models\\models_nom\\NMOS_VTG.inc"
    ],
    "FF": [
      "E:\\njust\\keyan\\SRAM Compiler_V2\\OpenRAM-stable\\technology\\freepdk45\\models\\tran_models\\models_ff\\PMOS_VTG.inc",
      "E:\\njust\\keyan\\SRAM Compiler_V2\\OpenRAM-stable\\technology\\freepdk45\\models\\tran_models\\models_ff\\NMOS_VTG.inc"
    ],
    "SS": [
      "E:\\njust\\keyan\\SRAM Compiler_V2\\OpenRAM-stable\\technology\\freepdk45\\models\\tran_models\\models_ss\\PMOS_VTG.inc",
      "E:\\njust\\keyan\\SRAM Compiler_V2\\OpenRAM-stable\\technology\\freepdk45\\models\\tran_models\\models_ss\\NMOS_VTG.inc"
    ]
  },
  "notes": [
    "OpenRAM FreePDK45 already contains direct NMOS_VTG / PMOS_VTG model definition files.",
    "No alias mapping is needed for the OpenYield Pinv source names.",
    "Simulation is still blocked by missing simulator choice, VDD, PVT selection, and measurement thresholds."
  ]
}
```

## Generated Candidate Files

| path | kind | exists | notes |
| --- | --- | --- | --- |
| E:\njust\keyan\SRAM Compiler_V2\OpenRAM-stable\deliverables\sram_layoutgen_step45_clean\docs\candidate_spice\gen_delay_inv_candidate.sp | candidate_subckt | True | Planning-only inverter leaf. |
| E:\njust\keyan\SRAM Compiler_V2\OpenRAM-stable\deliverables\sram_layoutgen_step45_clean\docs\candidate_spice\delay_chain_symbolic_tb.sp | symbolic_testbench | True | Nine-stage DELAY_CHAIN with four loads per stage. |
| E:\njust\keyan\SRAM Compiler_V2\OpenRAM-stable\deliverables\sram_layoutgen_step45_clean\docs\candidate_spice\delay_chain_measure.inc | measure_template | True | Planning-only .measure placeholders. |
| E:\njust\keyan\SRAM Compiler_V2\OpenRAM-stable\deliverables\sram_layoutgen_step45_clean\docs\candidate_spice\delay_chain_corner_placeholder.inc | corner_placeholder | True | PDK include plus TBD corner placeholders. |
| E:\njust\keyan\SRAM Compiler_V2\OpenRAM-stable\deliverables\sram_layoutgen_step45_clean\docs\candidate_spice\README.md | readme | True | Usage boundary and missing input checklist. |

## gen_delay_inv Candidate SPICE Summary

```json
{
  "subckt_name": "gen_delay_inv",
  "pin_order": [
    "A",
    "Z",
    "vdd",
    "gnd"
  ],
  "transistor_model_names": [
    "PMOS_VTG",
    "NMOS_VTG"
  ],
  "transistor_sizes_from_source": {
    "nmos_width": "0.9e-07",
    "pmos_width": "2.7e-07",
    "length": "0.05e-6"
  },
  "validated_spice": false,
  "timing_proof": false
}
```

## Delay Chain Symbolic Testbench Summary

```json
{
  "stage_count": 9,
  "four_loads_per_stage": true,
  "stage_instances": [
    "dinv0",
    "dinv1",
    "dinv2",
    "dinv3",
    "dinv4",
    "dinv5",
    "dinv6",
    "dinv7",
    "dinv8"
  ],
  "load_policy": "four same-source inverter loads per stage output",
  "placeholder_params": [
    "VDD_VALUE",
    "TEMP_VALUE",
    "RBL_INPUT_SLEW"
  ],
  "validated_spice": false,
  "timing_proof": false
}
```

## Missing Files / Missing Decisions

- Project-specified simulator (ngspice / hspice / spectre) is still unknown.
- Project-specified VDD is still unknown.
- Project-specified PVT corner selection is still unknown.
- Measurement threshold policy is still unknown.

## What Codex Can Do Now

- Search and bind FreePDK45 NMOS_VTG / PMOS_VTG model include files
- Emit candidate gen_delay_inv transistor subckt template
- Emit planning-only DELAY_CHAIN symbolic testbench template
- Emit placeholder measurement and corner include files

## What Needs User / Teacher / Project Provider

- 1. Confirm the intended FreePDK45 model include and simulator syntax
- 2. Project-specified simulator: ngspice / hspice / spectre
- 3. Project-specified VDD
- 4. Project-specified PVT corner
- 5. Measurement threshold policy, e.g. 50% VDD or 10%-90% slew

## Boundary Assertions

```json
{
  "candidate_spice_is_not_validated_spice": true,
  "candidate_testbench_is_not_timing_proof": true,
  "no_simulation_has_been_run": true,
  "standalone_modified": false,
  "routing_modified": false,
  "gds_writer_modified": false
}
```

## Next Recommended Task

- `candidate_spice_syntax_check_or_pvt_corner_definition`