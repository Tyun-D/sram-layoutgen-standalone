# OpenYield L5 Validation Report

## Summary

- top_gds_sanity_status: `FAILED`
- module_completeness_status: `PASSED`
- placement_consistency_status: `PASSED`
- pin_accessibility_status: `PASSED`
- rail_stitch_audit_status: `PASSED`
- routing_handoff_audit_status: `PASSED`
- candidate_geometry_risk_status: `PASSED`
- drc_smoke_status: `FAILED`
- lvs_feasibility_status: `LVS_BLOCKED_BY_MISSING_NETLIST`
- timing_metadata_consistency_status: `PASSED`
- remaining_L5_basic_validation_blockers_count: `1`
- can_claim_L5_basic_validation_passed_now: `False`
- can_claim_validated_full_openyield_gds_now: `False`
- can_claim_drc_clean_now: `False`
- can_claim_lvs_clean_now: `False`
- can_claim_timing_closure_now: `False`

## Check Results

- `top_gds_sanity`: `FAILED`. All available GDS parsers failed to parse the top-level candidate.
- `module_completeness`: `PASSED`. All 20 required L3 modules are present in placement and top-level references.
- `placement_consistency`: `PASSED`. Placement metadata is numerically consistent with the top-level floorplan.
- `pin_accessibility`: `PASSED`. Pin metadata audit emitted with contract-pin risks recorded.
- `rail_stitch_audit`: `PASSED`. Rail stitch plan covers VDD/GND and all modules.
- `routing_handoff_audit`: `PASSED`. Routing handoff captures semantic net ownership and unresolved detailed-routing items.
- `candidate_geometry_risk`: `PASSED`. Candidate-geometry and contract-pin risk classes recorded for downstream DRC/LVS/timing gates.
- `drc_smoke`: `FAILED`. KLayout DRC smoke command failed.
- `lvs_feasibility`: `LVS_BLOCKED_BY_MISSING_NETLIST`. No generated top-level netlist is available for LVS.
- `timing_metadata_consistency`: `PASSED`. Timing metadata remains traceable from DELAY_CHAIN into routing handoff.

## Recommended Next Validation Tasks

- Run or review integrated KLayout DRC smoke and triage all reported markers before any DRC claim.
- Promote contract-pin modules to geometry-backed pin accessibility proof.
- Promote candidate-geometry modules to routing/power/LVS-capable proof before any full-GDS claim.
- Export a consistent top-level netlist and module pin mapping for future LVS.
- Keep timing evidence at metadata/smoke scope; do not claim timing closure.
