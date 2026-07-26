# OpenYield R3 Minimum Implementation Plan

## Target Configuration

{
  "word_size": 4,
  "num_words": 4,
  "words_per_row": 1,
  "parameterized_beyond_baseline": true
}

## Minimum Scope

- array-centric layout with bitcell_array as the physical core
- generator-owned main/dummy/replica array placement with meaningful boundary positions
- row decoder and wordline driver composition aligned to row pitch
- precharge/column_mux/sense_amp/write_driver composition aligned to column pitch
- control modules placed in a dedicated periphery region with explicit ownership
- structure-complete SRAM GDS prototype generation through the existing GDS backend
- R3 structure report covering hierarchy, placement regions, and claimed limits

## Explicitly Not Required

- DRC clean
- LVS clean
- complete routing closure
- timing closure
- multi-bank support
- multi-port support

## Deliverables

- structure-complete module layouts
- placement_plan with array/row/column/control regions
- structure_complete_sram_gds prototype
- R3 structure report with non-signoff gate wording

## Constraints

- Do not hard-code 4x4, even though the baseline config remains 4x4.
- Do not use OpenRAM as a black-box generator.
- Do not route everything in R3; leave WL/BL/control/power/pin proof to R4.
