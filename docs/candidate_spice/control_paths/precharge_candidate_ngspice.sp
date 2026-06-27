* PRECHARGE CANDIDATE NGSPICE
* SOURCE-LINKED CANDIDATE
* NOT VALIDATED SPICE
* NOT TIMING PROOF
* NOT PHYSICAL INTEGRATION
* Source: /data1/qujh/work/external/OpenYield/sram_compiler/subcircuits/precharge_and_write_driver.py / class Precharge
* ENB polarity inference: active_low (All three devices are PMOS with source/bulk tied to VDD and gate tied to ENB; PMOS turns on when gate is driven low relative to source, so ENB is inferred active-low.)
.subckt precharge_candidate VDD ENB BL BLB
M_PRE_BL BL ENB VDD VDD PMOS_VTG W=2.7e-07 L=5e-08
M_PRE_BLB BLB ENB VDD VDD PMOS_VTG W=2.7e-07 L=5e-08
M_EQ BL ENB BLB VDD PMOS_VTG W=2.7e-07 L=5e-08
.ends precharge_candidate
