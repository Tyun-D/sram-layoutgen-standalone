* PRECHARGE CANDIDATE CONTRACT / SKELETON
* SOURCE-LINKED BUT NOT VALIDATED SPICE
* NOT TIMING PROOF
* NOT PHYSICAL INTEGRATION
* OpenYield source: precharge_and_write_driver.py / class Precharge
.SUBCKT precharge_candidate_contract VDD ENB BL BLB
* M1: precharge BL to VDD when ENB is low
M_PRE_BL BL ENB VDD VDD PMOS_VTG W={PMOS_WIDTH} L={LCH}
* M2: precharge BLB to VDD when ENB is low
M_PRE_BLB BLB ENB VDD VDD PMOS_VTG W={PMOS_WIDTH} L={LCH}
* M3: equalization transistor between BL and BLB, gate tied to ENB
M_EQ BL ENB BLB VDD PMOS_VTG W={PMOS_WIDTH} L={LCH}
.ENDS precharge_candidate_contract
