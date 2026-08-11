# CellSynth v2 Verification API

## Level0Validator
Inputs: symbolic state, GoldenSpec, TechnologyDB. Outputs: PASS/FAIL, lower bounds, symbolic failure schema. Cost: cheap. Cache key: canonical_hash(S).

## Level1ConnectivityChecker
Inputs: generated geometry/resource graph. Outputs: connectivity, via/contact correctness, pin access, internal extracted graph. Cost: moderate. Feedback: router/contact/pin planner.

## DRCOracle
Inputs: GDS, top, TechnologyDB version, KLayout deck. Outputs: DRC_PASS/DRC_FAIL, marker schema. Cost: external. Feedback: geometry/routing/compaction constraints.

## LVSOracle
Inputs: GDS, top, golden spice, golden subckt, pin map, LVS deck. Outputs: LVS_NOT_RUN/LVS_SETUP_FAIL/LVS_COMPARE_FAIL/LVS_PASS plus diagnostic schema. Feedback: geometry compiler, routing connectivity, pin labeling, model mapping.

## PEXOracle
Inputs: DRC+LVS clean GDS. Outputs: PEX_AVAILABLE_VALIDATED/PEX_AVAILABLE_UNVALIDATED/PEX_UNAVAILABLE and metrics. Feedback: parasitic cost model.

## CharacterizationOracle
Inputs: PEX-qualified netlist, source-derived behavior, PVT/slew/load grid. Outputs: timing/power/capacitance metrics. Feedback: critical-net weights.
