# OpenYield TIME Evidence + Crossing Bundle Report

This report is metadata-only. It does not prove legal routing, legal placement, rail continuity, timing closure, DRC, LVS, or standalone integration readiness.

## Audit Summary

```json
{
  "time_control_evidence_crossing_bundle_available": true,
  "precharge_closure_status": "partial_missing_gnd",
  "precharge_gnd_evidence_found": false,
  "all_required_crossings_have_adjacency": false,
  "all_required_crossings_have_handoff_or_reservation": true,
  "all_crossing_budgets_pass": true,
  "can_enter_time_control_metadata_closure": false,
  "can_enter_time_control_physical_placement": false,
  "can_enter_standalone_control_placement": false
}
```

## PRECHARGE GND Evidence Search

| source | alias | found | pin/label | layer | bbox | side | confidence | notes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| openyield_module_contract.power_pins | VDD | True | VDD | None | None | None | high | OpenYield PRECHARGE source contract explicitly declares VDD -> vdd. |
| openyield_module_contract.power_pins | VSS | False | None | None | None | None | high_negative | OpenYield PRECHARGE source contract does not declare VSS in current parsed metadata. |
| gds_pin_audit.pins | EN/ENB/PRE/precharge_enb | True | EN | 11/texttype0 | {'x0': 0.0, 'y0': -0.045, 'x1': 0.705, 'y1': 0.02} | bottom | high | Local gen_precharge GDS exposes EN as the physical alias of active-low precharge enable. |
| gds_pin_audit.power_rail_audit | gnd | False | None | None | None | missing | high_negative | Current local gen_precharge GDS pin audit reports has_gnd=false. |
| gds_pin_audit.labels | gnd | False | None | None | None | None | high_negative | No gnd text label was found among gen_precharge labels in the current audit report. |
| macro_metadata_audit.module_metadata | VSS/gnd | False | None | None | None | None | medium_negative | Macro metadata audit classifies PRECHARGE power_status as no_gnd_required, which does not prove a local GND pin. |
| openyield_module_contract.pins | BL/BR/BLB | True | BL, BLB | None | None | None | high | Source contract confirms precharge bitline pins only; it does not add GND evidence. |
| local_hardmacro_metadata | VSS!/GND!/VGND/ground/0 | False | None | None | None | None | high_negative | No alternate ground alias evidence was found in current local metadata reports for gen_precharge. |
| local_spice_or_cdl_metadata | gnd | False | None | None | None | None | high_negative | No local SPICE/CDL macro file is registered for gen_precharge in current metadata. |

## PRECHARGE Closure Decision

```json
{
  "precharge_gnd_evidence_search_available": true,
  "precharge_gnd_pin_known": false,
  "precharge_gnd_evidence_found": false,
  "precharge_power_metadata_complete": false,
  "precharge_rail_continuity_proven": false,
  "precharge_closure_status": "partial_missing_gnd",
  "precharge_safe_for_metadata_planning": "partial",
  "precharge_safe_for_physical_placement": false,
  "can_enter_time_control_metadata_closure": true
}
```

## Control Region Crossing Signal Proof

| edge | source signals | target | producer region | consumer region | crossing | adjacency | handoff | reservation | margin | covered |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| CLK_TO_CLK_BUF | clk | clk_buf | pdrive_region | pdrive_region | False | - | - | PDRIVE_REGION_REGION_BUDGET_PROXY | 1.6 | True |
| CLK_BUF_TO_CLK_BAR | clk_buf | clk_bar | pdrive_region | generated_logic_region | True | PDRIVE_TO_GENERATED_LOGIC | - | GENERATED_LOGIC_REGION_REGION_BUDGET_PROXY | 1.2 | True |
| CLK_BUF_CS_TO_GATED_CLK_BUF | clk_buf, cs | gated_clk_buf | generated_logic_region | generated_logic_region | False | - | - | GENERATED_LOGIC_REGION_REGION_BUDGET_PROXY | 1.4 | True |
| CLK_BAR_CS_TO_GATED_CLK_BAR | clk_bar, cs | gated_clk_bar | generated_logic_region | generated_logic_region | False | - | - | GENERATED_LOGIC_REGION_REGION_BUDGET_PROXY | 1.4 | True |
| GATED_CLK_BAR_TO_WL_EN | gated_clk_bar | wl_en | generated_logic_region | wordline_enable_control_region | True | - | WORDLINE_ENABLE_TO_WORDLINEDRIVER_B | CONTROL_ROW_WORDLINE_ENABLE_CHANNEL | 1.6 | False |
| WL_EN_TO_WL_EN_BAR | wl_en | wl_en_bar | wordline_enable_control_region | wordline_enable_control_region | False | - | WL_EN_BAR_TO_PRECHARGE_PNAND3_C | CONTROL_ROW_WL_EN_BAR_SECONDARY_CHANNEL | 1.6 | True |
| RBL_TO_RBL_DELAY | rbl | rbl_delay | delay_chain_region | delay_chain_region | False | - | - | DELAY_CHAIN_REGION_REGION_BUDGET_PROXY | 1.6 | True |
| RBL_DELAY_TO_RBL_DELAY_BAR | rbl_delay | rbl_delay_bar | delay_chain_region | generated_logic_region | True | DELAY_CHAIN_TO_GENERATED_LOGIC | - | GENERATED_LOGIC_REGION_REGION_BUDGET_PROXY | 1.4 | True |
| RBL_DELAY_BAR_GATED_CLK_BAR_WE_TO_W_EN | rbl_delay_bar, gated_clk_bar, we | w_en | sense_write_enable_region | sense_write_enable_region | False | - | WRITE_ENABLE_TO_WRITEDRIVER_EN | CONTROL_ROW_WRITE_ENABLE_CHANNEL | 1.2 | True |
| RBL_DELAY_GATED_CLK_BAR_WE_BAR_TO_S_EN | rbl_delay, gated_clk_bar, we_bar | s_en | sense_write_enable_region | sense_write_enable_region | False | - | SENSE_ENABLE_TO_SENSEAMP_EN | CONTROL_ROW_SENSE_ENABLE_CHANNEL | 1.2 | True |
| GATED_CLK_BUF_RBL_DELAY_WL_EN_BAR_TO_PRE_UNBUF | gated_clk_buf, rbl_delay, wl_en_bar | PRE_UNBUF | precharge_control_region | precharge_control_region | False | - | - | PRECHARGE_CONTROL_REGION_REGION_BUDGET_PROXY | 1.2 | True |
| PRE_UNBUF_TO_PRE | PRE_UNBUF | PRE | precharge_control_region | precharge_control_region | False | - | PRECHARGE_ENB_TO_PRECHARGE_ENB | CONTROL_ROW_PRECHARGE_ENB_CHANNEL | 1.6 | True |

## Crossing Coverage Summary

```json
{
  "control_region_crossing_proof_available": true,
  "all_core_dependency_edges_have_region_assignment": true,
  "all_required_crossings_have_adjacency": false,
  "all_required_crossings_have_handoff_or_reservation": true,
  "all_crossing_budgets_pass": true,
  "missing_region_assignments": [],
  "missing_adjacencies": [
    "GATED_CLK_BAR_TO_WL_EN"
  ],
  "missing_handoff_constraints": [],
  "missing_reservation_rules": [],
  "physical_routing_proven": false
}
```

## Grouped Interface Crossing Proof

| interface | control signals | source regions | target macro | handoff constraints | reservation rules | coverage complete | metadata ready | physical ready |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| TIME_CONTROL_TO_WRITEDRIVER_INTERFACE | write_enable | sense_write_enable_region | WRITEDRIVER | WRITE_ENABLE_TO_WRITEDRIVER_EN | CONTROL_ROW_WRITE_ENABLE_CHANNEL | True | True | False |
| TIME_CONTROL_TO_SENSEAMP_INTERFACE | sense_enable | sense_write_enable_region | SENSEAMP | SENSE_ENABLE_TO_SENSEAMP_EN | CONTROL_ROW_SENSE_ENABLE_CHANNEL | True | True | False |
| TIME_CONTROL_TO_PRECHARGE_INTERFACE | precharge_enb, wl_en_bar | precharge_control_region, wordline_enable_control_region | PRECHARGE | PRECHARGE_ENB_TO_PRECHARGE_ENB, WL_EN_BAR_TO_PRECHARGE_PNAND3_C | CONTROL_ROW_PRECHARGE_ENB_CHANNEL, CONTROL_ROW_WL_EN_BAR_SECONDARY_CHANNEL | True | partial | False |
| TIME_CONTROL_TO_WORDLINEDRIVER_INTERFACE | wordline_enable | wordline_enable_control_region | WORDLINEDRIVER | WORDLINE_ENABLE_TO_WORDLINEDRIVER_B | CONTROL_ROW_WORDLINE_ENABLE_CHANNEL | True | True | False |

## Consistency Checks

| check | value |
| --- | --- |
| time_control_evidence_crossing_bundle_available | True |
| precharge_gnd_evidence_search_available | True |
| precharge_gnd_evidence_found | False |
| precharge_closure_status | partial_missing_gnd |
| precharge_power_metadata_complete | False |
| control_region_crossing_proof_available | True |
| all_core_dependency_edges_have_region_assignment | True |
| all_required_crossings_have_adjacency | False |
| all_required_crossings_have_handoff_or_reservation | True |
| all_crossing_budgets_pass | True |
| grouped_interface_crossing_proof_available | True |
| can_enter_time_control_metadata_closure | False |
| can_enter_time_control_physical_placement | False |
| can_enter_standalone_control_placement | False |
| safe_for_metadata_planning | False |
| safe_for_physical_placement | False |

## Unresolved Items

- PRECHARGE GND may remain missing, depending on evidence result
- PRECHARGE rail continuity proof is missing
- crossing proof is metadata-only, not legal routing
- region adjacency is not legal routing
- abstract region refinement is not legal placement
- control routing proof is missing
- delay timing proof is missing
- wen-delay timing proof is missing
- shared rail is disabled
- no DRC/LVS proof exists
- standalone integration is not allowed yet

## Step 6.31 Recommendation

```json
{
  "recommended_next_phase": "time_control_precharge_local_ground_semantics_or_finer_crossing_contracts",
  "candidate_directions": [
    "precharge_local_ground_semantics_review",
    "conditional_wen_crossing_refinement",
    "macro_handoff_side_refinement",
    "time_control_delay_timing_metadata_refinement"
  ],
  "reason": [
    "PRECHARGE local hardmacro metadata still does not expose GND evidence in current reports.",
    "Crossing coverage is now bundled and structurally covered at metadata level, but it is still not legal routing proof.",
    "The next step should refine evidence or contract granularity rather than attempt standalone integration."
  ]
}
```

## Entry Decisions

- can_enter_time_control_metadata_closure: `False`
- can_enter_time_control_physical_placement: `False`
- can_enter_standalone_control_placement: `False`

