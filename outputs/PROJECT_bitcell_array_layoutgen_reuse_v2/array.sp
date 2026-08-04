*FIRST LINE IS A COMMENT

.SUBCKT dummy_cell_1rw bl br wl vdd gnd
* Inverter 1
MM0 Q_bar Q gnd gnd NMOS_VTG W=205.00n L=50n
MM4 Q_bar Q vdd vdd PMOS_VTG W=90n L=50n

* Inverer 2
MM1 Q Q_bar gnd gnd NMOS_VTG W=205.00n L=50n
MM5 Q Q_bar vdd vdd PMOS_VTG W=90n L=50n

* Access transistors
MM3 bl_noconn wl Q gnd NMOS_VTG W=135.00n L=50n
MM2 br_noconn wl Q_bar gnd NMOS_VTG W=135.00n L=50n
.ENDS dummy_cell_1rw


.SUBCKT sram_dummy_array_0
+ bl_0_0 br_0_0 bl_0_1 br_0_1 bl_0_2 br_0_2 bl_0_3 br_0_3 bl_0_4 br_0_4
+ bl_0_5 br_0_5 bl_0_6 br_0_6 bl_0_7 br_0_7 bl_0_8 br_0_8 bl_0_9 br_0_9
+ bl_0_10 br_0_10 bl_0_11 br_0_11 bl_0_12 br_0_12 bl_0_13 br_0_13
+ bl_0_14 br_0_14 bl_0_15 br_0_15 bl_0_16 br_0_16 wl_0_0 vdd gnd
* INOUT : bl_0_0 
* INOUT : br_0_0 
* INOUT : bl_0_1 
* INOUT : br_0_1 
* INOUT : bl_0_2 
* INOUT : br_0_2 
* INOUT : bl_0_3 
* INOUT : br_0_3 
* INOUT : bl_0_4 
* INOUT : br_0_4 
* INOUT : bl_0_5 
* INOUT : br_0_5 
* INOUT : bl_0_6 
* INOUT : br_0_6 
* INOUT : bl_0_7 
* INOUT : br_0_7 
* INOUT : bl_0_8 
* INOUT : br_0_8 
* INOUT : bl_0_9 
* INOUT : br_0_9 
* INOUT : bl_0_10 
* INOUT : br_0_10 
* INOUT : bl_0_11 
* INOUT : br_0_11 
* INOUT : bl_0_12 
* INOUT : br_0_12 
* INOUT : bl_0_13 
* INOUT : br_0_13 
* INOUT : bl_0_14 
* INOUT : br_0_14 
* INOUT : bl_0_15 
* INOUT : br_0_15 
* INOUT : bl_0_16 
* INOUT : br_0_16 
* INPUT : wl_0_0 
* POWER : vdd 
* GROUND: gnd 
Xbit_r0_c0
+ bl_0_0 br_0_0 wl_0_0 vdd gnd
+ dummy_cell_1rw
Xbit_r0_c1
+ bl_0_1 br_0_1 wl_0_0 vdd gnd
+ dummy_cell_1rw
Xbit_r0_c2
+ bl_0_2 br_0_2 wl_0_0 vdd gnd
+ dummy_cell_1rw
Xbit_r0_c3
+ bl_0_3 br_0_3 wl_0_0 vdd gnd
+ dummy_cell_1rw
Xbit_r0_c4
+ bl_0_4 br_0_4 wl_0_0 vdd gnd
+ dummy_cell_1rw
Xbit_r0_c5
+ bl_0_5 br_0_5 wl_0_0 vdd gnd
+ dummy_cell_1rw
Xbit_r0_c6
+ bl_0_6 br_0_6 wl_0_0 vdd gnd
+ dummy_cell_1rw
Xbit_r0_c7
+ bl_0_7 br_0_7 wl_0_0 vdd gnd
+ dummy_cell_1rw
Xbit_r0_c8
+ bl_0_8 br_0_8 wl_0_0 vdd gnd
+ dummy_cell_1rw
Xbit_r0_c9
+ bl_0_9 br_0_9 wl_0_0 vdd gnd
+ dummy_cell_1rw
Xbit_r0_c10
+ bl_0_10 br_0_10 wl_0_0 vdd gnd
+ dummy_cell_1rw
Xbit_r0_c11
+ bl_0_11 br_0_11 wl_0_0 vdd gnd
+ dummy_cell_1rw
Xbit_r0_c12
+ bl_0_12 br_0_12 wl_0_0 vdd gnd
+ dummy_cell_1rw
Xbit_r0_c13
+ bl_0_13 br_0_13 wl_0_0 vdd gnd
+ dummy_cell_1rw
Xbit_r0_c14
+ bl_0_14 br_0_14 wl_0_0 vdd gnd
+ dummy_cell_1rw
Xbit_r0_c15
+ bl_0_15 br_0_15 wl_0_0 vdd gnd
+ dummy_cell_1rw
Xbit_r0_c16
+ bl_0_16 br_0_16 wl_0_0 vdd gnd
+ dummy_cell_1rw
.ENDS sram_dummy_array_0

.SUBCKT sram_dummy_array
+ bl_0_0 br_0_0 bl_0_1 br_0_1 bl_0_2 br_0_2 bl_0_3 br_0_3 bl_0_4 br_0_4
+ bl_0_5 br_0_5 bl_0_6 br_0_6 bl_0_7 br_0_7 bl_0_8 br_0_8 bl_0_9 br_0_9
+ bl_0_10 br_0_10 bl_0_11 br_0_11 bl_0_12 br_0_12 bl_0_13 br_0_13
+ bl_0_14 br_0_14 bl_0_15 br_0_15 wl_0_0 vdd gnd
* INOUT : bl_0_0 
* INOUT : br_0_0 
* INOUT : bl_0_1 
* INOUT : br_0_1 
* INOUT : bl_0_2 
* INOUT : br_0_2 
* INOUT : bl_0_3 
* INOUT : br_0_3 
* INOUT : bl_0_4 
* INOUT : br_0_4 
* INOUT : bl_0_5 
* INOUT : br_0_5 
* INOUT : bl_0_6 
* INOUT : br_0_6 
* INOUT : bl_0_7 
* INOUT : br_0_7 
* INOUT : bl_0_8 
* INOUT : br_0_8 
* INOUT : bl_0_9 
* INOUT : br_0_9 
* INOUT : bl_0_10 
* INOUT : br_0_10 
* INOUT : bl_0_11 
* INOUT : br_0_11 
* INOUT : bl_0_12 
* INOUT : br_0_12 
* INOUT : bl_0_13 
* INOUT : br_0_13 
* INOUT : bl_0_14 
* INOUT : br_0_14 
* INOUT : bl_0_15 
* INOUT : br_0_15 
* INPUT : wl_0_0 
* POWER : vdd 
* GROUND: gnd 
Xbit_r0_c0
+ bl_0_0 br_0_0 wl_0_0 vdd gnd
+ dummy_cell_1rw
Xbit_r0_c1
+ bl_0_1 br_0_1 wl_0_0 vdd gnd
+ dummy_cell_1rw
Xbit_r0_c2
+ bl_0_2 br_0_2 wl_0_0 vdd gnd
+ dummy_cell_1rw
Xbit_r0_c3
+ bl_0_3 br_0_3 wl_0_0 vdd gnd
+ dummy_cell_1rw
Xbit_r0_c4
+ bl_0_4 br_0_4 wl_0_0 vdd gnd
+ dummy_cell_1rw
Xbit_r0_c5
+ bl_0_5 br_0_5 wl_0_0 vdd gnd
+ dummy_cell_1rw
Xbit_r0_c6
+ bl_0_6 br_0_6 wl_0_0 vdd gnd
+ dummy_cell_1rw
Xbit_r0_c7
+ bl_0_7 br_0_7 wl_0_0 vdd gnd
+ dummy_cell_1rw
Xbit_r0_c8
+ bl_0_8 br_0_8 wl_0_0 vdd gnd
+ dummy_cell_1rw
Xbit_r0_c9
+ bl_0_9 br_0_9 wl_0_0 vdd gnd
+ dummy_cell_1rw
Xbit_r0_c10
+ bl_0_10 br_0_10 wl_0_0 vdd gnd
+ dummy_cell_1rw
Xbit_r0_c11
+ bl_0_11 br_0_11 wl_0_0 vdd gnd
+ dummy_cell_1rw
Xbit_r0_c12
+ bl_0_12 br_0_12 wl_0_0 vdd gnd
+ dummy_cell_1rw
Xbit_r0_c13
+ bl_0_13 br_0_13 wl_0_0 vdd gnd
+ dummy_cell_1rw
Xbit_r0_c14
+ bl_0_14 br_0_14 wl_0_0 vdd gnd
+ dummy_cell_1rw
Xbit_r0_c15
+ bl_0_15 br_0_15 wl_0_0 vdd gnd
+ dummy_cell_1rw
.ENDS sram_dummy_array

.SUBCKT replica_cell_1rw bl br wl vdd gnd
* Inverter 1
MM0 vdd Q gnd gnd NMOS_VTG W=205.00n L=50n
MM4 vdd Q vdd vdd PMOS_VTG W=90n L=50n

* Inverer 2
MM1 Q vdd gnd gnd NMOS_VTG W=205.00n L=50n
MM5 Q vdd vdd vdd PMOS_VTG W=90n L=50n

* Access transistors
MM3 bl wl Q gnd NMOS_VTG W=135.00n L=50n
MM2 br wl vdd gnd NMOS_VTG W=135.00n L=50n
.ENDS cell_1rw


.SUBCKT sram_replica_column
+ bl_0_0 br_0_0 wl_0_0 wl_0_1 wl_0_2 wl_0_3 wl_0_4 wl_0_5 wl_0_6 wl_0_7
+ wl_0_8 wl_0_9 wl_0_10 wl_0_11 wl_0_12 wl_0_13 wl_0_14 wl_0_15 wl_0_16
+ vdd gnd
* OUTPUT: bl_0_0 
* OUTPUT: br_0_0 
* INPUT : wl_0_0 
* INPUT : wl_0_1 
* INPUT : wl_0_2 
* INPUT : wl_0_3 
* INPUT : wl_0_4 
* INPUT : wl_0_5 
* INPUT : wl_0_6 
* INPUT : wl_0_7 
* INPUT : wl_0_8 
* INPUT : wl_0_9 
* INPUT : wl_0_10 
* INPUT : wl_0_11 
* INPUT : wl_0_12 
* INPUT : wl_0_13 
* INPUT : wl_0_14 
* INPUT : wl_0_15 
* INPUT : wl_0_16 
* POWER : vdd 
* GROUND: gnd 
Xrbc_0
+ bl_0_0 br_0_0 wl_0_0 vdd gnd
+ replica_cell_1rw
Xrbc_1
+ bl_0_0 br_0_0 wl_0_1 vdd gnd
+ replica_cell_1rw
Xrbc_2
+ bl_0_0 br_0_0 wl_0_2 vdd gnd
+ replica_cell_1rw
Xrbc_3
+ bl_0_0 br_0_0 wl_0_3 vdd gnd
+ replica_cell_1rw
Xrbc_4
+ bl_0_0 br_0_0 wl_0_4 vdd gnd
+ replica_cell_1rw
Xrbc_5
+ bl_0_0 br_0_0 wl_0_5 vdd gnd
+ replica_cell_1rw
Xrbc_6
+ bl_0_0 br_0_0 wl_0_6 vdd gnd
+ replica_cell_1rw
Xrbc_7
+ bl_0_0 br_0_0 wl_0_7 vdd gnd
+ replica_cell_1rw
Xrbc_8
+ bl_0_0 br_0_0 wl_0_8 vdd gnd
+ replica_cell_1rw
Xrbc_9
+ bl_0_0 br_0_0 wl_0_9 vdd gnd
+ replica_cell_1rw
Xrbc_10
+ bl_0_0 br_0_0 wl_0_10 vdd gnd
+ replica_cell_1rw
Xrbc_11
+ bl_0_0 br_0_0 wl_0_11 vdd gnd
+ replica_cell_1rw
Xrbc_12
+ bl_0_0 br_0_0 wl_0_12 vdd gnd
+ replica_cell_1rw
Xrbc_13
+ bl_0_0 br_0_0 wl_0_13 vdd gnd
+ replica_cell_1rw
Xrbc_14
+ bl_0_0 br_0_0 wl_0_14 vdd gnd
+ replica_cell_1rw
Xrbc_15
+ bl_0_0 br_0_0 wl_0_15 vdd gnd
+ replica_cell_1rw
Xrbc_16
+ bl_0_0 br_0_0 wl_0_16 vdd gnd
+ replica_cell_1rw
.ENDS sram_replica_column

.SUBCKT cell_1rw bl br wl vdd gnd
* Inverter 1
MM0 Q_bar Q gnd gnd NMOS_VTG W=205.00n L=50n
MM4 Q_bar Q vdd vdd PMOS_VTG W=90n L=50n

* Inverer 2
MM1 Q Q_bar gnd gnd NMOS_VTG W=205.00n L=50n
MM5 Q Q_bar vdd vdd PMOS_VTG W=90n L=50n

* Access transistors
MM3 bl wl Q gnd NMOS_VTG W=135.00n L=50n
MM2 br wl Q_bar gnd NMOS_VTG W=135.00n L=50n
.ENDS cell_1rw


.SUBCKT sram_bitcell_array
+ bl_0_0 br_0_0 bl_0_1 br_0_1 bl_0_2 br_0_2 bl_0_3 br_0_3 bl_0_4 br_0_4
+ bl_0_5 br_0_5 bl_0_6 br_0_6 bl_0_7 br_0_7 bl_0_8 br_0_8 bl_0_9 br_0_9
+ bl_0_10 br_0_10 bl_0_11 br_0_11 bl_0_12 br_0_12 bl_0_13 br_0_13
+ bl_0_14 br_0_14 bl_0_15 br_0_15 wl_0_0 wl_0_1 wl_0_2 wl_0_3 wl_0_4
+ wl_0_5 wl_0_6 wl_0_7 wl_0_8 wl_0_9 wl_0_10 wl_0_11 wl_0_12 wl_0_13
+ wl_0_14 wl_0_15 vdd gnd
* INOUT : bl_0_0 
* INOUT : br_0_0 
* INOUT : bl_0_1 
* INOUT : br_0_1 
* INOUT : bl_0_2 
* INOUT : br_0_2 
* INOUT : bl_0_3 
* INOUT : br_0_3 
* INOUT : bl_0_4 
* INOUT : br_0_4 
* INOUT : bl_0_5 
* INOUT : br_0_5 
* INOUT : bl_0_6 
* INOUT : br_0_6 
* INOUT : bl_0_7 
* INOUT : br_0_7 
* INOUT : bl_0_8 
* INOUT : br_0_8 
* INOUT : bl_0_9 
* INOUT : br_0_9 
* INOUT : bl_0_10 
* INOUT : br_0_10 
* INOUT : bl_0_11 
* INOUT : br_0_11 
* INOUT : bl_0_12 
* INOUT : br_0_12 
* INOUT : bl_0_13 
* INOUT : br_0_13 
* INOUT : bl_0_14 
* INOUT : br_0_14 
* INOUT : bl_0_15 
* INOUT : br_0_15 
* INPUT : wl_0_0 
* INPUT : wl_0_1 
* INPUT : wl_0_2 
* INPUT : wl_0_3 
* INPUT : wl_0_4 
* INPUT : wl_0_5 
* INPUT : wl_0_6 
* INPUT : wl_0_7 
* INPUT : wl_0_8 
* INPUT : wl_0_9 
* INPUT : wl_0_10 
* INPUT : wl_0_11 
* INPUT : wl_0_12 
* INPUT : wl_0_13 
* INPUT : wl_0_14 
* INPUT : wl_0_15 
* POWER : vdd 
* GROUND: gnd 
* rows: 16 cols: 16
Xbit_r0_c0
+ bl_0_0 br_0_0 wl_0_0 vdd gnd
+ cell_1rw
Xbit_r1_c0
+ bl_0_0 br_0_0 wl_0_1 vdd gnd
+ cell_1rw
Xbit_r2_c0
+ bl_0_0 br_0_0 wl_0_2 vdd gnd
+ cell_1rw
Xbit_r3_c0
+ bl_0_0 br_0_0 wl_0_3 vdd gnd
+ cell_1rw
Xbit_r4_c0
+ bl_0_0 br_0_0 wl_0_4 vdd gnd
+ cell_1rw
Xbit_r5_c0
+ bl_0_0 br_0_0 wl_0_5 vdd gnd
+ cell_1rw
Xbit_r6_c0
+ bl_0_0 br_0_0 wl_0_6 vdd gnd
+ cell_1rw
Xbit_r7_c0
+ bl_0_0 br_0_0 wl_0_7 vdd gnd
+ cell_1rw
Xbit_r8_c0
+ bl_0_0 br_0_0 wl_0_8 vdd gnd
+ cell_1rw
Xbit_r9_c0
+ bl_0_0 br_0_0 wl_0_9 vdd gnd
+ cell_1rw
Xbit_r10_c0
+ bl_0_0 br_0_0 wl_0_10 vdd gnd
+ cell_1rw
Xbit_r11_c0
+ bl_0_0 br_0_0 wl_0_11 vdd gnd
+ cell_1rw
Xbit_r12_c0
+ bl_0_0 br_0_0 wl_0_12 vdd gnd
+ cell_1rw
Xbit_r13_c0
+ bl_0_0 br_0_0 wl_0_13 vdd gnd
+ cell_1rw
Xbit_r14_c0
+ bl_0_0 br_0_0 wl_0_14 vdd gnd
+ cell_1rw
Xbit_r15_c0
+ bl_0_0 br_0_0 wl_0_15 vdd gnd
+ cell_1rw
Xbit_r0_c1
+ bl_0_1 br_0_1 wl_0_0 vdd gnd
+ cell_1rw
Xbit_r1_c1
+ bl_0_1 br_0_1 wl_0_1 vdd gnd
+ cell_1rw
Xbit_r2_c1
+ bl_0_1 br_0_1 wl_0_2 vdd gnd
+ cell_1rw
Xbit_r3_c1
+ bl_0_1 br_0_1 wl_0_3 vdd gnd
+ cell_1rw
Xbit_r4_c1
+ bl_0_1 br_0_1 wl_0_4 vdd gnd
+ cell_1rw
Xbit_r5_c1
+ bl_0_1 br_0_1 wl_0_5 vdd gnd
+ cell_1rw
Xbit_r6_c1
+ bl_0_1 br_0_1 wl_0_6 vdd gnd
+ cell_1rw
Xbit_r7_c1
+ bl_0_1 br_0_1 wl_0_7 vdd gnd
+ cell_1rw
Xbit_r8_c1
+ bl_0_1 br_0_1 wl_0_8 vdd gnd
+ cell_1rw
Xbit_r9_c1
+ bl_0_1 br_0_1 wl_0_9 vdd gnd
+ cell_1rw
Xbit_r10_c1
+ bl_0_1 br_0_1 wl_0_10 vdd gnd
+ cell_1rw
Xbit_r11_c1
+ bl_0_1 br_0_1 wl_0_11 vdd gnd
+ cell_1rw
Xbit_r12_c1
+ bl_0_1 br_0_1 wl_0_12 vdd gnd
+ cell_1rw
Xbit_r13_c1
+ bl_0_1 br_0_1 wl_0_13 vdd gnd
+ cell_1rw
Xbit_r14_c1
+ bl_0_1 br_0_1 wl_0_14 vdd gnd
+ cell_1rw
Xbit_r15_c1
+ bl_0_1 br_0_1 wl_0_15 vdd gnd
+ cell_1rw
Xbit_r0_c2
+ bl_0_2 br_0_2 wl_0_0 vdd gnd
+ cell_1rw
Xbit_r1_c2
+ bl_0_2 br_0_2 wl_0_1 vdd gnd
+ cell_1rw
Xbit_r2_c2
+ bl_0_2 br_0_2 wl_0_2 vdd gnd
+ cell_1rw
Xbit_r3_c2
+ bl_0_2 br_0_2 wl_0_3 vdd gnd
+ cell_1rw
Xbit_r4_c2
+ bl_0_2 br_0_2 wl_0_4 vdd gnd
+ cell_1rw
Xbit_r5_c2
+ bl_0_2 br_0_2 wl_0_5 vdd gnd
+ cell_1rw
Xbit_r6_c2
+ bl_0_2 br_0_2 wl_0_6 vdd gnd
+ cell_1rw
Xbit_r7_c2
+ bl_0_2 br_0_2 wl_0_7 vdd gnd
+ cell_1rw
Xbit_r8_c2
+ bl_0_2 br_0_2 wl_0_8 vdd gnd
+ cell_1rw
Xbit_r9_c2
+ bl_0_2 br_0_2 wl_0_9 vdd gnd
+ cell_1rw
Xbit_r10_c2
+ bl_0_2 br_0_2 wl_0_10 vdd gnd
+ cell_1rw
Xbit_r11_c2
+ bl_0_2 br_0_2 wl_0_11 vdd gnd
+ cell_1rw
Xbit_r12_c2
+ bl_0_2 br_0_2 wl_0_12 vdd gnd
+ cell_1rw
Xbit_r13_c2
+ bl_0_2 br_0_2 wl_0_13 vdd gnd
+ cell_1rw
Xbit_r14_c2
+ bl_0_2 br_0_2 wl_0_14 vdd gnd
+ cell_1rw
Xbit_r15_c2
+ bl_0_2 br_0_2 wl_0_15 vdd gnd
+ cell_1rw
Xbit_r0_c3
+ bl_0_3 br_0_3 wl_0_0 vdd gnd
+ cell_1rw
Xbit_r1_c3
+ bl_0_3 br_0_3 wl_0_1 vdd gnd
+ cell_1rw
Xbit_r2_c3
+ bl_0_3 br_0_3 wl_0_2 vdd gnd
+ cell_1rw
Xbit_r3_c3
+ bl_0_3 br_0_3 wl_0_3 vdd gnd
+ cell_1rw
Xbit_r4_c3
+ bl_0_3 br_0_3 wl_0_4 vdd gnd
+ cell_1rw
Xbit_r5_c3
+ bl_0_3 br_0_3 wl_0_5 vdd gnd
+ cell_1rw
Xbit_r6_c3
+ bl_0_3 br_0_3 wl_0_6 vdd gnd
+ cell_1rw
Xbit_r7_c3
+ bl_0_3 br_0_3 wl_0_7 vdd gnd
+ cell_1rw
Xbit_r8_c3
+ bl_0_3 br_0_3 wl_0_8 vdd gnd
+ cell_1rw
Xbit_r9_c3
+ bl_0_3 br_0_3 wl_0_9 vdd gnd
+ cell_1rw
Xbit_r10_c3
+ bl_0_3 br_0_3 wl_0_10 vdd gnd
+ cell_1rw
Xbit_r11_c3
+ bl_0_3 br_0_3 wl_0_11 vdd gnd
+ cell_1rw
Xbit_r12_c3
+ bl_0_3 br_0_3 wl_0_12 vdd gnd
+ cell_1rw
Xbit_r13_c3
+ bl_0_3 br_0_3 wl_0_13 vdd gnd
+ cell_1rw
Xbit_r14_c3
+ bl_0_3 br_0_3 wl_0_14 vdd gnd
+ cell_1rw
Xbit_r15_c3
+ bl_0_3 br_0_3 wl_0_15 vdd gnd
+ cell_1rw
Xbit_r0_c4
+ bl_0_4 br_0_4 wl_0_0 vdd gnd
+ cell_1rw
Xbit_r1_c4
+ bl_0_4 br_0_4 wl_0_1 vdd gnd
+ cell_1rw
Xbit_r2_c4
+ bl_0_4 br_0_4 wl_0_2 vdd gnd
+ cell_1rw
Xbit_r3_c4
+ bl_0_4 br_0_4 wl_0_3 vdd gnd
+ cell_1rw
Xbit_r4_c4
+ bl_0_4 br_0_4 wl_0_4 vdd gnd
+ cell_1rw
Xbit_r5_c4
+ bl_0_4 br_0_4 wl_0_5 vdd gnd
+ cell_1rw
Xbit_r6_c4
+ bl_0_4 br_0_4 wl_0_6 vdd gnd
+ cell_1rw
Xbit_r7_c4
+ bl_0_4 br_0_4 wl_0_7 vdd gnd
+ cell_1rw
Xbit_r8_c4
+ bl_0_4 br_0_4 wl_0_8 vdd gnd
+ cell_1rw
Xbit_r9_c4
+ bl_0_4 br_0_4 wl_0_9 vdd gnd
+ cell_1rw
Xbit_r10_c4
+ bl_0_4 br_0_4 wl_0_10 vdd gnd
+ cell_1rw
Xbit_r11_c4
+ bl_0_4 br_0_4 wl_0_11 vdd gnd
+ cell_1rw
Xbit_r12_c4
+ bl_0_4 br_0_4 wl_0_12 vdd gnd
+ cell_1rw
Xbit_r13_c4
+ bl_0_4 br_0_4 wl_0_13 vdd gnd
+ cell_1rw
Xbit_r14_c4
+ bl_0_4 br_0_4 wl_0_14 vdd gnd
+ cell_1rw
Xbit_r15_c4
+ bl_0_4 br_0_4 wl_0_15 vdd gnd
+ cell_1rw
Xbit_r0_c5
+ bl_0_5 br_0_5 wl_0_0 vdd gnd
+ cell_1rw
Xbit_r1_c5
+ bl_0_5 br_0_5 wl_0_1 vdd gnd
+ cell_1rw
Xbit_r2_c5
+ bl_0_5 br_0_5 wl_0_2 vdd gnd
+ cell_1rw
Xbit_r3_c5
+ bl_0_5 br_0_5 wl_0_3 vdd gnd
+ cell_1rw
Xbit_r4_c5
+ bl_0_5 br_0_5 wl_0_4 vdd gnd
+ cell_1rw
Xbit_r5_c5
+ bl_0_5 br_0_5 wl_0_5 vdd gnd
+ cell_1rw
Xbit_r6_c5
+ bl_0_5 br_0_5 wl_0_6 vdd gnd
+ cell_1rw
Xbit_r7_c5
+ bl_0_5 br_0_5 wl_0_7 vdd gnd
+ cell_1rw
Xbit_r8_c5
+ bl_0_5 br_0_5 wl_0_8 vdd gnd
+ cell_1rw
Xbit_r9_c5
+ bl_0_5 br_0_5 wl_0_9 vdd gnd
+ cell_1rw
Xbit_r10_c5
+ bl_0_5 br_0_5 wl_0_10 vdd gnd
+ cell_1rw
Xbit_r11_c5
+ bl_0_5 br_0_5 wl_0_11 vdd gnd
+ cell_1rw
Xbit_r12_c5
+ bl_0_5 br_0_5 wl_0_12 vdd gnd
+ cell_1rw
Xbit_r13_c5
+ bl_0_5 br_0_5 wl_0_13 vdd gnd
+ cell_1rw
Xbit_r14_c5
+ bl_0_5 br_0_5 wl_0_14 vdd gnd
+ cell_1rw
Xbit_r15_c5
+ bl_0_5 br_0_5 wl_0_15 vdd gnd
+ cell_1rw
Xbit_r0_c6
+ bl_0_6 br_0_6 wl_0_0 vdd gnd
+ cell_1rw
Xbit_r1_c6
+ bl_0_6 br_0_6 wl_0_1 vdd gnd
+ cell_1rw
Xbit_r2_c6
+ bl_0_6 br_0_6 wl_0_2 vdd gnd
+ cell_1rw
Xbit_r3_c6
+ bl_0_6 br_0_6 wl_0_3 vdd gnd
+ cell_1rw
Xbit_r4_c6
+ bl_0_6 br_0_6 wl_0_4 vdd gnd
+ cell_1rw
Xbit_r5_c6
+ bl_0_6 br_0_6 wl_0_5 vdd gnd
+ cell_1rw
Xbit_r6_c6
+ bl_0_6 br_0_6 wl_0_6 vdd gnd
+ cell_1rw
Xbit_r7_c6
+ bl_0_6 br_0_6 wl_0_7 vdd gnd
+ cell_1rw
Xbit_r8_c6
+ bl_0_6 br_0_6 wl_0_8 vdd gnd
+ cell_1rw
Xbit_r9_c6
+ bl_0_6 br_0_6 wl_0_9 vdd gnd
+ cell_1rw
Xbit_r10_c6
+ bl_0_6 br_0_6 wl_0_10 vdd gnd
+ cell_1rw
Xbit_r11_c6
+ bl_0_6 br_0_6 wl_0_11 vdd gnd
+ cell_1rw
Xbit_r12_c6
+ bl_0_6 br_0_6 wl_0_12 vdd gnd
+ cell_1rw
Xbit_r13_c6
+ bl_0_6 br_0_6 wl_0_13 vdd gnd
+ cell_1rw
Xbit_r14_c6
+ bl_0_6 br_0_6 wl_0_14 vdd gnd
+ cell_1rw
Xbit_r15_c6
+ bl_0_6 br_0_6 wl_0_15 vdd gnd
+ cell_1rw
Xbit_r0_c7
+ bl_0_7 br_0_7 wl_0_0 vdd gnd
+ cell_1rw
Xbit_r1_c7
+ bl_0_7 br_0_7 wl_0_1 vdd gnd
+ cell_1rw
Xbit_r2_c7
+ bl_0_7 br_0_7 wl_0_2 vdd gnd
+ cell_1rw
Xbit_r3_c7
+ bl_0_7 br_0_7 wl_0_3 vdd gnd
+ cell_1rw
Xbit_r4_c7
+ bl_0_7 br_0_7 wl_0_4 vdd gnd
+ cell_1rw
Xbit_r5_c7
+ bl_0_7 br_0_7 wl_0_5 vdd gnd
+ cell_1rw
Xbit_r6_c7
+ bl_0_7 br_0_7 wl_0_6 vdd gnd
+ cell_1rw
Xbit_r7_c7
+ bl_0_7 br_0_7 wl_0_7 vdd gnd
+ cell_1rw
Xbit_r8_c7
+ bl_0_7 br_0_7 wl_0_8 vdd gnd
+ cell_1rw
Xbit_r9_c7
+ bl_0_7 br_0_7 wl_0_9 vdd gnd
+ cell_1rw
Xbit_r10_c7
+ bl_0_7 br_0_7 wl_0_10 vdd gnd
+ cell_1rw
Xbit_r11_c7
+ bl_0_7 br_0_7 wl_0_11 vdd gnd
+ cell_1rw
Xbit_r12_c7
+ bl_0_7 br_0_7 wl_0_12 vdd gnd
+ cell_1rw
Xbit_r13_c7
+ bl_0_7 br_0_7 wl_0_13 vdd gnd
+ cell_1rw
Xbit_r14_c7
+ bl_0_7 br_0_7 wl_0_14 vdd gnd
+ cell_1rw
Xbit_r15_c7
+ bl_0_7 br_0_7 wl_0_15 vdd gnd
+ cell_1rw
Xbit_r0_c8
+ bl_0_8 br_0_8 wl_0_0 vdd gnd
+ cell_1rw
Xbit_r1_c8
+ bl_0_8 br_0_8 wl_0_1 vdd gnd
+ cell_1rw
Xbit_r2_c8
+ bl_0_8 br_0_8 wl_0_2 vdd gnd
+ cell_1rw
Xbit_r3_c8
+ bl_0_8 br_0_8 wl_0_3 vdd gnd
+ cell_1rw
Xbit_r4_c8
+ bl_0_8 br_0_8 wl_0_4 vdd gnd
+ cell_1rw
Xbit_r5_c8
+ bl_0_8 br_0_8 wl_0_5 vdd gnd
+ cell_1rw
Xbit_r6_c8
+ bl_0_8 br_0_8 wl_0_6 vdd gnd
+ cell_1rw
Xbit_r7_c8
+ bl_0_8 br_0_8 wl_0_7 vdd gnd
+ cell_1rw
Xbit_r8_c8
+ bl_0_8 br_0_8 wl_0_8 vdd gnd
+ cell_1rw
Xbit_r9_c8
+ bl_0_8 br_0_8 wl_0_9 vdd gnd
+ cell_1rw
Xbit_r10_c8
+ bl_0_8 br_0_8 wl_0_10 vdd gnd
+ cell_1rw
Xbit_r11_c8
+ bl_0_8 br_0_8 wl_0_11 vdd gnd
+ cell_1rw
Xbit_r12_c8
+ bl_0_8 br_0_8 wl_0_12 vdd gnd
+ cell_1rw
Xbit_r13_c8
+ bl_0_8 br_0_8 wl_0_13 vdd gnd
+ cell_1rw
Xbit_r14_c8
+ bl_0_8 br_0_8 wl_0_14 vdd gnd
+ cell_1rw
Xbit_r15_c8
+ bl_0_8 br_0_8 wl_0_15 vdd gnd
+ cell_1rw
Xbit_r0_c9
+ bl_0_9 br_0_9 wl_0_0 vdd gnd
+ cell_1rw
Xbit_r1_c9
+ bl_0_9 br_0_9 wl_0_1 vdd gnd
+ cell_1rw
Xbit_r2_c9
+ bl_0_9 br_0_9 wl_0_2 vdd gnd
+ cell_1rw
Xbit_r3_c9
+ bl_0_9 br_0_9 wl_0_3 vdd gnd
+ cell_1rw
Xbit_r4_c9
+ bl_0_9 br_0_9 wl_0_4 vdd gnd
+ cell_1rw
Xbit_r5_c9
+ bl_0_9 br_0_9 wl_0_5 vdd gnd
+ cell_1rw
Xbit_r6_c9
+ bl_0_9 br_0_9 wl_0_6 vdd gnd
+ cell_1rw
Xbit_r7_c9
+ bl_0_9 br_0_9 wl_0_7 vdd gnd
+ cell_1rw
Xbit_r8_c9
+ bl_0_9 br_0_9 wl_0_8 vdd gnd
+ cell_1rw
Xbit_r9_c9
+ bl_0_9 br_0_9 wl_0_9 vdd gnd
+ cell_1rw
Xbit_r10_c9
+ bl_0_9 br_0_9 wl_0_10 vdd gnd
+ cell_1rw
Xbit_r11_c9
+ bl_0_9 br_0_9 wl_0_11 vdd gnd
+ cell_1rw
Xbit_r12_c9
+ bl_0_9 br_0_9 wl_0_12 vdd gnd
+ cell_1rw
Xbit_r13_c9
+ bl_0_9 br_0_9 wl_0_13 vdd gnd
+ cell_1rw
Xbit_r14_c9
+ bl_0_9 br_0_9 wl_0_14 vdd gnd
+ cell_1rw
Xbit_r15_c9
+ bl_0_9 br_0_9 wl_0_15 vdd gnd
+ cell_1rw
Xbit_r0_c10
+ bl_0_10 br_0_10 wl_0_0 vdd gnd
+ cell_1rw
Xbit_r1_c10
+ bl_0_10 br_0_10 wl_0_1 vdd gnd
+ cell_1rw
Xbit_r2_c10
+ bl_0_10 br_0_10 wl_0_2 vdd gnd
+ cell_1rw
Xbit_r3_c10
+ bl_0_10 br_0_10 wl_0_3 vdd gnd
+ cell_1rw
Xbit_r4_c10
+ bl_0_10 br_0_10 wl_0_4 vdd gnd
+ cell_1rw
Xbit_r5_c10
+ bl_0_10 br_0_10 wl_0_5 vdd gnd
+ cell_1rw
Xbit_r6_c10
+ bl_0_10 br_0_10 wl_0_6 vdd gnd
+ cell_1rw
Xbit_r7_c10
+ bl_0_10 br_0_10 wl_0_7 vdd gnd
+ cell_1rw
Xbit_r8_c10
+ bl_0_10 br_0_10 wl_0_8 vdd gnd
+ cell_1rw
Xbit_r9_c10
+ bl_0_10 br_0_10 wl_0_9 vdd gnd
+ cell_1rw
Xbit_r10_c10
+ bl_0_10 br_0_10 wl_0_10 vdd gnd
+ cell_1rw
Xbit_r11_c10
+ bl_0_10 br_0_10 wl_0_11 vdd gnd
+ cell_1rw
Xbit_r12_c10
+ bl_0_10 br_0_10 wl_0_12 vdd gnd
+ cell_1rw
Xbit_r13_c10
+ bl_0_10 br_0_10 wl_0_13 vdd gnd
+ cell_1rw
Xbit_r14_c10
+ bl_0_10 br_0_10 wl_0_14 vdd gnd
+ cell_1rw
Xbit_r15_c10
+ bl_0_10 br_0_10 wl_0_15 vdd gnd
+ cell_1rw
Xbit_r0_c11
+ bl_0_11 br_0_11 wl_0_0 vdd gnd
+ cell_1rw
Xbit_r1_c11
+ bl_0_11 br_0_11 wl_0_1 vdd gnd
+ cell_1rw
Xbit_r2_c11
+ bl_0_11 br_0_11 wl_0_2 vdd gnd
+ cell_1rw
Xbit_r3_c11
+ bl_0_11 br_0_11 wl_0_3 vdd gnd
+ cell_1rw
Xbit_r4_c11
+ bl_0_11 br_0_11 wl_0_4 vdd gnd
+ cell_1rw
Xbit_r5_c11
+ bl_0_11 br_0_11 wl_0_5 vdd gnd
+ cell_1rw
Xbit_r6_c11
+ bl_0_11 br_0_11 wl_0_6 vdd gnd
+ cell_1rw
Xbit_r7_c11
+ bl_0_11 br_0_11 wl_0_7 vdd gnd
+ cell_1rw
Xbit_r8_c11
+ bl_0_11 br_0_11 wl_0_8 vdd gnd
+ cell_1rw
Xbit_r9_c11
+ bl_0_11 br_0_11 wl_0_9 vdd gnd
+ cell_1rw
Xbit_r10_c11
+ bl_0_11 br_0_11 wl_0_10 vdd gnd
+ cell_1rw
Xbit_r11_c11
+ bl_0_11 br_0_11 wl_0_11 vdd gnd
+ cell_1rw
Xbit_r12_c11
+ bl_0_11 br_0_11 wl_0_12 vdd gnd
+ cell_1rw
Xbit_r13_c11
+ bl_0_11 br_0_11 wl_0_13 vdd gnd
+ cell_1rw
Xbit_r14_c11
+ bl_0_11 br_0_11 wl_0_14 vdd gnd
+ cell_1rw
Xbit_r15_c11
+ bl_0_11 br_0_11 wl_0_15 vdd gnd
+ cell_1rw
Xbit_r0_c12
+ bl_0_12 br_0_12 wl_0_0 vdd gnd
+ cell_1rw
Xbit_r1_c12
+ bl_0_12 br_0_12 wl_0_1 vdd gnd
+ cell_1rw
Xbit_r2_c12
+ bl_0_12 br_0_12 wl_0_2 vdd gnd
+ cell_1rw
Xbit_r3_c12
+ bl_0_12 br_0_12 wl_0_3 vdd gnd
+ cell_1rw
Xbit_r4_c12
+ bl_0_12 br_0_12 wl_0_4 vdd gnd
+ cell_1rw
Xbit_r5_c12
+ bl_0_12 br_0_12 wl_0_5 vdd gnd
+ cell_1rw
Xbit_r6_c12
+ bl_0_12 br_0_12 wl_0_6 vdd gnd
+ cell_1rw
Xbit_r7_c12
+ bl_0_12 br_0_12 wl_0_7 vdd gnd
+ cell_1rw
Xbit_r8_c12
+ bl_0_12 br_0_12 wl_0_8 vdd gnd
+ cell_1rw
Xbit_r9_c12
+ bl_0_12 br_0_12 wl_0_9 vdd gnd
+ cell_1rw
Xbit_r10_c12
+ bl_0_12 br_0_12 wl_0_10 vdd gnd
+ cell_1rw
Xbit_r11_c12
+ bl_0_12 br_0_12 wl_0_11 vdd gnd
+ cell_1rw
Xbit_r12_c12
+ bl_0_12 br_0_12 wl_0_12 vdd gnd
+ cell_1rw
Xbit_r13_c12
+ bl_0_12 br_0_12 wl_0_13 vdd gnd
+ cell_1rw
Xbit_r14_c12
+ bl_0_12 br_0_12 wl_0_14 vdd gnd
+ cell_1rw
Xbit_r15_c12
+ bl_0_12 br_0_12 wl_0_15 vdd gnd
+ cell_1rw
Xbit_r0_c13
+ bl_0_13 br_0_13 wl_0_0 vdd gnd
+ cell_1rw
Xbit_r1_c13
+ bl_0_13 br_0_13 wl_0_1 vdd gnd
+ cell_1rw
Xbit_r2_c13
+ bl_0_13 br_0_13 wl_0_2 vdd gnd
+ cell_1rw
Xbit_r3_c13
+ bl_0_13 br_0_13 wl_0_3 vdd gnd
+ cell_1rw
Xbit_r4_c13
+ bl_0_13 br_0_13 wl_0_4 vdd gnd
+ cell_1rw
Xbit_r5_c13
+ bl_0_13 br_0_13 wl_0_5 vdd gnd
+ cell_1rw
Xbit_r6_c13
+ bl_0_13 br_0_13 wl_0_6 vdd gnd
+ cell_1rw
Xbit_r7_c13
+ bl_0_13 br_0_13 wl_0_7 vdd gnd
+ cell_1rw
Xbit_r8_c13
+ bl_0_13 br_0_13 wl_0_8 vdd gnd
+ cell_1rw
Xbit_r9_c13
+ bl_0_13 br_0_13 wl_0_9 vdd gnd
+ cell_1rw
Xbit_r10_c13
+ bl_0_13 br_0_13 wl_0_10 vdd gnd
+ cell_1rw
Xbit_r11_c13
+ bl_0_13 br_0_13 wl_0_11 vdd gnd
+ cell_1rw
Xbit_r12_c13
+ bl_0_13 br_0_13 wl_0_12 vdd gnd
+ cell_1rw
Xbit_r13_c13
+ bl_0_13 br_0_13 wl_0_13 vdd gnd
+ cell_1rw
Xbit_r14_c13
+ bl_0_13 br_0_13 wl_0_14 vdd gnd
+ cell_1rw
Xbit_r15_c13
+ bl_0_13 br_0_13 wl_0_15 vdd gnd
+ cell_1rw
Xbit_r0_c14
+ bl_0_14 br_0_14 wl_0_0 vdd gnd
+ cell_1rw
Xbit_r1_c14
+ bl_0_14 br_0_14 wl_0_1 vdd gnd
+ cell_1rw
Xbit_r2_c14
+ bl_0_14 br_0_14 wl_0_2 vdd gnd
+ cell_1rw
Xbit_r3_c14
+ bl_0_14 br_0_14 wl_0_3 vdd gnd
+ cell_1rw
Xbit_r4_c14
+ bl_0_14 br_0_14 wl_0_4 vdd gnd
+ cell_1rw
Xbit_r5_c14
+ bl_0_14 br_0_14 wl_0_5 vdd gnd
+ cell_1rw
Xbit_r6_c14
+ bl_0_14 br_0_14 wl_0_6 vdd gnd
+ cell_1rw
Xbit_r7_c14
+ bl_0_14 br_0_14 wl_0_7 vdd gnd
+ cell_1rw
Xbit_r8_c14
+ bl_0_14 br_0_14 wl_0_8 vdd gnd
+ cell_1rw
Xbit_r9_c14
+ bl_0_14 br_0_14 wl_0_9 vdd gnd
+ cell_1rw
Xbit_r10_c14
+ bl_0_14 br_0_14 wl_0_10 vdd gnd
+ cell_1rw
Xbit_r11_c14
+ bl_0_14 br_0_14 wl_0_11 vdd gnd
+ cell_1rw
Xbit_r12_c14
+ bl_0_14 br_0_14 wl_0_12 vdd gnd
+ cell_1rw
Xbit_r13_c14
+ bl_0_14 br_0_14 wl_0_13 vdd gnd
+ cell_1rw
Xbit_r14_c14
+ bl_0_14 br_0_14 wl_0_14 vdd gnd
+ cell_1rw
Xbit_r15_c14
+ bl_0_14 br_0_14 wl_0_15 vdd gnd
+ cell_1rw
Xbit_r0_c15
+ bl_0_15 br_0_15 wl_0_0 vdd gnd
+ cell_1rw
Xbit_r1_c15
+ bl_0_15 br_0_15 wl_0_1 vdd gnd
+ cell_1rw
Xbit_r2_c15
+ bl_0_15 br_0_15 wl_0_2 vdd gnd
+ cell_1rw
Xbit_r3_c15
+ bl_0_15 br_0_15 wl_0_3 vdd gnd
+ cell_1rw
Xbit_r4_c15
+ bl_0_15 br_0_15 wl_0_4 vdd gnd
+ cell_1rw
Xbit_r5_c15
+ bl_0_15 br_0_15 wl_0_5 vdd gnd
+ cell_1rw
Xbit_r6_c15
+ bl_0_15 br_0_15 wl_0_6 vdd gnd
+ cell_1rw
Xbit_r7_c15
+ bl_0_15 br_0_15 wl_0_7 vdd gnd
+ cell_1rw
Xbit_r8_c15
+ bl_0_15 br_0_15 wl_0_8 vdd gnd
+ cell_1rw
Xbit_r9_c15
+ bl_0_15 br_0_15 wl_0_9 vdd gnd
+ cell_1rw
Xbit_r10_c15
+ bl_0_15 br_0_15 wl_0_10 vdd gnd
+ cell_1rw
Xbit_r11_c15
+ bl_0_15 br_0_15 wl_0_11 vdd gnd
+ cell_1rw
Xbit_r12_c15
+ bl_0_15 br_0_15 wl_0_12 vdd gnd
+ cell_1rw
Xbit_r13_c15
+ bl_0_15 br_0_15 wl_0_13 vdd gnd
+ cell_1rw
Xbit_r14_c15
+ bl_0_15 br_0_15 wl_0_14 vdd gnd
+ cell_1rw
Xbit_r15_c15
+ bl_0_15 br_0_15 wl_0_15 vdd gnd
+ cell_1rw
.ENDS sram_bitcell_array

.SUBCKT sram_replica_bitcell_array
+ rbl_bl_0_0 rbl_br_0_0 bl_0_0 br_0_0 bl_0_1 br_0_1 bl_0_2 br_0_2 bl_0_3
+ br_0_3 bl_0_4 br_0_4 bl_0_5 br_0_5 bl_0_6 br_0_6 bl_0_7 br_0_7 bl_0_8
+ br_0_8 bl_0_9 br_0_9 bl_0_10 br_0_10 bl_0_11 br_0_11 bl_0_12 br_0_12
+ bl_0_13 br_0_13 bl_0_14 br_0_14 bl_0_15 br_0_15 rbl_wl_0_0 wl_0_0
+ wl_0_1 wl_0_2 wl_0_3 wl_0_4 wl_0_5 wl_0_6 wl_0_7 wl_0_8 wl_0_9 wl_0_10
+ wl_0_11 wl_0_12 wl_0_13 wl_0_14 wl_0_15 vdd gnd
* INOUT : rbl_bl_0_0 
* INOUT : rbl_br_0_0 
* INOUT : bl_0_0 
* INOUT : br_0_0 
* INOUT : bl_0_1 
* INOUT : br_0_1 
* INOUT : bl_0_2 
* INOUT : br_0_2 
* INOUT : bl_0_3 
* INOUT : br_0_3 
* INOUT : bl_0_4 
* INOUT : br_0_4 
* INOUT : bl_0_5 
* INOUT : br_0_5 
* INOUT : bl_0_6 
* INOUT : br_0_6 
* INOUT : bl_0_7 
* INOUT : br_0_7 
* INOUT : bl_0_8 
* INOUT : br_0_8 
* INOUT : bl_0_9 
* INOUT : br_0_9 
* INOUT : bl_0_10 
* INOUT : br_0_10 
* INOUT : bl_0_11 
* INOUT : br_0_11 
* INOUT : bl_0_12 
* INOUT : br_0_12 
* INOUT : bl_0_13 
* INOUT : br_0_13 
* INOUT : bl_0_14 
* INOUT : br_0_14 
* INOUT : bl_0_15 
* INOUT : br_0_15 
* INPUT : rbl_wl_0_0 
* INPUT : wl_0_0 
* INPUT : wl_0_1 
* INPUT : wl_0_2 
* INPUT : wl_0_3 
* INPUT : wl_0_4 
* INPUT : wl_0_5 
* INPUT : wl_0_6 
* INPUT : wl_0_7 
* INPUT : wl_0_8 
* INPUT : wl_0_9 
* INPUT : wl_0_10 
* INPUT : wl_0_11 
* INPUT : wl_0_12 
* INPUT : wl_0_13 
* INPUT : wl_0_14 
* INPUT : wl_0_15 
* POWER : vdd 
* GROUND: gnd 
* rows: 16 cols: 16
* rbl: [1, 0] left_rbl: [0] right_rbl: []
Xbitcell_array
+ bl_0_0 br_0_0 bl_0_1 br_0_1 bl_0_2 br_0_2 bl_0_3 br_0_3 bl_0_4 br_0_4
+ bl_0_5 br_0_5 bl_0_6 br_0_6 bl_0_7 br_0_7 bl_0_8 br_0_8 bl_0_9 br_0_9
+ bl_0_10 br_0_10 bl_0_11 br_0_11 bl_0_12 br_0_12 bl_0_13 br_0_13
+ bl_0_14 br_0_14 bl_0_15 br_0_15 wl_0_0 wl_0_1 wl_0_2 wl_0_3 wl_0_4
+ wl_0_5 wl_0_6 wl_0_7 wl_0_8 wl_0_9 wl_0_10 wl_0_11 wl_0_12 wl_0_13
+ wl_0_14 wl_0_15 vdd gnd
+ sram_bitcell_array
Xreplica_col_0
+ rbl_bl_0_0 rbl_br_0_0 rbl_wl_0_0 wl_0_0 wl_0_1 wl_0_2 wl_0_3 wl_0_4
+ wl_0_5 wl_0_6 wl_0_7 wl_0_8 wl_0_9 wl_0_10 wl_0_11 wl_0_12 wl_0_13
+ wl_0_14 wl_0_15 vdd gnd
+ sram_replica_column
Xdummy_row_0
+ bl_0_0 br_0_0 bl_0_1 br_0_1 bl_0_2 br_0_2 bl_0_3 br_0_3 bl_0_4 br_0_4
+ bl_0_5 br_0_5 bl_0_6 br_0_6 bl_0_7 br_0_7 bl_0_8 br_0_8 bl_0_9 br_0_9
+ bl_0_10 br_0_10 bl_0_11 br_0_11 bl_0_12 br_0_12 bl_0_13 br_0_13
+ bl_0_14 br_0_14 bl_0_15 br_0_15 rbl_wl_0_0 vdd gnd
+ sram_dummy_array
.ENDS sram_replica_bitcell_array

.SUBCKT sram_dummy_array_1
+ bl_0_0 br_0_0 bl_0_1 br_0_1 bl_0_2 br_0_2 bl_0_3 br_0_3 bl_0_4 br_0_4
+ bl_0_5 br_0_5 bl_0_6 br_0_6 bl_0_7 br_0_7 bl_0_8 br_0_8 bl_0_9 br_0_9
+ bl_0_10 br_0_10 bl_0_11 br_0_11 bl_0_12 br_0_12 bl_0_13 br_0_13
+ bl_0_14 br_0_14 bl_0_15 br_0_15 bl_0_16 br_0_16 wl_0_0 vdd gnd
* INOUT : bl_0_0 
* INOUT : br_0_0 
* INOUT : bl_0_1 
* INOUT : br_0_1 
* INOUT : bl_0_2 
* INOUT : br_0_2 
* INOUT : bl_0_3 
* INOUT : br_0_3 
* INOUT : bl_0_4 
* INOUT : br_0_4 
* INOUT : bl_0_5 
* INOUT : br_0_5 
* INOUT : bl_0_6 
* INOUT : br_0_6 
* INOUT : bl_0_7 
* INOUT : br_0_7 
* INOUT : bl_0_8 
* INOUT : br_0_8 
* INOUT : bl_0_9 
* INOUT : br_0_9 
* INOUT : bl_0_10 
* INOUT : br_0_10 
* INOUT : bl_0_11 
* INOUT : br_0_11 
* INOUT : bl_0_12 
* INOUT : br_0_12 
* INOUT : bl_0_13 
* INOUT : br_0_13 
* INOUT : bl_0_14 
* INOUT : br_0_14 
* INOUT : bl_0_15 
* INOUT : br_0_15 
* INOUT : bl_0_16 
* INOUT : br_0_16 
* INPUT : wl_0_0 
* POWER : vdd 
* GROUND: gnd 
Xbit_r0_c0
+ bl_0_0 br_0_0 wl_0_0 vdd gnd
+ dummy_cell_1rw
Xbit_r0_c1
+ bl_0_1 br_0_1 wl_0_0 vdd gnd
+ dummy_cell_1rw
Xbit_r0_c2
+ bl_0_2 br_0_2 wl_0_0 vdd gnd
+ dummy_cell_1rw
Xbit_r0_c3
+ bl_0_3 br_0_3 wl_0_0 vdd gnd
+ dummy_cell_1rw
Xbit_r0_c4
+ bl_0_4 br_0_4 wl_0_0 vdd gnd
+ dummy_cell_1rw
Xbit_r0_c5
+ bl_0_5 br_0_5 wl_0_0 vdd gnd
+ dummy_cell_1rw
Xbit_r0_c6
+ bl_0_6 br_0_6 wl_0_0 vdd gnd
+ dummy_cell_1rw
Xbit_r0_c7
+ bl_0_7 br_0_7 wl_0_0 vdd gnd
+ dummy_cell_1rw
Xbit_r0_c8
+ bl_0_8 br_0_8 wl_0_0 vdd gnd
+ dummy_cell_1rw
Xbit_r0_c9
+ bl_0_9 br_0_9 wl_0_0 vdd gnd
+ dummy_cell_1rw
Xbit_r0_c10
+ bl_0_10 br_0_10 wl_0_0 vdd gnd
+ dummy_cell_1rw
Xbit_r0_c11
+ bl_0_11 br_0_11 wl_0_0 vdd gnd
+ dummy_cell_1rw
Xbit_r0_c12
+ bl_0_12 br_0_12 wl_0_0 vdd gnd
+ dummy_cell_1rw
Xbit_r0_c13
+ bl_0_13 br_0_13 wl_0_0 vdd gnd
+ dummy_cell_1rw
Xbit_r0_c14
+ bl_0_14 br_0_14 wl_0_0 vdd gnd
+ dummy_cell_1rw
Xbit_r0_c15
+ bl_0_15 br_0_15 wl_0_0 vdd gnd
+ dummy_cell_1rw
Xbit_r0_c16
+ bl_0_16 br_0_16 wl_0_0 vdd gnd
+ dummy_cell_1rw
.ENDS sram_dummy_array_1

.SUBCKT sram_dummy_array_2
+ bl_0_0 br_0_0 wl_0_0 wl_0_1 wl_0_2 wl_0_3 wl_0_4 wl_0_5 wl_0_6 wl_0_7
+ wl_0_8 wl_0_9 wl_0_10 wl_0_11 wl_0_12 wl_0_13 wl_0_14 wl_0_15 wl_0_16
+ wl_0_17 wl_0_18 vdd gnd
* INOUT : bl_0_0 
* INOUT : br_0_0 
* INPUT : wl_0_0 
* INPUT : wl_0_1 
* INPUT : wl_0_2 
* INPUT : wl_0_3 
* INPUT : wl_0_4 
* INPUT : wl_0_5 
* INPUT : wl_0_6 
* INPUT : wl_0_7 
* INPUT : wl_0_8 
* INPUT : wl_0_9 
* INPUT : wl_0_10 
* INPUT : wl_0_11 
* INPUT : wl_0_12 
* INPUT : wl_0_13 
* INPUT : wl_0_14 
* INPUT : wl_0_15 
* INPUT : wl_0_16 
* INPUT : wl_0_17 
* INPUT : wl_0_18 
* POWER : vdd 
* GROUND: gnd 
Xbit_r0_c0
+ bl_0_0 br_0_0 wl_0_0 vdd gnd
+ dummy_cell_1rw
Xbit_r1_c0
+ bl_0_0 br_0_0 wl_0_1 vdd gnd
+ dummy_cell_1rw
Xbit_r2_c0
+ bl_0_0 br_0_0 wl_0_2 vdd gnd
+ dummy_cell_1rw
Xbit_r3_c0
+ bl_0_0 br_0_0 wl_0_3 vdd gnd
+ dummy_cell_1rw
Xbit_r4_c0
+ bl_0_0 br_0_0 wl_0_4 vdd gnd
+ dummy_cell_1rw
Xbit_r5_c0
+ bl_0_0 br_0_0 wl_0_5 vdd gnd
+ dummy_cell_1rw
Xbit_r6_c0
+ bl_0_0 br_0_0 wl_0_6 vdd gnd
+ dummy_cell_1rw
Xbit_r7_c0
+ bl_0_0 br_0_0 wl_0_7 vdd gnd
+ dummy_cell_1rw
Xbit_r8_c0
+ bl_0_0 br_0_0 wl_0_8 vdd gnd
+ dummy_cell_1rw
Xbit_r9_c0
+ bl_0_0 br_0_0 wl_0_9 vdd gnd
+ dummy_cell_1rw
Xbit_r10_c0
+ bl_0_0 br_0_0 wl_0_10 vdd gnd
+ dummy_cell_1rw
Xbit_r11_c0
+ bl_0_0 br_0_0 wl_0_11 vdd gnd
+ dummy_cell_1rw
Xbit_r12_c0
+ bl_0_0 br_0_0 wl_0_12 vdd gnd
+ dummy_cell_1rw
Xbit_r13_c0
+ bl_0_0 br_0_0 wl_0_13 vdd gnd
+ dummy_cell_1rw
Xbit_r14_c0
+ bl_0_0 br_0_0 wl_0_14 vdd gnd
+ dummy_cell_1rw
Xbit_r15_c0
+ bl_0_0 br_0_0 wl_0_15 vdd gnd
+ dummy_cell_1rw
Xbit_r16_c0
+ bl_0_0 br_0_0 wl_0_16 vdd gnd
+ dummy_cell_1rw
Xbit_r17_c0
+ bl_0_0 br_0_0 wl_0_17 vdd gnd
+ dummy_cell_1rw
Xbit_r18_c0
+ bl_0_0 br_0_0 wl_0_18 vdd gnd
+ dummy_cell_1rw
.ENDS sram_dummy_array_2

.SUBCKT sram_dummy_array_3
+ bl_0_0 br_0_0 wl_0_0 wl_0_1 wl_0_2 wl_0_3 wl_0_4 wl_0_5 wl_0_6 wl_0_7
+ wl_0_8 wl_0_9 wl_0_10 wl_0_11 wl_0_12 wl_0_13 wl_0_14 wl_0_15 wl_0_16
+ wl_0_17 wl_0_18 vdd gnd
* INOUT : bl_0_0 
* INOUT : br_0_0 
* INPUT : wl_0_0 
* INPUT : wl_0_1 
* INPUT : wl_0_2 
* INPUT : wl_0_3 
* INPUT : wl_0_4 
* INPUT : wl_0_5 
* INPUT : wl_0_6 
* INPUT : wl_0_7 
* INPUT : wl_0_8 
* INPUT : wl_0_9 
* INPUT : wl_0_10 
* INPUT : wl_0_11 
* INPUT : wl_0_12 
* INPUT : wl_0_13 
* INPUT : wl_0_14 
* INPUT : wl_0_15 
* INPUT : wl_0_16 
* INPUT : wl_0_17 
* INPUT : wl_0_18 
* POWER : vdd 
* GROUND: gnd 
Xbit_r0_c0
+ bl_0_0 br_0_0 wl_0_0 vdd gnd
+ dummy_cell_1rw
Xbit_r1_c0
+ bl_0_0 br_0_0 wl_0_1 vdd gnd
+ dummy_cell_1rw
Xbit_r2_c0
+ bl_0_0 br_0_0 wl_0_2 vdd gnd
+ dummy_cell_1rw
Xbit_r3_c0
+ bl_0_0 br_0_0 wl_0_3 vdd gnd
+ dummy_cell_1rw
Xbit_r4_c0
+ bl_0_0 br_0_0 wl_0_4 vdd gnd
+ dummy_cell_1rw
Xbit_r5_c0
+ bl_0_0 br_0_0 wl_0_5 vdd gnd
+ dummy_cell_1rw
Xbit_r6_c0
+ bl_0_0 br_0_0 wl_0_6 vdd gnd
+ dummy_cell_1rw
Xbit_r7_c0
+ bl_0_0 br_0_0 wl_0_7 vdd gnd
+ dummy_cell_1rw
Xbit_r8_c0
+ bl_0_0 br_0_0 wl_0_8 vdd gnd
+ dummy_cell_1rw
Xbit_r9_c0
+ bl_0_0 br_0_0 wl_0_9 vdd gnd
+ dummy_cell_1rw
Xbit_r10_c0
+ bl_0_0 br_0_0 wl_0_10 vdd gnd
+ dummy_cell_1rw
Xbit_r11_c0
+ bl_0_0 br_0_0 wl_0_11 vdd gnd
+ dummy_cell_1rw
Xbit_r12_c0
+ bl_0_0 br_0_0 wl_0_12 vdd gnd
+ dummy_cell_1rw
Xbit_r13_c0
+ bl_0_0 br_0_0 wl_0_13 vdd gnd
+ dummy_cell_1rw
Xbit_r14_c0
+ bl_0_0 br_0_0 wl_0_14 vdd gnd
+ dummy_cell_1rw
Xbit_r15_c0
+ bl_0_0 br_0_0 wl_0_15 vdd gnd
+ dummy_cell_1rw
Xbit_r16_c0
+ bl_0_0 br_0_0 wl_0_16 vdd gnd
+ dummy_cell_1rw
Xbit_r17_c0
+ bl_0_0 br_0_0 wl_0_17 vdd gnd
+ dummy_cell_1rw
Xbit_r18_c0
+ bl_0_0 br_0_0 wl_0_18 vdd gnd
+ dummy_cell_1rw
.ENDS sram_dummy_array_3

.SUBCKT sram_capped_replica_bitcell_array
+ rbl_bl_0_0 rbl_br_0_0 bl_0_0 br_0_0 bl_0_1 br_0_1 bl_0_2 br_0_2 bl_0_3
+ br_0_3 bl_0_4 br_0_4 bl_0_5 br_0_5 bl_0_6 br_0_6 bl_0_7 br_0_7 bl_0_8
+ br_0_8 bl_0_9 br_0_9 bl_0_10 br_0_10 bl_0_11 br_0_11 bl_0_12 br_0_12
+ bl_0_13 br_0_13 bl_0_14 br_0_14 bl_0_15 br_0_15 rbl_wl_0_0 wl_0_0
+ wl_0_1 wl_0_2 wl_0_3 wl_0_4 wl_0_5 wl_0_6 wl_0_7 wl_0_8 wl_0_9 wl_0_10
+ wl_0_11 wl_0_12 wl_0_13 wl_0_14 wl_0_15 vdd gnd
* INOUT : rbl_bl_0_0 
* INOUT : rbl_br_0_0 
* INOUT : bl_0_0 
* INOUT : br_0_0 
* INOUT : bl_0_1 
* INOUT : br_0_1 
* INOUT : bl_0_2 
* INOUT : br_0_2 
* INOUT : bl_0_3 
* INOUT : br_0_3 
* INOUT : bl_0_4 
* INOUT : br_0_4 
* INOUT : bl_0_5 
* INOUT : br_0_5 
* INOUT : bl_0_6 
* INOUT : br_0_6 
* INOUT : bl_0_7 
* INOUT : br_0_7 
* INOUT : bl_0_8 
* INOUT : br_0_8 
* INOUT : bl_0_9 
* INOUT : br_0_9 
* INOUT : bl_0_10 
* INOUT : br_0_10 
* INOUT : bl_0_11 
* INOUT : br_0_11 
* INOUT : bl_0_12 
* INOUT : br_0_12 
* INOUT : bl_0_13 
* INOUT : br_0_13 
* INOUT : bl_0_14 
* INOUT : br_0_14 
* INOUT : bl_0_15 
* INOUT : br_0_15 
* INPUT : rbl_wl_0_0 
* INPUT : wl_0_0 
* INPUT : wl_0_1 
* INPUT : wl_0_2 
* INPUT : wl_0_3 
* INPUT : wl_0_4 
* INPUT : wl_0_5 
* INPUT : wl_0_6 
* INPUT : wl_0_7 
* INPUT : wl_0_8 
* INPUT : wl_0_9 
* INPUT : wl_0_10 
* INPUT : wl_0_11 
* INPUT : wl_0_12 
* INPUT : wl_0_13 
* INPUT : wl_0_14 
* INPUT : wl_0_15 
* POWER : vdd 
* GROUND: gnd 
* rows: 16 cols: 16
* rbl: [1, 0] left_rbl: [0] right_rbl: []
Xreplica_bitcell_array
+ rbl_bl_0_0 rbl_br_0_0 bl_0_0 br_0_0 bl_0_1 br_0_1 bl_0_2 br_0_2 bl_0_3
+ br_0_3 bl_0_4 br_0_4 bl_0_5 br_0_5 bl_0_6 br_0_6 bl_0_7 br_0_7 bl_0_8
+ br_0_8 bl_0_9 br_0_9 bl_0_10 br_0_10 bl_0_11 br_0_11 bl_0_12 br_0_12
+ bl_0_13 br_0_13 bl_0_14 br_0_14 bl_0_15 br_0_15 rbl_wl_0_0 wl_0_0
+ wl_0_1 wl_0_2 wl_0_3 wl_0_4 wl_0_5 wl_0_6 wl_0_7 wl_0_8 wl_0_9 wl_0_10
+ wl_0_11 wl_0_12 wl_0_13 wl_0_14 wl_0_15 vdd gnd
+ sram_replica_bitcell_array
Xdummy_row_bot
+ rbl_bl_0_0 rbl_br_0_0 bl_0_0 br_0_0 bl_0_1 br_0_1 bl_0_2 br_0_2 bl_0_3
+ br_0_3 bl_0_4 br_0_4 bl_0_5 br_0_5 bl_0_6 br_0_6 bl_0_7 br_0_7 bl_0_8
+ br_0_8 bl_0_9 br_0_9 bl_0_10 br_0_10 bl_0_11 br_0_11 bl_0_12 br_0_12
+ bl_0_13 br_0_13 bl_0_14 br_0_14 bl_0_15 br_0_15 gnd vdd gnd
+ sram_dummy_array_1
Xdummy_row_top
+ rbl_bl_0_0 rbl_br_0_0 bl_0_0 br_0_0 bl_0_1 br_0_1 bl_0_2 br_0_2 bl_0_3
+ br_0_3 bl_0_4 br_0_4 bl_0_5 br_0_5 bl_0_6 br_0_6 bl_0_7 br_0_7 bl_0_8
+ br_0_8 bl_0_9 br_0_9 bl_0_10 br_0_10 bl_0_11 br_0_11 bl_0_12 br_0_12
+ bl_0_13 br_0_13 bl_0_14 br_0_14 bl_0_15 br_0_15 gnd vdd gnd
+ sram_dummy_array_0
Xdummy_col_left
+ dummy_left_bl_0_0 dummy_left_br_0_0 gnd rbl_wl_0_0 wl_0_0 wl_0_1
+ wl_0_2 wl_0_3 wl_0_4 wl_0_5 wl_0_6 wl_0_7 wl_0_8 wl_0_9 wl_0_10
+ wl_0_11 wl_0_12 wl_0_13 wl_0_14 wl_0_15 gnd vdd gnd
+ sram_dummy_array_2
Xdummy_col_right
+ dummy_right_bl_0_0 dummy_right_br_0_0 gnd rbl_wl_0_0 wl_0_0 wl_0_1
+ wl_0_2 wl_0_3 wl_0_4 wl_0_5 wl_0_6 wl_0_7 wl_0_8 wl_0_9 wl_0_10
+ wl_0_11 wl_0_12 wl_0_13 wl_0_14 wl_0_15 gnd vdd gnd
+ sram_dummy_array_3
.ENDS sram_capped_replica_bitcell_array
