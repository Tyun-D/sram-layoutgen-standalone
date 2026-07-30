# Decoder Live Baseline Recovery Audit

## Result

- status: `BLOCKED_MISSING_LIVE_BASELINE`
- branch: `project/mainline-inventory-20260726`
- current_head_before_followup: `68e7340daaecbcc48a23cce6757e8247efedfbc1`

## Search Performed

- filesystem search roots:
  - `/data1/qujh`
  - `/tmp/qujh_delay_chain_scratch`
- searched for:
  - `*decoder*machine*gate*.json`
  - `*decoder*.lyrdb`
  - `*24*marker*`
  - `*decoder*negative*summary*.json`
  - `*decoder*clean.gds`
  - `*decoder*baseline*lock*.json`
  - strings: `METAL2.2`, `METAL2.5`, `drc_marker_count=24|72`, `horizontal_m3_bus`, `vertical_m2_link`
- result:
  - matched files: `0`
  - stash entries: `0`
  - git history contains decoder audit commits, but no recovered live executable baseline artifact

## What Is Missing

- the exact decoder clean/baseline GDS associated with the user-requested live `24-marker` state
- the corresponding marker database / atlas
- a decoder-specific machine gate and negative summary proving:
  - `EN = horizontal_m3_bus`
  - `WL*_pre = vertical_m2_link`
  - `routing/power/connectivity/foreign-net/negative = true`
- a baseline lock tying those artifacts to immutable SHA values

## Recovery Boundary

- Because the baseline was not recovered, it would be non-defensible to fabricate the `24-marker` state or resume M2-only edits from an inferred proxy.
- The minimum safe recovery path is:
  - recover the exact baseline artifact bundle
  - lock its SHA
  - resume only `METAL2.2 x16` and `METAL2.5 x8` one-parameter-at-a-time edits
