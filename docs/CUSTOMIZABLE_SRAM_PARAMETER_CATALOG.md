# Customizable SRAM Parameter Catalog

- total parameters: `25`
- support counts: `{'SUPPORTED_WITH_CONSTRAINTS': 17, 'PARTIALLY_SUPPORTED': 5, 'NOT_IMPLEMENTED': 1, 'EXPERIMENTAL': 1, 'FULLY_SUPPORTED': 1}`

| parameter_name | support_level | default_value | currently_supported | tested_configs | known_constraints |
| --- | --- | --- | --- | --- | --- |
| word_count | SUPPORTED_WITH_CONSTRAINTS | 64 | True | 8x64_wpr4;4x32_wpr2;16x16_wpr1 | current delivery still uses fallback for some logical fields |
| word_size | SUPPORTED_WITH_CONSTRAINTS | 8 | True | 8x64_wpr4;4x32_wpr2;16x16_wpr1 | raw source still partly fallback-backed |
| address_bits | SUPPORTED_WITH_CONSTRAINTS | 6 | True | 8x64_wpr4;4x32_wpr2 | derived rather than independently set |
| num_rows | PARTIALLY_SUPPORTED | 16 | True | 16x16_wpr1;8x64_wpr4 | only 16 physically instantiated in project evidence |
| num_cols | PARTIALLY_SUPPORTED | 32 | True | 16x16_wpr1;8x64_wpr4;4x32_wpr2 | only 8/16/32 explicitly evidenced |
| bank_count | SUPPORTED_WITH_CONSTRAINTS | 1 | True | 8x64_wpr4 | single-bank only in current evidence |
| words_per_row | SUPPORTED_WITH_CONSTRAINTS | 4 | True | 16x16_wpr1;4x32_wpr2;8x64_wpr4 | full raw-backed logical path incomplete |
| column_mux_ratio | SUPPORTED_WITH_CONSTRAINTS | 4 | True | 16x16_wpr1;4x32_wpr2;8x64_wpr4 | coupled to choose_columnmux |
| bitcell_array_rows_cols | SUPPORTED_WITH_CONSTRAINTS | 16x32 | True | 8x64_wpr4 | current evidence concentrated on 16x32 |
| dummy_row_column | SUPPORTED_WITH_CONSTRAINTS | enabled | True | 8x64_wpr4 | enable/count not exposed as stable public knob |
| tap_spacing | NOT_IMPLEMENTED | bundled default | False |  | leaf exists but no exposed project parameter |
| replica_cell | SUPPORTED_WITH_CONSTRAINTS | enabled | True | 8x64_wpr4 | no alternate replica structures evidenced |
| precharge_structure | SUPPORTED_WITH_CONSTRAINTS | bundled precharge | True | 8x64_wpr4 | single proven structure |
| sense_amp_structure | SUPPORTED_WITH_CONSTRAINTS | bundled sense_amp | True | 8x64_wpr4 | QB treatment caveat remains explicit |
| write_driver_structure | PARTIALLY_SUPPORTED | bundled write_driver | True | 8x64_wpr4 | adapter exists but no dedicated final qualification wave |
| wl_driver_stages_sizes | PARTIALLY_SUPPORTED | bundled macro | True | 8x64_wpr4;Team B zero-gap chain | current project has two separate proof lines |
| decoder_architecture | EXPERIMENTAL | legacy row decoder path | False |  | no final legal placement closure |
| delay_chain_stage_count | SUPPORTED_WITH_CONSTRAINTS | 9/4 | True | delay_chain=9x4;wen_delay_chain=4x4 | only locked baseline counts verified |
| delay_chain_load_count | SUPPORTED_WITH_CONSTRAINTS | 4 | True | delay_chain=9x4;wen_delay_chain=4x4 | arbitrary load counts not formally qualified |
| buffer_inverter_sizes | SUPPORTED_WITH_CONSTRAINTS | baseline locked family | True | PINV family; PNAND2/3; pdrive | only approved variants should be reused |
| dff_variant | SUPPORTED_WITH_CONSTRAINTS | approved release | True | DFF reusable release; DFF_BUF reusable release | single approved variants only |
| power_rail_width_direction_stitch | SUPPORTED_WITH_CONSTRAINTS | fixed baseline | True | M2R top power rails; Team B zero-gap parent stitching | not generalized into project-wide public parameter |
| pin_location_access_strategy | SUPPORTED_WITH_CONSTRAINTS | current project defaults | True | M2R perimeter pins; Team B pin-access proofs | strategy differs between top-level and Team B library |
| module_spacing_abutment_strategy | PARTIALLY_SUPPORTED | mixed baseline | True | Team B AND2/AND3 zero-gap; inverter-chain zero-gap | general project-wide abutment framework not finished |
| pdk | FULLY_SUPPORTED | freepdk45 | True | freepdk45 | single-PDK project baseline |
