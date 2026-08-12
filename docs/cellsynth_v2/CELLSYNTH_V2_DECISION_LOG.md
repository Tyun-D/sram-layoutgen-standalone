# CellSynth v2 Decision Log

## 2026-08-11T18:48:09.892172+00:00
- Created persistent CellSynth v2 memory.
- Paused DFF area optimization until architecture gates pass.
- Classified current 9.1017 um^2 DFF as DRC-clean but not LVS-closed.
- Adopted multi-fidelity verification policy and TechnologyDB single-source policy.
- OpenRAM remains reference-only.

## 2026-08-12 PN column routing foundation
- Reclassified `BLOCKED_CELLSYNTH_V2_VERIFIED_COOPT_ENGINE_V1` as a useful diagnostic checkpoint.
- The prior `PN_SIMULTANEOUS_PLACEMENT_GATE` was correctly `FAIL`: global `nmos_dx` movement and bounding-box overlap are not a true common-column P/N placement model.
- The prior routing subproblem was scaffold-only: it admitted a DRC+LVS-clean smaller candidate only after P/N overlap disappeared, and did not repair the overlap routing counterexample.
- `DFF_V2_COOPT_S1_P1p50_DX14p80_B0p42` is frozen as a routing regression because it preserves positive P/N overlap and LVS passes, but DRC reports only local `METAL2.2`/`METAL2.5` spacing violations.
- Next valid abstraction is a common symbolic column set with per-terminal access choices and conflict-aware local routing. Folding remains disabled.
