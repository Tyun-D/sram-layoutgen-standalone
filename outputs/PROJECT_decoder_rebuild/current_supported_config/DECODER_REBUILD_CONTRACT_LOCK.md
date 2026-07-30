# Decoder Rebuild Contract Lock

- selected_config_id: `formal_16x16_wpr1`
- top_cell_name: `PROJECT_DECODER_REBUILD_16X16`
- openyield_commit: `1c34428d8b913963c4971d093b1a7c2df97a2509`
- decoder_py_blob: `03d791c1852c846dd5ae8c5a464ba89d71bf8180`
- wordline_driver_py_blob: `9b0875fa75e7c97f032cf9ba6d4823262e7d0333`
- en_strategy: `horizontal_m3_bus`
- wl_pre_strategy: `vertical_m2_link`

## Child Assets

- `decoder_gate_cells`
  - gds_sha256: `27c050ae04593e536fb4a8b890e48d62657161fa1499e01f6188e41fc5b64c67`
  - pin_names: `['A[*]', 'GND', 'VDD', 'dec_stage[*]', 'enable']`
  - pin_abstraction_complete: `False`
- `row_decoder`
  - gds_sha256: `fe84bd37c4d5671aef6222cfe42991a72be84e1d5fe569ac53aa72d1a1e3e76c`
  - pin_names: `['A[*]', 'GND', 'VDD', 'dec_out[*]', 'enable']`
  - pin_abstraction_complete: `False`
- `wordline_decoder`
  - gds_sha256: `abeca5eaa4e5993ce8f83ce62f361800b1c2f6654e696df9775be6342c155e55`
  - pin_names: `['A[*]', 'DEC_WL[*]', 'GND', 'VDD', 'enable']`
  - pin_abstraction_complete: `False`

## Known Limitations

- All currently approved decoder child module pin maps export wildcard bus labels rather than bit-exact pins.
- The selected child assets are candidate module geometry, not previously closed decoder top-level routing.
- This contract lock is sufficient for executable rebuild/validation, but not sufficient to claim pre-validated decoder route closure.
- Formal inventory snapshot lines: 11
