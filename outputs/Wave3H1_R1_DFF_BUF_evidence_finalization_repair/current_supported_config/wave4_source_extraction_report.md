# Wave4 Source Extraction

- openyield_commit: `1c34428d8b913963c4971d093b1a7c2df97a2509`
- time_generate_path: `/data1/qujh/work/external/OpenYield/sram_compiler/subcircuits/time_generate.py`
- time_generate_sha256: `fa5277f078f79d5b43335c2dcd6e364625aa8ad17b7108d323b85e73dfeaae80`
- dff_constructor_signature:
```json
{
  "formal_parameters": [
    "nmos_model",
    "pmos_model",
    "pmos_width",
    "nmos_width",
    "length",
    "w_rc",
    "pi_res",
    "pi_cap"
  ],
  "source_text": "def __init__(self, nmos_model=\"NMOS_VTG\", pmos_model=\"PMOS_VTG\",\n                 # Base widths for NAND gate transistors\n                 pmos_width=5e-07, nmos_width=2.5e-07,\n                 length=0.05e-6,\n                 w_rc=False, pi_res=100 @ u_Ohm, pi_cap=0.001 @ u_pF,\n                 ):\n\n        super().__init__(\n            nmos_model, pmos_model,\n            nmos_width, pmos_width, length,\n            w_rc=w_rc, pi_res=pi_res, pi_cap=pi_cap,\n        ) \n        self.inv_dff = Pinv(nmos_model,pmos_model,2.5e-07, 5e-07,0.05e-6,num=1)\n        self.subcircuit(self.inv_dff)\n\n        self.trans_dff = TransmissionGate(\n            nmos_model=\"NMOS_VTG\",\n            pmos_model=\"PMOS_VTG\"\n        )\n        self.subcircuit(self.trans_dff)\n        # 构建传输门型触发器\n        self.add_dff()"
}
```
- source_derived_facts:
```json
{
  "ADDR_DFF": {
    "class_name": "ADDR_DFF",
    "class_present": true,
    "__init__": {
      "parameters": [
        "self",
        "nmos_model",
        "pmos_model",
        "pmos_width",
        "nmos_width",
        "length",
        "num_rows",
        "w_rc",
        "pi_res",
        "pi_cap"
      ],
      "self_num_rows_source": "num_rows",
      "n_bits_expression": "ceil(log2(self.num_rows)) if self.num_rows > 1 else 1",
      "nodes": {
        "construction_steps": [
          "nodes = ['VDD', 'VSS', 'CLK']",
          "nodes.extend([f'A{i}' for i in range(n_bits)])",
          "nodes.extend([f'A_dff{i}' for i in range(n_bits)])"
        ],
        "derived_order_summary": [
          "VDD",
          "VSS",
          "CLK",
          "[f'A{i}' for i in range(n_bits)]",
          "[f'A_dff{i}' for i in range(n_bits)]"
        ]
      }
    },
    "add_addr_dff_array": {
      "present": true,
      "parameters": [
        "self",
        "n_bits"
      ],
      "loop_range_expression": "range(n_bits)",
      "self_X": {
        "instance_name_expression": "f'dff_{i}'",
        "child_cell_expression": "self.dff_addr.NAME",
        "net_parameter_order": [
          "'VDD'",
          "'VSS'",
          "f'A{i}'",
          "f'A_dff{i}'",
          "'CLK'"
        ],
        "keyword_arguments": {},
        "source_text": "self.X(f'dff_{i}', self.dff_addr.NAME, \n                   'VDD', 'VSS', f'A{i}', f'A_dff{i}', 'CLK')"
      }
    },
    "dff_constructor_call": {
      "source_text": "dff(nmos_model, pmos_model)",
      "positional_arguments": [
        "nmos_model",
        "pmos_model"
      ],
      "keyword_arguments": {},
      "positional_bindings": [
        {
          "position": 1,
          "source_expression": "nmos_model",
          "actual_formal_parameter": "nmos_model"
        },
        {
          "position": 2,
          "source_expression": "pmos_model",
          "actual_formal_parameter": "pmos_model"
        }
      ],
      "uses_default_formals": [
        "pmos_width",
        "nmos_width",
        "length"
      ]
    }
  },
  "DATA_DFF": {
    "class_name": "DATA_DFF",
    "class_present": true,
    "__init__": {
      "parameters": [
        "self",
        "nmos_model",
        "pmos_model",
        "pmos_width",
        "nmos_width",
        "length",
        "num_cols",
        "w_rc",
        "pi_res",
        "pi_cap"
      ],
      "self_num_cols_source": "num_cols",
      "nodes": {
        "construction_steps": [
          "nodes = ['VDD', 'VSS', 'CLK']",
          "nodes.extend([f'DIN{i}' for i in range(num_cols)])",
          "nodes.extend([f'DIN_dff{i}' for i in range(num_cols)])"
        ],
        "derived_order_summary": [
          "VDD",
          "VSS",
          "CLK",
          "[f'DIN{i}' for i in range(num_cols)]",
          "[f'DIN_dff{i}' for i in range(num_cols)]"
        ]
      }
    },
    "add_data_dff_array": {
      "present": true,
      "parameters": [
        "self",
        "num_cols"
      ],
      "loop_range_expression": "range(num_cols)",
      "self_X": {
        "instance_name_expression": "f'dff_{i}'",
        "child_cell_expression": "self.dff_data.NAME",
        "net_parameter_order": [
          "'VDD'",
          "'VSS'",
          "f'DIN{i}'",
          "f'DIN_dff{i}'",
          "'CLK'"
        ],
        "keyword_arguments": {},
        "source_text": "self.X(f'dff_{i}', self.dff_data.NAME, \n                   'VDD', 'VSS', f'DIN{i}', f'DIN_dff{i}', 'CLK')"
      }
    },
    "dff_constructor_call": {
      "source_text": "dff(nmos_model, pmos_model, length)",
      "positional_arguments": [
        "nmos_model",
        "pmos_model",
        "length"
      ],
      "keyword_arguments": {},
      "positional_bindings": [
        {
          "position": 1,
          "source_expression": "nmos_model",
          "actual_formal_parameter": "nmos_model"
        },
        {
          "position": 2,
          "source_expression": "pmos_model",
          "actual_formal_parameter": "pmos_model"
        },
        {
          "position": 3,
          "source_expression": "length",
          "actual_formal_parameter": "pmos_width"
        }
      ]
    },
    "DATA_DFF_constructor_binding": {
      "third_positional_source_expression": "length",
      "actual_formal_parameter": "pmos_width",
      "exact_approved_DFF_binding_status": "UNRESOLVED_REQUIRES_WAVE4B_SOURCE_BINDING_REVIEW"
    }
  }
}
```
- project_execution_policy:
```json
{
  "locked_plan_next_wave": "Wave4 / ADDR_DFF / DATA_DFF",
  "execution_next_stage": "Wave4A / ADDR_DFF_SOURCE_TOPOLOGY_AND_BINDING_LOCK",
  "deferred_sibling_stage": "Wave4B / DATA_DFF",
  "same_wave": true,
  "independent_wave4_siblings": true,
  "current_supported_rows": 16,
  "current_supported_cols": 16,
  "current_supported_addr_dff_count": 4,
  "current_supported_data_dff_count": 16,
  "required_execution_order": [
    "ADDR_DFF",
    "DATA_DFF"
  ]
}
```
- later_stage_recommendation:
```json
{
  "ADDR_DFF": "Wave4A / ADDR_DFF_SOURCE_TOPOLOGY_AND_BINDING_LOCK",
  "DATA_DFF": "Wave4B / DATA_DFF with explicit constructor positional binding review"
}
```
