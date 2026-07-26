# OpenYield WRITEDRIVER Adapter Audit

- OpenYield module: `WRITEDRIVER`
- local macro: `write_driver`
- power status: `vdd_gnd_metadata_present`
- safe_for_physical_mapping: `True`
- safe_for_shared_rail: `False`
- can enter limited placement: `True`
- semantic coexistence with column mux / sense amp / storage array: `True`
- standalone modified: `False`
- routing changed: `False`
- GDS writer changed: `False`
- write_driver changed: `False`

## OpenYield Contract

- canonical module: `write_driver`
- role: `write_driver`
- pin list: `VDD, VSS, EN, DIN, BL, BLB`
- canonical pins: `vdd, gnd, write_enable, din, bl, br`
- power pins: `{'VDD': 'vdd', 'VSS': 'gnd'}`
- semantic coexistence reason: `adapter-only metadata and placement planning do not change routing or shared rails.`

## Local Macro

- GDS: `E:\njust\keyan\SRAM Compiler_V2\OpenRAM-stable\deliverables\sram_layoutgen_step45_clean\technology\freepdk45\gds_lib\write_driver.gds`
- SPICE: `E:\njust\keyan\SRAM Compiler_V2\OpenRAM-stable\deliverables\sram_layoutgen_step45_clean\technology\freepdk45\sp_lib\write_driver.sp`
- GDS bbox: `{'x0': -0.0999999999999994, 'y0': 0.0, 'x1': 0.7399999999999956, 'y1': 4.174999999999975}`
- GDS labels: `en, din, vdd, br, bl, gnd`
- SPICE pins: `din, bl, br, en, vdd, gnd`

## Pin Mapping

| OpenYield pin | Local pin | Canonical signal | Shape source | Contract pin present | Required |
| --- | --- | --- | --- | --- | --- |
| VDD | vdd | vdd | label_plus_shape | True | True |
| VSS | gnd | gnd | label_plus_shape | True | True |
| EN | write_enable | write_enable | label_plus_shape | True | True |
| DIN | din | din | label_plus_shape | True | True |
| BL | bl | bl | label_plus_shape | True | True |
| BLB | br | br | label_plus_shape | True | True |

## Notes

- OpenYield WRITEDRIVER exposes only DIN and EN externally; internal DINB/ENB generation stays inside the SPICE macro.
- BL/BLB map to the local bl/br pins without a routing rewrite.
- Shared rail remains disabled until a separate rail continuity proof exists.
- This audit is read-only and does not modify standalone, routing, or GDS writer code.
