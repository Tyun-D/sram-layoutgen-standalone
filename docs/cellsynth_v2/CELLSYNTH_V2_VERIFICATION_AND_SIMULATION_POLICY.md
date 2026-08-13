# CellSynth v2 Verification and Simulation Policy

## Level 0 - Symbolic / Partial-State Validation
Applies during topology/folding/placement search. Checks parent MOS identity, topology preservation, W/L equivalence, legal orientation/fingering, legal diffusion sharing, graph connectivity, PDK lower bounds, routing lower bounds and contact-access lower bounds. No SPICE is run at this level.

## Level 1 - Geometry / Connectivity Precheck
Applies after symbolic geometry generation. Checks ACTIVE/POLY device semantics, contact connectivity, via connectivity, layer connectivity, pin access, incremental rule checks and internal extracted connectivity. Overlap across routing layers without a via is not connectivity.

## Level 2 - Hard Physical Correctness
Complete candidates require full DRC and layout extraction/LVS. Hard gate: `DRC = PASS` and `LVS = PASS`. Candidates with DRC-only PASS are not physically valid Pareto candidates.

## Level 3 - PEX / Electrical Metric Extraction
For DRC+LVS-clean Pareto candidates, run credible parasitic extraction if available. Record wire/via resistance, ground/coupling/diffusion capacitance and pin capacitances, especially for CLK, CLKB, D, Q and feedback nets. If no calibrated extraction exists, report `PEX_UNAVAILABLE`.

## Level 4 - Post-Layout DFF Characterization
For Level-3-qualified top-K candidates only, derive clock polarity from OpenYield source and characterize capture, hold, clock-to-Q, setup, hold, slew, pulse width, input/output capacitance and power over discovered valid PVT/slew/load points. Do not invent unavailable corners.

## Multi-Fidelity Policy
All partial states get cheap analytical bounds. Completed symbolic candidates get routability/geometric prediction. A smaller set gets generated geometry and precheck. Pareto survivors get DRC/LVS. Top-K DRC/LVS-clean candidates get PEX and SPICE characterization. `K` is configurable and recorded.

## Feedback Policy
DRC failures strengthen geometry/routing constraints. LVS disconnects repair connectivity/via/contact/router models. LVS wrong-device failures repair geometry compiler/folding semantics. PEX high CLK capacitance increases clock-access/parasitic cost. High feedback RC increases feedback locality cost. Poor timing updates critical-path weights.

## CELLSYNTH_V2_AUTONOMOUS_CLOSURE_POLICY

Internal verification failures are iterative feedback, not task-level blockers. CellSynth router work must iterate through generation, verification, diagnosis, model repair and regeneration until the stage objective closes or a genuine external blocker/formal infeasibility proof exists.


## Regression Fixture Terminology
- `HISTORICAL_COUNTEREXAMPLE` records a previously observed failure mode that may not be deterministic in a packaged variant.
- `REPRODUCIBLE_REGRESSION_FIXTURE` is an intentional deterministic mutation that must trigger the intended internal/external failure before repair.
- True P/N column candidates require Level1 PASS, external DRC PASS and external LVS PASS before entering the verified frontier.
