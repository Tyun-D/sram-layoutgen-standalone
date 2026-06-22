# OpenYield TIME Control Timing Metadata Report

- Scope: `time_control_timing_metadata_inventory`
- Repo root: `E:\njust\keyan\SRAM Compiler_V2\OpenRAM-stable\deliverables\sram_layoutgen_step45_clean`
- Tech dir: `E:\njust\keyan\SRAM Compiler_V2\OpenRAM-stable\deliverables\sram_layoutgen_step45_clean\technology\freepdk45`

## Audit Summary

```json
{
  "time_control_timing_metadata_inventory_available": true,
  "all_required_timing_objects_analyzed": true,
  "all_stage_counts_recorded_or_missing_noted": true,
  "all_required_timing_model_sources_checked": true,
  "delay_chain_timing_metadata_available": true,
  "wen_delay_chain_timing_metadata_available": true,
  "pdrive_timing_metadata_available": true,
  "enable_path_timing_metadata_available": true,
  "precharge_timing_exception_retained": true,
  "dff_row_clock_timing_metadata_available": true,
  "timing_proof_available_now": false,
  "can_enter_timing_proof_planning": true,
  "can_enter_physical_timing_closure_now": false,
  "can_enter_routing_proof_planning": true,
  "can_enter_physical_routing_now": false,
  "can_enter_physical_placement_now": false,
  "can_generate_time_control_gds_now": false,
  "can_modify_standalone_now": false
}
```

## Input Reports And Assets

```json
{
  "routing_obstacle": "E:\\njust\\keyan\\SRAM Compiler_V2\\OpenRAM-stable\\deliverables\\sram_layoutgen_step45_clean\\docs\\openyield_time_control_routing_obstacle_report.json",
  "legal_placement_readonly": "E:\\njust\\keyan\\SRAM Compiler_V2\\OpenRAM-stable\\deliverables\\sram_layoutgen_step45_clean\\docs\\openyield_time_control_legal_placement_readonly_report.json",
  "composite_feasibility": "E:\\njust\\keyan\\SRAM Compiler_V2\\OpenRAM-stable\\deliverables\\sram_layoutgen_step45_clean\\docs\\openyield_time_control_composite_feasibility_report.json",
  "leaf_inventory": "E:\\njust\\keyan\\SRAM Compiler_V2\\OpenRAM-stable\\deliverables\\sram_layoutgen_step45_clean\\docs\\openyield_time_control_leaf_inventory_report.json",
  "generated_logic_contracts": "E:\\njust\\keyan\\SRAM Compiler_V2\\OpenRAM-stable\\deliverables\\sram_layoutgen_step45_clean\\docs\\openyield_time_control_generated_logic_contract_report.json",
  "signal_bindings": "E:\\njust\\keyan\\SRAM Compiler_V2\\OpenRAM-stable\\deliverables\\sram_layoutgen_step45_clean\\docs\\openyield_time_control_signal_binding_report.json",
  "repo_asset_inventory": "E:\\njust\\keyan\\SRAM Compiler_V2\\OpenRAM-stable\\deliverables\\sram_layoutgen_step45_clean\\docs\\openyield_repo_physical_asset_inventory_report.json",
  "subblock_audit": "E:\\njust\\keyan\\SRAM Compiler_V2\\OpenRAM-stable\\deliverables\\sram_layoutgen_step45_clean\\docs\\openyield_time_control_subblock_audit_report.json"
}
```

## Timing Object Table

| object | role | stage | leafs | spice | load model | classification | timing proof |
| --- | --- | --- | --- | --- | --- | --- | --- |
| DELAY_CHAIN | replica_bitline_delay / rbl_delay_generation | 9 | gen_delay_inv | False | source_confirmed_four_load_inverters_per_stage | blocked_by_missing_spice_or_lib | False |
| WEN_DELAY_CHAIN | write_enable_delay_conditioning | 6 | gen_delay_inv | False | conditional_write_branch_load_present_but_not_quantified_for_general_configs | blocked_by_missing_spice_or_lib | False |
| PDRIVE | clock_buffer_chain | 4 | gen_inv | False | consumer_fanout_known_metadata_only | blocked_by_missing_spice_or_lib | False |
| PDRIVE2_FOR_PRE | precharge_enable_buffer_chain | 2 | gen_inv | False | consumer_fanout_known_metadata_only | blocked_by_precharge_power_exception | False |
| WL_PDRIVE | wordline_enable_buffer_chain | 2 | gen_inv | False | consumer_fanout_known_metadata_only | blocked_by_missing_spice_or_lib | False |
| PINV | single_inversion_helper | 1 | gen_inv | False | binding_level_consumer_list_known | blocked_by_missing_spice_or_lib | False |
| AND2 | gated_clock_generation | 2 | gen_nand2, gen_inv | False | binding_level_consumer_list_known | blocked_by_missing_spice_or_lib | False |
| AND3_COMPOSITE | enable_logic_generation | 4 | gen_nand2, gen_inv | False | binding_level_consumer_list_known | blocked_by_missing_spice_or_lib | False |
| PNAND3_COMPOSITE | precharge_gating_generation | 3 | gen_nand2, gen_inv | False | binding_level_consumer_list_known | blocked_by_precharge_power_exception | False |
| PRECHARGE | precharge_consumer_handoff | 1 | gen_precharge | False | None | blocked_by_precharge_power_exception | False |
| DFF_ROW | clocked_register_row | 1 | dff | True | None | blocked_by_standalone_clock_integration | False |
| WRITE_ENABLE_PATH | consumer_enable_path | None |  | False | path_dependency_known_but_numeric_load_unproven | blocked_by_missing_stage_count | False |
| SENSE_ENABLE_PATH | consumer_enable_path | None |  | False | path_dependency_known_but_numeric_load_unproven | blocked_by_missing_stage_count | False |
| PRECHARGE_ENABLE_PATH | consumer_enable_path | None |  | False | path_dependency_known_but_numeric_load_unproven | blocked_by_precharge_power_exception | False |
| WORDLINE_ENABLE_PATH | consumer_enable_path | None |  | False | path_dependency_known_but_numeric_load_unproven | blocked_by_missing_stage_count | False |
| RBL_DELAY_PATH | replica_delay_path | None |  | False | path_dependency_known_but_numeric_load_unproven | blocked_by_missing_stage_count | False |
| GATED_CLOCK_PATH | gated_clock_path | None |  | False | path_dependency_known_but_numeric_load_unproven | blocked_by_standalone_clock_integration | False |

## Delay Chain Timing Metadata

```json
{
  "timing_object": "DELAY_CHAIN",
  "timing_role": "replica_bitline_delay / rbl_delay_generation",
  "source_contract": "DELAY_CHAIN_GENERATED_LOGIC_CONTRACT",
  "source_signals": [
    "rbl"
  ],
  "target_signals": [
    "rbl_delay",
    "Pinv.A",
    "AND3.A",
    "PNAND3.B"
  ],
  "leaf_sequence": [
    "gen_delay_inv",
    "gen_delay_inv",
    "gen_delay_inv",
    "gen_delay_inv",
    "gen_delay_inv",
    "gen_delay_inv",
    "gen_delay_inv",
    "gen_delay_inv",
    "gen_delay_inv"
  ],
  "stage_count": 9,
  "stage_count_source": "generated_logic_contract.candidate_cell_count_if_known",
  "known_leaf_macro": [
    "gen_delay_inv"
  ],
  "leaf_has_spice": false,
  "leaf_has_lib": false,
  "known_cell_delay_model": false,
  "known_load_model": "source_confirmed_four_load_inverters_per_stage",
  "known_input_slew_model": null,
  "known_output_load_model": "consumer_pin_list_known_metadata_only",
  "known_rc_model": null,
  "known_corner_definition": null,
  "known_voltage_temperature_corner": null,
  "requires_spice": true,
  "requires_liberty": true,
  "requires_parasitic_estimate": true,
  "requires_routing_rc": true,
  "requires_load_extraction": true,
  "requires_replica_path_calibration": true,
  "requires_waveform_check": true,
  "requires_margin_policy": true,
  "requires_write_path_timing_model": false,
  "timing_metadata_available": true,
  "timing_proof_available": false,
  "safe_for_timing_metadata_planning": true,
  "safe_for_timing_proof_planning": true,
  "safe_for_timing_closure": false,
  "timing_proof_readiness_classification": "blocked_by_missing_spice_or_lib",
  "consumer_macro": null,
  "consumer_pin": null,
  "consumer_pin_side": null,
  "notes": [
    "Stage count source-confirmed as 9.",
    "Load model is known at source level: four load inverters per stage.",
    "OpenYield source defines a nine-stage inverter delay chain with four load inverters per stage.",
    "TIME instantiates DelayChain from rbl to rbl_delay.",
    "This contract is especially timing-sensitive and must remain metadata-only until delay proof exists."
  ],
  "blockers": [
    "missing spice or lib for generated/control leaf",
    "timing proof is missing",
    "no SPICE timing closure has been run",
    "replica calibration required"
  ]
}
```

## WEN Delay Chain Timing Metadata

```json
{
  "timing_object": "WEN_DELAY_CHAIN",
  "timing_role": "write_enable_delay_conditioning",
  "source_contract": "WEN_DELAY_CHAIN_CONDITIONAL_GENERATED_LOGIC_CONTRACT",
  "source_signals": [
    "rbl_delay_bar"
  ],
  "target_signals": [
    "rbl_delay_bar_wen",
    "AND3.A via w_en_rbl_input"
  ],
  "leaf_sequence": [
    "gen_delay_inv",
    "gen_delay_inv",
    "gen_delay_inv",
    "gen_delay_inv",
    "gen_delay_inv",
    "gen_delay_inv"
  ],
  "stage_count": 6,
  "stage_count_source": "generated_logic_contract.candidate_cell_count_if_known",
  "known_leaf_macro": [
    "gen_delay_inv"
  ],
  "leaf_has_spice": false,
  "leaf_has_lib": false,
  "known_cell_delay_model": false,
  "known_load_model": "conditional_write_branch_load_present_but_not_quantified_for_general_configs",
  "known_input_slew_model": null,
  "known_output_load_model": "consumer_pin_list_known_metadata_only",
  "known_rc_model": null,
  "known_corner_definition": null,
  "known_voltage_temperature_corner": null,
  "requires_spice": true,
  "requires_liberty": true,
  "requires_parasitic_estimate": true,
  "requires_routing_rc": true,
  "requires_load_extraction": true,
  "requires_replica_path_calibration": false,
  "requires_waveform_check": true,
  "requires_margin_policy": true,
  "requires_write_path_timing_model": true,
  "timing_metadata_available": true,
  "timing_proof_available": false,
  "safe_for_timing_metadata_planning": true,
  "safe_for_timing_proof_planning": true,
  "safe_for_timing_closure": false,
  "timing_proof_readiness_classification": "blocked_by_missing_spice_or_lib",
  "consumer_macro": null,
  "consumer_pin": null,
  "consumer_pin_side": null,
  "notes": [
    "Conditional applicability preserved exactly: operation == write and num_rows == 16 and num_cols == 512.",
    "This contract must not generalize to all configs.",
    "The chain is only instantiated in the special-case `write` + `16x512` branch.",
    "This keeps the adapter audit at source-semantic level; the general path still uses rbl_delay_bar directly.",
    "This contract is partial/conditional by design and must not be generalized beyond the source-confirmed branch."
  ],
  "blockers": [
    "missing spice or lib for generated/control leaf",
    "timing proof is missing",
    "no SPICE timing closure has been run",
    "write path timing model required"
  ]
}
```

## Pdrive / Wordline / Precharge Drive Metadata

| object | stage | source | targets | classification |
| --- | --- | --- | --- | --- |
| PDRIVE | 4 | clk | clk_buf, ADDR_DFF.CLK, DATA_DFF.CLK, DFF_BUF.CLK, Pinv.A, AND2.B | blocked_by_missing_spice_or_lib |
| PDRIVE2_FOR_PRE | 2 | gated_clk_buf, rbl_delay, wl_en_bar | PRE, PRECHARGE.ENB | blocked_by_precharge_power_exception |
| WL_PDRIVE | 2 | gated_clk_bar | wl_en, WORDLINEDRIVER.B, Pinv.A(wl_en_bar), RWL_AND2.B | blocked_by_missing_spice_or_lib |
| PRECHARGE_ENABLE_PATH | None | gated_clk_buf, rbl_delay, wl_en_bar | PRE, PRECHARGE.ENB | blocked_by_precharge_power_exception |
| WORDLINE_ENABLE_PATH | None | gated_clk_bar | wl_en, WORDLINEDRIVER.B, Pinv.A(wl_en_bar), RWL_AND2.B | blocked_by_missing_stage_count |

## Write / Sense Enable Path Timing Metadata

| object | consumer | pin | pin side | classification |
| --- | --- | --- | --- | --- |
| WRITE_ENABLE_PATH | write_driver | EN | bottom | blocked_by_missing_stage_count |
| SENSE_ENABLE_PATH | sense_amp | EN | top | blocked_by_missing_stage_count |

## DFF Row / Gated Clock Timing Metadata

| object | source | targets | classification | blockers |
| --- | --- | --- | --- | --- |
| DFF_ROW |  |  | blocked_by_standalone_clock_integration | missing load model; timing proof is missing; no SPICE timing closure has been run; standalone clock integration required |
| GATED_CLOCK_PATH | clk, clk_buf, cs, clk_bar | clk_buf, ADDR_DFF.CLK, DATA_DFF.CLK, DFF_BUF.CLK, Pinv.A, AND2.B, clk_bar, gated_clk_buf, PNAND3.A, gated_clk_bar, WL_PDRIVE.A, AND3.B | blocked_by_standalone_clock_integration | stage count missing; timing proof is missing; no SPICE timing closure has been run; standalone clock integration required |

## SPICE / LIB / Model Inventory

| macro | spice | lib | subckt | power pins | delay model | usable now |
| --- | --- | --- | --- | --- | --- | --- |
| gen_inv | False | False | None | False | False | False |
| gen_nand2 | False | False | None | False | False | False |
| gen_delay_inv | False | False | None | False | False | False |
| gen_precharge | False | False | None | False | False | False |
| dff | True | False | dff | True | False | False |
| sense_amp | True | False | sense_amp | True | False | False |
| write_driver | True | False | write_driver | True | False | False |
| gen_wl_driver | False | False | None | False | False | False |
| gen_col_mux_vdd_labeled | False | False | None | False | False | False |
| cell_1rw | True | False | cell_1rw | True | False | False |
| replica_cell_1rw | True | False | replica_cell_1rw | True | False | False |

## Timing Proof Readiness Classification

| object | classification | metadata planning | proof planning | closure |
| --- | --- | --- | --- | --- |
| DELAY_CHAIN | blocked_by_missing_spice_or_lib | True | True | False |
| WEN_DELAY_CHAIN | blocked_by_missing_spice_or_lib | True | True | False |
| PDRIVE | blocked_by_missing_spice_or_lib | True | True | False |
| PDRIVE2_FOR_PRE | blocked_by_precharge_power_exception | True | True | False |
| WL_PDRIVE | blocked_by_missing_spice_or_lib | True | True | False |
| PINV | blocked_by_missing_spice_or_lib | True | True | False |
| AND2 | blocked_by_missing_spice_or_lib | True | True | False |
| AND3_COMPOSITE | blocked_by_missing_spice_or_lib | True | True | False |
| PNAND3_COMPOSITE | blocked_by_precharge_power_exception | True | True | False |
| PRECHARGE | blocked_by_precharge_power_exception | True | True | False |
| DFF_ROW | blocked_by_standalone_clock_integration | True | True | False |
| WRITE_ENABLE_PATH | blocked_by_missing_stage_count | True | True | False |
| SENSE_ENABLE_PATH | blocked_by_missing_stage_count | True | True | False |
| PRECHARGE_ENABLE_PATH | blocked_by_precharge_power_exception | True | True | False |
| WORDLINE_ENABLE_PATH | blocked_by_missing_stage_count | True | True | False |
| RBL_DELAY_PATH | blocked_by_missing_stage_count | True | True | False |
| GATED_CLOCK_PATH | blocked_by_standalone_clock_integration | True | True | False |

## Blockers

- DELAY_CHAIN: missing spice or lib for generated/control leaf
- DELAY_CHAIN: timing proof is missing
- DELAY_CHAIN: no SPICE timing closure has been run
- DELAY_CHAIN: replica calibration required
- WEN_DELAY_CHAIN: missing spice or lib for generated/control leaf
- WEN_DELAY_CHAIN: timing proof is missing
- WEN_DELAY_CHAIN: no SPICE timing closure has been run
- WEN_DELAY_CHAIN: write path timing model required
- PDRIVE: missing spice or lib for generated/control leaf
- PDRIVE: timing proof is missing
- PDRIVE: no SPICE timing closure has been run
- PDRIVE2_FOR_PRE: missing spice or lib for generated/control leaf
- PDRIVE2_FOR_PRE: timing proof is missing
- PDRIVE2_FOR_PRE: no SPICE timing closure has been run
- PDRIVE2_FOR_PRE: precharge power exception retained
- WL_PDRIVE: missing spice or lib for generated/control leaf
- WL_PDRIVE: timing proof is missing
- WL_PDRIVE: no SPICE timing closure has been run
- PINV: missing spice or lib for generated/control leaf
- PINV: timing proof is missing
- PINV: no SPICE timing closure has been run
- AND2: missing spice or lib for generated/control leaf
- AND2: timing proof is missing
- AND2: no SPICE timing closure has been run
- AND3_COMPOSITE: missing spice or lib for generated/control leaf
- AND3_COMPOSITE: timing proof is missing
- AND3_COMPOSITE: no SPICE timing closure has been run
- PNAND3_COMPOSITE: missing spice or lib for generated/control leaf
- PNAND3_COMPOSITE: timing proof is missing
- PNAND3_COMPOSITE: no SPICE timing closure has been run
- PNAND3_COMPOSITE: precharge power exception retained
- PRECHARGE: missing spice or lib for generated/control leaf
- PRECHARGE: missing load model
- PRECHARGE: timing proof is missing
- PRECHARGE: no SPICE timing closure has been run
- PRECHARGE: precharge power exception retained
- DFF_ROW: missing load model
- DFF_ROW: timing proof is missing
- DFF_ROW: no SPICE timing closure has been run
- DFF_ROW: standalone clock integration required
- WRITE_ENABLE_PATH: stage count missing
- WRITE_ENABLE_PATH: timing proof is missing
- WRITE_ENABLE_PATH: no SPICE timing closure has been run
- SENSE_ENABLE_PATH: stage count missing
- SENSE_ENABLE_PATH: timing proof is missing
- SENSE_ENABLE_PATH: no SPICE timing closure has been run
- PRECHARGE_ENABLE_PATH: stage count missing
- PRECHARGE_ENABLE_PATH: timing proof is missing
- PRECHARGE_ENABLE_PATH: no SPICE timing closure has been run
- PRECHARGE_ENABLE_PATH: precharge power exception retained
- WORDLINE_ENABLE_PATH: stage count missing
- WORDLINE_ENABLE_PATH: timing proof is missing
- WORDLINE_ENABLE_PATH: no SPICE timing closure has been run
- RBL_DELAY_PATH: stage count missing
- RBL_DELAY_PATH: timing proof is missing
- RBL_DELAY_PATH: no SPICE timing closure has been run
- RBL_DELAY_PATH: replica calibration required
- GATED_CLOCK_PATH: stage count missing
- GATED_CLOCK_PATH: timing proof is missing
- GATED_CLOCK_PATH: no SPICE timing closure has been run
- GATED_CLOCK_PATH: standalone clock integration required

## Boundary Assertions

```json
{
  "stage_count_known_is_not_delay_proof": true,
  "leaf_sequence_known_is_not_timing_proof": true,
  "spice_exists_is_not_timing_closure": true,
  "routing_obstacle_inventory_is_not_parasitic_extraction": true,
  "timing_metadata_planning_is_not_timing_proof": true,
  "standalone_modified": false,
  "routing_modified": false,
  "gds_writer_modified": false
}
```