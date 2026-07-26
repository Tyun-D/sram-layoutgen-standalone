# OpenYield Decoder Generated Block Plan Summary

This report summarizes the decoder metadata chain as a generated-block pre-placement plan. It remains metadata-only and does not create legal physical placement, routing, or GDS.

## Plan Summary

- plan_name: `DECODER_CASCADE_GENERATED_BLOCK_PLAN`
- target_block: `DECODER_CASCADE`
- addr_width: `5`
- num_rows: `32`
- metadata_chain_complete: `True`
- can_enter_decoder_generated_block_planning: `True`
- can_enter_decoder_preplacement_feasibility: `True`
- can_enter_physical_decoder_placement: `False`
- can_enter_very_limited_control_row_smoke: `False`

## Stage Hierarchy

```json
{
  "level_0": {
    "stage_count": 1,
    "stage": "DEC_0_0",
    "role": "intermediate_enable_bus",
    "template": "DECODER_LEVEL0_STAGE_TEMPLATE",
    "inputs": [
      "A3",
      "A4",
      "VSS"
    ],
    "enable": "VDD",
    "outputs": [
      "EN_0_0_0",
      "EN_0_0_1",
      "EN_0_0_2",
      "EN_0_0_3",
      "EN_0_0_4",
      "EN_0_0_5",
      "EN_0_0_6",
      "EN_0_0_7"
    ],
    "consumed_outputs": [
      "EN_0_0_0",
      "EN_0_0_1",
      "EN_0_0_2",
      "EN_0_0_3"
    ],
    "unconsumed_outputs": [
      "EN_0_0_4",
      "EN_0_0_5",
      "EN_0_0_6",
      "EN_0_0_7"
    ]
  },
  "level_1": {
    "stage_count": 4,
    "stages": [
      "DEC_1_0",
      "DEC_1_1",
      "DEC_1_2",
      "DEC_1_3"
    ],
    "role": "wordline_outputs",
    "template": "DECODER_LEVEL1_STAGE_TEMPLATE",
    "inputs": [
      "A0",
      "A1",
      "A2"
    ],
    "enables": [
      "EN_0_0_0",
      "EN_0_0_1",
      "EN_0_0_2",
      "EN_0_0_3"
    ],
    "outputs": [
      "WL0",
      "WL1",
      "WL2",
      "WL3",
      "WL4",
      "WL5",
      "WL6",
      "WL7",
      "WL8",
      "WL9",
      "WL10",
      "WL11",
      "WL12",
      "WL13",
      "WL14",
      "WL15",
      "WL16",
      "WL17",
      "WL18",
      "WL19",
      "WL20",
      "WL21",
      "WL22",
      "WL23",
      "WL24",
      "WL25",
      "WL26",
      "WL27",
      "WL28",
      "WL29",
      "WL30",
      "WL31"
    ]
  }
}
```

## Logic Strategy

```json
{
  "recommended_decoder_logic_strategy": "metadata_composite_nand2_inv",
  "direct_pnand3_exists": false,
  "direct_and3_exists": false,
  "gen_nand4_proxy_only": true,
  "gen_nand4_safe_for_physical_substitution": false
}
```

## Composite Leaf Convention Summary

```json
{
  "pnand3_composite_convention_available": true,
  "and3_composite_convention_available": true,
  "leaf_pin_metadata_complete": true,
  "leaf_power_metadata_complete": true,
  "composite_internal_net_routing_proven": false,
  "composite_rail_continuity_proven": false,
  "convention_names": [
    "PNAND3_COMPOSITE_NAND2_INV",
    "AND3_COMPOSITE_NAND2_INV"
  ]
}
```

## Output Contract / Truth Table Summary

```json
{
  "truth_table_binding": {
    "truth_table_binding_complete": true,
    "requires_decoder_truth_table_binding": false,
    "input_handoff_consistent": true,
    "level_enable_handoff_consistent": true,
    "wordline_output_handoff_consistent": true,
    "wordline_driver_semantics_confirmed": true
  },
  "output_contracts": {
    "local_contract_count": 8,
    "contract_names": [
      "DECODER3_8_OUTPUT_CONTRACT_WL0",
      "DECODER3_8_OUTPUT_CONTRACT_WL1",
      "DECODER3_8_OUTPUT_CONTRACT_WL2",
      "DECODER3_8_OUTPUT_CONTRACT_WL3",
      "DECODER3_8_OUTPUT_CONTRACT_WL4",
      "DECODER3_8_OUTPUT_CONTRACT_WL5",
      "DECODER3_8_OUTPUT_CONTRACT_WL6",
      "DECODER3_8_OUTPUT_CONTRACT_WL7"
    ],
    "all_local_outputs_have_contract": true,
    "all_level0_outputs_have_expansion": true,
    "all_level1_outputs_have_expansion": true
  }
}
```

## Handoff Budget Summary

```json
{
  "wordline_handoff_group_count": 4,
  "wordline_outputs": 32,
  "all_wordline_outputs_have_handoff_budget": true,
  "wordline_handoff_budget_pass": true,
  "wordline_handoff_budget_is_tight": true,
  "wordline_group_required_width": 2.0,
  "wordline_group_available_width": 2.0,
  "consumed_enable_outputs": 4,
  "unused_enable_outputs": 4,
  "all_consumed_enable_outputs_have_handoff_budget": true,
  "unused_enable_outputs_not_routed": true,
  "enable_handoff_budget_pass": true,
  "enable_required_width": 1.2,
  "enable_available_width": 2.0,
  "physical_routing_proven": false
}
```

## BBox Proxy Summary

```json
{
  "bbox_proxy_is_metadata_only": true,
  "bbox_proxy_not_legal_physical_layout": true,
  "stage_bbox_proxy_policy": "pessimistic_linear_macro_proxy_from_row_rules",
  "stage_bbox_proxy_width": 44.7275,
  "stage_bbox_proxy_height": 1.565,
  "composite_leaf_bbox_proxy": {
    "PNAND3_COMPOSITE_NAND2_INV": {
      "bbox_proxy_policy": "horizontal_leaf_chain",
      "bbox_proxy_width": 3.2975,
      "bbox_proxy_height": 1.48,
      "internal_gap": 0.2,
      "bbox_proxy_is_metadata_only": true
    },
    "AND3_COMPOSITE_NAND2_INV": {
      "bbox_proxy_policy": "horizontal_leaf_chain",
      "bbox_proxy_width": 4.32,
      "bbox_proxy_height": 1.48,
      "internal_gap": 0.2,
      "bbox_proxy_is_metadata_only": true
    }
  },
  "handoff_window_bbox_proxy": {
    "WORDLINE_OUTPUT_HANDOFF_WINDOW_GROUP_0": {
      "width": 2.0,
      "height": 12.52
    },
    "WORDLINE_OUTPUT_HANDOFF_WINDOW_GROUP_1": {
      "width": 2.0,
      "height": 12.52
    },
    "WORDLINE_OUTPUT_HANDOFF_WINDOW_GROUP_2": {
      "width": 2.0,
      "height": 12.52
    },
    "WORDLINE_OUTPUT_HANDOFF_WINDOW_GROUP_3": {
      "width": 2.0,
      "height": 12.52
    },
    "ENABLE_BUS_HANDOFF_WINDOW": {
      "width": 2.0,
      "height": 1.48
    }
  }
}
```

## Power / Rail Policy

```json
{
  "decoder_power_policy": "local_horizontal_vdd_gnd_only_no_shared_rail",
  "safe_for_shared_rail": false,
  "rail_continuity_proven": false,
  "stage_power_policy_available": true,
  "leaf_power_metadata_complete": true,
  "composite_rail_continuity_proven": false
}
```

## Consistency Checks

| check | value |
| --- | --- |
| decoder_stage_candidates_available | True |
| decoder_row_rules_available | True |
| decoder_logic_repair_strategy_available | True |
| decoder_composite_leaf_conventions_available | True |
| decoder_stage_templates_available | True |
| decoder_truth_table_binding_complete | True |
| decoder_output_contracts_available | True |
| decoder_output_handoff_budget_available | True |
| input_handoff_consistent | True |
| level_enable_handoff_consistent | True |
| wordline_output_handoff_consistent | True |
| unused_enable_outputs_not_routed | True |
| all_required_sections_present | True |
| metadata_chain_complete | True |
| physical_routing_proven | False |

## Blockers

- bbox proxies are metadata-only
- stage packing is not legalized
- composite internal net routing is not proven
- rail continuity is not proven
- shared rail is disabled
- handoff windows are metadata proxies
- wordline budget is tight and not a routing proof
- decoder level1 enable target physical pin-side proof is missing
- full channel legality is not proven

## Step 6.18 Recommendation

Step 6.18 should perform decoder pre-placement feasibility: validate whether the metadata stage rows, bbox proxies, and tight wordline budget can be turned into a bounded prototype packing study without claiming legal placement.

