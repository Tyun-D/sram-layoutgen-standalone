# OpenYield TIME Control Composite Feasibility Report

- Scope: `time_control_composite_internal_placement_feasibility_audit`
- Repo root: `E:\njust\keyan\SRAM Compiler_V2\OpenRAM-stable\deliverables\sram_layoutgen_step45_clean`
- Tech dir: `E:\njust\keyan\SRAM Compiler_V2\OpenRAM-stable\deliverables\sram_layoutgen_step45_clean\technology\freepdk45`

## Audit Summary

```json
{
  "time_control_composite_internal_placement_feasibility_available": true,
  "all_required_subblocks_analyzed": true,
  "all_required_leaf_sequences_available": true,
  "all_required_bbox_proxies_available": true,
  "all_required_external_pin_accessibility_available": true,
  "all_required_power_side_compatibility_checked": true,
  "composite_internal_routing_proven": false,
  "timing_proof_available": false,
  "rail_continuity_proven": false,
  "precharge_exception_retained": true,
  "can_enter_legal_placement_readonly_audit": true,
  "can_enter_routing_obstacle_readonly_audit": true,
  "can_enter_timing_metadata_inventory": true,
  "can_enter_physical_placement_now": false,
  "can_generate_time_control_gds_now": false,
  "can_modify_standalone_now": false
}
```

## Input Reports And Assets

```json
{
  "leaf_inventory": "E:\\njust\\keyan\\SRAM Compiler_V2\\OpenRAM-stable\\deliverables\\sram_layoutgen_step45_clean\\docs\\openyield_time_control_leaf_inventory_report.json",
  "power_rail_audit": "E:\\njust\\keyan\\SRAM Compiler_V2\\OpenRAM-stable\\deliverables\\sram_layoutgen_step45_clean\\docs\\openyield_hardcell_power_rail_continuity_report.json",
  "generated_logic_contracts": "E:\\njust\\keyan\\SRAM Compiler_V2\\OpenRAM-stable\\deliverables\\sram_layoutgen_step45_clean\\docs\\openyield_time_control_generated_logic_contract_report.json",
  "abstract_payload": "E:\\njust\\keyan\\SRAM Compiler_V2\\OpenRAM-stable\\deliverables\\sram_layoutgen_step45_clean\\docs\\openyield_time_control_abstract_floorplan_payload_report.json",
  "region_refinement": "E:\\njust\\keyan\\SRAM Compiler_V2\\OpenRAM-stable\\deliverables\\sram_layoutgen_step45_clean\\docs\\openyield_time_control_region_refinement_report.json"
}
```

## Subblock Composite Topology

| subblock | leaf sequence | bbox proxy (w x h) | classification | legal-readonly | physical |
| --- | --- | --- | --- | --- | --- |
| PINV | gen_inv | 0.8225 x 1.48 | ready_for_readonly_legal_placement_planning | True | False |
| AND2 | gen_nand2 -> gen_inv | 1.86 x 1.48 | ready_for_readonly_feasibility_but_missing_timing | True | False |
| AND3_COMPOSITE | gen_nand2 -> gen_inv -> gen_nand2 -> gen_inv | 3.72 x 1.48 | ready_for_readonly_feasibility_but_missing_timing | True | False |
| PNAND3_COMPOSITE | gen_nand2 -> gen_inv -> gen_nand2 | 2.897 x 1.48 | ready_for_readonly_feasibility_but_precharge_exception | True | False |
| PDRIVE | gen_inv -> gen_inv -> gen_inv -> gen_inv | 3.29 x 1.48 | ready_for_readonly_feasibility_but_missing_timing | True | False |
| PDRIVE2_FOR_PRE | gen_inv -> gen_inv | 1.645 x 1.48 | ready_for_readonly_feasibility_but_precharge_exception | True | False |
| WL_PDRIVE | gen_inv -> gen_inv | 1.645 x 1.48 | ready_for_readonly_feasibility_but_missing_timing | True | False |
| DELAY_CHAIN | gen_delay_inv -> gen_delay_inv -> gen_delay_inv -> gen_delay_inv -> gen_delay_inv -> gen_delay_inv -> gen_delay_inv -> gen_delay_inv -> gen_delay_inv | 7.402 x 2.585 | ready_for_readonly_feasibility_but_missing_timing | True | False |
| WEN_DELAY_CHAIN | gen_delay_inv -> gen_delay_inv -> gen_delay_inv -> gen_delay_inv -> gen_delay_inv -> gen_delay_inv | 4.935 x 2.585 | ready_for_readonly_feasibility_but_missing_timing | True | False |
| PRECHARGE | gen_precharge | 0.785 x 1.42 | ready_for_readonly_feasibility_but_precharge_exception | True | False |
| DFF_ROW | dff | 2.86 x 2.67 | blocked_by_row_placement_requirement | True | False |

## Leaf Sequence / BBox Proxy Table

| subblock | leaf count | width | height | ordering | internal nets |
| --- | --- | --- | --- | --- | --- |
| PINV | 1 | 0.8225 | 1.4800000000000002 | single_stage |  |
| AND2 | 2 | 1.86 | 1.4800000000000002 | gen_nand2 -> gen_inv | n_ab |
| AND3_COMPOSITE | 4 | 3.72 | 1.4800000000000002 | gen_nand2 -> gen_inv -> gen_nand2 -> gen_inv | ab_n, ab, abc_n |
| PNAND3_COMPOSITE | 3 | 2.8975 | 1.4800000000000002 | gen_nand2 -> gen_inv -> gen_nand2 | ab_n, ab |
| PDRIVE | 4 | 3.29 | 1.4800000000000002 | repeated gen_inv buffer stages | stage_0, stage_1, stage_2 |
| PDRIVE2_FOR_PRE | 2 | 1.645 | 1.4800000000000002 | repeated gen_inv buffer stages | stage_0 |
| WL_PDRIVE | 2 | 1.645 | 1.4800000000000002 | repeated gen_inv buffer stages | stage_0 |
| DELAY_CHAIN | 9 | 7.4025 | 2.585 | repeated gen_delay_inv stages | stage_0, stage_1, stage_2, stage_3, stage_4, stage_5, stage_6, stage_7 |
| WEN_DELAY_CHAIN | 6 | 4.9350000000000005 | 2.585 | repeated gen_delay_inv stages | stage_0, stage_1, stage_2, stage_3, stage_4 |
| PRECHARGE | 1 | 0.7849999999999999 | 1.4200000000000002 | gen_precharge |  |
| DFF_ROW | 1 | 2.8599999999999826 | 2.6699999999999835 | repeated dff in row order |  |

## Pin Accessibility Summary

| subblock | input | output | control | internal nets |
| --- | --- | --- | --- | --- |
| PINV | complete | complete | not_applicable | not_applicable |
| AND2 | complete | complete | not_applicable | metadata_proxy_only |
| AND3_COMPOSITE | partial | complete | not_applicable | metadata_proxy_only |
| PNAND3_COMPOSITE | partial | complete | not_applicable | metadata_proxy_only |
| PDRIVE | complete | complete | not_applicable | metadata_proxy_only |
| PDRIVE2_FOR_PRE | complete | complete | not_applicable | metadata_proxy_only |
| WL_PDRIVE | complete | complete | not_applicable | metadata_proxy_only |
| DELAY_CHAIN | complete | complete | not_applicable | metadata_proxy_only |
| WEN_DELAY_CHAIN | complete | complete | not_applicable | metadata_proxy_only |
| PRECHARGE | not_applicable | complete | complete | not_applicable |
| DFF_ROW | complete | complete | complete | not_applicable |

## Power Side Compatibility Summary

| subblock | vdd consistency | gnd consistency | policy | precharge exception |
| --- | --- | --- | --- | --- |
| PINV | True | True | consistent_vdd_top_gnd_bottom | - |
| AND2 | True | True | consistent_vdd_top_gnd_bottom | - |
| AND3_COMPOSITE | True | True | consistent_vdd_top_gnd_bottom | - |
| PNAND3_COMPOSITE | True | True | consistent_vdd_top_gnd_bottom | intentional_no_local_gnd_metadata_exception |
| PDRIVE | True | True | consistent_vdd_top_gnd_bottom | - |
| PDRIVE2_FOR_PRE | True | True | consistent_vdd_top_gnd_bottom | intentional_no_local_gnd_metadata_exception |
| WL_PDRIVE | True | True | consistent_vdd_top_gnd_bottom | - |
| DELAY_CHAIN | True | True | consistent_vdd_top_gnd_bottom | - |
| WEN_DELAY_CHAIN | True | True | consistent_vdd_top_gnd_bottom | - |
| PRECHARGE | True | False | precharge_vdd_only_exception | intentional_no_local_gnd_metadata_exception |
| DFF_ROW | True | True | consistent_vdd_top_gnd_bottom | - |

## PRECHARGE Exception Section

```json
{
  "subblock_name": "PRECHARGE",
  "precharge_exception_if_any": "intentional_no_local_gnd_metadata_exception",
  "safe_for_composite_readonly_feasibility": true,
  "safe_for_legal_placement_readonly": true,
  "safe_for_physical_placement": false,
  "blockers": [
    "precharge power exception retained",
    "blocked by precharge power exception",
    "rail continuity proof missing",
    "no legal routing proof",
    "no physical placement proof",
    "PRECHARGE adapter metadata may remain partial",
    "PRECHARGE power-domain closure may remain incomplete",
    "handoff constraints are metadata-only",
    "channel reservation rules are not legal routing",
    "control routing proof is missing",
    "rail continuity proof is missing",
    "no local GND proof and no across-abutment rail continuity proof"
  ]
}
```

## DFF Row Feasibility Section

```json
{
  "subblock_name": "DFF_ROW",
  "requires_row_alignment": true,
  "row_alignment_available": true,
  "safe_for_composite_readonly_feasibility": true,
  "safe_for_legal_placement_readonly": true,
  "safe_for_physical_placement": false,
  "blockers": [
    "row placement proof required",
    "no legal placement proof",
    "no routing proof",
    "no standalone integration"
  ]
}
```

## Feasibility Classification

| subblock | classification | readonly feasibility | legal-readonly | physical |
| --- | --- | --- | --- | --- |
| PINV | ready_for_readonly_legal_placement_planning | True | True | False |
| AND2 | ready_for_readonly_feasibility_but_missing_timing | True | True | False |
| AND3_COMPOSITE | ready_for_readonly_feasibility_but_missing_timing | True | True | False |
| PNAND3_COMPOSITE | ready_for_readonly_feasibility_but_precharge_exception | True | True | False |
| PDRIVE | ready_for_readonly_feasibility_but_missing_timing | True | True | False |
| PDRIVE2_FOR_PRE | ready_for_readonly_feasibility_but_precharge_exception | True | True | False |
| WL_PDRIVE | ready_for_readonly_feasibility_but_missing_timing | True | True | False |
| DELAY_CHAIN | ready_for_readonly_feasibility_but_missing_timing | True | True | False |
| WEN_DELAY_CHAIN | ready_for_readonly_feasibility_but_missing_timing | True | True | False |
| PRECHARGE | ready_for_readonly_feasibility_but_precharge_exception | True | True | False |
| DFF_ROW | blocked_by_row_placement_requirement | True | True | False |

## Blockers

- PINV: stdcell physical library not proven
- PINV: no legal routing proof
- PINV: no DRC/LVS proof
- AND2: timing proof required
- AND2: routing proof required
- AND2: stdcell physical library not proven
- AND2: no legal routing proof
- AND2: no DRC/LVS proof
- AND3_COMPOSITE: timing proof required
- AND3_COMPOSITE: routing proof required
- AND3_COMPOSITE: stdcell physical library not proven
- AND3_COMPOSITE: no legal routing proof
- AND3_COMPOSITE: no DRC/LVS proof
- AND3_COMPOSITE: handoff constraints are metadata-only
- AND3_COMPOSITE: channel reservation rules are not legal routing
- AND3_COMPOSITE: control routing proof is missing
- AND3_COMPOSITE: delay timing proof is missing
- PNAND3_COMPOSITE: precharge power exception retained
- PNAND3_COMPOSITE: timing proof required
- PNAND3_COMPOSITE: routing proof required
- PNAND3_COMPOSITE: rail continuity proof missing
- PNAND3_COMPOSITE: no legal routing proof
- PNAND3_COMPOSITE: no physical placement proof
- PNAND3_COMPOSITE: PRECHARGE adapter metadata may remain partial
- PNAND3_COMPOSITE: PRECHARGE power-domain closure may remain incomplete
- PNAND3_COMPOSITE: handoff constraints are metadata-only
- PNAND3_COMPOSITE: channel reservation rules are not legal routing
- PNAND3_COMPOSITE: control routing proof is missing
- PNAND3_COMPOSITE: rail continuity proof is missing
- PDRIVE: timing proof required
- PDRIVE: routing proof required
- PDRIVE: no legal placement proof
- PDRIVE: no routing proof
- PDRIVE2_FOR_PRE: precharge power exception retained
- PDRIVE2_FOR_PRE: timing proof required
- PDRIVE2_FOR_PRE: routing proof required
- PDRIVE2_FOR_PRE: rail continuity proof missing
- PDRIVE2_FOR_PRE: no legal routing proof
- PDRIVE2_FOR_PRE: no physical placement proof
- PDRIVE2_FOR_PRE: PRECHARGE adapter metadata may remain partial
- PDRIVE2_FOR_PRE: PRECHARGE power-domain closure may remain incomplete
- PDRIVE2_FOR_PRE: handoff constraints are metadata-only
- PDRIVE2_FOR_PRE: channel reservation rules are not legal routing
- PDRIVE2_FOR_PRE: control routing proof is missing
- PDRIVE2_FOR_PRE: rail continuity proof is missing
- WL_PDRIVE: timing proof required
- WL_PDRIVE: routing proof required
- WL_PDRIVE: no legal placement proof
- WL_PDRIVE: no routing proof
- WL_PDRIVE: handoff constraints are metadata-only
- WL_PDRIVE: channel reservation rules are not legal routing
- WL_PDRIVE: control routing proof is missing
- WL_PDRIVE: delay timing proof is missing
- DELAY_CHAIN: timing proof required
- DELAY_CHAIN: routing proof required
- DELAY_CHAIN: delay timing proof missing
- DELAY_CHAIN: no legal placement proof
- DELAY_CHAIN: no routing proof
- WEN_DELAY_CHAIN: timing proof required
- WEN_DELAY_CHAIN: routing proof required
- WEN_DELAY_CHAIN: wen-delay timing proof missing
- WEN_DELAY_CHAIN: no legal placement proof
- WEN_DELAY_CHAIN: no routing proof
- WEN_DELAY_CHAIN: handoff constraints are metadata-only
- WEN_DELAY_CHAIN: channel reservation rules are not legal routing
- WEN_DELAY_CHAIN: control routing proof is missing
- WEN_DELAY_CHAIN: delay timing proof is missing
- PRECHARGE: precharge power exception retained
- PRECHARGE: blocked by precharge power exception
- PRECHARGE: rail continuity proof missing
- PRECHARGE: no legal routing proof
- PRECHARGE: no physical placement proof
- PRECHARGE: PRECHARGE adapter metadata may remain partial
- PRECHARGE: PRECHARGE power-domain closure may remain incomplete
- PRECHARGE: handoff constraints are metadata-only
- PRECHARGE: channel reservation rules are not legal routing
- PRECHARGE: control routing proof is missing
- PRECHARGE: rail continuity proof is missing
- PRECHARGE: no local GND proof and no across-abutment rail continuity proof
- DFF_ROW: row placement proof required
- DFF_ROW: no legal placement proof
- DFF_ROW: no routing proof
- DFF_ROW: no standalone integration

## Boundary Assertions

```json
{
  "bbox_proxy_is_not_legal_placement": true,
  "pin_accessibility_is_not_routing_proof": true,
  "power_side_consistency_is_not_rail_continuity_proof": true,
  "readonly_feasibility_is_not_physical_ready": true,
  "standalone_modified": false,
  "routing_modified": false,
  "gds_writer_modified": false
}
```