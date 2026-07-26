# OpenYield Row Orientation Compare Report

This is a storage-only compare smoke. It does not modify the main standalone flow, routing, shared-rail behavior, or peripheral placement.

## Summary

- rows / cols: `2 x 4`
- pitch: `0.895 x 1.565`
- all_r0 GDS: `E:\njust\keyan\SRAM Compiler_V2\OpenRAM-stable\deliverables\sram_layoutgen_step45_clean\build\openyield_storage_only_smoke_2x4_stitched\storage_only_2x4_all_r0.gds`
- alternating_mx GDS: `E:\njust\keyan\SRAM Compiler_V2\OpenRAM-stable\deliverables\sram_layoutgen_step45_clean\build\openyield_storage_only_smoke_2x4_mx\storage_only_2x4_alternating_mx.gds`
- all_r0 total markers: `84`
- alternating_mx total markers: `44`
- all_r0 METAL1.2: `38`
- alternating_mx METAL1.2: `32`
- all_r0 METAL2.2: `34`
- alternating_mx METAL2.2: `0`
- row-boundary METAL2 markers: `34 -> 0`
- power stitch related markers: `18 -> 12`
- cross-row power short risk: `True -> False`
- recommend storage row policy: `alternating_mx`
- recommend modify array_aggregation.py: `True`
- recommend modify standalone.py: `False`
- storage aggregation can continue: `True`

## Compare Table

| metric | all_r0 | alternating_mx | delta |
| --- | --- | --- | --- |
| total_markers | 84 | 44 | -40 |
| METAL1.2 | 38 | 32 | -6 |
| METAL2.2 | 34 | 0 | -34 |
| row_boundary_METAL2 | 34 | 0 | -34 |
| power_stitch_related | 18 | 12 | -6 |
| cross_row_power_short_risk | True | False | n/a |

## Decision Notes

- METAL2.2 seam markers: 34 -> 0
- total DRC markers: 84 -> 44
- cross-row power short risk: True -> False
- power-stitch-related markers: 18 -> 12
- Alternating MX reduced row-seam METAL2 pressure without introducing a new power-stitch hazard in this smoke.

## Next Steps

- Keep this as a storage-only policy result first; do not wire it into standalone until a follow-up storage-array-only integration step is approved.
- If adopted later, update array aggregation placement only; do not change routing, GDS writer, or peripheral placement in the same step.
- Re-run the stitched storage-only DRC smoke after any future integration change to confirm the seam result holds.
