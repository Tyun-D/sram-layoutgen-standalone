# OpenYield Storage-Only Tiny DRC Smoke Report

This report checks the stitched storage-only smoke GDS. It is not full SRAM signoff.

## Summary

- input GDS: `E:\njust\keyan\SRAM Compiler_V2\OpenRAM-stable\deliverables\sram_layoutgen_step45_clean\build\openyield_storage_only_smoke_2x4_stitched\storage_only_2x4_stitched.gds`
- topcell: `openyield_storage_only_2x4`
- DRC deck: `E:\njust\keyan\SRAM Compiler_V2\OpenRAM-stable\deliverables\sram_layoutgen_step45_clean\technology\freepdk45\tech\freepdk45.lydrc`
- DRC deck available: `True`
- KLayout: `C:\Users\33568\AppData\Roaming\KLayout\klayout_app.exe`
- KLayout available: `True`
- DRC ran: `True`
- DRC violation count: `40`
- DRC clean: `False`
- power stitch related violation: `False`
- red-layer gap related violation: `True`
- VDD/GND short observed: `False`
- BL/BR/WL bridge observed: `False`
- recommend keep current power stitch: `True`
- can enter next step: `False`
- next step blocker: `tiny DRC has spacing markers outside the power stitch bridges; inspect M1/M2 cell-internal or abutment gaps before expanding aggregation`

## Power Stitch Context

- stitch power rails: `True`
- power rail layer: `m1`
- VDD stitch count: `12`
- GND stitch count: `12`
- side power trunk added: `False`
- same-net power only: `True`
- crosses BL/BR/WL: `False`
- marker bboxes parsed: `40`
- stitch-overlapping DRC markers: `0`

## Violation Type Stats

| type | count |
| --- | --- |
| METAL1.2: METAL1.2 : Minimum spacing of metal1 : 65nm | 6 |
| METAL2.2: METAL2.2 : Minimum spacing of intermediate metal2 : 70nm | 34 |

## Spacing / Notch / Min-Width Stats

| type | count |
| --- | --- |
| METAL1.2: METAL1.2 : Minimum spacing of metal1 : 65nm | 6 |
| METAL2.2: METAL2.2 : Minimum spacing of intermediate metal2 : 70nm | 34 |

## Red-Layer Gap Related Stats

| type | count |
| --- | --- |
| METAL1.2: METAL1.2 : Minimum spacing of metal1 : 65nm | 6 |

## Outputs

- DRC marker DB: `E:\njust\keyan\SRAM Compiler_V2\OpenRAM-stable\deliverables\sram_layoutgen_step45_clean\build\openyield_storage_only_smoke_2x4_stitched\storage_only_2x4_stitched_drc.lyrdb`
- DRC log: `E:\njust\keyan\SRAM Compiler_V2\OpenRAM-stable\deliverables\sram_layoutgen_step45_clean\build\openyield_storage_only_smoke_2x4_stitched\storage_only_2x4_stitched_drc.log`
- JSON report: `E:\njust\keyan\SRAM Compiler_V2\OpenRAM-stable\deliverables\sram_layoutgen_step45_clean\docs\openyield_storage_only_drc_smoke_report.json`
- Markdown report: `E:\njust\keyan\SRAM Compiler_V2\OpenRAM-stable\deliverables\sram_layoutgen_step45_clean\docs\openyield_storage_only_drc_smoke_report.md`

## Manual KLayout Checklist

1. Open E:\njust\keyan\SRAM Compiler_V2\OpenRAM-stable\deliverables\sram_layoutgen_step45_clean\build\openyield_storage_only_smoke_2x4_stitched\storage_only_2x4_stitched.gds in KLayout.
2. Zoom into boundaries between dummy/bitcell/replica cells.
3. Open the DRC marker browser and load the generated .lyrdb if available.
4. Check whether power stitch rectangles have spacing, min-width, or notch markers.
5. Check whether the small red-layer gaps have any same-layer spacing/notch markers.
6. Confirm no bridge connects VDD to GND.
7. Confirm no bridge touches BL, BR, RBL, RBLB, or WL pins.
8. If automatic DRC ran, inspect E:\njust\keyan\SRAM Compiler_V2\OpenRAM-stable\deliverables\sram_layoutgen_step45_clean\build\openyield_storage_only_smoke_2x4_stitched\storage_only_2x4_stitched_drc.lyrdb marker categories and marker locations.

## Notes

- This is a tiny storage-only DRC smoke; it is not full SRAM signoff.
- KLayout DRC reports geometric rule markers, not full net-aware LVS connectivity.
- Power-stitch connectivity conclusions are limited to same-net bridge construction and marker overlap.
