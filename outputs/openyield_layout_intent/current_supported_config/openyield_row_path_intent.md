# OpenYield Row Path Intent

- physical_role: `ROW_PATH`
- modules: row_decoder, wordline_decoder, decoder_gate_cells, wordline_driver, wordline_driver_gate_cells
- row_address_width: `2`
- relation: Wordline driver fanout must match num_rows and every WL[i] must map one-to-one onto a bitcell row.
- pitch alignment: Row path geometry must align to bitcell array row pitch before structure-complete SRAM GDS can exist.
- routing expectation: decoder output -> WL driver input -> WL[i] should remain an explicit R3/R4 routing chain with row-pitch alignment.

## Candidate Geometry Modules

- row_decoder
- wordline_decoder
- decoder_gate_cells
- wordline_driver_gate_cells

## R3/R4 Required Work

- R3 must define a real row-path generator boundary for decoder stages and WL driver composition.
- R3 must define row-pitch-owned placement anchors relative to ARRAY_CORE.
- R4 must define decoder-to-driver and driver-to-WL routing implementation rather than contract-only handoff.
