# OpenYield Step 4 Final Smoke Report

This is a representative standalone GDS smoke only. It is not final signoff.

## 2x16_wpr1

| mode | gds_generated | gds_path | layout_bbox | size_um | storage_bbox | storage_orientation | bitcell_pitch | storage_instances | peripheral_instances | peripherals_old_path | routing_changed | gds_writer_changed | shared_rail_merge | cross_row_power_short_risk |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| legacy_default | True | E:\njust\keyan\SRAM Compiler_V2\OpenRAM-stable\deliverables\sram_layoutgen_step45_clean\build\openyield_step4_final_smoke\2x16_wpr1\legacy_default\sram_2x16_wpr1_fd45.gds | (-0.1,-0.105)-(15.2025,50.705) | 15.202499999999999 x 50.705 / 770.8427624999999 | (11.2,22.9175)-(14.915,44.9575) | legacy_openram_mirror_x | {'x': 0.705, 'y': 1.365} | 80 | 64 | True | False | False | False | None |
| openyield_all_r0 | True | E:\njust\keyan\SRAM Compiler_V2\OpenRAM-stable\deliverables\sram_layoutgen_step45_clean\build\openyield_step4_final_smoke\2x16_wpr1\openyield_all_r0\sram_2x16_wpr1_fd45.gds | (-0.1,-0.105)-(15.9225,50.705) | 15.922499999999975 x 50.705 / 807.3503624999987 | (11.2,22.9175)-(15.675,47.9575) | all_r0 | {'x': 0.895, 'y': 1.5650000000000002} | 80 | 64 | True | False | False | False | True |
| openyield_alternating_mx | True | E:\njust\keyan\SRAM Compiler_V2\OpenRAM-stable\deliverables\sram_layoutgen_step45_clean\build\openyield_step4_final_smoke\2x16_wpr1\openyield_alternating_mx\sram_2x16_wpr1_fd45.gds | (-0.1,-0.105)-(15.9225,50.705) | 15.922499999999975 x 50.705 / 807.3503624999987 | (11.2,22.9175)-(15.675,47.9575) | alternating_r0_mx | {'x': 0.895, 'y': 1.5650000000000002} | 80 | 64 | True | False | False | False | False |

## 4x32_wpr2

| mode | gds_generated | gds_path | layout_bbox | size_um | storage_bbox | storage_orientation | bitcell_pitch | storage_instances | peripheral_instances | peripherals_old_path | routing_changed | gds_writer_changed | shared_rail_merge | cross_row_power_short_risk |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| legacy_default | True | E:\njust\keyan\SRAM Compiler_V2\OpenRAM-stable\deliverables\sram_layoutgen_step45_clean\build\openyield_step4_final_smoke\4x32_wpr2\legacy_default\sram_4x32_wpr2_fd45.gds | (-0.1,-0.105)-(19.3925,50.705) | 19.392499999999995 x 50.705 / 983.2967124999997 | (11.2,22.9175)-(19.145,44.9575) | legacy_openram_mirror_x | {'x': 0.705, 'y': 1.365} | 176 | 87 | True | False | False | False | None |
| openyield_all_r0 | True | E:\njust\keyan\SRAM Compiler_V2\OpenRAM-stable\deliverables\sram_layoutgen_step45_clean\build\openyield_step4_final_smoke\4x32_wpr2\openyield_all_r0\sram_4x32_wpr2_fd45.gds | (-0.1,-0.105)-(21.2925,50.705) | 21.292499999999976 x 50.705 / 1079.6362124999987 | (11.2,22.9175)-(21.045,47.9575) | all_r0 | {'x': 0.895, 'y': 1.5650000000000002} | 176 | 87 | True | False | False | False | True |
| openyield_alternating_mx | True | E:\njust\keyan\SRAM Compiler_V2\OpenRAM-stable\deliverables\sram_layoutgen_step45_clean\build\openyield_step4_final_smoke\4x32_wpr2\openyield_alternating_mx\sram_4x32_wpr2_fd45.gds | (-0.1,-0.105)-(21.2925,50.705) | 21.292499999999976 x 50.705 / 1079.6362124999987 | (11.2,22.9175)-(21.045,47.9575) | alternating_r0_mx | {'x': 0.895, 'y': 1.5650000000000002} | 176 | 87 | True | False | False | False | False |

## Optional DRC Smoke

- ran: `True`
- case: `2x16_wpr1`
- mode: `openyield_alternating_mx`
- marker_count: `298`
- clean: `False`
- reason: `None`
