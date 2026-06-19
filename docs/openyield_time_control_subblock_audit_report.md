# OpenYield TIME Control Subblock Audit Report

This is a read-only source / contract / candidate-macro audit for the remaining TIME control subblocks. It does not modify placement, routing, standalone.py, or the GDS writer.

## Audit Summary

```json
{
  "remaining_control_subblocks_without_adapter_level_physical_closure": [
    "DELAY_CHAIN",
    "WEN_DELAY_CHAIN",
    "PDRIVE",
    "PDRIVE2_FOR_PRE",
    "WL_PDRIVE"
  ],
  "subblocks_safe_for_metadata_planning": [
    "DELAY_CHAIN",
    "WEN_DELAY_CHAIN",
    "PDRIVE",
    "PDRIVE2_FOR_PRE",
    "WL_PDRIVE"
  ],
  "subblocks_safe_for_physical_placement": [],
  "time_control_subblock_audit_available": true,
  "time_as_single_macro_allowed": false,
  "can_enter_time_control_subblock_metadata_planning": true,
  "can_enter_time_control_physical_placement": false,
  "can_enter_standalone_control_placement": false
}
```

## Remaining TIME Subblocks

| subblock | OpenYield source | inputs | outputs | role | mapping | metadata planning | physical placement | source confirmed |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| DELAY_CHAIN | delay_chain | rbl | rbl_delay | replica-delay based timing generation | partial_generated_chain_candidate | True | False | True |
| WEN_DELAY_CHAIN | wen_delay_chain | rbl_delay_bar | rbl_delay_bar_wen | write-enable timing generation | partial_generated_chain_candidate | True | False | True |
| PDRIVE | pdrive | clk | clk_buf | clock buffer / pulse driver chain | partial_generated_chain_candidate | True | False | True |
| PDRIVE2_FOR_PRE | pdrive2_for_pre | PRE_UNBUF | PRE | precharge control driver | partial_generated_chain_candidate | True | False | True |
| WL_PDRIVE | wl_pdrive | gated_clk_bar | wl_en | wordline enable pulse driver | partial_generated_chain_candidate | True | False | True |

## Local Candidate Macro / Generated Cell Audit

| candidate | GDS | SPICE | pin metadata | power metadata | metadata planning | physical placement |
| --- | --- | --- | --- | --- | --- | --- |
| gen_delay_inv | True | False | True | True | True | False |
| gen_inv | True | False | True | True | True | False |
| gen_nand2 | True | False | True | True | True | False |
| gen_nand4 | True | False | True | False | partial | False |
| dff | True | True | True | True | True | False |

## Control Signal Dependency Graph

| source | via | target | confirmed |
| --- | --- | --- | --- |
| clk | PDRIVE | clk_buf | True |
| clk_buf | Pinv | clk_bar | True |
| cs + clk_bar | AND2 | gated_clk_bar | True |
| cs + clk_buf | AND2 | gated_clk_buf | True |
| gated_clk_bar | WL_PDRIVE | wordline_enable / wl_en | True |
| rbl | DELAY_CHAIN | rbl_delay | True |
| rbl_delay | Pinv | rbl_delay_bar | True |
| rbl_delay_bar + gated_clk_bar + we | AND3 | write_enable / w_en | True |
| rbl_delay + gated_clk_bar + we_bar | AND3 | sense_enable / s_en | True |
| gated_clk_buf + rbl_delay + wl_en_bar | PNAND3 | PRE_UNBUF | True |
| PRE_UNBUF | PDRIVE2_FOR_PRE | precharge_enb / PRE | True |

## Unresolved Items

- TIME must remain decomposed; treating TIME as one macro is not allowed.
- delay_chain / wen_delay_chain / pdrive / pdrive2_for_pre / wl_pdrive still require generated layout or stdcell-row realization.
- gen_nand4 exists as GDS candidate but current pin metadata is incomplete.
- Physical timing proof, routing proof, and control-row placement proof are all still missing.
- This audit closes semantic planning only; it does not allow physical control placement or standalone control placement.

## Step 6.24 Recommendation

```json
{
  "recommended_next_phase": "time_control_signal_binding_contracts",
  "candidate_directions": [
    "delay_chain_binding_contracts",
    "wen_delay_chain_binding_contracts",
    "precharge_control_contracts",
    "wordline_enable_control_contracts",
    "sense_write_enable_signal_binding"
  ],
  "reason": [
    "Source-level semantics are now sufficient for metadata planning.",
    "Physical control placement is still blocked, so the next useful step is binding contracts rather than placement.",
    "The remaining uncertainty is at signal-binding and generated-logic contract level, not decoder metadata level."
  ]
}
```

## Entry Decisions

- can_enter_time_control_subblock_metadata_planning: `True`
- can_enter_time_control_physical_placement: `False`
- can_enter_standalone_control_placement: `False`

