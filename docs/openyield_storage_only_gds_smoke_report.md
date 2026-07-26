# OpenYield Storage-Only GDS Smoke Report

This is a tiny hardcell-only GDS smoke for manual viewing. It is not a final SRAM layout and does not include routing, peripheral macros, shared rail merge, or signoff.

## Summary

- rows: `2`
- cols: `4`
- pitch: `0.895 x 1.565`
- orientation: `R0`
- instance count: `14`
- GDS: `E:\njust\keyan\SRAM Compiler_V2\OpenRAM-stable\deliverables\sram_layoutgen_step45_clean\build\openyield_storage_only_smoke_2x4\storage_only_2x4.gds`
- SVG: `E:\njust\keyan\SRAM Compiler_V2\OpenRAM-stable\deliverables\sram_layoutgen_step45_clean\build\openyield_storage_only_smoke_2x4\storage_only_2x4.svg`
- layout bbox: `(-0.095, -0.1)-(6.17, 3.03); 6.265 x 3.13`
- only allowed macros: `True`
- contains peripheral macro: `False`
- shared rail merge: `False`
- routing changed: `False`
- main GDS flow changed: `False`

## Macro Counts

| macro | count |
| --- | --- |
| cell_1rw | 8 |
| dummy_cell_1rw | 4 |
| replica_cell_1rw | 2 |

## Cell Arrays

| name | cell | rows | cols | pitch | mirror | bbox |
| --- | --- | --- | --- | --- | --- | --- |
| dummy_left | dummy_cell_1rw | 2 | 1 | 0.895 x 1.565 | mx=False, my=False | (-0.095, -0.1)-(0.8, 3.0300000000000002); 0.895 x 3.13 |
| bitcell_array | cell_1rw | 2 | 4 | 0.895 x 1.565 | mx=False, my=False | (0.8, -0.1)-(4.38, 3.0300000000000002); 3.58 x 3.13 |
| dummy_right | dummy_cell_1rw | 2 | 1 | 0.895 x 1.565 | mx=False, my=False | (4.38, -0.1)-(5.2749999999999995, 3.0300000000000002); 0.895 x 3.13 |
| replica_column | replica_cell_1rw | 2 | 1 | 0.895 x 1.565 | mx=False, my=False | (5.275, -0.1)-(6.17, 3.0300000000000002); 0.895 x 3.13 |

## Geometry Smoke Checks

| check | result |
| --- | --- |
| only_allowed_macros | True |
| no_peripheral_macros | True |
| instance_count_correct | True |
| pitch_correct | True |
| legacy_pitch_not_used | True |
| no_mirror_or_flip | True |
| shared_rail_merge_not_run | True |
| routing_not_changed | True |
| main_gds_flow_not_changed | True |
| gds_exists_nonempty | True |
| clean | True |

## Next Steps

- Open the smoke GDS in KLayout for visual inspection of full-bbox storage tiling.
- If visual spacing is acceptable, keep full bbox pitch as the conservative OpenYield-enabled storage pitch.
- Run a tiny storage-only DRC only as a smoke check; do not treat this GDS as final SRAM signoff.
