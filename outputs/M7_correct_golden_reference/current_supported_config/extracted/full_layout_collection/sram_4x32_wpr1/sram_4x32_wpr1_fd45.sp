* Structural research netlist for sram_4x32_wpr1_fd45
* This is generated without OpenRAM compiler code.
* Row decoder/control glue use replacement macro subckt contracts.

.include "E:/njust/keyan/SRAM Compiler_V2/OpenRAM-stable/deliverables/sram_layoutgen_standalone/technology/freepdk45/sp_lib/cell_1rw.sp"
.include "E:/njust/keyan/SRAM Compiler_V2/OpenRAM-stable/deliverables/sram_layoutgen_standalone/technology/freepdk45/sp_lib/dff.sp"
.include "E:/njust/keyan/SRAM Compiler_V2/OpenRAM-stable/deliverables/sram_layoutgen_standalone/technology/freepdk45/sp_lib/dummy_cell_1rw.sp"
.include "E:/njust/keyan/SRAM Compiler_V2/OpenRAM-stable/deliverables/sram_layoutgen_standalone/technology/freepdk45/sp_lib/replica_cell_1rw.sp"
.include "E:/njust/keyan/SRAM Compiler_V2/OpenRAM-stable/deliverables/sram_layoutgen_standalone/technology/freepdk45/sp_lib/sense_amp.sp"
.include "E:/njust/keyan/SRAM Compiler_V2/OpenRAM-stable/deliverables/sram_layoutgen_standalone/technology/freepdk45/sp_lib/tri_gate.sp"
.include "E:/njust/keyan/SRAM Compiler_V2/OpenRAM-stable/deliverables/sram_layoutgen_standalone/technology/freepdk45/sp_lib/write_driver.sp"

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

.SUBCKT sram_4x32_wpr1_fd45 clk csb web addr[0] addr[1] addr[2] addr[3] addr[4] din[0] din[1] din[2] din[3] dout[0] dout[1] dout[2] dout[3] vdd gnd
Xbit_r0_c0 bl[0] br[0] wl[0] vdd gnd cell_1rw
Xbit_r0_c1 bl[1] br[1] wl[0] vdd gnd cell_1rw
Xbit_r0_c2 bl[2] br[2] wl[0] vdd gnd cell_1rw
Xbit_r0_c3 bl[3] br[3] wl[0] vdd gnd cell_1rw
Xdummy_l_r0 dummy_bl_l dummy_br_l wl[0] vdd gnd dummy_cell_1rw
Xdummy_r_r0 dummy_bl_r dummy_br_r wl[0] vdd gnd dummy_cell_1rw
Xreplica_r0 rbl rbr replica_wl[0] vdd gnd replica_cell_1rw
Xbit_r1_c0 bl[0] br[0] wl[1] vdd gnd cell_1rw
Xbit_r1_c1 bl[1] br[1] wl[1] vdd gnd cell_1rw
Xbit_r1_c2 bl[2] br[2] wl[1] vdd gnd cell_1rw
Xbit_r1_c3 bl[3] br[3] wl[1] vdd gnd cell_1rw
Xdummy_l_r1 dummy_bl_l dummy_br_l wl[1] vdd gnd dummy_cell_1rw
Xdummy_r_r1 dummy_bl_r dummy_br_r wl[1] vdd gnd dummy_cell_1rw
Xreplica_r1 rbl rbr replica_wl[1] vdd gnd replica_cell_1rw
Xbit_r2_c0 bl[0] br[0] wl[2] vdd gnd cell_1rw
Xbit_r2_c1 bl[1] br[1] wl[2] vdd gnd cell_1rw
Xbit_r2_c2 bl[2] br[2] wl[2] vdd gnd cell_1rw
Xbit_r2_c3 bl[3] br[3] wl[2] vdd gnd cell_1rw
Xdummy_l_r2 dummy_bl_l dummy_br_l wl[2] vdd gnd dummy_cell_1rw
Xdummy_r_r2 dummy_bl_r dummy_br_r wl[2] vdd gnd dummy_cell_1rw
Xreplica_r2 rbl rbr replica_wl[2] vdd gnd replica_cell_1rw
Xbit_r3_c0 bl[0] br[0] wl[3] vdd gnd cell_1rw
Xbit_r3_c1 bl[1] br[1] wl[3] vdd gnd cell_1rw
Xbit_r3_c2 bl[2] br[2] wl[3] vdd gnd cell_1rw
Xbit_r3_c3 bl[3] br[3] wl[3] vdd gnd cell_1rw
Xdummy_l_r3 dummy_bl_l dummy_br_l wl[3] vdd gnd dummy_cell_1rw
Xdummy_r_r3 dummy_bl_r dummy_br_r wl[3] vdd gnd dummy_cell_1rw
Xreplica_r3 rbl rbr replica_wl[3] vdd gnd replica_cell_1rw
Xbit_r4_c0 bl[0] br[0] wl[4] vdd gnd cell_1rw
Xbit_r4_c1 bl[1] br[1] wl[4] vdd gnd cell_1rw
Xbit_r4_c2 bl[2] br[2] wl[4] vdd gnd cell_1rw
Xbit_r4_c3 bl[3] br[3] wl[4] vdd gnd cell_1rw
Xdummy_l_r4 dummy_bl_l dummy_br_l wl[4] vdd gnd dummy_cell_1rw
Xdummy_r_r4 dummy_bl_r dummy_br_r wl[4] vdd gnd dummy_cell_1rw
Xreplica_r4 rbl rbr replica_wl[4] vdd gnd replica_cell_1rw
Xbit_r5_c0 bl[0] br[0] wl[5] vdd gnd cell_1rw
Xbit_r5_c1 bl[1] br[1] wl[5] vdd gnd cell_1rw
Xbit_r5_c2 bl[2] br[2] wl[5] vdd gnd cell_1rw
Xbit_r5_c3 bl[3] br[3] wl[5] vdd gnd cell_1rw
Xdummy_l_r5 dummy_bl_l dummy_br_l wl[5] vdd gnd dummy_cell_1rw
Xdummy_r_r5 dummy_bl_r dummy_br_r wl[5] vdd gnd dummy_cell_1rw
Xreplica_r5 rbl rbr replica_wl[5] vdd gnd replica_cell_1rw
Xbit_r6_c0 bl[0] br[0] wl[6] vdd gnd cell_1rw
Xbit_r6_c1 bl[1] br[1] wl[6] vdd gnd cell_1rw
Xbit_r6_c2 bl[2] br[2] wl[6] vdd gnd cell_1rw
Xbit_r6_c3 bl[3] br[3] wl[6] vdd gnd cell_1rw
Xdummy_l_r6 dummy_bl_l dummy_br_l wl[6] vdd gnd dummy_cell_1rw
Xdummy_r_r6 dummy_bl_r dummy_br_r wl[6] vdd gnd dummy_cell_1rw
Xreplica_r6 rbl rbr replica_wl[6] vdd gnd replica_cell_1rw
Xbit_r7_c0 bl[0] br[0] wl[7] vdd gnd cell_1rw
Xbit_r7_c1 bl[1] br[1] wl[7] vdd gnd cell_1rw
Xbit_r7_c2 bl[2] br[2] wl[7] vdd gnd cell_1rw
Xbit_r7_c3 bl[3] br[3] wl[7] vdd gnd cell_1rw
Xdummy_l_r7 dummy_bl_l dummy_br_l wl[7] vdd gnd dummy_cell_1rw
Xdummy_r_r7 dummy_bl_r dummy_br_r wl[7] vdd gnd dummy_cell_1rw
Xreplica_r7 rbl rbr replica_wl[7] vdd gnd replica_cell_1rw
Xbit_r8_c0 bl[0] br[0] wl[8] vdd gnd cell_1rw
Xbit_r8_c1 bl[1] br[1] wl[8] vdd gnd cell_1rw
Xbit_r8_c2 bl[2] br[2] wl[8] vdd gnd cell_1rw
Xbit_r8_c3 bl[3] br[3] wl[8] vdd gnd cell_1rw
Xdummy_l_r8 dummy_bl_l dummy_br_l wl[8] vdd gnd dummy_cell_1rw
Xdummy_r_r8 dummy_bl_r dummy_br_r wl[8] vdd gnd dummy_cell_1rw
Xreplica_r8 rbl rbr replica_wl[8] vdd gnd replica_cell_1rw
Xbit_r9_c0 bl[0] br[0] wl[9] vdd gnd cell_1rw
Xbit_r9_c1 bl[1] br[1] wl[9] vdd gnd cell_1rw
Xbit_r9_c2 bl[2] br[2] wl[9] vdd gnd cell_1rw
Xbit_r9_c3 bl[3] br[3] wl[9] vdd gnd cell_1rw
Xdummy_l_r9 dummy_bl_l dummy_br_l wl[9] vdd gnd dummy_cell_1rw
Xdummy_r_r9 dummy_bl_r dummy_br_r wl[9] vdd gnd dummy_cell_1rw
Xreplica_r9 rbl rbr replica_wl[9] vdd gnd replica_cell_1rw
Xbit_r10_c0 bl[0] br[0] wl[10] vdd gnd cell_1rw
Xbit_r10_c1 bl[1] br[1] wl[10] vdd gnd cell_1rw
Xbit_r10_c2 bl[2] br[2] wl[10] vdd gnd cell_1rw
Xbit_r10_c3 bl[3] br[3] wl[10] vdd gnd cell_1rw
Xdummy_l_r10 dummy_bl_l dummy_br_l wl[10] vdd gnd dummy_cell_1rw
Xdummy_r_r10 dummy_bl_r dummy_br_r wl[10] vdd gnd dummy_cell_1rw
Xreplica_r10 rbl rbr replica_wl[10] vdd gnd replica_cell_1rw
Xbit_r11_c0 bl[0] br[0] wl[11] vdd gnd cell_1rw
Xbit_r11_c1 bl[1] br[1] wl[11] vdd gnd cell_1rw
Xbit_r11_c2 bl[2] br[2] wl[11] vdd gnd cell_1rw
Xbit_r11_c3 bl[3] br[3] wl[11] vdd gnd cell_1rw
Xdummy_l_r11 dummy_bl_l dummy_br_l wl[11] vdd gnd dummy_cell_1rw
Xdummy_r_r11 dummy_bl_r dummy_br_r wl[11] vdd gnd dummy_cell_1rw
Xreplica_r11 rbl rbr replica_wl[11] vdd gnd replica_cell_1rw
Xbit_r12_c0 bl[0] br[0] wl[12] vdd gnd cell_1rw
Xbit_r12_c1 bl[1] br[1] wl[12] vdd gnd cell_1rw
Xbit_r12_c2 bl[2] br[2] wl[12] vdd gnd cell_1rw
Xbit_r12_c3 bl[3] br[3] wl[12] vdd gnd cell_1rw
Xdummy_l_r12 dummy_bl_l dummy_br_l wl[12] vdd gnd dummy_cell_1rw
Xdummy_r_r12 dummy_bl_r dummy_br_r wl[12] vdd gnd dummy_cell_1rw
Xreplica_r12 rbl rbr replica_wl[12] vdd gnd replica_cell_1rw
Xbit_r13_c0 bl[0] br[0] wl[13] vdd gnd cell_1rw
Xbit_r13_c1 bl[1] br[1] wl[13] vdd gnd cell_1rw
Xbit_r13_c2 bl[2] br[2] wl[13] vdd gnd cell_1rw
Xbit_r13_c3 bl[3] br[3] wl[13] vdd gnd cell_1rw
Xdummy_l_r13 dummy_bl_l dummy_br_l wl[13] vdd gnd dummy_cell_1rw
Xdummy_r_r13 dummy_bl_r dummy_br_r wl[13] vdd gnd dummy_cell_1rw
Xreplica_r13 rbl rbr replica_wl[13] vdd gnd replica_cell_1rw
Xbit_r14_c0 bl[0] br[0] wl[14] vdd gnd cell_1rw
Xbit_r14_c1 bl[1] br[1] wl[14] vdd gnd cell_1rw
Xbit_r14_c2 bl[2] br[2] wl[14] vdd gnd cell_1rw
Xbit_r14_c3 bl[3] br[3] wl[14] vdd gnd cell_1rw
Xdummy_l_r14 dummy_bl_l dummy_br_l wl[14] vdd gnd dummy_cell_1rw
Xdummy_r_r14 dummy_bl_r dummy_br_r wl[14] vdd gnd dummy_cell_1rw
Xreplica_r14 rbl rbr replica_wl[14] vdd gnd replica_cell_1rw
Xbit_r15_c0 bl[0] br[0] wl[15] vdd gnd cell_1rw
Xbit_r15_c1 bl[1] br[1] wl[15] vdd gnd cell_1rw
Xbit_r15_c2 bl[2] br[2] wl[15] vdd gnd cell_1rw
Xbit_r15_c3 bl[3] br[3] wl[15] vdd gnd cell_1rw
Xdummy_l_r15 dummy_bl_l dummy_br_l wl[15] vdd gnd dummy_cell_1rw
Xdummy_r_r15 dummy_bl_r dummy_br_r wl[15] vdd gnd dummy_cell_1rw
Xreplica_r15 rbl rbr replica_wl[15] vdd gnd replica_cell_1rw
Xbit_r16_c0 bl[0] br[0] wl[16] vdd gnd cell_1rw
Xbit_r16_c1 bl[1] br[1] wl[16] vdd gnd cell_1rw
Xbit_r16_c2 bl[2] br[2] wl[16] vdd gnd cell_1rw
Xbit_r16_c3 bl[3] br[3] wl[16] vdd gnd cell_1rw
Xdummy_l_r16 dummy_bl_l dummy_br_l wl[16] vdd gnd dummy_cell_1rw
Xdummy_r_r16 dummy_bl_r dummy_br_r wl[16] vdd gnd dummy_cell_1rw
Xreplica_r16 rbl rbr replica_wl[16] vdd gnd replica_cell_1rw
Xbit_r17_c0 bl[0] br[0] wl[17] vdd gnd cell_1rw
Xbit_r17_c1 bl[1] br[1] wl[17] vdd gnd cell_1rw
Xbit_r17_c2 bl[2] br[2] wl[17] vdd gnd cell_1rw
Xbit_r17_c3 bl[3] br[3] wl[17] vdd gnd cell_1rw
Xdummy_l_r17 dummy_bl_l dummy_br_l wl[17] vdd gnd dummy_cell_1rw
Xdummy_r_r17 dummy_bl_r dummy_br_r wl[17] vdd gnd dummy_cell_1rw
Xreplica_r17 rbl rbr replica_wl[17] vdd gnd replica_cell_1rw
Xbit_r18_c0 bl[0] br[0] wl[18] vdd gnd cell_1rw
Xbit_r18_c1 bl[1] br[1] wl[18] vdd gnd cell_1rw
Xbit_r18_c2 bl[2] br[2] wl[18] vdd gnd cell_1rw
Xbit_r18_c3 bl[3] br[3] wl[18] vdd gnd cell_1rw
Xdummy_l_r18 dummy_bl_l dummy_br_l wl[18] vdd gnd dummy_cell_1rw
Xdummy_r_r18 dummy_bl_r dummy_br_r wl[18] vdd gnd dummy_cell_1rw
Xreplica_r18 rbl rbr replica_wl[18] vdd gnd replica_cell_1rw
Xbit_r19_c0 bl[0] br[0] wl[19] vdd gnd cell_1rw
Xbit_r19_c1 bl[1] br[1] wl[19] vdd gnd cell_1rw
Xbit_r19_c2 bl[2] br[2] wl[19] vdd gnd cell_1rw
Xbit_r19_c3 bl[3] br[3] wl[19] vdd gnd cell_1rw
Xdummy_l_r19 dummy_bl_l dummy_br_l wl[19] vdd gnd dummy_cell_1rw
Xdummy_r_r19 dummy_bl_r dummy_br_r wl[19] vdd gnd dummy_cell_1rw
Xreplica_r19 rbl rbr replica_wl[19] vdd gnd replica_cell_1rw
Xbit_r20_c0 bl[0] br[0] wl[20] vdd gnd cell_1rw
Xbit_r20_c1 bl[1] br[1] wl[20] vdd gnd cell_1rw
Xbit_r20_c2 bl[2] br[2] wl[20] vdd gnd cell_1rw
Xbit_r20_c3 bl[3] br[3] wl[20] vdd gnd cell_1rw
Xdummy_l_r20 dummy_bl_l dummy_br_l wl[20] vdd gnd dummy_cell_1rw
Xdummy_r_r20 dummy_bl_r dummy_br_r wl[20] vdd gnd dummy_cell_1rw
Xreplica_r20 rbl rbr replica_wl[20] vdd gnd replica_cell_1rw
Xbit_r21_c0 bl[0] br[0] wl[21] vdd gnd cell_1rw
Xbit_r21_c1 bl[1] br[1] wl[21] vdd gnd cell_1rw
Xbit_r21_c2 bl[2] br[2] wl[21] vdd gnd cell_1rw
Xbit_r21_c3 bl[3] br[3] wl[21] vdd gnd cell_1rw
Xdummy_l_r21 dummy_bl_l dummy_br_l wl[21] vdd gnd dummy_cell_1rw
Xdummy_r_r21 dummy_bl_r dummy_br_r wl[21] vdd gnd dummy_cell_1rw
Xreplica_r21 rbl rbr replica_wl[21] vdd gnd replica_cell_1rw
Xbit_r22_c0 bl[0] br[0] wl[22] vdd gnd cell_1rw
Xbit_r22_c1 bl[1] br[1] wl[22] vdd gnd cell_1rw
Xbit_r22_c2 bl[2] br[2] wl[22] vdd gnd cell_1rw
Xbit_r22_c3 bl[3] br[3] wl[22] vdd gnd cell_1rw
Xdummy_l_r22 dummy_bl_l dummy_br_l wl[22] vdd gnd dummy_cell_1rw
Xdummy_r_r22 dummy_bl_r dummy_br_r wl[22] vdd gnd dummy_cell_1rw
Xreplica_r22 rbl rbr replica_wl[22] vdd gnd replica_cell_1rw
Xbit_r23_c0 bl[0] br[0] wl[23] vdd gnd cell_1rw
Xbit_r23_c1 bl[1] br[1] wl[23] vdd gnd cell_1rw
Xbit_r23_c2 bl[2] br[2] wl[23] vdd gnd cell_1rw
Xbit_r23_c3 bl[3] br[3] wl[23] vdd gnd cell_1rw
Xdummy_l_r23 dummy_bl_l dummy_br_l wl[23] vdd gnd dummy_cell_1rw
Xdummy_r_r23 dummy_bl_r dummy_br_r wl[23] vdd gnd dummy_cell_1rw
Xreplica_r23 rbl rbr replica_wl[23] vdd gnd replica_cell_1rw
Xbit_r24_c0 bl[0] br[0] wl[24] vdd gnd cell_1rw
Xbit_r24_c1 bl[1] br[1] wl[24] vdd gnd cell_1rw
Xbit_r24_c2 bl[2] br[2] wl[24] vdd gnd cell_1rw
Xbit_r24_c3 bl[3] br[3] wl[24] vdd gnd cell_1rw
Xdummy_l_r24 dummy_bl_l dummy_br_l wl[24] vdd gnd dummy_cell_1rw
Xdummy_r_r24 dummy_bl_r dummy_br_r wl[24] vdd gnd dummy_cell_1rw
Xreplica_r24 rbl rbr replica_wl[24] vdd gnd replica_cell_1rw
Xbit_r25_c0 bl[0] br[0] wl[25] vdd gnd cell_1rw
Xbit_r25_c1 bl[1] br[1] wl[25] vdd gnd cell_1rw
Xbit_r25_c2 bl[2] br[2] wl[25] vdd gnd cell_1rw
Xbit_r25_c3 bl[3] br[3] wl[25] vdd gnd cell_1rw
Xdummy_l_r25 dummy_bl_l dummy_br_l wl[25] vdd gnd dummy_cell_1rw
Xdummy_r_r25 dummy_bl_r dummy_br_r wl[25] vdd gnd dummy_cell_1rw
Xreplica_r25 rbl rbr replica_wl[25] vdd gnd replica_cell_1rw
Xbit_r26_c0 bl[0] br[0] wl[26] vdd gnd cell_1rw
Xbit_r26_c1 bl[1] br[1] wl[26] vdd gnd cell_1rw
Xbit_r26_c2 bl[2] br[2] wl[26] vdd gnd cell_1rw
Xbit_r26_c3 bl[3] br[3] wl[26] vdd gnd cell_1rw
Xdummy_l_r26 dummy_bl_l dummy_br_l wl[26] vdd gnd dummy_cell_1rw
Xdummy_r_r26 dummy_bl_r dummy_br_r wl[26] vdd gnd dummy_cell_1rw
Xreplica_r26 rbl rbr replica_wl[26] vdd gnd replica_cell_1rw
Xbit_r27_c0 bl[0] br[0] wl[27] vdd gnd cell_1rw
Xbit_r27_c1 bl[1] br[1] wl[27] vdd gnd cell_1rw
Xbit_r27_c2 bl[2] br[2] wl[27] vdd gnd cell_1rw
Xbit_r27_c3 bl[3] br[3] wl[27] vdd gnd cell_1rw
Xdummy_l_r27 dummy_bl_l dummy_br_l wl[27] vdd gnd dummy_cell_1rw
Xdummy_r_r27 dummy_bl_r dummy_br_r wl[27] vdd gnd dummy_cell_1rw
Xreplica_r27 rbl rbr replica_wl[27] vdd gnd replica_cell_1rw
Xbit_r28_c0 bl[0] br[0] wl[28] vdd gnd cell_1rw
Xbit_r28_c1 bl[1] br[1] wl[28] vdd gnd cell_1rw
Xbit_r28_c2 bl[2] br[2] wl[28] vdd gnd cell_1rw
Xbit_r28_c3 bl[3] br[3] wl[28] vdd gnd cell_1rw
Xdummy_l_r28 dummy_bl_l dummy_br_l wl[28] vdd gnd dummy_cell_1rw
Xdummy_r_r28 dummy_bl_r dummy_br_r wl[28] vdd gnd dummy_cell_1rw
Xreplica_r28 rbl rbr replica_wl[28] vdd gnd replica_cell_1rw
Xbit_r29_c0 bl[0] br[0] wl[29] vdd gnd cell_1rw
Xbit_r29_c1 bl[1] br[1] wl[29] vdd gnd cell_1rw
Xbit_r29_c2 bl[2] br[2] wl[29] vdd gnd cell_1rw
Xbit_r29_c3 bl[3] br[3] wl[29] vdd gnd cell_1rw
Xdummy_l_r29 dummy_bl_l dummy_br_l wl[29] vdd gnd dummy_cell_1rw
Xdummy_r_r29 dummy_bl_r dummy_br_r wl[29] vdd gnd dummy_cell_1rw
Xreplica_r29 rbl rbr replica_wl[29] vdd gnd replica_cell_1rw
Xbit_r30_c0 bl[0] br[0] wl[30] vdd gnd cell_1rw
Xbit_r30_c1 bl[1] br[1] wl[30] vdd gnd cell_1rw
Xbit_r30_c2 bl[2] br[2] wl[30] vdd gnd cell_1rw
Xbit_r30_c3 bl[3] br[3] wl[30] vdd gnd cell_1rw
Xdummy_l_r30 dummy_bl_l dummy_br_l wl[30] vdd gnd dummy_cell_1rw
Xdummy_r_r30 dummy_bl_r dummy_br_r wl[30] vdd gnd dummy_cell_1rw
Xreplica_r30 rbl rbr replica_wl[30] vdd gnd replica_cell_1rw
Xbit_r31_c0 bl[0] br[0] wl[31] vdd gnd cell_1rw
Xbit_r31_c1 bl[1] br[1] wl[31] vdd gnd cell_1rw
Xbit_r31_c2 bl[2] br[2] wl[31] vdd gnd cell_1rw
Xbit_r31_c3 bl[3] br[3] wl[31] vdd gnd cell_1rw
Xdummy_l_r31 dummy_bl_l dummy_br_l wl[31] vdd gnd dummy_cell_1rw
Xdummy_r_r31 dummy_bl_r dummy_br_r wl[31] vdd gnd dummy_cell_1rw
Xreplica_r31 rbl rbr replica_wl[31] vdd gnd replica_cell_1rw
Xrowaddr_inv_0 addr_q[0] row_addr_b[0] vdd gnd gen_inv
Xrowaddr_inv_1 addr_q[1] row_addr_b[1] vdd gnd gen_inv
Xrowaddr_inv_2 addr_q[2] row_addr_b[2] vdd gnd gen_inv
Xrowaddr_inv_3 addr_q[3] row_addr_b[3] vdd gnd gen_inv
Xrowaddr_inv_4 addr_q[4] row_addr_b[4] vdd gnd gen_inv
Xcolsel_0 csb col_sel[0] vdd gnd gen_inv
Xprecharge_0 bl[0] br[0] pchg_en vdd gnd gen_precharge
Xcolmux_0 bl[0] br[0] mux_d[0] col_sel[0] vdd gnd gen_col_mux
Xprecharge_1 bl[1] br[1] pchg_en vdd gnd gen_precharge
Xcolmux_1 bl[1] br[1] mux_d[1] col_sel[0] vdd gnd gen_col_mux
Xprecharge_2 bl[2] br[2] pchg_en vdd gnd gen_precharge
Xcolmux_2 bl[2] br[2] mux_d[2] col_sel[0] vdd gnd gen_col_mux
Xprecharge_3 bl[3] br[3] pchg_en vdd gnd gen_precharge
Xcolmux_3 bl[3] br[3] mux_d[3] col_sel[0] vdd gnd gen_col_mux
Xreplica_precharge rbl rbr pchg_en vdd gnd gen_precharge
Xsense_0 bl[0] br[0] dout_int[0] sense_en vdd gnd sense_amp
Xwrite_0 din_q[0] bl[0] br[0] write_en vdd gnd write_driver
Xtri_0 dout_int[0] dout[0] tri_en tri_en_bar vdd gnd tri_gate
Xsense_1 bl[1] br[1] dout_int[1] sense_en vdd gnd sense_amp
Xwrite_1 din_q[1] bl[1] br[1] write_en vdd gnd write_driver
Xtri_1 dout_int[1] dout[1] tri_en tri_en_bar vdd gnd tri_gate
Xsense_2 bl[2] br[2] dout_int[2] sense_en vdd gnd sense_amp
Xwrite_2 din_q[2] bl[2] br[2] write_en vdd gnd write_driver
Xtri_2 dout_int[2] dout[2] tri_en tri_en_bar vdd gnd tri_gate
Xsense_3 bl[3] br[3] dout_int[3] sense_en vdd gnd sense_amp
Xwrite_3 din_q[3] bl[3] br[3] write_en vdd gnd write_driver
Xtri_3 dout_int[3] dout[3] tri_en tri_en_bar vdd gnd tri_gate
Xdff_data_0 din[0] din_q[0] clk vdd gnd dff
Xdff_data_1 din[1] din_q[1] clk vdd gnd dff
Xdff_data_2 din[2] din_q[2] clk vdd gnd dff
Xdff_data_3 din[3] din_q[3] clk vdd gnd dff
Xdff_ctrl_0 addr[0] addr_q[0] clk vdd gnd dff
Xdff_ctrl_1 addr[1] addr_q[1] clk vdd gnd dff
Xdff_ctrl_2 addr[2] addr_q[2] clk vdd gnd dff
Xdff_ctrl_3 addr[3] addr_q[3] clk vdd gnd dff
Xdff_ctrl_4 addr[4] addr_q[4] clk vdd gnd dff
Xdff_ctrl_5 web pchg_en clk vdd gnd dff
Xdff_ctrl_6 csb sense_en clk vdd gnd dff
Xdff_ctrl_7 web write_en clk vdd gnd dff
Xdff_ctrl_8 csb tri_en clk vdd gnd dff
Xdelay_0 clk delay[0] vdd gnd gen_delay_inv
Xdelay_1 delay[0] delay[1] vdd gnd gen_delay_inv
Xdelay_2 delay[1] delay[2] vdd gnd gen_delay_inv
Xdelay_3 delay[2] delay[3] vdd gnd gen_delay_inv
Xdelay_4 delay[3] delay[4] vdd gnd gen_delay_inv
Xdelay_5 delay[4] delay[5] vdd gnd gen_delay_inv
Xdec_nand_0 row_addr_b[0] row_addr_b[1] dec_n[0] vdd gnd gen_nand2
Xwl_driver_0 dec_n[0] wl[0] vdd gnd gen_wl_driver
Xdec_nand_1 addr_q[0] row_addr_b[1] dec_n[1] vdd gnd gen_nand2
Xwl_driver_1 dec_n[1] wl[1] vdd gnd gen_wl_driver
Xdec_nand_2 row_addr_b[0] addr_q[1] dec_n[2] vdd gnd gen_nand2
Xwl_driver_2 dec_n[2] wl[2] vdd gnd gen_wl_driver
Xdec_nand_3 addr_q[0] addr_q[1] dec_n[3] vdd gnd gen_nand2
Xwl_driver_3 dec_n[3] wl[3] vdd gnd gen_wl_driver
Xdec_nand_4 row_addr_b[0] row_addr_b[1] dec_n[4] vdd gnd gen_nand2
Xwl_driver_4 dec_n[4] wl[4] vdd gnd gen_wl_driver
Xdec_nand_5 addr_q[0] row_addr_b[1] dec_n[5] vdd gnd gen_nand2
Xwl_driver_5 dec_n[5] wl[5] vdd gnd gen_wl_driver
Xdec_nand_6 row_addr_b[0] addr_q[1] dec_n[6] vdd gnd gen_nand2
Xwl_driver_6 dec_n[6] wl[6] vdd gnd gen_wl_driver
Xdec_nand_7 addr_q[0] addr_q[1] dec_n[7] vdd gnd gen_nand2
Xwl_driver_7 dec_n[7] wl[7] vdd gnd gen_wl_driver
Xdec_nand_8 row_addr_b[0] row_addr_b[1] dec_n[8] vdd gnd gen_nand2
Xwl_driver_8 dec_n[8] wl[8] vdd gnd gen_wl_driver
Xdec_nand_9 addr_q[0] row_addr_b[1] dec_n[9] vdd gnd gen_nand2
Xwl_driver_9 dec_n[9] wl[9] vdd gnd gen_wl_driver
Xdec_nand_10 row_addr_b[0] addr_q[1] dec_n[10] vdd gnd gen_nand2
Xwl_driver_10 dec_n[10] wl[10] vdd gnd gen_wl_driver
Xdec_nand_11 addr_q[0] addr_q[1] dec_n[11] vdd gnd gen_nand2
Xwl_driver_11 dec_n[11] wl[11] vdd gnd gen_wl_driver
Xdec_nand_12 row_addr_b[0] row_addr_b[1] dec_n[12] vdd gnd gen_nand2
Xwl_driver_12 dec_n[12] wl[12] vdd gnd gen_wl_driver
Xdec_nand_13 addr_q[0] row_addr_b[1] dec_n[13] vdd gnd gen_nand2
Xwl_driver_13 dec_n[13] wl[13] vdd gnd gen_wl_driver
Xdec_nand_14 row_addr_b[0] addr_q[1] dec_n[14] vdd gnd gen_nand2
Xwl_driver_14 dec_n[14] wl[14] vdd gnd gen_wl_driver
Xdec_nand_15 addr_q[0] addr_q[1] dec_n[15] vdd gnd gen_nand2
Xwl_driver_15 dec_n[15] wl[15] vdd gnd gen_wl_driver
Xdec_nand_16 row_addr_b[0] row_addr_b[1] dec_n[16] vdd gnd gen_nand2
Xwl_driver_16 dec_n[16] wl[16] vdd gnd gen_wl_driver
Xdec_nand_17 addr_q[0] row_addr_b[1] dec_n[17] vdd gnd gen_nand2
Xwl_driver_17 dec_n[17] wl[17] vdd gnd gen_wl_driver
Xdec_nand_18 row_addr_b[0] addr_q[1] dec_n[18] vdd gnd gen_nand2
Xwl_driver_18 dec_n[18] wl[18] vdd gnd gen_wl_driver
Xdec_nand_19 addr_q[0] addr_q[1] dec_n[19] vdd gnd gen_nand2
Xwl_driver_19 dec_n[19] wl[19] vdd gnd gen_wl_driver
Xdec_nand_20 row_addr_b[0] row_addr_b[1] dec_n[20] vdd gnd gen_nand2
Xwl_driver_20 dec_n[20] wl[20] vdd gnd gen_wl_driver
Xdec_nand_21 addr_q[0] row_addr_b[1] dec_n[21] vdd gnd gen_nand2
Xwl_driver_21 dec_n[21] wl[21] vdd gnd gen_wl_driver
Xdec_nand_22 row_addr_b[0] addr_q[1] dec_n[22] vdd gnd gen_nand2
Xwl_driver_22 dec_n[22] wl[22] vdd gnd gen_wl_driver
Xdec_nand_23 addr_q[0] addr_q[1] dec_n[23] vdd gnd gen_nand2
Xwl_driver_23 dec_n[23] wl[23] vdd gnd gen_wl_driver
Xdec_nand_24 row_addr_b[0] row_addr_b[1] dec_n[24] vdd gnd gen_nand2
Xwl_driver_24 dec_n[24] wl[24] vdd gnd gen_wl_driver
Xdec_nand_25 addr_q[0] row_addr_b[1] dec_n[25] vdd gnd gen_nand2
Xwl_driver_25 dec_n[25] wl[25] vdd gnd gen_wl_driver
Xdec_nand_26 row_addr_b[0] addr_q[1] dec_n[26] vdd gnd gen_nand2
Xwl_driver_26 dec_n[26] wl[26] vdd gnd gen_wl_driver
Xdec_nand_27 addr_q[0] addr_q[1] dec_n[27] vdd gnd gen_nand2
Xwl_driver_27 dec_n[27] wl[27] vdd gnd gen_wl_driver
Xdec_nand_28 row_addr_b[0] row_addr_b[1] dec_n[28] vdd gnd gen_nand2
Xwl_driver_28 dec_n[28] wl[28] vdd gnd gen_wl_driver
Xdec_nand_29 addr_q[0] row_addr_b[1] dec_n[29] vdd gnd gen_nand2
Xwl_driver_29 dec_n[29] wl[29] vdd gnd gen_wl_driver
Xdec_nand_30 row_addr_b[0] addr_q[1] dec_n[30] vdd gnd gen_nand2
Xwl_driver_30 dec_n[30] wl[30] vdd gnd gen_wl_driver
Xdec_nand_31 addr_q[0] addr_q[1] dec_n[31] vdd gnd gen_nand2
Xwl_driver_31 dec_n[31] wl[31] vdd gnd gen_wl_driver
Xctrl_inv_0 ctrl_in[0] ctrl_out[0] vdd gnd gen_inv
Xctrl_nand_1 ctrl_in[1] clk ctrl_out[1] vdd gnd gen_nand2
Xctrl_nand_2 ctrl_in[2] clk ctrl_out[2] vdd gnd gen_nand2
Xctrl_inv_3 ctrl_in[3] ctrl_out[3] vdd gnd gen_inv
* NOTE: generated decoder/control logic is structural and intended for layout integration testing.
* NOTE: matching physical GDS for gen_* macros is a replacement-library task.
.ENDS
