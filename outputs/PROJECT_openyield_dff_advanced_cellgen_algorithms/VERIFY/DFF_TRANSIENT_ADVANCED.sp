.include /tmp/qujh_delay_chain_scratch/storage_relief_20260725/worktrees/project_mainline_inventory_20260726/outputs/PROJECT_openyield_dff_advanced_cellgen_algorithms/SOURCE_AUTHORITY/dff_openyield_original.sp
VDD VDD 0 1.0
VD D 0 PWL(0n 0 0.20n 0 0.21n 1 1.20n 1 1.21n 0 2.20n 0 2.21n 1 3.20n 1)
VCLK CLK 0 PULSE(0 1 0.50n 10p 10p 0.35n 1.0n)
X1 VDD 0 D Q CLK dff_openyield_original
Cq Q 0 3f
.ic v(Q)=0
.tran 1p 4n uic
.measure tran q_after_first FIND v(Q) AT=0.80n
.measure tran q_after_second FIND v(Q) AT=1.80n
.measure tran q_after_third FIND v(Q) AT=2.80n
.measure tran q_hold_after_first FIND v(Q) AT=1.30n
.measure tran q_hold_after_second FIND v(Q) AT=2.30n
.end
