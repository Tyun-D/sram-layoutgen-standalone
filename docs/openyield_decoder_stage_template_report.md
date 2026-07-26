# OpenYield Decoder Stage Template Audit

This is a metadata-only audit for decoder stage templates. It does not modify placement, routing, standalone.py, or the GDS writer.

## Summary

- recommended_decoder_logic_strategy: `metadata_composite_nand2_inv`
- decoder_stage_templates_available: `True`
- decoder_composite_leaf_conventions_bound: `True`
- stage_pin_slots_available: `True`
- stage_internal_net_zones_available: `True`
- stage_bbox_proxy_available: `True`
- stage_power_policy_available: `True`
- truth_table_binding_complete: `False`
- can_enter_decoder_generated_block_planning: `True`
- can_enter_physical_decoder_placement: `False`
- can_enter_very_limited_control_row_smoke: `False`

## Templates

| template | role | input_slots | output_slots | enable_slot | leaf_slot_count | zone_count | bbox_proxy | safe_metadata | safe_physical |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| DECODER3_8_STAGE_TEMPLATE | decoder_stage | EN, A0, A1, A2, VDD, VSS | WL0, WL1, WL2, WL3 ... | EN | 19 | 5 | {"stage_bbox_proxy_policy": "conservative_leaf_slot_sum", "stage_bbox_width": 55.5075, "stage_bbox_height": 2.0, "internal_gap": 0.2, "stage_bbox_proxy_is_metadata_only": true, "stage_bbox_not_legal_physical_layout": true} | True | False |
| DECODER_LEVEL0_STAGE_TEMPLATE | intermediate_enable_bus | EN, A0, A1, A2, VDD, VSS | EN_0_0_0, EN_0_0_1, EN_0_0_2, EN_0_0_3 ... | EN | 19 | 5 | {"stage_bbox_proxy_policy": "conservative_leaf_slot_sum", "stage_bbox_width": 55.5075, "stage_bbox_height": 2.0, "internal_gap": 0.2, "stage_bbox_proxy_is_metadata_only": true, "stage_bbox_not_legal_physical_layout": true} | True | False |
| DECODER_LEVEL1_STAGE_TEMPLATE | wordline_outputs | EN, A0, A1, A2, VDD, VSS | WL0, WL1, WL2, WL3 ... | EN | 19 | 5 | {"stage_bbox_proxy_policy": "conservative_leaf_slot_sum", "stage_bbox_width": 55.5075, "stage_bbox_height": 2.0, "internal_gap": 0.2, "stage_bbox_proxy_is_metadata_only": true, "stage_bbox_not_legal_physical_layout": true} | True | False |

## Level 0 Binding

```json
{
  "stage_name": "DEC_0_0",
  "role": "intermediate_enable_bus",
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
  "template": "DECODER_LEVEL0_STAGE_TEMPLATE",
  "input_anchor": "DECODER_INPUT_ANCHOR",
  "output_anchor": "EAST_ENABLE_BUS_ANCHOR"
}
```

## Level 1 Binding

```json
[
  {
    "stage_name": "DEC_1_0",
    "role": "wordline_outputs",
    "inputs": [
      "A0",
      "A1",
      "A2"
    ],
    "enable": "EN_0_0_0",
    "outputs": [
      "WL0",
      "WL1",
      "WL2",
      "WL3",
      "WL4",
      "WL5",
      "WL6",
      "WL7"
    ],
    "template": "DECODER_LEVEL1_STAGE_TEMPLATE",
    "input_anchor": "LOCAL_ADDR_BUS_ANCHOR",
    "enable_anchor": "ENABLE_BUS_ANCHOR",
    "output_anchor": "WORDLINE_DRIVER_INPUT_HANDOFF_ANCHOR"
  },
  {
    "stage_name": "DEC_1_1",
    "role": "wordline_outputs",
    "inputs": [
      "A0",
      "A1",
      "A2"
    ],
    "enable": "EN_0_0_1",
    "outputs": [
      "WL8",
      "WL9",
      "WL10",
      "WL11",
      "WL12",
      "WL13",
      "WL14",
      "WL15"
    ],
    "template": "DECODER_LEVEL1_STAGE_TEMPLATE",
    "input_anchor": "LOCAL_ADDR_BUS_ANCHOR",
    "enable_anchor": "ENABLE_BUS_ANCHOR",
    "output_anchor": "WORDLINE_DRIVER_INPUT_HANDOFF_ANCHOR"
  },
  {
    "stage_name": "DEC_1_2",
    "role": "wordline_outputs",
    "inputs": [
      "A0",
      "A1",
      "A2"
    ],
    "enable": "EN_0_0_2",
    "outputs": [
      "WL16",
      "WL17",
      "WL18",
      "WL19",
      "WL20",
      "WL21",
      "WL22",
      "WL23"
    ],
    "template": "DECODER_LEVEL1_STAGE_TEMPLATE",
    "input_anchor": "LOCAL_ADDR_BUS_ANCHOR",
    "enable_anchor": "ENABLE_BUS_ANCHOR",
    "output_anchor": "WORDLINE_DRIVER_INPUT_HANDOFF_ANCHOR"
  },
  {
    "stage_name": "DEC_1_3",
    "role": "wordline_outputs",
    "inputs": [
      "A0",
      "A1",
      "A2"
    ],
    "enable": "EN_0_0_3",
    "outputs": [
      "WL24",
      "WL25",
      "WL26",
      "WL27",
      "WL28",
      "WL29",
      "WL30",
      "WL31"
    ],
    "template": "DECODER_LEVEL1_STAGE_TEMPLATE",
    "input_anchor": "LOCAL_ADDR_BUS_ANCHOR",
    "enable_anchor": "ENABLE_BUS_ANCHOR",
    "output_anchor": "WORDLINE_DRIVER_INPUT_HANDOFF_ANCHOR"
  }
]
```

## Blockers

- Stage templates are metadata-only and do not prove legal stage packing.
- Per-slot physical access, internal routing, and rail continuity are still unproven.
- WL truth-table binding from decoder.py is not yet explicitly expanded into slot polarity bindings.
- Physical decoder placement and control-row smoke remain blocked.

## Step 6.14 Recommendation

- Expand decoder truth-table binding next: map each WL slot to its input polarity combination and bind stage templates to output-specific metadata contracts before any placement-oriented decoder prototype.
