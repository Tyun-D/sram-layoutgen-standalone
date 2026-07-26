# OpenYield TIME Control Packing Invariant Audit

This is a metadata-only invariant audit over the Stage 6.32 payload. It does not prove legal placement, legal routing, timing closure, DRC, or LVS.

## Audit Summary

```json
{
  "packing_invariant_audit_available": true,
  "required_groups_present": true,
  "consumer_handoff_regions_aligned": true,
  "required_adjacency_invariants_hold": true,
  "all_region_channel_margins_non_negative": true,
  "invariants_clean": true,
  "can_modify_standalone_now": false,
  "can_generate_time_control_gds_now": false,
  "can_enter_physical_placement_now": false
}
```

## Packing Groups

| group | present |
| --- | --- |
| front_end_registers | True |
| timing_generation | True |
| generated_logic_core | True |
| consumer_handoff_boundary | True |
| decoder_boundary | True |

## Region Assignment Checks

| subblock | assigned region | region exists |
| --- | --- | --- |
| ADDR_DFF_ROW | generated_logic_region | True |
| DATA_DFF_ROW | generated_logic_region | True |
| DELAY_CHAIN_CLUSTER | delay_chain_region | True |
| WEN_DELAY_CHAIN_CLUSTER | sense_write_enable_region | True |
| PDRIVE_CLUSTER | pdrive_region | True |
| GENERATED_LOGIC_CLUSTER | generated_logic_region | True |
| PRECHARGE_HANDOFF | precharge_control_region | True |
| SENSEAMP_HANDOFF | sense_write_enable_region | True |
| WRITEDRIVER_HANDOFF | sense_write_enable_region | True |
| WORDLINEDRIVER_HANDOFF | wordline_enable_control_region | True |
| DECODER_INTERFACE | consumer_handoff_region | True |

## Handoff Alignment

| subblock | interface | assigned region | source regions | aligned |
| --- | --- | --- | --- | --- |
| PRECHARGE_HANDOFF | TIME_CONTROL_TO_PRECHARGE_INTERFACE | precharge_control_region | precharge_control_region, wordline_enable_control_region | True |
| SENSEAMP_HANDOFF | TIME_CONTROL_TO_SENSEAMP_INTERFACE | sense_write_enable_region | sense_write_enable_region | True |
| WRITEDRIVER_HANDOFF | TIME_CONTROL_TO_WRITEDRIVER_INTERFACE | sense_write_enable_region | sense_write_enable_region | True |
| WORDLINEDRIVER_HANDOFF | TIME_CONTROL_TO_WORDLINEDRIVER_INTERFACE | wordline_enable_control_region | wordline_enable_control_region | True |

## Adjacency Invariants

| left | right | left region | right region | metadata path | adjacent or reachable |
| --- | --- | --- | --- | --- | --- |
| DELAY_CHAIN_CLUSTER | GENERATED_LOGIC_CLUSTER | delay_chain_region | generated_logic_region | delay_chain_region -> generated_logic_region | True |
| PDRIVE_CLUSTER | GENERATED_LOGIC_CLUSTER | pdrive_region | generated_logic_region | pdrive_region -> generated_logic_region | True |
| GENERATED_LOGIC_CLUSTER | DECODER_INTERFACE | generated_logic_region | consumer_handoff_region | generated_logic_region -> consumer_handoff_region | True |
| GENERATED_LOGIC_CLUSTER | PRECHARGE_HANDOFF | generated_logic_region | precharge_control_region | generated_logic_region -> consumer_handoff_region -> precharge_control_region | True |
| GENERATED_LOGIC_CLUSTER | WORDLINEDRIVER_HANDOFF | generated_logic_region | wordline_enable_control_region | generated_logic_region -> consumer_handoff_region -> wordline_enable_control_region | True |
| SENSEAMP_HANDOFF | WRITEDRIVER_HANDOFF | sense_write_enable_region | sense_write_enable_region | sense_write_enable_region | True |

## Channel Margins

| region | budget margin | risk | usable for metadata ordering |
| --- | --- | --- | --- |
| delay_chain_region | 1.6 | pass_moderate_margin | True |
| pdrive_region | 1.6 | pass_moderate_margin | True |
| generated_logic_region | 1.6 | pass_moderate_margin | True |
| consumer_handoff_region | 1.6 | pass_moderate_margin | True |
| precharge_control_region | 1.6 | pass_moderate_margin | True |
| wordline_enable_control_region | 1.0 | pass_moderate_margin | True |
| sense_write_enable_region | 1.4 | pass_moderate_margin | True |

## Violations

```json
{
  "group_order_violation_items": [],
  "missing_region_assignments": [],
  "misaligned_handoffs": [],
  "adjacency_violations": [],
  "negative_margin_regions": []
}
```

## Consistency Checks

| check | value |
| --- | --- |
| packing_invariant_audit_available | True |
| required_groups_present | True |
| all_subblocks_have_known_region_or_allowed_decoder_boundary | True |
| consumer_handoff_regions_aligned | True |
| required_adjacency_invariants_hold | True |
| all_region_channel_margins_non_negative | True |
| default_enabled_still_false | True |
| legacy_path_unchanged | True |
| standalone_still_blocked | True |
| gds_still_blocked | True |
| physical_placement_still_blocked | True |
| invariants_clean | True |

## Notes

- This audit checks internal consistency of the metadata payload only.
- Passing invariants does not prove legal placement, legal routing, timing closure, DRC, or LVS.
- The audit is intended to reduce future prototype ambiguity, not to reopen the physical gate.

