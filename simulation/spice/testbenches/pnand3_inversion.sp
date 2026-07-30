.include "/tmp/qujh_delay_chain_scratch/storage_relief_20260725/worktrees/project_mainline_inventory_20260726/simulation/spice/netlists/PNAND3.inc"
.title pnand3_inversion

VVDD VDD 0 1.0
VVSS VSS 0 0
VA A 0 1.0
VB B 0 1.0
VC C 0 1.0
XDUT VDD VSS A B C Z PNAND3
.tran 2p 400p
.measure tran z_final FIND v(Z) AT=350p
.measure tran z_max MAX v(Z)
.measure tran z_min MIN v(Z)

.end
