# OpenYield Row-Boundary Audit Report

This audit focuses on the 34 METAL2.2 seam markers in the storage-only stitched smoke. It is a policy analysis, not a main-flow change.

## Summary

- METAL2 marker total: `34`
- row-boundary marker count: `34`
- marker y values: `[1.475, 1.4975]`
- concentrated at row boundary: `True`
- near BL/BR/RBL/RBLB: `True`
- current R0/R0 likely source: `True`
- recommend R0/MX compare smoke: `True`
- recommend row gap now: `False`
- recommend modify array_aggregation.py now: `False`
- recommend modify standalone.py now: `False`
- storage aggregation can continue now: `False`

## Evidence

- Row-boundary y reference: `1.465`
- Distance to seam min/max/mean: `{'min': 0.01, 'max': 0.0325, 'mean': 0.013971}`
- Local y values relative to row1 origin: `[-0.09, -0.0675]`
- Nearest bitline label stats: `{'bl': 14, 'br': 20}`
- Nearest macro stats: `{'cell_1rw': 16, 'dummy_cell_1rw': 12, 'replica_cell_1rw': 6}`
- Likely cause stats: `{'abutment_boundary_spacing': 20, 'storage_only_missing_context': 14}`

## Policy Read

- The current all-R0 row policy keeps lower-edge M2 bitline features on the seam side for both rows.
- An R0/MX alternation is theoretically the most direct way to move row1 bottom-edge M2 features away from the seam without paying blanket area cost.
- A row gap or keepout would likely help spacing too, but reads as a conservative workaround until an R0/MX compare smoke is checked.
- The 4 horizontal M1 markers are a separate horizontal-boundary issue and are not the main evidence for changing row orientation.

## Next Steps

- Generate a separate R0/MX storage-only compare smoke outside the main flow.
- Do not change pitch or power stitch before the R0/MX compare smoke confirms whether the 34 seam markers collapse.
- Keep the 4 horizontal METAL1.2 markers as a separate issue; they are not explained by row orientation alone.
- Treat the 2 array-edge markers as context candidates that may improve with edge dummy/context handling rather than row orientation.
