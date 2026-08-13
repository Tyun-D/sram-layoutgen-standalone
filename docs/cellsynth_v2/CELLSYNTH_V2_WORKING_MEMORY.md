# CellSynth v2 Working Memory

This is the persistent CellSynth v2 project-memory entry point. Future CellSynth work must read this file, the global work rules, the verification policy, and the algorithm architecture before modifying CellSynth code.

## Permanent Read Set
- `docs/PROJECT_GLOBAL_WORK_RULES.md`
- `docs/cellsynth_v2/CELLSYNTH_V2_WORKING_MEMORY.md`
- `docs/cellsynth_v2/CELLSYNTH_V2_VERIFICATION_AND_SIMULATION_POLICY.md`
- `docs/cellsynth_v2/CELLSYNTH_V2_ALGORITHM_ARCHITECTURE.md`

## Core Principles
1. Euler trails are a diffusion-sharing/topology tool, not a complete standard-cell placement algorithm.
2. Do not model a transistor as a permanently fixed isolated rectangle.
3. Folding, placement, diffusion topology, contact access and routing are strongly coupled.
4. ACTIVE/OD geometry must be contour-generated from local electrical and physical requirements.
5. Do not reserve a fixed central routing channel; routing may overlap/interleave with device regions where FreePDK45 permits it.
6. Contacts belong to electrical access nodes, not automatically to every MOS terminal.
7. Routing connectivity is explicit: M1-to-M2 requires VIA1, M2-to-M3 requires VIA2.
8. DRC PASS does not imply electrical correctness.
9. A generated layout is not a valid cell until LVS passes.
10. PEX and circuit characterization are optimization feedback, not merely final reports.
11. Search must operate primarily on canonical symbolic states rather than blindly sweeping physical coordinates.
12. Exact/constraint-based optimization is the correctness backbone; learning can guide ranking or repair but cannot replace DRC/LVS.

## Current Stage Decision
The 9.1017 um^2 DFF remains a compact DRC-clean candidate, but it is not yet a valid electrical cell because LVS is not closed. Area optimization is paused until CellSynth v2 architecture, TechnologyDB, GoldenSpec, LVS, and feedback policies are established.

## Connectivity-First Correctness Baseline

`DFF_V2_CONNECTIVITY_BASELINE` is the first automatically generated OpenYield
22-MOS DFF cell that passed both DRC and LVS.

- DRC: `DRC_PASS`
- LVS: `LVS_PASS`
- bbox: `35.88 x 15.8 um`
- area: `566.904 um^2`
- extracted MOS: `22` (`11 PMOS`, `11 NMOS`)
- golden nets connected: `13/13`
- external pins: `CLK D Q VDD VSS`
- PEX: `UNAVAILABLE`

This cell is a correctness baseline, not an optimized standard cell. Future
optimization must preserve DRC/LVS correctness and may only admit candidates to
the physical Pareto frontier after `Level1Connectivity = PASS`, `DRC = PASS`,
and `LVS = PASS`.

## PN Column Routing Foundation Lesson

`BLOCKED_CELLSYNTH_V2_VERIFIED_COOPT_ENGINE_V1` is retained as diagnostic
evidence, not as a failed experiment to erase.  It demonstrated that reducing
the conservative routing envelope can preserve DRC/LVS, but it did not
demonstrate true simultaneous P/N placement.

Established lessons:

- A single global `nmos_dx` variable is not a column-placement model.
- PMOS/NMOS bounding-box overlap is only a metric, not proof of paired columns.
- True P/N placement requires a common symbolic column set with explicit
  `P(c)`, `N(c)` and `paired_column(c)` assignments.
- The fixed terminal-to-M2 vertical-access template cannot support general
  overlapped P/N device spans.
- `DX14.80` is now the frozen routing regression fixture: transistor placement,
  ACTIVE and POLY stay fixed; only access/routing resources may change.


## Local Router Kernel Decision

Full-DFF P/N placement optimization is paused until the local pin-access and detailed-routing kernel is independently verified. The router must close microbenchmarks and the frozen DX14.80 regression before the P/N column master optimizer resumes.

## CELLSYNTH_V2_AUTONOMOUS_CLOSURE_POLICY

Internal verification failures are iterative feedback, not task-level blockers. CellSynth router work must iterate through generation, verification, diagnosis, model repair and regeneration until the stage objective closes or a genuine external blocker/formal infeasibility proof exists.


## 2026-08-13 True P/N Common-Column Closure
- `DFF_V2_DX14P80_LOCAL_ROUTER_REPAIRED` proved positive P/N overlap is routable but remains a routing regression fixture, not the final placement architecture.
- CellSynth v2 now uses a common symbolic column set with `Pplace[p,c]` and `Nplace[n,c]`; `nmos_dx` is not a master placement variable.
- Best verified paired-column DFF: `DFF_V2_PN_COLUMN_GATE_SORTED_P1p8`, area `388.206` um^2, paired columns `11`, DRC/LVS PASS.


## Shared Diffusion QoR Reset
- MEMORY-A: Common-column is a representation/search variable, not an optimization target. Do not maximize paired columns as the primary objective.
- MEMORY-B: P/N common column does not force common gate; model `SAME_NET_COMMON_GATE`, `DIFFERENT_NET_SPLIT_GATE`, and `ILLEGAL_PAIR` explicitly.
- MEMORY-C: DRC/LVS correctness baselines such as 566/442/388 um^2 prove engine correctness, not layout quality.
- MEMORY-D: Verification failure remains an optimizer oracle: model, solve, generate, verify, counterexample, cut/model repair, re-solve.
- Folding policy: future folding preserves 22 logical parent MOS, but extracted physical MOS count may exceed 22 after parallel-finger normalization.


## 2026-08-13 Routing-Aware Style Restoration
- `DFF_V2_SHARED_DIFF_P1p45` at 233.24 um^2 is retained as DRC/LVS correctness evidence but reclassified as `HUMAN_REJECTED` / `QoR style rejected` because routing is macro-like and high-layer dominated.
- The recovered `PROJECT_OPENYIELD_DFF_ROUTING_AWARE_FEOL_BEOL_CO_OPTIMIZATION` package is the priority style reference, not a source of formal topology or copied polygons.
- Best regenerated compact FEOL/BEOL candidate: `DFF_V2_COMPACT_FEOL_BEOL_DP1p45_S7p15_RP0p3`, area `139.825` um^2, DRC/LVS PASS, OpenYield exact 22T source preserved.


## 2026-08-13 DFF_TG4_INV7 QoR Reproduction
- `DFF_TG4_INV7` is now `VERIFIED_QOR_BASELINE` after current external DRC+LVS revalidation against the OpenYield original 22T golden specification.
- Baseline bbox/area: `13.745 x 4.2525 um`, `58.450613 um^2`; pins `D Q CLK VDD VSS`; extracted MOS `22`.
- The 139.825 um^2 compact FEOL/BEOL candidate remains DRC/LVS-correct but is not a QoR baseline because contacts/VIA1/VIA2 remain fixed at `50/50/50` and routing is M2/M3 dominated.
- The promoted compact path is local-interconnect-first: child-local FEOL/M1, selected M1 landings, short M2 bridge/drop, M3 only when lower layers are infeasible.

## 2026-08-13T16:18:56.364979+00:00 DFF 9.1 Compact LVS Closure
- Phase 1 is `DFF_COMPACT_LVS_CLOSURE`.
- `DFF_TOPO_SHARED_00_7_TRAIL` remains the compact architecture/style seed, not a formal replacement until repaired candidates pass current DRC/LVS.
- `DFF_9P1_REPAIR_ITER012` is the current compact verified best-area candidate: area `29.199063` um^2, DRC/LVS PASS, OpenYield 22T nf=1 preserved.
- The repair methodology is minimal-disturbance counterexample closure: fix pins, gate-net merges, body ties and S/D ownership bridges without reverting to macro-like routing.
