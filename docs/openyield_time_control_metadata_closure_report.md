# OpenYield TIME Control Metadata Closure Report

This is a metadata-planning closure report only. It does not prove legal routing, legal placement, timing closure, DRC, LVS, or physical readiness.

## Audit Summary

```json
{
  "time_control_metadata_closure_available": true,
  "time_control_metadata_chain_complete": true,
  "precharge_closure_status": "intentional_no_local_gnd_metadata_exception",
  "control_region_crossing_coverage_complete": true,
  "can_enter_very_limited_abstract_to_placement_readiness": true,
  "can_enter_time_control_physical_placement": false,
  "can_enter_standalone_control_placement": false
}
```

## Closure State

```json
{
  "precharge_closure_status": "intentional_no_local_gnd_metadata_exception",
  "precharge_blocker_retained_if_any": null
}
```

## Consistency Checks

| check | value |
| --- | --- |
| time_control_metadata_closure_available | True |
| time_control_metadata_chain_complete | True |
| time_control_decomposition_closed | True |
| time_control_signal_bindings_closed | True |
| time_control_generated_logic_contracts_closed | True |
| time_control_consumer_contracts_closed | True |
| time_control_fast_bundle_closed | True |
| time_control_precharge_constraints_closed | True |
| time_control_region_refinement_closed | True |
| time_control_closure_unblock_closed | True |
| precharge_closure_status | intentional_no_local_gnd_metadata_exception |
| control_region_crossing_coverage_complete | True |
| all_required_crossings_have_adjacency | True |
| all_required_crossings_have_handoff_or_reservation | True |
| all_crossing_budgets_pass | True |
| can_enter_very_limited_abstract_to_placement_readiness | True |
| can_enter_time_control_physical_placement | False |
| can_enter_standalone_control_placement | False |
| safe_for_metadata_planning | True |
| safe_for_physical_placement | False |

## Unresolved Items

- PRECHARGE may still carry a retained metadata-only exception or power blocker.
- rail continuity proof is missing.
- routing proof is missing.
- delay timing proof is missing.
- wen-delay timing proof is missing.
- region refinement is not legal placement.
- crossing coverage is not legal routing.
- shared rail is disabled.
- no DRC/LVS proof exists.
- standalone integration remains blocked.

## Entry Decisions

- can_enter_very_limited_abstract_to_placement_readiness: `True`
- can_enter_time_control_physical_placement: `False`
- can_enter_standalone_control_placement: `False`

