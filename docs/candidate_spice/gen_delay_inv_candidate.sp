* CANDIDATE / PLANNING-ONLY
* NOT VALIDATED SPICE
* NOT TIMING PROOF
* DO NOT CLAIM TIMING CLOSURE
* REQUIRES MANUAL REVIEW, PDK MODEL BINDING, AND CHARACTERIZATION
* Source-visible generator values: NMOS W=0.9e-07, PMOS W=2.7e-07, L=0.05e-6
* These sizes come from OpenYield DelayChain/Pinv source and are not characterized here.

.SUBCKT gen_delay_inv A Z vdd gnd
M_P Z A vdd vdd PMOS_VTG W=2.7e-07 L=0.05e-6
M_N Z A gnd gnd NMOS_VTG W=0.9e-07 L=0.05e-6
.ENDS gen_delay_inv
