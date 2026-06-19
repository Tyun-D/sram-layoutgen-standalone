# OpenYield TIME PRECHARGE + Control-Row Constraints Bundle Report

This is a metadata-only bundle. It does not claim legal placement, legal routing, timing closure, DRC closure, LVS closure, or standalone integration readiness.

## Audit Summary

```json
{
  "time_control_precharge_constraints_bundle_available": true,
  "precharge_adapter_metadata_closure_status": "partial",
  "control_handoff_constraints_available": true,
  "control_channel_reservation_rules_available": true,
  "grouped_planning_interfaces_available": true,
  "all_control_channel_budgets_pass": true,
  "can_enter_time_control_constraint_planning": true,
  "can_enter_time_control_physical_placement": false,
  "can_enter_standalone_control_placement": false
}
```

## PRECHARGE Adapter Metadata Closure

```json
{
  "precharge_adapter_metadata_available": true,
  "precharge_adapter_metadata_closure_status": "partial",
  "precharge_consumer_signal": "PRE / precharge_enb",
  "precharge_consumer_pin": "ENB",
  "precharge_consumer_pin_aliases": [
    "EN",
    "ENB",
    "precharge_enb",
    "PRE"
  ],
  "precharge_active_level": "active_low",
  "precharge_pin_known": true,
  "precharge_pin_side_known": true,
  "precharge_power_domain_known": "partial",
  "precharge_vdd_pin_known": true,
  "precharge_gnd_pin_known": false,
  "precharge_power_metadata_complete": false,
  "precharge_pin_metadata_complete": true,
  "precharge_safe_for_metadata_planning": "partial",
  "precharge_safe_for_physical_placement": false,
  "gds_macro_candidate": "gen_precharge",
  "physical_alias_pin_name": "EN",
  "physical_alias_pin_side": "bottom",
  "power_rail_summary": {
    "has_vdd": true,
    "has_gnd": false,
    "vdd_side": "top",
    "gnd_side": "missing",
    "rail_continuity_status": "rail_needs_manual_review"
  },
  "notes": [
    "PRECHARGE still has no dedicated adapter module in the current clean worktree.",
    "The active-low consumer contract is normalized to ENB while the current hard-macro GDS exposes the physical alias pin EN.",
    "Power-domain closure remains partial because VDD metadata exists but GND pin metadata is still missing in the current GDS pin audit."
  ]
}
```

## Control-Row Handoff Constraints

| constraint | source signal | source region | target macro | target pin | target pin side | target region | fanout | tracks | required width | channel width | budget margin | pass |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| WRITE_ENABLE_TO_WRITEDRIVER_EN | write_enable | sense_write_enable_region | WRITEDRIVER | EN | bottom | consumer_handoff_region | 1 | 1 | 0.4 | 2.0 | 1.6 | True |
| SENSE_ENABLE_TO_SENSEAMP_EN | sense_enable | sense_write_enable_region | SENSEAMP | EN | top | consumer_handoff_region | 1 | 1 | 0.4 | 2.0 | 1.6 | True |
| PRECHARGE_ENB_TO_PRECHARGE_ENB | precharge_enb | precharge_control_region | PRECHARGE | ENB | bottom | consumer_handoff_region | 1 | 1 | 0.4 | 2.0 | 1.6 | True |
| WORDLINE_ENABLE_TO_WORDLINEDRIVER_B | wordline_enable | wordline_enable_control_region | WORDLINEDRIVER | B | left | consumer_handoff_region | 3 | 3 | 0.8 | 2.0 | 1.2 | True |
| WL_EN_BAR_TO_PRECHARGE_PNAND3_C | wl_en_bar | wordline_enable_control_region | PRECHARGE | PNAND3.C | internal_metadata_only | precharge_control_region | 1 | 1 | 0.4 | 2.0 | 1.6 | True |

## Control Channel Reservation Rules

| rule | signals | source region | target region | reserved width | required width | margin | risk | shares with | mode |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| CONTROL_ROW_WRITE_ENABLE_CHANNEL | write_enable | sense_write_enable_region | consumer_handoff_region | 2.0 | 0.4 | 1.6 | pass_moderate_margin | - | exclusive |
| CONTROL_ROW_SENSE_ENABLE_CHANNEL | sense_enable | sense_write_enable_region | consumer_handoff_region | 2.0 | 0.4 | 1.6 | pass_moderate_margin | - | exclusive |
| CONTROL_ROW_PRECHARGE_ENB_CHANNEL | precharge_enb | precharge_control_region | consumer_handoff_region | 2.0 | 0.4 | 1.6 | pass_moderate_margin | - | exclusive |
| CONTROL_ROW_WORDLINE_ENABLE_CHANNEL | wordline_enable | wordline_enable_control_region | consumer_handoff_region | 2.0 | 0.8 | 1.2 | pass_moderate_margin | - | exclusive |
| CONTROL_ROW_WL_EN_BAR_SECONDARY_CHANNEL | wl_en_bar | wordline_enable_control_region | precharge_control_region | 2.0 | 0.4 | 1.6 | pass_moderate_margin | - | exclusive |

## Grouped Planning Interfaces

| interface | source signals | target macro | target pins | polarity | metadata ready | physical ready | blocked by |
| --- | --- | --- | --- | --- | --- | --- | --- |
| TIME_CONTROL_TO_WRITEDRIVER_INTERFACE | write_enable | WRITEDRIVER | EN | active_high | True | False | handoff constraints are metadata-only, channel reservation rules are not legal routing, control routing proof is missing, delay timing proof is missing |
| TIME_CONTROL_TO_SENSEAMP_INTERFACE | sense_enable | SENSEAMP | EN | active_high | True | False | handoff constraints are metadata-only, channel reservation rules are not legal routing, control routing proof is missing, delay timing proof is missing |
| TIME_CONTROL_TO_PRECHARGE_INTERFACE | precharge_enb, wl_en_bar | PRECHARGE | ENB, PNAND3.C | precharge_enb active_low, wl_en_bar active_high_local_secondary | partial | False | PRECHARGE adapter metadata may remain partial, PRECHARGE power-domain closure may remain incomplete, handoff constraints are metadata-only, channel reservation rules are not legal routing, control routing proof is missing, rail continuity proof is missing |
| TIME_CONTROL_TO_WORDLINEDRIVER_INTERFACE | wordline_enable | WORDLINEDRIVER | B | active_high | True | False | handoff constraints are metadata-only, channel reservation rules are not legal routing, control routing proof is missing, delay timing proof is missing |

## Consistency Checks

| check | value |
| --- | --- |
| time_control_precharge_constraints_bundle_available | True |
| precharge_adapter_metadata_available | True |
| precharge_adapter_metadata_closure_status | partial |
| control_handoff_constraints_available | True |
| control_channel_reservation_rules_available | True |
| grouped_planning_interfaces_available | True |
| all_primary_control_interfaces_have_constraints | True |
| all_control_channel_budgets_pass | True |
| precharge_metadata_ready_for_planning | True |
| precharge_physical_ready | False |
| safe_for_metadata_planning | True |
| safe_for_physical_placement | False |
| can_enter_time_control_constraint_planning | True |
| can_enter_time_control_physical_placement | False |
| can_enter_standalone_control_placement | False |

## Unresolved Items

- PRECHARGE adapter metadata may remain partial
- PRECHARGE power-domain closure may remain incomplete
- handoff constraints are metadata-only
- channel reservation rules are not legal routing
- abstract envelope is not legal placement
- control routing proof is missing
- delay timing proof is missing
- wen-delay timing proof is missing
- rail continuity proof is missing
- shared rail is disabled
- no DRC/LVS proof exists
- standalone integration is not allowed yet

## Step 6.29 Recommendation

```json
{
  "recommended_next_phase": "time_control_control_row_planning_or_precharge_power_metadata_closure",
  "candidate_directions": [
    "precharge_power_metadata_closure",
    "control_row_region_refinement",
    "control_grouped_fanout_proof",
    "time_control_delay_timing_metadata_refinement"
  ],
  "reason": [
    "The control-row handoff story is now bundled at metadata level and all current channel budgets pass under the current assumptions.",
    "PRECHARGE remains partial because power-domain closure is still incomplete.",
    "The next useful step is to refine control-row planning evidence, not to claim legal routing or physical placement."
  ]
}
```

## Entry Decisions

- can_enter_time_control_constraint_planning: `True`
- can_enter_time_control_physical_placement: `False`
- can_enter_standalone_control_placement: `False`

