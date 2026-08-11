.model NMOS_VTG NMOS level=1 VTO=0.45 KP=120e-6 CGSO=1e-10 CGDO=1e-10
.model PMOS_VTG PMOS level=1 VTO=-0.45 KP=40e-6 CGSO=1e-10 CGDO=1e-10
.include /tmp/qujh_delay_chain_scratch/storage_relief_20260725/worktrees/project_mainline_inventory_20260726/outputs/PROJECT_openyield_exact_cell_source/inv/openyield_exact.sp
VDD VDD 0 1.0
VA A 0 PULSE(0 1 0.5n 10p 10p 0.5n 1n)
X1 VDD 0 A Z inv_openyield_exact
Cz Z 0 1f
.tran 1p 2n
.measure tran z_low FIND v(Z) AT=0.8n
.measure tran z_high FIND v(Z) AT=1.4n
.end
