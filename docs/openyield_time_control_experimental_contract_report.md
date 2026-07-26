# OpenYield TIME Control Experimental Contract Report

This report refines the default-off prototype plan into a structured contract. It remains metadata-only and does not authorize standalone integration, routing, or GDS generation.

## Audit Summary

```json
{
  "experimental_contract_available": true,
  "default_enabled": false,
  "legacy_path_unchanged": true,
  "prototype_subplan_count": 11,
  "can_modify_standalone_now": false,
  "can_generate_time_control_gds_now": false,
  "can_enter_physical_placement_now": false
}
```

## Config Surface

| field | value |
| --- | --- |
| flag_name | enable_openyield_time_control_experimental_placement |
| default_enabled | False |
| allowed_mode | metadata_prototype_only |
| legacy_path_unchanged | True |
| standalone_py_modified | False |
| routing_modified | False |
| gds_writer_modified | False |
| physical_gds_generated | False |
| shared_rail_enabled | False |
| uses_time_as_single_macro | False |

## Prototype Subplans

| subblock | plan kind | region | consumer | metadata ready | physical ready | blocked by |
| --- | --- | --- | --- | --- | --- | --- |
| ADDR_DFF_ROW | abstract_dff_row | generated_logic_region | - | True | False | no legal placement proof, no routing proof, no standalone integration |
| DATA_DFF_ROW | abstract_dff_row | generated_logic_region | - | True | False | no legal placement proof, no routing proof, no standalone integration |
| DELAY_CHAIN_CLUSTER | timing_chain_cluster | delay_chain_region | - | True | False | delay timing proof missing, no legal placement proof, no routing proof |
| WEN_DELAY_CHAIN_CLUSTER | timing_chain_cluster | sense_write_enable_region | - | True | False | wen-delay timing proof missing, no legal placement proof, no routing proof |
| PDRIVE_CLUSTER | buffer_chain_cluster | pdrive_region | - | True | False | no legal placement proof, no routing proof |
| GENERATED_LOGIC_CLUSTER | stdcell_row_abstract_cluster | generated_logic_region | - | True | False | stdcell physical library not proven, no legal routing proof, no DRC/LVS proof |
| PRECHARGE_HANDOFF | consumer_handoff_reservation_only | precharge_control_region | PRECHARGE | True | False | rail continuity proof missing, no legal routing proof, no physical placement proof |
| SENSEAMP_HANDOFF | consumer_handoff_reservation_only | sense_write_enable_region | SENSEAMP | True | False | no legal routing proof, no physical placement proof |
| WRITEDRIVER_HANDOFF | consumer_handoff_reservation_only | sense_write_enable_region | WRITEDRIVER | True | False | no legal routing proof, no physical placement proof |
| WORDLINEDRIVER_HANDOFF | consumer_handoff_reservation_only | wordline_enable_control_region | WORDLINEDRIVER | True | False | no legal routing proof, no physical placement proof |
| DECODER_INTERFACE | decoder_boundary_reservation_only | consumer_handoff_region | DECODER_CASCADE | True | False | decoder placement intentionally untouched, no legal routing proof, no standalone integration |

## Gate Snapshot

```json
{
  "time_control_metadata_closure_available": true,
  "time_control_metadata_chain_complete": true,
  "control_region_crossing_coverage_complete": true,
  "precharge_closure_status": "intentional_no_local_gnd_metadata_exception",
  "can_create_experimental_opt_in_placement_plan": true,
  "can_modify_standalone_now": false,
  "can_generate_time_control_gds_now": false,
  "can_enter_physical_placement_now": false
}
```

## Consistency Checks

| check | value |
| --- | --- |
| experimental_contract_available | True |
| default_enabled | False |
| legacy_path_unchanged | True |
| standalone_py_modified | False |
| routing_modified | False |
| gds_writer_modified | False |
| physical_gds_generated | False |
| time_as_single_macro_forbidden | True |
| consumer_handoff_subplans_present | True |
| abstract_row_subplans_present | True |
| can_modify_standalone_now | False |
| can_generate_time_control_gds_now | False |
| can_enter_physical_placement_now | False |

## Allowed Capabilities

- default-off config surfacing
- abstract row/region metadata packing
- consumer handoff reservation modeling
- future gate bookkeeping

## Blocked Capabilities

- standalone integration
- physical TIME/control placement
- TIME/control GDS generation
- legal routing proof
- rail continuity proof
- shared rail enablement

## Notes

- This contract refines the Stage D prototype plan into a reusable data model.
- It remains metadata-only and cannot be treated as placement or routing proof.
- prototype_plan_scope=stage_d_openyield_time_control_opt_in_prototype_plan

