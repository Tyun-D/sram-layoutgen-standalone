# Simulation Results Summary

- source_netlist: `outputs/M12N2_clean_openyield_sram_top/current_supported_config/openyield_sram_top_v1_16x16.sp`
- formal_spice_basis: `authoritative clean-top extracted netlist`, not planning-only candidate SPICE

## Level 3 SPICE Results

- pnand2_inversion / PNAND2: `PASS` | z_final=1.840987e-05
- pnand3_inversion / PNAND3: `PASS` | z_final=4.141989e-05
- and2_truth / AND2: `PASS` | z_final=0.9999978
- and3_truth / AND3: `PASS` | z_final=0.9999978
- pdrive_buffer / pdrive: `PASS` | z_low=-0.02222769 z_high=1.020346
- wl_pdrive_buffer / wl_pdrive: `PASS` | z_low=-0.05707977 z_high=1.069538
- pdrive2_for_pre_buffer / pdrive2_for_pre: `PASS` | z_low=-0.05707977 z_high=1.069538
- delay_chain_polarity / delay_chain: `FAIL` | z_low=0.9997884 z_high=1.010554
- dff_capture / DFF: `PASS` | q_first=-8.463124e-05 q_second=1.000024
- dff_buf_capture / DFF_BUF: `PASS` | q_first=9.977353e-06 qb_first=0.9999867 q_second=0.9999971 qb_second=1.314608e-05
