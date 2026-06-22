* CANDIDATE / PLANNING-ONLY
* NOT VALIDATED SPICE
* NOT TIMING PROOF
* DO NOT CLAIM TIMING CLOSURE
* REQUIRES MANUAL REVIEW, PDK MODEL BINDING, AND CHARACTERIZATION
* Planning-only measure template. Thresholds remain TBD.
*.measure tran chain_delay_rbl_to_rbl_delay TRIG v(rbl) VAL=__TBD_THRESH__ RISE=1 TARG v(rbl_delay) VAL=__TBD_THRESH__ RISE=1
*.measure tran input_slew_at_rbl TRIG v(rbl) VAL=__TBD_SLEW_LOW__ RISE=1 TARG v(rbl) VAL=__TBD_SLEW_HIGH__ RISE=1
*.measure tran output_slew_at_rbl_delay TRIG v(rbl_delay) VAL=__TBD_SLEW_LOW__ RISE=1 TARG v(rbl_delay) VAL=__TBD_SLEW_HIGH__ RISE=1
*.measure tran pulse_width_at_rbl_delay TRIG v(rbl_delay) VAL=__TBD_THRESH__ RISE=1 TARG v(rbl_delay) VAL=__TBD_THRESH__ FALL=1
*.measure tran stage_midpoint_delay_rbl_to_dout_5 TRIG v(rbl) VAL=__TBD_THRESH__ RISE=1 TARG v(dout_5) VAL=__TBD_THRESH__ RISE=1
