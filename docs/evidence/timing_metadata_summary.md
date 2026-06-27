# Timing Metadata Summary

## Delay Chain

- Timing object: `DELAY_CHAIN`
- Source signal: `rbl`
- Target signal: `rbl_delay`
- Stage count: `9`
- Load policy: `four_load_inverters_per_stage`
- Inversion: `odd_stage_chain_inverts`
- Model corners: `nom, ff, ss`
- VDD: `1.0 V`
- TEMP: `25 C`
- Worst smoke delay: `2.15738e-10 s` at `ss`

## Corner Delays

- `nom`: rise-to-fall `1.963452e-10 s`, fall-to-rise `1.87624e-10 s`
- `ff`: rise-to-fall `1.801558e-10 s`, fall-to-rise `1.715128e-10 s`
- `ss`: rise-to-fall `2.15738e-10 s`, fall-to-rise `2.067219e-10 s`

## Status

- Evidence type: `ngspice_smoke_only`
- Proof status: `not_formal_proof`
- Timing closure status: `not_timing_closure`
- Physical integration status: `not_enabled`