* OpenYield/current-source exact canonical SPICE for INV_OPENYIELD_EXACT
* authority_level=CURRENT_SOURCE_BOUND_OPENRAM_BACKED_EXACT
.model NMOS_VTG NMOS level=1 VTO=0.45 KP=120e-6
.model PMOS_VTG PMOS level=1 VTO=-0.45 KP=40e-6
.subckt inv_openyield_exact VDD VSS A Z
MMP0 Z A VDD VDD PMOS_VTG W=500n L=50n
MMN0 Z A VSS VSS NMOS_VTG W=250n L=50n
.ends inv_openyield_exact
.end
