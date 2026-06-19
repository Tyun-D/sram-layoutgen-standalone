# OpenYield Decoder Row Rule Audit

This is a metadata-only decoder generated-logic row-rule and stage-packing audit. It does not modify standalone.py, routing, or the GDS writer.

## Summary

- addr_width: `5`
- num_rows: `32`
- decoder_row_rules_available: `True`
- decoder_stage_packing_available: `True`
- decoder_logic_row_metadata_available: `True`
- decoder_direct_nand3_missing: `True`
- decoder_generated_logic_unresolved: `True`
- decoder_power_metadata_complete: `False`
- decoder_pin_metadata_complete: `False`
- can_enter_decoder_generated_block_planning: `True`
- can_enter_physical_decoder_placement: `False`
- can_enter_very_limited_control_row_smoke: `False`

## Decoder Hierarchy

- n_levels: `2`
- level_groups: `[1, 4]`
- total_decoder3_8_instances: `5`

## Stage Packing Plan

| row_name | stage_name | level | decoder_index | enable_net | input_side | output_side | estimated_cell_count | candidate_bbox | notes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| DECODER_LEVEL0_ROW | DEC_0_0 | 0 | 0 | VDD | decoder_input_side | east_enable_bus_side | 27 | {"x0": 0.0, "y0": 0.0, "x1": 44.7275, "y1": 1.565, "width": 44.7275, "height": 1.565} | Estimated bbox uses a pessimistic linear macro proxy and is metadata-only.; Output side is an intermediate enable bus, not final WL pins. |
| DECODER_LEVEL1_ROW_GROUP_0 | DEC_1_0 | 1 | 0 | EN_0_0_0 | decoder_input_side | wordline_driver_side | 27 | {"x0": 0.0, "y0": 3.13, "x1": 44.7275, "y1": 4.695, "width": 44.7275, "height": 1.565} | Estimated bbox uses a pessimistic linear macro proxy and is metadata-only.; Output side targets WL nets for downstream WORDLINEDRIVER.A handoff. |
| DECODER_LEVEL1_ROW_GROUP_1 | DEC_1_1 | 1 | 1 | EN_0_0_1 | decoder_input_side | wordline_driver_side | 27 | {"x0": 0.0, "y0": 6.26, "x1": 44.7275, "y1": 7.825, "width": 44.7275, "height": 1.565} | Estimated bbox uses a pessimistic linear macro proxy and is metadata-only.; Output side targets WL nets for downstream WORDLINEDRIVER.A handoff. |
| DECODER_LEVEL1_ROW_GROUP_2 | DEC_1_2 | 1 | 2 | EN_0_0_2 | decoder_input_side | wordline_driver_side | 27 | {"x0": 0.0, "y0": 9.39, "x1": 44.7275, "y1": 10.955, "width": 44.7275, "height": 1.565} | Estimated bbox uses a pessimistic linear macro proxy and is metadata-only.; Output side targets WL nets for downstream WORDLINEDRIVER.A handoff. |
| DECODER_LEVEL1_ROW_GROUP_3 | DEC_1_3 | 1 | 3 | EN_0_0_3 | decoder_input_side | wordline_driver_side | 27 | {"x0": 0.0, "y0": 12.52, "x1": 44.7275, "y1": 14.085, "width": 44.7275, "height": 1.565} | Estimated bbox uses a pessimistic linear macro proxy and is metadata-only.; Output side targets WL nets for downstream WORDLINEDRIVER.A handoff. |

## Decoder Row Rules

| rule | target | level | stage_count | logic_cell_sequence | input_side | output_side | enable_side | power_policy | pin_metadata_status | placement_status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| DECODER_LEVEL0_ROW_RULE | DECODER_LEVEL0_ROW | 0 | 1 | Pinv, AND3, AND2 | decoder_input_side | east_enable_bus_side | north_or_tiehigh_side | local_horizontal_vdd_gnd_only_no_shared_rail | partial | needs_power_metadata_repair |
| DECODER_LEVEL1_ROW_RULE | DECODER_LEVEL1_ROW_GROUP_* | 1 | 4 | Pinv, AND3, AND2 | west_addr_side | east_wordline_side | north_enable_bus_side | local_horizontal_vdd_gnd_only_no_shared_rail | partial | needs_logic_macro_repair |
| DECODER_STAGE_PROXY_RULE | DECODER3_8_GROUP | -1 | 5 | 3x Pinv, 8x AND3, 8x AND2 | left | right | top | metadata_only_proxy_power_policy | partial | metadata_row_rule_only |

## Logic Cell Availability

```json
{
  "Pinv_to_gen_inv": {
    "mapping": "direct_metadata_candidate",
    "gds_available": true,
    "spice_available": false,
    "pin_metadata_complete": true,
    "power_metadata_complete": true,
    "safe_for_physical_placement": false
  },
  "PNAND2_to_gen_nand2": {
    "mapping": "direct_metadata_candidate",
    "gds_available": true,
    "spice_available": false,
    "pin_metadata_complete": true,
    "power_metadata_complete": true,
    "safe_for_physical_placement": false
  },
  "AND2_to_gen_nand2_plus_gen_inv": {
    "mapping": "composite_metadata_candidate",
    "required_cells": {
      "gen_nand2": 1,
      "gen_inv": 1
    },
    "resolved": true,
    "safe_for_physical_placement": false
  },
  "PNAND3_direct": {
    "mapping": "missing_direct_macro",
    "direct_nand3_available": false
  },
  "AND3_resolution": {
    "mapping": "generated_logic_unresolved",
    "required_cells": {
      "pnand3_like": 1,
      "gen_inv": 1
    },
    "gen_nand4_substitution": "metadata_only_possible",
    "safe_for_physical_placement": false
  }
}
```

## Pin Metadata Audit

| macro | required_pins | available_labels | missing_labels | pin_metadata_complete | power_metadata_complete | safe_for_metadata_mapping | safe_for_physical_placement |
| --- | --- | --- | --- | --- | --- | --- | --- |
| gen_inv | a, z, vdd, gnd | a, z, vdd, gnd | - | True | True | True | False |
| gen_nand2 | a, b, z, vdd, gnd | a, b, z, vdd, gnd | - | True | True | True | False |
| gen_nand4 | a, b, c, d, z, vdd, gnd | - | a, b, c, d, z, vdd, gnd | False | False | True | False |
| gen_wl_driver | decoder_input, wordline_enable, wl, vdd, gnd | decoder_input, wordline_enable, wl, vdd, gnd | - | True | True | True | False |

## Power Metadata Audit

| macro | row_power_policy | local_power_pins_available | rail_continuity_proven | safe_for_shared_rail | power_metadata_blockers |
| --- | --- | --- | --- | --- | --- |
| gen_inv | local_horizontal_vdd_gnd_only_no_shared_rail | True | False | False | rail_continuity_not_proven; shared_rail_not_allowed_for_decoder_generated_logic |
| gen_nand2 | local_horizontal_vdd_gnd_only_no_shared_rail | True | False | False | rail_continuity_not_proven; shared_rail_not_allowed_for_decoder_generated_logic |
| gen_nand4 | local_horizontal_vdd_gnd_only_no_shared_rail | False | False | False | power_metadata_incomplete; rail_continuity_not_proven; shared_rail_not_allowed_for_decoder_generated_logic |
| gen_wl_driver | local_horizontal_vdd_gnd_only_no_shared_rail | True | False | False | rail_continuity_not_proven; shared_rail_not_allowed_for_decoder_generated_logic |

## Input Handoff

```json
{
  "source": "ADDR_DFF_ROW.addr_q[i]",
  "sink": "DECODER_CASCADE.A[i]",
  "source_anchor": "DECODER_INPUT_ANCHOR",
  "source_window": "ADDR_TO_DECODER_WINDOW",
  "decoder_stage_input_side": "decoder_input_side",
  "metadata_only": true,
  "pin_proven": false,
  "physical_routing_proven": false
}
```

## Output Handoff

```json
{
  "source": "DECODER_CASCADE.WL[row] / decoder_out[row]",
  "consumer": "WORDLINEDRIVER",
  "consumer_pin": "A",
  "sink": "WORDLINEDRIVER.A[row]",
  "wordline_driver_semantics_confirmed": true,
  "metadata_only": true,
  "pin_proven": false,
  "physical_routing_proven": false
}
```

## Blockers

- Direct PNAND3 / AND3 hard macro is still missing, so decoder stage logic is not fully resolved.
- gen_nand4 is not pin/power metadata complete and cannot be treated as a proven PNAND3 replacement.
- Shared rail safety is not proven for decoder generated-logic rows.
- Per-stage pin metadata is only partial and output routing toward WORDLINEDRIVER.A remains unproven.
- Row-rule and stage-packing data are metadata planning aids only, not legal decoder placement evidence.

## Step 6.11 Recommendation

- Audit decoder logic leaf repair options next: prove or reject PNAND3 substitution strategy, then define per-stage pin/power metadata before any decoder physical smoke.
