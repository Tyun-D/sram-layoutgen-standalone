# OpenYield ColumnMux Repaired Candidate Install Report

This report documents a non-destructive install of the repaired ColumnMux candidate into a separate tech-library path. The original replacement GDS and `replacement_macros.json` are left untouched.

## Summary

- source GDS: `E:\njust\keyan\SRAM Compiler_V2\OpenRAM-stable\deliverables\sram_layoutgen_step45_clean\technology\freepdk45\gds_lib\openram_replacements\gen_col_mux.gds`
- installed candidate GDS: `E:\njust\keyan\SRAM Compiler_V2\OpenRAM-stable\deliverables\sram_layoutgen_step45_clean\technology\freepdk45\gds_lib\openyield_repaired\gen_col_mux_vdd_labeled.gds`
- alias metadata path: `E:\njust\keyan\SRAM Compiler_V2\OpenRAM-stable\deliverables\sram_layoutgen_step45_clean\technology\freepdk45\openyield_repaired_macro_aliases.json`
- original modified: `False`
- replacement_macros modified: `False`
- replacement_macros untouched: `True`
- selected candidate source: `source_gds_top_m1_shape`
- selected candidate bbox: `{'x0': 0.14, 'y0': 1.6275, 'x1': 0.46, 'y1': 1.6925000000000001}`
- new text label: `{'name': 'vdd', 'layer': 11, 'texttype': 0, 'x': 0.3, 'y': 1.66}`
- power status before: `vdd_shape_unlabeled`
- power status after: `vdd_label_present`
- safe_for_physical_mapping: `True`
- safe_for_shared_rail: `False`
- can_enter_columnmux_limited_placement: `True`
- can_proceed_step5_9_standalone_opt_in: `True`

## Alias Metadata

- local macro: `gen_col_mux_vdd_labeled`
- source macro: `gen_col_mux`
- repair type: `add_vdd_text_label_only`
- integration status: `candidate_only`
- candidate GDS: `E:\njust\keyan\SRAM Compiler_V2\OpenRAM-stable\deliverables\sram_layoutgen_step45_clean\technology\freepdk45\gds_lib\openyield_repaired\gen_col_mux_vdd_labeled.gds`

## Before / After

- polygon count before: `50`
- polygon count after: `50`
- polygon count unchanged: `True`
- text count before: `9`
- text count after: `10`
- text count delta: `1`
- label count delta: `1`
- vdd label present before: `False`
- vdd label present after: `True`
- vdd label matches M1 shape: `True`
- vdd label inside candidate shape: `True`

## Notes

- The install path is non-destructive: it regenerates the candidate from the original replacement GDS and writes it to the openyield_repaired tech library.
- Only one new TEXT label is added; polygon geometry remains unchanged.
- replacement_macros.json is intentionally untouched.
- The repaired alias metadata lives outside replacement_macros.json so it can be consumed as a candidate-only mapping.
- Shared rail remains disabled until a separate rail continuity proof exists.
