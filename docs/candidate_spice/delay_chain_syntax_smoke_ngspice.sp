* SERVER NGSPICE SYNTAX SMOKE
* CANDIDATE / PLANNING-ONLY
* NOT VALIDATED SPICE
* NOT TIMING PROOF
* DO NOT CLAIM TIMING CLOSURE
* Temporary sources and transient settings are parse/startup-only, not formal PVT.

.include "local_model_include_nom_server.inc"
.include "gen_delay_inv_candidate.sp"

.param VDD_VALUE=1.0
.temp 25

VDD_SRC vdd 0 {VDD_VALUE}
VIN rbl 0 DC 0 PULSE(0 {VDD_VALUE} 0 10p 10p 100p 200p)

Xdinv0 rbl dout_1 vdd 0 gen_delay_inv
Xdload_0_0 dout_1 n_0_0 vdd 0 gen_delay_inv
Xdload_0_1 dout_1 n_0_1 vdd 0 gen_delay_inv
Xdload_0_2 dout_1 n_0_2 vdd 0 gen_delay_inv
Xdload_0_3 dout_1 n_0_3 vdd 0 gen_delay_inv

Xdinv1 dout_1 dout_2 vdd 0 gen_delay_inv
Xdload_1_0 dout_2 n_1_0 vdd 0 gen_delay_inv
Xdload_1_1 dout_2 n_1_1 vdd 0 gen_delay_inv
Xdload_1_2 dout_2 n_1_2 vdd 0 gen_delay_inv
Xdload_1_3 dout_2 n_1_3 vdd 0 gen_delay_inv

Xdinv2 dout_2 dout_3 vdd 0 gen_delay_inv
Xdload_2_0 dout_3 n_2_0 vdd 0 gen_delay_inv
Xdload_2_1 dout_3 n_2_1 vdd 0 gen_delay_inv
Xdload_2_2 dout_3 n_2_2 vdd 0 gen_delay_inv
Xdload_2_3 dout_3 n_2_3 vdd 0 gen_delay_inv

Xdinv3 dout_3 dout_4 vdd 0 gen_delay_inv
Xdload_3_0 dout_4 n_3_0 vdd 0 gen_delay_inv
Xdload_3_1 dout_4 n_3_1 vdd 0 gen_delay_inv
Xdload_3_2 dout_4 n_3_2 vdd 0 gen_delay_inv
Xdload_3_3 dout_4 n_3_3 vdd 0 gen_delay_inv

Xdinv4 dout_4 dout_5 vdd 0 gen_delay_inv
Xdload_4_0 dout_5 n_4_0 vdd 0 gen_delay_inv
Xdload_4_1 dout_5 n_4_1 vdd 0 gen_delay_inv
Xdload_4_2 dout_5 n_4_2 vdd 0 gen_delay_inv
Xdload_4_3 dout_5 n_4_3 vdd 0 gen_delay_inv

Xdinv5 dout_5 dout_6 vdd 0 gen_delay_inv
Xdload_5_0 dout_6 n_5_0 vdd 0 gen_delay_inv
Xdload_5_1 dout_6 n_5_1 vdd 0 gen_delay_inv
Xdload_5_2 dout_6 n_5_2 vdd 0 gen_delay_inv
Xdload_5_3 dout_6 n_5_3 vdd 0 gen_delay_inv

Xdinv6 dout_6 dout_7 vdd 0 gen_delay_inv
Xdload_6_0 dout_7 n_6_0 vdd 0 gen_delay_inv
Xdload_6_1 dout_7 n_6_1 vdd 0 gen_delay_inv
Xdload_6_2 dout_7 n_6_2 vdd 0 gen_delay_inv
Xdload_6_3 dout_7 n_6_3 vdd 0 gen_delay_inv

Xdinv7 dout_7 dout_8 vdd 0 gen_delay_inv
Xdload_7_0 dout_8 n_7_0 vdd 0 gen_delay_inv
Xdload_7_1 dout_8 n_7_1 vdd 0 gen_delay_inv
Xdload_7_2 dout_8 n_7_2 vdd 0 gen_delay_inv
Xdload_7_3 dout_8 n_7_3 vdd 0 gen_delay_inv

Xdinv8 dout_8 rbl_delay vdd 0 gen_delay_inv
Xdload_8_0 rbl_delay n_8_0 vdd 0 gen_delay_inv
Xdload_8_1 rbl_delay n_8_1 vdd 0 gen_delay_inv
Xdload_8_2 rbl_delay n_8_2 vdd 0 gen_delay_inv
Xdload_8_3 rbl_delay n_8_3 vdd 0 gen_delay_inv

.tran 1p 400p
.print tran v(rbl) v(rbl_delay)
.end
