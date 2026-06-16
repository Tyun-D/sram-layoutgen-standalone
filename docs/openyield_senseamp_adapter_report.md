# OpenYield SenseAmp Architecture Adapter Report

This Step 5.1 report is read-only. It does not modify placement, routing, GDS writer, hardcell GDS, or OpenYield source.

## Inputs

- openyield_root: `E:\njust\keyan\SRAM Compiler_V2\OpenRAM-stable\third_party\OpenYield`
- contracts: `E:\njust\keyan\SRAM Compiler_V2\OpenRAM-stable\deliverables\sram_layoutgen_step45_clean\docs\openyield_module_contracts.json`
- tech_dir: `E:\njust\keyan\SRAM Compiler_V2\OpenRAM-stable\deliverables\sram_layoutgen_step45_clean\technology\freepdk45`
- local_spice: `E:\njust\keyan\SRAM Compiler_V2\OpenRAM-stable\deliverables\sram_layoutgen_step45_clean\technology\freepdk45\sp_lib\sense_amp.sp`
- local_gds: `E:\njust\keyan\SRAM Compiler_V2\OpenRAM-stable\deliverables\sram_layoutgen_step45_clean\technology\freepdk45\gds_lib\sense_amp.gds`

## Pin Lists

- OpenYield SENSEAMP pins: `VDD, VSS, EN, IN, INB, Q, QB`
- local sense_amp SPICE pins: `bl, br, dout, en, vdd, gnd`
- local sense_amp GDS label-backed canonical pins: `vdd, gnd, sense_enable, bl, br, dout`

## Pin Adaptation

| OpenYield pin | Local pin | Canonical signal | Type | Required | Notes |
| --- | --- | --- | --- | --- | --- |
| VDD | vdd | vdd | direct_physical_pin | True | - |
| VSS | gnd | gnd | direct_physical_pin | True | - |
| EN | en | sense_enable | direct_physical_pin | True | - |
| IN | bl | bl | direct_physical_pin | True | - |
| INB | br | br | direct_physical_pin | True | - |
| Q | dout | dout | direct_physical_pin | True | - |
| QB | - | dout_b | dropped_complementary_output | False | Local sense_amp has no proven dout_b/QB physical pin.; Do not add a fake layout pin.; QB is treated as observation-only for the current physical readout path. |

## Q/QB Findings

- Q -> dout established: `True`
- QB -> dout_b established: `False`
- OpenYield QB required by downstream logic: `False`
- QB instance output references: `2`
- QB observation/testbench references: `6`
- Q-only output path examples: `1`

OpenYield names SENSEAMP.QB nets, but the scanned physical output path feeds OUT from SA_Q. SA_QB appears as a senseamp output net and in testbench observation/initialization, not as a required local GDS output pin.

## Adapter Decision

- adapter strategy: `single_ended_q_to_dout`
- safe for physical mapping: `True`
- requires netlist rewrite: `True`
- requires layout pin: `False`
- requires layout change: `False`
- can enter sense_amp placement: `True`

## Source Scan Summary

- source scan hits: `102`
- QB hits: `70`
- QB downstream logic hits: `0`

### Representative Examples

#### Q-only output path
- `sram_compiler/testbenches/sram_6t_core_testbench.py:441` 'VDD', 'VSS', f'SA_Q{target_col}', 'S_EN', 'OUT', 'OUT_B'

#### QB instance output
- `sram_compiler/testbenches/sram_6t_core_testbench.py:576` f'SA_Q{col}', f'SA_QB{col}',  # Outputs
- `sram_compiler/testbenches/sram_6t_core_testbench.py:588` f'SA_Q{col}', f'SA_QB{col}',  # Outputs

#### QB observation/testbench
- `sram_compiler/testbenches/sram_6t_core_MC_testbench.py:132` init_cond[f'SA_QB{col}'] = self.vdd @ u_V
- `sram_compiler/testbenches/sram_6t_core_MC_testbench.py:235` f'V(SA_QB{self.target_col // self.mux_in})' + \
- `sram_compiler/testbenches/sram_6t_core_MC_testbench.py:329` init_cond[f'SA_QB{col}'] = self.vdd @ u_V
- `sram_compiler/testbenches/sram_6t_core_MC_testbench.py:365` f'V(SA_QB{self.target_col // self.mux_in})\n'
- `sram_compiler/testbenches/sram_6t_core_MC_testbench.py:774` f'V(SA_QB{target_col})',
- `sram_compiler/testbenches/sram_6t_core_MC_testbench.py:802` # f'V(SA_QB{target_col})',

#### QB downstream

- none

## Conclusions

- OpenYield SENSEAMP uses pins VDD, VSS, EN, IN, INB, Q, QB.
- Local sense_amp SPICE/GDS exposes bl, br, dout, en, vdd, gnd and has no proven dout_b/QB pin.
- Q -> dout is established by local GDS label plus shape audit.
- QB -> dout_b is not established and must not be forced.
- QB appears observation/testbench-oriented for the current readout path; the single-ended Q -> dout adapter is acceptable.
- Recommended adapter strategy: single_ended_q_to_dout.
- Can enter sense_amp placement with this adapter: True.

## Next Step

- Proceed to sense_amp placement only with the architecture adapter active.
- Keep QB as unsupported/dropped unless a later OpenYield architecture path proves it feeds required physical logic.
- After sense_amp, audit write_driver and then column mux power metadata before broader peripheral placement.
