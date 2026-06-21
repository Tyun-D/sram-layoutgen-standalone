# OpenYield TIME Control Placement Readiness Report

This is a very-limited abstract readiness audit only. It does not authorize physical placement, standalone integration, routing changes, or GDS generation.

## Audit Summary

```json
{
  "time_control_placement_readiness_available": true,
  "metadata_ready_subblock_count": 11,
  "partial_metadata_subblock_count": 0,
  "can_create_experimental_opt_in_placement_plan": true,
  "can_modify_standalone": false,
  "can_generate_time_control_gds": false,
  "can_enter_physical_placement": false
}
```

## Subblock Readiness

| subblock | category | placement style | metadata ready | physical ready | blocked by |
| --- | --- | --- | --- | --- | --- |
| ADDR_DFF_ROW | latched_address_array | row_based_dff_array | True | False | no legal placement proof, no routing proof, no standalone integration |
| DATA_DFF_ROW | latched_write_data_array | row_based_dff_array | True | False | no legal placement proof, no routing proof, no standalone integration |
| DELAY_CHAIN_CLUSTER | generated_logic_timing_chain | generated_logic_or_stdcell_row | True | False | delay timing proof missing, no legal placement proof, no routing proof |
| WEN_DELAY_CHAIN_CLUSTER | generated_logic_timing_chain | generated_logic_or_stdcell_row | True | False | wen-delay timing proof missing, no legal placement proof, no routing proof |
| PDRIVE_CLUSTER | generated_logic_buffer_chain | generated_logic_or_stdcell_row | True | False | no legal placement proof, no routing proof |
| GENERATED_LOGIC_CLUSTER | nand_and_inverter_logic | stdcell_row_candidate | True | False | stdcell physical library not proven, no legal routing proof, no DRC/LVS proof |
| PRECHARGE_HANDOFF | consumer_macro_handoff | control_to_macro_handoff_only | True | False | rail continuity proof missing, no legal routing proof, no physical placement proof |
| SENSEAMP_HANDOFF | consumer_macro_handoff | control_to_macro_handoff_only | True | False | no legal routing proof, no physical placement proof |
| WRITEDRIVER_HANDOFF | consumer_macro_handoff | control_to_macro_handoff_only | True | False | no legal routing proof, no physical placement proof |
| WORDLINEDRIVER_HANDOFF | consumer_macro_handoff | control_to_macro_handoff_only | True | False | no legal routing proof, no physical placement proof |
| DECODER_INTERFACE | decoder_boundary_handoff | decoder_boundary_only | True | False | decoder placement intentionally untouched, no legal routing proof, no standalone integration |

## Readiness Summary

```json
{
  "metadata_ready_subblocks": [
    "ADDR_DFF_ROW",
    "DATA_DFF_ROW",
    "DELAY_CHAIN_CLUSTER",
    "WEN_DELAY_CHAIN_CLUSTER",
    "PDRIVE_CLUSTER",
    "GENERATED_LOGIC_CLUSTER",
    "PRECHARGE_HANDOFF",
    "SENSEAMP_HANDOFF",
    "WRITEDRIVER_HANDOFF",
    "WORDLINEDRIVER_HANDOFF",
    "DECODER_INTERFACE"
  ],
  "partial_metadata_subblocks": [],
  "physical_blocked_subblocks": [
    "ADDR_DFF_ROW",
    "DATA_DFF_ROW",
    "DELAY_CHAIN_CLUSTER",
    "WEN_DELAY_CHAIN_CLUSTER",
    "PDRIVE_CLUSTER",
    "GENERATED_LOGIC_CLUSTER",
    "PRECHARGE_HANDOFF",
    "SENSEAMP_HANDOFF",
    "WRITEDRIVER_HANDOFF",
    "WORDLINEDRIVER_HANDOFF",
    "DECODER_INTERFACE"
  ],
  "recommended_next_stage": "default_off_experimental_opt_in_prototype_plan"
}
```

## Consistency Checks

| check | value |
| --- | --- |
| time_control_placement_readiness_available | True |
| time_control_metadata_closure_available | True |
| time_control_metadata_chain_complete | True |
| control_region_crossing_coverage_complete | True |
| time_control_region_metadata_planning_available | True |
| precharge_closure_status | intentional_no_local_gnd_metadata_exception |
| metadata_ready_subblock_count | 11 |
| partial_metadata_subblock_count | 0 |
| physical_ready_subblock_count | 0 |
| can_create_experimental_opt_in_placement_plan | True |
| can_modify_standalone | False |
| can_generate_time_control_gds | False |
| can_enter_physical_placement | False |
| safe_for_metadata_prototype_only | True |
| safe_for_physical_placement | False |

## Unresolved Items

- This audit is abstract-to-placement readiness only; it is not legal placement proof.
- No TIME/control routed wires are proven.
- No TIME/control GDS is generated.
- PRECHARGE rail continuity proof is still missing.
- Delay timing proof is missing.
- WEN-delay timing proof is missing.
- Decoder physical placement remains intentionally out of scope.
- Standalone integration remains blocked at this stage.
- No DRC/LVS proof exists for a TIME/control assembly.

## Entry Decisions

- can_create_experimental_opt_in_placement_plan: `True`
- can_modify_standalone: `False`
- can_generate_time_control_gds: `False`
- can_enter_physical_placement: `False`

