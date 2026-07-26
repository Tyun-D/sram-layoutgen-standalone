# OpenYield Delay Chain Testbench Plan Report

- Scope: `delay_chain_spice_testbench_plan`
- Repo root: `E:\njust\keyan\SRAM Compiler_V2\OpenRAM-stable\deliverables\sram_layoutgen_step45_clean`
- Tech dir: `E:\njust\keyan\SRAM Compiler_V2\OpenRAM-stable\deliverables\sram_layoutgen_step45_clean\technology\freepdk45`

## Audit Summary

```json
{
  "delay_chain_spice_testbench_plan_available": true,
  "delay_chain_structure_captured": true,
  "stage_count_confirmed": true,
  "four_load_inverter_policy_captured": true,
  "model_dependencies_identified": true,
  "measurement_plan_available": true,
  "corner_plan_available": true,
  "artifact_contract_available": true,
  "can_emit_testbench_template_now": true,
  "can_run_testbench_now": false,
  "can_claim_delay_proof_now": false,
  "can_claim_timing_closure_now": false,
  "can_enter_gen_delay_inv_transistor_netlist_recovery_plan": true,
  "can_enter_four_load_inverter_stage_model_plan": true,
  "can_enter_wen_delay_chain_conditional_testbench_plan": true,
  "can_enter_physical_timing_closure_now": false,
  "can_enter_physical_routing_now": false,
  "can_enter_physical_placement_now": false,
  "can_generate_time_control_gds_now": false,
  "can_modify_standalone_now": false
}
```

## Input Reports And Assets

```json
{
  "model_recovery": "E:\\njust\\keyan\\SRAM Compiler_V2\\OpenRAM-stable\\deliverables\\sram_layoutgen_step45_clean\\docs\\openyield_generated_logic_model_recovery_report.json",
  "timing_proof_plan": "E:\\njust\\keyan\\SRAM Compiler_V2\\OpenRAM-stable\\deliverables\\sram_layoutgen_step45_clean\\docs\\openyield_time_control_timing_proof_plan_report.json",
  "timing_metadata": "E:\\njust\\keyan\\SRAM Compiler_V2\\OpenRAM-stable\\deliverables\\sram_layoutgen_step45_clean\\docs\\openyield_time_control_timing_metadata_report.json",
  "generated_logic_contract": "E:\\njust\\keyan\\SRAM Compiler_V2\\OpenRAM-stable\\deliverables\\sram_layoutgen_step45_clean\\docs\\openyield_time_control_generated_logic_contract_report.json",
  "signal_binding": "E:\\njust\\keyan\\SRAM Compiler_V2\\OpenRAM-stable\\deliverables\\sram_layoutgen_step45_clean\\docs\\openyield_time_control_signal_binding_report.json",
  "repo_asset_inventory": "E:\\njust\\keyan\\SRAM Compiler_V2\\OpenRAM-stable\\deliverables\\sram_layoutgen_step45_clean\\docs\\openyield_repo_physical_asset_inventory_report.json"
}
```

## DELAY_CHAIN Structure Plan

```json
{
  "timing_object": "DELAY_CHAIN",
  "timing_role": "replica_bitline_delay / rbl_delay_generation",
  "source_signal": "rbl",
  "target_signal": "rbl_delay",
  "leaf": "gen_delay_inv",
  "stage_count": 9,
  "load_model_source": "source_confirmed_four_load_inverters_per_stage",
  "requires_replica_path_calibration": true,
  "requires_parasitic_estimate": true,
  "requires_waveform_check": true,
  "can_claim_delay_proof_now": false,
  "stage_plan": [
    {
      "stage_index": 1,
      "stage_i.input": "rbl",
      "stage_i.output": "planned_stage_1_out",
      "stage_i.load_inverters": 4,
      "stage_i.load_model_status": "source_confirmed_count_only_not_quantified",
      "stage_i.requires_gen_delay_inv_model": true,
      "stage_i.requires_input_slew": true,
      "stage_i.requires_output_load": true,
      "stage_i.requires_rc": true
    },
    {
      "stage_index": 2,
      "stage_i.input": "planned_stage_1_out",
      "stage_i.output": "planned_stage_2_out",
      "stage_i.load_inverters": 4,
      "stage_i.load_model_status": "source_confirmed_count_only_not_quantified",
      "stage_i.requires_gen_delay_inv_model": true,
      "stage_i.requires_input_slew": true,
      "stage_i.requires_output_load": true,
      "stage_i.requires_rc": true
    },
    {
      "stage_index": 3,
      "stage_i.input": "planned_stage_2_out",
      "stage_i.output": "planned_stage_3_out",
      "stage_i.load_inverters": 4,
      "stage_i.load_model_status": "source_confirmed_count_only_not_quantified",
      "stage_i.requires_gen_delay_inv_model": true,
      "stage_i.requires_input_slew": true,
      "stage_i.requires_output_load": true,
      "stage_i.requires_rc": true
    },
    {
      "stage_index": 4,
      "stage_i.input": "planned_stage_3_out",
      "stage_i.output": "planned_stage_4_out",
      "stage_i.load_inverters": 4,
      "stage_i.load_model_status": "source_confirmed_count_only_not_quantified",
      "stage_i.requires_gen_delay_inv_model": true,
      "stage_i.requires_input_slew": true,
      "stage_i.requires_output_load": true,
      "stage_i.requires_rc": true
    },
    {
      "stage_index": 5,
      "stage_i.input": "planned_stage_4_out",
      "stage_i.output": "planned_stage_5_out",
      "stage_i.load_inverters": 4,
      "stage_i.load_model_status": "source_confirmed_count_only_not_quantified",
      "stage_i.requires_gen_delay_inv_model": true,
      "stage_i.requires_input_slew": true,
      "stage_i.requires_output_load": true,
      "stage_i.requires_rc": true
    },
    {
      "stage_index": 6,
      "stage_i.input": "planned_stage_5_out",
      "stage_i.output": "planned_stage_6_out",
      "stage_i.load_inverters": 4,
      "stage_i.load_model_status": "source_confirmed_count_only_not_quantified",
      "stage_i.requires_gen_delay_inv_model": true,
      "stage_i.requires_input_slew": true,
      "stage_i.requires_output_load": true,
      "stage_i.requires_rc": true
    },
    {
      "stage_index": 7,
      "stage_i.input": "planned_stage_6_out",
      "stage_i.output": "planned_stage_7_out",
      "stage_i.load_inverters": 4,
      "stage_i.load_model_status": "source_confirmed_count_only_not_quantified",
      "stage_i.requires_gen_delay_inv_model": true,
      "stage_i.requires_input_slew": true,
      "stage_i.requires_output_load": true,
      "stage_i.requires_rc": true
    },
    {
      "stage_index": 8,
      "stage_i.input": "planned_stage_7_out",
      "stage_i.output": "planned_stage_8_out",
      "stage_i.load_inverters": 4,
      "stage_i.load_model_status": "source_confirmed_count_only_not_quantified",
      "stage_i.requires_gen_delay_inv_model": true,
      "stage_i.requires_input_slew": true,
      "stage_i.requires_output_load": true,
      "stage_i.requires_rc": true
    },
    {
      "stage_index": 9,
      "stage_i.input": "planned_stage_8_out",
      "stage_i.output": "rbl_delay",
      "stage_i.load_inverters": 4,
      "stage_i.load_model_status": "source_confirmed_count_only_not_quantified",
      "stage_i.requires_gen_delay_inv_model": true,
      "stage_i.requires_input_slew": true,
      "stage_i.requires_output_load": true,
      "stage_i.requires_rc": true
    }
  ]
}
```

## SPICE Testbench Plan

```json
{
  "testbench_name": "openyield_delay_chain_stage9_plan_only",
  "target_timing_object": "DELAY_CHAIN",
  "chain_stage_count": 9,
  "leaf_macro": "gen_delay_inv",
  "leaf_model_status": "recoverable_from_generator_source_but_not_usable_now",
  "leaf_model_source": "generator_source_only",
  "required_subckt_name": "gen_delay_inv",
  "required_pin_order": [
    "A",
    "Z",
    "vdd",
    "gnd"
  ],
  "required_pin_order_status": "candidate_from_gds_pin_metadata_not_validated_spice_order",
  "input_signal": "rbl",
  "output_signal": "rbl_delay",
  "input_slew_parameters": {
    "slew_name": "rbl_input_slew",
    "value": null,
    "known": false,
    "source_of_value": "requires_user_or_characterization_definition"
  },
  "supply_parameters": {
    "vdd": null,
    "gnd": "0_reference_only",
    "voltage_known": false,
    "source_of_value": "requires_user_or_pdk_definition"
  },
  "temperature_parameters": {
    "temperature": null,
    "temperature_known": false,
    "source_of_value": "requires_user_or_pdk_definition"
  },
  "corner_parameters": [
    "PVT_corner_definition",
    "replica_delay_margin_corner"
  ],
  "load_model": "source_confirmed_four_load_inverters_per_stage",
  "per_stage_load_policy": "attach four inverter loads to each stage output as planning-only symbolic load",
  "four_load_inverters_per_stage_encoded": true,
  "output_load_policy": "final stage requires consumer pin load plus distributed stage load placeholder",
  "rc_placeholder_policy": "use named RC placeholders only; no quantified RC may be claimed now",
  "replica_calibration_policy": "must calibrate chain result against replica bitline RC/load before proof",
  "waveform_probe_points": [
    "rbl",
    "planned_stage_1_out",
    "planned_stage_5_out",
    "rbl_delay"
  ],
  "delay_measurement_points": [
    {
      "name": "rbl_to_rbl_delay",
      "from": "rbl",
      "to": "rbl_delay",
      "status": "planning_only"
    }
  ],
  "slew_measurement_points": [
    {
      "name": "rbl_input_slew",
      "node": "rbl",
      "status": "requires_voltage_thresholds"
    },
    {
      "name": "rbl_delay_output_slew",
      "node": "rbl_delay",
      "status": "requires_voltage_thresholds"
    }
  ],
  "pulse_width_measurement_points": [
    {
      "name": "rbl_delay_pulse_width",
      "node": "rbl_delay",
      "status": "requires_simulation"
    }
  ],
  "success_metrics": [
    "bounded delay across corners with replica calibration and waveform integrity",
    "all nine stages instantiated in template structure",
    "four-load-per-stage policy preserved in template metadata"
  ],
  "failure_metrics": [
    "missing gen_delay_inv model",
    "missing PDK transistor model",
    "missing corner definition",
    "missing replica RC/load calibration",
    "missing waveform threshold policy"
  ],
  "required_includes": [
    "E:\\njust\\keyan\\SRAM Compiler_V2\\OpenRAM-stable\\third_party\\OpenYield\\sram_compiler\\subcircuits\\time_generate.py"
  ],
  "required_device_models": [
    "PDK transistor models"
  ],
  "required_generated_logic_models": [
    {
      "model_name": "gen_delay_inv",
      "status": "missing_usable_spice_or_lib",
      "source": "generator_source_only"
    },
    {
      "model_name": "gen_inv",
      "status": "needed_for_four_load_stage_model",
      "source": "future_four_load_inverter_stage_model_plan"
    }
  ],
  "required_artifacts_before_run": [
    "gen_delay_inv transistor-level subckt",
    "four-load inverter stage model",
    "PVT corner definition",
    "replica bitline RC/load model",
    "consumer pin load model",
    "measurement threshold definition"
  ],
  "can_emit_testbench_template_now": true,
  "can_run_testbench_now": false,
  "can_claim_delay_proof_now": false,
  "can_claim_timing_closure_now": false,
  "blockers": [
    "No validated gen_delay_inv SPICE model exists yet.",
    "No validated PDK device model include path is bound in current report.",
    "No numerical corner/slew/load values are authorized in this step.",
    "No replica calibration data exists yet."
  ],
  "contract_evidence": {
    "generated_logic_contract_name": "DELAY_CHAIN_GENERATED_LOGIC_CONTRACT",
    "generated_logic_contract_input_pins": [
      "in"
    ],
    "generated_logic_contract_output_pins": [
      "out"
    ],
    "signal_binding_output_signal": "rbl_delay"
  }
}
```

## Artifact Contract

| artifact | type | allowed now | model before use | approval before sim | is proof result |
| --- | --- | --- | --- | --- | --- |
| delay_chain_testbench_template.sp | spice_testbench_template | True | True | True | False |
| delay_chain_testbench_config.json | testbench_config_json | True | True | True | False |
| delay_chain_measurement_spec.json | measurement_spec_json | True | True | True | False |
| delay_chain_corner_spec.json | corner_spec_json | True | True | True | False |
| delay_chain_plan.md | README / md report | True | False | False | False |
| delay_chain_measured_delay_result.json | measured_delay_result | False | False | False | True |
| delay_chain_timing_closed_report.md | timing_closed_report | False | False | False | True |
| delay_chain_validated.lib | validated_liberty | False | False | False | True |
| delay_chain_extracted_rc.spef | extracted_rc | False | False | False | True |
| delay_chain_route.gds | physical_routing | False | False | False | True |
| time_control_delay_chain.gds | gds_layout | False | False | False | True |

## Corner Plan

| corner | process | voltage | temperature | needs definition | planning safe |
| --- | --- | --- | --- | --- | --- |
| PVT_corner_definition | None | None | None | True | True |
| replica_delay_margin_corner | None | None | None | True | True |

## Measurement Plan

| measurement | from | to | edge | threshold | can evaluate now |
| --- | --- | --- | --- | --- | --- |
| chain_delay_rbl_to_rbl_delay | rbl | rbl_delay | matching_edge_required_but_not_quantified | requires_voltage_level_definition | False |
| input_slew_at_rbl | rbl | rbl | input_edge_to_be_defined | requires_voltage_level_definition | False |
| output_slew_at_rbl_delay | rbl_delay | rbl_delay | output_edge_to_be_defined | requires_voltage_level_definition | False |
| pulse_width_at_rbl_delay | rbl_delay | rbl_delay | pulse_width_policy_to_be_defined | requires_voltage_level_definition | False |

## Model Dependency Table

| model | status | source candidate | can use now | needs characterization | blocker |
| --- | --- | --- | --- | --- | --- |
| gen_delay_inv | recoverable_from_generator_source_but_missing_usable_spice | E:\njust\keyan\SRAM Compiler_V2\OpenRAM-stable\third_party\OpenYield\sram_compiler\subcircuits\time_generate.py | False | True | critical |
| gen_inv | recoverable_from_generator_source_but_missing_usable_spice | openyield generator source or future recovered netlist | False | True | high |
| PDK transistor models | path_not_proven_in_current_report_set | None | False | False | critical |
| four-load inverter model | count_known_value_unknown | future four_load_inverter_stage_model_plan | False | True | high |
| replica bitline RC/load model | metadata_only_not_quantified | replica_cell_1rw.sp + future RC/load calibration plan | False | True | critical |
| consumer pin load model | consumer_list_known_but_load_value_unknown | Pinv.A / AND3.A / PNAND3.B metadata | False | True | high |

## Ranked Next Tasks

| rank | task | readonly | modifies main flow | unblocks |
| --- | --- | --- | --- | --- |
| 1 | gen_delay_inv_transistor_netlist_recovery_plan | True | False | delay_chain_testbench_template_contract, four_load_inverter_stage_model_plan |
| 2 | four_load_inverter_stage_model_plan | True | False | delay_chain_testbench_template_contract |
| 3 | delay_chain_testbench_template_contract | True | False | pvt_corner_definition_plan, waveform_measurement_spec_plan |
| 4 | pvt_corner_definition_plan | True | False | can_run_testbench_now_future_gate |
| 5 | replica_load_calibration_plan | True | False | can_claim_delay_proof_now_future_gate |
| 6 | waveform_measurement_spec_plan | True | False | future_delay_chain_simulation_request |

## Blockers

- gen_delay_inv has no usable SPICE or Liberty model yet.
- PDK transistor model path is not yet proven in current planning inputs.
- PVT corner definitions remain unspecified for execution.
- Replica bitline RC/load calibration is not yet quantified.
- Input slew values are not yet quantified.
- Output load values are not yet quantified.
- Waveform threshold levels are not yet quantified.
- No executable simulation is authorized in this step.
- missing spice or lib for generated/control leaf
- timing proof is missing
- no SPICE timing closure has been run
- replica calibration required
- gen_delay_inv timing model missing
- gen_inv: Recovery still requires manual netlist materialization plus characterization.
- gen_nand2: Recovery still requires manual netlist materialization plus characterization.
- gen_delay_inv: Recovery still requires manual netlist materialization plus characterization.

## Boundary Assertions

```json
{
  "testbench_plan != executable_simulation": true,
  "testbench_template != validated_timing_model": true,
  "generated_source != SPICE_model": true,
  "stage_count != delay_proof": true,
  "load_policy != quantified_load_proof": true,
  "standalone_modified": false,
  "routing_modified": false,
  "gds_writer_modified": false
}
```

## Next Recommended Proof Task

- `gen_delay_inv_transistor_netlist_recovery_plan`