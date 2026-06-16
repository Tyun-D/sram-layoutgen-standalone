# OpenYield Hardcell DRC Baseline Report

This compares single-hardcell KLayout DRC baselines against the storage-only stitched marker set. It is not full SRAM signoff.

## Summary

- hardcell_baseline_clean: `True`
- storage_markers_explained_by_hardcell: `0`
- storage_markers_new_from_aggregation: `40`
- pitch_change_required: `False`
- power_stitch_change_required: `False`
- storage_aggregation_can_continue: `False`

## Hardcell DRC Counts

| cell | marker_count | METAL1.2 | METAL2.2 | clean |
| --- | --- | --- | --- | --- |
| cell_1rw | 0 | 0 | 0 | True |
| dummy_cell_1rw | 0 | 0 | 0 | True |
| replica_cell_1rw | 0 | 0 | 0 | True |

## Storage Match Stats

| explanation | count |
| --- | --- |
| aggregation_boundary_spacing | 38 |
| storage_only_missing_context | 2 |

## Aggregation Location Stats

| location | count |
| --- | --- |
| array_outer_edge | 2 |
| horizontal_cell_boundary | 4 |
| vertical_row_boundary | 34 |

## Notes

- Keep the current power stitch policy; this baseline did not implicate the stitch rectangles.
- Unmatched storage-only markers should be treated as row-boundary or missing-context candidates until inspected in KLayout.
