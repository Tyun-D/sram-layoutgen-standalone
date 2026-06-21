# OpenYield TIME Control Leaf Inventory

This report inventories leaf macro geometry, pin-side metadata, and power-side evidence for later readonly feasibility work. It is not placement proof, routing proof, or physical-ready signoff.

## Audit Summary

```json
{
  "time_control_leaf_bbox_pin_side_inventory_available": true,
  "all_required_leaf_gds_found": true,
  "all_recommended_leaf_variants_selected": true,
  "all_required_leaf_bbox_known": true,
  "all_required_leaf_pin_sides_known": false,
  "all_required_leaf_power_sides_known_or_exception_recorded": true,
  "precharge_exception_retained": true,
  "all_subblocks_have_leaf_inventory": true,
  "composite_readiness_classified": true,
  "can_enter_composite_internal_placement_feasibility_audit": true,
  "can_enter_legal_placement_readonly_audit": true,
  "can_enter_physical_placement_now": false,
  "can_generate_time_control_gds_now": false,
  "can_modify_standalone_now": false
}
```

## Input Reports And Assets

```json
{
  "asset_inventory": "E:\\njust\\keyan\\SRAM Compiler_V2\\OpenRAM-stable\\deliverables\\sram_layoutgen_step45_clean\\docs\\openyield_repo_physical_asset_inventory_report.json",
  "power_rail_audit": "E:\\njust\\keyan\\SRAM Compiler_V2\\OpenRAM-stable\\deliverables\\sram_layoutgen_step45_clean\\docs\\openyield_hardcell_power_rail_continuity_report.json",
  "generated_logic_report": "E:\\njust\\keyan\\SRAM Compiler_V2\\OpenRAM-stable\\deliverables\\sram_layoutgen_step45_clean\\docs\\openyield_time_control_generated_logic_contract_report.json",
  "abstract_payload_report": "E:\\njust\\keyan\\SRAM Compiler_V2\\OpenRAM-stable\\deliverables\\sram_layoutgen_step45_clean\\docs\\openyield_time_control_abstract_floorplan_payload_report.json",
  "region_refinement_report": "E:\\njust\\keyan\\SRAM Compiler_V2\\OpenRAM-stable\\deliverables\\sram_layoutgen_step45_clean\\docs\\openyield_time_control_region_refinement_report.json"
}
```

## Leaf GDS BBox / Pin Side Inventory

| macro | variant | bbox | input sides | output sides | control sides | vdd | gnd | legal-readonly | physical |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| gen_inv | openram_replacements | (-0.08,-0.08)-(0.7425,1.4) | {"A": "left"} | {"Z": "right"} | {} | top | bottom | True | False |
| gen_nand2 | openram_replacements | (-0.08,-0.08)-(0.9575,1.4) | {"A": "left", "B": "internal"} | {"Z": "internal"} | {} | top | bottom | True | False |
| gen_delay_inv | openram_replacements | (-0.08,-0.08)-(0.7425,2.505) | {"A": "left"} | {"Z": "right"} | {} | top | bottom | True | False |
| gen_precharge | openram_replacements | (-0.08,-0.08)-(0.705,1.34) | {} | {} | {"en_bar": "bottom"} | top | unknown | True | False |
| dff | default_gds_lib | (0,-0.1)-(2.86,2.57) | {"D": "left"} | {"Q": "right"} | {} | top | bottom | True | False |
| gen_inv | default_gds_lib | (0,0)-(1.2,1.565) | {} | {} | {} | top | bottom | False | False |
| gen_nand2 | default_gds_lib | (0,0)-(1.65,1.565) | {} | {} | {} | top | bottom | False | False |
| gen_delay_inv | default_gds_lib | (0,0)-(1.2,1.565) | {} | {} | {} | left | bottom | False | False |
| gen_precharge | default_gds_lib | (0,0)-(0.895,1.565) | {} | {} | {} | left | unknown | False | False |
| sense_amp | default_gds_lib | (-0.035,0)-(0.74,6.01) | {} | {"dout": "left"} | {} | left | right | True | False |
| write_driver | default_gds_lib | (-0.1,0)-(0.74,4.175) | {} | {} | {} | left | left | True | False |
| gen_wl_driver | openram_replacements | (-0.08,-0.105)-(2.965,1.4) | {"A": "left"} | {"Z": "top"} | {"B": "left"} | top | bottom | True | False |
| gen_col_mux_vdd_labeled | openyield_repaired | (-0.08,-0.08)-(0.7375,1.8) | {} | {} | {} | top | right | True | False |
| cell_1rw | default_gds_lib | (-0.095,-0.1)-(0.8,1.465) | {} | {"Q": "left", "Q_bar": "right"} | {} | top | bottom | True | True |
| dummy_cell_1rw | default_gds_lib | (-0.095,-0.1)-(0.8,1.465) | {} | {} | {} | top | bottom | True | True |
| replica_cell_1rw | default_gds_lib | (-0.095,-0.1)-(0.8,1.465) | {} | {} | {} | top | bottom | True | True |

## Power Side Summary

```json
{
  "storage_reference_cells": [
    {
      "macro_name": "cell_1rw",
      "vdd_side": "top",
      "gnd_side": "bottom",
      "policy": "top_vdd_bottom_gnd"
    },
    {
      "macro_name": "dummy_cell_1rw",
      "vdd_side": "top",
      "gnd_side": "bottom",
      "policy": "top_vdd_bottom_gnd"
    },
    {
      "macro_name": "replica_cell_1rw",
      "vdd_side": "top",
      "gnd_side": "bottom",
      "policy": "top_vdd_bottom_gnd"
    }
  ],
  "generated_logic_leaves": [
    {
      "macro_name": "gen_inv",
      "variant_name": "openram_replacements",
      "vdd_side": "top",
      "gnd_side": "bottom",
      "quality": "explicit_vdd_gnd"
    },
    {
      "macro_name": "gen_nand2",
      "variant_name": "openram_replacements",
      "vdd_side": "top",
      "gnd_side": "bottom",
      "quality": "explicit_vdd_gnd"
    },
    {
      "macro_name": "gen_delay_inv",
      "variant_name": "openram_replacements",
      "vdd_side": "top",
      "gnd_side": "bottom",
      "quality": "explicit_vdd_gnd"
    },
    {
      "macro_name": "gen_precharge",
      "variant_name": "openram_replacements",
      "vdd_side": "top",
      "gnd_side": "unknown",
      "quality": "vdd_only_exception"
    },
    {
      "macro_name": "dff",
      "variant_name": "default_gds_lib",
      "vdd_side": "top",
      "gnd_side": "bottom",
      "quality": "explicit_vdd_gnd"
    },
    {
      "macro_name": "gen_inv",
      "variant_name": "default_gds_lib",
      "vdd_side": "top",
      "gnd_side": "bottom",
      "quality": "explicit_vdd_gnd"
    },
    {
      "macro_name": "gen_nand2",
      "variant_name": "default_gds_lib",
      "vdd_side": "top",
      "gnd_side": "bottom",
      "quality": "explicit_vdd_gnd"
    },
    {
      "macro_name": "gen_delay_inv",
      "variant_name": "default_gds_lib",
      "vdd_side": "left",
      "gnd_side": "bottom",
      "quality": "explicit_vdd_gnd"
    },
    {
      "macro_name": "gen_precharge",
      "variant_name": "default_gds_lib",
      "vdd_side": "left",
      "gnd_side": "unknown",
      "quality": "vdd_only_exception"
    }
  ],
  "consumer_hard_macros": [
    {
      "macro_name": "sense_amp",
      "variant_name": "default_gds_lib",
      "vdd_side": "left",
      "gnd_side": "right",
      "quality": "explicit_vdd_gnd"
    },
    {
      "macro_name": "write_driver",
      "variant_name": "default_gds_lib",
      "vdd_side": "left",
      "gnd_side": "left",
      "quality": "explicit_vdd_gnd"
    },
    {
      "macro_name": "gen_wl_driver",
      "variant_name": "openram_replacements",
      "vdd_side": "top",
      "gnd_side": "bottom",
      "quality": "explicit_vdd_gnd"
    },
    {
      "macro_name": "gen_col_mux_vdd_labeled",
      "variant_name": "openyield_repaired",
      "vdd_side": "top",
      "gnd_side": "right",
      "quality": "explicit_vdd_gnd"
    }
  ]
}
```

## Subblock To Leaf Mapping

| subblock | leafs | bbox inputs | pin sides | power sides | legal-readonly | blockers |
| --- | --- | --- | --- | --- | --- | --- |
| PINV | gen_inv | True | True | True | True |  |
| AND2 | gen_nand2, gen_inv | True | True | True | True | timing proof required; routing proof required |
| AND3_COMPOSITE | gen_nand2, gen_inv | True | True | True | True | timing proof required; routing proof required |
| PNAND3_COMPOSITE | gen_nand2, gen_inv | True | True | True | True | timing proof required; routing proof required |
| PDRIVE | gen_inv | True | True | True | True | timing proof required; routing proof required; no legal placement proof; no routing proof |
| PDRIVE2_FOR_PRE | gen_inv, gen_precharge | True | True | True | True | timing proof required; routing proof required |
| WL_PDRIVE | gen_inv | True | True | True | True | timing proof required; routing proof required |
| DELAY_CHAIN | gen_delay_inv, gen_inv | True | True | True | True | timing proof required; routing proof required; delay timing proof missing; no legal placement proof; no routing proof |
| WEN_DELAY_CHAIN | gen_delay_inv, gen_inv | True | True | True | True | timing proof required; routing proof required; wen-delay timing proof missing; no legal placement proof; no routing proof |
| PRECHARGE | gen_precharge | True | True | True | True | blocked by precharge power exception; rail continuity proof missing; no legal routing proof; no physical placement proof; PRECHARGE adapter metadata may remain partial; PRECHARGE power-domain closure may remain incomplete; handoff constraints are metadata-only; channel reservation rules are not legal routing; control routing proof is missing; rail continuity proof is missing |
| DFF_ROW | dff | True | True | True | True | row placement proof required; no legal placement proof; no routing proof; no standalone integration |

## Composite Readiness Classification

| subblock | classification | legal-readonly | physical | blockers |
| --- | --- | --- | --- | --- |
| AND2 | blocked_by_timing_requirement | True | False | timing proof required; routing proof required |
| AND3_COMPOSITE | blocked_by_timing_requirement | True | False | timing proof required; routing proof required |
| PNAND3_COMPOSITE | blocked_by_timing_requirement | True | False | timing proof required; routing proof required |
| PDRIVE | blocked_by_timing_requirement | True | False | timing proof required; routing proof required; no legal placement proof; no routing proof |
| PDRIVE2_FOR_PRE | blocked_by_timing_requirement | True | False | timing proof required; routing proof required |
| WL_PDRIVE | blocked_by_timing_requirement | True | False | timing proof required; routing proof required |
| DELAY_CHAIN | blocked_by_timing_requirement | True | False | timing proof required; routing proof required; delay timing proof missing; no legal placement proof; no routing proof |
| WEN_DELAY_CHAIN | blocked_by_timing_requirement | True | False | timing proof required; routing proof required; wen-delay timing proof missing; no legal placement proof; no routing proof |

## PRECHARGE Special Section

```json
{
  "precharge_leaf_bbox_known": true,
  "precharge_en_pin_side_known": true,
  "precharge_vdd_side_known": true,
  "precharge_gnd_side_known": false,
  "precharge_no_local_gnd_exception": true,
  "precharge_safe_for_legal_placement_readonly": true,
  "precharge_safe_for_physical_placement": false,
  "precharge_blocker_for_physical_gate": "no local GND proof and no across-abutment rail continuity proof"
}
```

## Blockers

- gen_inv:default_gds_lib is not ready for legal-placement readonly planning.
- gen_nand2:default_gds_lib is not ready for legal-placement readonly planning.
- gen_delay_inv:default_gds_lib is not ready for legal-placement readonly planning.
- gen_precharge:default_gds_lib is not ready for legal-placement readonly planning.
- AND2: timing proof required
- AND2: routing proof required
- AND3_COMPOSITE: timing proof required
- AND3_COMPOSITE: routing proof required
- PNAND3_COMPOSITE: timing proof required
- PNAND3_COMPOSITE: routing proof required
- PDRIVE: timing proof required
- PDRIVE: routing proof required
- PDRIVE: no legal placement proof
- PDRIVE: no routing proof
- PDRIVE2_FOR_PRE: timing proof required
- PDRIVE2_FOR_PRE: routing proof required
- WL_PDRIVE: timing proof required
- WL_PDRIVE: routing proof required
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
- DFF_ROW: row placement proof required
- DFF_ROW: no legal placement proof
- DFF_ROW: no routing proof
- DFF_ROW: no standalone integration

## Boundary Assertions

```json
{
  "can_enter_physical_placement_now": false,
  "can_generate_time_control_gds_now": false,
  "can_modify_standalone_now": false,
  "standalone_modified": false,
  "routing_modified": false,
  "gds_writer_modified": false
}
```