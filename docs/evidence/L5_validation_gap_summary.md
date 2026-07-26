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

## Hierarchy Repair Status

- The top-level GDS hierarchy/export issue is repaired and `top_gds_sanity_status=PASSED`.
- The repaired top-level candidate parses successfully and exposes 20 direct top-level module references.

## Module Completeness Root Cause

- After hierarchy repair, `module_completeness` initially failed even though the top-level GDS already contained all 20 required L3 module instances.
- The failing evidence showed raw top-level references in prefixed form such as `bitcell_array__bitcell_array` and `CONTROL_LOGIC__CONTROL_LOGIC`.
- Root cause was the L5 module completeness checker comparing unprefixed required module names against prefixed top-level GDS direct references without normalization.

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

- No basic-validation check is skipped in the current pass.
- LVS remains a feasibility audit only, not an LVS-clean signoff claim.

## Module Completeness Repair

- The L5 checker now normalizes top-level direct references back to required module names.
- It records both `module_references_seen_raw` and `module_references_normalized` in `module_completeness_report.json`.
- For the current top-level GDS, all 20 required modules are now recognized after normalization.
- `required_modules_missing_from_top_gds_references=[]`
- `module_completeness_status=PASSED`

## Candidate Geometry And Contract Pin Impact

- Candidate geometry and contract pins do not necessarily block first-pass L5 basic validation.
- They still block any claim of full validated GDS, DRC clean, LVS clean, and timing closure.

## Current DRC / LVS Limits

- `drc_smoke_status=DRC_SMOKE_RAN_WITH_MARKERS`, so DRC clean cannot be claimed.
- `lvs_feasibility_status=LVS_BLOCKED_BY_MISSING_NETLIST`, so LVS clean cannot be claimed.
- Candidate geometry and contract-pin scope still block any full validated GDS claim.

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
- DRC smoke still reports markers.
- LVS is blocked by missing top-level netlist export.
- Timing evidence remains metadata consistency only and is not timing closure.

## Next Priority

- Run or review integrated KLayout DRC smoke and triage all reported markers before any DRC claim.
- Promote contract-pin modules to geometry-backed pin accessibility proof.
- Promote candidate-geometry modules to routing/power/LVS-capable proof before any full-GDS claim.
- Export a consistent top-level netlist and module pin mapping for future LVS.
- Keep timing evidence at metadata/smoke scope; do not claim timing closure.
