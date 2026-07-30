.include /data1/qujh/work/external/OpenYield/tran_models/models_TT.spice

.subckt PNAND3 VDD VSS A B C Z
Mpnand3_pmos1 Z A VDD VDD PMOS_VTG l=5e-08 w=2.7e-07
Mpnand3_pmos2 Z B VDD VDD PMOS_VTG l=5e-08 w=2.7e-07
Mpnand3_pmos3 Z C VDD VDD PMOS_VTG l=5e-08 w=2.7e-07
Mpnand3_nmos1 Z A net1 VSS NMOS_VTG l=5e-08 w=1.8e-07
Mpnand3_nmos2 net1 B net2 VSS NMOS_VTG l=5e-08 w=1.8e-07
Mpnand3_nmos3 net2 C VSS VSS NMOS_VTG l=5e-08 w=1.8e-07
.ends PNAND3
