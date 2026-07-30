.include /data1/qujh/work/external/OpenYield/tran_models/models_TT.spice

.subckt PINV1 VDD VSS A Z
Mpinv_pmos Z A VDD VDD PMOS_VTG l=5e-08 w=5e-07
Mpinv_nmos Z A VSS VSS NMOS_VTG l=5e-08 w=2.5e-07
.ends PINV1

.subckt delay_chain VDD VSS in out
Xdinv0 VDD VSS in dout_1 PINV1
Xdload_0_0 VDD VSS dout_1 n_0_0 PINV1
Xdload_0_1 VDD VSS dout_1 n_0_1 PINV1
Xdload_0_2 VDD VSS dout_1 n_0_2 PINV1
Xdload_0_3 VDD VSS dout_1 n_0_3 PINV1
Xdinv1 VDD VSS dout_1 dout_2 PINV1
Xdload_1_0 VDD VSS dout_2 n_1_0 PINV1
Xdload_1_1 VDD VSS dout_2 n_1_1 PINV1
Xdload_1_2 VDD VSS dout_2 n_1_2 PINV1
Xdload_1_3 VDD VSS dout_2 n_1_3 PINV1
Xdinv2 VDD VSS dout_2 dout_3 PINV1
Xdload_2_0 VDD VSS dout_3 n_2_0 PINV1
Xdload_2_1 VDD VSS dout_3 n_2_1 PINV1
Xdload_2_2 VDD VSS dout_3 n_2_2 PINV1
Xdload_2_3 VDD VSS dout_3 n_2_3 PINV1
Xdinv3 VDD VSS dout_3 dout_4 PINV1
Xdload_3_0 VDD VSS dout_4 n_3_0 PINV1
Xdload_3_1 VDD VSS dout_4 n_3_1 PINV1
Xdload_3_2 VDD VSS dout_4 n_3_2 PINV1
Xdload_3_3 VDD VSS dout_4 n_3_3 PINV1
Xdinv4 VDD VSS dout_4 dout_5 PINV1
Xdload_4_0 VDD VSS dout_5 n_4_0 PINV1
Xdload_4_1 VDD VSS dout_5 n_4_1 PINV1
Xdload_4_2 VDD VSS dout_5 n_4_2 PINV1
Xdload_4_3 VDD VSS dout_5 n_4_3 PINV1
Xdinv5 VDD VSS dout_5 dout_6 PINV1
Xdload_5_0 VDD VSS dout_6 n_5_0 PINV1
Xdload_5_1 VDD VSS dout_6 n_5_1 PINV1
Xdload_5_2 VDD VSS dout_6 n_5_2 PINV1
Xdload_5_3 VDD VSS dout_6 n_5_3 PINV1
Xdinv6 VDD VSS dout_6 dout_7 PINV1
Xdload_6_0 VDD VSS dout_7 n_6_0 PINV1
Xdload_6_1 VDD VSS dout_7 n_6_1 PINV1
Xdload_6_2 VDD VSS dout_7 n_6_2 PINV1
Xdload_6_3 VDD VSS dout_7 n_6_3 PINV1
Xdinv7 VDD VSS dout_7 dout_8 PINV1
Xdload_7_0 VDD VSS dout_8 n_7_0 PINV1
Xdload_7_1 VDD VSS dout_8 n_7_1 PINV1
Xdload_7_2 VDD VSS dout_8 n_7_2 PINV1
Xdload_7_3 VDD VSS dout_8 n_7_3 PINV1
Xdinv8 VDD VSS dout_8 out PINV1
Xdload_8_0 VDD VSS out n_8_0 PINV1
Xdload_8_1 VDD VSS out n_8_1 PINV1
Xdload_8_2 VDD VSS out n_8_2 PINV1
Xdload_8_3 VDD VSS out n_8_3 PINV1
.ends delay_chain
