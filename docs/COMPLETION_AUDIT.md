# Completion Audit

Objective:

1. Use FreePDK45-compatible layer definitions.
2. Use the same physical standard/hard macros as the bundled OpenRAM/FreePDK45
   library where they are currently used.
3. Follow OpenRAM's brick/generator idea with a replaceable macro scheme.
4. Prevent any occupied layout area from overlapping another occupied object.
5. Advance to full DRC/LVS.

## Evidence

Latest representative signoff runs:

| Case | Report | DRC | LVS | signoff_ready |
| --- | --- | ---: | ---: | --- |
| 4x32 wpr2 | `build/external_signoff_4x32_no_array_overlap/sram_4x32_wpr2_fd45.report.json` | 0 | 0 | true |
| 32x16 wpr2 | `build/compare_openram_32x16/ours_32x16_no_array_overlap/sram_16x32_wpr2_fd45.report.json` | 0 | 0 | true |
| 8x64 wpr4 | `build/external_signoff_8x64_wpr4_no_array_overlap/sram_8x64_wpr4_fd45.report.json` | 0 | 0 | true |

The maintained comparison aliases point to the latest 32x16 real-pin run:

- `build/compare_openram_32x16/A_ours_32x16_latest.gds`
- `build/compare_openram_32x16/A_ours_32x16_signoff_clean.gds`
- `build/compare_openram_32x16/A_ours_32x16_latest.report.json`

## Requirement Checks

### FreePDK45 layers

The latest 32x16 report has:

- `layer_audit.matches_bundled_freepdk45_layers: true`
- no unknown clean boundary/text LPPs.

### OpenRAM/FreePDK45 cell sources

The latest 32x16 report has:

- `openram_cell_source_audit.clean: true`
- `missing_gds_cells: []`
- `synthetic_generated_gds_cells: []`
- `generated_fallback_cells: []`
- `abstract_cells: []`

Generated/replacement macros are physical GDS references under:

```text
technology/freepdk45/gds_lib/openram_replacements/
```

### Replaceable macro scheme

The macro registry is:

```text
technology/freepdk45/replacement_macros.json
```

It is produced from real replacement GDS by:

```powershell
python examples\materialize_brick_library.py --force
```

The latest 32x16 report has:

- `macro_replacement_audit.macro_cell_count: 6`
- `macro_replacement_audit.physical_macro_count: 6`
- `macro_replacement_audit.missing_physical_macro_count: 0`
- `macro_replacement_audit.all_used_macros_have_physical_gds: true`

### No occupied-area overlap

The latest 32x16 report has:

- `geometry_audit.clean: true`
- `objects_outside_pr_boundary_count: 0`
- `placed_cell_overlap_count: 0`
- `generated_hardcell_overlap_count: 0`
- `generated_hardcell_spacing_violation_count: 0`

The built-in verifier reports any positive overlap as `cell_overlap`.

The storage-array family is compact again: in the latest 32x16 layout, the
physical gap from the bitcell array to the right dummy column is `0.31um`, and
the physical gap from the right dummy column to the replica bitline column is
`0.31um`. The replica bitcell column is no longer pushed to the far side of the
column-macro row.

The strict occupancy rule is now also applied inside repeated storage arrays.
The bitcell/dummy/replica pitch is `1.195um x 1.865um`, derived from the
measured `cell_1rw` physical bbox plus `0.30um` keepout. For 4x32, 32x16, and
8x64, storage-array max physical layer overlap is `0um` in X and `0um` in Y.

### Full DRC/LVS

KLayout external signoff was run on the full signoff GDS for 4x32, 32x16, and
8x64. All three report:

- KLayout DRC violation count: 0
- KLayout LVS item count: 0
- extracted netlist available
- `signoff_ready: true`
- `signoff_blockers: []`

## Routing Note

The signoff GDS contains only DRC-clean detailed geometry. The complete visual
GDS keeps remaining guide geometry so intended internal connectivity can be
inspected. For 32x16, generated macro signal pin coverage by drawn route
geometry is `367/367`; remaining visual guides are not promoted when they would
cause same-layer spacing conflicts or need missing via stacks.
