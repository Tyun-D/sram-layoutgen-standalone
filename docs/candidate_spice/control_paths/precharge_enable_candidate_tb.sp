* PRECHARGE CANDIDATE CONTRACT / SKELETON
* SOURCE-LINKED BUT NOT VALIDATED SPICE
* NOT TIMING PROOF
* NOT PHYSICAL INTEGRATION
* Source-linked logic role: PRE_UNBUF/PRE from gated_clk_buf, rbl_delay, wl_en_bar
* This is a testbench skeleton only; it does not claim transistor completeness.
.include "../gen_delay_inv_candidate.sp"
.param VDD_VALUE=1.0
.temp 25
VDD_SRC vdd 0 {VDD_VALUE}
VCLK gated_clk_buf 0 PULSE(0 {VDD_VALUE} 0 10p 10p 1n 2n)
VRBL rbl_delay 0 PULSE({VDD_VALUE} 0 300p 10p 10p 1n 2n)
VWL wl_en_bar 0 PULSE({VDD_VALUE} 0 600p 10p 10p 1n 2n)
* Placeholder for PRE_UNBUF/PRE candidate recovery from OpenYield PNAND3 + pdrive2_for_pre
* XPRE_UNBUF vdd 0 gated_clk_buf rbl_delay wl_en_bar pre_unbuf pre_unbuf_candidate
* XPRE vdd 0 pre_unbuf PRE pre_driver_candidate
.print tran v(gated_clk_buf) v(rbl_delay) v(wl_en_bar)
.tran 5p 4n
.end
