# PASS_OPENYIELD_CELLSYNTH_V2_THEORY_VERIFICATION_MEMORY_ARCHITECTURE

## Answers Required By Stage
1. DRC alone is insufficient because it proves local geometry rules, not schematic equivalence, missing vias, wrong device connectivity, wrong pin mapping or sequential behavior.
2. LVS must prove the extracted layout netlist has the same MOS devices, W/L, G/S/D/B connectivity and pins as `DFF_GOLDEN_ELECTRICAL_SPEC`.
3. PEX feeds back CLK/feedback/D/Q parasitics, via/wire resistance, capacitance and pin capacitance into placement/routing/folding costs.
4. Post-layout SPICE is required for capture behavior, inactive-edge hold, clock-to-Q, setup/hold, slew, input/output capacitance and power.
5. Every partial state uses Level-0 symbolic checks; every complete geometry uses Level-1 precheck; Pareto candidates require DRC/LVS; top-K DRC/LVS-clean candidates get PEX/SPICE.
6. Verification results alter solver decisions by strengthening constraints, repairing router/via/contact models and adjusting critical-net/parasitic costs.
7. Symbolic state is `{transistor_clusters, pn_ordering, trail_topology, finger_assignment, sd_orientation, diffusion_breaks, gate_alignment, od_contour_requirements, contact_access_decisions, pin_access_decisions, routing_topology}`.
8. Folding solves `nf_i` and finger partitions; placement solves rows/columns/trails/orientations; routing solves terminal access, layer/via/track and pin topology.
9. Pruning lower bounds cover width, height, area, diffusion breaks, routing tracks, vias, contact access and wirelength.
10. ACTIVE contours are symbolic OD segments with width, gate crossings, contact/access needs, local jogs and break reasons.
11. Contact multiplicity is optimized per electrical node using resistance/routability/capacitance/area tradeoffs.
12. Electrical routing connectivity is guaranteed by a layered graph with explicit vias; overlap alone is never connectivity.
13. The central routing-channel assumption is eliminated by making routing resources TechnologyDB-backed and placeable within legal device/pin regions.
14. Adopted literature ideas: route-aware placement, simultaneous folding/placement, ghost-via/pin-access reservation, CP-SAT/layered grid graph, lower-bound tightening, timing-aware objectives and ML only as heuristic guidance.
15. Rejected ideas: importing advanced-node/ASAP7/Nangate/SKY/GF/ASAP geometries, replacing FreePDK45 rules, treating RL as correctness oracle and ranking DRC-only cells as final.
16. Future runs must read `PROJECT_GLOBAL_WORK_RULES.md`, `CELLSYNTH_V2_WORKING_MEMORY.md`, `CELLSYNTH_V2_VERIFICATION_AND_SIMULATION_POLICY.md` and `CELLSYNTH_V2_ALGORITHM_ARCHITECTURE.md`.
17. Current 9.1017 um^2 layout is not yet LVS-correct: `LVS_FAIL`; reason: LVS setup reached extraction but failed top-cell schematic correspondence; generated layout top is DFF_TOPO_SHARED_00_7_TRAIL while golden subckt is dff_openyield_original.
18. Before area optimization resumes, implement TechnologyDB, GoldenSpec/LVS wrapper, Level-1 connectivity extraction, symbolic state, lower-bound pruning, layered router and DRC/LVS feedback.

## Invariants
- PDK changed = false
- external standard-cell library used = false
- OpenYield logical topology changed = false
- transistor W/L changed = false
- formal SRAM top modified = false
