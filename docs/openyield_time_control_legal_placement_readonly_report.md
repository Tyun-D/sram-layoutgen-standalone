# OpenYield TIME Control Legal Placement Readonly Report

- Scope: `time_control_legal_placement_readonly_audit`
- Repo root: `E:\njust\keyan\SRAM Compiler_V2\OpenRAM-stable\deliverables\sram_layoutgen_step45_clean`
- Tech dir: `E:\njust\keyan\SRAM Compiler_V2\OpenRAM-stable\deliverables\sram_layoutgen_step45_clean\technology\freepdk45`

## Audit Summary

```json
{
  "time_control_legal_placement_readonly_audit_available": true,
  "all_required_subblocks_mapped_to_regions": true,
  "all_required_region_capacity_checked": true,
  "all_required_bbox_proxies_fit_or_unknown_recorded": true,
  "overlap_free_in_metadata_proxy": true,
  "spacing_constraints_metadata_pass": true,
  "channel_pressure_metadata_pass": true,
  "dff_row_readonly_fit_available": true,
  "precharge_exception_retained": true,
  "legal_placement_readonly_candidate_available": true,
  "legal_placement_proof_available_now": false,
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
  "composite_feasibility": "E:\\njust\\keyan\\SRAM Compiler_V2\\OpenRAM-stable\\deliverables\\sram_layoutgen_step45_clean\\docs\\openyield_time_control_composite_feasibility_report.json",
  "leaf_inventory": "E:\\njust\\keyan\\SRAM Compiler_V2\\OpenRAM-stable\\deliverables\\sram_layoutgen_step45_clean\\docs\\openyield_time_control_leaf_inventory_report.json",
  "abstract_payload": "E:\\njust\\keyan\\SRAM Compiler_V2\\OpenRAM-stable\\deliverables\\sram_layoutgen_step45_clean\\docs\\openyield_time_control_abstract_floorplan_payload_report.json",
  "region_refinement": "E:\\njust\\keyan\\SRAM Compiler_V2\\OpenRAM-stable\\deliverables\\sram_layoutgen_step45_clean\\docs\\openyield_time_control_region_refinement_report.json",
  "metadata_closure": "E:\\njust\\keyan\\SRAM Compiler_V2\\OpenRAM-stable\\deliverables\\sram_layoutgen_step45_clean\\docs\\openyield_time_control_metadata_closure_report.json"
}
```

## Subblock To Region Mapping

| subblock | assigned region | fallback | neighbors |
| --- | --- | --- | --- |
| PINV | generated_logic_region | payload_subblock.assigned_region | delay_chain_region, pdrive_region, consumer_handoff_region |
| AND2 | generated_logic_region | payload_subblock.assigned_region | delay_chain_region, pdrive_region, consumer_handoff_region |
| AND3_COMPOSITE | generated_logic_region | payload_subblock.assigned_region | delay_chain_region, pdrive_region, consumer_handoff_region |
| PNAND3_COMPOSITE | precharge_control_region | payload_subblock.assigned_region | pdrive_region, consumer_handoff_region, wordline_enable_control_region |
| PDRIVE | pdrive_region | payload_subblock.assigned_region | generated_logic_region, precharge_control_region, wordline_enable_control_region |
| PDRIVE2_FOR_PRE | precharge_control_region | payload_subblock.assigned_region | pdrive_region, consumer_handoff_region, wordline_enable_control_region |
| WL_PDRIVE | pdrive_region | payload_subblock.assigned_region | generated_logic_region, precharge_control_region, wordline_enable_control_region |
| DELAY_CHAIN | delay_chain_region | payload_subblock.assigned_region | generated_logic_region, sense_write_enable_region |
| WEN_DELAY_CHAIN | sense_write_enable_region | payload_subblock.assigned_region | delay_chain_region, generated_logic_region, consumer_handoff_region |
| PRECHARGE | precharge_control_region | payload_subblock.assigned_region | pdrive_region, consumer_handoff_region, wordline_enable_control_region |
| DFF_ROW | generated_logic_region | payload_subblock.assigned_region | delay_chain_region, pdrive_region, consumer_handoff_region |

## Subblock Fit Audit

| subblock | region | bbox proxy | fit | spacing | channel risk | legal-readonly | physical |
| --- | --- | --- | --- | --- | --- | --- | --- |
| PINV | generated_logic_region | 0.8225 x 1.4800000000000002 | unknown | pass | pass_moderate_margin | True | False |
| AND2 | generated_logic_region | 1.86 x 1.4800000000000002 | unknown | pass | pass_moderate_margin | True | False |
| AND3_COMPOSITE | generated_logic_region | 3.72 x 1.4800000000000002 | unknown | pass | pass_moderate_margin | True | False |
| PNAND3_COMPOSITE | precharge_control_region | 2.8975 x 1.4800000000000002 | unknown | pass | pass_moderate_margin | True | False |
| PDRIVE | pdrive_region | 3.29 x 1.4800000000000002 | unknown | pass | pass_moderate_margin | True | False |
| PDRIVE2_FOR_PRE | precharge_control_region | 1.645 x 1.4800000000000002 | unknown | pass | pass_moderate_margin | True | False |
| WL_PDRIVE | pdrive_region | 1.645 x 1.4800000000000002 | unknown | pass | pass_moderate_margin | True | False |
| DELAY_CHAIN | delay_chain_region | 7.4025 x 2.585 | unknown | pass | pass_moderate_margin | True | False |
| WEN_DELAY_CHAIN | sense_write_enable_region | 4.9350000000000005 x 2.585 | unknown | pass | pass_moderate_margin | True | False |
| PRECHARGE | precharge_control_region | 0.7849999999999999 x 1.4200000000000002 | unknown | pass | pass_moderate_margin | True | False |
| DFF_ROW | generated_logic_region | 2.8599999999999826 x 2.6699999999999835 | unknown | pass | pass_moderate_margin | True | False |

## Region-Level Capacity Audit

| region | subblocks | width margin | height margin | capacity | overlap | risk |
| --- | --- | --- | --- | --- | --- | --- |
| delay_chain_region | DELAY_CHAIN | None | None | unknown | False | pass_moderate_margin |
| pdrive_region | PDRIVE, WL_PDRIVE | None | None | unknown | False | pass_moderate_margin |
| generated_logic_region | PINV, AND2, AND3_COMPOSITE, DFF_ROW | None | None | unknown | False | pass_moderate_margin |
| consumer_handoff_region |  | None | None | unknown | False | pass_moderate_margin |
| precharge_control_region | PNAND3_COMPOSITE, PDRIVE2_FOR_PRE, PRECHARGE | None | None | unknown | False | pass_moderate_margin |
| wordline_enable_control_region |  | None | None | unknown | False | pass_moderate_margin |
| sense_write_enable_region | WEN_DELAY_CHAIN | None | None | unknown | False | pass_moderate_margin |
| dff_row_region |  | None | None | unknown | False | unknown |

## Spacing / Overlap / Channel Pressure Summary

| subblock | spacing | overlap | required ch | reserved ch | margin | risk |
| --- | --- | --- | --- | --- | --- | --- |
| PINV | pass | False | 0.4 | 2.0 | 1.6 | pass_moderate_margin |
| AND2 | pass | False | 0.4 | 2.0 | 1.6 | pass_moderate_margin |
| AND3_COMPOSITE | pass | False | 0.4 | 2.0 | 1.6 | pass_moderate_margin |
| PNAND3_COMPOSITE | pass | False | 0.4 | 2.0 | 1.6 | pass_moderate_margin |
| PDRIVE | pass | False | 0.4 | 2.0 | 1.6 | pass_moderate_margin |
| PDRIVE2_FOR_PRE | pass | False | 0.4 | 2.0 | 1.6 | pass_moderate_margin |
| WL_PDRIVE | pass | False | 0.4 | 2.0 | 1.6 | pass_moderate_margin |
| DELAY_CHAIN | pass | False | 0.4 | 2.0 | 1.6 | pass_moderate_margin |
| WEN_DELAY_CHAIN | pass | False | 0.6 | 2.0 | 1.4 | pass_moderate_margin |
| PRECHARGE | pass | False | 0.4 | 2.0 | 1.6 | pass_moderate_margin |
| DFF_ROW | pass | False | 0.4 | 2.0 | 1.6 | pass_moderate_margin |

## DFF Row Audit

```json
{
  "dff_bbox_known": true,
  "dff_row_count_known": false,
  "dff_row_width_proxy": 2.8599999999999826,
  "dff_row_height_proxy": 2.6699999999999835,
  "row_alignment_available": true,
  "clock_distribution_proven": false,
  "row_spacing_proven": false,
  "safe_for_legal_placement_readonly": true,
  "safe_for_physical_placement": false,
  "blockers": [
    "row placement proof required",
    "no legal placement proof",
    "no routing proof",
    "no standalone integration",
    "region width/height capacity not explicitly known in source reports"
  ]
}
```

## PRECHARGE Exception Audit

```json
{
  "precharge_exception_retained": true,
  "precharge_no_local_gnd_exception": true,
  "precharge_region_fit_pass": {
    "PNAND3_COMPOSITE": "unknown",
    "PDRIVE2_FOR_PRE": "unknown",
    "PRECHARGE": "unknown"
  },
  "precharge_power_side_status": {
    "PNAND3_COMPOSITE": "precharge_exception_metadata_only",
    "PDRIVE2_FOR_PRE": "precharge_exception_metadata_only",
    "PRECHARGE": "precharge_exception_metadata_only"
  },
  "precharge_rail_continuity_proven": false,
  "precharge_safe_for_legal_placement_readonly": true,
  "precharge_safe_for_physical_placement": false,
  "precharge_blocks_physical_gate": true
}
```

## Blockers

- PINV: stdcell physical library not proven
- PINV: no legal routing proof
- PINV: no DRC/LVS proof
- PINV: region width/height capacity not explicitly known in source reports
- AND2: timing proof required
- AND2: routing proof required
- AND2: stdcell physical library not proven
- AND2: no legal routing proof
- AND2: no DRC/LVS proof
- AND2: region width/height capacity not explicitly known in source reports
- AND3_COMPOSITE: timing proof required
- AND3_COMPOSITE: routing proof required
- AND3_COMPOSITE: stdcell physical library not proven
- AND3_COMPOSITE: no legal routing proof
- AND3_COMPOSITE: no DRC/LVS proof
- AND3_COMPOSITE: handoff constraints are metadata-only
- AND3_COMPOSITE: channel reservation rules are not legal routing
- AND3_COMPOSITE: control routing proof is missing
- AND3_COMPOSITE: delay timing proof is missing
- AND3_COMPOSITE: region width/height capacity not explicitly known in source reports
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
- PNAND3_COMPOSITE: region width/height capacity not explicitly known in source reports
- PDRIVE: timing proof required
- PDRIVE: routing proof required
- PDRIVE: no legal placement proof
- PDRIVE: no routing proof
- PDRIVE: region width/height capacity not explicitly known in source reports
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
- PDRIVE2_FOR_PRE: region width/height capacity not explicitly known in source reports
- WL_PDRIVE: timing proof required
- WL_PDRIVE: routing proof required
- WL_PDRIVE: no legal placement proof
- WL_PDRIVE: no routing proof
- WL_PDRIVE: handoff constraints are metadata-only
- WL_PDRIVE: channel reservation rules are not legal routing
- WL_PDRIVE: control routing proof is missing
- WL_PDRIVE: delay timing proof is missing
- WL_PDRIVE: region width/height capacity not explicitly known in source reports
- DELAY_CHAIN: timing proof required
- DELAY_CHAIN: routing proof required
- DELAY_CHAIN: delay timing proof missing
- DELAY_CHAIN: no legal placement proof
- DELAY_CHAIN: no routing proof
- DELAY_CHAIN: region width/height capacity not explicitly known in source reports
- WEN_DELAY_CHAIN: timing proof required
- WEN_DELAY_CHAIN: routing proof required
- WEN_DELAY_CHAIN: wen-delay timing proof missing
- WEN_DELAY_CHAIN: no legal placement proof
- WEN_DELAY_CHAIN: no routing proof
- WEN_DELAY_CHAIN: handoff constraints are metadata-only
- WEN_DELAY_CHAIN: channel reservation rules are not legal routing
- WEN_DELAY_CHAIN: control routing proof is missing
- WEN_DELAY_CHAIN: delay timing proof is missing
- WEN_DELAY_CHAIN: region width/height capacity not explicitly known in source reports
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
- PRECHARGE: region width/height capacity not explicitly known in source reports
- DFF_ROW: row placement proof required
- DFF_ROW: no legal placement proof
- DFF_ROW: no routing proof
- DFF_ROW: no standalone integration
- DFF_ROW: region width/height capacity not explicitly known in source reports
- delay_chain_region: region width/height capacity not explicitly known
- pdrive_region: region width/height capacity not explicitly known
- generated_logic_region: region width/height capacity not explicitly known
- consumer_handoff_region: region width/height capacity not explicitly known
- precharge_control_region: region width/height capacity not explicitly known
- wordline_enable_control_region: region width/height capacity not explicitly known
- sense_write_enable_region: region width/height capacity not explicitly known
- dff_row_region: region width/height capacity not explicitly known

## Boundary Assertions

```json
{
  "bbox_proxy_is_not_legal_placement": true,
  "region_fit_is_not_drc_proof": true,
  "channel_margin_is_not_routing_proof": true,
  "no_local_gnd_exception_is_not_rail_continuity_proof": true,
  "standalone_modified": false,
  "routing_modified": false,
  "gds_writer_modified": false
}
```