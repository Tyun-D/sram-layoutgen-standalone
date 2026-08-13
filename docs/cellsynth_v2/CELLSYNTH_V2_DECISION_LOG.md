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

## CELLSYNTH_V2_AUTONOMOUS_CLOSURE_POLICY

Internal verification failures are iterative feedback, not task-level blockers. CellSynth router work must iterate through generation, verification, diagnosis, model repair and regeneration until the stage objective closes or a genuine external blocker/formal infeasibility proof exists.

## 2026-08-13 Autonomous DX14.80 Router Closure
- Closed `DX14P80_ROUTING_REPAIR_GATE` with frozen transistor/ACTIVE/POLY placement.
- Learned DRC conflicts from METAL2/VIA2 markers and LVS `CLK,D` short counterexample.
- Final repair uses route-only access shifts plus a shared same-net CLK VIA2 bridge.
- Microbenchmarks remain continuous regressions before future P/N column optimizer integration.
