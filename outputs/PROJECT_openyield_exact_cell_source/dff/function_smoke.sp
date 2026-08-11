.model NMOS_VTG NMOS level=1 VTO=0.45 KP=120e-6 CGSO=1e-10 CGDO=1e-10
.model PMOS_VTG PMOS level=1 VTO=-0.45 KP=40e-6 CGSO=1e-10 CGDO=1e-10
.include /tmp/qujh_delay_chain_scratch/storage_relief_20260725/worktrees/project_mainline_inventory_20260726/outputs/PROJECT_openyield_exact_cell_source/dff/openyield_exact.sp
VDD VDD 0 1.0
VD D 0 PULSE(0 1 0.2n 10p 10p 1.2n 2.4n)
VCLK CLK 0 PULSE(0 1 0.8n 10p 10p 0.5n 1.0n)
X1 VDD 0 D Q CLK dff_openyield_exact
Cq Q 0 1f
.ic v(Q)=0
.tran 1p 4n uic
.measure tran q_after_first FIND v(Q) AT=1.1n
.measure tran q_after_second FIND v(Q) AT=2.1n
.end
