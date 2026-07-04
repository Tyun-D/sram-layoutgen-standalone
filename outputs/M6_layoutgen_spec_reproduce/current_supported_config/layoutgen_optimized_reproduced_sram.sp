* Structural research netlist for layoutgen_optimized_reproduced_sram
* This is generated without OpenRAM compiler code.
* Row decoder/control glue use replacement macro subckt contracts.

.include "/data1/qujh/work/sram_layoutgen_step45_clean/technology/freepdk45/sp_lib/cell_1rw.sp"
.include "/data1/qujh/work/sram_layoutgen_step45_clean/technology/freepdk45/sp_lib/dff.sp"
.include "/data1/qujh/work/sram_layoutgen_step45_clean/technology/freepdk45/sp_lib/dummy_cell_1rw.sp"
.include "/data1/qujh/work/sram_layoutgen_step45_clean/technology/freepdk45/sp_lib/replica_cell_1rw.sp"
.include "/data1/qujh/work/sram_layoutgen_step45_clean/technology/freepdk45/sp_lib/sense_amp.sp"
.include "/data1/qujh/work/sram_layoutgen_step45_clean/technology/freepdk45/sp_lib/tri_gate.sp"
.include "/data1/qujh/work/sram_layoutgen_step45_clean/technology/freepdk45/sp_lib/write_driver.sp"

.SUBCKT gen_inv A Z vdd gnd
Mp0 Z A vdd vdd PMOS_VTG W=360n L=50n
Mn0 Z A gnd gnd NMOS_VTG W=180n L=50n
.ENDS gen_inv

.SUBCKT gen_nand2 A B Z vdd gnd
Mp0 Z A vdd vdd PMOS_VTG W=360n L=50n
Mp1 Z B vdd vdd PMOS_VTG W=360n L=50n
Mn0 Z A n1 gnd NMOS_VTG W=180n L=50n
Mn1 n1 B gnd gnd NMOS_VTG W=180n L=50n
.ENDS gen_nand2

.SUBCKT gen_nand4 A B C D Z vdd gnd
Mp0 Z A vdd vdd PMOS_VTG W=360n L=50n
Mp1 Z B vdd vdd PMOS_VTG W=360n L=50n
Mp2 Z C vdd vdd PMOS_VTG W=360n L=50n
Mp3 Z D vdd vdd PMOS_VTG W=360n L=50n
Mn0 Z A n1 gnd NMOS_VTG W=180n L=50n
Mn1 n1 B n2 gnd NMOS_VTG W=180n L=50n
Mn2 n2 C n3 gnd NMOS_VTG W=180n L=50n
Mn3 n3 D gnd gnd NMOS_VTG W=180n L=50n
.ENDS gen_nand4

.SUBCKT gen_nor2 A B Z vdd gnd
Mp0 p1 A vdd vdd PMOS_VTG W=360n L=50n
Mp1 Z B p1 vdd PMOS_VTG W=360n L=50n
Mn0 Z A gnd gnd NMOS_VTG W=180n L=50n
Mn1 Z B gnd gnd NMOS_VTG W=180n L=50n
.ENDS gen_nor2

.SUBCKT gen_wl_driver A Z vdd gnd
Xinv0 A Z vdd gnd gen_inv
.ENDS gen_wl_driver

.SUBCKT gen_precharge BL BR EN vdd gnd
Mp_bl BL EN vdd vdd PMOS_VTG W=720n L=50n
Mp_br BR EN vdd vdd PMOS_VTG W=720n L=50n
Mp_eq BL EN BR vdd PMOS_VTG W=360n L=50n
.ENDS gen_precharge

.SUBCKT gen_col_mux BL BR OUT SEL vdd gnd
Mn_bl OUT SEL BL gnd NMOS_VTG W=270n L=50n
Mn_br OUT SEL BR gnd NMOS_VTG W=270n L=50n
.ENDS gen_col_mux

.SUBCKT gen_delay_inv A Z vdd gnd
Xinv0 A Z vdd gnd gen_inv
.ENDS gen_delay_inv

.SUBCKT gen_well_tap vdd gnd
* physical tap cell placeholder for well/substrate contacts
.ENDS gen_well_tap

.SUBCKT layoutgen_optimized_reproduced_sram clk csb web addr[0] addr[1] addr[2] addr[3] addr[4] addr[5] din[0] din[1] din[2] din[3] din[4] din[5] din[6] din[7] dout[0] dout[1] dout[2] dout[3] dout[4] dout[5] dout[6] dout[7] vdd gnd
Xbit_r0_c0 bl[0] br[0] wl[0] vdd gnd cell_1rw
Xbit_r0_c1 bl[1] br[1] wl[0] vdd gnd cell_1rw
Xbit_r0_c2 bl[2] br[2] wl[0] vdd gnd cell_1rw
Xbit_r0_c3 bl[3] br[3] wl[0] vdd gnd cell_1rw
Xbit_r0_c4 bl[4] br[4] wl[0] vdd gnd cell_1rw
Xbit_r0_c5 bl[5] br[5] wl[0] vdd gnd cell_1rw
Xbit_r0_c6 bl[6] br[6] wl[0] vdd gnd cell_1rw
Xbit_r0_c7 bl[7] br[7] wl[0] vdd gnd cell_1rw
Xbit_r0_c8 bl[8] br[8] wl[0] vdd gnd cell_1rw
Xbit_r0_c9 bl[9] br[9] wl[0] vdd gnd cell_1rw
Xbit_r0_c10 bl[10] br[10] wl[0] vdd gnd cell_1rw
Xbit_r0_c11 bl[11] br[11] wl[0] vdd gnd cell_1rw
Xbit_r0_c12 bl[12] br[12] wl[0] vdd gnd cell_1rw
Xbit_r0_c13 bl[13] br[13] wl[0] vdd gnd cell_1rw
Xbit_r0_c14 bl[14] br[14] wl[0] vdd gnd cell_1rw
Xbit_r0_c15 bl[15] br[15] wl[0] vdd gnd cell_1rw
Xbit_r0_c16 bl[16] br[16] wl[0] vdd gnd cell_1rw
Xbit_r0_c17 bl[17] br[17] wl[0] vdd gnd cell_1rw
Xbit_r0_c18 bl[18] br[18] wl[0] vdd gnd cell_1rw
Xbit_r0_c19 bl[19] br[19] wl[0] vdd gnd cell_1rw
Xbit_r0_c20 bl[20] br[20] wl[0] vdd gnd cell_1rw
Xbit_r0_c21 bl[21] br[21] wl[0] vdd gnd cell_1rw
Xbit_r0_c22 bl[22] br[22] wl[0] vdd gnd cell_1rw
Xbit_r0_c23 bl[23] br[23] wl[0] vdd gnd cell_1rw
Xbit_r0_c24 bl[24] br[24] wl[0] vdd gnd cell_1rw
Xbit_r0_c25 bl[25] br[25] wl[0] vdd gnd cell_1rw
Xbit_r0_c26 bl[26] br[26] wl[0] vdd gnd cell_1rw
Xbit_r0_c27 bl[27] br[27] wl[0] vdd gnd cell_1rw
Xbit_r0_c28 bl[28] br[28] wl[0] vdd gnd cell_1rw
Xbit_r0_c29 bl[29] br[29] wl[0] vdd gnd cell_1rw
Xbit_r0_c30 bl[30] br[30] wl[0] vdd gnd cell_1rw
Xbit_r0_c31 bl[31] br[31] wl[0] vdd gnd cell_1rw
Xdummy_l_r0 dummy_bl_l dummy_br_l wl[0] vdd gnd dummy_cell_1rw
Xdummy_r_r0 dummy_bl_r dummy_br_r wl[0] vdd gnd dummy_cell_1rw
Xreplica_r0 rbl rbr replica_wl[0] vdd gnd replica_cell_1rw
Xbit_r1_c0 bl[0] br[0] wl[1] vdd gnd cell_1rw
Xbit_r1_c1 bl[1] br[1] wl[1] vdd gnd cell_1rw
Xbit_r1_c2 bl[2] br[2] wl[1] vdd gnd cell_1rw
Xbit_r1_c3 bl[3] br[3] wl[1] vdd gnd cell_1rw
Xbit_r1_c4 bl[4] br[4] wl[1] vdd gnd cell_1rw
Xbit_r1_c5 bl[5] br[5] wl[1] vdd gnd cell_1rw
Xbit_r1_c6 bl[6] br[6] wl[1] vdd gnd cell_1rw
Xbit_r1_c7 bl[7] br[7] wl[1] vdd gnd cell_1rw
Xbit_r1_c8 bl[8] br[8] wl[1] vdd gnd cell_1rw
Xbit_r1_c9 bl[9] br[9] wl[1] vdd gnd cell_1rw
Xbit_r1_c10 bl[10] br[10] wl[1] vdd gnd cell_1rw
Xbit_r1_c11 bl[11] br[11] wl[1] vdd gnd cell_1rw
Xbit_r1_c12 bl[12] br[12] wl[1] vdd gnd cell_1rw
Xbit_r1_c13 bl[13] br[13] wl[1] vdd gnd cell_1rw
Xbit_r1_c14 bl[14] br[14] wl[1] vdd gnd cell_1rw
Xbit_r1_c15 bl[15] br[15] wl[1] vdd gnd cell_1rw
Xbit_r1_c16 bl[16] br[16] wl[1] vdd gnd cell_1rw
Xbit_r1_c17 bl[17] br[17] wl[1] vdd gnd cell_1rw
Xbit_r1_c18 bl[18] br[18] wl[1] vdd gnd cell_1rw
Xbit_r1_c19 bl[19] br[19] wl[1] vdd gnd cell_1rw
Xbit_r1_c20 bl[20] br[20] wl[1] vdd gnd cell_1rw
Xbit_r1_c21 bl[21] br[21] wl[1] vdd gnd cell_1rw
Xbit_r1_c22 bl[22] br[22] wl[1] vdd gnd cell_1rw
Xbit_r1_c23 bl[23] br[23] wl[1] vdd gnd cell_1rw
Xbit_r1_c24 bl[24] br[24] wl[1] vdd gnd cell_1rw
Xbit_r1_c25 bl[25] br[25] wl[1] vdd gnd cell_1rw
Xbit_r1_c26 bl[26] br[26] wl[1] vdd gnd cell_1rw
Xbit_r1_c27 bl[27] br[27] wl[1] vdd gnd cell_1rw
Xbit_r1_c28 bl[28] br[28] wl[1] vdd gnd cell_1rw
Xbit_r1_c29 bl[29] br[29] wl[1] vdd gnd cell_1rw
Xbit_r1_c30 bl[30] br[30] wl[1] vdd gnd cell_1rw
Xbit_r1_c31 bl[31] br[31] wl[1] vdd gnd cell_1rw
Xdummy_l_r1 dummy_bl_l dummy_br_l wl[1] vdd gnd dummy_cell_1rw
Xdummy_r_r1 dummy_bl_r dummy_br_r wl[1] vdd gnd dummy_cell_1rw
Xreplica_r1 rbl rbr replica_wl[1] vdd gnd replica_cell_1rw
Xbit_r2_c0 bl[0] br[0] wl[2] vdd gnd cell_1rw
Xbit_r2_c1 bl[1] br[1] wl[2] vdd gnd cell_1rw
Xbit_r2_c2 bl[2] br[2] wl[2] vdd gnd cell_1rw
Xbit_r2_c3 bl[3] br[3] wl[2] vdd gnd cell_1rw
Xbit_r2_c4 bl[4] br[4] wl[2] vdd gnd cell_1rw
Xbit_r2_c5 bl[5] br[5] wl[2] vdd gnd cell_1rw
Xbit_r2_c6 bl[6] br[6] wl[2] vdd gnd cell_1rw
Xbit_r2_c7 bl[7] br[7] wl[2] vdd gnd cell_1rw
Xbit_r2_c8 bl[8] br[8] wl[2] vdd gnd cell_1rw
Xbit_r2_c9 bl[9] br[9] wl[2] vdd gnd cell_1rw
Xbit_r2_c10 bl[10] br[10] wl[2] vdd gnd cell_1rw
Xbit_r2_c11 bl[11] br[11] wl[2] vdd gnd cell_1rw
Xbit_r2_c12 bl[12] br[12] wl[2] vdd gnd cell_1rw
Xbit_r2_c13 bl[13] br[13] wl[2] vdd gnd cell_1rw
Xbit_r2_c14 bl[14] br[14] wl[2] vdd gnd cell_1rw
Xbit_r2_c15 bl[15] br[15] wl[2] vdd gnd cell_1rw
Xbit_r2_c16 bl[16] br[16] wl[2] vdd gnd cell_1rw
Xbit_r2_c17 bl[17] br[17] wl[2] vdd gnd cell_1rw
Xbit_r2_c18 bl[18] br[18] wl[2] vdd gnd cell_1rw
Xbit_r2_c19 bl[19] br[19] wl[2] vdd gnd cell_1rw
Xbit_r2_c20 bl[20] br[20] wl[2] vdd gnd cell_1rw
Xbit_r2_c21 bl[21] br[21] wl[2] vdd gnd cell_1rw
Xbit_r2_c22 bl[22] br[22] wl[2] vdd gnd cell_1rw
Xbit_r2_c23 bl[23] br[23] wl[2] vdd gnd cell_1rw
Xbit_r2_c24 bl[24] br[24] wl[2] vdd gnd cell_1rw
Xbit_r2_c25 bl[25] br[25] wl[2] vdd gnd cell_1rw
Xbit_r2_c26 bl[26] br[26] wl[2] vdd gnd cell_1rw
Xbit_r2_c27 bl[27] br[27] wl[2] vdd gnd cell_1rw
Xbit_r2_c28 bl[28] br[28] wl[2] vdd gnd cell_1rw
Xbit_r2_c29 bl[29] br[29] wl[2] vdd gnd cell_1rw
Xbit_r2_c30 bl[30] br[30] wl[2] vdd gnd cell_1rw
Xbit_r2_c31 bl[31] br[31] wl[2] vdd gnd cell_1rw
Xdummy_l_r2 dummy_bl_l dummy_br_l wl[2] vdd gnd dummy_cell_1rw
Xdummy_r_r2 dummy_bl_r dummy_br_r wl[2] vdd gnd dummy_cell_1rw
Xreplica_r2 rbl rbr replica_wl[2] vdd gnd replica_cell_1rw
Xbit_r3_c0 bl[0] br[0] wl[3] vdd gnd cell_1rw
Xbit_r3_c1 bl[1] br[1] wl[3] vdd gnd cell_1rw
Xbit_r3_c2 bl[2] br[2] wl[3] vdd gnd cell_1rw
Xbit_r3_c3 bl[3] br[3] wl[3] vdd gnd cell_1rw
Xbit_r3_c4 bl[4] br[4] wl[3] vdd gnd cell_1rw
Xbit_r3_c5 bl[5] br[5] wl[3] vdd gnd cell_1rw
Xbit_r3_c6 bl[6] br[6] wl[3] vdd gnd cell_1rw
Xbit_r3_c7 bl[7] br[7] wl[3] vdd gnd cell_1rw
Xbit_r3_c8 bl[8] br[8] wl[3] vdd gnd cell_1rw
Xbit_r3_c9 bl[9] br[9] wl[3] vdd gnd cell_1rw
Xbit_r3_c10 bl[10] br[10] wl[3] vdd gnd cell_1rw
Xbit_r3_c11 bl[11] br[11] wl[3] vdd gnd cell_1rw
Xbit_r3_c12 bl[12] br[12] wl[3] vdd gnd cell_1rw
Xbit_r3_c13 bl[13] br[13] wl[3] vdd gnd cell_1rw
Xbit_r3_c14 bl[14] br[14] wl[3] vdd gnd cell_1rw
Xbit_r3_c15 bl[15] br[15] wl[3] vdd gnd cell_1rw
Xbit_r3_c16 bl[16] br[16] wl[3] vdd gnd cell_1rw
Xbit_r3_c17 bl[17] br[17] wl[3] vdd gnd cell_1rw
Xbit_r3_c18 bl[18] br[18] wl[3] vdd gnd cell_1rw
Xbit_r3_c19 bl[19] br[19] wl[3] vdd gnd cell_1rw
Xbit_r3_c20 bl[20] br[20] wl[3] vdd gnd cell_1rw
Xbit_r3_c21 bl[21] br[21] wl[3] vdd gnd cell_1rw
Xbit_r3_c22 bl[22] br[22] wl[3] vdd gnd cell_1rw
Xbit_r3_c23 bl[23] br[23] wl[3] vdd gnd cell_1rw
Xbit_r3_c24 bl[24] br[24] wl[3] vdd gnd cell_1rw
Xbit_r3_c25 bl[25] br[25] wl[3] vdd gnd cell_1rw
Xbit_r3_c26 bl[26] br[26] wl[3] vdd gnd cell_1rw
Xbit_r3_c27 bl[27] br[27] wl[3] vdd gnd cell_1rw
Xbit_r3_c28 bl[28] br[28] wl[3] vdd gnd cell_1rw
Xbit_r3_c29 bl[29] br[29] wl[3] vdd gnd cell_1rw
Xbit_r3_c30 bl[30] br[30] wl[3] vdd gnd cell_1rw
Xbit_r3_c31 bl[31] br[31] wl[3] vdd gnd cell_1rw
Xdummy_l_r3 dummy_bl_l dummy_br_l wl[3] vdd gnd dummy_cell_1rw
Xdummy_r_r3 dummy_bl_r dummy_br_r wl[3] vdd gnd dummy_cell_1rw
Xreplica_r3 rbl rbr replica_wl[3] vdd gnd replica_cell_1rw
Xbit_r4_c0 bl[0] br[0] wl[4] vdd gnd cell_1rw
Xbit_r4_c1 bl[1] br[1] wl[4] vdd gnd cell_1rw
Xbit_r4_c2 bl[2] br[2] wl[4] vdd gnd cell_1rw
Xbit_r4_c3 bl[3] br[3] wl[4] vdd gnd cell_1rw
Xbit_r4_c4 bl[4] br[4] wl[4] vdd gnd cell_1rw
Xbit_r4_c5 bl[5] br[5] wl[4] vdd gnd cell_1rw
Xbit_r4_c6 bl[6] br[6] wl[4] vdd gnd cell_1rw
Xbit_r4_c7 bl[7] br[7] wl[4] vdd gnd cell_1rw
Xbit_r4_c8 bl[8] br[8] wl[4] vdd gnd cell_1rw
Xbit_r4_c9 bl[9] br[9] wl[4] vdd gnd cell_1rw
Xbit_r4_c10 bl[10] br[10] wl[4] vdd gnd cell_1rw
Xbit_r4_c11 bl[11] br[11] wl[4] vdd gnd cell_1rw
Xbit_r4_c12 bl[12] br[12] wl[4] vdd gnd cell_1rw
Xbit_r4_c13 bl[13] br[13] wl[4] vdd gnd cell_1rw
Xbit_r4_c14 bl[14] br[14] wl[4] vdd gnd cell_1rw
Xbit_r4_c15 bl[15] br[15] wl[4] vdd gnd cell_1rw
Xbit_r4_c16 bl[16] br[16] wl[4] vdd gnd cell_1rw
Xbit_r4_c17 bl[17] br[17] wl[4] vdd gnd cell_1rw
Xbit_r4_c18 bl[18] br[18] wl[4] vdd gnd cell_1rw
Xbit_r4_c19 bl[19] br[19] wl[4] vdd gnd cell_1rw
Xbit_r4_c20 bl[20] br[20] wl[4] vdd gnd cell_1rw
Xbit_r4_c21 bl[21] br[21] wl[4] vdd gnd cell_1rw
Xbit_r4_c22 bl[22] br[22] wl[4] vdd gnd cell_1rw
Xbit_r4_c23 bl[23] br[23] wl[4] vdd gnd cell_1rw
Xbit_r4_c24 bl[24] br[24] wl[4] vdd gnd cell_1rw
Xbit_r4_c25 bl[25] br[25] wl[4] vdd gnd cell_1rw
Xbit_r4_c26 bl[26] br[26] wl[4] vdd gnd cell_1rw
Xbit_r4_c27 bl[27] br[27] wl[4] vdd gnd cell_1rw
Xbit_r4_c28 bl[28] br[28] wl[4] vdd gnd cell_1rw
Xbit_r4_c29 bl[29] br[29] wl[4] vdd gnd cell_1rw
Xbit_r4_c30 bl[30] br[30] wl[4] vdd gnd cell_1rw
Xbit_r4_c31 bl[31] br[31] wl[4] vdd gnd cell_1rw
Xdummy_l_r4 dummy_bl_l dummy_br_l wl[4] vdd gnd dummy_cell_1rw
Xdummy_r_r4 dummy_bl_r dummy_br_r wl[4] vdd gnd dummy_cell_1rw
Xreplica_r4 rbl rbr replica_wl[4] vdd gnd replica_cell_1rw
Xbit_r5_c0 bl[0] br[0] wl[5] vdd gnd cell_1rw
Xbit_r5_c1 bl[1] br[1] wl[5] vdd gnd cell_1rw
Xbit_r5_c2 bl[2] br[2] wl[5] vdd gnd cell_1rw
Xbit_r5_c3 bl[3] br[3] wl[5] vdd gnd cell_1rw
Xbit_r5_c4 bl[4] br[4] wl[5] vdd gnd cell_1rw
Xbit_r5_c5 bl[5] br[5] wl[5] vdd gnd cell_1rw
Xbit_r5_c6 bl[6] br[6] wl[5] vdd gnd cell_1rw
Xbit_r5_c7 bl[7] br[7] wl[5] vdd gnd cell_1rw
Xbit_r5_c8 bl[8] br[8] wl[5] vdd gnd cell_1rw
Xbit_r5_c9 bl[9] br[9] wl[5] vdd gnd cell_1rw
Xbit_r5_c10 bl[10] br[10] wl[5] vdd gnd cell_1rw
Xbit_r5_c11 bl[11] br[11] wl[5] vdd gnd cell_1rw
Xbit_r5_c12 bl[12] br[12] wl[5] vdd gnd cell_1rw
Xbit_r5_c13 bl[13] br[13] wl[5] vdd gnd cell_1rw
Xbit_r5_c14 bl[14] br[14] wl[5] vdd gnd cell_1rw
Xbit_r5_c15 bl[15] br[15] wl[5] vdd gnd cell_1rw
Xbit_r5_c16 bl[16] br[16] wl[5] vdd gnd cell_1rw
Xbit_r5_c17 bl[17] br[17] wl[5] vdd gnd cell_1rw
Xbit_r5_c18 bl[18] br[18] wl[5] vdd gnd cell_1rw
Xbit_r5_c19 bl[19] br[19] wl[5] vdd gnd cell_1rw
Xbit_r5_c20 bl[20] br[20] wl[5] vdd gnd cell_1rw
Xbit_r5_c21 bl[21] br[21] wl[5] vdd gnd cell_1rw
Xbit_r5_c22 bl[22] br[22] wl[5] vdd gnd cell_1rw
Xbit_r5_c23 bl[23] br[23] wl[5] vdd gnd cell_1rw
Xbit_r5_c24 bl[24] br[24] wl[5] vdd gnd cell_1rw
Xbit_r5_c25 bl[25] br[25] wl[5] vdd gnd cell_1rw
Xbit_r5_c26 bl[26] br[26] wl[5] vdd gnd cell_1rw
Xbit_r5_c27 bl[27] br[27] wl[5] vdd gnd cell_1rw
Xbit_r5_c28 bl[28] br[28] wl[5] vdd gnd cell_1rw
Xbit_r5_c29 bl[29] br[29] wl[5] vdd gnd cell_1rw
Xbit_r5_c30 bl[30] br[30] wl[5] vdd gnd cell_1rw
Xbit_r5_c31 bl[31] br[31] wl[5] vdd gnd cell_1rw
Xdummy_l_r5 dummy_bl_l dummy_br_l wl[5] vdd gnd dummy_cell_1rw
Xdummy_r_r5 dummy_bl_r dummy_br_r wl[5] vdd gnd dummy_cell_1rw
Xreplica_r5 rbl rbr replica_wl[5] vdd gnd replica_cell_1rw
Xbit_r6_c0 bl[0] br[0] wl[6] vdd gnd cell_1rw
Xbit_r6_c1 bl[1] br[1] wl[6] vdd gnd cell_1rw
Xbit_r6_c2 bl[2] br[2] wl[6] vdd gnd cell_1rw
Xbit_r6_c3 bl[3] br[3] wl[6] vdd gnd cell_1rw
Xbit_r6_c4 bl[4] br[4] wl[6] vdd gnd cell_1rw
Xbit_r6_c5 bl[5] br[5] wl[6] vdd gnd cell_1rw
Xbit_r6_c6 bl[6] br[6] wl[6] vdd gnd cell_1rw
Xbit_r6_c7 bl[7] br[7] wl[6] vdd gnd cell_1rw
Xbit_r6_c8 bl[8] br[8] wl[6] vdd gnd cell_1rw
Xbit_r6_c9 bl[9] br[9] wl[6] vdd gnd cell_1rw
Xbit_r6_c10 bl[10] br[10] wl[6] vdd gnd cell_1rw
Xbit_r6_c11 bl[11] br[11] wl[6] vdd gnd cell_1rw
Xbit_r6_c12 bl[12] br[12] wl[6] vdd gnd cell_1rw
Xbit_r6_c13 bl[13] br[13] wl[6] vdd gnd cell_1rw
Xbit_r6_c14 bl[14] br[14] wl[6] vdd gnd cell_1rw
Xbit_r6_c15 bl[15] br[15] wl[6] vdd gnd cell_1rw
Xbit_r6_c16 bl[16] br[16] wl[6] vdd gnd cell_1rw
Xbit_r6_c17 bl[17] br[17] wl[6] vdd gnd cell_1rw
Xbit_r6_c18 bl[18] br[18] wl[6] vdd gnd cell_1rw
Xbit_r6_c19 bl[19] br[19] wl[6] vdd gnd cell_1rw
Xbit_r6_c20 bl[20] br[20] wl[6] vdd gnd cell_1rw
Xbit_r6_c21 bl[21] br[21] wl[6] vdd gnd cell_1rw
Xbit_r6_c22 bl[22] br[22] wl[6] vdd gnd cell_1rw
Xbit_r6_c23 bl[23] br[23] wl[6] vdd gnd cell_1rw
Xbit_r6_c24 bl[24] br[24] wl[6] vdd gnd cell_1rw
Xbit_r6_c25 bl[25] br[25] wl[6] vdd gnd cell_1rw
Xbit_r6_c26 bl[26] br[26] wl[6] vdd gnd cell_1rw
Xbit_r6_c27 bl[27] br[27] wl[6] vdd gnd cell_1rw
Xbit_r6_c28 bl[28] br[28] wl[6] vdd gnd cell_1rw
Xbit_r6_c29 bl[29] br[29] wl[6] vdd gnd cell_1rw
Xbit_r6_c30 bl[30] br[30] wl[6] vdd gnd cell_1rw
Xbit_r6_c31 bl[31] br[31] wl[6] vdd gnd cell_1rw
Xdummy_l_r6 dummy_bl_l dummy_br_l wl[6] vdd gnd dummy_cell_1rw
Xdummy_r_r6 dummy_bl_r dummy_br_r wl[6] vdd gnd dummy_cell_1rw
Xreplica_r6 rbl rbr replica_wl[6] vdd gnd replica_cell_1rw
Xbit_r7_c0 bl[0] br[0] wl[7] vdd gnd cell_1rw
Xbit_r7_c1 bl[1] br[1] wl[7] vdd gnd cell_1rw
Xbit_r7_c2 bl[2] br[2] wl[7] vdd gnd cell_1rw
Xbit_r7_c3 bl[3] br[3] wl[7] vdd gnd cell_1rw
Xbit_r7_c4 bl[4] br[4] wl[7] vdd gnd cell_1rw
Xbit_r7_c5 bl[5] br[5] wl[7] vdd gnd cell_1rw
Xbit_r7_c6 bl[6] br[6] wl[7] vdd gnd cell_1rw
Xbit_r7_c7 bl[7] br[7] wl[7] vdd gnd cell_1rw
Xbit_r7_c8 bl[8] br[8] wl[7] vdd gnd cell_1rw
Xbit_r7_c9 bl[9] br[9] wl[7] vdd gnd cell_1rw
Xbit_r7_c10 bl[10] br[10] wl[7] vdd gnd cell_1rw
Xbit_r7_c11 bl[11] br[11] wl[7] vdd gnd cell_1rw
Xbit_r7_c12 bl[12] br[12] wl[7] vdd gnd cell_1rw
Xbit_r7_c13 bl[13] br[13] wl[7] vdd gnd cell_1rw
Xbit_r7_c14 bl[14] br[14] wl[7] vdd gnd cell_1rw
Xbit_r7_c15 bl[15] br[15] wl[7] vdd gnd cell_1rw
Xbit_r7_c16 bl[16] br[16] wl[7] vdd gnd cell_1rw
Xbit_r7_c17 bl[17] br[17] wl[7] vdd gnd cell_1rw
Xbit_r7_c18 bl[18] br[18] wl[7] vdd gnd cell_1rw
Xbit_r7_c19 bl[19] br[19] wl[7] vdd gnd cell_1rw
Xbit_r7_c20 bl[20] br[20] wl[7] vdd gnd cell_1rw
Xbit_r7_c21 bl[21] br[21] wl[7] vdd gnd cell_1rw
Xbit_r7_c22 bl[22] br[22] wl[7] vdd gnd cell_1rw
Xbit_r7_c23 bl[23] br[23] wl[7] vdd gnd cell_1rw
Xbit_r7_c24 bl[24] br[24] wl[7] vdd gnd cell_1rw
Xbit_r7_c25 bl[25] br[25] wl[7] vdd gnd cell_1rw
Xbit_r7_c26 bl[26] br[26] wl[7] vdd gnd cell_1rw
Xbit_r7_c27 bl[27] br[27] wl[7] vdd gnd cell_1rw
Xbit_r7_c28 bl[28] br[28] wl[7] vdd gnd cell_1rw
Xbit_r7_c29 bl[29] br[29] wl[7] vdd gnd cell_1rw
Xbit_r7_c30 bl[30] br[30] wl[7] vdd gnd cell_1rw
Xbit_r7_c31 bl[31] br[31] wl[7] vdd gnd cell_1rw
Xdummy_l_r7 dummy_bl_l dummy_br_l wl[7] vdd gnd dummy_cell_1rw
Xdummy_r_r7 dummy_bl_r dummy_br_r wl[7] vdd gnd dummy_cell_1rw
Xreplica_r7 rbl rbr replica_wl[7] vdd gnd replica_cell_1rw
Xbit_r8_c0 bl[0] br[0] wl[8] vdd gnd cell_1rw
Xbit_r8_c1 bl[1] br[1] wl[8] vdd gnd cell_1rw
Xbit_r8_c2 bl[2] br[2] wl[8] vdd gnd cell_1rw
Xbit_r8_c3 bl[3] br[3] wl[8] vdd gnd cell_1rw
Xbit_r8_c4 bl[4] br[4] wl[8] vdd gnd cell_1rw
Xbit_r8_c5 bl[5] br[5] wl[8] vdd gnd cell_1rw
Xbit_r8_c6 bl[6] br[6] wl[8] vdd gnd cell_1rw
Xbit_r8_c7 bl[7] br[7] wl[8] vdd gnd cell_1rw
Xbit_r8_c8 bl[8] br[8] wl[8] vdd gnd cell_1rw
Xbit_r8_c9 bl[9] br[9] wl[8] vdd gnd cell_1rw
Xbit_r8_c10 bl[10] br[10] wl[8] vdd gnd cell_1rw
Xbit_r8_c11 bl[11] br[11] wl[8] vdd gnd cell_1rw
Xbit_r8_c12 bl[12] br[12] wl[8] vdd gnd cell_1rw
Xbit_r8_c13 bl[13] br[13] wl[8] vdd gnd cell_1rw
Xbit_r8_c14 bl[14] br[14] wl[8] vdd gnd cell_1rw
Xbit_r8_c15 bl[15] br[15] wl[8] vdd gnd cell_1rw
Xbit_r8_c16 bl[16] br[16] wl[8] vdd gnd cell_1rw
Xbit_r8_c17 bl[17] br[17] wl[8] vdd gnd cell_1rw
Xbit_r8_c18 bl[18] br[18] wl[8] vdd gnd cell_1rw
Xbit_r8_c19 bl[19] br[19] wl[8] vdd gnd cell_1rw
Xbit_r8_c20 bl[20] br[20] wl[8] vdd gnd cell_1rw
Xbit_r8_c21 bl[21] br[21] wl[8] vdd gnd cell_1rw
Xbit_r8_c22 bl[22] br[22] wl[8] vdd gnd cell_1rw
Xbit_r8_c23 bl[23] br[23] wl[8] vdd gnd cell_1rw
Xbit_r8_c24 bl[24] br[24] wl[8] vdd gnd cell_1rw
Xbit_r8_c25 bl[25] br[25] wl[8] vdd gnd cell_1rw
Xbit_r8_c26 bl[26] br[26] wl[8] vdd gnd cell_1rw
Xbit_r8_c27 bl[27] br[27] wl[8] vdd gnd cell_1rw
Xbit_r8_c28 bl[28] br[28] wl[8] vdd gnd cell_1rw
Xbit_r8_c29 bl[29] br[29] wl[8] vdd gnd cell_1rw
Xbit_r8_c30 bl[30] br[30] wl[8] vdd gnd cell_1rw
Xbit_r8_c31 bl[31] br[31] wl[8] vdd gnd cell_1rw
Xdummy_l_r8 dummy_bl_l dummy_br_l wl[8] vdd gnd dummy_cell_1rw
Xdummy_r_r8 dummy_bl_r dummy_br_r wl[8] vdd gnd dummy_cell_1rw
Xreplica_r8 rbl rbr replica_wl[8] vdd gnd replica_cell_1rw
Xbit_r9_c0 bl[0] br[0] wl[9] vdd gnd cell_1rw
Xbit_r9_c1 bl[1] br[1] wl[9] vdd gnd cell_1rw
Xbit_r9_c2 bl[2] br[2] wl[9] vdd gnd cell_1rw
Xbit_r9_c3 bl[3] br[3] wl[9] vdd gnd cell_1rw
Xbit_r9_c4 bl[4] br[4] wl[9] vdd gnd cell_1rw
Xbit_r9_c5 bl[5] br[5] wl[9] vdd gnd cell_1rw
Xbit_r9_c6 bl[6] br[6] wl[9] vdd gnd cell_1rw
Xbit_r9_c7 bl[7] br[7] wl[9] vdd gnd cell_1rw
Xbit_r9_c8 bl[8] br[8] wl[9] vdd gnd cell_1rw
Xbit_r9_c9 bl[9] br[9] wl[9] vdd gnd cell_1rw
Xbit_r9_c10 bl[10] br[10] wl[9] vdd gnd cell_1rw
Xbit_r9_c11 bl[11] br[11] wl[9] vdd gnd cell_1rw
Xbit_r9_c12 bl[12] br[12] wl[9] vdd gnd cell_1rw
Xbit_r9_c13 bl[13] br[13] wl[9] vdd gnd cell_1rw
Xbit_r9_c14 bl[14] br[14] wl[9] vdd gnd cell_1rw
Xbit_r9_c15 bl[15] br[15] wl[9] vdd gnd cell_1rw
Xbit_r9_c16 bl[16] br[16] wl[9] vdd gnd cell_1rw
Xbit_r9_c17 bl[17] br[17] wl[9] vdd gnd cell_1rw
Xbit_r9_c18 bl[18] br[18] wl[9] vdd gnd cell_1rw
Xbit_r9_c19 bl[19] br[19] wl[9] vdd gnd cell_1rw
Xbit_r9_c20 bl[20] br[20] wl[9] vdd gnd cell_1rw
Xbit_r9_c21 bl[21] br[21] wl[9] vdd gnd cell_1rw
Xbit_r9_c22 bl[22] br[22] wl[9] vdd gnd cell_1rw
Xbit_r9_c23 bl[23] br[23] wl[9] vdd gnd cell_1rw
Xbit_r9_c24 bl[24] br[24] wl[9] vdd gnd cell_1rw
Xbit_r9_c25 bl[25] br[25] wl[9] vdd gnd cell_1rw
Xbit_r9_c26 bl[26] br[26] wl[9] vdd gnd cell_1rw
Xbit_r9_c27 bl[27] br[27] wl[9] vdd gnd cell_1rw
Xbit_r9_c28 bl[28] br[28] wl[9] vdd gnd cell_1rw
Xbit_r9_c29 bl[29] br[29] wl[9] vdd gnd cell_1rw
Xbit_r9_c30 bl[30] br[30] wl[9] vdd gnd cell_1rw
Xbit_r9_c31 bl[31] br[31] wl[9] vdd gnd cell_1rw
Xdummy_l_r9 dummy_bl_l dummy_br_l wl[9] vdd gnd dummy_cell_1rw
Xdummy_r_r9 dummy_bl_r dummy_br_r wl[9] vdd gnd dummy_cell_1rw
Xreplica_r9 rbl rbr replica_wl[9] vdd gnd replica_cell_1rw
Xbit_r10_c0 bl[0] br[0] wl[10] vdd gnd cell_1rw
Xbit_r10_c1 bl[1] br[1] wl[10] vdd gnd cell_1rw
Xbit_r10_c2 bl[2] br[2] wl[10] vdd gnd cell_1rw
Xbit_r10_c3 bl[3] br[3] wl[10] vdd gnd cell_1rw
Xbit_r10_c4 bl[4] br[4] wl[10] vdd gnd cell_1rw
Xbit_r10_c5 bl[5] br[5] wl[10] vdd gnd cell_1rw
Xbit_r10_c6 bl[6] br[6] wl[10] vdd gnd cell_1rw
Xbit_r10_c7 bl[7] br[7] wl[10] vdd gnd cell_1rw
Xbit_r10_c8 bl[8] br[8] wl[10] vdd gnd cell_1rw
Xbit_r10_c9 bl[9] br[9] wl[10] vdd gnd cell_1rw
Xbit_r10_c10 bl[10] br[10] wl[10] vdd gnd cell_1rw
Xbit_r10_c11 bl[11] br[11] wl[10] vdd gnd cell_1rw
Xbit_r10_c12 bl[12] br[12] wl[10] vdd gnd cell_1rw
Xbit_r10_c13 bl[13] br[13] wl[10] vdd gnd cell_1rw
Xbit_r10_c14 bl[14] br[14] wl[10] vdd gnd cell_1rw
Xbit_r10_c15 bl[15] br[15] wl[10] vdd gnd cell_1rw
Xbit_r10_c16 bl[16] br[16] wl[10] vdd gnd cell_1rw
Xbit_r10_c17 bl[17] br[17] wl[10] vdd gnd cell_1rw
Xbit_r10_c18 bl[18] br[18] wl[10] vdd gnd cell_1rw
Xbit_r10_c19 bl[19] br[19] wl[10] vdd gnd cell_1rw
Xbit_r10_c20 bl[20] br[20] wl[10] vdd gnd cell_1rw
Xbit_r10_c21 bl[21] br[21] wl[10] vdd gnd cell_1rw
Xbit_r10_c22 bl[22] br[22] wl[10] vdd gnd cell_1rw
Xbit_r10_c23 bl[23] br[23] wl[10] vdd gnd cell_1rw
Xbit_r10_c24 bl[24] br[24] wl[10] vdd gnd cell_1rw
Xbit_r10_c25 bl[25] br[25] wl[10] vdd gnd cell_1rw
Xbit_r10_c26 bl[26] br[26] wl[10] vdd gnd cell_1rw
Xbit_r10_c27 bl[27] br[27] wl[10] vdd gnd cell_1rw
Xbit_r10_c28 bl[28] br[28] wl[10] vdd gnd cell_1rw
Xbit_r10_c29 bl[29] br[29] wl[10] vdd gnd cell_1rw
Xbit_r10_c30 bl[30] br[30] wl[10] vdd gnd cell_1rw
Xbit_r10_c31 bl[31] br[31] wl[10] vdd gnd cell_1rw
Xdummy_l_r10 dummy_bl_l dummy_br_l wl[10] vdd gnd dummy_cell_1rw
Xdummy_r_r10 dummy_bl_r dummy_br_r wl[10] vdd gnd dummy_cell_1rw
Xreplica_r10 rbl rbr replica_wl[10] vdd gnd replica_cell_1rw
Xbit_r11_c0 bl[0] br[0] wl[11] vdd gnd cell_1rw
Xbit_r11_c1 bl[1] br[1] wl[11] vdd gnd cell_1rw
Xbit_r11_c2 bl[2] br[2] wl[11] vdd gnd cell_1rw
Xbit_r11_c3 bl[3] br[3] wl[11] vdd gnd cell_1rw
Xbit_r11_c4 bl[4] br[4] wl[11] vdd gnd cell_1rw
Xbit_r11_c5 bl[5] br[5] wl[11] vdd gnd cell_1rw
Xbit_r11_c6 bl[6] br[6] wl[11] vdd gnd cell_1rw
Xbit_r11_c7 bl[7] br[7] wl[11] vdd gnd cell_1rw
Xbit_r11_c8 bl[8] br[8] wl[11] vdd gnd cell_1rw
Xbit_r11_c9 bl[9] br[9] wl[11] vdd gnd cell_1rw
Xbit_r11_c10 bl[10] br[10] wl[11] vdd gnd cell_1rw
Xbit_r11_c11 bl[11] br[11] wl[11] vdd gnd cell_1rw
Xbit_r11_c12 bl[12] br[12] wl[11] vdd gnd cell_1rw
Xbit_r11_c13 bl[13] br[13] wl[11] vdd gnd cell_1rw
Xbit_r11_c14 bl[14] br[14] wl[11] vdd gnd cell_1rw
Xbit_r11_c15 bl[15] br[15] wl[11] vdd gnd cell_1rw
Xbit_r11_c16 bl[16] br[16] wl[11] vdd gnd cell_1rw
Xbit_r11_c17 bl[17] br[17] wl[11] vdd gnd cell_1rw
Xbit_r11_c18 bl[18] br[18] wl[11] vdd gnd cell_1rw
Xbit_r11_c19 bl[19] br[19] wl[11] vdd gnd cell_1rw
Xbit_r11_c20 bl[20] br[20] wl[11] vdd gnd cell_1rw
Xbit_r11_c21 bl[21] br[21] wl[11] vdd gnd cell_1rw
Xbit_r11_c22 bl[22] br[22] wl[11] vdd gnd cell_1rw
Xbit_r11_c23 bl[23] br[23] wl[11] vdd gnd cell_1rw
Xbit_r11_c24 bl[24] br[24] wl[11] vdd gnd cell_1rw
Xbit_r11_c25 bl[25] br[25] wl[11] vdd gnd cell_1rw
Xbit_r11_c26 bl[26] br[26] wl[11] vdd gnd cell_1rw
Xbit_r11_c27 bl[27] br[27] wl[11] vdd gnd cell_1rw
Xbit_r11_c28 bl[28] br[28] wl[11] vdd gnd cell_1rw
Xbit_r11_c29 bl[29] br[29] wl[11] vdd gnd cell_1rw
Xbit_r11_c30 bl[30] br[30] wl[11] vdd gnd cell_1rw
Xbit_r11_c31 bl[31] br[31] wl[11] vdd gnd cell_1rw
Xdummy_l_r11 dummy_bl_l dummy_br_l wl[11] vdd gnd dummy_cell_1rw
Xdummy_r_r11 dummy_bl_r dummy_br_r wl[11] vdd gnd dummy_cell_1rw
Xreplica_r11 rbl rbr replica_wl[11] vdd gnd replica_cell_1rw
Xbit_r12_c0 bl[0] br[0] wl[12] vdd gnd cell_1rw
Xbit_r12_c1 bl[1] br[1] wl[12] vdd gnd cell_1rw
Xbit_r12_c2 bl[2] br[2] wl[12] vdd gnd cell_1rw
Xbit_r12_c3 bl[3] br[3] wl[12] vdd gnd cell_1rw
Xbit_r12_c4 bl[4] br[4] wl[12] vdd gnd cell_1rw
Xbit_r12_c5 bl[5] br[5] wl[12] vdd gnd cell_1rw
Xbit_r12_c6 bl[6] br[6] wl[12] vdd gnd cell_1rw
Xbit_r12_c7 bl[7] br[7] wl[12] vdd gnd cell_1rw
Xbit_r12_c8 bl[8] br[8] wl[12] vdd gnd cell_1rw
Xbit_r12_c9 bl[9] br[9] wl[12] vdd gnd cell_1rw
Xbit_r12_c10 bl[10] br[10] wl[12] vdd gnd cell_1rw
Xbit_r12_c11 bl[11] br[11] wl[12] vdd gnd cell_1rw
Xbit_r12_c12 bl[12] br[12] wl[12] vdd gnd cell_1rw
Xbit_r12_c13 bl[13] br[13] wl[12] vdd gnd cell_1rw
Xbit_r12_c14 bl[14] br[14] wl[12] vdd gnd cell_1rw
Xbit_r12_c15 bl[15] br[15] wl[12] vdd gnd cell_1rw
Xbit_r12_c16 bl[16] br[16] wl[12] vdd gnd cell_1rw
Xbit_r12_c17 bl[17] br[17] wl[12] vdd gnd cell_1rw
Xbit_r12_c18 bl[18] br[18] wl[12] vdd gnd cell_1rw
Xbit_r12_c19 bl[19] br[19] wl[12] vdd gnd cell_1rw
Xbit_r12_c20 bl[20] br[20] wl[12] vdd gnd cell_1rw
Xbit_r12_c21 bl[21] br[21] wl[12] vdd gnd cell_1rw
Xbit_r12_c22 bl[22] br[22] wl[12] vdd gnd cell_1rw
Xbit_r12_c23 bl[23] br[23] wl[12] vdd gnd cell_1rw
Xbit_r12_c24 bl[24] br[24] wl[12] vdd gnd cell_1rw
Xbit_r12_c25 bl[25] br[25] wl[12] vdd gnd cell_1rw
Xbit_r12_c26 bl[26] br[26] wl[12] vdd gnd cell_1rw
Xbit_r12_c27 bl[27] br[27] wl[12] vdd gnd cell_1rw
Xbit_r12_c28 bl[28] br[28] wl[12] vdd gnd cell_1rw
Xbit_r12_c29 bl[29] br[29] wl[12] vdd gnd cell_1rw
Xbit_r12_c30 bl[30] br[30] wl[12] vdd gnd cell_1rw
Xbit_r12_c31 bl[31] br[31] wl[12] vdd gnd cell_1rw
Xdummy_l_r12 dummy_bl_l dummy_br_l wl[12] vdd gnd dummy_cell_1rw
Xdummy_r_r12 dummy_bl_r dummy_br_r wl[12] vdd gnd dummy_cell_1rw
Xreplica_r12 rbl rbr replica_wl[12] vdd gnd replica_cell_1rw
Xbit_r13_c0 bl[0] br[0] wl[13] vdd gnd cell_1rw
Xbit_r13_c1 bl[1] br[1] wl[13] vdd gnd cell_1rw
Xbit_r13_c2 bl[2] br[2] wl[13] vdd gnd cell_1rw
Xbit_r13_c3 bl[3] br[3] wl[13] vdd gnd cell_1rw
Xbit_r13_c4 bl[4] br[4] wl[13] vdd gnd cell_1rw
Xbit_r13_c5 bl[5] br[5] wl[13] vdd gnd cell_1rw
Xbit_r13_c6 bl[6] br[6] wl[13] vdd gnd cell_1rw
Xbit_r13_c7 bl[7] br[7] wl[13] vdd gnd cell_1rw
Xbit_r13_c8 bl[8] br[8] wl[13] vdd gnd cell_1rw
Xbit_r13_c9 bl[9] br[9] wl[13] vdd gnd cell_1rw
Xbit_r13_c10 bl[10] br[10] wl[13] vdd gnd cell_1rw
Xbit_r13_c11 bl[11] br[11] wl[13] vdd gnd cell_1rw
Xbit_r13_c12 bl[12] br[12] wl[13] vdd gnd cell_1rw
Xbit_r13_c13 bl[13] br[13] wl[13] vdd gnd cell_1rw
Xbit_r13_c14 bl[14] br[14] wl[13] vdd gnd cell_1rw
Xbit_r13_c15 bl[15] br[15] wl[13] vdd gnd cell_1rw
Xbit_r13_c16 bl[16] br[16] wl[13] vdd gnd cell_1rw
Xbit_r13_c17 bl[17] br[17] wl[13] vdd gnd cell_1rw
Xbit_r13_c18 bl[18] br[18] wl[13] vdd gnd cell_1rw
Xbit_r13_c19 bl[19] br[19] wl[13] vdd gnd cell_1rw
Xbit_r13_c20 bl[20] br[20] wl[13] vdd gnd cell_1rw
Xbit_r13_c21 bl[21] br[21] wl[13] vdd gnd cell_1rw
Xbit_r13_c22 bl[22] br[22] wl[13] vdd gnd cell_1rw
Xbit_r13_c23 bl[23] br[23] wl[13] vdd gnd cell_1rw
Xbit_r13_c24 bl[24] br[24] wl[13] vdd gnd cell_1rw
Xbit_r13_c25 bl[25] br[25] wl[13] vdd gnd cell_1rw
Xbit_r13_c26 bl[26] br[26] wl[13] vdd gnd cell_1rw
Xbit_r13_c27 bl[27] br[27] wl[13] vdd gnd cell_1rw
Xbit_r13_c28 bl[28] br[28] wl[13] vdd gnd cell_1rw
Xbit_r13_c29 bl[29] br[29] wl[13] vdd gnd cell_1rw
Xbit_r13_c30 bl[30] br[30] wl[13] vdd gnd cell_1rw
Xbit_r13_c31 bl[31] br[31] wl[13] vdd gnd cell_1rw
Xdummy_l_r13 dummy_bl_l dummy_br_l wl[13] vdd gnd dummy_cell_1rw
Xdummy_r_r13 dummy_bl_r dummy_br_r wl[13] vdd gnd dummy_cell_1rw
Xreplica_r13 rbl rbr replica_wl[13] vdd gnd replica_cell_1rw
Xbit_r14_c0 bl[0] br[0] wl[14] vdd gnd cell_1rw
Xbit_r14_c1 bl[1] br[1] wl[14] vdd gnd cell_1rw
Xbit_r14_c2 bl[2] br[2] wl[14] vdd gnd cell_1rw
Xbit_r14_c3 bl[3] br[3] wl[14] vdd gnd cell_1rw
Xbit_r14_c4 bl[4] br[4] wl[14] vdd gnd cell_1rw
Xbit_r14_c5 bl[5] br[5] wl[14] vdd gnd cell_1rw
Xbit_r14_c6 bl[6] br[6] wl[14] vdd gnd cell_1rw
Xbit_r14_c7 bl[7] br[7] wl[14] vdd gnd cell_1rw
Xbit_r14_c8 bl[8] br[8] wl[14] vdd gnd cell_1rw
Xbit_r14_c9 bl[9] br[9] wl[14] vdd gnd cell_1rw
Xbit_r14_c10 bl[10] br[10] wl[14] vdd gnd cell_1rw
Xbit_r14_c11 bl[11] br[11] wl[14] vdd gnd cell_1rw
Xbit_r14_c12 bl[12] br[12] wl[14] vdd gnd cell_1rw
Xbit_r14_c13 bl[13] br[13] wl[14] vdd gnd cell_1rw
Xbit_r14_c14 bl[14] br[14] wl[14] vdd gnd cell_1rw
Xbit_r14_c15 bl[15] br[15] wl[14] vdd gnd cell_1rw
Xbit_r14_c16 bl[16] br[16] wl[14] vdd gnd cell_1rw
Xbit_r14_c17 bl[17] br[17] wl[14] vdd gnd cell_1rw
Xbit_r14_c18 bl[18] br[18] wl[14] vdd gnd cell_1rw
Xbit_r14_c19 bl[19] br[19] wl[14] vdd gnd cell_1rw
Xbit_r14_c20 bl[20] br[20] wl[14] vdd gnd cell_1rw
Xbit_r14_c21 bl[21] br[21] wl[14] vdd gnd cell_1rw
Xbit_r14_c22 bl[22] br[22] wl[14] vdd gnd cell_1rw
Xbit_r14_c23 bl[23] br[23] wl[14] vdd gnd cell_1rw
Xbit_r14_c24 bl[24] br[24] wl[14] vdd gnd cell_1rw
Xbit_r14_c25 bl[25] br[25] wl[14] vdd gnd cell_1rw
Xbit_r14_c26 bl[26] br[26] wl[14] vdd gnd cell_1rw
Xbit_r14_c27 bl[27] br[27] wl[14] vdd gnd cell_1rw
Xbit_r14_c28 bl[28] br[28] wl[14] vdd gnd cell_1rw
Xbit_r14_c29 bl[29] br[29] wl[14] vdd gnd cell_1rw
Xbit_r14_c30 bl[30] br[30] wl[14] vdd gnd cell_1rw
Xbit_r14_c31 bl[31] br[31] wl[14] vdd gnd cell_1rw
Xdummy_l_r14 dummy_bl_l dummy_br_l wl[14] vdd gnd dummy_cell_1rw
Xdummy_r_r14 dummy_bl_r dummy_br_r wl[14] vdd gnd dummy_cell_1rw
Xreplica_r14 rbl rbr replica_wl[14] vdd gnd replica_cell_1rw
Xbit_r15_c0 bl[0] br[0] wl[15] vdd gnd cell_1rw
Xbit_r15_c1 bl[1] br[1] wl[15] vdd gnd cell_1rw
Xbit_r15_c2 bl[2] br[2] wl[15] vdd gnd cell_1rw
Xbit_r15_c3 bl[3] br[3] wl[15] vdd gnd cell_1rw
Xbit_r15_c4 bl[4] br[4] wl[15] vdd gnd cell_1rw
Xbit_r15_c5 bl[5] br[5] wl[15] vdd gnd cell_1rw
Xbit_r15_c6 bl[6] br[6] wl[15] vdd gnd cell_1rw
Xbit_r15_c7 bl[7] br[7] wl[15] vdd gnd cell_1rw
Xbit_r15_c8 bl[8] br[8] wl[15] vdd gnd cell_1rw
Xbit_r15_c9 bl[9] br[9] wl[15] vdd gnd cell_1rw
Xbit_r15_c10 bl[10] br[10] wl[15] vdd gnd cell_1rw
Xbit_r15_c11 bl[11] br[11] wl[15] vdd gnd cell_1rw
Xbit_r15_c12 bl[12] br[12] wl[15] vdd gnd cell_1rw
Xbit_r15_c13 bl[13] br[13] wl[15] vdd gnd cell_1rw
Xbit_r15_c14 bl[14] br[14] wl[15] vdd gnd cell_1rw
Xbit_r15_c15 bl[15] br[15] wl[15] vdd gnd cell_1rw
Xbit_r15_c16 bl[16] br[16] wl[15] vdd gnd cell_1rw
Xbit_r15_c17 bl[17] br[17] wl[15] vdd gnd cell_1rw
Xbit_r15_c18 bl[18] br[18] wl[15] vdd gnd cell_1rw
Xbit_r15_c19 bl[19] br[19] wl[15] vdd gnd cell_1rw
Xbit_r15_c20 bl[20] br[20] wl[15] vdd gnd cell_1rw
Xbit_r15_c21 bl[21] br[21] wl[15] vdd gnd cell_1rw
Xbit_r15_c22 bl[22] br[22] wl[15] vdd gnd cell_1rw
Xbit_r15_c23 bl[23] br[23] wl[15] vdd gnd cell_1rw
Xbit_r15_c24 bl[24] br[24] wl[15] vdd gnd cell_1rw
Xbit_r15_c25 bl[25] br[25] wl[15] vdd gnd cell_1rw
Xbit_r15_c26 bl[26] br[26] wl[15] vdd gnd cell_1rw
Xbit_r15_c27 bl[27] br[27] wl[15] vdd gnd cell_1rw
Xbit_r15_c28 bl[28] br[28] wl[15] vdd gnd cell_1rw
Xbit_r15_c29 bl[29] br[29] wl[15] vdd gnd cell_1rw
Xbit_r15_c30 bl[30] br[30] wl[15] vdd gnd cell_1rw
Xbit_r15_c31 bl[31] br[31] wl[15] vdd gnd cell_1rw
Xdummy_l_r15 dummy_bl_l dummy_br_l wl[15] vdd gnd dummy_cell_1rw
Xdummy_r_r15 dummy_bl_r dummy_br_r wl[15] vdd gnd dummy_cell_1rw
Xreplica_r15 rbl rbr replica_wl[15] vdd gnd replica_cell_1rw
Xcoladdr_inv_0 addr[0] col_addr_b[0] vdd gnd gen_inv
Xcoladdr_inv_1 addr[1] col_addr_b[1] vdd gnd gen_inv
Xrowaddr_inv_0 addr[2] row_addr_b[0] vdd gnd gen_inv
Xrowaddr_inv_1 addr[3] row_addr_b[1] vdd gnd gen_inv
Xrowaddr_inv_2 addr[4] row_addr_b[2] vdd gnd gen_inv
Xrowaddr_inv_3 addr[5] row_addr_b[3] vdd gnd gen_inv
Xcolsel_0 col_addr_b[0] col_addr_b[1] col_sel[0] vdd gnd gen_nand2
Xcolsel_1 addr[0] col_addr_b[1] col_sel[1] vdd gnd gen_nand2
Xcolsel_2 col_addr_b[0] addr[1] col_sel[2] vdd gnd gen_nand2
Xcolsel_3 addr[0] addr[1] col_sel[3] vdd gnd gen_nand2
Xprecharge_0 bl[0] br[0] pchg_en vdd gnd gen_precharge
Xcolmux_0 bl[0] br[0] mux_d[0] col_sel[0] vdd gnd gen_col_mux
Xprecharge_1 bl[1] br[1] pchg_en vdd gnd gen_precharge
Xcolmux_1 bl[1] br[1] mux_d[0] col_sel[1] vdd gnd gen_col_mux
Xprecharge_2 bl[2] br[2] pchg_en vdd gnd gen_precharge
Xcolmux_2 bl[2] br[2] mux_d[0] col_sel[2] vdd gnd gen_col_mux
Xprecharge_3 bl[3] br[3] pchg_en vdd gnd gen_precharge
Xcolmux_3 bl[3] br[3] mux_d[0] col_sel[3] vdd gnd gen_col_mux
Xprecharge_4 bl[4] br[4] pchg_en vdd gnd gen_precharge
Xcolmux_4 bl[4] br[4] mux_d[1] col_sel[0] vdd gnd gen_col_mux
Xprecharge_5 bl[5] br[5] pchg_en vdd gnd gen_precharge
Xcolmux_5 bl[5] br[5] mux_d[1] col_sel[1] vdd gnd gen_col_mux
Xprecharge_6 bl[6] br[6] pchg_en vdd gnd gen_precharge
Xcolmux_6 bl[6] br[6] mux_d[1] col_sel[2] vdd gnd gen_col_mux
Xprecharge_7 bl[7] br[7] pchg_en vdd gnd gen_precharge
Xcolmux_7 bl[7] br[7] mux_d[1] col_sel[3] vdd gnd gen_col_mux
Xprecharge_8 bl[8] br[8] pchg_en vdd gnd gen_precharge
Xcolmux_8 bl[8] br[8] mux_d[2] col_sel[0] vdd gnd gen_col_mux
Xprecharge_9 bl[9] br[9] pchg_en vdd gnd gen_precharge
Xcolmux_9 bl[9] br[9] mux_d[2] col_sel[1] vdd gnd gen_col_mux
Xprecharge_10 bl[10] br[10] pchg_en vdd gnd gen_precharge
Xcolmux_10 bl[10] br[10] mux_d[2] col_sel[2] vdd gnd gen_col_mux
Xprecharge_11 bl[11] br[11] pchg_en vdd gnd gen_precharge
Xcolmux_11 bl[11] br[11] mux_d[2] col_sel[3] vdd gnd gen_col_mux
Xprecharge_12 bl[12] br[12] pchg_en vdd gnd gen_precharge
Xcolmux_12 bl[12] br[12] mux_d[3] col_sel[0] vdd gnd gen_col_mux
Xprecharge_13 bl[13] br[13] pchg_en vdd gnd gen_precharge
Xcolmux_13 bl[13] br[13] mux_d[3] col_sel[1] vdd gnd gen_col_mux
Xprecharge_14 bl[14] br[14] pchg_en vdd gnd gen_precharge
Xcolmux_14 bl[14] br[14] mux_d[3] col_sel[2] vdd gnd gen_col_mux
Xprecharge_15 bl[15] br[15] pchg_en vdd gnd gen_precharge
Xcolmux_15 bl[15] br[15] mux_d[3] col_sel[3] vdd gnd gen_col_mux
Xprecharge_16 bl[16] br[16] pchg_en vdd gnd gen_precharge
Xcolmux_16 bl[16] br[16] mux_d[4] col_sel[0] vdd gnd gen_col_mux
Xprecharge_17 bl[17] br[17] pchg_en vdd gnd gen_precharge
Xcolmux_17 bl[17] br[17] mux_d[4] col_sel[1] vdd gnd gen_col_mux
Xprecharge_18 bl[18] br[18] pchg_en vdd gnd gen_precharge
Xcolmux_18 bl[18] br[18] mux_d[4] col_sel[2] vdd gnd gen_col_mux
Xprecharge_19 bl[19] br[19] pchg_en vdd gnd gen_precharge
Xcolmux_19 bl[19] br[19] mux_d[4] col_sel[3] vdd gnd gen_col_mux
Xprecharge_20 bl[20] br[20] pchg_en vdd gnd gen_precharge
Xcolmux_20 bl[20] br[20] mux_d[5] col_sel[0] vdd gnd gen_col_mux
Xprecharge_21 bl[21] br[21] pchg_en vdd gnd gen_precharge
Xcolmux_21 bl[21] br[21] mux_d[5] col_sel[1] vdd gnd gen_col_mux
Xprecharge_22 bl[22] br[22] pchg_en vdd gnd gen_precharge
Xcolmux_22 bl[22] br[22] mux_d[5] col_sel[2] vdd gnd gen_col_mux
Xprecharge_23 bl[23] br[23] pchg_en vdd gnd gen_precharge
Xcolmux_23 bl[23] br[23] mux_d[5] col_sel[3] vdd gnd gen_col_mux
Xprecharge_24 bl[24] br[24] pchg_en vdd gnd gen_precharge
Xcolmux_24 bl[24] br[24] mux_d[6] col_sel[0] vdd gnd gen_col_mux
Xprecharge_25 bl[25] br[25] pchg_en vdd gnd gen_precharge
Xcolmux_25 bl[25] br[25] mux_d[6] col_sel[1] vdd gnd gen_col_mux
Xprecharge_26 bl[26] br[26] pchg_en vdd gnd gen_precharge
Xcolmux_26 bl[26] br[26] mux_d[6] col_sel[2] vdd gnd gen_col_mux
Xprecharge_27 bl[27] br[27] pchg_en vdd gnd gen_precharge
Xcolmux_27 bl[27] br[27] mux_d[6] col_sel[3] vdd gnd gen_col_mux
Xprecharge_28 bl[28] br[28] pchg_en vdd gnd gen_precharge
Xcolmux_28 bl[28] br[28] mux_d[7] col_sel[0] vdd gnd gen_col_mux
Xprecharge_29 bl[29] br[29] pchg_en vdd gnd gen_precharge
Xcolmux_29 bl[29] br[29] mux_d[7] col_sel[1] vdd gnd gen_col_mux
Xprecharge_30 bl[30] br[30] pchg_en vdd gnd gen_precharge
Xcolmux_30 bl[30] br[30] mux_d[7] col_sel[2] vdd gnd gen_col_mux
Xprecharge_31 bl[31] br[31] pchg_en vdd gnd gen_precharge
Xcolmux_31 bl[31] br[31] mux_d[7] col_sel[3] vdd gnd gen_col_mux
Xreplica_precharge rbl rbr pchg_en vdd gnd gen_precharge
Xsense_0 bl[0] br[0] dout_int[0] sense_en vdd gnd sense_amp
Xwrite_0 din[0] bl[0] br[0] write_en vdd gnd write_driver
Xtri_0 dout_int[0] dout[0] tri_en tri_en_bar vdd gnd tri_gate
Xsense_1 bl[4] br[4] dout_int[1] sense_en vdd gnd sense_amp
Xwrite_1 din[1] bl[4] br[4] write_en vdd gnd write_driver
Xtri_1 dout_int[1] dout[1] tri_en tri_en_bar vdd gnd tri_gate
Xsense_2 bl[8] br[8] dout_int[2] sense_en vdd gnd sense_amp
Xwrite_2 din[2] bl[8] br[8] write_en vdd gnd write_driver
Xtri_2 dout_int[2] dout[2] tri_en tri_en_bar vdd gnd tri_gate
Xsense_3 bl[12] br[12] dout_int[3] sense_en vdd gnd sense_amp
Xwrite_3 din[3] bl[12] br[12] write_en vdd gnd write_driver
Xtri_3 dout_int[3] dout[3] tri_en tri_en_bar vdd gnd tri_gate
Xsense_4 bl[16] br[16] dout_int[4] sense_en vdd gnd sense_amp
Xwrite_4 din[4] bl[16] br[16] write_en vdd gnd write_driver
Xtri_4 dout_int[4] dout[4] tri_en tri_en_bar vdd gnd tri_gate
Xsense_5 bl[20] br[20] dout_int[5] sense_en vdd gnd sense_amp
Xwrite_5 din[5] bl[20] br[20] write_en vdd gnd write_driver
Xtri_5 dout_int[5] dout[5] tri_en tri_en_bar vdd gnd tri_gate
Xsense_6 bl[24] br[24] dout_int[6] sense_en vdd gnd sense_amp
Xwrite_6 din[6] bl[24] br[24] write_en vdd gnd write_driver
Xtri_6 dout_int[6] dout[6] tri_en tri_en_bar vdd gnd tri_gate
Xsense_7 bl[28] br[28] dout_int[7] sense_en vdd gnd sense_amp
Xwrite_7 din[7] bl[28] br[28] write_en vdd gnd write_driver
Xtri_7 dout_int[7] dout[7] tri_en tri_en_bar vdd gnd tri_gate
Xdff_data_0 din[0] din_q[0] clk vdd gnd dff
Xdff_data_1 din[1] din_q[1] clk vdd gnd dff
Xdff_data_2 din[2] din_q[2] clk vdd gnd dff
Xdff_data_3 din[3] din_q[3] clk vdd gnd dff
Xdff_data_4 din[4] din_q[4] clk vdd gnd dff
Xdff_data_5 din[5] din_q[5] clk vdd gnd dff
Xdff_data_6 din[6] din_q[6] clk vdd gnd dff
Xdff_data_7 din[7] din_q[7] clk vdd gnd dff
Xdelay_0 clk delay[0] vdd gnd gen_delay_inv
Xdelay_1 delay[0] delay[1] vdd gnd gen_delay_inv
Xdelay_2 delay[1] delay[2] vdd gnd gen_delay_inv
Xdelay_3 delay[2] delay[3] vdd gnd gen_delay_inv
Xdelay_4 delay[3] delay[4] vdd gnd gen_delay_inv
Xdelay_5 delay[4] delay[5] vdd gnd gen_delay_inv
Xdec_nand_0 row_addr_b[0] row_addr_b[1] dec_n[0] vdd gnd gen_nand2
Xwl_driver_0 dec_n[0] wl[0] vdd gnd gen_wl_driver
Xdec_nand_1 addr[2] row_addr_b[1] dec_n[1] vdd gnd gen_nand2
Xwl_driver_1 dec_n[1] wl[1] vdd gnd gen_wl_driver
Xdec_nand_2 row_addr_b[0] addr[3] dec_n[2] vdd gnd gen_nand2
Xwl_driver_2 dec_n[2] wl[2] vdd gnd gen_wl_driver
Xdec_nand_3 addr[2] addr[3] dec_n[3] vdd gnd gen_nand2
Xwl_driver_3 dec_n[3] wl[3] vdd gnd gen_wl_driver
Xdec_nand_4 row_addr_b[0] row_addr_b[1] dec_n[4] vdd gnd gen_nand2
Xwl_driver_4 dec_n[4] wl[4] vdd gnd gen_wl_driver
Xdec_nand_5 addr[2] row_addr_b[1] dec_n[5] vdd gnd gen_nand2
Xwl_driver_5 dec_n[5] wl[5] vdd gnd gen_wl_driver
Xdec_nand_6 row_addr_b[0] addr[3] dec_n[6] vdd gnd gen_nand2
Xwl_driver_6 dec_n[6] wl[6] vdd gnd gen_wl_driver
Xdec_nand_7 addr[2] addr[3] dec_n[7] vdd gnd gen_nand2
Xwl_driver_7 dec_n[7] wl[7] vdd gnd gen_wl_driver
Xdec_nand_8 row_addr_b[0] row_addr_b[1] dec_n[8] vdd gnd gen_nand2
Xwl_driver_8 dec_n[8] wl[8] vdd gnd gen_wl_driver
Xdec_nand_9 addr[2] row_addr_b[1] dec_n[9] vdd gnd gen_nand2
Xwl_driver_9 dec_n[9] wl[9] vdd gnd gen_wl_driver
Xdec_nand_10 row_addr_b[0] addr[3] dec_n[10] vdd gnd gen_nand2
Xwl_driver_10 dec_n[10] wl[10] vdd gnd gen_wl_driver
Xdec_nand_11 addr[2] addr[3] dec_n[11] vdd gnd gen_nand2
Xwl_driver_11 dec_n[11] wl[11] vdd gnd gen_wl_driver
Xdec_nand_12 row_addr_b[0] row_addr_b[1] dec_n[12] vdd gnd gen_nand2
Xwl_driver_12 dec_n[12] wl[12] vdd gnd gen_wl_driver
Xdec_nand_13 addr[2] row_addr_b[1] dec_n[13] vdd gnd gen_nand2
Xwl_driver_13 dec_n[13] wl[13] vdd gnd gen_wl_driver
Xdec_nand_14 row_addr_b[0] addr[3] dec_n[14] vdd gnd gen_nand2
Xwl_driver_14 dec_n[14] wl[14] vdd gnd gen_wl_driver
Xdec_nand_15 addr[2] addr[3] dec_n[15] vdd gnd gen_nand2
Xwl_driver_15 dec_n[15] wl[15] vdd gnd gen_wl_driver
Xctrl_inv_0 ctrl_in[0] ctrl_out[0] vdd gnd gen_inv
Xctrl_nand_1 ctrl_in[1] clk ctrl_out[1] vdd gnd gen_nand2
Xctrl_nand_2 ctrl_in[2] clk ctrl_out[2] vdd gnd gen_nand2
Xctrl_inv_3 ctrl_in[3] ctrl_out[3] vdd gnd gen_inv
* NOTE: generated decoder/control logic is structural and intended for layout integration testing.
* NOTE: matching physical GDS for gen_* macros is a replacement-library task.
.ENDS
