# OpenYield TIME Generated Logic Contract Report

This is a metadata-only packaging audit for TIME generated logic. It does not modify placement, routing, standalone.py, or the GDS writer.

## Audit Summary

```json
{
  "time_control_generated_logic_contract_available": true,
  "generated_logic_contract_packaging_available": true,
  "all_core_logic_roles_have_contract": true,
  "all_signal_bindings_have_generated_logic_contract": true,
  "generated_logic_contract_coverage_complete": true,
  "partial_generated_logic_contracts_present": true,
  "can_enter_time_control_generated_logic_metadata_planning": true,
  "can_enter_time_control_physical_placement": false,
  "can_enter_standalone_control_placement": false
}
```

## Generated Logic Contract List

| contract | logic role | source symbol | used by signal bindings | candidate cells | mapping | metadata planning | physical placement |
| --- | --- | --- | --- | --- | --- | --- | --- |
| PINV_GENERATED_LOGIC_CONTRACT | inverter | Pinv | CLK_BAR_BINDING_CONTRACT, RBL_DELAY_BAR_BINDING_CONTRACT, WORDLINE_ENABLE_BINDING_CONTRACT | gen_inv | direct_metadata_inverter | True | False |
| AND2_GENERATED_LOGIC_CONTRACT | and2_composite | AND2 | GATED_CLK_BUF_BINDING_CONTRACT, GATED_CLK_BAR_BINDING_CONTRACT | gen_nand2, gen_inv | metadata_composite_and2 | True | False |
| AND3_COMPOSITE_GENERATED_LOGIC_CONTRACT | and3_composite | AND3 | WRITE_ENABLE_BINDING_CONTRACT, SENSE_ENABLE_BINDING_CONTRACT | gen_nand2, gen_inv | metadata_composite_and3 | True | False |
| PNAND3_COMPOSITE_GENERATED_LOGIC_CONTRACT | pnand3_composite | PNAND3 | PRECHARGE_ENB_BINDING_CONTRACT | gen_nand2, gen_inv | metadata_composite_pnand3 | True | False |
| PDRIVE_CHAIN_GENERATED_LOGIC_CONTRACT | buffer_chain | PDRIVE | CLK_BUF_BINDING_CONTRACT | gen_inv | generated_buffer_chain | True | False |
| PDRIVE2_FOR_PRE_CHAIN_GENERATED_LOGIC_CONTRACT | buffer_chain | PDRIVE2_FOR_PRE | PRECHARGE_ENB_BINDING_CONTRACT | gen_inv | generated_precharge_buffer_chain | True | False |
| WL_PDRIVE_CHAIN_GENERATED_LOGIC_CONTRACT | buffer_chain | WL_PDRIVE | WORDLINE_ENABLE_BINDING_CONTRACT | gen_inv | generated_wordline_enable_buffer_chain | True | False |
| DELAY_CHAIN_GENERATED_LOGIC_CONTRACT | delay_chain | DELAY_CHAIN | RBL_DELAY_BINDING_CONTRACT | gen_delay_inv, gen_inv | generated_delay_chain | True | False |
| WEN_DELAY_CHAIN_CONDITIONAL_GENERATED_LOGIC_CONTRACT | conditional_delay_chain | WEN_DELAY_CHAIN | WEN_DELAY_CONDITIONAL_BINDING_CONTRACT | gen_delay_inv, gen_inv | conditional_generated_delay_chain | True | False |

## Candidate Cell Audit

| candidate | GDS | SPICE | pin metadata | power metadata | used by contracts | metadata planning | physical placement |
| --- | --- | --- | --- | --- | --- | --- | --- |
| gen_delay_inv | True | False | True | True | DELAY_CHAIN_GENERATED_LOGIC_CONTRACT, WEN_DELAY_CHAIN_CONDITIONAL_GENERATED_LOGIC_CONTRACT | True | False |
| gen_inv | True | False | True | True | PINV_GENERATED_LOGIC_CONTRACT, AND2_GENERATED_LOGIC_CONTRACT, AND3_COMPOSITE_GENERATED_LOGIC_CONTRACT, PNAND3_COMPOSITE_GENERATED_LOGIC_CONTRACT, PDRIVE_CHAIN_GENERATED_LOGIC_CONTRACT, PDRIVE2_FOR_PRE_CHAIN_GENERATED_LOGIC_CONTRACT, WL_PDRIVE_CHAIN_GENERATED_LOGIC_CONTRACT, DELAY_CHAIN_GENERATED_LOGIC_CONTRACT, WEN_DELAY_CHAIN_CONDITIONAL_GENERATED_LOGIC_CONTRACT | True | False |
| gen_nand2 | True | False | True | True | AND2_GENERATED_LOGIC_CONTRACT, AND3_COMPOSITE_GENERATED_LOGIC_CONTRACT, PNAND3_COMPOSITE_GENERATED_LOGIC_CONTRACT | True | False |
| gen_nand4 | True | False | True | False |  | partial | False |
| dff | True | True | True | True |  | True | False |

## Contract-to-Signal Coverage

| signal binding contract | generated logic contracts | covered |
| --- | --- | --- |
| CLK_BUF_BINDING_CONTRACT | PDRIVE_CHAIN_GENERATED_LOGIC_CONTRACT | True |
| CLK_BAR_BINDING_CONTRACT | PINV_GENERATED_LOGIC_CONTRACT | True |
| GATED_CLK_BUF_BINDING_CONTRACT | AND2_GENERATED_LOGIC_CONTRACT | True |
| GATED_CLK_BAR_BINDING_CONTRACT | AND2_GENERATED_LOGIC_CONTRACT | True |
| RBL_DELAY_BINDING_CONTRACT | DELAY_CHAIN_GENERATED_LOGIC_CONTRACT | True |
| RBL_DELAY_BAR_BINDING_CONTRACT | PINV_GENERATED_LOGIC_CONTRACT | True |
| WORDLINE_ENABLE_BINDING_CONTRACT | WL_PDRIVE_CHAIN_GENERATED_LOGIC_CONTRACT, PINV_GENERATED_LOGIC_CONTRACT | True |
| WRITE_ENABLE_BINDING_CONTRACT | AND3_COMPOSITE_GENERATED_LOGIC_CONTRACT | True |
| SENSE_ENABLE_BINDING_CONTRACT | AND3_COMPOSITE_GENERATED_LOGIC_CONTRACT | True |
| PRECHARGE_ENB_BINDING_CONTRACT | PNAND3_COMPOSITE_GENERATED_LOGIC_CONTRACT, PDRIVE2_FOR_PRE_CHAIN_GENERATED_LOGIC_CONTRACT | True |
| WEN_DELAY_CONDITIONAL_BINDING_CONTRACT | WEN_DELAY_CHAIN_CONDITIONAL_GENERATED_LOGIC_CONTRACT | True |

## Consistency Checks

| check | value |
| --- | --- |
| time_as_single_macro_allowed | False |
| generated_logic_contract_packaging_available | True |
| all_core_logic_roles_have_contract | True |
| all_signal_bindings_have_generated_logic_contract | True |
| and3_composite_reuses_decoder_convention | True |
| pnand3_composite_reuses_decoder_convention | True |
| buffer_chain_contracts_available | True |
| delay_chain_contracts_available | True |
| conditional_wen_delay_policy_captured | True |
| control_signal_polarity_preserved | True |
| control_signal_consumer_binding_preserved | True |
| safe_for_metadata_planning | True |
| safe_for_physical_placement | False |

## Unresolved Items

- generated logic contracts are metadata-only
- chain stage placement is not legalized
- delay timing proof is missing
- wen-delay conditional timing proof is missing
- composite internal routing is not proven
- rail continuity is not proven
- control-row physical placement is not proven
- gen_nand4 remains partial
- no DRC/LVS proof exists
- standalone integration is not allowed yet

## Step 6.26 Recommendation

```json
{
  "recommended_next_phase": "time_control_consumer_side_contract_normalization",
  "candidate_directions": [
    "write_enable_consumer_contract_normalization",
    "sense_enable_consumer_contract_normalization",
    "precharge_enb_consumer_contract_normalization",
    "wordline_enable_consumer_contract_normalization"
  ],
  "reason": [
    "Generated-logic packaging is now available and covers every current TIME signal binding.",
    "The next useful step is consumer-side contract normalization, not physical placement.",
    "Control-row placement, routing, and signoff proofs remain blocked."
  ]
}
```

## Entry Decisions

- can_enter_time_control_generated_logic_metadata_planning: `True`
- can_enter_time_control_physical_placement: `False`
- can_enter_standalone_control_placement: `False`

