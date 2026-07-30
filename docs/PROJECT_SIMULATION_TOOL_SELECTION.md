# Project Simulation Tool Selection

- logic_primary: `NOT_AVAILABLE_WITH_CURRENT_EVIDENCE`
- logic_secondary: `NOT_AVAILABLE_WITH_CURRENT_EVIDENCE`
- spice_primary: `ngspice`
- spice_secondary: `Xyce`
- post_layout_extractor: `NOT_AVAILABLE_WITH_CURRENT_EVIDENCE`
- waveform_viewer: `gtkwave`

## Selection Reason

- logic: Prefer Icarus only when trusted Verilog exists; current server has Icarus but current project evidence does not.
- spice: Use ngspice as primary because it is available on PATH and matches existing project smoke conventions; use Xyce as secondary cross-check.
- post_layout: Do not claim a post-layout extractor until extraction-rule provenance, layout-netlist binding, and LVS/PEX evidence are all refreshed.

## Blocking Dependencies

- No authoritative project Verilog assets for PNAND2/PNAND3/AND2/AND3/DFF/DFF_BUF/control modules were discovered.
- No current-project post-layout extraction-rule provenance was discovered; pre-layout or historical extracted SPICE must not be relabeled as fresh post-layout simulation.
