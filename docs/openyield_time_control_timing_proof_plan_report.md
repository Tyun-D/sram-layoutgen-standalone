# OpenYield TIME Control Timing Proof Planning Report

- Scope: `time_control_timing_proof_planning`
- Repo root: `E:\njust\keyan\SRAM Compiler_V2\OpenRAM-stable\deliverables\sram_layoutgen_step45_clean`
- Tech dir: `E:\njust\keyan\SRAM Compiler_V2\OpenRAM-stable\deliverables\sram_layoutgen_step45_clean\technology\freepdk45`

## Audit Summary

```json
{
  "time_control_timing_proof_planning_available": true,
  "all_required_timing_proof_targets_planned": true,
  "all_required_models_identified": true,
  "model_recovery_plan_available": true,
  "proof_task_ranking_available": true,
  "can_start_timing_proof_without_main_flow_changes": true,
  "can_enter_generated_logic_model_recovery": true,
  "can_enter_delay_chain_testbench_planning": true,
  "timing_proof_available_now": false,
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
  "timing_metadata": "E:\\njust\\keyan\\SRAM Compiler_V2\\OpenRAM-stable\\deliverables\\sram_layoutgen_step45_clean\\docs\\openyield_time_control_timing_metadata_report.json",
  "routing_obstacle": "E:\\njust\\keyan\\SRAM Compiler_V2\\OpenRAM-stable\\deliverables\\sram_layoutgen_step45_clean\\docs\\openyield_time_control_routing_obstacle_report.json",
  "legal_placement_readonly": "E:\\njust\\keyan\\SRAM Compiler_V2\\OpenRAM-stable\\deliverables\\sram_layoutgen_step45_clean\\docs\\openyield_time_control_legal_placement_readonly_report.json",
  "asset_inventory": "E:\\njust\\keyan\\SRAM Compiler_V2\\OpenRAM-stable\\deliverables\\sram_layoutgen_step45_clean\\docs\\openyield_repo_physical_asset_inventory_report.json"
}
```

## Timing Proof Target Plan Table

| object | classification | readiness | next action | proof now | closure now |
| --- | --- | --- | --- | --- | --- |
| DELAY_CHAIN | blocked_by_missing_spice_or_lib | planning_ready_model_recovery_needed | recover_or_characterize_gen_delay_inv_timing_model | False | False |
| WEN_DELAY_CHAIN | blocked_by_missing_spice_or_lib | planning_ready_model_recovery_needed | plan_conditional_wen_delay_chain_testbench_for_write_16x512 | False | False |
| PDRIVE | blocked_by_missing_spice_or_lib | planning_ready_model_recovery_needed | recover_generated_logic_spice_or_timing_model_inventory | False | False |
| PDRIVE2_FOR_PRE | blocked_by_precharge_power_exception | planning_only_precharge_exception | recover_generated_logic_spice_or_timing_model_inventory | False | False |
| WL_PDRIVE | blocked_by_missing_spice_or_lib | planning_ready_model_recovery_needed | recover_generated_logic_spice_or_timing_model_inventory | False | False |
| PINV | blocked_by_missing_spice_or_lib | planning_ready_model_recovery_needed | recover_generated_logic_spice_or_timing_model_inventory | False | False |
| AND2 | blocked_by_missing_spice_or_lib | planning_ready_model_recovery_needed | recover_generated_logic_spice_or_timing_model_inventory | False | False |
| AND3_COMPOSITE | blocked_by_missing_spice_or_lib | planning_ready_model_recovery_needed | recover_generated_logic_spice_or_timing_model_inventory | False | False |
| PNAND3_COMPOSITE | blocked_by_precharge_power_exception | planning_only_precharge_exception | recover_generated_logic_spice_or_timing_model_inventory | False | False |
| PRECHARGE | blocked_by_precharge_power_exception | planning_only_precharge_exception | retain_precharge_exception_and_plan_power_resolution_inputs | False | False |
| DFF_ROW | blocked_by_standalone_clock_integration | planning_ready_clock_model_missing | prepare_dff_clock_path_model_plan | False | False |
| WRITE_ENABLE_PATH | blocked_by_missing_stage_count | planning_ready_path_resolution_needed | define_consumer_enable_pin_load_and_enable_window_model | False | False |
| SENSE_ENABLE_PATH | blocked_by_missing_stage_count | planning_ready_path_resolution_needed | define_consumer_enable_pin_load_and_enable_window_model | False | False |
| PRECHARGE_ENABLE_PATH | blocked_by_precharge_power_exception | planning_only_precharge_exception | retain_precharge_exception_and_plan_power_resolution_inputs | False | False |
| WORDLINE_ENABLE_PATH | blocked_by_missing_stage_count | planning_ready_path_resolution_needed | define_wordline_enable_consumer_load_model | False | False |
| RBL_DELAY_PATH | blocked_by_missing_stage_count | planning_ready_path_resolution_needed | combine_delay_chain_and_rbl_consumer_rc_assumptions | False | False |
| GATED_CLOCK_PATH | blocked_by_standalone_clock_integration | planning_ready_clock_model_missing | prepare_dff_clock_path_model_plan | False | False |

## DELAY_CHAIN Proof Plan

```json
{
  "timing_object": "DELAY_CHAIN",
  "current_metadata_status": "available",
  "current_blocker_classification": "blocked_by_missing_spice_or_lib",
  "required_spice_models": [
    "gen_delay_inv"
  ],
  "required_liberty_models": [
    "gen_delay_inv.lib_or_equivalent_delay_model"
  ],
  "required_load_models": [
    "source_confirmed_four_load_inverters_per_stage",
    "four_load_inverters_per_stage"
  ],
  "required_rc_models": [
    "interconnect_rc_extraction_or_bounded_estimate",
    "replica_bitline_rc_model"
  ],
  "required_corner_definitions": [
    "PVT_corner_definition",
    "replica_delay_margin_corner"
  ],
  "required_waveform_checks": [
    "waveform_shape_and_pulse_width_check"
  ],
  "required_replica_calibration": true,
  "required_consumer_pin_loads": [],
  "required_input_slew_assumptions": [
    "rbl_input_slew"
  ],
  "required_output_load_assumptions": [
    "distributed_inverter_load_plus_consumer_pin_load"
  ],
  "required_path_endpoints": [
    "rbl -> rbl_delay"
  ],
  "required_success_metric": "bounded delay across corners with replica calibration and waveform integrity",
  "minimal_proof_setup": [
    "reuse current metadata report as structural source of truth",
    "bind leaf macro names and consumer endpoints exactly as reported",
    "declare PVT corner set and success metric before simulation",
    "prepare chain-level SPICE or equivalent delay model for gen_delay_inv",
    "instantiate declared stages with explicit load-per-stage assumptions",
    "include interconnect RC estimate and waveform probes"
  ],
  "proof_steps": [
    "inventory required models, loads, corners, and route abstractions",
    "recover_or_characterize_gen_delay_inv_timing_model",
    "build target-specific testbench or equivalent delay abstraction",
    "calibrate replica path assumptions against rbl/load model",
    "run per-corner delay/slew/waveform measurement",
    "compare measured results against declared success metric",
    "record proof artifact boundaries and unresolved assumptions"
  ],
  "readiness_level": "planning_ready_model_recovery_needed",
  "can_start_proof_without_main_flow_changes": true,
  "requires_standalone_integration": false,
  "requires_routing_extraction": true,
  "requires_physical_layout": false,
  "requires_precharge_power_resolution": false,
  "can_claim_timing_proof_now": false,
  "can_claim_timing_closure_now": false,
  "blockers": [
    "missing spice or lib for generated/control leaf",
    "timing proof is missing",
    "no SPICE timing closure has been run",
    "replica calibration required",
    "gen_delay_inv timing model missing"
  ],
  "next_minimal_action": "recover_or_characterize_gen_delay_inv_timing_model",
  "notes": [
    "Stage count source-confirmed as 9.",
    "Load model is known at source level: four load inverters per stage.",
    "OpenYield source defines a nine-stage inverter delay chain with four load inverters per stage.",
    "TIME instantiates DelayChain from rbl to rbl_delay.",
    "This contract is especially timing-sensitive and must remain metadata-only until delay proof exists.",
    "stage_count = 9",
    "leaf = gen_delay_inv",
    "load_model_needed = four_load_inverters_per_stage",
    "requires_gen_delay_inv_spice_or_equivalent_model = True",
    "requires_input_slew = True",
    "requires_output_load = True",
    "requires_corner_definition = True",
    "requires_replica_path_calibration = True",
    "requires_routing_rc = True",
    "requires_waveform_check = True",
    "can_claim_delay_proof_now = False"
  ]
}
```

## WEN_DELAY_CHAIN Proof Plan

```json
{
  "timing_object": "WEN_DELAY_CHAIN",
  "current_metadata_status": "available",
  "current_blocker_classification": "blocked_by_missing_spice_or_lib",
  "required_spice_models": [
    "gen_delay_inv"
  ],
  "required_liberty_models": [
    "gen_delay_inv.lib_or_equivalent_delay_model"
  ],
  "required_load_models": [
    "conditional_write_branch_load_present_but_not_quantified_for_general_configs",
    "conditional_write_branch_load_for_write_16x512_only"
  ],
  "required_rc_models": [
    "interconnect_rc_extraction_or_bounded_estimate"
  ],
  "required_corner_definitions": [
    "PVT_corner_definition",
    "replica_delay_margin_corner"
  ],
  "required_waveform_checks": [
    "waveform_shape_and_pulse_width_check"
  ],
  "required_replica_calibration": false,
  "required_consumer_pin_loads": [],
  "required_input_slew_assumptions": [
    "rbl_delay_bar_input_slew"
  ],
  "required_output_load_assumptions": [
    "conditional_write_branch_consumer_load"
  ],
  "required_path_endpoints": [
    "rbl_delay_bar -> rbl_delay_bar_wen -> w_en path"
  ],
  "required_success_metric": "conditional write-only delay proof for 16x512 without over-generalization",
  "minimal_proof_setup": [
    "reuse current metadata report as structural source of truth",
    "bind leaf macro names and consumer endpoints exactly as reported",
    "declare PVT corner set and success metric before simulation",
    "prepare chain-level SPICE or equivalent delay model for gen_delay_inv",
    "instantiate declared stages with explicit load-per-stage assumptions",
    "include interconnect RC estimate and waveform probes"
  ],
  "proof_steps": [
    "inventory required models, loads, corners, and route abstractions",
    "preserve conditional scope: write + 16x512 only",
    "build target-specific testbench or equivalent delay abstraction",
    "run per-corner delay/slew/waveform measurement",
    "compare measured results against declared success metric",
    "record proof artifact boundaries and unresolved assumptions"
  ],
  "readiness_level": "planning_ready_model_recovery_needed",
  "can_start_proof_without_main_flow_changes": true,
  "requires_standalone_integration": false,
  "requires_routing_extraction": true,
  "requires_physical_layout": false,
  "requires_precharge_power_resolution": false,
  "can_claim_timing_proof_now": false,
  "can_claim_timing_closure_now": false,
  "blockers": [
    "missing spice or lib for generated/control leaf",
    "timing proof is missing",
    "no SPICE timing closure has been run",
    "write path timing model required",
    "conditional write-branch model missing"
  ],
  "next_minimal_action": "plan_conditional_wen_delay_chain_testbench_for_write_16x512",
  "notes": [
    "Conditional applicability preserved exactly: operation == write and num_rows == 16 and num_cols == 512.",
    "This contract must not generalize to all configs.",
    "The chain is only instantiated in the special-case `write` + `16x512` branch.",
    "This keeps the adapter audit at source-semantic level; the general path still uses rbl_delay_bar directly.",
    "This contract is partial/conditional by design and must not be generalized beyond the source-confirmed branch.",
    "stage_count = 6",
    "leaf = gen_delay_inv",
    "conditional_scope = write + 16x512 only",
    "requires_write_path_timing_model = True",
    "requires_gen_delay_inv_model = True",
    "requires_rc = True",
    "requires_waveform_check = True",
    "can_claim_wen_delay_proof_now = False"
  ]
}
```

## PDRIVE / WL_PDRIVE / PRE Drive Proof Plan

```json
[
  {
    "timing_object": "PDRIVE",
    "current_metadata_status": "available",
    "current_blocker_classification": "blocked_by_missing_spice_or_lib",
    "required_spice_models": [
      "gen_inv"
    ],
    "required_liberty_models": [
      "gen_inv.lib_or_equivalent_delay_model"
    ],
    "required_load_models": [
      "consumer_fanout_known_metadata_only",
      "fanout_load_model",
      "target_pin_load_model"
    ],
    "required_rc_models": [
      "interconnect_rc_extraction_or_bounded_estimate"
    ],
    "required_corner_definitions": [
      "PVT_corner_definition"
    ],
    "required_waveform_checks": [],
    "required_replica_calibration": false,
    "required_consumer_pin_loads": [],
    "required_input_slew_assumptions": [
      "clk_input_slew"
    ],
    "required_output_load_assumptions": [
      "clock_fanout_output_load"
    ],
    "required_path_endpoints": [
      "clk",
      "clk_buf",
      "ADDR_DFF.CLK",
      "DATA_DFF.CLK",
      "DFF_BUF.CLK",
      "Pinv.A",
      "AND2.B"
    ],
    "required_success_metric": "clock buffer chain delay/slew bound at all named consumers",
    "minimal_proof_setup": [
      "reuse current metadata report as structural source of truth",
      "bind leaf macro names and consumer endpoints exactly as reported",
      "declare PVT corner set and success metric before simulation",
      "prepare generated-logic leaf model inventory",
      "construct focused path-level testbench with declared fanout/load assumptions"
    ],
    "proof_steps": [
      "inventory required models, loads, corners, and route abstractions",
      "build target-specific testbench or equivalent delay abstraction",
      "run per-corner delay/slew/waveform measurement",
      "compare measured results against declared success metric",
      "record proof artifact boundaries and unresolved assumptions"
    ],
    "readiness_level": "planning_ready_model_recovery_needed",
    "can_start_proof_without_main_flow_changes": true,
    "requires_standalone_integration": false,
    "requires_routing_extraction": true,
    "requires_physical_layout": false,
    "requires_precharge_power_resolution": false,
    "can_claim_timing_proof_now": false,
    "can_claim_timing_closure_now": false,
    "blockers": [
      "missing spice or lib for generated/control leaf",
      "timing proof is missing",
      "no SPICE timing closure has been run",
      "generated logic fanout load model missing"
    ],
    "next_minimal_action": "recover_generated_logic_spice_or_timing_model_inventory",
    "notes": [
      "Stage count source-confirmed as 4.",
      "Drive-strength progression is known from source and preserved only as metadata notes.",
      "The source is a four-stage inverter chain with progressive upsizing.",
      "TIME uses pdrive to generate clk_buf, then a separate inverter derives clk_bar.",
      "Producer is a four-stage inverter chain with upsizing.",
      "This contract can drive planning metadata but not physical control placement.",
      "requires_gen_inv_timing_model = True",
      "requires_fanout_load_model = True",
      "requires_target_pin_load = True",
      "requires_routing_rc = True",
      "pdrive_timing_proof_available_now = False"
    ]
  },
  {
    "timing_object": "WL_PDRIVE",
    "current_metadata_status": "available",
    "current_blocker_classification": "blocked_by_missing_spice_or_lib",
    "required_spice_models": [
      "gen_inv",
      "gen_wl_driver"
    ],
    "required_liberty_models": [
      "gen_inv.lib_or_equivalent_delay_model",
      "gen_wl_driver.lib_or_equivalent_delay_model"
    ],
    "required_load_models": [
      "consumer_fanout_known_metadata_only",
      "fanout_load_model",
      "target_pin_load_model"
    ],
    "required_rc_models": [
      "interconnect_rc_extraction_or_bounded_estimate"
    ],
    "required_corner_definitions": [
      "PVT_corner_definition"
    ],
    "required_waveform_checks": [],
    "required_replica_calibration": false,
    "required_consumer_pin_loads": [],
    "required_input_slew_assumptions": [
      "gated_clk_bar_input_slew"
    ],
    "required_output_load_assumptions": [
      "wordline_enable_output_load"
    ],
    "required_path_endpoints": [
      "gated_clk_bar",
      "wl_en",
      "WORDLINEDRIVER.B",
      "Pinv.A(wl_en_bar)",
      "RWL_AND2.B"
    ],
    "required_success_metric": "wl_en arrival and slew bound at wordline-enable consumers",
    "minimal_proof_setup": [
      "reuse current metadata report as structural source of truth",
      "bind leaf macro names and consumer endpoints exactly as reported",
      "declare PVT corner set and success metric before simulation",
      "prepare generated-logic leaf model inventory",
      "construct focused path-level testbench with declared fanout/load assumptions"
    ],
    "proof_steps": [
      "inventory required models, loads, corners, and route abstractions",
      "build target-specific testbench or equivalent delay abstraction",
      "run per-corner delay/slew/waveform measurement",
      "compare measured results against declared success metric",
      "record proof artifact boundaries and unresolved assumptions"
    ],
    "readiness_level": "planning_ready_model_recovery_needed",
    "can_start_proof_without_main_flow_changes": true,
    "requires_standalone_integration": false,
    "requires_routing_extraction": true,
    "requires_physical_layout": false,
    "requires_precharge_power_resolution": false,
    "can_claim_timing_proof_now": false,
    "can_claim_timing_closure_now": false,
    "blockers": [
      "missing spice or lib for generated/control leaf",
      "timing proof is missing",
      "no SPICE timing closure has been run",
      "generated logic fanout load model missing"
    ],
    "next_minimal_action": "recover_generated_logic_spice_or_timing_model_inventory",
    "notes": [
      "Stage count source-confirmed as 2.",
      "wordline_enable active-high semantics are preserved.",
      "The source is a two-stage inverter chain that drives wl_en from gated_clk_bar.",
      "The testbench and earlier wordline audit confirm wl_en feeds the WordlineDriver B domain as active-high enable.",
      "The active-high interpretation is source-confirmed and consistent with the prior WORDLINEDRIVER adapter audit.",
      "requires_gen_inv_timing_model = True",
      "requires_fanout_load_model = True",
      "requires_target_pin_load = True",
      "requires_routing_rc = True",
      "pdrive_timing_proof_available_now = False"
    ]
  },
  {
    "timing_object": "PDRIVE2_FOR_PRE",
    "current_metadata_status": "available",
    "current_blocker_classification": "blocked_by_precharge_power_exception",
    "required_spice_models": [
      "gen_inv"
    ],
    "required_liberty_models": [
      "gen_inv.lib_or_equivalent_delay_model"
    ],
    "required_load_models": [
      "consumer_fanout_known_metadata_only",
      "fanout_load_model",
      "target_pin_load_model"
    ],
    "required_rc_models": [
      "interconnect_rc_extraction_or_bounded_estimate"
    ],
    "required_corner_definitions": [
      "PVT_corner_definition"
    ],
    "required_waveform_checks": [
      "active_low_precharge_enable_waveform_check"
    ],
    "required_replica_calibration": false,
    "required_consumer_pin_loads": [],
    "required_input_slew_assumptions": [
      "pre_unbuf_input_slew"
    ],
    "required_output_load_assumptions": [
      "precharge_enable_output_load"
    ],
    "required_path_endpoints": [
      "gated_clk_buf",
      "rbl_delay",
      "wl_en_bar",
      "PRE",
      "PRECHARGE.ENB"
    ],
    "required_success_metric": "PRE driver delay/slew bound with precharge exception explicitly retained",
    "minimal_proof_setup": [
      "reuse current metadata report as structural source of truth",
      "bind leaf macro names and consumer endpoints exactly as reported",
      "declare PVT corner set and success metric before simulation",
      "prepare generated-logic leaf model inventory",
      "construct focused path-level testbench with declared fanout/load assumptions"
    ],
    "proof_steps": [
      "inventory required models, loads, corners, and route abstractions",
      "build target-specific testbench or equivalent delay abstraction",
      "run per-corner delay/slew/waveform measurement",
      "retain precharge power exception and avoid closure claim",
      "compare measured results against declared success metric",
      "record proof artifact boundaries and unresolved assumptions"
    ],
    "readiness_level": "planning_only_precharge_exception",
    "can_start_proof_without_main_flow_changes": true,
    "requires_standalone_integration": false,
    "requires_routing_extraction": true,
    "requires_physical_layout": false,
    "requires_precharge_power_resolution": true,
    "can_claim_timing_proof_now": false,
    "can_claim_timing_closure_now": false,
    "blockers": [
      "missing spice or lib for generated/control leaf",
      "timing proof is missing",
      "no SPICE timing closure has been run",
      "precharge power exception retained",
      "generated logic fanout load model missing"
    ],
    "next_minimal_action": "recover_generated_logic_spice_or_timing_model_inventory",
    "notes": [
      "Stage count source-confirmed as 2.",
      "Precharge ENB polarity is preserved through PRE_UNBUF -> PRE buffering.",
      "The source is a two-stage inverter chain with drive scaling for precharge.",
      "It is downstream of the PNAND3 precharge gating node, not a standalone timing source.",
      "The signal name PRE is treated as canonical precharge_enb because the PRECHARGE consumer pin is ENB.",
      "requires_gen_inv_timing_model = True",
      "requires_fanout_load_model = True",
      "requires_target_pin_load = True",
      "requires_routing_rc = True",
      "pdrive_timing_proof_available_now = False"
    ]
  }
]
```

## Write / Sense Enable Proof Plan

```json
[
  {
    "timing_object": "WRITE_ENABLE_PATH",
    "current_metadata_status": "available",
    "current_blocker_classification": "blocked_by_missing_stage_count",
    "required_spice_models": [
      "write_driver",
      "sense_amp"
    ],
    "required_liberty_models": [
      "write_driver.lib_or_equivalent_delay_model",
      "sense_amp.lib_or_equivalent_delay_model"
    ],
    "required_load_models": [
      "path_dependency_known_but_numeric_load_unproven",
      "write_driver.EN_pin_load"
    ],
    "required_rc_models": [
      "interconnect_rc_extraction_or_bounded_estimate",
      "enable_net_route_rc_model"
    ],
    "required_corner_definitions": [
      "PVT_corner_definition"
    ],
    "required_waveform_checks": [
      "enable_arrival_window_vs_consumer_check"
    ],
    "required_replica_calibration": false,
    "required_consumer_pin_loads": [
      "write_driver.EN"
    ],
    "required_input_slew_assumptions": [
      "w_en_input_slew"
    ],
    "required_output_load_assumptions": [
      "write_driver_enable_load"
    ],
    "required_path_endpoints": [
      "w_en -> write_driver.EN"
    ],
    "required_success_metric": "w_en reaches write_driver.EN within declared enable window",
    "minimal_proof_setup": [
      "reuse current metadata report as structural source of truth",
      "bind leaf macro names and consumer endpoints exactly as reported",
      "declare PVT corner set and success metric before simulation",
      "compose producer logic + consumer pin load handoff testbench",
      "include route RC estimate from obstacle report as bounded placeholder"
    ],
    "proof_steps": [
      "inventory required models, loads, corners, and route abstractions",
      "build target-specific testbench or equivalent delay abstraction",
      "run per-corner delay/slew/waveform measurement",
      "check enable arrival window at consumer enable pin",
      "compare measured results against declared success metric",
      "record proof artifact boundaries and unresolved assumptions"
    ],
    "readiness_level": "planning_ready_path_resolution_needed",
    "can_start_proof_without_main_flow_changes": true,
    "requires_standalone_integration": false,
    "requires_routing_extraction": true,
    "requires_physical_layout": false,
    "requires_precharge_power_resolution": false,
    "can_claim_timing_proof_now": false,
    "can_claim_timing_closure_now": false,
    "blockers": [
      "stage count missing",
      "timing proof is missing",
      "no SPICE timing closure has been run",
      "consumer enable pin load not yet numerically modeled",
      "enable arrival window not yet quantified"
    ],
    "next_minimal_action": "define_consumer_enable_pin_load_and_enable_window_model",
    "notes": [
      "The first input is conditionally substituted by WEN_DELAY_CHAIN output in one special write branch.",
      "Physical implementation remains blocked because local AND3 is only a semantic composite, not a proven physical macro.",
      "routing obstacle risk=moderate",
      "requires_consumer_enable_pin_load = True",
      "requires_logic_path_stage_count_resolution = True",
      "requires_routing_rc = True",
      "requires_enable_arrival_window = True",
      "handoff_timing_proof_available_now = False"
    ]
  },
  {
    "timing_object": "SENSE_ENABLE_PATH",
    "current_metadata_status": "available",
    "current_blocker_classification": "blocked_by_missing_stage_count",
    "required_spice_models": [
      "write_driver",
      "sense_amp"
    ],
    "required_liberty_models": [
      "write_driver.lib_or_equivalent_delay_model",
      "sense_amp.lib_or_equivalent_delay_model"
    ],
    "required_load_models": [
      "path_dependency_known_but_numeric_load_unproven",
      "sense_amp.EN_pin_load"
    ],
    "required_rc_models": [
      "interconnect_rc_extraction_or_bounded_estimate",
      "enable_net_route_rc_model"
    ],
    "required_corner_definitions": [
      "PVT_corner_definition"
    ],
    "required_waveform_checks": [
      "enable_arrival_window_vs_consumer_check"
    ],
    "required_replica_calibration": false,
    "required_consumer_pin_loads": [
      "sense_amp.EN"
    ],
    "required_input_slew_assumptions": [
      "s_en_input_slew"
    ],
    "required_output_load_assumptions": [
      "sense_amp_enable_load"
    ],
    "required_path_endpoints": [
      "s_en -> sense_amp.EN"
    ],
    "required_success_metric": "s_en reaches sense_amp.EN within declared sense window",
    "minimal_proof_setup": [
      "reuse current metadata report as structural source of truth",
      "bind leaf macro names and consumer endpoints exactly as reported",
      "declare PVT corner set and success metric before simulation",
      "compose producer logic + consumer pin load handoff testbench",
      "include route RC estimate from obstacle report as bounded placeholder"
    ],
    "proof_steps": [
      "inventory required models, loads, corners, and route abstractions",
      "build target-specific testbench or equivalent delay abstraction",
      "run per-corner delay/slew/waveform measurement",
      "check enable arrival window at consumer enable pin",
      "compare measured results against declared success metric",
      "record proof artifact boundaries and unresolved assumptions"
    ],
    "readiness_level": "planning_ready_path_resolution_needed",
    "can_start_proof_without_main_flow_changes": true,
    "requires_standalone_integration": false,
    "requires_routing_extraction": true,
    "requires_physical_layout": false,
    "requires_precharge_power_resolution": false,
    "can_claim_timing_proof_now": false,
    "can_claim_timing_closure_now": false,
    "blockers": [
      "stage count missing",
      "timing proof is missing",
      "no SPICE timing closure has been run",
      "consumer enable pin load not yet numerically modeled",
      "enable arrival window not yet quantified"
    ],
    "next_minimal_action": "define_consumer_enable_pin_load_and_enable_window_model",
    "notes": [
      "This contract stays single-ended on the consumer side because the current sense-amp adapter uses Q -> dout and keeps QB dropped.",
      "routing obstacle risk=moderate",
      "requires_consumer_enable_pin_load = True",
      "requires_logic_path_stage_count_resolution = True",
      "requires_routing_rc = True",
      "requires_enable_arrival_window = True",
      "handoff_timing_proof_available_now = False"
    ]
  }
]
```

## PRECHARGE Timing Exception Proof Plan

```json
[
  {
    "timing_object": "PNAND3_COMPOSITE",
    "current_metadata_status": "available",
    "current_blocker_classification": "blocked_by_precharge_power_exception",
    "required_spice_models": [
      "gen_nand2",
      "gen_inv"
    ],
    "required_liberty_models": [
      "gen_nand2.lib_or_equivalent_delay_model",
      "gen_inv.lib_or_equivalent_delay_model"
    ],
    "required_load_models": [
      "binding_level_consumer_list_known"
    ],
    "required_rc_models": [
      "interconnect_rc_extraction_or_bounded_estimate"
    ],
    "required_corner_definitions": [
      "PVT_corner_definition"
    ],
    "required_waveform_checks": [],
    "required_replica_calibration": false,
    "required_consumer_pin_loads": [],
    "required_input_slew_assumptions": [
      "precharge_logic_input_slew_bundle"
    ],
    "required_output_load_assumptions": [
      "PRE_UNBUF_output_load"
    ],
    "required_path_endpoints": [
      "gated_clk_buf",
      "rbl_delay",
      "wl_en_bar",
      "PRE",
      "PRECHARGE.ENB"
    ],
    "required_success_metric": "PRE_UNBUF timing bound before final precharge drive stage",
    "minimal_proof_setup": [
      "reuse current metadata report as structural source of truth",
      "bind leaf macro names and consumer endpoints exactly as reported",
      "declare PVT corner set and success metric before simulation",
      "prepare generated-logic leaf model inventory",
      "construct focused path-level testbench with declared fanout/load assumptions"
    ],
    "proof_steps": [
      "inventory required models, loads, corners, and route abstractions",
      "build target-specific testbench or equivalent delay abstraction",
      "run per-corner delay/slew/waveform measurement",
      "compare measured results against declared success metric",
      "record proof artifact boundaries and unresolved assumptions"
    ],
    "readiness_level": "planning_only_precharge_exception",
    "can_start_proof_without_main_flow_changes": true,
    "requires_standalone_integration": false,
    "requires_routing_extraction": true,
    "requires_physical_layout": false,
    "requires_precharge_power_resolution": true,
    "can_claim_timing_proof_now": false,
    "can_claim_timing_closure_now": false,
    "blockers": [
      "missing spice or lib for generated/control leaf",
      "timing proof is missing",
      "no SPICE timing closure has been run",
      "precharge power exception retained"
    ],
    "next_minimal_action": "recover_generated_logic_spice_or_timing_model_inventory",
    "notes": [
      "Reuses decoder convention: PNAND3_COMPOSITE_NAND2_INV.",
      "Precharge input order gated_clk_buf / rbl_delay / wl_en_bar is preserved at metadata level.",
      "The signal name PRE is treated as canonical precharge_enb because the PRECHARGE consumer pin is ENB."
    ]
  },
  {
    "timing_object": "PRECHARGE_ENABLE_PATH",
    "current_metadata_status": "available",
    "current_blocker_classification": "blocked_by_precharge_power_exception",
    "required_spice_models": [
      "gen_precharge"
    ],
    "required_liberty_models": [
      "gen_precharge.lib_or_equivalent_delay_model"
    ],
    "required_load_models": [
      "path_dependency_known_but_numeric_load_unproven",
      "gen_precharge.ENB_pin_load"
    ],
    "required_rc_models": [
      "interconnect_rc_extraction_or_bounded_estimate",
      "enable_net_route_rc_model"
    ],
    "required_corner_definitions": [
      "PVT_corner_definition",
      "precharge_recovery_corner"
    ],
    "required_waveform_checks": [
      "active_low_precharge_enable_waveform_check"
    ],
    "required_replica_calibration": false,
    "required_consumer_pin_loads": [
      "gen_precharge.ENB"
    ],
    "required_input_slew_assumptions": [
      "PRE_and_wl_en_bar_input_slew"
    ],
    "required_output_load_assumptions": [
      "precharge_ENB_load"
    ],
    "required_path_endpoints": [
      "PRE_UNBUF -> PRE -> gen_precharge.ENB"
    ],
    "required_success_metric": "PRE/ENB relationship proven under active-low semantics",
    "minimal_proof_setup": [
      "reuse current metadata report as structural source of truth",
      "bind leaf macro names and consumer endpoints exactly as reported",
      "declare PVT corner set and success metric before simulation",
      "compose producer logic + consumer pin load handoff testbench",
      "include route RC estimate from obstacle report as bounded placeholder"
    ],
    "proof_steps": [
      "inventory required models, loads, corners, and route abstractions",
      "build target-specific testbench or equivalent delay abstraction",
      "run per-corner delay/slew/waveform measurement",
      "retain precharge power exception and avoid closure claim",
      "compare measured results against declared success metric",
      "record proof artifact boundaries and unresolved assumptions"
    ],
    "readiness_level": "planning_only_precharge_exception",
    "can_start_proof_without_main_flow_changes": true,
    "requires_standalone_integration": false,
    "requires_routing_extraction": true,
    "requires_physical_layout": false,
    "requires_precharge_power_resolution": true,
    "can_claim_timing_proof_now": false,
    "can_claim_timing_closure_now": false,
    "blockers": [
      "stage count missing",
      "timing proof is missing",
      "no SPICE timing closure has been run",
      "precharge power exception retained"
    ],
    "next_minimal_action": "retain_precharge_exception_and_plan_power_resolution_inputs",
    "notes": [
      "The signal name PRE is treated as canonical precharge_enb because the PRECHARGE consumer pin is ENB.",
      "routing obstacle risk=moderate",
      "routing obstacle risk=moderate_to_high",
      "precharge_no_local_gnd_exception = True",
      "precharge_power_exception_retained = True",
      "precharge_timing_proof_available_now = False",
      "precharge_safe_for_timing_proof_planning = True",
      "precharge_safe_for_timing_closure = False",
      "requires_precharge_power_resolution_for_physical_timing = True"
    ]
  },
  {
    "timing_object": "PRECHARGE",
    "current_metadata_status": "available",
    "current_blocker_classification": "blocked_by_precharge_power_exception",
    "required_spice_models": [
      "gen_precharge"
    ],
    "required_liberty_models": [
      "gen_precharge.lib_or_equivalent_delay_model"
    ],
    "required_load_models": [],
    "required_rc_models": [
      "interconnect_rc_extraction_or_bounded_estimate"
    ],
    "required_corner_definitions": [
      "PVT_corner_definition",
      "precharge_recovery_corner"
    ],
    "required_waveform_checks": [
      "active_low_precharge_enable_waveform_check"
    ],
    "required_replica_calibration": false,
    "required_consumer_pin_loads": [],
    "required_input_slew_assumptions": [
      "PRE_input_slew"
    ],
    "required_output_load_assumptions": [
      "bitline_precharge_device_gate_load"
    ],
    "required_path_endpoints": [],
    "required_success_metric": "precharge ENB handoff timing bound, without claiming physical closure",
    "minimal_proof_setup": [
      "reuse current metadata report as structural source of truth",
      "bind leaf macro names and consumer endpoints exactly as reported",
      "declare PVT corner set and success metric before simulation",
      "retain precharge_no_local_gnd_exception in setup notes",
      "treat proof as planning-only until power exception is resolved"
    ],
    "proof_steps": [
      "inventory required models, loads, corners, and route abstractions",
      "build target-specific testbench or equivalent delay abstraction",
      "run per-corner delay/slew/waveform measurement",
      "retain precharge power exception and avoid closure claim",
      "compare measured results against declared success metric",
      "record proof artifact boundaries and unresolved assumptions"
    ],
    "readiness_level": "planning_only_precharge_exception",
    "can_start_proof_without_main_flow_changes": true,
    "requires_standalone_integration": false,
    "requires_routing_extraction": true,
    "requires_physical_layout": false,
    "requires_precharge_power_resolution": true,
    "can_claim_timing_proof_now": false,
    "can_claim_timing_closure_now": false,
    "blockers": [
      "missing spice or lib for generated/control leaf",
      "missing load model",
      "timing proof is missing",
      "no SPICE timing closure has been run",
      "precharge power exception retained"
    ],
    "next_minimal_action": "retain_precharge_exception_and_plan_power_resolution_inputs",
    "notes": [
      "routing obstacle risk=moderate_to_high",
      "precharge_no_local_gnd_exception = True",
      "precharge_power_exception_retained = True",
      "precharge_timing_proof_available_now = False",
      "precharge_safe_for_timing_proof_planning = True",
      "precharge_safe_for_timing_closure = False",
      "requires_precharge_power_resolution_for_physical_timing = True"
    ]
  },
  {
    "timing_object": "PDRIVE2_FOR_PRE",
    "current_metadata_status": "available",
    "current_blocker_classification": "blocked_by_precharge_power_exception",
    "required_spice_models": [
      "gen_inv"
    ],
    "required_liberty_models": [
      "gen_inv.lib_or_equivalent_delay_model"
    ],
    "required_load_models": [
      "consumer_fanout_known_metadata_only",
      "fanout_load_model",
      "target_pin_load_model"
    ],
    "required_rc_models": [
      "interconnect_rc_extraction_or_bounded_estimate"
    ],
    "required_corner_definitions": [
      "PVT_corner_definition"
    ],
    "required_waveform_checks": [
      "active_low_precharge_enable_waveform_check"
    ],
    "required_replica_calibration": false,
    "required_consumer_pin_loads": [],
    "required_input_slew_assumptions": [
      "pre_unbuf_input_slew"
    ],
    "required_output_load_assumptions": [
      "precharge_enable_output_load"
    ],
    "required_path_endpoints": [
      "gated_clk_buf",
      "rbl_delay",
      "wl_en_bar",
      "PRE",
      "PRECHARGE.ENB"
    ],
    "required_success_metric": "PRE driver delay/slew bound with precharge exception explicitly retained",
    "minimal_proof_setup": [
      "reuse current metadata report as structural source of truth",
      "bind leaf macro names and consumer endpoints exactly as reported",
      "declare PVT corner set and success metric before simulation",
      "prepare generated-logic leaf model inventory",
      "construct focused path-level testbench with declared fanout/load assumptions"
    ],
    "proof_steps": [
      "inventory required models, loads, corners, and route abstractions",
      "build target-specific testbench or equivalent delay abstraction",
      "run per-corner delay/slew/waveform measurement",
      "retain precharge power exception and avoid closure claim",
      "compare measured results against declared success metric",
      "record proof artifact boundaries and unresolved assumptions"
    ],
    "readiness_level": "planning_only_precharge_exception",
    "can_start_proof_without_main_flow_changes": true,
    "requires_standalone_integration": false,
    "requires_routing_extraction": true,
    "requires_physical_layout": false,
    "requires_precharge_power_resolution": true,
    "can_claim_timing_proof_now": false,
    "can_claim_timing_closure_now": false,
    "blockers": [
      "missing spice or lib for generated/control leaf",
      "timing proof is missing",
      "no SPICE timing closure has been run",
      "precharge power exception retained",
      "generated logic fanout load model missing"
    ],
    "next_minimal_action": "recover_generated_logic_spice_or_timing_model_inventory",
    "notes": [
      "Stage count source-confirmed as 2.",
      "Precharge ENB polarity is preserved through PRE_UNBUF -> PRE buffering.",
      "The source is a two-stage inverter chain with drive scaling for precharge.",
      "It is downstream of the PNAND3 precharge gating node, not a standalone timing source.",
      "The signal name PRE is treated as canonical precharge_enb because the PRECHARGE consumer pin is ENB.",
      "requires_gen_inv_timing_model = True",
      "requires_fanout_load_model = True",
      "requires_target_pin_load = True",
      "requires_routing_rc = True",
      "pdrive_timing_proof_available_now = False"
    ]
  }
]
```

## DFF Row / Gated Clock Proof Plan

```json
[
  {
    "timing_object": "DFF_ROW",
    "current_metadata_status": "available",
    "current_blocker_classification": "blocked_by_standalone_clock_integration",
    "required_spice_models": [
      "dff"
    ],
    "required_liberty_models": [
      "dff.lib_or_equivalent_delay_model"
    ],
    "required_load_models": [
      "clock_consumer_capacitance_model"
    ],
    "required_rc_models": [
      "interconnect_rc_extraction_or_bounded_estimate",
      "clock_route_rc_model"
    ],
    "required_corner_definitions": [
      "PVT_corner_definition",
      "clock_setup_hold_corner"
    ],
    "required_waveform_checks": [],
    "required_replica_calibration": false,
    "required_consumer_pin_loads": [
      "dff.CLK"
    ],
    "required_input_slew_assumptions": [
      "clk_buf_input_slew"
    ],
    "required_output_load_assumptions": [
      "clocked_register_data_load"
    ],
    "required_path_endpoints": [
      "clk_buf -> dff.CLK"
    ],
    "required_success_metric": "clock arrival and capture assumptions documented for dff row",
    "minimal_proof_setup": [
      "reuse current metadata report as structural source of truth",
      "bind leaf macro names and consumer endpoints exactly as reported",
      "declare PVT corner set and success metric before simulation",
      "prepare dff clock pin timing model or equivalent SPICE harness",
      "define clock route/load abstraction without modifying standalone"
    ],
    "proof_steps": [
      "inventory required models, loads, corners, and route abstractions",
      "build target-specific testbench or equivalent delay abstraction",
      "run per-corner delay/slew/waveform measurement",
      "check clock pulse width / setup-hold assumptions at dff consumers",
      "compare measured results against declared success metric",
      "record proof artifact boundaries and unresolved assumptions"
    ],
    "readiness_level": "planning_ready_clock_model_missing",
    "can_start_proof_without_main_flow_changes": true,
    "requires_standalone_integration": true,
    "requires_routing_extraction": true,
    "requires_physical_layout": true,
    "requires_precharge_power_resolution": false,
    "can_claim_timing_proof_now": false,
    "can_claim_timing_closure_now": false,
    "blockers": [
      "missing load model",
      "timing proof is missing",
      "no SPICE timing closure has been run",
      "standalone clock integration required",
      "clock tree or clock route model missing"
    ],
    "next_minimal_action": "prepare_dff_clock_path_model_plan",
    "notes": [
      "routing obstacle risk=moderate",
      "clock_distribution_proven = False",
      "dff_row_timing_proof_available_now = False",
      "standalone_integration_required = True",
      "requires_clock_tree_or_clock_route_model = True"
    ]
  },
  {
    "timing_object": "GATED_CLOCK_PATH",
    "current_metadata_status": "available",
    "current_blocker_classification": "blocked_by_standalone_clock_integration",
    "required_spice_models": [
      "dff"
    ],
    "required_liberty_models": [
      "dff.lib_or_equivalent_delay_model"
    ],
    "required_load_models": [
      "path_dependency_known_but_numeric_load_unproven",
      "clock_consumer_capacitance_model"
    ],
    "required_rc_models": [
      "interconnect_rc_extraction_or_bounded_estimate",
      "clock_route_rc_model"
    ],
    "required_corner_definitions": [
      "PVT_corner_definition",
      "clock_setup_hold_corner"
    ],
    "required_waveform_checks": [
      "waveform_shape_and_pulse_width_check"
    ],
    "required_replica_calibration": false,
    "required_consumer_pin_loads": [
      "ADDR_DFF.CLK",
      "DATA_DFF.CLK",
      "DFF_BUF.CLK"
    ],
    "required_input_slew_assumptions": [
      "clk_and_cs_input_slew"
    ],
    "required_output_load_assumptions": [
      "gated_clock_fanout_load"
    ],
    "required_path_endpoints": [
      "clk -> clk_buf -> clk_bar/gated_clk_buf/gated_clk_bar"
    ],
    "required_success_metric": "clock gating path delay/slew/pulse width bounded at gated clock consumers",
    "minimal_proof_setup": [
      "reuse current metadata report as structural source of truth",
      "bind leaf macro names and consumer endpoints exactly as reported",
      "declare PVT corner set and success metric before simulation",
      "prepare dff clock pin timing model or equivalent SPICE harness",
      "define clock route/load abstraction without modifying standalone"
    ],
    "proof_steps": [
      "inventory required models, loads, corners, and route abstractions",
      "build target-specific testbench or equivalent delay abstraction",
      "run per-corner delay/slew/waveform measurement",
      "check clock pulse width / setup-hold assumptions at dff consumers",
      "compare measured results against declared success metric",
      "record proof artifact boundaries and unresolved assumptions"
    ],
    "readiness_level": "planning_ready_clock_model_missing",
    "can_start_proof_without_main_flow_changes": true,
    "requires_standalone_integration": true,
    "requires_routing_extraction": true,
    "requires_physical_layout": true,
    "requires_precharge_power_resolution": false,
    "can_claim_timing_proof_now": false,
    "can_claim_timing_closure_now": false,
    "blockers": [
      "stage count missing",
      "timing proof is missing",
      "no SPICE timing closure has been run",
      "standalone clock integration required",
      "clock tree or clock route model missing"
    ],
    "next_minimal_action": "prepare_dff_clock_path_model_plan",
    "notes": [
      "Producer is a four-stage inverter chain with upsizing.",
      "This contract can drive planning metadata but not physical control placement.",
      "clk_bar is explicitly the inversion of clk_buf, not a separately buffered top-level input.",
      "This is an AND semantic contract, not a direct hard macro mapping.",
      "This gated clock branch is the direct producer for wl_en and the enable-side input for w_en / s_en generation.",
      "routing obstacle risk=moderate",
      "clock_distribution_proven = False",
      "dff_row_timing_proof_available_now = False",
      "standalone_integration_required = True",
      "requires_clock_tree_or_clock_route_model = True"
    ]
  }
]
```

## Model Recovery / Characterization Plan

| model | spice | lib | priority | testbench | unblocks |
| --- | --- | --- | --- | --- | --- |
| gen_delay_inv | False | False | P0 | delay_chain_stage_sweep | DELAY_CHAIN, WEN_DELAY_CHAIN, RBL_DELAY_PATH |
| gen_inv | False | False | P0 | inverter_slew_load_sweep | PDRIVE, PDRIVE2_FOR_PRE, WL_PDRIVE, PINV, AND2, AND3_COMPOSITE, PNAND3_COMPOSITE |
| gen_nand2 | False | False | P0 | nand2_slew_load_sweep | AND2, AND3_COMPOSITE, PNAND3_COMPOSITE, WRITE_ENABLE_PATH, SENSE_ENABLE_PATH, PRECHARGE_ENABLE_PATH |
| dff | True | False | P1 | clock_to_q_setup_hold_sweep | DFF_ROW, GATED_CLOCK_PATH |
| gen_precharge | False | False | P1 | precharge_enable_handoff_sweep | PRECHARGE, PRECHARGE_ENABLE_PATH |
| gen_wl_driver | False | False | P1 | wordline_enable_handoff_sweep | WL_PDRIVE, WORDLINE_ENABLE_PATH |
| sense_amp | True | False | P1 | sense_enable_handoff_sweep | SENSE_ENABLE_PATH |
| write_driver | True | False | P1 | write_enable_handoff_sweep | WRITE_ENABLE_PATH |
| cell_1rw | True | False | P2 | replica_bitline_load_reference_sweep | RBL_DELAY_PATH |
| gen_col_mux_vdd_labeled | False | False | P2 | column_mux_handoff_reference_sweep | future_read_path_handoff_reference_only |
| replica_cell_1rw | True | False | P2 | replica_delay_reference_sweep | DELAY_CHAIN, RBL_DELAY_PATH |

## Ranked Proof Tasks

| rank | task | why first | unblocks | risk |
| --- | --- | --- | --- | --- |
| 1 | recover_generated_logic_spice_or_timing_model_inventory | generated logic macros remain the dominant blocker across delay, clock, and enable paths | DELAY_CHAIN, WEN_DELAY_CHAIN, PDRIVE, WL_PDRIVE, PINV, AND2, AND3_COMPOSITE, PNAND3_COMPOSITE | low |
| 2 | gen_inv_gen_nand2_gen_delay_inv_characterization_plan | these three leaves cover most timing-sensitive TIME/control logic | PDRIVE, WL_PDRIVE, PINV, AND2, AND3_COMPOSITE, PNAND3_COMPOSITE, DELAY_CHAIN, WEN_DELAY_CHAIN | medium |
| 3 | delay_chain_spice_testbench_plan | delay_chain is the most timing-sensitive metadata block and gates replica-path proof | DELAY_CHAIN, RBL_DELAY_PATH | medium |
| 4 | wen_delay_chain_conditional_testbench_plan | the write+16x512 exception must stay scoped and must not leak into general timing assumptions | WEN_DELAY_CHAIN, WRITE_ENABLE_PATH | medium |
| 5 | pdrive_enable_path_load_model_plan | clock/enable fanout and consumer pin loads are currently metadata-only | PDRIVE, WL_PDRIVE, WRITE_ENABLE_PATH, SENSE_ENABLE_PATH, WORDLINE_ENABLE_PATH | low |
| 6 | dff_clock_path_model_plan | clock proof stays blocked until dff consumers and gated clock route assumptions are modeled | DFF_ROW, GATED_CLOCK_PATH | medium |
| 7 | precharge_timing_exception_resolution_plan | precharge remains a known exception and must be quarantined before any closure claim | PRECHARGE, PRECHARGE_ENABLE_PATH, PDRIVE2_FOR_PRE, PNAND3_COMPOSITE | medium |

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
- DELAY_CHAIN: gen_delay_inv timing model missing
- WEN_DELAY_CHAIN: conditional write-branch model missing
- PDRIVE: generated logic fanout load model missing
- PDRIVE2_FOR_PRE: generated logic fanout load model missing
- WL_PDRIVE: generated logic fanout load model missing
- DFF_ROW: clock tree or clock route model missing
- WRITE_ENABLE_PATH: consumer enable pin load not yet numerically modeled
- WRITE_ENABLE_PATH: enable arrival window not yet quantified
- SENSE_ENABLE_PATH: consumer enable pin load not yet numerically modeled
- SENSE_ENABLE_PATH: enable arrival window not yet quantified
- GATED_CLOCK_PATH: clock tree or clock route model missing

## Boundary Assertions

```json
{
  "proof_plan_is_not_proof_result": true,
  "model_inventory_is_not_model_availability": true,
  "spice_file_existence_is_not_characterized_timing_model": true,
  "routing_proof_planning_is_not_extracted_rc": true,
  "timing_proof_is_not_timing_closure": true,
  "standalone_modified": false,
  "routing_modified": false,
  "gds_writer_modified": false
}
```

## Next Recommended Proof Task

- `recover_generated_logic_spice_or_timing_model_inventory`