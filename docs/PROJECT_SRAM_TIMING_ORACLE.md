# Project SRAM Timing Oracle

## Status

- oracle_status: `BLOCKED_BY_EXACT_SOURCE_GAPS`
- allowed derivation policy: `UPSTREAM_EXACT | CURRENT_SOURCE_EXACT | DERIVED_FROM_EXACT_RELATIONS`

## Blocking Fields

- `TIME_schedule`: startup clamp overlaps the first nominal functional cycle, so the first valid cycle is not frozen by exact source text alone.
- `write_sample_point`: upstream write proof measures internal storage-node Q/QB, while the current top-level interface exposes SA outputs instead.
- `disabled_hold_semantics`: upstream hold evidence is single-cell SNM/DC, not top-level transient hold behavior.
