# OpenYield TIME Control Abstract Floorplan Payload Report

This report packages the TIME/control abstract floorplan payload for future default-off prototype work. It remains metadata-only and does not authorize standalone integration, routing, or GDS generation.

## Audit Summary

```json
{
  "abstract_floorplan_payload_available": true,
  "default_enabled": false,
  "region_count": 7,
  "subblock_count": 11,
  "handoff_count": 4,
  "can_modify_standalone_now": false,
  "can_generate_time_control_gds_now": false,
  "can_enter_physical_placement_now": false
}
```

## Regions

| region | preferred neighbors | required width | reserved width | margin | risk | metadata only |
| --- | --- | --- | --- | --- | --- | --- |
| delay_chain_region | generated_logic_region, sense_write_enable_region | 0.4 | 2.0 | 1.6 | pass_moderate_margin | True |
| pdrive_region | generated_logic_region, precharge_control_region, wordline_enable_control_region | 0.4 | 2.0 | 1.6 | pass_moderate_margin | True |
| generated_logic_region | delay_chain_region, pdrive_region, consumer_handoff_region | 0.4 | 2.0 | 1.6 | pass_moderate_margin | True |
| consumer_handoff_region | generated_logic_region, precharge_control_region, wordline_enable_control_region, sense_write_enable_region | 0.4 | 2.0 | 1.6 | pass_moderate_margin | True |
| precharge_control_region | pdrive_region, consumer_handoff_region, wordline_enable_control_region | 0.4 | 2.0 | 1.6 | pass_moderate_margin | True |
| wordline_enable_control_region | pdrive_region, consumer_handoff_region, precharge_control_region | 1.0 | 2.0 | 1.0 | pass_moderate_margin | True |
| sense_write_enable_region | delay_chain_region, generated_logic_region, consumer_handoff_region | 0.6 | 2.0 | 1.4 | pass_moderate_margin | True |

## Subblocks

| subblock | plan kind | assigned region | order group | metadata ready | physical ready | consumer |
| --- | --- | --- | --- | --- | --- | --- |
| ADDR_DFF_ROW | abstract_dff_row | generated_logic_region | front_end_registers | True | False | - |
| DATA_DFF_ROW | abstract_dff_row | generated_logic_region | front_end_registers | True | False | - |
| DELAY_CHAIN_CLUSTER | timing_chain_cluster | delay_chain_region | timing_generation | True | False | - |
| WEN_DELAY_CHAIN_CLUSTER | timing_chain_cluster | sense_write_enable_region | timing_generation | True | False | - |
| PDRIVE_CLUSTER | buffer_chain_cluster | pdrive_region | timing_generation | True | False | - |
| GENERATED_LOGIC_CLUSTER | stdcell_row_abstract_cluster | generated_logic_region | generated_logic_core | True | False | - |
| PRECHARGE_HANDOFF | consumer_handoff_reservation_only | precharge_control_region | consumer_handoff_boundary | True | False | PRECHARGE |
| SENSEAMP_HANDOFF | consumer_handoff_reservation_only | sense_write_enable_region | consumer_handoff_boundary | True | False | SENSEAMP |
| WRITEDRIVER_HANDOFF | consumer_handoff_reservation_only | sense_write_enable_region | consumer_handoff_boundary | True | False | WRITEDRIVER |
| WORDLINEDRIVER_HANDOFF | consumer_handoff_reservation_only | wordline_enable_control_region | consumer_handoff_boundary | True | False | WORDLINEDRIVER |
| DECODER_INTERFACE | decoder_boundary_reservation_only | consumer_handoff_region | decoder_boundary | True | False | DECODER_CASCADE |

## Handoffs

| interface | source regions | target macro | signals | metadata ready | physical ready |
| --- | --- | --- | --- | --- | --- |
| TIME_CONTROL_TO_WRITEDRIVER_INTERFACE | sense_write_enable_region | WRITEDRIVER | write_enable | True | False |
| TIME_CONTROL_TO_SENSEAMP_INTERFACE | sense_write_enable_region | SENSEAMP | sense_enable | True | False |
| TIME_CONTROL_TO_PRECHARGE_INTERFACE | precharge_control_region, wordline_enable_control_region | PRECHARGE | precharge_enb, wl_en_bar | partial | False |
| TIME_CONTROL_TO_WORDLINEDRIVER_INTERFACE | wordline_enable_control_region | WORDLINEDRIVER | wordline_enable | True | False |

## Gate Snapshot

```json
{
  "can_create_experimental_opt_in_placement_plan": true,
  "can_modify_standalone_now": false,
  "can_generate_time_control_gds_now": false,
  "can_enter_physical_placement_now": false,
  "precharge_closure_status": "intentional_no_local_gnd_metadata_exception"
}
```

## Consistency Checks

| check | value |
| --- | --- |
| abstract_floorplan_payload_available | True |
| default_enabled | False |
| legacy_path_unchanged | True |
| region_count | 7 |
| subblock_count | 11 |
| handoff_count | 4 |
| all_regions_metadata_only | True |
| all_subblocks_require_opt_in | True |
| any_physical_ready_subblocks | False |
| standalone_py_modified | False |
| routing_modified | False |
| gds_writer_modified | False |
| physical_gds_generated | False |
| can_modify_standalone_now | False |
| can_generate_time_control_gds_now | False |
| can_enter_physical_placement_now | False |

## Notes

- This payload is metadata-only and intended for future default-off prototype planning.
- It does not prove legal placement, legal routing, rail continuity, or timing closure.
- Do not connect this payload to standalone until a later readiness gate explicitly allows it.

