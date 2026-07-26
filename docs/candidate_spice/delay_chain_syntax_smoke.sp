* CANDIDATE / PLANNING-ONLY
* NOT VALIDATED SPICE
* NOT TIMING PROOF
* DO NOT CLAIM TIMING CLOSURE
* REQUIRES MANUAL REVIEW, PDK MODEL BINDING, AND CHARACTERIZATION
* Syntax smoke only. Temporary VDD/TEMP are for parse/elaboration checks, not project signoff.
.include "E:/njust/keyan/SRAM Compiler_V2/OpenRAM-stable/deliverables/sram_layoutgen_step45_clean/docs/candidate_spice/local_model_include_nom.inc"
.include "gen_delay_inv_candidate.sp"
.include "delay_chain_measure.inc"
.param VDD_VALUE=1.0
.param TEMP_VALUE=25
.param RBL_INPUT_SLEW=1n
.temp 25
VDD_SRC vdd 0 1.0
VIN rbl 0 PULSE(0 1.0 0 10p 10p 200p 400p)
Xdinv0 rbl dout_1 vdd 0 gen_delay_inv
Xdload_0_0 dout_1 n_0_0 vdd 0 gen_delay_inv
.tran 1p 2n
.end
