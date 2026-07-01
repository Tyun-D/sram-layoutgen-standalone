# L0 Semantics Gap Summary

## First-Pass Blockers

- OpenYield did not expose explicit `SRAM_TOP` / `BANK` classes.
- OpenYield was row/column oriented and did not expose first-class `word_size` / `num_words` / `words_per_row` / `num_banks` / `num_ports` / `write_mask` parameters.
- `TIME` was a composite control/timing generator without frozen local semantic boundaries.
- Enable paths and decoder-to-wordline handoff were source-backed but still treated as unresolved semantic objects.

## Closure Method In This Pass

- Added a canonical SRAM semantic contract for the supported single-bank scope.
- Added a logical-spec to OpenYield parameter mapping contract, freezing how `num_words`, `word_size`, and `words_per_row` map into `num_rows`, `num_cols`, and `choose_columnmux`.
- Added explicit `SRAM_TOP` and `BANK` semantic contracts, closing the missing explicit-class issue by local canonical contract rather than waiting for upstream source changes.
- Added a `TIME` decomposition contract and standalone control-path semantic contracts for `DFF_ROW`, `GATED_CLOCK_PATH`, `WORDLINE_ENABLE_PATH`, `PRECHARGE_ENABLE_PATH`, `SENSE_ENABLE_PATH`, `WRITE_ENABLE_PATH`, and `DELAY_CHAIN`.
- Added a decoder/wordline handoff contract and froze routing/power/timing handoff semantics at L0.

## Explicit Unsupported Features

- `multi_bank`
- `multi_port`
- `write_mask`
- `write_size`
- `words_per_row_gt_2`
- `column_mux_ratio_gt_2`

## Why Unsupported Features Do Not Block L1

- Current L1 scope is explicitly single-bank, single implicit read/write port, no write-mask, and column-mux ratio limited to 1 or 2.
- Those unsupported features are out of scope rather than unknown semantics, so they no longer count as L0 blockers.

## Why L1 Can Now Start

- `remaining_L0_blockers_count = 0`
- `can_claim_L0_semantics_closed_now = True`
- `can_enter_L1_physical_primitive_closure = True`
- All required semantic objects now have either direct OpenYield source evidence or an explicit canonical local contract.
- Remaining open work is physical primitive realization, placement rules, module GDS generation, routing, rail proof, and signoff.

## L1 Next Work

- Realize the frozen semantic objects with physical primitives.
- Preserve the new logical-to-physical parameter contract while implementing bitcell/peripheral/control primitives.
- Keep unsupported features out of scope until a later semantic generalization pass.
