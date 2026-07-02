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

## Passed

- module_completeness
- placement_consistency
- pin_accessibility
- rail_stitch_audit
- routing_handoff_audit
- candidate_geometry_risk
- timing_metadata_consistency

## Skipped


## Candidate Geometry And Contract Pin Impact

- Candidate geometry and contract pins do not necessarily block first-pass L5 basic validation.
- They still block any claim of full validated GDS, DRC clean, LVS clean, and timing closure.

## Current Gate

- can_claim_L5_basic_validation_passed_now: `False`
- can_claim_validated_full_openyield_gds_now: `False`
- can_claim_drc_clean_now: `False`
- can_claim_lvs_clean_now: `False`
- can_claim_timing_closure_now: `False`

## Remaining Blockers

- top_gds_sanity: Top-level GDS could not be parsed into a trustworthy validation view.

## Why Full Validated GDS Is Still Not Claimable

- Candidate-geometry modules remain in the integrated top-level candidate.
- Contract-pin modules still need geometry-backed accessibility/LVS proof.
- DRC/LVS/timing closure are not fully proven in this pass.

## Next Priority

- Run or review integrated KLayout DRC smoke and triage all reported markers before any DRC claim.
- Promote contract-pin modules to geometry-backed pin accessibility proof.
- Promote candidate-geometry modules to routing/power/LVS-capable proof before any full-GDS claim.
- Export a consistent top-level netlist and module pin mapping for future LVS.
- Keep timing evidence at metadata/smoke scope; do not claim timing closure.
