* Canonical SPICE expanded from OpenYield original source for PNAND2_OPENYIELD_ORIGINAL
* authority_level=OPENYIELD_ORIGINAL_SOURCE_EXACT
* openyield_commit=1c34428d8b913963c4971d093b1a7c2df97a2509
* source_time_generate_sha=fa5277f078f79d5b43335c2dcd6e364625aa8ad17b7108d323b85e73dfeaae80
.model NMOS_VTG NMOS level=1 VTO=0.45 KP=120e-6 CGSO=1e-10 CGDO=1e-10
.model PMOS_VTG PMOS level=1 VTO=-0.45 KP=40e-6 CGSO=1e-10 CGDO=1e-10
.subckt pnand2_openyield_original VDD VSS A B Z
Mpnand2_pmos1 Z A VDD VDD PMOS_VTG W=270n L=50n
Mpnand2_pmos2 Z B VDD VDD PMOS_VTG W=270n L=50n
Mpnand2_nmos1 Z B net1 VSS NMOS_VTG W=180n L=50n
Mpnand2_nmos2 net1 A VSS VSS NMOS_VTG W=180n L=50n
.ends pnand2_openyield_original
.end
