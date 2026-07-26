# OpenYield Array Aggregation Row Policy Report

This report records row-orientation-policy support added to `array_aggregation.py`. It does not modify standalone.py, routing, or the main GDS writer.

## Summary

- supported row orientation policies: `['all_r0', 'alternating_mx']`
- default row orientation policy: `all_r0`
- alternating_mx supported in array_aggregation: `True`
- standalone.py modified: `False`
- routing modified: `False`
- GDS writer modified: `False`
- power stitch policy modified: `False`
- smoke uses array_aggregation source: `True`
- METAL2 seam marker cleared with alternating_mx: `True`
- power stitch still safe relative to baseline: `True`
- recommend storage row policy: `alternating_mx`
- recommend future standalone integration: `True`

## DRC Compare

| metric | all_r0 | alternating_mx |
| --- | --- | --- |
| total_markers | 84 | 44 |
| METAL2.2 | 34 | 0 |
| row_boundary_METAL2 | 34 | 0 |
| power_stitch_related | 18 | 12 |
| cross_row_power_short_risk | True | False |

## Next Steps

- Keep standalone.py unchanged in this step.
- If promoted later, wire alternating_mx into standalone storage placement behind an explicit opt-in flag only.
- Re-run the same storage-only compare smoke after any future adapter-to-standalone integration.
