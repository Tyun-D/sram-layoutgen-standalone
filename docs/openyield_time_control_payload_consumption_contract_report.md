# OpenYield TIME Control Payload Consumption Contract Audit

This is a metadata-only determinism audit for future default-off prototype builders.

## Audit Summary

```json
{
  "payload_consumption_contract_available": true,
  "identifier_uniqueness_clean": true,
  "group_order_materializable": true,
  "partial_precharge_preserved": true,
  "future_default_off_builder_can_consume_metadata": true,
  "can_modify_standalone_now": false,
  "can_generate_time_control_gds_now": false,
  "can_enter_physical_placement_now": false
}
```

## Region Reference Audit

| region | bad preferred neighbors | neighbors all known |
| --- | --- | --- |
| delay_chain_region |  | True |
| pdrive_region |  | True |
| generated_logic_region |  | True |
| consumer_handoff_region |  | True |
| precharge_control_region |  | True |
| wordline_enable_control_region |  | True |
| sense_write_enable_region |  | True |

## Subblock Consumption Rows

| subblock | assigned region | region exists | group | group rank | consumer target | blocked_by explicit | experimental aligned | candidate aligned |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| ADDR_DFF_ROW | generated_logic_region | True | front_end_registers | 0 | - | True | True | True |
| DATA_DFF_ROW | generated_logic_region | True | front_end_registers | 0 | - | True | True | True |
| DELAY_CHAIN_CLUSTER | delay_chain_region | True | timing_generation | 1 | - | True | True | None |
| WEN_DELAY_CHAIN_CLUSTER | sense_write_enable_region | True | timing_generation | 1 | - | True | True | None |
| PDRIVE_CLUSTER | pdrive_region | True | timing_generation | 1 | - | True | True | None |
| GENERATED_LOGIC_CLUSTER | generated_logic_region | True | generated_logic_core | 2 | - | True | True | True |
| PRECHARGE_HANDOFF | precharge_control_region | True | consumer_handoff_boundary | 3 | PRECHARGE | True | True | True |
| SENSEAMP_HANDOFF | sense_write_enable_region | True | consumer_handoff_boundary | 3 | SENSEAMP | True | True | None |
| WRITEDRIVER_HANDOFF | sense_write_enable_region | True | consumer_handoff_boundary | 3 | WRITEDRIVER | True | True | None |
| WORDLINEDRIVER_HANDOFF | wordline_enable_control_region | True | consumer_handoff_boundary | 3 | WORDLINEDRIVER | True | True | True |
| DECODER_INTERFACE | consumer_handoff_region | True | decoder_boundary | 4 | DECODER_CASCADE | True | True | None |

## Handoff Consumption Rows

| handoff | target macro | binding contracts | unresolved signals | matching subblock | consumer contract | metadata ready | consumer explicit |
| --- | --- | --- | --- | --- | --- | --- | --- |
| TIME_CONTROL_TO_WRITEDRIVER_INTERFACE | WRITEDRIVER | WRITE_ENABLE_BINDING_CONTRACT |  | WRITEDRIVER_HANDOFF | WRITE_ENABLE_CONSUMER_CONTRACT | True | True |
| TIME_CONTROL_TO_SENSEAMP_INTERFACE | SENSEAMP | SENSE_ENABLE_BINDING_CONTRACT |  | SENSEAMP_HANDOFF | SENSE_ENABLE_CONSUMER_CONTRACT | True | True |
| TIME_CONTROL_TO_PRECHARGE_INTERFACE | PRECHARGE | PRECHARGE_ENB_BINDING_CONTRACT, WORDLINE_ENABLE_BINDING_CONTRACT:derived_secondary_signal, PRECHARGE_ENB_BINDING_CONTRACT:derived_secondary_signal |  | PRECHARGE_HANDOFF | PRECHARGE_ENB_CONSUMER_CONTRACT | partial | True |
| TIME_CONTROL_TO_WORDLINEDRIVER_INTERFACE | WORDLINEDRIVER | WORDLINE_ENABLE_BINDING_CONTRACT |  | WORDLINEDRIVER_HANDOFF | WORDLINE_ENABLE_CONSUMER_CONTRACT | True | True |

## Group Ordering

| group | rank values | deterministic rank | rank |
| --- | --- | --- | --- |
| consumer_handoff_boundary | [3] | True | 3 |
| decoder_boundary | [4] | True | 4 |
| front_end_registers | [0] | True | 0 |
| generated_logic_core | [2] | True | 2 |
| timing_generation | [1] | True | 1 |

## Violations

```json
{
  "region_reference_violations": [],
  "subblock_region_violations": [],
  "subblock_blocker_violations": [],
  "subblock_plan_alignment_violations": [],
  "handoff_region_violations": [],
  "handoff_signal_violations": [],
  "handoff_consumer_violations": [],
  "group_order_violations": []
}
```

## Consistency Checks

| check | value |
| --- | --- |
| payload_consumption_contract_available | True |
| consumption_contract_complete_for_metadata | True |
| identifier_uniqueness_clean | True |
| region_reference_clean | True |
| subblock_region_assignment_clean | True |
| subblock_blockers_explicit | True |
| subblock_plan_alignment_clean | True |
| handoff_region_reference_clean | True |
| handoff_signal_binding_clean | True |
| handoff_consumer_endpoint_explicit | True |
| group_order_materializable | True |
| partial_precharge_preserved | True |
| default_off_still_preserved | True |
| legacy_path_unchanged | True |
| standalone_still_unmodified | True |
| routing_still_unmodified | True |
| gds_writer_still_unmodified | True |
| physical_gds_still_not_generated | True |
| future_default_off_builder_can_consume_metadata | True |
| can_modify_standalone_now | False |
| can_generate_time_control_gds_now | False |
| can_enter_physical_placement_now | False |

## Notes

- This audit checks whether a future default-off prototype builder can consume the current payload deterministically without hidden identifier, region, or endpoint assumptions.
- Passing this audit still does not prove legal placement, legal routing, timing closure, DRC, or LVS.
- PRECHARGE may remain partial, but that partial status must stay explicit and must not be silently upgraded.

