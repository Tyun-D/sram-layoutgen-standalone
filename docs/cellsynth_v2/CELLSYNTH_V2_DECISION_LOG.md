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


## 2026-08-13 True P/N Common-Column Optimizer
- Closed `PN_SIMULTANEOUS_PLACEMENT_GATE` with solver-generated common-column assignments for the full OpenYield 22-MOS DFF.
- Historical CLK-D short evidence is now separated from deterministic regression fixtures.
- Generic router reuse audit found no illegal DX14.80-specific hardcoding in the column optimizer path.


## 2026-08-13 Shared Diffusion OD/Routing Co-Optimization
- Reclassified `DFF_V2_PN_COLUMN_GATE_SORTED_P1p8` as `TRUE_PN_COLUMN_CORRECTNESS_MILESTONE`, not QoR baseline.
- First shared-diffusion DRC/LVS-valid candidate: `DFF_V2_SHARED_DIFF_P1p45`, area `233.24` um^2, active islands `4`, contacts `50`.


## 2026-08-13 Routing-Aware FEOL/BEOL Style Restoration
- Recovered the user-specified historical routing-aware package and classified it as `HISTORICAL_LAYOUT_STYLE_REFERENCE` pending current LVS revalidation.
- Rejected the 233.24 um^2 shared-diffusion output as a QoR/style baseline while preserving it as a correctness milestone.
- Generated `DFF_V2_COMPACT_FEOL_BEOL_DP1p45_S7p15_RP0p3` with compact in-cell routing tracks; DRC/LVS PASS and high-layer length reduced versus the 233.24 um^2 rejected baseline.


## 2026-08-13 DFF_TG4_INV7 QoR Baseline Reproduction
- Revalidated `DFF_TG4_INV7` as `VERIFIED_QOR_BASELINE` using current OpenYield golden LVS wrapper and FreePDK45 DRC/LVS.
- Reproduced the TG4-style project-native generator path as `DFF_V2_TG4_INV7_QOR_REPRODUCED`; DRC/LVS PASS, area `58.450613` um^2, area ratio `1.0`.
- Terminal access policy was corrected for future CellSynth v2 work: internal terminals are local route endpoints, not mandatory global/high-layer ports.

## 2026-08-13T16:18:56.364979+00:00 DFF 9.1 Compact LVS Closure
- Repaired the historical `DFF_TOPO_SHARED_00_7_TRAIL` compact topology with minimal local pin/gate/body/S-D connectivity additions.
- Best area valid candidate `DFF_9P1_REPAIR_ITER012` is DRC/LVS PASS at `29.199063` um^2; formal SRAM top remains unchanged.

## 2026-08-13T17:17:19.391396+00:00 DFF 9.1 Local Interconnect Compaction
- Accepted local-interconnect repair: same-net same-row M3/VIA2 handoff de-duplication plus trunk-pitch compaction.
- Rejected global M2-only trunk replacement because it created LVS shorts among boundary signals under frozen FEOL.


## 2026-08-13T17:47:22.328722+00:00 4-Island FEOL/BEOL Co-Optimization
- FEOL relational placement was re-opened because TP215 route audit showed terminal distribution caused the dominant BEOL cost.
- Accepted localized trunk family; rejected pure M2-only trunk removal due LVS shorts/M2 conflicts.

## Rectangular Cell Envelope Decision
- Human review rejected `DFF_4I_LOCAL_WIDE_D` as Phase-1 final because internal trunks still extend beyond the device body and define the final bbox.
- CellSynth v2 now treats the rectangular cell envelope as a solve-time hard constraint, not a post-process bbox.
- Internal route overflow must generate placement/routing/envelope feedback; only formal pins may occupy boundary corridors.


## 2026-08-13T18:23:53.331759+00:00 Rectangular Envelope Co-Optimization
- Added solve-time rectangular envelope audits and rejected post-hoc bbox as a promotion criterion.
- Central unified track-band counterexamples failed DRC/LVS; retained localized topology inside predeclared envelopes for human review.
