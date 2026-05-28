# Integration Notes

This generator is now organized around physical macro contracts rather than
hand-drawn abstract standard cells.

## Cell Sources

Accepted signoff sources:

- bundled FreePDK45/OpenRAM hardcell GDS files in `technology/freepdk45/gds_lib/`;
- generated replacement macro GDS files in
  `technology/freepdk45/gds_lib/openram_replacements/`;
- top-level SRAM interconnect emitted by this generator.

Rejected for signoff:

- synthetic generated-cell GDS created at runtime;
- abstract-only replacement macro entries;
- missing physical GDS for any used hardcell or replacement macro;
- abstract pin fallback used to hide missing GDS TEXT pin labels.

## Placement Contract

Every placed object contributes a physical occupied bounding box measured from
its real GDS where available. The verifier checks hardcell arrays, generated
replacement macros, and individually placed hardcells for overlap. Any positive
area overlap is reported as `cell_overlap`.

The current floorplan follows the OpenRAM idea of separating:

- bitcell/dummy/replica arrays;
- row decoder and wordline drivers;
- column mux, precharge, write driver, sense amp, and tri-gate regions;
- control and delay-chain logic.

The implementation is still lightweight, but the placement rule is strict:
occupied area cannot be reused by another macro.

## Routing Views

Use the GDS views by purpose:

- `*.gds`: full signoff candidate. This is the file passed to KLayout DRC/LVS.
- `*.complete.gds`: visual routing GDS. It keeps guide geometry so internal
  connectivity is easier to inspect side-by-side with OpenRAM output.
- `*.route_guides.gds`: debug-only routing guide view.

The report has two separate connectivity checks:

- `generated_pin_route_audit`: real generated-macro GDS pins covered by drawn route geometry.
- `generated_pin_route_or_guide_audit`: same coverage allowing route guides.

For signoff, `generated_pin_route_audit.all_generated_signal_pins_covered` must
be true.

## Replacement Workflow

When a new optimized macro is available:

1. Put the new GDS in `technology/freepdk45/gds_lib/openram_replacements/`.
2. Ensure GDS TEXT labels name the public pins.
3. Run `python examples\materialize_brick_library.py --force`.
4. Generate SRAM sizes that exercise the macro.
5. Run `examples\run_external_signoff.ps1`.
6. Check `*.report.json` for `signoff_ready: true` and empty
   `signoff_blockers`.

