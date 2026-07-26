# OpenYield TIME Control Payload Materialization Boundary Audit

This is a metadata-only audit for future default-off prototype builders.

## Audit Summary

```json
{
  "payload_materialization_boundary_audit_available": true,
  "group_rank_deterministic": true,
  "region_anchor_rules_explicit": true,
  "handoff_anchor_rules_explicit": true,
  "partial_precharge_propagation_explicit": true,
  "future_default_off_builder_can_materialize_metadata_plan": true,
  "can_modify_standalone_now": false,
  "can_generate_time_control_gds_now": false,
  "can_enter_physical_placement_now": false
}
```

## Group Materialization

| group | group rank | member count | payload order sequence | materializable | rank consistent |
| --- | --- | --- | --- | --- | --- |
| front_end_registers | 0 | 2 | ['ADDR_DFF_ROW', 'DATA_DFF_ROW'] | True | True |
| timing_generation | 1 | 3 | ['DELAY_CHAIN_CLUSTER', 'WEN_DELAY_CHAIN_CLUSTER', 'PDRIVE_CLUSTER'] | True | True |
| generated_logic_core | 2 | 1 | ['GENERATED_LOGIC_CLUSTER'] | True | True |
| consumer_handoff_boundary | 3 | 4 | ['PRECHARGE_HANDOFF', 'SENSEAMP_HANDOFF', 'WRITEDRIVER_HANDOFF', 'WORDLINEDRIVER_HANDOFF'] | True | True |
| decoder_boundary | 4 | 1 | ['DECODER_INTERFACE'] | True | True |

## Region Anchor Rules

| region | preferred neighbors | required width | reserved width | anchor explicit |
| --- | --- | --- | --- | --- |
| delay_chain_region | ['generated_logic_region', 'sense_write_enable_region'] | 0.4 | 2.0 | True |
| pdrive_region | ['generated_logic_region', 'precharge_control_region', 'wordline_enable_control_region'] | 0.4 | 2.0 | True |
| generated_logic_region | ['delay_chain_region', 'pdrive_region', 'consumer_handoff_region'] | 0.4 | 2.0 | True |
| consumer_handoff_region | ['generated_logic_region', 'precharge_control_region', 'wordline_enable_control_region', 'sense_write_enable_region'] | 0.4 | 2.0 | True |
| precharge_control_region | ['pdrive_region', 'consumer_handoff_region', 'wordline_enable_control_region'] | 0.4 | 2.0 | True |
| wordline_enable_control_region | ['pdrive_region', 'consumer_handoff_region', 'precharge_control_region'] | 1.0 | 2.0 | True |
| sense_write_enable_region | ['delay_chain_region', 'generated_logic_region', 'consumer_handoff_region'] | 0.6 | 2.0 | True |

## Handoff Anchor Rules

| handoff | target macro | source regions | matching subblocks | metadata ready | anchor explicit |
| --- | --- | --- | --- | --- | --- |
| TIME_CONTROL_TO_WRITEDRIVER_INTERFACE | WRITEDRIVER | ['sense_write_enable_region'] | ['WRITEDRIVER_HANDOFF'] | True | True |
| TIME_CONTROL_TO_SENSEAMP_INTERFACE | SENSEAMP | ['sense_write_enable_region'] | ['SENSEAMP_HANDOFF'] | True | True |
| TIME_CONTROL_TO_PRECHARGE_INTERFACE | PRECHARGE | ['precharge_control_region', 'wordline_enable_control_region'] | ['PRECHARGE_HANDOFF'] | partial | True |
| TIME_CONTROL_TO_WORDLINEDRIVER_INTERFACE | WORDLINEDRIVER | ['wordline_enable_control_region'] | ['WORDLINEDRIVER_HANDOFF'] | True | True |

## Blocker Propagation

| subblock | payload blocked_by | experimental blocked_by | propagation explicit |
| --- | --- | --- | --- |
| ADDR_DFF_ROW | ['no legal placement proof', 'no routing proof', 'no standalone integration'] | ['no legal placement proof', 'no routing proof', 'no standalone integration'] | True |
| DATA_DFF_ROW | ['no legal placement proof', 'no routing proof', 'no standalone integration'] | ['no legal placement proof', 'no routing proof', 'no standalone integration'] | True |
| DELAY_CHAIN_CLUSTER | ['delay timing proof missing', 'no legal placement proof', 'no routing proof'] | ['delay timing proof missing', 'no legal placement proof', 'no routing proof'] | True |
| WEN_DELAY_CHAIN_CLUSTER | ['wen-delay timing proof missing', 'no legal placement proof', 'no routing proof'] | ['wen-delay timing proof missing', 'no legal placement proof', 'no routing proof'] | True |
| PDRIVE_CLUSTER | ['no legal placement proof', 'no routing proof'] | ['no legal placement proof', 'no routing proof'] | True |
| GENERATED_LOGIC_CLUSTER | ['stdcell physical library not proven', 'no legal routing proof', 'no DRC/LVS proof'] | ['stdcell physical library not proven', 'no legal routing proof', 'no DRC/LVS proof'] | True |
| PRECHARGE_HANDOFF | ['rail continuity proof missing', 'no legal routing proof', 'no physical placement proof'] | ['rail continuity proof missing', 'no legal routing proof', 'no physical placement proof'] | True |
| SENSEAMP_HANDOFF | ['no legal routing proof', 'no physical placement proof'] | ['no legal routing proof', 'no physical placement proof'] | True |
| WRITEDRIVER_HANDOFF | ['no legal routing proof', 'no physical placement proof'] | ['no legal routing proof', 'no physical placement proof'] | True |
| WORDLINEDRIVER_HANDOFF | ['no legal routing proof', 'no physical placement proof'] | ['no legal routing proof', 'no physical placement proof'] | True |
| DECODER_INTERFACE | ['decoder placement intentionally untouched', 'no legal routing proof', 'no standalone integration'] | ['decoder placement intentionally untouched', 'no legal routing proof', 'no standalone integration'] | True |

## Violations

```json
{
  "group_materialization_violations": [],
  "region_anchor_violations": [],
  "handoff_anchor_violations": [],
  "blocker_propagation_violations": []
}
```

## Consistency Checks

| check | value |
| --- | --- |
| payload_materialization_boundary_audit_available | True |
| group_rank_deterministic | True |
| intra_group_order_materialized | True |
| region_anchor_rules_explicit | True |
| handoff_anchor_rules_explicit | True |
| partial_precharge_propagation_explicit | True |
| blocker_propagation_explicit | True |
| builder_guardrails_explicit | True |
| future_default_off_builder_can_materialize_metadata_plan | True |
| can_modify_standalone_now | False |
| can_generate_time_control_gds_now | False |
| can_enter_physical_placement_now | False |

## Notes

- This audit asks whether a future default-off prototype builder can turn the current payload into a deterministic abstract materialization plan without inventing hidden tie-breakers or anchor rules.
- Passing this audit still does not prove legal placement, legal routing, timing closure, DRC, or LVS.
- Payload-order materialization is an abstract builder rule only and must not be misread as physical legalization.

