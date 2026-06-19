# OpenYield Decoder Output Contract Audit

This is a metadata-only audit for decoder output-specific contracts. It does not modify placement, routing, standalone.py, or the GDS writer.

## Summary

- decoder_output_contracts_available: `True`
- can_enter_decoder_generated_block_planning: `True`
- can_enter_physical_decoder_placement: `False`
- can_enter_very_limited_control_row_smoke: `False`

## Generic Output Contracts

| contract | slot | polarity | selected_input_nets | and3_slot | and2_slot | internal_nets | subzone |
| --- | --- | --- | --- | --- | --- | --- | --- |
| DECODER3_8_OUTPUT_CONTRACT_WL0 | WL0 | {"A0": false, "A1": false, "A2": false} | {"A0_term": "A0_bar", "A1_term": "A1_bar", "A2_term": "A2_bar"} | Xdec_and3_wl0 | Xdec_and2_wl0 | wl0_and3_ab_n, wl0_and3_ab, wl0_and3_abc_n, wl0_and2_ab_n, wl0_and2_ab | OUTPUT_CONTRACT_ZONE_WL0 |
| DECODER3_8_OUTPUT_CONTRACT_WL1 | WL1 | {"A0": false, "A1": false, "A2": true} | {"A0_term": "A0_bar", "A1_term": "A1_bar", "A2_term": "A2"} | Xdec_and3_wl1 | Xdec_and2_wl1 | wl1_and3_ab_n, wl1_and3_ab, wl1_and3_abc_n, wl1_and2_ab_n, wl1_and2_ab | OUTPUT_CONTRACT_ZONE_WL1 |
| DECODER3_8_OUTPUT_CONTRACT_WL2 | WL2 | {"A0": false, "A1": true, "A2": false} | {"A0_term": "A0_bar", "A1_term": "A1", "A2_term": "A2_bar"} | Xdec_and3_wl2 | Xdec_and2_wl2 | wl2_and3_ab_n, wl2_and3_ab, wl2_and3_abc_n, wl2_and2_ab_n, wl2_and2_ab | OUTPUT_CONTRACT_ZONE_WL2 |
| DECODER3_8_OUTPUT_CONTRACT_WL3 | WL3 | {"A0": false, "A1": true, "A2": true} | {"A0_term": "A0_bar", "A1_term": "A1", "A2_term": "A2"} | Xdec_and3_wl3 | Xdec_and2_wl3 | wl3_and3_ab_n, wl3_and3_ab, wl3_and3_abc_n, wl3_and2_ab_n, wl3_and2_ab | OUTPUT_CONTRACT_ZONE_WL3 |
| DECODER3_8_OUTPUT_CONTRACT_WL4 | WL4 | {"A0": true, "A1": false, "A2": false} | {"A0_term": "A0", "A1_term": "A1_bar", "A2_term": "A2_bar"} | Xdec_and3_wl4 | Xdec_and2_wl4 | wl4_and3_ab_n, wl4_and3_ab, wl4_and3_abc_n, wl4_and2_ab_n, wl4_and2_ab | OUTPUT_CONTRACT_ZONE_WL4 |
| DECODER3_8_OUTPUT_CONTRACT_WL5 | WL5 | {"A0": true, "A1": false, "A2": true} | {"A0_term": "A0", "A1_term": "A1_bar", "A2_term": "A2"} | Xdec_and3_wl5 | Xdec_and2_wl5 | wl5_and3_ab_n, wl5_and3_ab, wl5_and3_abc_n, wl5_and2_ab_n, wl5_and2_ab | OUTPUT_CONTRACT_ZONE_WL5 |
| DECODER3_8_OUTPUT_CONTRACT_WL6 | WL6 | {"A0": true, "A1": true, "A2": false} | {"A0_term": "A0", "A1_term": "A1", "A2_term": "A2_bar"} | Xdec_and3_wl6 | Xdec_and2_wl6 | wl6_and3_ab_n, wl6_and3_ab, wl6_and3_abc_n, wl6_and2_ab_n, wl6_and2_ab | OUTPUT_CONTRACT_ZONE_WL6 |
| DECODER3_8_OUTPUT_CONTRACT_WL7 | WL7 | {"A0": true, "A1": true, "A2": true} | {"A0_term": "A0", "A1_term": "A1", "A2_term": "A2"} | Xdec_and3_wl7 | Xdec_and2_wl7 | wl7_and3_ab_n, wl7_and3_ab, wl7_and3_abc_n, wl7_and2_ab_n, wl7_and2_ab | OUTPUT_CONTRACT_ZONE_WL7 |

## Level 0 Output Expansion

```json
{
  "mapping": {
    "DEC_0_0.WL0": "EN_0_0_0",
    "DEC_0_0.WL1": "EN_0_0_1",
    "DEC_0_0.WL2": "EN_0_0_2",
    "DEC_0_0.WL3": "EN_0_0_3",
    "DEC_0_0.WL4": "EN_0_0_4",
    "DEC_0_0.WL5": "EN_0_0_5",
    "DEC_0_0.WL6": "EN_0_0_6",
    "DEC_0_0.WL7": "EN_0_0_7"
  },
  "downstream_consumed_enable_outputs": [
    "EN_0_0_0",
    "EN_0_0_1",
    "EN_0_0_2",
    "EN_0_0_3"
  ],
  "unused_or_unconsumed_enable_outputs": [
    "EN_0_0_4",
    "EN_0_0_5",
    "EN_0_0_6",
    "EN_0_0_7"
  ]
}
```

## Level 1 Output Expansion

```json
[
  {
    "stage_name": "DEC_1_0",
    "local_output_slot": "WL0",
    "global_wordline": "WL0"
  },
  {
    "stage_name": "DEC_1_0",
    "local_output_slot": "WL1",
    "global_wordline": "WL1"
  },
  {
    "stage_name": "DEC_1_0",
    "local_output_slot": "WL2",
    "global_wordline": "WL2"
  },
  {
    "stage_name": "DEC_1_0",
    "local_output_slot": "WL3",
    "global_wordline": "WL3"
  },
  {
    "stage_name": "DEC_1_0",
    "local_output_slot": "WL4",
    "global_wordline": "WL4"
  },
  {
    "stage_name": "DEC_1_0",
    "local_output_slot": "WL5",
    "global_wordline": "WL5"
  },
  {
    "stage_name": "DEC_1_0",
    "local_output_slot": "WL6",
    "global_wordline": "WL6"
  },
  {
    "stage_name": "DEC_1_0",
    "local_output_slot": "WL7",
    "global_wordline": "WL7"
  },
  {
    "stage_name": "DEC_1_1",
    "local_output_slot": "WL0",
    "global_wordline": "WL8"
  },
  {
    "stage_name": "DEC_1_1",
    "local_output_slot": "WL1",
    "global_wordline": "WL9"
  },
  {
    "stage_name": "DEC_1_1",
    "local_output_slot": "WL2",
    "global_wordline": "WL10"
  },
  {
    "stage_name": "DEC_1_1",
    "local_output_slot": "WL3",
    "global_wordline": "WL11"
  },
  {
    "stage_name": "DEC_1_1",
    "local_output_slot": "WL4",
    "global_wordline": "WL12"
  },
  {
    "stage_name": "DEC_1_1",
    "local_output_slot": "WL5",
    "global_wordline": "WL13"
  },
  {
    "stage_name": "DEC_1_1",
    "local_output_slot": "WL6",
    "global_wordline": "WL14"
  },
  {
    "stage_name": "DEC_1_1",
    "local_output_slot": "WL7",
    "global_wordline": "WL15"
  },
  {
    "stage_name": "DEC_1_2",
    "local_output_slot": "WL0",
    "global_wordline": "WL16"
  },
  {
    "stage_name": "DEC_1_2",
    "local_output_slot": "WL1",
    "global_wordline": "WL17"
  },
  {
    "stage_name": "DEC_1_2",
    "local_output_slot": "WL2",
    "global_wordline": "WL18"
  },
  {
    "stage_name": "DEC_1_2",
    "local_output_slot": "WL3",
    "global_wordline": "WL19"
  },
  {
    "stage_name": "DEC_1_2",
    "local_output_slot": "WL4",
    "global_wordline": "WL20"
  },
  {
    "stage_name": "DEC_1_2",
    "local_output_slot": "WL5",
    "global_wordline": "WL21"
  },
  {
    "stage_name": "DEC_1_2",
    "local_output_slot": "WL6",
    "global_wordline": "WL22"
  },
  {
    "stage_name": "DEC_1_2",
    "local_output_slot": "WL7",
    "global_wordline": "WL23"
  },
  {
    "stage_name": "DEC_1_3",
    "local_output_slot": "WL0",
    "global_wordline": "WL24"
  },
  {
    "stage_name": "DEC_1_3",
    "local_output_slot": "WL1",
    "global_wordline": "WL25"
  },
  {
    "stage_name": "DEC_1_3",
    "local_output_slot": "WL2",
    "global_wordline": "WL26"
  },
  {
    "stage_name": "DEC_1_3",
    "local_output_slot": "WL3",
    "global_wordline": "WL27"
  },
  {
    "stage_name": "DEC_1_3",
    "local_output_slot": "WL4",
    "global_wordline": "WL28"
  },
  {
    "stage_name": "DEC_1_3",
    "local_output_slot": "WL5",
    "global_wordline": "WL29"
  },
  {
    "stage_name": "DEC_1_3",
    "local_output_slot": "WL6",
    "global_wordline": "WL30"
  },
  {
    "stage_name": "DEC_1_3",
    "local_output_slot": "WL7",
    "global_wordline": "WL31"
  }
]
```

## Consistency Checks

```json
{
  "truth_table_binding_complete": true,
  "output_contracts_available": true,
  "all_local_outputs_have_contract": true,
  "all_level0_outputs_have_expansion": true,
  "all_level1_outputs_have_expansion": true,
  "enable_bus_handoff_consistent": true,
  "wordline_output_handoff_consistent": true,
  "slot_binding_consistent": true,
  "reservation_subzones_available": true,
  "physical_routing_proven": false
}
```

## Blockers

- Output-specific contracts are metadata-only and do not prove route completion.
- Reservation subzones are planning partitions, not legal physical layout regions.
- Physical decoder placement and control-row smoke remain blocked.

## Step 6.16 Recommendation

- Refine decoder output handoff windows next: split wordline-driver-side consumers into per-output access targets and add output-to-consumer budget metadata.
