.include "/tmp/qujh_delay_chain_scratch/storage_relief_20260725/worktrees/project_mainline_inventory_20260726/simulation/spice/netlists/DFF.inc"
.title dff_capture

VVDD VDD 0 1.0
VVSS VSS 0 0
VCLK CLK 0 PULSE(0 1.0 20p 5p 5p 80p 160p)
VD D 0 PWL(0p 0 70p 0 90p 1.0 230p 1.0 250p 0)
XDUT VDD VSS D Q CLK DFF
.tran 2p 420p
.measure tran q_first FIND v(Q) AT=150p
.measure tran q_second FIND v(Q) AT=310p

.end
