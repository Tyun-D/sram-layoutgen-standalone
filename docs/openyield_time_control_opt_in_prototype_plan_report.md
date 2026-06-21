# OpenYield TIME Control Default-Off Prototype Plan

This is a planning artifact only. It does not modify standalone integration, routing, GDS writing, or physical placement.

## Audit Summary

```json
{
  "default_off_experimental_opt_in_prototype_plan_available": true,
  "default_enabled": false,
  "legacy_path_unchanged": true,
  "can_modify_standalone_now": false,
  "can_generate_time_control_gds_now": false,
  "can_enter_physical_placement_now": false
}
```

## Prototype Contract

```json
{
  "default_enabled": false,
  "legacy_path_unchanged": true,
  "standalone_py_modified": false,
  "routing_modified": false,
  "gds_writer_modified": false,
  "physical_gds_generated": false,
  "shared_rail_enabled": false,
  "uses_time_as_single_macro": false,
  "allows_only_metadata_prototype": true
}
```

## Phased Steps

| step | allowed | default enabled | touches | forbidden |
| --- | --- | --- | --- | --- |
| prototype_config_surface_only | True | False | future spec/config surface only | standalone.py, routing, gds writer |
| abstract_subblock_row_packing_plan | True | False | metadata plan objects, abstract region packing | physical placement, GDS generation, real routed wires |
| consumer_handoff_stub_contracts | True | False | metadata-only consumer handoff reservations | sense/write/WL physical rewiring, shared rail |
| standalone_opt_in_gate_review | False | False | standalone.py only after a later gate | current turn integration |

## Candidate Interfaces

| interface | future plan kind | must stay default-off | blocked by |
| --- | --- | --- | --- |
| ADDR_DFF_ROW | abstract_dff_row | True | addr bus physical proof missing, standalone integration blocked |
| DATA_DFF_ROW | abstract_dff_row | True | data bus physical proof missing, standalone integration blocked |
| GENERATED_LOGIC_CLUSTER | stdcell_row_abstract_cluster | True | stdcell physical library proof missing, routing proof missing |
| PRECHARGE_HANDOFF | consumer_handoff_reservation_only | True | rail continuity proof missing, routing proof missing |
| WORDLINEDRIVER_HANDOFF | consumer_handoff_reservation_only | True | wordline routing proof missing, decoder coordination unresolved |

## Consistency Checks

| check | value |
| --- | --- |
| default_off_experimental_opt_in_prototype_plan_available | True |
| stage_c_gate_passed | True |
| time_control_metadata_closure_available | True |
| legacy_path_unchanged | True |
| default_enabled | False |
| can_modify_standalone_now | False |
| can_generate_time_control_gds_now | False |
| can_enter_physical_placement_now | False |
| can_claim_routing_proof | False |
| safe_for_metadata_prototype_only | True |

## Unresolved Items

- This plan is intentionally non-executable in the main generator path.
- No standalone integration is allowed in this stage.
- No TIME/control physical placement is allowed in this stage.
- No TIME/control GDS is allowed in this stage.
- No routing proof, DRC proof, or LVS proof is added by this plan.
- Decoder/TIME boundary still needs a later coordinated physical proof.
