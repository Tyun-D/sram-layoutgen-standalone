# OpenYield Layout Prototype Generation Report

- legacy baseline attempted: `True`
- legacy baseline GDS generated: `True`
- hybrid OpenYield attempted: `True`
- hybrid OpenYield GDS generated: `True`
- hybrid compacted attempted: `True`
- hybrid compacted GDS generated: `True`
- module coverage available: `True`
- openyield metadata consumed: `True`
- timing metadata consumer used: `True`
- candidate contracts used: `True`
- fallbacks recorded: `True`
- standalone default behavior preserved: `True`
- standalone modified for explicit opt-in: `True`
- routing modified: `False`
- gds writer modified: `False`
- can claim full OpenYield layout now: `False`
- can claim LVS clean now: `False`
- can claim DRC clean now: `False`
- can claim timing closure now: `False`
- can enter physical gap closure: `True`
- can enter guarded OpenYield layout integration: `True`

## OpenYield-Driven Modules

- bitcell_array
- dummy_array
- replica_array
- sense_amp
- write_driver
- column_mux
- wordline_driver

## Fallback Modules

- DELAY_CHAIN
- PRECHARGE
- PRECHARGE_ENABLE_PATH
- SENSE_ENABLE_PATH
- WRITE_ENABLE_PATH
- WORDLINE_ENABLE_PATH
- GATED_CLOCK_PATH
- DFF_ROW

## Physical Gaps

- TIME / DFF / control logic remain candidate-contract or metadata-only; no full physical OpenYield implementation is installed.
- Routing is still legacy/top-level layoutgen routing, not OpenYield-driven routing.
- Shared rail continuity is not proven for repaired/peripheral hardmacros.
- Column mux repaired alias is candidate-only and must not be treated as full signoff collateral.
- No LVS closure, no timing closure, and no full-chip DRC signoff are claimed.
