# M9 Net Binding Matrix

- openyield_net_binding_count: `34`

| binding_id | net_name | target_module | target_pin | implementation_strategy | expected_routing_layer_hint |
| --- | --- | --- | --- | --- | --- |
| PINBIND_001_DFF_ROW | A[i] | DFF_ROW | A[i] | periphery_bus | control_or_address_bus_layer |
| PINBIND_002_row_decoder | A_dff[i] | row_decoder | A[i] | periphery_bus | control_or_address_bus_layer |
| PINBIND_003_wordline_driver | DEC_WL[i] | wordline_driver | A | horizontal_across_array_rows | row_path_and_wordline_distribution_layer |
| PINBIND_004_wordline_driver | WL_EN | wordline_driver | B | replica_chain_periphery_route | control_timing_layer |
| PINBIND_005_bitcell_array | WL[i] | bitcell_array | WL[i] | horizontal_across_array_rows | row_path_and_wordline_distribution_layer |
| PINBIND_006_precharge | BL[i];BLB[i] | precharge | BL/BLB | vertical_along_array_columns | bitline_stack |
| PINBIND_007_column_mux | BL[i];BLB[i] | column_mux | BL[i]/BLB[i] | vertical_along_array_columns | bitline_stack |
| PINBIND_008_sense_amp | SA_IN[*];SA_INB[*] | sense_amp | IN/INB | periphery_to_column_path | column_path_input_layer |
| PINBIND_009_sense_amp | BL[i];BLB[i] | sense_amp | IN/INB | vertical_along_array_columns | bitline_stack |
| PINBIND_010_SRAM_TOP | SA_Q[*];SA_QB[*] | SRAM_TOP | dout path | column_path_to_top_io | column_path_output_layer |
| PINBIND_011_DFF_ROW | DIN[i] | DFF_ROW | DIN[i] | periphery_to_column_path | column_path_input_layer |
| PINBIND_012_write_driver | DIN_dff[i] | write_driver | DIN | periphery_to_column_path | column_path_input_layer |
| PINBIND_013_write_driver | w_en | write_driver | EN | replica_chain_periphery_route | control_timing_layer |
| PINBIND_014_bitcell_array | BL[i];BLB[i] | bitcell_array | BL[i]/BLB[i] | vertical_along_array_columns | bitline_stack |
| PINBIND_015_DELAY_CHAIN | rbl | DELAY_CHAIN | in | vertical_along_array_columns | bitline_stack |
| PINBIND_016_SENSE_ENABLE_PATH | rbl_delay | SENSE_ENABLE_PATH | input | replica_chain_periphery_route | control_timing_layer |
| PINBIND_017_WRITE_ENABLE_PATH | rbl_delay_bar | WRITE_ENABLE_PATH | input | replica_chain_periphery_route | control_timing_layer |
| PINBIND_018_precharge | PRE | precharge | ENB | replica_chain_periphery_route | control_timing_layer |
| PINBIND_019_sense_amp | s_en | sense_amp | EN | replica_chain_periphery_route | control_timing_layer |
| PINBIND_020_DFF_ROW | clk_buf | DFF_ROW | CLK | top_clock_spine | clock_distribution_layer |
| PINBIND_021_GATED_CLOCK_PATH | gated_clk_bar;gated_clk_buf | GATED_CLOCK_PATH | internal gates | top_clock_spine | clock_distribution_layer |
| PINBIND_022_WORDLINE_ENABLE_PATH | wl_en | WORDLINE_ENABLE_PATH | derived output | replica_chain_periphery_route | control_timing_layer |
| PINBIND_023_PRECHARGE_ENABLE_PATH | PRE | PRECHARGE_ENABLE_PATH | derived output | replica_chain_periphery_route | control_timing_layer |
| PINBIND_024_WRITE_ENABLE_PATH | w_en | WRITE_ENABLE_PATH | derived output | replica_chain_periphery_route | control_timing_layer |
| PINBIND_025_SENSE_ENABLE_PATH | s_en | SENSE_ENABLE_PATH | derived output | replica_chain_periphery_route | control_timing_layer |
| PINBIND_026_all_modules | VDD;VSS | all_modules | power pins | top_level_rails_and_stitches | power_rail_layers |
| PINBIND_027_CONTROL_LOGIC | clk | CONTROL_LOGIC | clk | top_clock_spine | clock_distribution_layer |
| PINBIND_028_CONTROL_LOGIC | csb | CONTROL_LOGIC | csb | periphery_control_spine | control_bus_layer |
| PINBIND_029_CONTROL_LOGIC | web | CONTROL_LOGIC | web | periphery_control_spine | control_bus_layer |
| PINBIND_030_SRAM_TOP | DOUT[i] | SRAM_TOP | DOUT[i] | column_path_to_top_io | column_path_output_layer |
| PINBIND_031_ALL_MODULES | VDD | ALL_MODULES | VDD | top_level_rails_and_stitches | power_rail_layers |
| PINBIND_032_ALL_MODULES | VSS | ALL_MODULES | GND | top_level_rails_and_stitches | power_rail_layers |
| PINBIND_033_DELAY_CHAIN | RBL | DELAY_CHAIN | rbl | replica_chain_periphery_route | control_timing_layer |
| PINBIND_033_CONTROL_LOGIC | RBL | CONTROL_LOGIC | delay_in | replica_chain_periphery_route | control_timing_layer |
