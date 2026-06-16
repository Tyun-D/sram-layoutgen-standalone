# OpenYield Step 4 Storage Aggregation Summary

This report summarizes Step 4 only. It does not claim full SRAM signoff.

## Completed

- Added limited OpenYield storage-array aggregation planning for cell_1rw, dummy_cell_1rw, and replica_cell_1rw.
- Audited legal storage pitch and kept the conservative full-bbox pitch 0.895 x 1.565.
- Built storage-only GDS smoke and power-stitch smoke without changing the main routing or GDS writer.
- Compared all_r0 versus alternating_mx and showed METAL2 seam markers drop from 34 to 0.
- Wired row orientation policy into array_aggregation.py and then into standalone as an explicit opt-in parameter.
- Verified representative standalone GDS generation for 2x16_wpr1 and 4x32_wpr2 across legacy, all_r0, and alternating_mx modes.

## Final Strategy

- macros: `['cell_1rw', 'dummy_cell_1rw', 'replica_cell_1rw']`
- pitch: `0.895 x 1.565`
- default row policy: `all_r0`
- optional recommended row policy: `alternating_mx`
- power stitch: storage-only smoke uses same-net horizontal power stitch; main flow still does not perform shared rail merge
- default path unchanged: `True`
- OpenYield storage aggregation opt-in available: `True`

## Why Not all_r0

- Storage-only compare smoke showed row-boundary METAL2 markers 34 -> 0 when switching from all_r0 to alternating_mx.
- Cross-row power short risk improved from True to False in the storage-only compare smoke.

## Why Not Legacy Pitch

- The legacy 0.705 x 1.365 pitch caused real bbox overlap with risky layers including active, contact, m1, m2, and via1.
- The current recommendation remains use_full_bbox_pitch because the legacy pitch is not a harmless rail-only overlap.

## Still Unresolved

- METAL1.2 residual markers remain; storage-only DRC is still not clean.
- Storage-only DRC smoke is not equivalent to final SRAM signoff.
- Peripheral modules are still on the old path and not adapted to OpenYield contracts.
- sense_amp Q/QB semantic adaptation is not done.
- gen_col_mux VDD metadata is still incomplete.
- wordline driver B-pin semantics still need confirmation.
- TIME/control logic adaptation and expansion are not done.

## Step 5 Recommendation

- can enter Step 5: `True`
- Start Step 5 from sense_amp because its Q/QB interface is the clearest semantic mismatch between OpenYield storage behavior and the current standalone periphery.
- After sense_amp, handle write_driver and then column mux power metadata so the data-path periphery can move toward contract-driven placement.
- Keep alternating_mx explicit and opt-in while Step 5 adapts one peripheral family at a time.
