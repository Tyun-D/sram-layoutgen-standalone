.model NMOS_VTG NMOS level=1 VTO=0.45 KP=120e-6 CGSO=1e-10 CGDO=1e-10
.model PMOS_VTG PMOS level=1 VTO=-0.45 KP=40e-6 CGSO=1e-10 CGDO=1e-10
.include /tmp/qujh_delay_chain_scratch/storage_relief_20260725/worktrees/project_mainline_inventory_20260726/outputs/PROJECT_openyield_exact_cell_source/wl_driver/openyield_exact.sp
VDD VDD 0 1.0
VA A 0 PULSE(0 1 0.5n 10p 10p 1n 2n)
VB B 0 PULSE(0 1 0.5n 10p 10p 1n 2n)
X1 VDD 0 A B WL wl_driver_openyield_exact
Cwl WL 0 1f
.tran 1p 2n
.measure tran wl_high FIND v(WL) AT=1.0n
.measure tran wl_low FIND v(WL) AT=0.2n
.end
