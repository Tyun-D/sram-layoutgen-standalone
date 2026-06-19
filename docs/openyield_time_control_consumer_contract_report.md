# OpenYield TIME Control Consumer Contract Report

This is a metadata-only consumer-side normalization audit. It does not modify placement, routing, standalone.py, or the GDS writer.

## Audit Summary

```json
{
  "time_control_consumer_contract_available": true,
  "consumer_contract_normalization_available": true,
  "all_primary_control_consumers_have_contract": true,
  "control_signal_aliases_normalized": true,
  "control_signal_polarity_consistent": true,
  "consumer_pin_binding_consistent": true,
  "precharge_enb_consumer_contract_status": "source_level_metadata_only",
  "can_enter_time_control_consumer_metadata_planning": true,
  "can_enter_time_control_physical_placement": false,
  "can_enter_standalone_control_placement": false
}
```

## Consumer-Side Contract List

| contract | control signal | consumer macro | consumer pin | expected active level | fanout count | metadata planning | physical placement | status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| WRITE_ENABLE_CONSUMER_CONTRACT | write_enable | WRITEDRIVER | EN | active_high | 1 | True | False | normalized_metadata_contract |
| SENSE_ENABLE_CONSUMER_CONTRACT | sense_enable | SENSEAMP | EN | active_high | 1 | True | False | normalized_metadata_contract |
| PRECHARGE_ENB_CONSUMER_CONTRACT | precharge_enb | PRECHARGE | ENB | active_low | 1 | partial | False | source_level_metadata_only |
| WORDLINE_ENABLE_CONSUMER_CONTRACT | wordline_enable | WORDLINEDRIVER | B | active_high | 3 | True | False | normalized_metadata_contract |

## Alias Normalization

| alias | canonical signal | consumer endpoint | local consumer pin |
| --- | --- | --- | --- |
| w_en | write_enable | WRITEDRIVER.EN | en |
| write_enable | write_enable | WRITEDRIVER.EN | en |
| s_en | sense_enable | SENSEAMP.EN | en |
| sense_enable | sense_enable | SENSEAMP.EN | en |
| PRE | precharge_enb | PRECHARGE.ENB | EN |
| precharge_enb | precharge_enb | PRECHARGE.ENB | EN |
| wl_en | wordline_enable | WORDLINEDRIVER.B | B |
| wordline_enable | wordline_enable | WORDLINEDRIVER.B | B |
| wl_en_bar | inverted_wordline_enable | PRECHARGE.PNAND3.C | None |

## Fanout Audit

| control signal | fanout targets | fanout count | multi consumer | physical_routing_proven |
| --- | --- | --- | --- | --- |
| write_enable | WRITEDRIVER.EN | 1 | False | False |
| sense_enable | SENSEAMP.EN | 1 | False | False |
| precharge_enb | PRECHARGE.ENB | 1 | False | False |
| wordline_enable | WORDLINEDRIVER.B, Pinv.A(wl_en_bar), RWL_AND2.B | 3 | True | False |
| wl_en_bar | PRECHARGE.PNAND3.C | 1 | False | False |

## Consumer Pin Metadata Audit

| consumer macro | consumer pin | pin known | pin side known | power domain known | metadata planning | physical placement |
| --- | --- | --- | --- | --- | --- | --- |
| WRITEDRIVER | EN | True | True | True | True | False |
| SENSEAMP | EN | True | True | True | True | False |
| PRECHARGE | ENB | True | True | partial | partial | False |
| WORDLINEDRIVER | B | True | True | True | True | False |

## Consistency Checks

| check | value |
| --- | --- |
| consumer_contract_normalization_available | True |
| all_primary_control_consumers_have_contract | True |
| write_enable_consumer_contract_available | True |
| sense_enable_consumer_contract_available | True |
| precharge_enb_consumer_contract_available | True |
| wordline_enable_consumer_contract_available | True |
| write_enable_consumer_consistent | True |
| writedriver_enable_pin_known | True |
| writedriver_enable_active_high | True |
| sense_enable_consumer_consistent | True |
| senseamp_enable_pin_known | True |
| senseamp_enable_active_high | True |
| precharge_enb_consumer_consistent | True |
| precharge_enable_pin_known | True |
| precharge_enable_active_low | True |
| precharge_consumer_adapter_available | False |
| wordline_enable_consumer_consistent | True |
| wordlinedriver_B_pin_known | True |
| wordlinedriver_B_active_high | True |
| wl_en_bar_secondary_path_preserved | True |
| conditional_wen_delay_policy_preserved | True |
| control_signal_aliases_normalized | True |
| control_signal_polarity_consistent | True |
| consumer_pin_binding_consistent | True |
| fanout_metadata_available | True |
| consumer_contracts_complete_for_metadata_planning | True |
| consumer_contracts_complete_for_physical_planning | False |
| safe_for_metadata_planning | True |
| safe_for_physical_placement | False |

## Unresolved Items

- consumer contracts are metadata-only
- control fanout routing is not proven
- consumer physical pin-side proof may be incomplete for PRECHARGE
- precharge adapter may still be missing or source-level only
- timing proof for enable arrival is missing
- routing proof for all control signals is missing
- control-row physical placement proof is missing
- rail continuity proof is missing
- no DRC/LVS proof exists
- standalone integration is not allowed yet

## Step 6.27 Recommendation

```json
{
  "recommended_next_phase": "time_control_consumer_pin_metadata_closure",
  "candidate_directions": [
    "precharge_consumer_adapter_audit",
    "wordline_secondary_consumer_contract_normalization",
    "control_fanout_handoff_budget",
    "control_row_preplacement_constraints"
  ],
  "reason": [
    "Primary consumer-side contracts are now normalized at metadata level.",
    "The weakest link is PRECHARGE consumer closure, which is still source-level plus pin-audit only.",
    "Routing, timing, and control-row placement remain blocked, so the next useful step is consumer-pin metadata closure rather than physical placement."
  ]
}
```

## Entry Decisions

- can_enter_time_control_consumer_metadata_planning: `True`
- can_enter_time_control_physical_placement: `False`
- can_enter_standalone_control_placement: `False`

