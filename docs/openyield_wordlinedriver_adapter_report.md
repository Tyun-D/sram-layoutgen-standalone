# OpenYield WORDLINEDRIVER Adapter Audit

This is a read-only semantic audit plus a limited placement plan. It does not modify standalone.py, routing, or the GDS writer.

## Summary

- OpenYield module: `WORDLINEDRIVER`
- local macro: `gen_wl_driver`
- power status: `vdd_gnd_metadata_present`
- safe_for_physical_mapping: `True`
- safe_for_shared_rail: `False`
- can enter limited placement: `True`
- wordline_driver_pin_labels_verified: `True`
- wordline_driver_pin_report_consistent: `True`
- semantic confirmation: `confirmed_active_high`
- standalone modified: `False`
- routing changed: `False`
- GDS writer changed: `False`
- wordline_driver changed: `False`

## OpenYield Source Audit

- topology: `nand2_plus_inverter`
- A source: `decoder_input`
- B source: `wordline_enable`
- Z sink: `wl`
- B polarity: `high_active`
- evidence: `WORDLINEDRIVER.NAME and NODES are declared in sram_compiler/subcircuits/wordline_driver.py.; Driver chain is NAND2 -> inverter, so Z is asserted only when A and B are both high.; testbench create_wl_driver passes decoder_enable to A and WL_EN to B.; WL row output is passed as the Z sink in the testbench instance connections.; Testbench connects decoder_enable to A and WL_EN to B.`

## OpenYield Contract

- canonical module: `wl_driver`
- role: `wordline_driver`
- pin list: `VDD, VSS, A, B, Z`
- canonical pins: `vdd, gnd, decoder_input, wordline_enable, wl`
- power pins: `{'VDD': 'vdd', 'VSS': 'gnd'}`

## Local Macro

- GDS: `E:\njust\keyan\SRAM Compiler_V2\OpenRAM-stable\deliverables\sram_layoutgen_step45_clean\technology\freepdk45\gds_lib\gen_wl_driver.gds`
- SPICE: `None`
- GDS bbox: `{'x0': 0.0, 'y0': 0.0, 'x1': 1.5499999999999996, 'y1': 1.5649999999999997}`
- primary GDS labels: `none`
- primary GDS label count: `0`
- pin audit GDS: `technology\freepdk45\gds_lib\openram_replacements\gen_wl_driver.gds`
- pin audit labels: `Z, A, B, gnd, vdd, G, S, D, G, S, D, G, S, S, S, S, D, A, Z, gnd, vdd, G, S, D, G, S, S, S, S, D, Z, gnd, vdd, A, B`
- pin audit label count: `35`
- SPICE pins: ``

## Pin Mapping

| OpenYield pin | Local pin | Canonical signal | Shape source | Semantic status | Contract pin present | Required |
| --- | --- | --- | --- | --- | --- | --- |
| VDD | vdd | vdd | label_plus_shape | confirmed | True | True |
| VSS | gnd | gnd | label_plus_shape | confirmed | True | True |
| A | decoder_input | decoder_input | label_plus_shape | confirmed | True | True |
| B | wordline_enable | wordline_enable | label_plus_shape | confirmed_active_high | True | True |
| Z | wl | wl | label_plus_shape | confirmed | True | True |

## Limited Placement Plan

- rows: `4`
- origin: `(0.0, 0.0)`
- pitch_y: `1.565`
- row orientation policy: `all_r0`
- can enter limited placement: `True`
- wordline_driver_pin_labels_verified: `True`
- wordline_driver_pin_report_consistent: `True`

## Notes

- OpenYield WORDLINEDRIVER is a NAND2 followed by an inverter.
- A maps to decoder_input, B maps to wordline_enable, and Z is the final wl output.
- The enable is active-high because the NAND stage requires both A and B to be asserted before the output inverter drives WL high.
- Shared rail remains disabled until a separate rail continuity proof exists.
- This audit is read-only and does not modify standalone, routing, or GDS writer code.
- The OpenYield source chain confirms a NAND2 followed by an inverter, so B is active-high and Z is the final WL output.
