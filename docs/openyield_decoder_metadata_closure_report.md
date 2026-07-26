# OpenYield Decoder Metadata Closure Report

This report closes the decoder metadata line for now. It summarizes what is closed, what remains blocked, and why decoder physical push should stop here.

## Closure Summary

```json
{
  "metadata_chain_complete": true,
  "decoder_metadata_closure_available": true,
  "decoder_metadata_can_be_used_for_future_planning": true,
  "decoder_physical_prototype_allowed": false,
  "decoder_physical_placement_allowed": false,
  "very_limited_control_row_smoke_allowed": false
}
```

## Source Reports

| step | scope | report |
| --- | --- | --- |
| 6.9 | step6_9_openyield_decoder_stage_candidate_audit | docs/openyield_decoder_stage_candidate_report.json |
| 6.10 | step6_10_openyield_decoder_row_rule_audit | docs/openyield_decoder_row_rule_report.json |
| 6.11 | step6_11_openyield_decoder_logic_repair_audit | docs/openyield_decoder_logic_repair_report.json |
| 6.12 | step6_12_openyield_decoder_composite_leaf_convention_audit | docs/openyield_decoder_composite_leaf_convention_report.json |
| 6.13 | step6_13_openyield_decoder_stage_template_audit | docs/openyield_decoder_stage_template_report.json |
| 6.14 | step6_14_openyield_decoder_truth_table_binding_audit | docs/openyield_decoder_truth_table_binding_report.json |
| 6.15 | step6_15_openyield_decoder_output_contract_audit | docs/openyield_decoder_output_contract_report.json |
| 6.16 | step6_16_openyield_decoder_output_handoff_budget_audit | docs/openyield_decoder_output_handoff_budget_report.json |
| 6.17 | step6_17_openyield_decoder_generated_block_plan_summary | docs/openyield_decoder_generated_block_plan_report.json |
| 6.18 | step6_18_openyield_decoder_preplacement_feasibility_audit | docs/openyield_decoder_preplacement_feasibility_report.json |
| 6.19 | step6_19_openyield_decoder_handoff_relief_audit | docs/openyield_decoder_handoff_relief_report.json |
| 6.20 | step6_20_openyield_decoder_channel_requirement_audit | docs/openyield_decoder_channel_requirement_report.json |
| 6.21 | step6_21_openyield_control_parent_reservation_audit | docs/openyield_control_parent_reservation_report.json |

## Closed Metadata Checklist

| item | closed |
| --- | --- |
| decoder_stage_candidates_closed | True |
| decoder_row_rules_closed | True |
| decoder_logic_repair_strategy_closed | True |
| decoder_composite_leaf_conventions_closed | True |
| decoder_stage_templates_closed | True |
| decoder_truth_table_binding_closed | True |
| decoder_output_contracts_closed | True |
| decoder_output_handoff_budget_closed | True |
| decoder_generated_block_plan_closed | True |
| decoder_preplacement_feasibility_closed | True |
| decoder_handoff_relief_closed | True |
| decoder_channel_requirement_closed | True |
| parent_control_reservation_closed | True |

## Generated-Block Plan Status

```json
{
  "plan_name": "DECODER_CASCADE_GENERATED_BLOCK_PLAN",
  "logic_strategy": "metadata_composite_nand2_inv",
  "level_groups": [
    1,
    4
  ],
  "stage_count": 5,
  "level0_stage": "DEC_0_0",
  "level1_stages": [
    "DEC_1_0",
    "DEC_1_1",
    "DEC_1_2",
    "DEC_1_3"
  ],
  "truth_table_binding_complete": true,
  "output_contracts_available": true,
  "all_level1_outputs_have_handoff_budget": true
}
```

## Preplacement / Channel / Parent Reservation Status

```json
{
  "decoder_preplacement_status": {
    "bounded_preplacement_model_available": true,
    "metadata_stage_packing_consistent": true,
    "bbox_proxy_overlap_found": false,
    "wordline_handoff_budget_is_tight": true
  },
  "decoder_channel_requirement_status": {
    "base_wordline_channel_width": 2.0,
    "recommended_wordline_channel_width": 2.2,
    "old_wordline_margin": 0.0,
    "new_wordline_margin": 0.2,
    "wordline_margin_still_low": true,
    "parent_2p2_reservation_recorded": true,
    "physical_parent_space_proven": false,
    "safe_for_metadata_requirement_propagation": true,
    "safe_for_physical_floorplan_claim": false
  },
  "parent_reservation_status": {
    "reservation_name": "PARENT_CONTROL_ROW_DECODER_WORDLINE_2P2_RESERVATION",
    "parent_reservation_required": true,
    "parent_reservation_recorded": true,
    "physical_parent_space_proven": false,
    "safe_for_parent_metadata_planning": true,
    "safe_for_physical_floorplan_claim": false
  }
}
```

## Open Blockers

- stage bbox proxies are metadata-only
- stage packing is not legalized
- composite internal routing is not proven
- rail continuity is not proven
- shared rail is disabled
- wordline handoff windows are metadata proxies
- wordline margin is still low even after 2.2um requirement
- parent floorplan space for extra 0.2um is not physically proven
- level1 enable target physical pin-side proof is still missing
- full channel legality is not proven
- no DRC/LVS proof exists

## Decision Summary

```json
{
  "decoder_metadata_line_status": "closed_for_now",
  "decoder_physical_push_status": "stop",
  "recommended_next_phase": "TIME_remaining_control_subblock_audit",
  "reason": [
    "decoder metadata is sufficient as future planning reference",
    "decoder physical prototype remains blocked",
    "further local decoder metadata micro-tuning is not the best next investment",
    "remaining TIME/control subblocks now dominate control-signal generation uncertainty"
  ]
}
```

## Step 6.23 Recommendation

```json
{
  "candidate_directions": [
    "delay_chain_adapter_audit",
    "wen_delay_chain_adapter_audit",
    "pdrive_adapter_audit",
    "wl_pdrive_adapter_audit",
    "precharge_control_adapter_audit",
    "time_control_signal_summary"
  ],
  "recommended_step_6_23": "delay_chain_wen_delay_chain_pdrive_adapter_audit",
  "reason": [
    "TIME should not be treated as one opaque macro",
    "DFF and decoder related metadata has reached closure for now",
    "remaining critical timing/control logic includes delay_chain, wen_delay_chain, pdrive, and wl_pdrive",
    "these subblocks drive sense_enable, write_enable, precharge_enb, and wordline_enable generation"
  ]
}
```

