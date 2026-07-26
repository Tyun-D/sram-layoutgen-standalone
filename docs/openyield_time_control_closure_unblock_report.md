# OpenYield TIME Control Closure Unblock Report

This report unblocks metadata closure only. It does not prove legal routing, legal placement, rail continuity, timing closure, DRC, LVS, or physical readiness.

## Audit Summary

```json
{
  "generated_logic_to_wordline_enable_adjacency_available": true,
  "gated_clk_bar_to_wl_en_crossing_covered": true,
  "all_required_crossings_have_adjacency": true,
  "all_required_crossings_have_handoff_or_reservation": true,
  "all_crossing_budgets_pass": true,
  "precharge_ground_semantics_classification": "intentional_no_local_gnd_metadata_exception",
  "precharge_power_metadata_complete": true,
  "can_enter_time_control_metadata_closure": true
}
```

## Adjacency Unblock

```json
{
  "adjacency_name": "GENERATED_LOGIC_TO_WORDLINE_ENABLE_CONTROL",
  "source_region": "generated_logic_region",
  "target_region": "wordline_enable_control_region",
  "signals_crossing": [
    "gated_clk_bar"
  ],
  "edge_covered": "GATED_CLK_BAR_TO_WL_EN",
  "estimated_tracks": 1,
  "required_width": 0.4,
  "reserved_width": 2.0,
  "margin": 1.6,
  "risk_level": "pass_moderate_margin",
  "metadata_only": true,
  "physical_routing_proven": false,
  "generated_logic_to_wordline_enable_adjacency_available": true,
  "gated_clk_bar_to_wl_en_crossing_covered": true
}
```

## PRECHARGE Ground Semantics

```json
{
  "precharge_ground_semantics_classification": "intentional_no_local_gnd_metadata_exception",
  "precharge_gnd_pin_known": false,
  "precharge_gnd_evidence_found": false,
  "precharge_no_gnd_required_claim_found": true,
  "precharge_power_metadata_complete": true,
  "precharge_power_metadata_completion_basis": "no_local_gnd_required_exception",
  "precharge_rail_continuity_proven": false,
  "precharge_safe_for_metadata_planning": true,
  "precharge_safe_for_physical_placement": false
}
```

## Crossing Proof

| edge | source signals | target | producer region | consumer region | adjacency | handoff | reservation | margin | covered |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| CLK_TO_CLK_BUF | clk | clk_buf | pdrive_region | pdrive_region | - | - | PDRIVE_REGION_REGION_BUDGET_PROXY | 1.6 | True |
| CLK_BUF_TO_CLK_BAR | clk_buf | clk_bar | pdrive_region | generated_logic_region | PDRIVE_TO_GENERATED_LOGIC | - | GENERATED_LOGIC_REGION_REGION_BUDGET_PROXY | 1.2 | True |
| CLK_BUF_CS_TO_GATED_CLK_BUF | clk_buf, cs | gated_clk_buf | generated_logic_region | generated_logic_region | - | - | GENERATED_LOGIC_REGION_REGION_BUDGET_PROXY | 1.4 | True |
| CLK_BAR_CS_TO_GATED_CLK_BAR | clk_bar, cs | gated_clk_bar | generated_logic_region | generated_logic_region | - | - | GENERATED_LOGIC_REGION_REGION_BUDGET_PROXY | 1.4 | True |
| GATED_CLK_BAR_TO_WL_EN | gated_clk_bar | wl_en | generated_logic_region | wordline_enable_control_region | GENERATED_LOGIC_TO_WORDLINE_ENABLE_CONTROL | WORDLINE_ENABLE_TO_WORDLINEDRIVER_B | CONTROL_ROW_WORDLINE_ENABLE_CHANNEL | 1.6 | True |
| WL_EN_TO_WL_EN_BAR | wl_en | wl_en_bar | wordline_enable_control_region | wordline_enable_control_region | - | WL_EN_BAR_TO_PRECHARGE_PNAND3_C | CONTROL_ROW_WL_EN_BAR_SECONDARY_CHANNEL | 1.6 | True |
| RBL_TO_RBL_DELAY | rbl | rbl_delay | delay_chain_region | delay_chain_region | - | - | DELAY_CHAIN_REGION_REGION_BUDGET_PROXY | 1.6 | True |
| RBL_DELAY_TO_RBL_DELAY_BAR | rbl_delay | rbl_delay_bar | delay_chain_region | generated_logic_region | DELAY_CHAIN_TO_GENERATED_LOGIC | - | GENERATED_LOGIC_REGION_REGION_BUDGET_PROXY | 1.4 | True |
| RBL_DELAY_BAR_GATED_CLK_BAR_WE_TO_W_EN | rbl_delay_bar, gated_clk_bar, we | w_en | sense_write_enable_region | sense_write_enable_region | - | WRITE_ENABLE_TO_WRITEDRIVER_EN | CONTROL_ROW_WRITE_ENABLE_CHANNEL | 1.2 | True |
| RBL_DELAY_GATED_CLK_BAR_WE_BAR_TO_S_EN | rbl_delay, gated_clk_bar, we_bar | s_en | sense_write_enable_region | sense_write_enable_region | - | SENSE_ENABLE_TO_SENSEAMP_EN | CONTROL_ROW_SENSE_ENABLE_CHANNEL | 1.2 | True |
| GATED_CLK_BUF_RBL_DELAY_WL_EN_BAR_TO_PRE_UNBUF | gated_clk_buf, rbl_delay, wl_en_bar | PRE_UNBUF | precharge_control_region | precharge_control_region | - | - | PRECHARGE_CONTROL_REGION_REGION_BUDGET_PROXY | 1.2 | True |
| PRE_UNBUF_TO_PRE | PRE_UNBUF | PRE | precharge_control_region | precharge_control_region | - | PRECHARGE_ENB_TO_PRECHARGE_ENB | CONTROL_ROW_PRECHARGE_ENB_CHANNEL | 1.6 | True |

## Crossing Coverage Summary

```json
{
  "generated_logic_to_wordline_enable_adjacency_available": true,
  "gated_clk_bar_to_wl_en_crossing_covered": true,
  "all_required_crossings_have_adjacency": true,
  "missing_adjacencies": [],
  "all_required_crossings_have_handoff_or_reservation": true,
  "all_crossing_budgets_pass": true,
  "physical_routing_proven": false
}
```

## Consistency Checks

| check | value |
| --- | --- |
| time_control_closure_unblock_available | True |
| generated_logic_to_wordline_enable_adjacency_available | True |
| gated_clk_bar_to_wl_en_crossing_covered | True |
| all_required_crossings_have_adjacency | True |
| all_required_crossings_have_handoff_or_reservation | True |
| all_crossing_budgets_pass | True |
| precharge_ground_semantics_classification | intentional_no_local_gnd_metadata_exception |
| precharge_power_metadata_complete | True |
| evidence_conflict_found | False |
| can_enter_time_control_metadata_closure | True |
| can_enter_time_control_physical_placement | False |
| can_enter_standalone_control_placement | False |
| safe_for_metadata_planning | True |
| safe_for_physical_placement | False |

## Unresolved Items

- PRECHARGE ground semantics remains metadata-only even if classified as no-local-gnd exception
- PRECHARGE rail continuity proof is missing
- crossing coverage is metadata-only, not legal routing
- abstract region refinement is not legal placement
- control routing proof is missing
- delay timing proof is missing
- wen-delay timing proof is missing
- shared rail is disabled
- no DRC/LVS proof exists
- standalone integration is not allowed yet

## Entry Decisions

- can_enter_time_control_metadata_closure: `True`
- can_enter_time_control_physical_placement: `False`
- can_enter_standalone_control_placement: `False`

