# OpenYield TIME Control Routing Obstacle Readonly Report

- Scope: `time_control_routing_obstacle_readonly_audit`
- Repo root: `E:\njust\keyan\SRAM Compiler_V2\OpenRAM-stable\deliverables\sram_layoutgen_step45_clean`
- Tech dir: `E:\njust\keyan\SRAM Compiler_V2\OpenRAM-stable\deliverables\sram_layoutgen_step45_clean\technology\freepdk45`

## Audit Summary

```json
{
  "time_control_routing_obstacle_readonly_audit_available": true,
  "all_required_control_nets_analyzed": true,
  "all_required_region_crossings_checked": true,
  "all_required_handoffs_checked": true,
  "obstacle_inventory_available": true,
  "pin_access_risk_classified": true,
  "channel_pressure_rechecked": true,
  "routing_obstacle_readonly_candidate_available": true,
  "routing_proof_available_now": false,
  "can_enter_timing_metadata_inventory": true,
  "can_enter_routing_proof_planning": true,
  "can_enter_physical_routing_now": false,
  "can_enter_physical_placement_now": false,
  "can_generate_time_control_gds_now": false,
  "can_modify_standalone_now": false
}
```

## Input Reports And Assets

```json
{
  "legal_placement_readonly": "E:\\njust\\keyan\\SRAM Compiler_V2\\OpenRAM-stable\\deliverables\\sram_layoutgen_step45_clean\\docs\\openyield_time_control_legal_placement_readonly_report.json",
  "composite_feasibility": "E:\\njust\\keyan\\SRAM Compiler_V2\\OpenRAM-stable\\deliverables\\sram_layoutgen_step45_clean\\docs\\openyield_time_control_composite_feasibility_report.json",
  "leaf_inventory": "E:\\njust\\keyan\\SRAM Compiler_V2\\OpenRAM-stable\\deliverables\\sram_layoutgen_step45_clean\\docs\\openyield_time_control_leaf_inventory_report.json",
  "region_refinement": "E:\\njust\\keyan\\SRAM Compiler_V2\\OpenRAM-stable\\deliverables\\sram_layoutgen_step45_clean\\docs\\openyield_time_control_region_refinement_report.json",
  "metadata_closure": "E:\\njust\\keyan\\SRAM Compiler_V2\\OpenRAM-stable\\deliverables\\sram_layoutgen_step45_clean\\docs\\openyield_time_control_metadata_closure_report.json"
}
```

## Control Net Routing Obstacle Table

| net | source | targets | crosses boundary | margin | pin access | obstacle risk | readonly planning |
| --- | --- | --- | --- | --- | --- | --- | --- |
| clk | external_clock | PDRIVE | True | None | metadata_complete | moderate | True |
| clk_buf | PDRIVE | PINV, AND2, AND3_COMPOSITE | True | 1.2 | metadata_complete | moderate | True |
| clk_bar | PINV | AND2, AND3_COMPOSITE | False | None | metadata_complete | moderate | True |
| gated_clk_buf | AND2 | PNAND3_COMPOSITE | True | None | metadata_complete | moderate | True |
| gated_clk_bar | AND2 | WL_PDRIVE, WEN_DELAY_CHAIN | True | None | metadata_complete | moderate | True |
| rbl | replica_array | DELAY_CHAIN | True | None | metadata_complete | moderate | True |
| rbl_delay | DELAY_CHAIN | AND3_COMPOSITE, WEN_DELAY_CHAIN | True | 1.4 | metadata_complete | moderate | True |
| rbl_delay_bar | PINV | DELAY_CHAIN, WEN_DELAY_CHAIN | True | None | metadata_complete | moderate | True |
| rbl_delay_bar_wen | DELAY_CHAIN | WEN_DELAY_CHAIN | True | 1.4 | metadata_complete | moderate | True |
| we | external_control | AND3_COMPOSITE, WEN_DELAY_CHAIN | True | None | metadata_complete | low | True |
| we_bar | external_control | AND3_COMPOSITE, WEN_DELAY_CHAIN | True | None | metadata_complete | low | True |
| w_en | WEN_DELAY_CHAIN | write_driver | True | 1.0 | partial | moderate | True |
| write_enable | AND3_COMPOSITE | write_driver | True | 1.0 | metadata_complete | moderate | True |
| s_en | WEN_DELAY_CHAIN | sense_amp | True | 1.0 | partial | moderate | True |
| sense_enable | AND3_COMPOSITE | sense_amp | True | 1.0 | metadata_complete | moderate | True |
| PRE_UNBUF | PNAND3_COMPOSITE | PDRIVE2_FOR_PRE | False | None | partial | moderate | True |
| PRE | PDRIVE2_FOR_PRE | gen_precharge | True | 1.0 | partial | moderate_to_high | True |
| precharge_enb | PDRIVE2_FOR_PRE | gen_precharge | True | 1.6 | partial | moderate_to_high | True |
| wl_en | WL_PDRIVE | gen_wl_driver | True | 1.2 | metadata_complete | moderate | True |
| wordline_enable | WL_PDRIVE | gen_wl_driver | True | 1.6 | partial | moderate | True |
| wl_en_bar | PINV | PNAND3_COMPOSITE, gen_precharge | True | 1.6 | partial | moderate_to_high | True |

## Region Crossing / Adjacency Audit

| edge | signal | source region | target region | adjacency | handoff | reservation | routing proof |
| --- | --- | --- | --- | --- | --- | --- | --- |
| DELAY_CHAIN_TO_GENERATED_LOGIC | rbl_delay | delay_chain_region | generated_logic_region | True | False | False | False |
| DELAY_CHAIN_TO_GENERATED_LOGIC | rbl_delay_bar_wen | delay_chain_region | generated_logic_region | True | False | False | False |
| PDRIVE_TO_GENERATED_LOGIC | clk_buf | pdrive_region | generated_logic_region | True | False | False | False |
| PDRIVE_TO_GENERATED_LOGIC | PRE | pdrive_region | generated_logic_region | True | False | False | False |
| GATED_CLK_BAR_TO_WL_EN | wl_en | generated_logic_region | wordline_enable_control_region | True | False | False | False |
| GENERATED_LOGIC_TO_CONSUMER_HANDOFF | w_en | generated_logic_region | consumer_handoff_region | True | False | False | False |
| GENERATED_LOGIC_TO_CONSUMER_HANDOFF | s_en | generated_logic_region | consumer_handoff_region | True | False | False | False |
| GENERATED_LOGIC_TO_CONSUMER_HANDOFF | PRE | generated_logic_region | consumer_handoff_region | True | False | False | False |
| PRECHARGE_ENB_TO_CONSUMER_HANDOFF | precharge_enb | precharge_control_region | consumer_handoff_region | True | True | True | False |
| WORDLINE_ENABLE_TO_CONSUMER_HANDOFF | wordline_enable | wordline_enable_control_region | consumer_handoff_region | True | True | True | False |
| WRITE_ENABLE_TO_CONSUMER_HANDOFF | write_enable | sense_write_enable_region | consumer_handoff_region | True | True | True | False |
| SENSE_ENABLE_TO_CONSUMER_HANDOFF | sense_enable | sense_write_enable_region | consumer_handoff_region | True | True | True | False |
| WL_EN_BAR_TO_PRECHARGE_CONTROL | wl_en_bar | wordline_enable_control_region | precharge_control_region | True | True | True | False |

## Obstacle Source Inventory

| obstacle | type | region/macro | layer | direction | risk |
| --- | --- | --- | --- | --- | --- |
| storage_array_boundary | boundary | storage_array_boundary | unknown | vertical | moderate |
| bitcell_bl_br_verticals | routing_trunk | storage_array_boundary | m2_or_m3_unknown | vertical | moderate |
| wordline_horizontals | routing_trunk | storage_array_boundary | m1_or_m2_unknown | horizontal | moderate |
| sense_amp_pin_sides | consumer_macro_pin_side | sense_amp | unknown | unknown | moderate |
| column_mux_pin_sides | consumer_macro_pin_side | gen_col_mux_vdd_labeled | unknown | unknown | low |
| write_driver_pin_sides | consumer_macro_pin_side | write_driver | unknown | unknown | moderate |
| precharge_pin_side | consumer_macro_pin_side | gen_precharge | unknown | unknown | moderate |
| dff_row_clock_data_pins | row_pin_bank | dff | unknown | unknown | moderate |
| power_rails | power_rail | multiple_macros | unknown | horizontal_or_vertical_unknown | moderate |
| reserved_control_channels | reservation_proxy | control_regions | unknown | unknown | moderate |

## Consumer Handoff Audit

| handoff | signal | consumer | pin | pin side | adjacency | readonly planning | physical |
| --- | --- | --- | --- | --- | --- | --- | --- |
| WRITE_ENABLE_TO_WRITEDRIVER_EN | write_enable | write_driver | EN | bottom | True | True | False |
| SENSE_ENABLE_TO_SENSEAMP_EN | sense_enable | sense_amp | EN | top | True | True | False |
| PRECHARGE_ENB_TO_PRECHARGE_ENB | precharge_enb | gen_precharge | ENB | bottom | True | True | False |
| WORDLINE_ENABLE_TO_WORDLINEDRIVER_B | wordline_enable | gen_wl_driver | B | left | True | True | False |
| WL_EN_BAR_TO_PRECHARGE_PNAND3_C | wl_en_bar | gen_precharge | PNAND3.C | unknown | True | True | False |

## PRECHARGE Routing Exception Audit

```json
{
  "precharge_signal": "precharge_enb / PRE / wl_en_bar",
  "precharge_pin": "ENB / en_bar / PNAND3.C",
  "precharge_pin_side": "bottom",
  "precharge_no_local_gnd_exception": true,
  "precharge_power_side_status": "vdd_only_exception_metadata_only",
  "precharge_region": "precharge_control_region",
  "precharge_handoff_region": "consumer_handoff_region",
  "precharge_routing_obstacle_risk": "moderate",
  "precharge_rail_continuity_proven": false,
  "precharge_routing_proof_available": false,
  "precharge_safe_for_routing_readonly_planning": true,
  "precharge_safe_for_physical_routing": false,
  "precharge_blocks_physical_gate": true,
  "blockers": [
    "PRECHARGE adapter metadata may remain partial",
    "PRECHARGE power-domain closure may remain incomplete",
    "handoff constraints are metadata-only",
    "channel reservation rules are not legal routing",
    "control routing proof is missing",
    "rail continuity proof is missing",
    "precharge path retains metadata-only exception",
    "routing proof is missing",
    "no local GND proof and no across-abutment rail continuity proof"
  ]
}
```

## Blockers

- clk: region adjacency metadata missing
- clk: no handoff constraint or reservation rule
- clk: routing proof is missing
- clk_buf: no handoff constraint or reservation rule
- clk_buf: routing proof is missing
- clk_bar: routing proof is missing
- gated_clk_buf: region adjacency metadata missing
- gated_clk_buf: no handoff constraint or reservation rule
- gated_clk_buf: routing proof is missing
- gated_clk_bar: region adjacency metadata missing
- gated_clk_bar: no handoff constraint or reservation rule
- gated_clk_bar: routing proof is missing
- rbl: region adjacency metadata missing
- rbl: no handoff constraint or reservation rule
- rbl: routing proof is missing
- rbl_delay: no handoff constraint or reservation rule
- rbl_delay: routing proof is missing
- rbl_delay_bar: region adjacency metadata missing
- rbl_delay_bar: no handoff constraint or reservation rule
- rbl_delay_bar: routing proof is missing
- rbl_delay_bar_wen: no handoff constraint or reservation rule
- rbl_delay_bar_wen: routing proof is missing
- we: region adjacency metadata missing
- we: no handoff constraint or reservation rule
- we: routing proof is missing
- we_bar: region adjacency metadata missing
- we_bar: no handoff constraint or reservation rule
- we_bar: routing proof is missing
- w_en: pin-side metadata incomplete or partial
- w_en: no handoff constraint or reservation rule
- w_en: routing proof is missing
- write_enable: routing proof is missing
- s_en: pin-side metadata incomplete or partial
- s_en: no handoff constraint or reservation rule
- s_en: routing proof is missing
- sense_enable: routing proof is missing
- PRE_UNBUF: pin-side metadata incomplete or partial
- PRE_UNBUF: routing proof is missing
- PRE: pin-side metadata incomplete or partial
- PRE: precharge path retains metadata-only exception
- PRE: routing proof is missing
- precharge_enb: pin-side metadata incomplete or partial
- precharge_enb: precharge path retains metadata-only exception
- precharge_enb: routing proof is missing
- wl_en: routing proof is missing
- wordline_enable: pin-side metadata incomplete or partial
- wordline_enable: routing proof is missing
- wl_en_bar: pin-side metadata incomplete or partial
- wl_en_bar: precharge path retains metadata-only exception
- wl_en_bar: routing proof is missing
- DELAY_CHAIN_TO_GENERATED_LOGIC: adjacency is metadata only
- DELAY_CHAIN_TO_GENERATED_LOGIC: routing proof is missing
- PDRIVE_TO_GENERATED_LOGIC: adjacency is metadata only
- PDRIVE_TO_GENERATED_LOGIC: routing proof is missing
- GATED_CLK_BAR_TO_WL_EN: adjacency is metadata only
- GATED_CLK_BAR_TO_WL_EN: routing proof is missing
- GENERATED_LOGIC_TO_CONSUMER_HANDOFF: adjacency is metadata only
- GENERATED_LOGIC_TO_CONSUMER_HANDOFF: routing proof is missing
- PRECHARGE_ENB_TO_CONSUMER_HANDOFF: adjacency is metadata only
- PRECHARGE_ENB_TO_CONSUMER_HANDOFF: routing proof is missing
- WORDLINE_ENABLE_TO_CONSUMER_HANDOFF: adjacency is metadata only
- WORDLINE_ENABLE_TO_CONSUMER_HANDOFF: routing proof is missing
- WRITE_ENABLE_TO_CONSUMER_HANDOFF: adjacency is metadata only
- WRITE_ENABLE_TO_CONSUMER_HANDOFF: routing proof is missing
- SENSE_ENABLE_TO_CONSUMER_HANDOFF: adjacency is metadata only
- SENSE_ENABLE_TO_CONSUMER_HANDOFF: routing proof is missing
- WL_EN_BAR_TO_PRECHARGE_CONTROL: adjacency is metadata only
- WL_EN_BAR_TO_PRECHARGE_CONTROL: routing proof is missing
- WRITE_ENABLE_TO_WRITEDRIVER_EN: handoff constraints are metadata-only
- WRITE_ENABLE_TO_WRITEDRIVER_EN: channel reservation rules are not legal routing
- WRITE_ENABLE_TO_WRITEDRIVER_EN: control routing proof is missing
- WRITE_ENABLE_TO_WRITEDRIVER_EN: delay timing proof is missing
- WRITE_ENABLE_TO_WRITEDRIVER_EN: routing proof is missing
- SENSE_ENABLE_TO_SENSEAMP_EN: handoff constraints are metadata-only
- SENSE_ENABLE_TO_SENSEAMP_EN: channel reservation rules are not legal routing
- SENSE_ENABLE_TO_SENSEAMP_EN: control routing proof is missing
- SENSE_ENABLE_TO_SENSEAMP_EN: delay timing proof is missing
- SENSE_ENABLE_TO_SENSEAMP_EN: routing proof is missing
- PRECHARGE_ENB_TO_PRECHARGE_ENB: PRECHARGE adapter metadata may remain partial
- PRECHARGE_ENB_TO_PRECHARGE_ENB: PRECHARGE power-domain closure may remain incomplete
- PRECHARGE_ENB_TO_PRECHARGE_ENB: handoff constraints are metadata-only
- PRECHARGE_ENB_TO_PRECHARGE_ENB: channel reservation rules are not legal routing
- PRECHARGE_ENB_TO_PRECHARGE_ENB: control routing proof is missing
- PRECHARGE_ENB_TO_PRECHARGE_ENB: rail continuity proof is missing
- PRECHARGE_ENB_TO_PRECHARGE_ENB: precharge path retains metadata-only exception
- PRECHARGE_ENB_TO_PRECHARGE_ENB: routing proof is missing
- WORDLINE_ENABLE_TO_WORDLINEDRIVER_B: handoff constraints are metadata-only
- WORDLINE_ENABLE_TO_WORDLINEDRIVER_B: channel reservation rules are not legal routing
- WORDLINE_ENABLE_TO_WORDLINEDRIVER_B: control routing proof is missing
- WORDLINE_ENABLE_TO_WORDLINEDRIVER_B: delay timing proof is missing
- WORDLINE_ENABLE_TO_WORDLINEDRIVER_B: routing proof is missing
- WL_EN_BAR_TO_PRECHARGE_PNAND3_C: PRECHARGE adapter metadata may remain partial
- WL_EN_BAR_TO_PRECHARGE_PNAND3_C: PRECHARGE power-domain closure may remain incomplete
- WL_EN_BAR_TO_PRECHARGE_PNAND3_C: handoff constraints are metadata-only
- WL_EN_BAR_TO_PRECHARGE_PNAND3_C: channel reservation rules are not legal routing
- WL_EN_BAR_TO_PRECHARGE_PNAND3_C: control routing proof is missing
- WL_EN_BAR_TO_PRECHARGE_PNAND3_C: rail continuity proof is missing
- WL_EN_BAR_TO_PRECHARGE_PNAND3_C: precharge path retains metadata-only exception
- WL_EN_BAR_TO_PRECHARGE_PNAND3_C: routing proof is missing
- storage_array_boundary: obstacle geometry not fully known
- bitcell_bl_br_verticals: obstacle geometry not fully known
- wordline_horizontals: obstacle geometry not fully known
- power_rails: obstacle geometry not fully known
- reserved_control_channels: obstacle geometry not fully known

## Boundary Assertions

```json
{
  "channel_margin_is_not_routing_proof": true,
  "pin_side_metadata_is_not_pin_access_proof": true,
  "obstacle_inventory_is_not_drc_clean": true,
  "safe_for_routing_readonly_planning_is_not_physical_routing": true,
  "standalone_modified": false,
  "routing_modified": false,
  "gds_writer_modified": false
}
```