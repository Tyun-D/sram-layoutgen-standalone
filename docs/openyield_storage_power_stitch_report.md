# OpenYield Storage-Only GDS Smoke Report

This is a tiny hardcell-only GDS smoke for manual viewing. It is not a final SRAM layout and does not include routing, peripheral macros, shared rail merge, or signoff.

## Summary

- rows: `2`
- cols: `4`
- pitch: `0.895 x 1.565`
- orientation: `R0`
- instance count: `14`
- GDS: `E:\njust\keyan\SRAM Compiler_V2\OpenRAM-stable\deliverables\sram_layoutgen_step45_clean\build\openyield_storage_only_smoke_2x4_stitched\storage_only_2x4_stitched.gds`
- input GDS: `None` (in_memory_storage_only_layout)
- SVG: `E:\njust\keyan\SRAM Compiler_V2\OpenRAM-stable\deliverables\sram_layoutgen_step45_clean\build\openyield_storage_only_smoke_2x4_stitched\storage_only_2x4_stitched.svg`
- layout bbox: `(-0.095, -0.1)-(6.17, 3.03); 6.265 x 3.13`
- only allowed macros: `True`
- contains peripheral macro: `False`
- stitch power rails: `True`
- power rail layer: `m1`
- VDD stitch count: `12`
- GND stitch count: `12`
- side power trunk added: `False`
- same-net power only: `True`
- crosses BL/BR/WL: `False`
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

## Power Stitch Records

| name | net | layer | row | left | right | gap | rect |
| --- | --- | --- | --- | --- | --- | --- | --- |
| vdd_stitch_r0_dummy_left_r0_to_bit_r0_c0 | vdd | m1 | 0 | dummy_left_r0 | bit_r0_c0 | 0.01 | (0.795, 1.3325)-(0.805, 1.3975); 0.01 x 0.065 |
| gnd_stitch_r0_dummy_left_r0_to_bit_r0_c0 | gnd | m1 | 0 | dummy_left_r0 | bit_r0_c0 | 0.01 | (0.795, -0.0325)-(0.805, 0.0325); 0.01 x 0.065 |
| vdd_stitch_r0_bit_r0_c0_to_bit_r0_c1 | vdd | m1 | 0 | bit_r0_c0 | bit_r0_c1 | 0.01 | (1.69, 1.3325)-(1.7, 1.3975); 0.01 x 0.065 |
| gnd_stitch_r0_bit_r0_c0_to_bit_r0_c1 | gnd | m1 | 0 | bit_r0_c0 | bit_r0_c1 | 0.01 | (1.69, -0.0325)-(1.7, 0.0325); 0.01 x 0.065 |
| vdd_stitch_r0_bit_r0_c1_to_bit_r0_c2 | vdd | m1 | 0 | bit_r0_c1 | bit_r0_c2 | 0.01 | (2.585, 1.3325)-(2.595, 1.3975); 0.01 x 0.065 |
| gnd_stitch_r0_bit_r0_c1_to_bit_r0_c2 | gnd | m1 | 0 | bit_r0_c1 | bit_r0_c2 | 0.01 | (2.585, -0.0325)-(2.595, 0.0325); 0.01 x 0.065 |
| vdd_stitch_r0_bit_r0_c2_to_bit_r0_c3 | vdd | m1 | 0 | bit_r0_c2 | bit_r0_c3 | 0.01 | (3.48, 1.3325)-(3.49, 1.3975); 0.01 x 0.065 |
| gnd_stitch_r0_bit_r0_c2_to_bit_r0_c3 | gnd | m1 | 0 | bit_r0_c2 | bit_r0_c3 | 0.01 | (3.48, -0.0325)-(3.49, 0.0325); 0.01 x 0.065 |
| vdd_stitch_r0_bit_r0_c3_to_dummy_right_r0 | vdd | m1 | 0 | bit_r0_c3 | dummy_right_r0 | 0.01 | (4.375, 1.3325)-(4.385, 1.3975); 0.01 x 0.065 |
| gnd_stitch_r0_bit_r0_c3_to_dummy_right_r0 | gnd | m1 | 0 | bit_r0_c3 | dummy_right_r0 | 0.01 | (4.375, -0.0325)-(4.385, 0.0325); 0.01 x 0.065 |
| vdd_stitch_r0_dummy_right_r0_to_replica_r0 | vdd | m1 | 0 | dummy_right_r0 | replica_r0 | 0.01 | (5.27, 1.3325)-(5.28, 1.3975); 0.01 x 0.065 |
| gnd_stitch_r0_dummy_right_r0_to_replica_r0 | gnd | m1 | 0 | dummy_right_r0 | replica_r0 | 0.01 | (5.27, -0.0325)-(5.28, 0.0325); 0.01 x 0.065 |
| vdd_stitch_r1_dummy_left_r1_to_bit_r1_c0 | vdd | m1 | 1 | dummy_left_r1 | bit_r1_c0 | 0.01 | (0.795, 2.8975)-(0.805, 2.9625); 0.01 x 0.065 |
| gnd_stitch_r1_dummy_left_r1_to_bit_r1_c0 | gnd | m1 | 1 | dummy_left_r1 | bit_r1_c0 | 0.01 | (0.795, 1.5325)-(0.805, 1.5975); 0.01 x 0.065 |
| vdd_stitch_r1_bit_r1_c0_to_bit_r1_c1 | vdd | m1 | 1 | bit_r1_c0 | bit_r1_c1 | 0.01 | (1.69, 2.8975)-(1.7, 2.9625); 0.01 x 0.065 |
| gnd_stitch_r1_bit_r1_c0_to_bit_r1_c1 | gnd | m1 | 1 | bit_r1_c0 | bit_r1_c1 | 0.01 | (1.69, 1.5325)-(1.7, 1.5975); 0.01 x 0.065 |
| vdd_stitch_r1_bit_r1_c1_to_bit_r1_c2 | vdd | m1 | 1 | bit_r1_c1 | bit_r1_c2 | 0.01 | (2.585, 2.8975)-(2.595, 2.9625); 0.01 x 0.065 |
| gnd_stitch_r1_bit_r1_c1_to_bit_r1_c2 | gnd | m1 | 1 | bit_r1_c1 | bit_r1_c2 | 0.01 | (2.585, 1.5325)-(2.595, 1.5975); 0.01 x 0.065 |
| vdd_stitch_r1_bit_r1_c2_to_bit_r1_c3 | vdd | m1 | 1 | bit_r1_c2 | bit_r1_c3 | 0.01 | (3.48, 2.8975)-(3.49, 2.9625); 0.01 x 0.065 |
| gnd_stitch_r1_bit_r1_c2_to_bit_r1_c3 | gnd | m1 | 1 | bit_r1_c2 | bit_r1_c3 | 0.01 | (3.48, 1.5325)-(3.49, 1.5975); 0.01 x 0.065 |
| vdd_stitch_r1_bit_r1_c3_to_dummy_right_r1 | vdd | m1 | 1 | bit_r1_c3 | dummy_right_r1 | 0.01 | (4.375, 2.8975)-(4.385, 2.9625); 0.01 x 0.065 |
| gnd_stitch_r1_bit_r1_c3_to_dummy_right_r1 | gnd | m1 | 1 | bit_r1_c3 | dummy_right_r1 | 0.01 | (4.375, 1.5325)-(4.385, 1.5975); 0.01 x 0.065 |
| vdd_stitch_r1_dummy_right_r1_to_replica_r1 | vdd | m1 | 1 | dummy_right_r1 | replica_r1 | 0.01 | (5.27, 2.8975)-(5.28, 2.9625); 0.01 x 0.065 |
| gnd_stitch_r1_dummy_right_r1_to_replica_r1 | gnd | m1 | 1 | dummy_right_r1 | replica_r1 | 0.01 | (5.27, 1.5325)-(5.28, 1.5975); 0.01 x 0.065 |

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
| stitch_shapes_power_only | True |
| no_vdd_gnd_cross_stitch | True |
| no_signal_pin_stitch | True |
| no_bl_br_wl_stitch | True |
| explicit_bridge_not_global_shared_rail_merge | True |
| gds_exists_nonempty | True |
| clean | True |

## Next Steps

- Open the smoke GDS in KLayout for visual inspection of full-bbox storage tiling.
- If visual spacing is acceptable, keep full bbox pitch as the conservative OpenYield-enabled storage pitch.
- Run a tiny storage-only DRC only as a smoke check; do not treat this GDS as final SRAM signoff.
