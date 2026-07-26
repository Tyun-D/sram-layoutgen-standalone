# OpenYield Four-Load Inverter Stage Model Report

- Scope: `four_load_inverter_stage_model_plan`
- Repo root: `E:\njust\keyan\SRAM Compiler_V2\OpenRAM-stable\deliverables\sram_layoutgen_step45_clean`
- Tech dir: `E:\njust\keyan\SRAM Compiler_V2\OpenRAM-stable\deliverables\sram_layoutgen_step45_clean\technology\freepdk45`

## Audit Summary

```json
{
  "four_load_inverter_stage_model_plan_available": true,
  "source_four_load_pattern_found": true,
  "load_count_per_stage_confirmed": true,
  "all_stage_load_contracts_available": true,
  "load_inverter_binding_decision_available": true,
  "load_capacitance_quantified": false,
  "load_pin_order_validated_by_spice": false,
  "can_emit_symbolic_load_testbench_template_now": true,
  "can_run_delay_chain_testbench_now": false,
  "can_claim_delay_proof_now": false,
  "can_claim_timing_closure_now": false,
  "can_enter_delay_chain_testbench_template_contract": true,
  "can_enter_pvt_corner_definition_plan": true,
  "can_enter_replica_load_calibration_plan": true,
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
  "gen_delay_inv_recovery": "E:\\njust\\keyan\\SRAM Compiler_V2\\OpenRAM-stable\\deliverables\\sram_layoutgen_step45_clean\\docs\\openyield_gen_delay_inv_netlist_recovery_report.json",
  "delay_chain_plan": "E:\\njust\\keyan\\SRAM Compiler_V2\\OpenRAM-stable\\deliverables\\sram_layoutgen_step45_clean\\docs\\openyield_delay_chain_testbench_plan_report.json",
  "leaf_inventory": "E:\\njust\\keyan\\SRAM Compiler_V2\\OpenRAM-stable\\deliverables\\sram_layoutgen_step45_clean\\docs\\openyield_time_control_leaf_inventory_report.json",
  "time_generate_source": "E:\\njust\\keyan\\SRAM Compiler_V2\\OpenRAM-stable\\third_party\\OpenYield\\sram_compiler\\subcircuits\\time_generate.py",
  "standard_cell_source": "E:\\njust\\keyan\\SRAM Compiler_V2\\OpenRAM-stable\\third_party\\OpenYield\\sram_compiler\\subcircuits\\standard_cell.py",
  "gen_delay_inv_gds": "E:\\njust\\keyan\\SRAM Compiler_V2\\OpenRAM-stable\\deliverables\\sram_layoutgen_step45_clean\\technology\\freepdk45\\gds_lib\\openram_replacements\\gen_delay_inv.gds",
  "gen_inv_gds": "E:\\njust\\keyan\\SRAM Compiler_V2\\OpenRAM-stable\\deliverables\\sram_layoutgen_step45_clean\\technology\\freepdk45\\gds_lib\\openram_replacements\\gen_inv.gds"
}
```

## Source Evidence

```json
{
  "source_file": "E:\\njust\\keyan\\SRAM Compiler_V2\\OpenRAM-stable\\third_party\\OpenYield\\sram_compiler\\subcircuits\\time_generate.py",
  "source_symbol_or_function": [
    "DelayChain.add_delay_chain",
    "Pinv"
  ],
  "source_lines_if_available": [
    299,
    306,
    321,
    333,
    336,
    337,
    341,
    343,
    347,
    348,
    352,
    355,
    356,
    5,
    10,
    16,
    24,
    25,
    26,
    31,
    33
  ],
  "source_uses_same_inv_for_delay_and_load": true,
  "source_load_instance_pattern": "dload_<stage>_<slot> instances all use self.inv.NAME, same as dinv<stage>",
  "source_load_count_per_stage": 4,
  "source_load_stage_count": 9,
  "source_load_nodes": {
    "stage_0": {
      "driver_output": "dout_1",
      "load_outputs": [
        "n_0_0",
        "n_0_1",
        "n_0_2",
        "n_0_3"
      ]
    },
    "stage_1_to_7": "driver outputs dout_2..dout_8 each fan out to n_<stage>_0..3",
    "stage_8": {
      "driver_output": "out",
      "load_outputs": [
        "n_8_0",
        "n_8_1",
        "n_8_2",
        "n_8_3"
      ]
    }
  },
  "source_mentions_load_transistor_sizing": true,
  "source_mentions_load_pin_order": true,
  "source_mentions_load_power_pins": true,
  "source_evidence_strength": "high",
  "source_limitations": [
    "The source proves instance topology and shared leaf origin, but not a validated SPICE subckt file.",
    "The source proves Pinv node order (VDD, VSS, A, Z) for the Python generator leaf, not a validated exported .SUBCKT order for gen_delay_inv/gen_inv.",
    "The source does not quantify the effective input capacitance of each load inverter."
  ],
  "supporting_source_blocks": {
    "delay_chain_block": [
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
      },
      {
        "line": 346,
        "text": "            # 负载"
      },
      {
        "line": 347,
        "text": "            for j in range(4):"
      },
      {
        "line": 348,
        "text": "                self.X(f'dload_{i}_{j}', self.inv.NAME,"
      },
      {
        "line": 349,
        "text": "                       'VDD', 'VSS', f'dout_{i+1}', f'n_{i}_{j}')"
      },
      {
        "line": 350,
        "text": ""
      },
      {
        "line": 351,
        "text": "        # 最后一级反相器 (第9级)"
      },
      {
        "line": 352,
        "text": "        self.X('dinv8', self.inv.NAME, 'VDD', 'VSS', 'dout_8', 'out')"
      },
      {
        "line": 353,
        "text": ""
      },
      {
        "line": 354,
        "text": "        # 最后一级的4个负载"
      },
      {
        "line": 355,
        "text": "        for j in range(4):"
      },
      {
        "line": 356,
        "text": "            self.X(f'dload_8_{j}', self.inv.NAME,"
      }
    ],
    "pinv_block": [
      {
        "line": 5,
        "text": "class Pinv(BaseSubcircuit):"
      },
      {
        "line": 6,
        "text": "    \"\"\""
      },
      {
        "line": 7,
        "text": "    Standard CMOS Inverter"
      },
      {
        "line": 8,
        "text": "    NODES: VDD, VSS, A (Input), Z (Output)"
      },
      {
        "line": 9,
        "text": "    \"\"\""
      },
      {
        "line": 10,
        "text": "    NODES = ('VDD', 'VSS', 'A', 'Z')"
      },
      {
        "line": 11,
        "text": ""
      },
      {
        "line": 12,
        "text": "    def __init__(self, nmos_model, pmos_model,"
      },
      {
        "line": 13,
        "text": "                 nmos_width, pmos_width, length,"
      },
      {
        "line": 14,
        "text": "                 w_rc=False, pi_res=100 @ u_Ohm, pi_cap=0.001 @ u_pF,num=''):"
      },
      {
        "line": 15,
        "text": ""
      },
      {
        "line": 16,
        "text": "        self.NAME = f\"PINV{num}\""
      },
      {
        "line": 17,
        "text": "        super().__init__("
      },
      {
        "line": 18,
        "text": "            nmos_model, pmos_model,"
      },
      {
        "line": 19,
        "text": "            nmos_width, pmos_width, length,"
      },
      {
        "line": 20,
        "text": "            w_rc, pi_res, pi_cap)"
      },
      {
        "line": 21,
        "text": ""
      },
      {
        "line": 22,
        "text": "        self.nmos_model = nmos_model"
      },
      {
        "line": 23,
        "text": "        self.pmos_model = pmos_model"
      },
      {
        "line": 24,
        "text": "        self.nmos_width = nmos_width"
      },
      {
        "line": 25,
        "text": "        self.pmos_width = pmos_width"
      },
      {
        "line": 26,
        "text": "        self.length = length"
      },
      {
        "line": 27,
        "text": ""
      },
      {
        "line": 28,
        "text": "        self.add_inverter_transistors()"
      },
      {
        "line": 29,
        "text": ""
      },
      {
        "line": 30,
        "text": "    def add_inverter_transistors(self):"
      },
      {
        "line": 31,
        "text": "        self.M('pinv_pmos', 'Z', 'A', 'VDD', 'VDD',"
      },
      {
        "line": 32,
        "text": "            model=self.pmos_model, w=self.pmos_width, l=self.length)"
      },
      {
        "line": 33,
        "text": "        self.M('pinv_nmos', 'Z', 'A', 'VSS', 'VSS',"
      },
      {
        "line": 34,
        "text": "            model=self.nmos_model, w=self.nmos_width, l=self.length)"
      }
    ]
  },
  "derived_conclusions": {
    "load_inverter_same_as_delay_stage_source": true,
    "load_count_source_confirmed": true,
    "load_capacitance_quantified": false,
    "four_load_count_known": true,
    "four_load_capacitance_value_known": false,
    "requires_characterization_or_cap_estimation": true
  }
}
```

## Load Inverter Candidate Binding Comparison

| candidate | same source | matches source pattern | validated spice | validated load cap | planning | simulate now | risk |
| --- | --- | --- | --- | --- | --- | --- | --- |
| same_source_Pinv_as_delay_stage | True | True | False | False | True | False | medium |
| gen_delay_inv_candidate_subckt | False | False | False | False | False | False | medium |
| gen_inv_openram_replacement | False | False | False | False | False | False | high |
| symbolic_inverter_load_only | False | True | False | False | True | False | low |

## Per-Stage Load Model Contract

| stage | driver | input | output | load count | load candidate | model type | template safe | simulate now |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 0 | dinv0 | in | dout_1 | 4 | same_source_Pinv_as_delay_stage | four_parallel_inverter_gate_loads | True | False |
| 1 | dinv1 | dout_1 | dout_2 | 4 | same_source_Pinv_as_delay_stage | four_parallel_inverter_gate_loads | True | False |
| 2 | dinv2 | dout_2 | dout_3 | 4 | same_source_Pinv_as_delay_stage | four_parallel_inverter_gate_loads | True | False |
| 3 | dinv3 | dout_3 | dout_4 | 4 | same_source_Pinv_as_delay_stage | four_parallel_inverter_gate_loads | True | False |
| 4 | dinv4 | dout_4 | dout_5 | 4 | same_source_Pinv_as_delay_stage | four_parallel_inverter_gate_loads | True | False |
| 5 | dinv5 | dout_5 | dout_6 | 4 | same_source_Pinv_as_delay_stage | four_parallel_inverter_gate_loads | True | False |
| 6 | dinv6 | dout_6 | dout_7 | 4 | same_source_Pinv_as_delay_stage | four_parallel_inverter_gate_loads | True | False |
| 7 | dinv7 | dout_7 | dout_8 | 4 | same_source_Pinv_as_delay_stage | four_parallel_inverter_gate_loads | True | False |
| 8 | dinv8 | dout_8 | out | 4 | same_source_Pinv_as_delay_stage | four_parallel_inverter_gate_loads | True | False |

## SPICE Template Implication

```json
{
  "template_load_strategy": "planning_only_four_parallel_inverter_loads_per_stage",
  "load_subckt_name_candidate": "PINV1",
  "load_pin_order_candidate": [
    "VDD",
    "VSS",
    "A",
    "Z"
  ],
  "load_connection_pattern": {
    "rule": "each load inverter input connects to the current stage output, each load inverter output connects to a unique dummy node",
    "stage_0_example": {
      "driver_output": "dout_1",
      "load_instances": [
        {
          "instance_name": "dload_0_0",
          "input_node": "dout_1",
          "output_node": "n_0_0"
        },
        {
          "instance_name": "dload_0_1",
          "input_node": "dout_1",
          "output_node": "n_0_1"
        },
        {
          "instance_name": "dload_0_2",
          "input_node": "dout_1",
          "output_node": "n_0_2"
        },
        {
          "instance_name": "dload_0_3",
          "input_node": "dout_1",
          "output_node": "n_0_3"
        }
      ]
    }
  },
  "load_output_treatment": "dummy load outputs must remain isolated metadata nodes and must not be treated as real signal path endpoints",
  "floating_load_outputs_allowed": true,
  "requires_dummy_output_load_handling": true,
  "requires_body_tie_policy": true,
  "requires_pdk_model_binding": true,
  "requires_validation_before_run": true,
  "can_emit_template_with_symbolic_loads": true,
  "can_run_template_now": false,
  "notes": [
    "The source proves stage fanout topology, not quantitative capacitance.",
    "A future template may normalize PINV1 into a canonical alias such as gen_delay_inv, but that alias is not validated now.",
    "Dummy load outputs are bookkeeping nodes only."
  ]
}
```

## Load Model Artifact Contract

| artifact | type | allowed now | manual review | pdk binding | characterization | validated load model | timing proof |
| --- | --- | --- | --- | --- | --- | --- | --- |
| four_load_inverter_stage_contract.json | planning_contract_json | True | True | False | False | False | False |
| delay_chain_load_model_notes.md | planning_notes_markdown | True | False | False | False | False | False |
| delay_chain_symbolic_load_template.sp | symbolic_spice_template | True | True | True | True | False | False |
| validated_four_load_model.sp | validated_spice_model | False | True | True | True | True | False |
| load_capacitance_extracted.json | quantified_load_extract | False | True | True | True | True | False |
| measured_delay_result.json | measurement_result | False | True | True | True | False | True |
| timing_closed_report.md | timing_closure_claim | False | True | True | True | False | True |

## Blockers

- The four-load count is source-confirmed, but the effective load capacitance per inverter is not quantified.
- No validated SPICE pin order exists for gen_delay_inv or gen_inv in the current input set.
- No PDK transistor model include path is bound for executable simulation.
- A future load template still needs manual netlist materialization and characterization.
- Replica bitline calibration remains required before any delay proof.
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
  "load_inverter_contract_is_not_characterization_result": true,
  "load_count_confirmation_is_not_load_capacitance_value": true,
  "symbolic_template != executable_simulation": true,
  "standalone_modified": false,
  "routing_modified": false,
  "gds_writer_modified": false
}
```

## Next Recommended Proof Task

- `delay_chain_testbench_template_contract`