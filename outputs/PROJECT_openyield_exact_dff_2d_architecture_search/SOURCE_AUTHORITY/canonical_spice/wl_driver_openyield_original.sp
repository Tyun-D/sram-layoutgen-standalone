* Canonical SPICE expanded from OpenYield original source for WL_DRIVER_OPENYIELD_ORIGINAL
* authority_level=OPENYIELD_ORIGINAL_SOURCE_EXACT
* openyield_commit=1c34428d8b913963c4971d093b1a7c2df97a2509
* source_time_generate_sha=fa5277f078f79d5b43335c2dcd6e364625aa8ad17b7108d323b85e73dfeaae80
.model NMOS_VTG NMOS level=1 VTO=0.45 KP=120e-6 CGSO=1e-10 CGDO=1e-10
.model PMOS_VTG PMOS level=1 VTO=-0.45 KP=40e-6 CGSO=1e-10 CGDO=1e-10
.subckt wl_driver_openyield_original VDD VSS A B WL
MNAND_pnand2_pmos1 NAND_Z A VDD VDD PMOS_VTG W=270n L=50n
MNAND_pnand2_pmos2 NAND_Z B VDD VDD PMOS_VTG W=270n L=50n
MNAND_pnand2_nmos1 NAND_Z B net1 VSS NMOS_VTG W=180n L=50n
MNAND_pnand2_nmos2 net1 A VSS VSS NMOS_VTG W=180n L=50n
MINV_pinv_pmos WL NAND_Z VDD VDD PMOS_VTG W=270n L=50n
MINV_pinv_nmos WL NAND_Z VSS VSS NMOS_VTG W=90n L=50n
.ends wl_driver_openyield_original
.end
