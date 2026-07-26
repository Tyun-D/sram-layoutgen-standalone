* PRECHARGE TRANSIENT SMOKE
* CANDIDATE / SMOKE-ONLY
* TEMPORARY LOAD/STIMULUS
* NOT FUNCTIONAL PROOF
* NOT TIMING PROOF
* NOT TIMING CLOSURE
.include "/data1/qujh/work/sram_layoutgen_step45_clean/docs/candidate_spice/local_model_include_nom_server.inc"
.include "/data1/qujh/work/sram_layoutgen_step45_clean/docs/candidate_spice/control_paths/precharge_candidate_ngspice.sp"
.param VDD_VALUE=1.0
.param V10='0.1*VDD_VALUE'
.param V90='0.9*VDD_VALUE'
.temp 25
VDD_SRC VDD 0 {VDD_VALUE}
VENB ENB 0 DC {VDD_VALUE} PULSE({VDD_VALUE} 0 200p 10p 10p 1.2n 2.4n)
* Smoke-only bitline load; not representative of full SRAM bitline RC.
CBL BL 0 5f
CBLB BLB 0 5f
.ic V(BL)=0 V(BLB)=0
XPRE VDD ENB BL BLB precharge_candidate
.measure tran smoke_bl_rise trig v(BL) val='V10' rise=1 targ v(BL) val='V90' rise=1
.measure tran smoke_blb_rise trig v(BLB) val='V10' rise=1 targ v(BLB) val='V90' rise=1
.tran 2p 4n
.print tran v(ENB) v(BL) v(BLB)
.end
