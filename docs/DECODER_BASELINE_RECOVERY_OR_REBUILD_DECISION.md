# Decoder Baseline Recovery Or Rebuild Decision

- historical_recovery_status: `NOT_RECOVERED`
- decision: `REPRODUCIBLE_DECODER_BASELINE_REBUILD`

## Why Recovery Was Rejected

- The final recovery pass covered Git reflog, unreachable objects, string-history search, checkpoints, tmp roots, and quarantine.
- No complete baseline bundle was recovered that simultaneously binds GDS SHA, generator/config SHA, DRC database, machine gate, negative summary, and route strategy.
- A historical `24-marker` claim therefore cannot be restored honestly.

## What Rebuild Means Here

- Rebuild is now the only defensible path.
- Any rebuilt baseline must be recorded as a new reproducible baseline, not mislabeled as the lost historical one.
- The preferred contract remains `EN = horizontal_m3_bus` and `WL*_pre = vertical_m2_link`, but fresh DRC counts must come from the new run.

## Remaining Boundary

- Current repo evidence still lacks an executable decoder-specific production gate, determinism harness, negative suite, and marker-delta repair loop.
- Therefore the project can select rebuild as the path forward, but cannot yet claim active decoder closure beyond that boundary.
