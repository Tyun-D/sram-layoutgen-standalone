* OpenYield/current-source exact canonical SPICE for PNAND2_OPENYIELD_EXACT
* authority_level=CURRENT_SOURCE_BOUND_WL_DRIVER_LEAF_EXACT
.model NMOS_VTG NMOS level=1 VTO=0.45 KP=120e-6
.model PMOS_VTG PMOS level=1 VTO=-0.45 KP=40e-6
.subckt pnand2_openyield_exact VDD VSS A B Z
MMP_A Z A VDD VDD PMOS_VTG W=270n L=50n
MMP_B Z B VDD VDD PMOS_VTG W=270n L=50n
MMN_A NINT A Z VSS NMOS_VTG W=180n L=50n
MMN_B VSS B NINT VSS NMOS_VTG W=180n L=50n
.ends pnand2_openyield_exact
.end
