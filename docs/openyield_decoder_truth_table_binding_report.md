# OpenYield Decoder Truth Table Binding Audit

This is a metadata-only audit for decoder output truth-table binding. It does not modify placement, routing, standalone.py, or the GDS writer.

## Summary

- truth_table_auto_parse_success: `True`
- decoder_truth_table_binding_available: `True`
- truth_table_binding_complete: `True`
- requires_decoder_truth_table_binding: `False`
- can_enter_decoder_generated_block_planning: `True`
- can_enter_physical_decoder_placement: `False`
- can_enter_very_limited_control_row_smoke: `False`

## Generic DECODER3_8 Truth Table

| output | polarity_terms | required_inverted_nets | and3_slot | and2_slot | source |
| --- | --- | --- | --- | --- | --- |
| WL0 | {"A0": false, "A1": false, "A2": false} | A0_bar, A1_bar, A2_bar | Xdec_and3_wl0 | Xdec_and2_wl0 | decoder.py input_combinations[0] = ('A0b', 'A1b', 'A2b') |
| WL1 | {"A0": false, "A1": false, "A2": true} | A0_bar, A1_bar | Xdec_and3_wl1 | Xdec_and2_wl1 | decoder.py input_combinations[1] = ('A0b', 'A1b', 'A2') |
| WL2 | {"A0": false, "A1": true, "A2": false} | A0_bar, A2_bar | Xdec_and3_wl2 | Xdec_and2_wl2 | decoder.py input_combinations[2] = ('A0b', 'A1', 'A2b') |
| WL3 | {"A0": false, "A1": true, "A2": true} | A0_bar | Xdec_and3_wl3 | Xdec_and2_wl3 | decoder.py input_combinations[3] = ('A0b', 'A1', 'A2') |
| WL4 | {"A0": true, "A1": false, "A2": false} | A1_bar, A2_bar | Xdec_and3_wl4 | Xdec_and2_wl4 | decoder.py input_combinations[4] = ('A0', 'A1b', 'A2b') |
| WL5 | {"A0": true, "A1": false, "A2": true} | A1_bar | Xdec_and3_wl5 | Xdec_and2_wl5 | decoder.py input_combinations[5] = ('A0', 'A1b', 'A2') |
| WL6 | {"A0": true, "A1": true, "A2": false} | A2_bar | Xdec_and3_wl6 | Xdec_and2_wl6 | decoder.py input_combinations[6] = ('A0', 'A1', 'A2b') |
| WL7 | {"A0": true, "A1": true, "A2": true} | - | Xdec_and3_wl7 | Xdec_and2_wl7 | decoder.py input_combinations[7] = ('A0', 'A1', 'A2') |

## Level 0 Binding

```json
{
  "level0_truth_binding": true,
  "level0_stage_name": "DEC_0_0",
  "local_slot_to_global_net_map": {
    "EN": "VDD",
    "A0": "VSS",
    "A1": "A4",
    "A2": "A3"
  },
  "stage_local_output_to_enable_bus_map": {
    "WL0": "EN_0_0_0",
    "WL1": "EN_0_0_1",
    "WL2": "EN_0_0_2",
    "WL3": "EN_0_0_3",
    "WL4": "EN_0_0_4",
    "WL5": "EN_0_0_5",
    "WL6": "EN_0_0_6",
    "WL7": "EN_0_0_7"
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
  ],
  "metadata_only": true,
  "physical_routing_proven": false
}
```

## Level 1 Binding

```json
[
  {
    "stage_name": "DEC_1_0",
    "stage_index": 0,
    "enable_net": "EN_0_0_0",
    "local_slot_to_global_net_map": {
      "EN": "EN_0_0_0",
      "A0": "A2",
      "A1": "A1",
      "A2": "A0"
    },
    "local_output_slot_to_global_wl_map": {
      "WL0": "WL0",
      "WL1": "WL1",
      "WL2": "WL2",
      "WL3": "WL3",
      "WL4": "WL4",
      "WL5": "WL5",
      "WL6": "WL6",
      "WL7": "WL7"
    },
    "truth_table_rows": [
      {
        "local_output_slot": "WL0",
        "global_wordline": "WL0",
        "input_polarity_terms": {
          "A0": false,
          "A1": false,
          "A2": false
        },
        "required_inverted_nets": [
          "A0_bar",
          "A1_bar",
          "A2_bar"
        ],
        "and3_leaf_slot": "Xdec_and3_wl0",
        "and2_leaf_slot": "Xdec_and2_wl0"
      },
      {
        "local_output_slot": "WL1",
        "global_wordline": "WL1",
        "input_polarity_terms": {
          "A0": false,
          "A1": false,
          "A2": true
        },
        "required_inverted_nets": [
          "A0_bar",
          "A1_bar"
        ],
        "and3_leaf_slot": "Xdec_and3_wl1",
        "and2_leaf_slot": "Xdec_and2_wl1"
      },
      {
        "local_output_slot": "WL2",
        "global_wordline": "WL2",
        "input_polarity_terms": {
          "A0": false,
          "A1": true,
          "A2": false
        },
        "required_inverted_nets": [
          "A0_bar",
          "A2_bar"
        ],
        "and3_leaf_slot": "Xdec_and3_wl2",
        "and2_leaf_slot": "Xdec_and2_wl2"
      },
      {
        "local_output_slot": "WL3",
        "global_wordline": "WL3",
        "input_polarity_terms": {
          "A0": false,
          "A1": true,
          "A2": true
        },
        "required_inverted_nets": [
          "A0_bar"
        ],
        "and3_leaf_slot": "Xdec_and3_wl3",
        "and2_leaf_slot": "Xdec_and2_wl3"
      },
      {
        "local_output_slot": "WL4",
        "global_wordline": "WL4",
        "input_polarity_terms": {
          "A0": true,
          "A1": false,
          "A2": false
        },
        "required_inverted_nets": [
          "A1_bar",
          "A2_bar"
        ],
        "and3_leaf_slot": "Xdec_and3_wl4",
        "and2_leaf_slot": "Xdec_and2_wl4"
      },
      {
        "local_output_slot": "WL5",
        "global_wordline": "WL5",
        "input_polarity_terms": {
          "A0": true,
          "A1": false,
          "A2": true
        },
        "required_inverted_nets": [
          "A1_bar"
        ],
        "and3_leaf_slot": "Xdec_and3_wl5",
        "and2_leaf_slot": "Xdec_and2_wl5"
      },
      {
        "local_output_slot": "WL6",
        "global_wordline": "WL6",
        "input_polarity_terms": {
          "A0": true,
          "A1": true,
          "A2": false
        },
        "required_inverted_nets": [
          "A2_bar"
        ],
        "and3_leaf_slot": "Xdec_and3_wl6",
        "and2_leaf_slot": "Xdec_and2_wl6"
      },
      {
        "local_output_slot": "WL7",
        "global_wordline": "WL7",
        "input_polarity_terms": {
          "A0": true,
          "A1": true,
          "A2": true
        },
        "required_inverted_nets": [],
        "and3_leaf_slot": "Xdec_and3_wl7",
        "and2_leaf_slot": "Xdec_and2_wl7"
      }
    ],
    "metadata_only": true,
    "physical_routing_proven": false
  },
  {
    "stage_name": "DEC_1_1",
    "stage_index": 1,
    "enable_net": "EN_0_0_1",
    "local_slot_to_global_net_map": {
      "EN": "EN_0_0_1",
      "A0": "A2",
      "A1": "A1",
      "A2": "A0"
    },
    "local_output_slot_to_global_wl_map": {
      "WL0": "WL8",
      "WL1": "WL9",
      "WL2": "WL10",
      "WL3": "WL11",
      "WL4": "WL12",
      "WL5": "WL13",
      "WL6": "WL14",
      "WL7": "WL15"
    },
    "truth_table_rows": [
      {
        "local_output_slot": "WL0",
        "global_wordline": "WL8",
        "input_polarity_terms": {
          "A0": false,
          "A1": false,
          "A2": false
        },
        "required_inverted_nets": [
          "A0_bar",
          "A1_bar",
          "A2_bar"
        ],
        "and3_leaf_slot": "Xdec_and3_wl0",
        "and2_leaf_slot": "Xdec_and2_wl0"
      },
      {
        "local_output_slot": "WL1",
        "global_wordline": "WL9",
        "input_polarity_terms": {
          "A0": false,
          "A1": false,
          "A2": true
        },
        "required_inverted_nets": [
          "A0_bar",
          "A1_bar"
        ],
        "and3_leaf_slot": "Xdec_and3_wl1",
        "and2_leaf_slot": "Xdec_and2_wl1"
      },
      {
        "local_output_slot": "WL2",
        "global_wordline": "WL10",
        "input_polarity_terms": {
          "A0": false,
          "A1": true,
          "A2": false
        },
        "required_inverted_nets": [
          "A0_bar",
          "A2_bar"
        ],
        "and3_leaf_slot": "Xdec_and3_wl2",
        "and2_leaf_slot": "Xdec_and2_wl2"
      },
      {
        "local_output_slot": "WL3",
        "global_wordline": "WL11",
        "input_polarity_terms": {
          "A0": false,
          "A1": true,
          "A2": true
        },
        "required_inverted_nets": [
          "A0_bar"
        ],
        "and3_leaf_slot": "Xdec_and3_wl3",
        "and2_leaf_slot": "Xdec_and2_wl3"
      },
      {
        "local_output_slot": "WL4",
        "global_wordline": "WL12",
        "input_polarity_terms": {
          "A0": true,
          "A1": false,
          "A2": false
        },
        "required_inverted_nets": [
          "A1_bar",
          "A2_bar"
        ],
        "and3_leaf_slot": "Xdec_and3_wl4",
        "and2_leaf_slot": "Xdec_and2_wl4"
      },
      {
        "local_output_slot": "WL5",
        "global_wordline": "WL13",
        "input_polarity_terms": {
          "A0": true,
          "A1": false,
          "A2": true
        },
        "required_inverted_nets": [
          "A1_bar"
        ],
        "and3_leaf_slot": "Xdec_and3_wl5",
        "and2_leaf_slot": "Xdec_and2_wl5"
      },
      {
        "local_output_slot": "WL6",
        "global_wordline": "WL14",
        "input_polarity_terms": {
          "A0": true,
          "A1": true,
          "A2": false
        },
        "required_inverted_nets": [
          "A2_bar"
        ],
        "and3_leaf_slot": "Xdec_and3_wl6",
        "and2_leaf_slot": "Xdec_and2_wl6"
      },
      {
        "local_output_slot": "WL7",
        "global_wordline": "WL15",
        "input_polarity_terms": {
          "A0": true,
          "A1": true,
          "A2": true
        },
        "required_inverted_nets": [],
        "and3_leaf_slot": "Xdec_and3_wl7",
        "and2_leaf_slot": "Xdec_and2_wl7"
      }
    ],
    "metadata_only": true,
    "physical_routing_proven": false
  },
  {
    "stage_name": "DEC_1_2",
    "stage_index": 2,
    "enable_net": "EN_0_0_2",
    "local_slot_to_global_net_map": {
      "EN": "EN_0_0_2",
      "A0": "A2",
      "A1": "A1",
      "A2": "A0"
    },
    "local_output_slot_to_global_wl_map": {
      "WL0": "WL16",
      "WL1": "WL17",
      "WL2": "WL18",
      "WL3": "WL19",
      "WL4": "WL20",
      "WL5": "WL21",
      "WL6": "WL22",
      "WL7": "WL23"
    },
    "truth_table_rows": [
      {
        "local_output_slot": "WL0",
        "global_wordline": "WL16",
        "input_polarity_terms": {
          "A0": false,
          "A1": false,
          "A2": false
        },
        "required_inverted_nets": [
          "A0_bar",
          "A1_bar",
          "A2_bar"
        ],
        "and3_leaf_slot": "Xdec_and3_wl0",
        "and2_leaf_slot": "Xdec_and2_wl0"
      },
      {
        "local_output_slot": "WL1",
        "global_wordline": "WL17",
        "input_polarity_terms": {
          "A0": false,
          "A1": false,
          "A2": true
        },
        "required_inverted_nets": [
          "A0_bar",
          "A1_bar"
        ],
        "and3_leaf_slot": "Xdec_and3_wl1",
        "and2_leaf_slot": "Xdec_and2_wl1"
      },
      {
        "local_output_slot": "WL2",
        "global_wordline": "WL18",
        "input_polarity_terms": {
          "A0": false,
          "A1": true,
          "A2": false
        },
        "required_inverted_nets": [
          "A0_bar",
          "A2_bar"
        ],
        "and3_leaf_slot": "Xdec_and3_wl2",
        "and2_leaf_slot": "Xdec_and2_wl2"
      },
      {
        "local_output_slot": "WL3",
        "global_wordline": "WL19",
        "input_polarity_terms": {
          "A0": false,
          "A1": true,
          "A2": true
        },
        "required_inverted_nets": [
          "A0_bar"
        ],
        "and3_leaf_slot": "Xdec_and3_wl3",
        "and2_leaf_slot": "Xdec_and2_wl3"
      },
      {
        "local_output_slot": "WL4",
        "global_wordline": "WL20",
        "input_polarity_terms": {
          "A0": true,
          "A1": false,
          "A2": false
        },
        "required_inverted_nets": [
          "A1_bar",
          "A2_bar"
        ],
        "and3_leaf_slot": "Xdec_and3_wl4",
        "and2_leaf_slot": "Xdec_and2_wl4"
      },
      {
        "local_output_slot": "WL5",
        "global_wordline": "WL21",
        "input_polarity_terms": {
          "A0": true,
          "A1": false,
          "A2": true
        },
        "required_inverted_nets": [
          "A1_bar"
        ],
        "and3_leaf_slot": "Xdec_and3_wl5",
        "and2_leaf_slot": "Xdec_and2_wl5"
      },
      {
        "local_output_slot": "WL6",
        "global_wordline": "WL22",
        "input_polarity_terms": {
          "A0": true,
          "A1": true,
          "A2": false
        },
        "required_inverted_nets": [
          "A2_bar"
        ],
        "and3_leaf_slot": "Xdec_and3_wl6",
        "and2_leaf_slot": "Xdec_and2_wl6"
      },
      {
        "local_output_slot": "WL7",
        "global_wordline": "WL23",
        "input_polarity_terms": {
          "A0": true,
          "A1": true,
          "A2": true
        },
        "required_inverted_nets": [],
        "and3_leaf_slot": "Xdec_and3_wl7",
        "and2_leaf_slot": "Xdec_and2_wl7"
      }
    ],
    "metadata_only": true,
    "physical_routing_proven": false
  },
  {
    "stage_name": "DEC_1_3",
    "stage_index": 3,
    "enable_net": "EN_0_0_3",
    "local_slot_to_global_net_map": {
      "EN": "EN_0_0_3",
      "A0": "A2",
      "A1": "A1",
      "A2": "A0"
    },
    "local_output_slot_to_global_wl_map": {
      "WL0": "WL24",
      "WL1": "WL25",
      "WL2": "WL26",
      "WL3": "WL27",
      "WL4": "WL28",
      "WL5": "WL29",
      "WL6": "WL30",
      "WL7": "WL31"
    },
    "truth_table_rows": [
      {
        "local_output_slot": "WL0",
        "global_wordline": "WL24",
        "input_polarity_terms": {
          "A0": false,
          "A1": false,
          "A2": false
        },
        "required_inverted_nets": [
          "A0_bar",
          "A1_bar",
          "A2_bar"
        ],
        "and3_leaf_slot": "Xdec_and3_wl0",
        "and2_leaf_slot": "Xdec_and2_wl0"
      },
      {
        "local_output_slot": "WL1",
        "global_wordline": "WL25",
        "input_polarity_terms": {
          "A0": false,
          "A1": false,
          "A2": true
        },
        "required_inverted_nets": [
          "A0_bar",
          "A1_bar"
        ],
        "and3_leaf_slot": "Xdec_and3_wl1",
        "and2_leaf_slot": "Xdec_and2_wl1"
      },
      {
        "local_output_slot": "WL2",
        "global_wordline": "WL26",
        "input_polarity_terms": {
          "A0": false,
          "A1": true,
          "A2": false
        },
        "required_inverted_nets": [
          "A0_bar",
          "A2_bar"
        ],
        "and3_leaf_slot": "Xdec_and3_wl2",
        "and2_leaf_slot": "Xdec_and2_wl2"
      },
      {
        "local_output_slot": "WL3",
        "global_wordline": "WL27",
        "input_polarity_terms": {
          "A0": false,
          "A1": true,
          "A2": true
        },
        "required_inverted_nets": [
          "A0_bar"
        ],
        "and3_leaf_slot": "Xdec_and3_wl3",
        "and2_leaf_slot": "Xdec_and2_wl3"
      },
      {
        "local_output_slot": "WL4",
        "global_wordline": "WL28",
        "input_polarity_terms": {
          "A0": true,
          "A1": false,
          "A2": false
        },
        "required_inverted_nets": [
          "A1_bar",
          "A2_bar"
        ],
        "and3_leaf_slot": "Xdec_and3_wl4",
        "and2_leaf_slot": "Xdec_and2_wl4"
      },
      {
        "local_output_slot": "WL5",
        "global_wordline": "WL29",
        "input_polarity_terms": {
          "A0": true,
          "A1": false,
          "A2": true
        },
        "required_inverted_nets": [
          "A1_bar"
        ],
        "and3_leaf_slot": "Xdec_and3_wl5",
        "and2_leaf_slot": "Xdec_and2_wl5"
      },
      {
        "local_output_slot": "WL6",
        "global_wordline": "WL30",
        "input_polarity_terms": {
          "A0": true,
          "A1": true,
          "A2": false
        },
        "required_inverted_nets": [
          "A2_bar"
        ],
        "and3_leaf_slot": "Xdec_and3_wl6",
        "and2_leaf_slot": "Xdec_and2_wl6"
      },
      {
        "local_output_slot": "WL7",
        "global_wordline": "WL31",
        "input_polarity_terms": {
          "A0": true,
          "A1": true,
          "A2": true
        },
        "required_inverted_nets": [],
        "and3_leaf_slot": "Xdec_and3_wl7",
        "and2_leaf_slot": "Xdec_and2_wl7"
      }
    ],
    "metadata_only": true,
    "physical_routing_proven": false
  }
]
```

## Slot-Level Contract

```json
{
  "slot_binding_available": true,
  "input_inversion_slot_binding_available": true,
  "output_leaf_slot_binding_available": true,
  "enable_distribution_binding_available": true,
  "truth_table_binding_complete": true,
  "requires_decoder_truth_table_binding": false
}
```

## Handoff Consistency

```json
{
  "input_handoff_consistent": true,
  "level_enable_handoff_consistent": true,
  "output_handoff_consistent": true,
  "wordline_driver_semantics_confirmed": true,
  "physical_routing_proven": false
}
```

## Blockers

- Truth-table binding is metadata-only and does not prove physical routing.
- Per-slot physical access, internal routing, and rail continuity remain unproven.
- Decoder placement and control-row smoke remain blocked even after output binding.

## Step 6.15 Recommendation

- Audit output-specific decoder contracts next: bind each WL slot to explicit input-bar usage, output handoff metadata, and per-output reservation subzones before any placement-oriented prototype.
