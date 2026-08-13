# CellSynth v2 Anti-Patterns

- Treating DRC PASS as electrical correctness.
- Calling schematic transient simulation post-layout verification.
- Routing M1/M2 overlap without VIA1 as connected.
- Ranking candidates by area before LVS.
- Using OpenRAM or external cells as geometry source.
- Generating many names for identical geometry.
- Hard-coding FreePDK45 rules in multiple code paths.
- Reserving a fixed central channel by default.
- Assigning one contact to every MOS terminal without node-level access reasoning.
- Running expensive SPICE on every partial search state.
- Global NMOS-row translation is not simultaneous P/N placement.
- Positive PMOS/NMOS bounding-box overlap is not proof of paired-column placement.
- Fixed terminal-to-M2 vertical-access templates are incompatible with general simultaneous P/N placement.
- A routing-subproblem gate must not PASS merely because external DRC/LVS failures were ignored.
- Constant contact/via/routing-resource counts across all search states do not demonstrate contact/routing co-optimization.

## CELLSYNTH_V2_AUTONOMOUS_CLOSURE_POLICY

Internal verification failures are iterative feedback, not task-level blockers. CellSynth router work must iterate through generation, verification, diagnosis, model repair and regeneration until the stage objective closes or a genuine external blocker/formal infeasibility proof exists.
