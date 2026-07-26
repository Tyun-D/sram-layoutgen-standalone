# OpenYield Decoder Stage Candidate Audit

This is a read-only metadata audit for DECODER_CASCADE stage/group candidates. It does not modify standalone.py, routing, placement, or the GDS writer.

## Summary

- decoder_cascade_exists: `True`
- decoder3_8_exists: `True`
- decoder_stage_decomposition_success: `True`
- decoder_generated_block_plan_available: `True`
- decoder_envelope_is_metadata_only: `True`
- decoder_hardmacro_pin_proven: `False`
- decoder_logic_macros_partially_available: `True`
- decoder_direct_and3_or_nand3_missing: `True`
- can_enter_decoder_generated_block_planning: `True`
- can_enter_physical_decoder_placement: `False`
- can_enter_very_limited_control_row_smoke: `False`

## Top-Level Decoder View

- source path: `E:\njust\keyan\SRAM Compiler_V2\OpenRAM-stable\third_party\OpenYield\sram_compiler\subcircuits\decoder.py`
- addr_width: `5`
- num_rows: `32`
- top inputs: `VDD, VSS, A[0], A[1], A[2], A[3], A[4]`
- top outputs: `WL[0], WL[1], WL[2], WL[3], WL[4], WL[5], WL[6], WL[7] ...`

## Decoder Hierarchy

- n_levels: `2`
- level_groups: `[1, 4]`
- total_decoder3_8_instances: `5`

| level | decoder_index | stage_name | enable_net | address_node_order | decoder_pin_map | output_role | first_outputs |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 0 | 0 | DEC_0_0 | VDD | A3, A4, VSS | EN=VDD, A0=VSS, A1=A4, A2=A3 | intermediate_enable_bus | EN_0_0_0, EN_0_0_1, EN_0_0_2, EN_0_0_3 ... |
| 1 | 0 | DEC_1_0 | EN_0_0_0 | A0, A1, A2 | EN=EN_0_0_0, A0=A2, A1=A1, A2=A0 | wordline_outputs | WL0, WL1, WL2, WL3 ... |
| 1 | 1 | DEC_1_1 | EN_0_0_1 | A0, A1, A2 | EN=EN_0_0_1, A0=A2, A1=A1, A2=A0 | wordline_outputs | WL8, WL9, WL10, WL11 ... |
| 1 | 2 | DEC_1_2 | EN_0_0_2 | A0, A1, A2 | EN=EN_0_0_2, A0=A2, A1=A1, A2=A0 | wordline_outputs | WL16, WL17, WL18, WL19 ... |
| 1 | 3 | DEC_1_3 | EN_0_0_3 | A0, A1, A2 | EN=EN_0_0_3, A0=A2, A1=A1, A2=A0 | wordline_outputs | WL24, WL25, WL26, WL27 ... |

## Stage / Group Candidates

| candidate | type | source_class | inputs | outputs | subcells | local_macros | missing_macros | mapping_status | placement_feasibility |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| DECODER_CASCADE_STAGE_PLAN | hierarchical_decoder_plan | DECODER_CASCADE | A[0], A[1], A[2], A[3], A[4] | WL[*] | DECODER3_8 | gen_inv, gen_nand2, gen_nand4, gen_wl_driver | gen_nand3 | generated_logic_partial | metadata_stage_plan_only |
| DECODER3_8_GROUP | decoder_stage_group | DECODER3_8 | EN, A0, A1, A2 | WL0, WL1, WL2, WL3, WL4, WL5, WL6, WL7 | Pinv, AND3, AND2 | gen_inv, gen_nand2 | gen_nand3 | generated_logic_partial | needs_generated_logic_row_rules |
| DECODER_LOGIC_CELL_SET | logic_cell_set | Pinv/PNAND2/PNAND3/AND2/AND3 | A, B, C | Z | Pinv, PNAND2, PNAND3, AND2, AND3 | gen_inv, gen_nand2, gen_nand4 | gen_nand3 | generated_logic_partial | needs_generated_logic_row_rules |

## Local Macro Availability

| macro | gds | spice | labels | power_metadata | safe_metadata_mapping | safe_physical_placement | notes |
| --- | --- | --- | --- | --- | --- | --- | --- |
| gen_inv | True | False | True | True | True | False | No local SPICE leaf discovered.; Availability supports metadata planning only; decoder row rules and routing remain unproven. |
| gen_delay_inv | True | False | True | True | True | False | No local SPICE leaf discovered. |
| gen_nand2 | True | False | True | True | True | False | No local SPICE leaf discovered.; Availability supports metadata planning only; decoder row rules and routing remain unproven. |
| gen_nand4 | True | False | False | False | True | False | No local SPICE leaf discovered.; GDS exists but label coverage is missing or incomplete in current pin audit.; Power metadata is incomplete in current GDS pin audit.; Availability supports metadata planning only; decoder row rules and routing remain unproven. |
| tri_gate | True | True | True | True | True | False | - |
| dff | True | True | True | True | True | False | DFF is a proven local hardcell, but it is upstream of decoder input handoff rather than a decoder logic leaf. |
| gen_wl_driver | True | False | True | True | True | False | No local SPICE leaf discovered.; Wordline driver semantics were confirmed earlier, but decoder-to-driver routing is still metadata-only. |

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

- DECODER_CASCADE is still metadata-only and is not a pin-proven hard macro.
- No direct local gen_nand3 / AND3 hard macro is available; decoder stage logic remains partially compositional.
- Generated-logic row rules, stage grouping row packing, and power rail strategy are not yet proven for decoder placement.
- Decoder output handoff to WORDLINEDRIVER.A is semantic-only; no physical routing proof exists.
- Control-row physical smoke remains blocked until decoder pin/power/routing evidence exists.

## Step 6.10 Recommendation

- Define decoder generated-logic row rules and per-stage power/pin metadata before any decoder physical placement or control-row smoke.
