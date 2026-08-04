# Decoder Rebuild Contract Lock

- selected_config_id: `formal_16x16_wpr1`
- top_cell_name: `PROJECT_DECODER_REBUILD_16X16`
- openyield_commit: `1c34428d8b913963c4971d093b1a7c2df97a2509`
- decoder_py_blob: `03d791c1852c846dd5ae8c5a464ba89d71bf8180`
- wordline_driver_py_blob: `9b0875fa75e7c97f032cf9ba6d4823262e7d0333`
- topology: `decoder_cascade_1_plus_2`
- level0_enable_strategy: `decoder_gate_cells_v2_with_A0_A1_tied_to_VSS_and_EN_tied_to_VDD`
- level1_wordline_strategy: `two_decoder_gate_cells_v2_instances_driven_by_level0_WL0_WL1`

## Child Assets

- `upper_enable_stage`
  - module: `decoder_gate_cells_v2`
  - role: `level0_enable_decode`
  - gds_sha256: `8af15a3cfb41a9b0737731809c0539606067f86b9f62d18ebf2563fcabd96f18`
  - pin_names: `['A0', 'A1', 'A2', 'EN', 'VDD', 'VSS', 'WL0', 'WL0_pre', 'WL1', 'WL1_pre', 'WL2', 'WL2_pre', 'WL3', 'WL3_pre', 'WL4', 'WL4_pre', 'WL5', 'WL5_pre', 'WL6', 'WL6_pre', 'WL7', 'WL7_pre']`
  - pin_abstraction_complete: `True`
  - formal_connections: `{'EN': 'VDD', 'A0': 'VSS', 'A1': 'VSS', 'A2': 'A3'}`
- `lower_wordline_stage_0`
  - module: `decoder_gate_cells_v2`
  - role: `level1_wordline_decode_low`
  - gds_sha256: `8af15a3cfb41a9b0737731809c0539606067f86b9f62d18ebf2563fcabd96f18`
  - pin_names: `['A0', 'A1', 'A2', 'EN', 'VDD', 'VSS', 'WL0', 'WL0_pre', 'WL1', 'WL1_pre', 'WL2', 'WL2_pre', 'WL3', 'WL3_pre', 'WL4', 'WL4_pre', 'WL5', 'WL5_pre', 'WL6', 'WL6_pre', 'WL7', 'WL7_pre']`
  - pin_abstraction_complete: `True`
  - formal_connections: `{'EN': 'EN_0_0_0', 'A0': 'A2', 'A1': 'A1', 'A2': 'A0'}`
- `lower_wordline_stage_1`
  - module: `decoder_gate_cells_v2`
  - role: `level1_wordline_decode_high`
  - gds_sha256: `8af15a3cfb41a9b0737731809c0539606067f86b9f62d18ebf2563fcabd96f18`
  - pin_names: `['A0', 'A1', 'A2', 'EN', 'VDD', 'VSS', 'WL0', 'WL0_pre', 'WL1', 'WL1_pre', 'WL2', 'WL2_pre', 'WL3', 'WL3_pre', 'WL4', 'WL4_pre', 'WL5', 'WL5_pre', 'WL6', 'WL6_pre', 'WL7', 'WL7_pre']`
  - pin_abstraction_complete: `True`
  - formal_connections: `{'EN': 'EN_0_0_1', 'A0': 'A2', 'A1': 'A1', 'A2': 'A0'}`

## Known Limitations

- The selected child assets are project-owned regenerated v2 child candidates rather than historical decoder-top signoff assets.
- This contract lock reflects the OpenYield DECODER_CASCADE topology for 16 rows and supersedes the earlier three-module side-by-side placeholder composition.
- Formal inventory snapshot lines: 11
