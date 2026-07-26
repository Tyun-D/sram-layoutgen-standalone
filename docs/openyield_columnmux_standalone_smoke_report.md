# OpenYield ColumnMux Standalone Smoke Report

- case: `4x32_wpr2`
- standalone modified: `True`
- new parameter: `enable_openyield_columnmux_adapter` default `False`
- all modes generated GDS: `True`
- alias GDS vdd label visible: `True`
- legacy_default kept legacy path: `True`
- columnmux_only uses repaired alias: `True`
- senseamp_plus_columnmux pairs: `True`
- storage_plus_senseamp_plus_columnmux uses alternating_mx: `True`
- routing changed: `False`
- GDS writer changed: `False`
- write_driver changed: `False`
- wordline_driver changed: `False`
- shared rail enabled: `False`
- next step recommendation: `proceed_to_write_driver_opt_in_after_columnmux_smoke`

## Mode Summary

| mode | GDS | bbox (W x H) | area | column mux count | local macro | repaired alias | vdd label | safe phys | safe shared | routing changed | GDS writer changed | storage enabled | storage policy | cross-row risk |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| legacy_default | True | 19.3925 x 50.7050 | 983.2967 | 8 | gen_col_mux | False | True | False | False | False | False | False | all_r0 | None |
| columnmux_only | True | 19.3925 x 50.7050 | 983.2967 | 8 | gen_col_mux_vdd_labeled | True | True | True | False | False | False | False | all_r0 | None |
| senseamp_plus_columnmux | True | 19.3925 x 50.7050 | 983.2967 | 8 | gen_col_mux_vdd_labeled | True | True | True | False | False | False | False | all_r0 | None |
| storage_plus_senseamp_plus_columnmux | True | 21.2925 x 50.7050 | 1079.6362 | 8 | gen_col_mux_vdd_labeled | True | True | True | False | False | False | True | alternating_mx | False |

## Alias Audit

- repaired candidate GDS: `E:\njust\keyan\SRAM Compiler_V2\OpenRAM-stable\deliverables\sram_layoutgen_step45_clean\technology\freepdk45\gds_lib\openyield_repaired\gen_col_mux_vdd_labeled.gds`
- vdd label present: `True`
- polygon count unchanged: `True`
- text count delta: `1`
- replacement_macros untouched: `True`
