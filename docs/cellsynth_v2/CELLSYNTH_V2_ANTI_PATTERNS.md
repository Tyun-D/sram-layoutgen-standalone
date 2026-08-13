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


## Additional Anti-Patterns From True P/N Column Closure
- ANTI-PATTERN: treating `pmos_nmos_overlap_x > 0` as sufficient proof of simultaneous P/N placement.
- ANTI-PATTERN: accepting a column candidate without symbolic/GDS column-coordinate correspondence.
- ANTI-PATTERN: using a repaired regression fixture as a placement architecture template.


## Shared Diffusion Anti-Patterns
- ANTI-PATTERN: calling two metal-connected isolated ACTIVE rectangles shared diffusion.
- ANTI-PATTERN: treating `paired_column_count` as a QoR objective.
- ANTI-PATTERN: allowing correctness milestones to overwrite compact QoR baselines.


## Routing-Aware Style Anti-Patterns
- ANTI-PATTERN: treating a DRC/LVS-correct macro-like routed DFF as a layout-quality baseline.
- ANTI-PATTERN: routing every internal terminal to a high global M3 trunk by default.
- ANTI-PATTERN: exposing internal DFF nets at the cell boundary or using boundary-like long lines for local feedback.


## QoR Baseline Anti-Patterns
- ANTI-PATTERN: keeping a DRC/LVS-correct but M2/M3-trunk-dominated 139 um^2 DFF as the quality baseline after a 58.45 um^2 DRC/LVS-clean project-native baseline is available.
- ANTI-PATTERN: treating every internal transistor terminal as a global routing port.
