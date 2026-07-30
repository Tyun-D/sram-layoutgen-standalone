.include /data1/qujh/work/external/OpenYield/tran_models/models_TT.spice

.subckt PINV1 VDD VSS A Z
Mpinv_pmos Z A VDD VDD PMOS_VTG l=5e-08 w=5e-07
Mpinv_nmos Z A VSS VSS NMOS_VTG l=5e-08 w=2.5e-07
.ends PINV1

.subckt PINV2 VDD VSS A Z
Mpinv_pmos Z A VDD VDD PMOS_VTG l=5e-08 w=8.1e-07
Mpinv_nmos Z A VSS VSS NMOS_VTG l=5e-08 w=2.7e-07
.ends PINV2

.subckt PINV3 VDD VSS A Z
Mpinv_pmos Z A VDD VDD PMOS_VTG l=5e-08 w=2.43e-06
Mpinv_nmos Z A VSS VSS NMOS_VTG l=5e-08 w=9.1e-07
.ends PINV3

.subckt PINV4 VDD VSS A Z
Mpinv_pmos Z A VDD VDD PMOS_VTG l=5e-08 w=7.29e-06
Mpinv_nmos Z A VSS VSS NMOS_VTG l=5e-08 w=2.43e-06
.ends PINV4

.subckt pdrive VDD VSS A Z
Xbuf_inv1 VDD VSS A zb1_node PINV1
Xbuf_inv2 VDD VSS zb1_node zb2_node PINV2
Xbuf_inv3 VDD VSS zb2_node zb3_node PINV3
Xbuf_inv4 VDD VSS zb3_node Z PINV4
.ends pdrive
