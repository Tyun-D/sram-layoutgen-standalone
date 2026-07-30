* PROJECT_EXPLORATORY_TB
* claim_allowed = engineering_debug_only
* derived from OpenYield upstream reference + current project top interface
* This deck intentionally avoids asserting a final owner-reviewed timing oracle.

.include /tmp/qujh_delay_chain_scratch/storage_relief_20260725/worktrees/project_mainline_inventory_20260726/outputs/M12N2_clean_openyield_sram_top/current_supported_config/openyield_sram_top_v1_16x16.sp

VDD VDD 0 DC 1.0
VSS VSS 0 DC 0

* Guard cycle after startup clamp before any functional interpretation.
VCLK clk 0 PULSE(0 1.0 3n 0.1n 0.1n 5n 10n)
VCSB csb 0 PWL(0n 1.0 8n 1.0 8.1n 0 18n 0 18.1n 1.0 28n 1.0 28.1n 0 40n 0)
VWEB web 0 PWL(0n 1.0 8n 1.0 8.1n 0 18n 0 18.1n 1.0 28n 1.0 28.1n 0 40n 0)

* Conservative exploratory pattern only.
VA0 A0 0 PWL(0n 0 20n 0 20.1n 1.0 40n 1.0)
VA1 A1 0 DC 0
VA2 A2 0 DC 0
VA3 A3 0 DC 0

VDIN0 DIN0 0 PWL(0n 0 8n 0 8.1n 1.0 18n 1.0 18.1n 0 40n 0)
VDIN1 DIN1 0 DC 0
VDIN2 DIN2 0 DC 0
VDIN3 DIN3 0 DC 0
VDIN4 DIN4 0 DC 0
VDIN5 DIN5 0 DC 0
VDIN6 DIN6 0 DC 0
VDIN7 DIN7 0 DC 0
VDIN8 DIN8 0 DC 0
VDIN9 DIN9 0 DC 0
VDIN10 DIN10 0 DC 0
VDIN11 DIN11 0 DC 0
VDIN12 DIN12 0 DC 0
VDIN13 DIN13 0 DC 0
VDIN14 DIN14 0 DC 0
VDIN15 DIN15 0 DC 0

XDUT VDD VSS clk csb web A0 A1 A2 A3 DIN0 DIN1 DIN2 DIN3 DIN4 DIN5 DIN6 DIN7 DIN8 DIN9 DIN10 DIN11 DIN12 DIN13 DIN14 DIN15 SA_Q0 SA_Q1 SA_Q2 SA_Q3 SA_Q4 SA_Q5 SA_Q6 SA_Q7 SA_Q8 SA_Q9 SA_Q10 SA_Q11 SA_Q12 SA_Q13 SA_Q14 SA_Q15 SA_QB0 SA_QB1 SA_QB2 SA_QB3 SA_QB4 SA_QB5 SA_QB6 SA_QB7 SA_QB8 SA_QB9 SA_QB10 SA_QB11 SA_QB12 SA_QB13 SA_QB14 SA_QB15 OPENYIELD_SRAM_TOP_V1

.tran 0.01n 50n
.print tran V(clk) V(csb) V(web) V(A0) V(DIN0) V(SA_Q0) V(SA_QB0)
.end
