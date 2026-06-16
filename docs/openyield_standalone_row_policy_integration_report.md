# OpenYield Standalone Row Policy Integration Report

This report checks that the standalone opt-in storage path now accepts an explicit row orientation policy while keeping the default legacy path unchanged.

## Summary

- standalone.py modified: `True`
- new parameter name: `openyield_storage_row_orientation_policy`
- default value: `all_r0`
- supported policies: `['all_r0', 'alternating_mx']`
- default legacy path preserved: `True`
- all_r0 path ok: `True`
- alternating_mx path ok: `True`
- peripherals old path preserved: `True`
- routing unchanged: `True`
- GDS writer unchanged: `True`
- shared rail merge unchanged: `True`

## Standalone Cases

| case | enabled | policy | cross_row_power_short_risk | generated_gds | gds |
| --- | --- | --- | --- | --- | --- |
| legacy_default | False | all_r0 | None | True | E:\njust\keyan\SRAM Compiler_V2\OpenRAM-stable\deliverables\sram_layoutgen_step45_clean\build\openyield_standalone_row_policy_legacy_default\sram_2x16_wpr1_fd45.gds |
| openyield_all_r0 | True | all_r0 | True | True | E:\njust\keyan\SRAM Compiler_V2\OpenRAM-stable\deliverables\sram_layoutgen_step45_clean\build\openyield_standalone_row_policy_openyield_all_r0\sram_2x16_wpr1_fd45.gds |
| openyield_alternating_mx | True | alternating_mx | False | True | E:\njust\keyan\SRAM Compiler_V2\OpenRAM-stable\deliverables\sram_layoutgen_step45_clean\build\openyield_standalone_row_policy_openyield_alternating_mx\sram_2x16_wpr1_fd45.gds |

## Storage Array Mirror Audit

| case | array | mirror_x | role | policy |
| --- | --- | --- | --- | --- |
| legacy_default | bitcell_array | True | bitcell_array | None |
| legacy_default | dummy_left_array | True | dummy_bitcell | None |
| legacy_default | dummy_right_array | True | dummy_bitcell | None |
| legacy_default | replica_bitline_array | True | replica_bitline | None |
| openyield_all_r0 | bitcell_array | False | bitcell_array | all_r0 |
| openyield_all_r0 | dummy_left_array | False | dummy_bitcell | all_r0 |
| openyield_all_r0 | dummy_right_array | False | dummy_bitcell | all_r0 |
| openyield_all_r0 | replica_bitline_array | False | replica_bitline | all_r0 |
| openyield_alternating_mx | bitcell_array | True | bitcell_array | alternating_mx |
| openyield_alternating_mx | dummy_left_array | True | dummy_bitcell | alternating_mx |
| openyield_alternating_mx | dummy_right_array | True | dummy_bitcell | alternating_mx |
| openyield_alternating_mx | replica_bitline_array | True | replica_bitline | alternating_mx |

## DRC Compare Reference

| metric | all_r0 | alternating_mx |
| --- | --- | --- |
| total_markers | 84 | 44 |
| METAL2.2 | 34 | 0 |
| row_boundary_METAL2 | 34 | 0 |
| cross_row_power_short_risk | True | False |

## Next Steps

- Keep the default standalone behavior unchanged; only explicit opt-in should activate OpenYield storage aggregation.
- If promoted further, expose the row policy only for storage placement and keep peripheral placement on the old path.
- Before broader rollout, re-run the standalone path on representative SRAM sizes and inspect the generated GDS in KLayout.
