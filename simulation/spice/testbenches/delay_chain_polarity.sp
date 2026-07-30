.include "/tmp/qujh_delay_chain_scratch/storage_relief_20260725/worktrees/project_mainline_inventory_20260726/simulation/spice/netlists/delay_chain.inc"
.title delay_chain_polarity

VVDD VDD 0 1.0
VVSS VSS 0 0
VA A 0 PULSE(0 1.0 40p 5p 5p 120p 240p)
XDUT VDD VSS A Z delay_chain
.tran 2p 500p
.measure tran z_low MIN v(Z) FROM=0p TO=180p
.measure tran z_high MAX v(Z) FROM=250p TO=460p

.end
