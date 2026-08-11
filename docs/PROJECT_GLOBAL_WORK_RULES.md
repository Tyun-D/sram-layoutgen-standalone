# Project Global Work Rules

This file is the authoritative global work-rules document for this project. It applies to all future analysis, code generation, GDS generation, verification, status reporting, and human-review packaging.

## RULE-A: Mandatory Work-Start Read

Before every new analysis, modification, generation, or verification task, the worker must read:

- `docs/PROJECT_GLOBAL_WORK_RULES.md`
- `docs/PROJECT_CURRENT_STATUS.json`
- the latest relevant section of `docs/PROJECT_TASK_MASTER_LOG.md`

The task log must begin with a `WORK_START_RULE_AUDIT` record containing:

- `GLOBAL_RULES_READ = true`
- `GLOBAL_RULES_SHA = <sha256>`
- `CURRENT_STATUS_READ = true`
- `CURRENT_STATUS_SHA = <sha256>`
- `LATEST_MASTER_LOG_READ = true`
- `LATEST_MASTER_LOG_SHA = <sha256>`

If this is not completed, the worker must not modify code, generate GDS, or return a PASS status.

## RULE-B: OpenYield Original Netlist Is Circuit Authority

Any claim using these phrases must trace to OpenYield original source, original netlist generator, original SPICE, or a reproducibly expanded canonical netlist:

- `OpenYield exact`
- `OpenYield source exact`
- `OpenYield transistor topology`
- `OpenYield DFF`
- `OpenYield WL driver`
- `OpenYield precharge`
- `OpenYield write driver`

The evidence must record:

- source path
- source SHA
- source snapshot or commit
- module/subckt name
- Pin order
- MOS count
- W/L
- G/S/D/B

The following are not `OPENYIELD_ORIGINAL_SOURCE_EXACT` by themselves:

- existing GDS
- canonical physical identity
- repaired source-bound composite
- OpenRAM adapter
- manual reconstruction

They must be classified by their true authority level, such as:

- `CURRENT_SOURCE_BOUND`
- `DERIVED_IMPLEMENTATION`
- `RECOVERED_FROM_PHYSICAL_EVIDENCE`
- `OPENRAM_BACKED`
- `MANUAL_RECONSTRUCTION`

If OpenYield original netlist authority cannot be recovered, the correct blocking state is:

`BLOCKED_BY_MISSING_OPENYIELD_ORIGINAL_NETLIST_AUTHORITY`

Do not silently substitute existing GDS, placeholders, or reconstructions.

## RULE-C: No Placeholder Or Synthetic Authority In Formal Candidates

Formal candidates must not use:

- placeholder netlists
- dummy netlists
- synthetic topology
- hand-written approximation

Exploratory experiments may use them only if explicitly marked:

`EXPLORATORY_ONLY`

## RULE-D: Existing FreePDK45 Is Fixed

Permanent constraints:

- `PDK changed = false`
- `external standard-cell library used = false`

Do not use existing GDS/LEF/CDL from:

- Nangate45
- SKY130
- GF180
- ASAP7
- any other PDK or standard-cell library

External algorithms or layout ideas may be studied, but final geometry must be regenerated from current FreePDK45 rules/models and the correct circuit-authority netlist.

## RULE-E: Circuit Topology And W/L Are Locked

Unless explicitly authorized by the circuit owner, layout generation must not change:

- MOS count
- MOS type
- W/L
- logical connectivity
- clock semantics
- polarity

Allowed layout optimization includes:

- placement
- source/drain legal flip
- diffusion sharing
- folding
- well sharing
- rail planning
- Pin planning
- routing
- orientation
- abutment

## RULE-F: Final GDS Is Physical Fact Authority

Physical facts must be independently recoverable from final GDS:

- bbox
- gap
- orientation
- placement
- Pin coordinate
- route length
- top count
- abutment

Generator JSON alone is insufficient. Physical PASS reports must include:

`REPORT_VS_FINAL_GDS_MATCH = true`

## RULE-G: Candidates Must Be Geometrically Distinct

Named candidate families such as `SOURCE_ORDER`, `DIFFUSION_OPT`, `CLOCK_CENTRIC`, `FOLDED`, and `PARETO` must pass a geometry diversity gate.

The gate must compare at least:

- placement graph
- transistor origins
- orientation
- route geometry
- GDS geometry signature

If two candidates have identical geometry, classify duplicates as:

`DUPLICATE_CANDIDATE`

Do not copy one layout under multiple names and call it a multi-candidate search.

## RULE-H: Validators Must Check Result Semantics

Program execution is not sufficient evidence.

For SPICE, `returncode = 0` is not a functional PASS. Required checks include:

- log health PASS
- all measures numeric
- expected high greater than threshold
- expected low less than threshold
- edge behavior correct

For WL driver, the source truth table must be checked. For example, if the source requires A=B=1 to drive WL high, the validator must explicitly prove that behavior and all other input combinations.

Any of the following must fail the gate:

- fatal
- aborted
- measure failed
- NaN
- wrong logic level

## RULE-I: No PASS Without Actual Experiment

These are not success endpoints:

- `NOT_RUN`
- `SPECIFIED_NOT_GENERATED`
- `PLANNED`
- `PLACEHOLDER`
- `NOT_INSTALLED`
- candidate list only

PASS requires actual generation, verification, failure analysis, repair where needed, and re-verification.

