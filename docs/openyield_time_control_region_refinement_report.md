# OpenYield TIME Control Region Refinement Report

This report refines metadata-only control-row regions and PRECHARGE power closure. It does not prove rail continuity, legal routing, legal placement, timing closure, DRC, or LVS.

## Audit Summary

```json
{
  "time_control_region_refinement_available": true,
  "precharge_closure_status": "partial_missing_gnd",
  "all_region_budgets_pass": true,
  "all_adjacency_budgets_pass": true,
  "can_enter_time_control_region_metadata_planning": true,
  "can_enter_time_control_physical_placement": false,
  "can_enter_standalone_control_placement": false
}
```

## PRECHARGE Power Metadata Closure

```json
{
  "precharge_power_metadata_audit_available": true,
  "precharge_macro_candidate": "gen_precharge",
  "precharge_consumer_signal": "PRE / precharge_enb",
  "precharge_consumer_pin": "ENB",
  "precharge_pin_aliases": [
    "EN",
    "ENB",
    "precharge_enb",
    "PRE"
  ],
  "precharge_active_level": "active_low",
  "precharge_vdd_pin_known": true,
  "precharge_gnd_pin_known": false,
  "precharge_vdd_side": "top",
  "precharge_gnd_side": "missing",
  "precharge_power_domain_known": "partial",
  "precharge_power_metadata_complete": false,
  "precharge_rail_continuity_proven": false,
  "precharge_shared_rail_safe": false,
  "precharge_safe_for_metadata_planning": "partial",
  "precharge_safe_for_physical_placement": false,
  "precharge_closure_status": "partial_missing_gnd",
  "notes": [
    "This is power metadata closure only; it is not rail continuity proof.",
    "Shared rail remains disabled even if VDD metadata is present.",
    "Current closure still does not allow physical placement or legal routing claims."
  ]
}
```

## Control-Row Region Refinement

| region | inputs | outputs | preferred neighbors | signal count | track count | required width | reserved width | margin | risk |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| delay_chain_region | rbl, rbl_delay_bar | rbl_delay, rbl_delay_bar_wen | generated_logic_region, sense_write_enable_region | 2 | 1 | 0.4 | 2.0 | 1.6 | pass_moderate_margin |
| pdrive_region | clk, PRE_UNBUF, gated_clk_bar | clk_buf, PRE, wl_en | generated_logic_region, precharge_control_region, wordline_enable_control_region | 3 | 1 | 0.4 | 2.0 | 1.6 | pass_moderate_margin |
| generated_logic_region | cs, clk_buf, clk_bar, we, we_bar, wl_en, rbl_delay | gated_clk_buf, gated_clk_bar, w_en, s_en, PRE_UNBUF, wl_en_bar | delay_chain_region, pdrive_region, consumer_handoff_region | 6 | 1 | 0.4 | 2.0 | 1.6 | pass_moderate_margin |
| consumer_handoff_region | w_en, s_en, PRE, wl_en | WRITEDRIVER.EN, SENSEAMP.EN, PRECHARGE.ENB, WORDLINEDRIVER.B | generated_logic_region, precharge_control_region, wordline_enable_control_region, sense_write_enable_region | 4 | 1 | 0.4 | 2.0 | 1.6 | pass_moderate_margin |
| precharge_control_region | gated_clk_buf, rbl_delay, wl_en_bar | PRE_UNBUF, PRE | pdrive_region, consumer_handoff_region, wordline_enable_control_region | 2 | 1 | 0.4 | 2.0 | 1.6 | pass_moderate_margin |
| wordline_enable_control_region | gated_clk_bar | wl_en, wl_en_bar | pdrive_region, consumer_handoff_region, precharge_control_region | 2 | 4 | 1.0 | 2.0 | 1.0 | pass_moderate_margin |
| sense_write_enable_region | rbl_delay_bar, rbl_delay, gated_clk_bar, we, we_bar | w_en, s_en | delay_chain_region, generated_logic_region, consumer_handoff_region | 2 | 2 | 0.6 | 2.0 | 1.4 | pass_moderate_margin |

## Region Adjacency / Handoff Planning

| adjacency | source | target | signals | tracks | required width | reserved width | margin | risk |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| DELAY_CHAIN_TO_GENERATED_LOGIC | delay_chain_region | generated_logic_region | rbl_delay, rbl_delay_bar_wen | 2 | 0.6 | 2.0 | 1.4 | pass_moderate_margin |
| PDRIVE_TO_GENERATED_LOGIC | pdrive_region | generated_logic_region | clk_buf, PRE, wl_en | 3 | 0.8 | 2.0 | 1.2 | pass_moderate_margin |
| GENERATED_LOGIC_TO_CONSUMER_HANDOFF | generated_logic_region | consumer_handoff_region | w_en, s_en, PRE, wl_en | 4 | 1.0 | 2.0 | 1.0 | pass_moderate_margin |
| PRECHARGE_CONTROL_TO_CONSUMER_HANDOFF | precharge_control_region | consumer_handoff_region | precharge_enb | 1 | 0.4 | 2.0 | 1.6 | pass_moderate_margin |
| WORDLINE_ENABLE_TO_CONSUMER_HANDOFF | wordline_enable_control_region | consumer_handoff_region | wordline_enable | 1 | 0.4 | 2.0 | 1.6 | pass_moderate_margin |
| SENSE_WRITE_ENABLE_TO_CONSUMER_HANDOFF | sense_write_enable_region | consumer_handoff_region | write_enable, sense_enable | 2 | 0.6 | 2.0 | 1.4 | pass_moderate_margin |
| WORDLINE_ENABLE_TO_PRECHARGE_CONTROL | wordline_enable_control_region | precharge_control_region | wl_en_bar | 1 | 0.4 | 2.0 | 1.6 | pass_moderate_margin |

## Grouped Planning Interface Refinement

| interface | source regions | target macro | control signals | precharge power dependency | metadata ready | physical ready |
| --- | --- | --- | --- | --- | --- | --- |
| TIME_CONTROL_TO_WRITEDRIVER_INTERFACE | sense_write_enable_region | WRITEDRIVER | write_enable | - | True | False |
| TIME_CONTROL_TO_SENSEAMP_INTERFACE | sense_write_enable_region | SENSEAMP | sense_enable | - | True | False |
| TIME_CONTROL_TO_PRECHARGE_INTERFACE | precharge_control_region, wordline_enable_control_region | PRECHARGE | precharge_enb, wl_en_bar | partial_missing_gnd | partial | False |
| TIME_CONTROL_TO_WORDLINEDRIVER_INTERFACE | wordline_enable_control_region | WORDLINEDRIVER | wordline_enable | - | True | False |

## Consistency Checks

| check | value |
| --- | --- |
| time_control_region_refinement_available | True |
| precharge_power_metadata_audit_available | True |
| precharge_power_metadata_complete | False |
| precharge_closure_status | partial_missing_gnd |
| control_row_region_refinement_available | True |
| region_adjacency_metadata_available | True |
| grouped_planning_interface_refinement_available | True |
| all_region_budgets_pass | True |
| all_adjacency_budgets_pass | True |
| precharge_interface_metadata_ready | partial |
| safe_for_metadata_planning | True |
| safe_for_physical_placement | False |
| can_enter_time_control_region_metadata_planning | True |
| can_enter_time_control_physical_placement | False |
| can_enter_standalone_control_placement | False |

## Unresolved Items

- PRECHARGE power metadata may remain partial if GND is still missing
- rail continuity proof is missing
- region budgets are metadata-only
- region adjacency is not legal routing
- abstract region refinement is not legal placement
- control routing proof is missing
- delay timing proof is missing
- wen-delay timing proof is missing
- shared rail is disabled
- no DRC/LVS proof exists
- standalone integration is not allowed yet

## Step 6.30 Recommendation

```json
{
  "recommended_next_phase": "time_control_precharge_gnd_evidence_or_region_crossing_fanout_refinement",
  "candidate_directions": [
    "precharge_gnd_evidence_search",
    "control_region_crossing_signal_proof",
    "time_control_delay_timing_metadata_refinement",
    "control_row_macro_handoff_side_refinement"
  ],
  "reason": [
    "PRECHARGE power metadata remains the least-closed part of the bundle because GND is still not proven in current metadata.",
    "Region-level planning is now structured enough for metadata planning, but it still does not prove legal routing or legal placement.",
    "The next safe step is deeper evidence gathering, not standalone integration."
  ]
}
```

## Entry Decisions

- can_enter_time_control_region_metadata_planning: `True`
- can_enter_time_control_physical_placement: `False`
- can_enter_standalone_control_placement: `False`

