# ADDR_DFF AST Extraction

- source_label: `1c34428d8b913963c4971d093b1a7c2df97a2509:sram_compiler/subcircuits/time_generate.py`
- addr_dff:
```json
{
  "__init__": {
    "formal_parameters": [
      {
        "parameter": "self",
        "kind": "positional",
        "default_source": null
      },
      {
        "parameter": "nmos_model",
        "kind": "positional",
        "default_source": "'NMOS_VTG'"
      },
      {
        "parameter": "pmos_model",
        "kind": "positional",
        "default_source": "'PMOS_VTG'"
      },
      {
        "parameter": "pmos_width",
        "kind": "positional",
        "default_source": "5e-07"
      },
      {
        "parameter": "nmos_width",
        "kind": "positional",
        "default_source": "2.5e-07"
      },
      {
        "parameter": "length",
        "kind": "positional",
        "default_source": "5e-08"
      },
      {
        "parameter": "num_rows",
        "kind": "positional",
        "default_source": "16"
      },
      {
        "parameter": "w_rc",
        "kind": "positional",
        "default_source": "False"
      },
      {
        "parameter": "pi_res",
        "kind": "positional",
        "default_source": "100 @ u_Ohm"
      },
      {
        "parameter": "pi_cap",
        "kind": "positional",
        "default_source": "0.001 @ u_pF"
      }
    ]
  },
  "self_num_rows_source": "num_rows",
  "nodes_initial_value": [
    "VDD",
    "VSS",
    "CLK"
  ],
  "nodes_extend_expressions": [
    "[f'A{i}' for i in range(n_bits)]",
    "[f'A_dff{i}' for i in range(n_bits)]"
  ],
  "n_bits_expressions": [
    "ceil(log2(self.num_rows)) if self.num_rows > 1 else 1",
    "ceil(log2(self.num_rows)) if self.num_rows > 1 else 1"
  ],
  "dff_addr_constructor": {
    "source_text": "self.dff_addr = dff(nmos_model, pmos_model)",
    "positional_arguments": [
      "nmos_model",
      "pmos_model"
    ],
    "keyword_arguments": {}
  },
  "subcircuit_call_source": "self.subcircuit(self.dff_addr)",
  "add_addr_dff_array_call": {
    "source_text": "self.add_addr_dff_array(n_bits)",
    "arguments": [
      "n_bits"
    ]
  },
  "add_addr_dff_array": {
    "formal_parameters": [
      {
        "parameter": "self",
        "kind": "positional",
        "default_source": null
      },
      {
        "parameter": "n_bits",
        "kind": "positional",
        "default_source": null
      }
    ],
    "loop_target": "i",
    "loop_iterator": "range(n_bits)",
    "self_x_instance_name_expression": "f'dff_{i}'",
    "self_x_child_expression": "self.dff_addr.NAME",
    "self_x_net_argument_order": [
      "'VDD'",
      "'VSS'",
      "f'A{i}'",
      "f'A_dff{i}'",
      "'CLK'"
    ]
  }
}
```
- time:
```json
{
  "__init__": {
    "formal_parameters": [
      {
        "parameter": "self",
        "kind": "positional",
        "default_source": null
      },
      {
        "parameter": "nmos_model",
        "kind": "positional",
        "default_source": "'NMOS_VTG'"
      },
      {
        "parameter": "pmos_model",
        "kind": "positional",
        "default_source": "'PMOS_VTG'"
      },
      {
        "parameter": "pmos_width",
        "kind": "positional",
        "default_source": "2.7e-07"
      },
      {
        "parameter": "nmos_width",
        "kind": "positional",
        "default_source": "1.8e-07"
      },
      {
        "parameter": "length",
        "kind": "positional",
        "default_source": "5e-08"
      },
      {
        "parameter": "num_rows",
        "kind": "positional",
        "default_source": "16"
      },
      {
        "parameter": "num_cols",
        "kind": "positional",
        "default_source": "8"
      },
      {
        "parameter": "w_rc",
        "kind": "positional",
        "default_source": "False"
      },
      {
        "parameter": "pi_res",
        "kind": "positional",
        "default_source": "100 @ u_Ohm"
      },
      {
        "parameter": "pi_cap",
        "kind": "positional",
        "default_source": "0.001 @ u_pF"
      },
      {
        "parameter": "operation",
        "kind": "positional",
        "default_source": "'read'"
      }
    ]
  },
  "addr_dff_constructor_call": {
    "source_text": "dff_buf_addr=ADDR_DFF(nmos_model=\"NMOS_VTG\",\n            pmos_model=\"PMOS_VTG\",num_rows=self.num_rows)",
    "positional_arguments": [],
    "keyword_arguments": {
      "nmos_model": "\"NMOS_VTG\"",
      "pmos_model": "\"PMOS_VTG\"",
      "num_rows": "self.num_rows"
    }
  },
  "addr_dff_connections_initial": [
    "VDD",
    "VSS",
    "clk_buf"
  ],
  "addr_dff_connection_loops": [
    {
      "loop_target": "i",
      "loop_iterator": "range(self.n_bits)",
      "append_expressions": [
        "f'A{i}'"
      ]
    },
    {
      "loop_target": "i",
      "loop_iterator": "range(self.n_bits)",
      "append_expressions": [
        "f'A_dff{i}'"
      ]
    }
  ],
  "dff_buf_addr_instance_call": {
    "instance_name_expression": "'dff_buf_addr'",
    "child_expression": "dff_buf_addr.NAME",
    "remaining_arguments": [
      "*addr_dff_connections"
    ]
  }
}
```
- dff:
```json
{
  "__init__": {
    "formal_parameters": [
      {
        "parameter": "self",
        "kind": "positional",
        "default_source": null
      },
      {
        "parameter": "nmos_model",
        "kind": "positional",
        "default_source": "'NMOS_VTG'"
      },
      {
        "parameter": "pmos_model",
        "kind": "positional",
        "default_source": "'PMOS_VTG'"
      },
      {
        "parameter": "pmos_width",
        "kind": "positional",
        "default_source": "5e-07"
      },
      {
        "parameter": "nmos_width",
        "kind": "positional",
        "default_source": "2.5e-07"
      },
      {
        "parameter": "length",
        "kind": "positional",
        "default_source": "5e-08"
      },
      {
        "parameter": "w_rc",
        "kind": "positional",
        "default_source": "False"
      },
      {
        "parameter": "pi_res",
        "kind": "positional",
        "default_source": "100 @ u_Ohm"
      },
      {
        "parameter": "pi_cap",
        "kind": "positional",
        "default_source": "0.001 @ u_pF"
      }
    ]
  }
}
```
