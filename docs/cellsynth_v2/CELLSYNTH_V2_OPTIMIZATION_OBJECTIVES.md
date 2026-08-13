# CellSynth v2 Optimization Objectives

Hard constraints precede optimization: DRC, LVS, W/L exactness, topology exactness and pin access. Feasible candidates are ranked on a Pareto vector:

- area
- extracted/estimated delay
- power
- CLK capacitance
- feedback parasitic
- wirelength
- via count
- pin-access penalty
- congestion
- diffusion breaks

Produce `BEST_AREA`, `BEST_DELAY`, `BEST_ROUTING`, `BEST_POWER` and `BEST_BALANCED` only when the required metric fidelity is available.


## Verified QoR Frontier Policy
Candidates enter QoR Pareto only after Level1, external DRC, and external LVS pass. Track area, width, height, ACTIVE islands, shared diffusion, diffusion breaks, contacts, vias, M1/M2/M3 length, high-layer length, clock/feedback route proxies, pin access, whitespace, DRC and LVS.


## DFF_TG4_INV7 QoR Baseline
`DFF_TG4_INV7` is the current verified OpenYield DFF QoR baseline for nf=1 compact-style work: `58.450613 um^2`, DRC/LVS PASS. Future generated DFF QoR claims must compare against it, not against the 139/233/388/566 um^2 correctness milestones.
