# OpenYield ColumnMux VDD Pin-Proof Report

This Step 5.6 report is read-only. It generates a repaired candidate GDS by adding a single `vdd` TEXT label to the suspected top M1 rail and then re-audits the result.

## Summary

- source GDS: `E:\njust\keyan\SRAM Compiler_V2\OpenRAM-stable\deliverables\sram_layoutgen_step45_clean\technology\freepdk45\gds_lib\openram_replacements\gen_col_mux.gds`
- repaired candidate GDS: `E:\njust\keyan\SRAM Compiler_V2\OpenRAM-stable\deliverables\sram_layoutgen_step45_clean\build\openyield_colmux_repair\gen_col_mux_vdd_labeled.gds`
- modified original GDS: `False`
- selected candidate source: `power_report_suspected_shape`
- selected candidate bbox: `{'x0': 0.14, 'y0': 1.6275, 'x1': 0.46, 'y1': 1.6925000000000001}`
- new text label: `{'name': 'vdd', 'layer': 11, 'texttype': 0, 'x': 0.3, 'y': 1.66}`
- vdd_label_present_before: `False`
- vdd_label_present_after: `True`
- power_status before: `vdd_shape_unlabeled`
- power_status after: `vdd_label_present`
- safe_for_physical_mapping: `True`
- safe_for_shared_rail: `False`
- can_enter_columnmux_placement: `limited_or_metadata_only`
- recommended_integration: `add_repaired_macro_alias`

## Before / After

- polygon count before: `50`
- polygon count after: `50`
- polygon count unchanged: `True`
- text count before: `9`
- text count after: `10`
- labels added count: `1`
- vdd label matches M1 shape: `True`
- vdd label inside candidate shape: `True`

## Notes

- The repair only appends one TEXT element; no polygon coordinates are changed.
- The candidate is proof-only and does not modify the original replacement GDS or replacement_macros.json.
- Shared rail still remains unproven; this repair only upgrades pin metadata from unlabeled shape to label-backed pin.
