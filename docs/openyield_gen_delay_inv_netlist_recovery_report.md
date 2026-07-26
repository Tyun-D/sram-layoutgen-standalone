# OpenYield gen_delay_inv Netlist Recovery Plan

- Scope: `gen_delay_inv_transistor_netlist_recovery_plan`
- Repo root: `E:\njust\keyan\SRAM Compiler_V2\OpenRAM-stable\deliverables\sram_layoutgen_step45_clean`
- Tech dir: `E:\njust\keyan\SRAM Compiler_V2\OpenRAM-stable\deliverables\sram_layoutgen_step45_clean\technology\freepdk45`

## Audit Summary

```json
{
  "gen_delay_inv_transistor_netlist_recovery_plan_available": true,
  "source_evidence_found": true,
  "gds_pin_evidence_found": true,
  "candidate_subckt_contract_available": true,
  "candidate_pin_order_available": true,
  "candidate_pin_order_validated_by_spice": false,
  "transistor_sizing_known": false,
  "pdk_device_model_bound": false,
  "can_emit_candidate_subckt_template_now": true,
  "can_emit_validated_spice_now": false,
  "can_enter_four_load_inverter_stage_model_plan": true,
  "can_enter_delay_chain_testbench_template_contract": true,
  "can_run_delay_chain_testbench_now": false,
  "can_claim_delay_proof_now": false,
  "can_claim_timing_closure_now": false,
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
  "delay_chain_plan": "E:\\njust\\keyan\\SRAM Compiler_V2\\OpenRAM-stable\\deliverables\\sram_layoutgen_step45_clean\\docs\\openyield_delay_chain_testbench_plan_report.json",
  "model_recovery": "E:\\njust\\keyan\\SRAM Compiler_V2\\OpenRAM-stable\\deliverables\\sram_layoutgen_step45_clean\\docs\\openyield_generated_logic_model_recovery_report.json",
  "leaf_inventory": "E:\\njust\\keyan\\SRAM Compiler_V2\\OpenRAM-stable\\deliverables\\sram_layoutgen_step45_clean\\docs\\openyield_time_control_leaf_inventory_report.json",
  "source_file": "E:\\njust\\keyan\\SRAM Compiler_V2\\OpenRAM-stable\\third_party\\OpenYield\\sram_compiler\\subcircuits\\time_generate.py",
  "recommended_gds": "E:\\njust\\keyan\\SRAM Compiler_V2\\OpenRAM-stable\\deliverables\\sram_layoutgen_step45_clean\\technology\\freepdk45\\gds_lib\\openram_replacements\\gen_delay_inv.gds",
  "default_gds": "E:\\njust\\keyan\\SRAM Compiler_V2\\OpenRAM-stable\\deliverables\\sram_layoutgen_step45_clean\\technology\\freepdk45\\gds_lib\\gen_delay_inv.gds"
}
```

## Source Evidence

```json
{
  "source_file": "E:\\njust\\keyan\\SRAM Compiler_V2\\OpenRAM-stable\\third_party\\OpenYield\\sram_compiler\\subcircuits\\time_generate.py",
  "source_symbol_or_function": [
    "DelayChain",
    "Pinv"
  ],
  "source_lines_if_available": [
    4,
    14,
    19,
    24,
    25,
    36,
    39,
    47,
    55,
    65,
    66,
    67,
    68,
    107,
    115,
    125,
    126,
    150,
    158,
    164,
    165,
    190,
    198,
    202,
    206,
    207,
    262,
    269,
    275,
    276,
    277,
    299,
    308,
    315,
    321,
    359,
    363,
    364,
    372,
    375
  ],
  "source_role": "DelayChain source constructs gen_delay_inv-equivalent inverter chain and load topology.",
  "source_mentions_delay_chain": true,
  "source_mentions_gen_delay_inv": false,
  "source_mentions_four_load_inverters": true,
  "source_mentions_transistor_sizing": true,
  "source_mentions_pin_order": true,
  "source_mentions_power_pins": true,
  "source_evidence_strength": "medium",
  "source_limitations": [
    "Source defines DelayChain behavior and Pinv instantiation, but does not directly emit a validated gen_delay_inv subckt file.",
    "Source-visible node order uses VDD/VSS/in/out at DelayChain level, not necessarily final leaf subckt pin order.",
    "Pinv internal implementation is imported from standard_cell.py and is not validated here as a finished SPICE leaf."
  ],
  "transistor_sizing_source_confirmed": false,
  "requires_manual_sizing_recovery": true,
  "highlight_block": [
    {
      "line": 298,
      "text": ""
    },
    {
      "line": 299,
      "text": "class DelayChain(BaseSubcircuit):#用于复制位线延迟的延迟链"
    },
    {
      "line": 300,
      "text": "    \"\"\""
    },
    {
      "line": 301,
      "text": "    延迟链电路 (sram_delay_chain)"
    },
    {
      "line": 302,
      "text": "    输入: in, VDD, VSS"
    },
    {
      "line": 303,
      "text": "    输出: out"
    },
    {
      "line": 304,
      "text": "    \"\"\""
    },
    {
      "line": 305,
      "text": "    NAME = \"delay_chain\""
    },
    {
      "line": 306,
      "text": "    NODES = ('VDD', 'VSS', 'in', 'out')"
    },
    {
      "line": 307,
      "text": ""
    },
    {
      "line": 308,
      "text": "    def __init__(self, nmos_model=\"NMOS_VTG\", pmos_model=\"PMOS_VTG\","
    },
    {
      "line": 309,
      "text": "                 pmos_width=5e-07, nmos_width=2.5e-07,"
    },
    {
      "line": 310,
      "text": "                 length=0.05e-6,"
    },
    {
      "line": 311,
      "text": "                 w_rc=False, pi_res=100 @ u_Ohm, pi_cap=0.001 @ u_pF,"
    },
    {
      "line": 312,
      "text": "                 ):"
    },
    {
      "line": 313,
      "text": ""
    },
    {
      "line": 314,
      "text": "        super().__init__("
    },
    {
      "line": 315,
      "text": "            nmos_model, pmos_model,"
    },
    {
      "line": 316,
      "text": "            nmos_width, pmos_width, length,"
    },
    {
      "line": 317,
      "text": "            w_rc=w_rc, pi_res=pi_res, pi_cap=pi_cap,"
    },
    {
      "line": 318,
      "text": "        )"
    },
    {
      "line": 319,
      "text": ""
    },
    {
      "line": 320,
      "text": "        # 创建基本反相器单元"
    },
    {
      "line": 321,
      "text": "        self.inv = Pinv(nmos_model, pmos_model,0.9e-07,2.7e-07, length=0.05e-6,num=1)"
    },
    {
      "line": 322,
      "text": "        self.subcircuit(self.inv)"
    },
    {
      "line": 323,
      "text": ""
    },
    {
      "line": 324,
      "text": "        # 添加内部节点"
    },
    {
      "line": 325,
      "text": "        #self.add_internal_nodes()"
    },
    {
      "line": 326,
      "text": ""
    },
    {
      "line": 327,
      "text": "        # 构建延迟链"
    },
    {
      "line": 328,
      "text": "        self.add_delay_chain()"
    },
    {
      "line": 329,
      "text": ""
    },
    {
      "line": 330,
      "text": "    def add_delay_chain(self):"
    },
    {
      "line": 331,
      "text": "        \"\"\"构建延迟链电路\"\"\""
    },
    {
      "line": 332,
      "text": "        # 第一级反相器"
    },
    {
      "line": 333,
      "text": "        self.X('dinv0', self.inv.NAME, 'VDD', 'VSS', 'in', 'dout_1')"
    },
    {
      "line": 334,
      "text": ""
    },
    {
      "line": 335,
      "text": "        # 第一级的4个负载"
    },
    {
      "line": 336,
      "text": "        for j in range(4):"
    },
    {
      "line": 337,
      "text": "            self.X(f'dload_0_{j}', self.inv.NAME,"
    },
    {
      "line": 338,
      "text": "                   'VDD', 'VSS', 'dout_1', f'n_0_{j}')"
    },
    {
      "line": 339,
      "text": ""
    },
    {
      "line": 340,
      "text": "        # 中间7级反相器 (第2级到第8级)"
    },
    {
      "line": 341,
      "text": "        for i in range(1, 8):"
    },
    {
      "line": 342,
      "text": "            # 反相器"
    },
    {
      "line": 343,
      "text": "            self.X(f'dinv{i}', self.inv.NAME,"
    },
    {
      "line": 344,
      "text": "                   'VDD', 'VSS', f'dout_{i}', f'dout_{i+1}')"
    },
    {
      "line": 345,
      "text": ""
    }
  ]
}
```

## GDS / Leaf Evidence

```json
{
  "macro_name": "gen_delay_inv",
  "recommended_gds_variant": "openram_replacements",
  "gds_path": "E:\\njust\\keyan\\SRAM Compiler_V2\\OpenRAM-stable\\deliverables\\sram_layoutgen_step45_clean\\technology\\freepdk45\\gds_lib\\openram_replacements\\gen_delay_inv.gds",
  "bbox": {
    "x0": -0.08,
    "y0": -0.08,
    "x1": 0.7425,
    "y1": 2.505
  },
  "pin_labels": [
    "A",
    "D",
    "G",
    "S",
    "Z",
    "gnd",
    "vdd"
  ],
  "input_pins": [
    "A"
  ],
  "output_pins": [
    "Z"
  ],
  "vdd_pins": [
    "vdd"
  ],
  "gnd_pins": [
    "gnd"
  ],
  "pin_side_map": {
    "A": "left",
    "Z": "right",
    "gnd": "bottom",
    "vdd": "top",
    "G": "bottom",
    "S": "left",
    "D": "bottom"
  },
  "candidate_pin_order": [
    "A",
    "Z",
    "vdd",
    "gnd"
  ],
  "candidate_pin_order_source": "openram_replacements GDS pin labels plus prior delay-chain planning contract",
  "candidate_pin_order_validated_by_spice": false,
  "power_side_policy": "top_vdd_bottom_gnd",
  "rail_evidence_status": "within_macro_only",
  "safe_for_netlist_contract_planning": true,
  "safe_for_validated_spice_generation": false,
  "fallback_variant_comparison": {
    "variant_name": "default_gds_lib",
    "gds_path": "E:\\njust\\keyan\\SRAM Compiler_V2\\OpenRAM-stable\\deliverables\\sram_layoutgen_step45_clean\\technology\\freepdk45\\gds_lib\\gen_delay_inv.gds",
    "pin_labels": [],
    "recommended_for_future_planning": false
  },
  "notes": [
    "Recommended variant is openram_replacements because it has explicit A/Z/vdd/gnd label evidence.",
    "Default gds_lib variant lacks useful pin label evidence for contract planning.",
    "candidate_pin_order_validated_by_spice=False",
    "safe_for_validated_spice_generation=False"
  ]
}
```

## Candidate Subckt Contract

```json
{
  "subckt_name": "gen_delay_inv",
  "candidate_pin_order": [
    "A",
    "Z",
    "vdd",
    "gnd"
  ],
  "logical_function": "inverter / delay inverter",
  "expected_polarity": "inverting",
  "input_pin": "A",
  "output_pin": "Z",
  "power_pins": [
    "vdd",
    "gnd"
  ],
  "requires_pdk_device_models": true,
  "requires_transistor_sizing": true,
  "requires_body_connection_policy": true,
  "requires_load_stage_context": true,
  "requires_characterization": true,
  "usable_for_testbench_template": true,
  "usable_for_spice_simulation_now": false,
  "usable_for_timing_proof_now": false
}
```

## Transistor-Level Recovery Requirements

| field | value_known | source | requires_manual_or_pdk_definition |
| --- | --- | --- | --- |
| required_device_models | False | time_generate.py names NMOS_VTG / PMOS_VTG but no include path is bound | True |
| required_pmos_model_name | True | time_generate.py default parameter pmos_model="PMOS_VTG" | True |
| required_nmos_model_name | True | time_generate.py default parameter nmos_model="NMOS_VTG" | True |
| required_channel_length | True | time_generate.py DelayChain uses length=0.05e-6 and Pinv(... length=0.05e-6 ...) | True |
| required_pmos_width | True | time_generate.py DelayChain instantiates Pinv(... pmos_width=2.7e-07 ...) | True |
| required_nmos_width | True | time_generate.py DelayChain instantiates Pinv(... nmos_width=0.9e-07 ...) | True |
| required_finger_count | False | None | True |
| required_body_tie_policy | False | not proven by current source/GDS evidence | True |
| required_supply_naming_policy | True | DelayChain source uses VDD/VSS; GDS planning contract uses vdd/gnd alias pair | True |
| required_pin_order_policy | True | candidate contract only: [A, Z, vdd, gnd] | True |
| required_subckt_naming_policy | True | candidate name fixed to gen_delay_inv for planning compatibility | True |
| required_instance_naming_policy | False | future candidate template only | True |
| required_load_inverter_context | True | DelayChain add_delay_chain() adds four same-leaf loads per stage | True |
| required_validation_steps | True | recovery plan defines future validation path, not executed now | True |

## Recovery Decision

```json
{
  "recovery_decision": "recoverable_from_generator_source_but_requires_manual_netlist_materialization",
  "can_emit_candidate_subckt_template_now": true,
  "can_emit_validated_spice_now": false,
  "can_enter_four_load_inverter_stage_model_plan": true,
  "can_enter_delay_chain_testbench_template_contract": true,
  "can_run_delay_chain_testbench_now": false,
  "can_claim_delay_proof_now": false
}
```

## Future Artifact Contract

| artifact | type | allowed_now | manual_review | pdk_binding | characterization | validated | timing_proof |
| --- | --- | --- | --- | --- | --- | --- | --- |
| gen_delay_inv_candidate_subckt_template.sp | candidate_subckt_template | True | True | True | True | False | False |
| gen_delay_inv_subckt_contract.json | subckt_contract_json | True | True | False | False | False | False |
| gen_delay_inv_recovery_notes.md | recovery_notes | True | False | False | False | False | False |
| gen_delay_inv_validated.sp | validated_spice | False | True | True | True | True | False |
| gen_delay_inv.lib | validated_liberty | False | True | True | True | True | False |
| measured_delay_result.json | measured_delay_result | False | True | True | True | False | True |
| timing_closed_report.md | timing_closed_report | False | True | True | True | False | True |

## Blockers

- No existing validated SPICE subckt for gen_delay_inv was found.
- GDS pin labels provide candidate logical pins only, not validated SPICE pin order.
- Transistor sizing is source-visible in DelayChain construction, but Pinv internal implementation still needs manual recovery review.
- PDK model include path is not bound in current plan.
- Body connection policy is not proven from current source/GDS evidence alone.
- No characterization or simulation has been run.
- gen_inv: Recovery still requires manual netlist materialization plus characterization.
- gen_nand2: Recovery still requires manual netlist materialization plus characterization.
- gen_delay_inv: Recovery still requires manual netlist materialization plus characterization.
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

## Boundary Assertions

```json
{
  "generator_source_is_not_validated_spice": true,
  "gds_pin_order_is_not_validated_spice_pin_order": true,
  "candidate_subckt_contract_is_not_validated_model": true,
  "recovery_plan_is_not_characterization_result": true,
  "recovery_plan_is_not_timing_proof": true,
  "standalone_modified": false,
  "routing_modified": false,
  "gds_writer_modified": false
}
```

## Next Recommended Proof Task

- `four_load_inverter_stage_model_plan`