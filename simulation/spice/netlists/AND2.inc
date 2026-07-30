.include /data1/qujh/work/external/OpenYield/tran_models/models_TT.spice

.subckt PNAND2 VDD VSS A B Z
Mpnand2_pmos1 Z A VDD VDD PMOS_VTG l=5e-08 w=2.7e-07
Mpnand2_pmos2 Z B VDD VDD PMOS_VTG l=5e-08 w=2.7e-07
Mpnand2_nmos1 Z B net1 VSS NMOS_VTG l=5e-08 w=1.8e-07
Mpnand2_nmos2 net1 A VSS VSS NMOS_VTG l=5e-08 w=1.8e-07
.ends PNAND2

.subckt PINV VDD VSS A Z
Mpinv_pmos Z A VDD VDD PMOS_VTG l=5e-08 w=2.7e-07
Mpinv_nmos Z A VSS VSS NMOS_VTG l=5e-08 w=9e-08
.ends PINV

.subckt AND2 VDD VSS A B Z
XPNAND3 VDD VSS A B zb_int PNAND2
XPINV VDD VSS zb_int Z PINV
.ends AND2
