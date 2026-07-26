# ADDR_DFF Config Resolution

- time_init_formal_parameters:
```json
[
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
```
- time_num_rows_default_source: `16`
- time_addr_dff_constructor_call:
```json
{
  "source_text": "dff_buf_addr=ADDR_DFF(nmos_model=\"NMOS_VTG\",\n            pmos_model=\"PMOS_VTG\",num_rows=self.num_rows)",
  "positional_arguments": [],
  "keyword_arguments": {
    "nmos_model": "\"NMOS_VTG\"",
    "pmos_model": "\"PMOS_VTG\"",
    "num_rows": "self.num_rows"
  }
}
```
- current_authority_candidates:
```json
[
  {
    "path": "/data1/qujh/work/sram_layoutgen_step45_clean/outputs/M8_reproduce_uploaded_golden/current_supported_config/SRAM_SPEC.json",
    "source_category": "current_layoutgen_sram_spec",
    "current_or_historical": "current",
    "content_sha256": "bafd91115ef6e8c616c775b0d83ffa058e7744229d55f84da4235e91249212ed",
    "parsed_num_rows": 16,
    "precedence": 10,
    "selected_or_rejected_reason": "selected_current_authority_consensus"
  },
  {
    "path": "/data1/qujh/work/sram_layoutgen_step45_clean/outputs/M9_openyield_netlist_translator/current_supported_config/M9_SRAM_SPEC.json",
    "source_category": "current_openyield_layoutgen_spec",
    "current_or_historical": "current",
    "content_sha256": "c9daa330b3e685cc18d6bdd811b768e6f44cc16cc1011223f8762179fb936247",
    "parsed_num_rows": 16,
    "precedence": 20,
    "selected_or_rejected_reason": "selected_current_authority_consensus"
  },
  {
    "path": "1c34428d8b913963c4971d093b1a7c2df97a2509:sram_compiler/config_yaml/global.yaml",
    "source_category": "locked_openyield_global_yaml_blob",
    "current_or_historical": "current",
    "content_sha256": "a0927167d2db7d9730fc239065cd345c93c323d7de9f68b9351da3c03adba94f",
    "parsed_num_rows": 16,
    "precedence": 30,
    "selected_or_rejected_reason": "selected_current_authority_consensus"
  },
  {
    "path": "1c34428d8b913963c4971d093b1a7c2df97a2509:sram_compiler/subcircuits/time_generate.py::TIME.__init__.num_rows_default",
    "source_category": "locked_time_generate_ast_default",
    "current_or_historical": "current",
    "content_sha256": "fa5277f078f79d5b43335c2dcd6e364625aa8ad17b7108d323b85e73dfeaae80",
    "parsed_num_rows": 16,
    "precedence": 40,
    "selected_or_rejected_reason": "selected_current_authority_consensus"
  }
]
```
- current_authority_values:
```json
[
  16
]
```
- num_rows_authority_conflict: `False`
- resolved_num_rows: `16`
- resolved_n_bits: `4`
- all_current_authorities_equal_16: `True`
