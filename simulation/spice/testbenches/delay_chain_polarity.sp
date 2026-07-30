.include "/tmp/qujh_delay_chain_scratch/storage_relief_20260725/worktrees/project_mainline_inventory_20260726/simulation/spice/netlists/delay_chain.inc"
.title delay_chain_polarity

VVDD VDD 0 1.0
VVSS VSS 0 0
VA A 0 PULSE(0 1.0 40p 5p 5p 120p 240p)
XDUT VDD VSS A Z delay_chain
.tran 1p 700p
.measure tran t_in_rise WHEN v(A)=0.5 RISE=1
.measure tran t_out_fall WHEN v(Z)=0.5 FALL=1
.measure tran tpd_rise_fall PARAM='t_out_fall-t_in_rise'
.measure tran t_in_fall WHEN v(A)=0.5 FALL=1
.measure tran t_out_rise WHEN v(Z)=0.5 RISE=1
.measure tran tpd_fall_rise PARAM='t_out_rise-t_in_fall'
.measure tran z_after_first_rise FIND v(Z) AT=300p
.measure tran z_after_first_fall FIND v(Z) AT=430p
.measure tran z_min MIN v(Z) FROM=0p TO=700p
.measure tran z_max MAX v(Z) FROM=0p TO=700p

.end
