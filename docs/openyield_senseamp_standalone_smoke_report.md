# OpenYield SenseAmp Standalone Smoke Report

This report checks that the sense_amp adapter is wired into standalone as an explicit opt-in path while leaving the legacy path unchanged.

## Summary

- standalone.py modified: `True`
- new parameter: `enable_openyield_senseamp_adapter`
- default value: `False`
- legacy_default preserved: `True`
- senseamp_only passed: `True`
- storage_plus_senseamp passed: `True`
- generated fake dout_b: `False`
- routing changed: `False`
- GDS writer changed: `False`
- write_driver changed: `False`
- column_mux changed: `False`
- wordline_driver changed: `False`

## Cases

| case | senseamp_enabled | storage_enabled | generated_gds | sense_amp_count | adapter_strategy | gds |
| --- | --- | --- | --- | --- | --- | --- |
| legacy_default | False | False | True | 2 | single_ended_q_to_dout | E:\njust\keyan\SRAM Compiler_V2\OpenRAM-stable\deliverables\sram_layoutgen_step45_clean\build\openyield_senseamp_standalone_legacy_default\sram_2x16_wpr1_fd45.gds |
| senseamp_only | True | False | True | 2 | single_ended_q_to_dout | E:\njust\keyan\SRAM Compiler_V2\OpenRAM-stable\deliverables\sram_layoutgen_step45_clean\build\openyield_senseamp_standalone_senseamp_only\sram_2x16_wpr1_fd45.gds |
| storage_plus_senseamp | True | True | True | 2 | single_ended_q_to_dout | E:\njust\keyan\SRAM Compiler_V2\OpenRAM-stable\deliverables\sram_layoutgen_step45_clean\build\openyield_senseamp_standalone_storage_plus_senseamp\sram_2x16_wpr1_fd45.gds |

## SenseAmp Mapping

- local macro: `sense_amp`
- local pins: `bl, br, dout, en, vdd, gnd`
- dropped pins: `{'QB': 'dropped_complementary_output'}`
- example placements: `[{'instance_name': 'Xsa_c0', 'macro_name': 'sense_amp', 'col': 0, 'x': 12.0, 'y': 14.257499999999999, 'orientation': 'R0', 'nets': {'vdd': 'vdd', 'gnd': 'gnd', 'en': 'sense_enable', 'bl': 'bl[0]', 'br': 'br[0]', 'dout': 'dout[0]'}, 'dropped_pins': {'QB': 'dropped_complementary_output'}, 'adapter_strategy': 'single_ended_q_to_dout', 'safe_for_physical_mapping': True, 'notes': ('Column-direct sense amp placement plan.',)}, {'instance_name': 'Xsa_c1', 'macro_name': 'sense_amp', 'col': 1, 'x': 12.705, 'y': 14.257499999999999, 'orientation': 'R0', 'nets': {'vdd': 'vdd', 'gnd': 'gnd', 'en': 'sense_enable', 'bl': 'bl[1]', 'br': 'br[1]', 'dout': 'dout[1]'}, 'dropped_pins': {'QB': 'dropped_complementary_output'}, 'adapter_strategy': 'single_ended_q_to_dout', 'safe_for_physical_mapping': True, 'notes': ('Column-direct sense amp placement plan.',)}]`

## Next Step

- Keep the sense_amp adapter opt-in only; do not enable it by default yet.
- Use the same pattern for the next peripheral adapter so the main flow stays easy to audit.
- The next adapter should be column mux or write driver, depending on whether you want to settle data-path source semantics or write-path semantics first.
