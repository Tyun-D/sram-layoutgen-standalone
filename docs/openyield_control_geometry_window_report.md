# OpenYield Control Geometry Window Report

This is a metadata-only geometry window and keepout audit. It does not modify standalone.py, routing, or the GDS writer.

## Summary

- addr_width: `5`
- data_width: `4`
- decoder_side_geometry_proven: `False`
- write_driver_side_pin_known: `True`
- keepout_conflict_found: `False`
- hardmacro_overlap_found: `False`
- physical_routing_proven: `False`
- clock_skew_checked: `False`
- safe_for_geometry_window_metadata: `True`
- can_enter_physical_row_placement: `False`
- can_enter_standalone_control_placement: `False`

## DFF Row BBoxes

```json
{
  "ADDR_DFF_ROW": {
    "x0": 0.0,
    "y0": 0.0,
    "x1": 15.099999999999984,
    "y1": 2.67,
    "width": 15.099999999999984,
    "height": 2.67
  },
  "DATA_DFF_ROW": {
    "x0": 0.0,
    "y0": 5.34,
    "x1": 12.039999999999981,
    "y1": 8.01,
    "width": 12.039999999999981,
    "height": 2.67
  }
}
```

## Geometry Windows

| window | x0 | y0 | x1 | y1 | width | height | metadata_only | physical_routing_proven |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| CLOCK_ENTRY_WINDOW | -2.0 | 0.0 | 0.0 | 8.01 | 2.0 | 8.01 | True | False |
| ADDR_TO_DECODER_WINDOW | 15.099999999999984 | 0.0 | 17.099999999999984 | 2.67 | 2.0 | 2.67 | True | False |
| DATA_TO_WRITEDRIVER_WINDOW | 0.0 | 8.01 | 12.039999999999981 | 10.01 | 12.039999999999981 | 2.0 | True | False |

## Keepouts

| keepout | x0 | y0 | x1 | y1 | width | height | overlaps_known_hardmacro |
| --- | --- | --- | --- | --- | --- | --- | --- |
| CLOCK_CHANNEL_KEEPOUT | -2.0 | 0.0 | 0.0 | 8.01 | 2.0 | 8.01 | False |
| ADDR_TO_DECODER_KEEPOUT | 15.099999999999984 | 0.0 | 17.099999999999984 | 2.67 | 2.0 | 2.67 | False |
| DATA_TO_WRITEDRIVER_KEEPOUT | 0.0 | 8.01 | 12.039999999999981 | 10.01 | 12.039999999999981 | 2.0 | False |

## Blockers

- Decoder input side is still not pin-proven at hardmacro level.
- All geometry windows and keepouts remain metadata-only; no physical routing exists yet.
- Clock skew and real clock tree distribution remain unchecked.
- Shared rail and integrated control-row legalization are still out of scope.

## Step 6.7 Recommendation

- Next, tie decoder-side and write-driver-side windows to explicit local placement candidates or hardmacro anchors before attempting the first physical control-row placement smoke.
