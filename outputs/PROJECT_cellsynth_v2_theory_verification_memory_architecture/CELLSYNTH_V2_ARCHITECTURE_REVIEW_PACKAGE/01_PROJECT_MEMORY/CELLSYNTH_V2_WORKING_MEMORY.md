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
