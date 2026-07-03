# M4E Direct Implementation Plan

- go_nogo_decision: `PARTIAL_GO_WITH_DEFINED_SCOPE`
- allowed_next_stage: `M5_IMPLEMENT_OPENYIELD_LAYOUTGEN_INTEGRATION`
- No more evaluation is allowed after M4E.

## M5 Scope

- Implement 14 modules directly in M5: arrays, row-path parameterized generators, and wrapper-backed column/data modules.
- Keep 6 modules on `LAYOUTGEN_FALLBACK_WITH_OPENYIELD_SEMANTICS` in M5: `CONTROL_LOGIC`, `GATED_CLOCK_PATH`, `PRECHARGE_ENABLE_PATH`, `SENSE_ENABLE_PATH`, `WORDLINE_ENABLE_PATH`, `WRITE_ENABLE_PATH`.

## Ordered Work Items

1. Refactor `sram_layoutgen/standalone.py` and `sram_layoutgen/openyield_adapter/M3F_optimized_layoutgen_restore.py` so the optimized generator consumes the M4E implementation-binding table.
2. Preserve direct array bindings in `array_aggregation.py` and lock OpenYield-owned counts/orientations there.
3. Convert row-path modules (`row_decoder`, `wordline_decoder`, `decoder_gate_cells`, `wordline_driver_gate_cells`, `DELAY_CHAIN`, `DFF_ROW`) into parameterized generator-owned outputs inside the optimized trunk.
4. Promote wrapper-backed modules (`wordline_driver`, `column_mux`, `sense_amp`, `write_driver`, `precharge`) from semantic placement plans to routed physical ownership with existing real cells.
5. Re-enable net hookup for all 34 mapped net bindings through the optimized top-level generator path.
6. Use `hardcell_power_rail_continuity.py` as the gate before enabling shared-rail behavior on wrappers.

## Deferred Full-Scope Items

- Native OpenYield physical implementations for the six fallback control/time modules.
- Alignment of the frozen 4x4 intent JSON parameters with the 8x64_wpr4 optimized implementation baseline.
- Final proof for shared-rail continuity on wrapper-backed peripherals.
