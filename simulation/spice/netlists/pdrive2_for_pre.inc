.include /data1/qujh/work/external/OpenYield/tran_models/models_TT.spice

.subckt PINV1 VDD VSS A Z
Mpinv_pmos Z A VDD VDD PMOS_VTG l=5e-08 w=5e-07
Mpinv_nmos Z A VSS VSS NMOS_VTG l=5e-08 w=2.5e-07
.ends PINV1

.subckt PINV2 VDD VSS A Z
Mpinv_pmos Z A VDD VDD PMOS_VTG l=5e-08 w=8.1e-07
Mpinv_nmos Z A VSS VSS NMOS_VTG l=5e-08 w=2.7e-07
.ends PINV2

.subckt pdrive2_for_pre VDD VSS A Z
Xbuf_inv1 VDD VSS A zb1_node PINV1
Xbuf_inv2 VDD VSS zb1_node Z PINV2
.ends pdrive2_for_pre
