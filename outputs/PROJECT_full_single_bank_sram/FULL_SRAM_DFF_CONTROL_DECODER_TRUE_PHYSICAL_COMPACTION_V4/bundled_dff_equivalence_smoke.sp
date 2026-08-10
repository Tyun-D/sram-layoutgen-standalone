.include /tmp/qujh_delay_chain_scratch/storage_relief_20260725/worktrees/project_mainline_inventory_20260726/technology/freepdk45/sp_lib/dff.sp
.model NMOS_VTG nmos level=1 vto=0.45 kp=120u lambda=0.05
.model PMOS_VTG pmos level=1 vto=-0.45 kp=50u lambda=0.05
VDD vdd 0 1.0
VGND gnd 0 0
VD D 0 PULSE(0 1 0.2n 20p 20p 1.4n 2.8n)
VCLK clk 0 PULSE(0 1 0.8n 20p 20p 0.8n 1.6n)
X0 D Q clk vdd gnd dff
.tran 5p 6n
.control
run
meas tran q_after_first FIND v(Q) AT=1.25n
meas tran q_after_second FIND v(Q) AT=2.85n
write bundled_dff_equivalence_smoke.raw
quit
.endc
.end
