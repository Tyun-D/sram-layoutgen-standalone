# SRAM Spec

## Locked Parameters

- word_size: `8`
- num_words: `64`
- words_per_row: `4`
- num_rows: `16`
- num_cols: `32`
- num_banks: `1`
- num_ports: `1`
- tech: `freepdk45`
- bitcell_pitch_x: `0.895`
- bitcell_pitch_y: `1.465`
- column_mux_ratio: `4`
- mux_enabled: `True`
- dummy_enabled: `True`
- replica_enabled: `True`
- power_rail_overlap_enabled: `True`
- power_stitch_enabled: `True`
- rail_abutment_enabled: `True`
- top_pin_strategy: `perimeter_pins_from_layoutgen_geometry`
- generator_entry_script: `/data1/qujh/work/sram_layoutgen_step45_clean/scripts/openyield_generate_layout_prototype.py`
- generator_function: `sram_layoutgen.standalone.write_standalone`
- reference_gds_path: `/data1/qujh/work/sram_layoutgen_step45_clean/outputs/layout_prototype/hybrid_openyield_rail_overlap/hybrid_openyield_rail_overlap.complete.gds`
- expected_output_gds_path: `/data1/qujh/work/sram_layoutgen_step45_clean/outputs/M6_layoutgen_spec_reproduce/current_supported_config/layoutgen_optimized_reproduced_sram.gds`

## Reference Evidence

- reference_name: `hybrid_openyield_rail_overlap`
- reference_width_um: `42.77249999999998`
- reference_height_um: `47.34500000000001`
- reference_vertical_abutment_policy: `same_net_power_rail_overlap_packing`
- baseline_reference_name: `sram_8x64_wpr4_fd45`

- derivation_basis: `outputs/layout_prototype/baseline_legacy/prototype_result.json` and `outputs/layout_prototype/hybrid_openyield_rail_overlap/prototype_result.json` both lock the case to 8x64_wpr4.
