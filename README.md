# sram_layoutgen_standalone

Lightweight FreePDK45 SRAM layout generator for the OpenRAM-stable deliverable.

The current strict flow is intentionally brick based:

- Bitcells and peripheral hardcells are instantiated from the bundled
  `technology/freepdk45/gds_lib/*.gds` libraries.
- Decoder/control/column replacement macros are instantiated from
  `technology/freepdk45/gds_lib/openram_replacements/gen_*.gds`.
- The top layout reads real GDS bounding boxes and GDS TEXT pin labels before
  placement and routing. The strict signoff flow does not use hand-drawn
  fallback standard cells or abstract pin locations.
- Placement uses OpenRAM-style logical origins for storage arrays. Bitcell,
  dummy, and replica cells may use designed boundary stitching when the bundled
  GDS library does so; ordinary module/peripheral overlap is still treated as a
  layout error and is checked by structural audits plus external KLayout DRC.

## Generate One SRAM

```powershell
python -m sram_layoutgen --word-size 16 --num-words 32 --words-per-row 2 --out build/demo_32x16
```

With external KLayout DRC/LVS:

```powershell
powershell -ExecutionPolicy Bypass -File examples\run_external_signoff.ps1 -WordSize 16 -NumWords 32 -WordsPerRow 2 -OutDir build\demo_32x16_signoff
```

## Important Outputs

Each run writes a set of GDS views:

- `*.gds`: signoff-clean candidate used for full KLayout DRC/LVS.
- `*.complete.gds`: visual GDS with complete guide geometry kept for review.
- `*.presentation.gds`: cleaner visual view without debug overlays.
- `*.debug.gds`: richest debug view with module overlays and labels.
- `*.route_guides.gds`: route-guide focused debug view.
- `*.report.json`: machine-readable audit and signoff report.
- `*.report.md`: readable summary.

For the maintained 32x16 comparison, generate a fresh run with:

```powershell
powershell -ExecutionPolicy Bypass -File examples\run_external_signoff.ps1 -WordSize 16 -NumWords 32 -WordsPerRow 2 -OutDir build\compare_openram_32x16\ours_32x16_storage_rows_connected_v2
```

The current 32x16 flow verifies that every storage row has a formal wordline
rail and that each row rail intersects all storage WL pins: left dummy, all
bitcells, replica, and right dummy.

## Replacement Macro Scheme

The replacement contract is stored in:

```text
technology/freepdk45/replacement_macros.json
```

It is regenerated from real OpenRAM-style replacement GDS files:

```powershell
python examples\materialize_brick_library.py --force
```

To replace a decoder, precharge, mux, or control macro later:

1. Add the new physical GDS under `technology/freepdk45/gds_lib/openram_replacements/`.
2. Keep the macro name and pin names compatible, or update the generator role mapping.
3. Regenerate `replacement_macros.json`.
4. Run external signoff on at least a small fixed case and one stress case.

The report field `openram_cell_source_audit.clean` must stay `true`. If a macro
is missing physical GDS, uses synthetic fallback geometry, or lacks required
pin access, signoff is not considered ready.

## Signoff Gates

`signoff_ready` is true only when the report proves:

- bundled FreePDK45 layer mapping is used;
- all used cells/macros have real bundled or OpenRAM-style physical GDS;
- generated/replacement macro signal pins are covered by drawn routes;
- placement overlap audit is clean;
- built-in DRC-lite is clean;
- external full KLayout DRC is clean;
- external KLayout LVS extraction/comparison reports zero items.

Recent verified runs:

- `build/external_signoff_4x32_realpin_strict/`
- `build/compare_openram_32x16/ours_32x16_realpin_strict/`
- `build/external_signoff_8x64_wpr4_realpin_strict/`
