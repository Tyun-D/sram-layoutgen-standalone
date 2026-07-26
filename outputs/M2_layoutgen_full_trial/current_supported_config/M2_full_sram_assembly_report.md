# M2 Full SRAM Assembly Report

- top_cell_name: `openyield_layoutgen_full_trial_sram`
- top_gds_path: `/data1/qujh/work/sram_layoutgen_step45_clean/outputs/M2_layoutgen_full_trial/current_supported_config/openyield_layoutgen_full_trial_sram.gds`
- placed_instance_count: `20`
- top_bbox: `{'x0': 8.7175, 'y0': 12.0, 'x1': 42.81, 'y1': 41.12, 'width': 34.0925, 'height': 29.12}`

| module_name | physical_role | source_class | region | x | y | width | height |
| --- | --- | --- | --- | --- | --- | --- | --- |
| bitcell_array | ARRAY_CORE | first_round_openyield_gds | ARRAY_CORE_REGION | 16.0 | 12.0 | 3.58 | 6.26 |
| dummy_array | ARRAY_DUMMY | first_round_openyield_gds | ARRAY_DUMMY_REGION | 10.42 | 12.0 | 3.58 | 6.26 |
| replica_array | ARRAY_REPLICA | first_round_openyield_gds | ARRAY_REPLICA_REGION | 21.58 | 12.0 | 1.79 | 7.68 |
| row_decoder | ROW_DECODER | temporary_wrapper | ROW_PATH_REGION | 9.754999999999999 | 12.0 | 4.245 | 3.13 |
| wordline_decoder | ROW_DECODER | temporary_wrapper | ROW_PATH_REGION | 9.754999999999999 | 15.93 | 4.245 | 3.045 |
| decoder_gate_cells | ROW_DECODER | temporary_wrapper | ROW_PATH_REGION | 8.717500000000001 | 19.775 | 5.2825 | 3.045 |
| wordline_driver | WORDLINE_DRIVER | first_round_openyield_gds | ROW_PATH_REGION | 10.955 | 23.619999999999997 | 3.045 | 1.505 |
| wordline_driver_gate_cells | WORDLINE_DRIVER | temporary_wrapper | ROW_PATH_REGION | 11.1025 | 25.924999999999997 | 2.8975 | 2.96 |
| precharge | COLUMN_PRECHARGE | first_round_openyield_gds | COLUMN_PATH_REGION | 16.0 | 20.259999999999998 | 0.785 | 1.42 |
| column_mux | COLUMN_MUX | first_round_openyield_gds | COLUMN_PATH_REGION | 17.785 | 20.259999999999998 | 0.8175 | 1.88 |
| sense_amp | SENSE_AMP | first_round_openyield_gds | COLUMN_PATH_REGION | 19.6025 | 20.259999999999998 | 0.775 | 6.01 |
| write_driver | WRITE_DRIVER | first_round_openyield_gds | COLUMN_PATH_REGION | 21.377499999999998 | 20.259999999999998 | 0.84 | 4.175 |
| CONTROL_LOGIC | CONTROL_LOGIC | temporary_wrapper | CONTROL_REGION | 26.369999999999997 | 20.259999999999998 | 6.105 | 4.235 |
| DELAY_CHAIN | DELAY_CHAIN | temporary_wrapper | CONTROL_REGION | 26.369999999999997 | 25.294999999999998 | 3.29 | 2.585 |
| PRECHARGE_ENABLE_PATH | ENABLE_PATH | temporary_wrapper | CONTROL_REGION | 26.369999999999997 | 28.68 | 4.245 | 4.065 |
| SENSE_ENABLE_PATH | ENABLE_PATH | temporary_wrapper | CONTROL_REGION | 26.369999999999997 | 33.545 | 3.4225 | 7.575 |
| WRITE_ENABLE_PATH | ENABLE_PATH | temporary_wrapper | CONTROL_REGION | 31.369999999999997 | 20.259999999999998 | 1.6625 | 6.76 |
| WORDLINE_ENABLE_PATH | ENABLE_PATH | temporary_wrapper | CONTROL_REGION | 31.369999999999997 | 27.819999999999997 | 3.8675 | 3.07 |
| GATED_CLOCK_PATH | CLOCK_PATH | temporary_wrapper | CONTROL_REGION | 31.369999999999997 | 31.689999999999998 | 2.6825 | 2.96 |
| DFF_ROW | DFF_ROW | temporary_wrapper | CONTROL_REGION | 31.369999999999997 | 35.449999999999996 | 11.44 | 2.67 |
