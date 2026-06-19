# OpenYield TIME Control Fast Metadata Bundle Report

This bundle is metadata-only. It combines precharge consumer closure, wordline secondary consumer closure, control fanout budget estimation, and an abstract control-row envelope without claiming legal physical placement.

## Audit Summary

```json
{
  "time_control_fast_bundle_available": true,
  "precharge_metadata_closure_status": "partial",
  "wordline_secondary_consumer_metadata_available": true,
  "fanout_budget_metadata_pass": true,
  "control_abstract_envelope_available": true,
  "can_enter_time_control_abstract_envelope_planning": true,
  "can_enter_time_control_physical_placement": false,
  "can_enter_standalone_control_placement": false
}
```

## PRECHARGE Consumer Pin Metadata Closure

```json
{
  "control_signal": "PRE / precharge_enb",
  "consumer_macro": "PRECHARGE",
  "consumer_pin": "ENB",
  "expected_active_level": "active_low",
  "current_status": "source_level_metadata_only",
  "precharge_consumer_pin_known": true,
  "precharge_consumer_pin_side_known": true,
  "precharge_power_domain_known": "partial",
  "precharge_adapter_available": false,
  "precharge_metadata_closure_available": "partial",
  "precharge_safe_for_metadata_planning": "partial",
  "precharge_safe_for_physical_placement": false,
  "precharge_consumer_status": "source_level_plus_pin_metadata",
  "notes": [
    "PRECHARGE still has no dedicated adapter module in the current clean worktree.",
    "GDS pin audit provides EN/precharge_enb pin metadata, but power-domain closure remains partial because GND metadata is not fully closed.",
    "This closure is enough for metadata planning only."
  ]
}
```

## Wordline Secondary Consumer Closure

```json
{
  "control_signal": "wordline_enable / wl_en",
  "wordline_primary_consumer_closed": true,
  "primary_consumer": "WORDLINEDRIVER.B",
  "wordline_secondary_consumers_available": true,
  "secondary_consumers": [
    "Pinv.A(wl_en_bar)",
    "RWL_AND2.B"
  ],
  "wl_en_bar_secondary_targets": [
    "PRECHARGE.PNAND3.C"
  ],
  "wl_en_bar_path_preserved": true,
  "rwl_and2_consumer_preserved": true,
  "wordline_fanout_metadata_complete": true,
  "wordline_fanout_physical_routing_proven": false,
  "source_evidence": [
    "gated_clk_bar -> WL_PDRIVE -> wl_en; wl_en -> Pinv -> wl_en_bar",
    "Consumer contract keeps WORDLINEDRIVER.B as primary while preserving wl_en_bar and RWL-side secondary paths."
  ]
}
```

## Control Fanout Budget

| signal | fanout | targets | tracks | pitch | margin | required width | channel width | pass | budget margin | risk |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| write_enable | 1 | WRITEDRIVER.EN | 1 | 0.2 | 0.2 | 0.4 | 2.0 | True | 1.6 | pass_moderate_margin |
| sense_enable | 1 | SENSEAMP.EN | 1 | 0.2 | 0.2 | 0.4 | 2.0 | True | 1.6 | pass_moderate_margin |
| precharge_enb | 1 | PRECHARGE.ENB | 1 | 0.2 | 0.2 | 0.4 | 2.0 | True | 1.6 | pass_moderate_margin |
| wordline_enable | 3 | WORDLINEDRIVER.B, Pinv.A(wl_en_bar), RWL_AND2.B | 3 | 0.2 | 0.2 | 0.8 | 2.0 | True | 1.2 | pass_moderate_margin |
| wl_en_bar | 1 | PRECHARGE.PNAND3.C | 1 | 0.2 | 0.2 | 0.4 | 2.0 | True | 1.6 | pass_moderate_margin |

## Control-Row Abstract Placement Envelope

| region | source contracts | inputs | outputs | consumer targets | bbox proxy policy | metadata_only | legal placement |
| --- | --- | --- | --- | --- | --- | --- | --- |
| delay_chain_region | RBL_DELAY_BINDING_CONTRACT, WEN_DELAY_CONDITIONAL_BINDING_CONTRACT, DELAY_CHAIN_GENERATED_LOGIC_CONTRACT, WEN_DELAY_CHAIN_CONDITIONAL_GENERATED_LOGIC_CONTRACT | rbl, rbl_delay_bar | rbl_delay, rbl_delay_bar_wen | WRITE_ENABLE_CONSUMER_CONTRACT, SENSE_ENABLE_CONSUMER_CONTRACT | track_count_and_stage_count_proxy_only | True | False |
| pdrive_region | CLK_BUF_BINDING_CONTRACT, PDRIVE_CHAIN_GENERATED_LOGIC_CONTRACT, PDRIVE2_FOR_PRE_CHAIN_GENERATED_LOGIC_CONTRACT, WL_PDRIVE_CHAIN_GENERATED_LOGIC_CONTRACT | clk, PRE_UNBUF, gated_clk_bar | clk_buf, PRE, wl_en | WRITE_ENABLE_CONSUMER_CONTRACT, SENSE_ENABLE_CONSUMER_CONTRACT, PRECHARGE_ENB_CONSUMER_CONTRACT, WORDLINE_ENABLE_CONSUMER_CONTRACT | buffer_chain_stage_proxy_only | True | False |
| generated_logic_region | AND2_GENERATED_LOGIC_CONTRACT, AND3_COMPOSITE_GENERATED_LOGIC_CONTRACT, PNAND3_COMPOSITE_GENERATED_LOGIC_CONTRACT, PINV_GENERATED_LOGIC_CONTRACT | cs, clk_buf, clk_bar, we, we_bar, wl_en, rbl_delay | gated_clk_buf, gated_clk_bar, w_en, s_en, PRE_UNBUF, wl_en_bar | WRITE_ENABLE_CONSUMER_CONTRACT, SENSE_ENABLE_CONSUMER_CONTRACT, PRECHARGE_ENB_CONSUMER_CONTRACT, WORDLINE_ENABLE_CONSUMER_CONTRACT | composite_gate_count_proxy_only | True | False |
| consumer_handoff_region | WRITE_ENABLE_CONSUMER_CONTRACT, SENSE_ENABLE_CONSUMER_CONTRACT, PRECHARGE_ENB_CONSUMER_CONTRACT, WORDLINE_ENABLE_CONSUMER_CONTRACT | w_en, s_en, PRE, wl_en | WRITEDRIVER.EN, SENSEAMP.EN, PRECHARGE.ENB, WORDLINEDRIVER.B | peripheral hard macro pin access | macro_pin_side_and_fanout_proxy_only | True | False |
| precharge_control_region | PRECHARGE_ENB_BINDING_CONTRACT, PRECHARGE_ENB_CONSUMER_CONTRACT | gated_clk_buf, rbl_delay, wl_en_bar | PRE_UNBUF, PRE | PRECHARGE.ENB, PRECHARGE.PNAND3.C | source_level_plus_pin_metadata_only | True | False |
| wordline_enable_control_region | WORDLINE_ENABLE_BINDING_CONTRACT, WORDLINE_ENABLE_CONSUMER_CONTRACT | gated_clk_bar | wl_en, wl_en_bar | WORDLINEDRIVER.B, Pinv.A(wl_en_bar), RWL_AND2.B | primary_plus_secondary_fanout_proxy_only | True | False |
| sense_write_enable_region | WRITE_ENABLE_BINDING_CONTRACT, SENSE_ENABLE_BINDING_CONTRACT, WRITE_ENABLE_CONSUMER_CONTRACT, SENSE_ENABLE_CONSUMER_CONTRACT | rbl_delay_bar, rbl_delay, gated_clk_bar, we, we_bar | w_en, s_en | WRITEDRIVER.EN, SENSEAMP.EN | paired_enable_channel_proxy_only | True | False |

## Consistency Checks

| check | value |
| --- | --- |
| time_control_fast_bundle_available | True |
| precharge_consumer_metadata_closure_available | partial |
| wordline_secondary_consumer_metadata_available | True |
| control_fanout_budget_available | True |
| control_abstract_envelope_available | True |
| all_primary_control_consumers_have_contract | True |
| consumer_contracts_complete_for_metadata_planning | True |
| generated_logic_contract_coverage_complete | True |
| control_signal_binding_consistent | True |
| control_signal_polarity_consistent | True |
| fanout_budget_metadata_pass | True |
| safe_for_metadata_planning | True |
| safe_for_physical_placement | False |
| can_enter_time_control_abstract_envelope_planning | True |
| can_enter_time_control_physical_placement | False |
| can_enter_standalone_control_placement | False |

## Unresolved Items

- PRECHARGE adapter may still be partial/source-level
- fanout budget is metadata-only
- abstract envelope is not legal placement
- control routing proof is missing
- delay timing proof is missing
- wen-delay timing proof is missing
- rail continuity proof is missing
- shared rail is disabled
- no DRC/LVS proof exists
- standalone integration is not allowed yet

## Step 6.28 Recommendation

```json
{
  "recommended_next_phase": "time_control_precharge_adapter_audit_or_control_row_constraints",
  "candidate_directions": [
    "precharge_adapter_metadata_closure",
    "control_row_handoff_constraints",
    "control_channel_reservation_rules",
    "time_control_grouped_planning_interfaces"
  ],
  "reason": [
    "The fast bundle now closes the main metadata handoff story for TIME control signals.",
    "PRECHARGE remains the least-closed consumer and is still not physical-ready.",
    "The next step should refine abstract planning interfaces, not physical placement."
  ]
}
```

## Entry Decisions

- can_enter_time_control_abstract_envelope_planning: `True`
- can_enter_time_control_physical_placement: `False`
- can_enter_standalone_control_placement: `False`

