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
