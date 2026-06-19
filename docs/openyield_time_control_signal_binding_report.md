# OpenYield TIME Control Signal Binding Report

This is a read-only signal-level binding contract audit. It does not modify placement, routing, standalone.py, or the GDS writer.

## Audit Summary

```json
{
  "time_control_signal_binding_available": true,
  "time_as_single_macro_allowed": false,
  "control_signal_binding_consistent": true,
  "all_core_control_signals_have_binding_contract": true,
  "partial_or_conditional_bindings_present": true,
  "can_enter_time_control_signal_metadata_planning": true,
  "can_enter_time_control_physical_placement": false,
  "can_enter_standalone_control_placement": false
}
```

## Signal Binding Contracts

| contract | signal | producer | dependency | consumers | active level | conditional | metadata planning | physical placement |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| CLK_BUF_BINDING_CONTRACT | clk_buf | PDRIVE | clk -> PDRIVE -> clk_buf | ADDR_DFF, DATA_DFF, DFF_BUF, clk_bar inverter, gated clock logic | clock_buffered | always | True | False |
| CLK_BAR_BINDING_CONTRACT | clk_bar | Pinv | clk_buf -> Pinv -> clk_bar | gated clock logic | inverted_clk_buf | always | True | False |
| GATED_CLK_BUF_BINDING_CONTRACT | gated_clk_buf | AND2 | cs + clk_buf -> AND2 -> gated_clk_buf | precharge control logic | high_when_cs_and_clk_buf_high | always | True | False |
| GATED_CLK_BAR_BINDING_CONTRACT | gated_clk_bar | AND2 | cs + clk_bar -> AND2 -> gated_clk_bar | WL_PDRIVE, WRITE_ENABLE path, SENSE_ENABLE path | high_when_cs_and_clk_bar_high | always | True | False |
| RBL_DELAY_BINDING_CONTRACT | rbl_delay | DELAY_CHAIN | rbl -> DELAY_CHAIN -> rbl_delay | Pinv, SENSE_ENABLE path, PRECHARGE path | replica_delay_domain | always | True | False |
| RBL_DELAY_BAR_BINDING_CONTRACT | rbl_delay_bar | Pinv | rbl_delay -> Pinv -> rbl_delay_bar | WRITE_ENABLE path, WEN_DELAY_CHAIN conditional path | inverted_replica_delay_domain | always | True | False |
| WORDLINE_ENABLE_BINDING_CONTRACT | wl_en | WL_PDRIVE | gated_clk_bar -> WL_PDRIVE -> wl_en; wl_en -> Pinv -> wl_en_bar | WORDLINEDRIVER, PRECHARGE path, Replica RWL AND2 | active_high | always | True | False |
| WRITE_ENABLE_BINDING_CONTRACT | w_en | AND3 | rbl_delay_bar + gated_clk_bar + we -> AND3 -> w_en | WRITEDRIVER | active_high | always, with conditional alternate first input in special WEN path | True | False |
| SENSE_ENABLE_BINDING_CONTRACT | s_en | AND3 | rbl_delay + gated_clk_bar + we_bar -> AND3 -> s_en | SENSEAMP | active_high | always | True | False |
| PRECHARGE_ENB_BINDING_CONTRACT | PRE | PNAND3 + PDRIVE2_FOR_PRE | gated_clk_buf + rbl_delay + wl_en_bar -> PNAND3 -> PRE_UNBUF; PRE_UNBUF -> PDRIVE2_FOR_PRE -> PRE | PRECHARGE | active_low | always | True | False |
| WEN_DELAY_CONDITIONAL_BINDING_CONTRACT | rbl_delay_bar_wen | WEN_DELAY_CHAIN | rbl_delay_bar -> WEN_DELAY_CHAIN -> rbl_delay_bar_wen -> w_en path | WRITE_ENABLE path | conditional_write_timing_domain | operation == write and num_rows == 16 and num_cols == 512 | True | False |

## Polarity / Consumer Consistency

| check | value |
| --- | --- |
| wordline_enable_active_high_consistent | True |
| write_enable_consumer_consistent | True |
| sense_enable_consumer_consistent | True |
| precharge_enb_active_low_consistent | True |
| clk_bar_inversion_consistent | True |
| gated_clock_dependency_consistent | True |

## Dependency Graph

| source | via | target | confirmed | metadata_only | physical_routing_proven |
| --- | --- | --- | --- | --- | --- |
| clk | PDRIVE | clk_buf | True | True | False |
| clk_buf | Pinv | clk_bar | True | True | False |
| clk_buf + cs | AND2 | gated_clk_buf | True | True | False |
| clk_bar + cs | AND2 | gated_clk_bar | True | True | False |
| gated_clk_bar | WL_PDRIVE | wl_en | True | True | False |
| wl_en | Pinv | wl_en_bar | True | True | False |
| rbl | DELAY_CHAIN | rbl_delay | True | True | False |
| rbl_delay | Pinv | rbl_delay_bar | True | True | False |
| rbl_delay_bar + gated_clk_bar + we | AND3 | w_en | True | True | False |
| rbl_delay + gated_clk_bar + we_bar | AND3 | s_en | True | True | False |
| gated_clk_buf + rbl_delay + wl_en_bar | PNAND3 | PRE_UNBUF | True | True | False |
| PRE_UNBUF | PDRIVE2_FOR_PRE | PRE | True | True | False |

## Unresolved Items

- TIME still decomposed, not a macro.
- delay / pdrive chains still require generated layout or stdcell-row realization.
- timing proof missing for delay_chain and wen_delay_chain.
- routing proof missing for all control signals.
- control-row physical placement proof missing.
- rail continuity proof missing.
- gen_nand4 remains partial / not physical-ready.

## Step 6.25 Recommendation

```json
{
  "recommended_next_phase": "time_control_generated_logic_contract_packaging",
  "candidate_directions": [
    "and2_and3_metadata_contract_packaging",
    "wl_enable_precharge_enable_consumer_binding",
    "write_enable_sense_enable_consumer_binding",
    "conditional_wen_delay_policy_capture"
  ],
  "reason": [
    "The signal graph and polarity semantics are now source-confirmed.",
    "The next bottleneck is packaging generated-logic contracts cleanly for future planning, not physical placement.",
    "Control placement and routing remain blocked, so the best next move is contract-level normalization."
  ]
}
```

## Entry Decisions

- can_enter_time_control_signal_metadata_planning: `True`
- can_enter_time_control_physical_placement: `False`
- can_enter_standalone_control_placement: `False`

