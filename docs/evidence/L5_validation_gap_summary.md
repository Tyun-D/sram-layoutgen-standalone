# L5 Validation Gap Summary

## Checks Run

- top-level GDS sanity verification
- module completeness verification
- placement consistency verification
- pin metadata / accessibility audit
- rail stitch plan completeness audit
- routing handoff consistency audit
- candidate geometry / contract risk classification
- optional DRC smoke
- optional LVS feasibility audit
- timing metadata consistency audit

## First-Round Blocker

- The only first-round L5 basic-validation blocker was `top_gds_sanity`.
- First-round parser failures were consistent across tools:
  - `gdstk`: missing referenced cells and unstable parse failure
  - `gdspy`: recursive dependency overflow
  - `KLayout`: hierarchy/topological sort failure

## Passed

- top_gds_sanity
- module_completeness
- placement_consistency
- pin_accessibility
- rail_stitch_audit
- routing_handoff_audit
- candidate_geometry_risk
- timing_metadata_consistency

## Skipped

- No basic-validation check is currently skipped.
- LVS remains a feasibility audit only; it is not a clean-LVS claim.

## Root Cause And Repair

- Root cause was a top-level GDS hierarchy/export defect, not an L5 validator false negative.
- The original integrated GDS omitted dependent leaf cells under imported module hierarchies, so the written library contained top cells with missing references.
- The original assembly also allowed name collisions between wrapper cells and imported source cells, which created self-reference / cycle risk for modules such as `sense_amp` and `write_driver`.
- The repair was implemented in the L4 assembly/export path by switching to complete hierarchical import with per-module namespace prefixing.
- Each imported module now carries a module-local prefix, internal references are rewritten into the prefixed namespace, and self-referential wrapper collisions are redirected to the correct external source hierarchy when needed.
- Post-repair diagnosis reports `missing_referenced_cells_count=0`, `self_reference_count=0`, and `cycle_count=0`.
- The repaired top-level candidate GDS is now parsed successfully by `gdstk`, and `top_gds_sanity_status=PASSED`.

## Candidate Geometry And Contract Pin Impact

- Candidate geometry and contract pins do not necessarily block first-pass L5 basic validation.
- They still block any claim of full validated GDS, DRC clean, LVS clean, and timing closure.

## DRC Smoke Status

- `drc_smoke_status=DRC_SMOKE_RAN_WITH_MARKERS`
- The current DRC smoke result is no longer a GDS parse failure side effect.
- KLayout DRC now runs on the repaired top-level GDS and reports markers that need later triage before any DRC-clean claim.

## Current Gate

- can_claim_L5_basic_validation_passed_now: `True`
- can_claim_validated_full_openyield_gds_now: `False`
- can_claim_drc_clean_now: `False`
- can_claim_lvs_clean_now: `False`
- can_claim_timing_closure_now: `False`

## Remaining Blockers

- No remaining basic-validation blockers.

## Why Full Validated GDS Is Still Not Claimable

- Candidate-geometry modules remain in the integrated top-level candidate.
- Contract-pin modules still need geometry-backed accessibility/LVS proof.
- DRC smoke still reports markers, so `can_claim_drc_clean_now=False`.
- LVS remains blocked by missing top-level netlist/pin-mapping export, so `can_claim_lvs_clean_now=False`.
- Timing metadata is still metadata-consistency only, not timing closure, so `can_claim_timing_closure_now=False`.
- Because those downstream signoff conditions remain open, `can_claim_validated_full_openyield_gds_now=False`.

## Next Priority

- Run or review integrated KLayout DRC smoke and triage all reported markers before any DRC claim.
- Promote contract-pin modules to geometry-backed pin accessibility proof.
- Promote candidate-geometry modules to routing/power/LVS-capable proof before any full-GDS claim.
- Export a consistent top-level netlist and module pin mapping for future LVS.
- Keep timing evidence at metadata/smoke scope; do not claim timing closure.
