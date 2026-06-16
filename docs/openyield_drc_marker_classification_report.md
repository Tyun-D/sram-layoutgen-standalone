# OpenYield DRC Marker Classification Report

This classifies KLayout DRC markers for the tiny storage-only stitched GDS. It is not full SRAM signoff.

## Summary

- input GDS: `E:\njust\keyan\SRAM Compiler_V2\OpenRAM-stable\deliverables\sram_layoutgen_step45_clean\build\openyield_storage_only_smoke_2x4_stitched\storage_only_2x4_stitched.gds`
- input LYRDB: `E:\njust\keyan\SRAM Compiler_V2\OpenRAM-stable\deliverables\sram_layoutgen_step45_clean\build\openyield_storage_only_smoke_2x4_stitched\storage_only_2x4_stitched_drc.lyrdb`
- LYRDB parse success: `True`
- total markers: `40`
- power stitch safe for current smoke: `True`
- current pitch definitely too small: `False`
- current pitch needs context review: `True`
- needs stitch change: `False`
- needs hardcell-level DRC baseline: `True`
- storage aggregation not blocked by power stitch: `True`
- can continue storage aggregation: `False`

## Rule Type Stats

| rule | count |
| --- | --- |
| METAL1.2 | 6 |
| METAL2.2 | 34 |

## Location Class Stats

| location_class | count |
| --- | --- |
| array_outer_edge | 2 |
| horizontal_cell_boundary | 4 |
| vertical_row_boundary | 34 |

## Likely Cause Stats

| likely_cause | count |
| --- | --- |
| abutment_boundary_spacing | 24 |
| storage_only_missing_context | 16 |

## M1 Marker Summary

- count: `6`
- near power stitch: `0`
- overlap power stitch: `0`
- near power pin: `0`
- near bitline pin: `0`

| id | center | nearest_instance | macro | location | cause | stitch_dist | bitline | bitline_dist |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | (4.38, 1.725) | bit_r1_c3 | cell_1rw | horizontal_cell_boundary | abutment_boundary_spacing | 0.095 | br | 0.321012 |
| 2 | (4.38, 0.16) | bit_r0_c3 | cell_1rw | horizontal_cell_boundary | abutment_boundary_spacing | 0.095 | br | 0.321012 |
| 3 | (0.8, 0.16) | dummy_left_r0 | dummy_cell_1rw | horizontal_cell_boundary | abutment_boundary_spacing | 0.095 | br | 0.321012 |
| 4 | (-0.095, 0.16) | dummy_left_r0 | dummy_cell_1rw | array_outer_edge | storage_only_missing_context | 0.890084 | bl | 0.325383 |
| 5 | (0.8, 0.16) | dummy_left_r0 | dummy_cell_1rw | horizontal_cell_boundary | abutment_boundary_spacing | 0.095 | br | 0.321012 |
| 6 | (-0.095, 0.16) | dummy_left_r0 | dummy_cell_1rw | array_outer_edge | storage_only_missing_context | 0.890084 | bl | 0.325383 |

## M2 Marker Summary

- count: `34`
- near power stitch: `2`
- overlap power stitch: `0`
- near power pin: `0`
- near bitline pin: `14`

| id | center | nearest_instance | macro | location | cause | stitch_dist | bitline | bitline_dist |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 7 | (5.145, 1.4975) | dummy_right_r1 | dummy_cell_1rw | vertical_row_boundary | abutment_boundary_spacing | 0.099032 | br | 0.165742 |
| 8 | (5.215, 1.4975) | dummy_right_r1 | dummy_cell_1rw | vertical_row_boundary | abutment_boundary_spacing | 0.029108 | br | 0.23102 |
| 9 | (4.995, 1.475) | dummy_right_r1 | dummy_cell_1rw | vertical_row_boundary | storage_only_missing_context | 0.244655 | br | 0.093 |
| 10 | (4.475, 1.475) | dummy_right_r1 | dummy_cell_1rw | vertical_row_boundary | abutment_boundary_spacing | 0.072672 | bl | 0.21154 |
| 11 | (2.31, 1.475) | bit_r1_c1 | cell_1rw | vertical_row_boundary | storage_only_missing_context | 0.244655 | br | 0.093 |
| 12 | (5.37, 1.475) | replica_r1 | replica_cell_1rw | vertical_row_boundary | abutment_boundary_spacing | 0.072672 | bl | 0.21154 |
| 13 | (0.185, 1.475) | dummy_left_r1 | dummy_cell_1rw | vertical_row_boundary | storage_only_missing_context | 0.576959 | bl | 0.093134 |
| 14 | (0.67, 1.4975) | dummy_left_r1 | dummy_cell_1rw | vertical_row_boundary | abutment_boundary_spacing | 0.099032 | br | 0.165742 |
| 15 | (6.11, 1.4975) | replica_r1 | replica_cell_1rw | vertical_row_boundary | abutment_boundary_spacing | 0.804004 | br | 0.23102 |
| 16 | (0.705, 1.475) | dummy_left_r1 | dummy_cell_1rw | vertical_row_boundary | abutment_boundary_spacing | 0.072672 | br | 0.20706 |
| 17 | (4.1, 1.475) | bit_r1_c3 | cell_1rw | vertical_row_boundary | storage_only_missing_context | 0.244655 | br | 0.093 |
| 18 | (1.415, 1.475) | bit_r1_c0 | cell_1rw | vertical_row_boundary | storage_only_missing_context | 0.244655 | br | 0.093 |
| 19 | (3.39, 1.475) | bit_r1_c2 | cell_1rw | vertical_row_boundary | abutment_boundary_spacing | 0.072672 | br | 0.20706 |
| 20 | (2.87, 1.475) | bit_r1_c2 | cell_1rw | vertical_row_boundary | storage_only_missing_context | 0.244655 | bl | 0.093134 |
| 21 | (1.08, 1.475) | bit_r1_c0 | cell_1rw | vertical_row_boundary | storage_only_missing_context | 0.244655 | bl | 0.093134 |
| 22 | (2.685, 1.475) | bit_r1_c2 | cell_1rw | vertical_row_boundary | abutment_boundary_spacing | 0.072672 | bl | 0.21154 |
| 23 | (0.74, 1.4975) | dummy_left_r1 | dummy_cell_1rw | vertical_row_boundary | abutment_boundary_spacing | 0.029108 | br | 0.23102 |
| 24 | (3.205, 1.475) | bit_r1_c2 | cell_1rw | vertical_row_boundary | storage_only_missing_context | 0.244655 | br | 0.093 |
| 25 | (4.66, 1.475) | dummy_right_r1 | dummy_cell_1rw | vertical_row_boundary | storage_only_missing_context | 0.244655 | bl | 0.093134 |
| 26 | (3.765, 1.475) | bit_r1_c3 | cell_1rw | vertical_row_boundary | storage_only_missing_context | 0.244655 | bl | 0.093134 |
| 27 | (0.52, 1.475) | dummy_left_r1 | dummy_cell_1rw | vertical_row_boundary | storage_only_missing_context | 0.244655 | br | 0.093 |
| 28 | (1.6, 1.475) | bit_r1_c0 | cell_1rw | vertical_row_boundary | abutment_boundary_spacing | 0.072672 | br | 0.20706 |
| 29 | (0.895, 1.475) | bit_r1_c0 | cell_1rw | vertical_row_boundary | abutment_boundary_spacing | 0.072672 | bl | 0.21154 |
| 30 | (4.285, 1.475) | bit_r1_c3 | cell_1rw | vertical_row_boundary | abutment_boundary_spacing | 0.072672 | br | 0.20706 |
| 31 | (1.975, 1.475) | bit_r1_c1 | cell_1rw | vertical_row_boundary | storage_only_missing_context | 0.244655 | bl | 0.093134 |
| 32 | (5.555, 1.475) | replica_r1 | replica_cell_1rw | vertical_row_boundary | storage_only_missing_context | 0.244655 | bl | 0.093134 |
| 33 | (1.79, 1.475) | bit_r1_c1 | cell_1rw | vertical_row_boundary | abutment_boundary_spacing | 0.072672 | bl | 0.21154 |
| 34 | (2.495, 1.475) | bit_r1_c1 | cell_1rw | vertical_row_boundary | abutment_boundary_spacing | 0.072672 | br | 0.20706 |
| 35 | (0.0, 1.475) | dummy_left_r1 | dummy_cell_1rw | vertical_row_boundary | abutment_boundary_spacing | 0.761483 | bl | 0.21154 |
| 36 | (6.04, 1.4975) | replica_r1 | replica_cell_1rw | vertical_row_boundary | abutment_boundary_spacing | 0.734004 | br | 0.165742 |
| 37 | (3.58, 1.475) | bit_r1_c3 | cell_1rw | vertical_row_boundary | abutment_boundary_spacing | 0.072672 | bl | 0.21154 |
| 38 | (5.89, 1.475) | replica_r1 | replica_cell_1rw | vertical_row_boundary | storage_only_missing_context | 0.576959 | br | 0.093 |
| 39 | (6.075, 1.475) | replica_r1 | replica_cell_1rw | vertical_row_boundary | abutment_boundary_spacing | 0.761483 | br | 0.20706 |
| 40 | (5.18, 1.475) | dummy_right_r1 | dummy_cell_1rw | vertical_row_boundary | abutment_boundary_spacing | 0.072672 | br | 0.20706 |

## Conclusions

- The power stitch rectangles are not overlapped by any marker, so keep the current same-net M1 power stitch smoke policy.
- The M1 markers are consistent with metal1 spacing gaps, but the script cannot prove same-net identity for non-power M1 shapes.
- The M2 markers are near storage cells and should not be fixed by bridging BL/BR/RBL/RBLB.
- Full bbox pitch is not proven too small by this classifier; row/abutment context and hardcell baseline DRC still need review.
- Hardcell-level DRC baselines are recommended: `True`.

## Hardcell Baseline Plan

1. Run the bundled FreePDK45 KLayout DRC deck on a standalone cell_1rw GDS instance.
2. Repeat for dummy_cell_1rw and replica_cell_1rw.
3. Compare single-cell METAL1.2/METAL2.2 markers against the storage-only marker coordinates.
4. If single-cell baselines already contain the same rules, do not attribute those markers to aggregation.

## Next Steps

- Do not add BL/BR/RBL/RBLB bridges.
- Keep the current same-net M1 power stitch policy for this smoke because no marker overlaps a stitch bridge.
- Before changing pitch, run hardcell-level DRC baselines and inspect M2 markers at the row boundary in KLayout.
- Treat storage-only DRC as context smoke only, not final SRAM signoff.
