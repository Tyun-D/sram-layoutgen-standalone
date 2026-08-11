* Canonical SPICE expanded from OpenYield original source for INV_OPENYIELD_ORIGINAL
* authority_level=OPENYIELD_ORIGINAL_SOURCE_EXACT
* openyield_commit=1c34428d8b913963c4971d093b1a7c2df97a2509
* source_time_generate_sha=fa5277f078f79d5b43335c2dcd6e364625aa8ad17b7108d323b85e73dfeaae80
.model NMOS_VTG NMOS level=1 VTO=0.45 KP=120e-6 CGSO=1e-10 CGDO=1e-10
.model PMOS_VTG PMOS level=1 VTO=-0.45 KP=40e-6 CGSO=1e-10 CGDO=1e-10
.subckt inv_openyield_original VDD VSS A Z
Mpinv_pmos Z A VDD VDD PMOS_VTG W=500n L=50n
Mpinv_nmos Z A VSS VSS NMOS_VTG W=250n L=50n
.ends inv_openyield_original
.end
