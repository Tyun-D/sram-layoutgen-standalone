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
