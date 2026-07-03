# M3R OpenYield Net To Physical Pin Map

| binding_id | net_name | net_category | layout_role | source_module | source_pin | target_module | target_pin | physical_binding_kind | physical_pin_or_region | routing_layer_hint | intent_status | semantic_exported_to_gds |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| PINBIND_001_DFF_ROW | A[i] | ADDRESS | address_distribution | SRAM_TOP | A[i] | DFF_ROW | A[i] | region_fallback | semantic_region_anchor | control_or_address_bus_layer | MAPPED | True |
| PINBIND_002_row_decoder | A_dff[i] | ADDRESS | address_distribution | DFF_ROW | A_dff[i] | row_decoder | A[i] | region_fallback | semantic_region_anchor | control_or_address_bus_layer | MAPPED | True |
| PINBIND_003_wordline_driver | DEC_WL[i] | WORDLINE | row_pitch_aligned_wordline | row_decoder | WL[i] | wordline_driver | A | region_fallback | semantic_region_anchor | row_path_and_wordline_distribution_layer | MAPPED | True |
| PINBIND_004_wordline_driver | WL_EN | TIMING_REPLICA | replica_timing_distribution | CONTROL_LOGIC | wl_en | wordline_driver | B | region_fallback | semantic_region_anchor | control_timing_layer | MAPPED | True |
| PINBIND_005_bitcell_array | WL[i] | WORDLINE | row_pitch_aligned_wordline | wordline_driver | Z | bitcell_array | WL[i] | region_fallback | semantic_region_anchor | row_path_and_wordline_distribution_layer | MAPPED | True |
| PINBIND_006_precharge | BL[i];BLB[i] | BITLINE_BAR | column_pitch_aligned_bitline_bar | bitcell_array | BL[i]/BLB[i] | precharge | BL/BLB | region_fallback | semantic_region_anchor | bitline_stack | MAPPED | True |
| PINBIND_007_column_mux | BL[i];BLB[i] | BITLINE_BAR | column_pitch_aligned_bitline_bar | precharge | BL/BLB | column_mux | BL[i]/BLB[i] | region_fallback | semantic_region_anchor | bitline_stack | MAPPED | True |
| PINBIND_008_sense_amp | SA_IN[*];SA_INB[*] | DATA_IN | write_data_delivery | column_mux | SA_IN/SA_INB | sense_amp | IN/INB | region_fallback | semantic_region_anchor | column_path_input_layer | MAPPED | True |
| PINBIND_009_sense_amp | BL[i];BLB[i] | BITLINE_BAR | column_pitch_aligned_bitline_bar | bitcell_array | BL[i]/BLB[i] | sense_amp | IN/INB | region_fallback | semantic_region_anchor | bitline_stack | MAPPED | True |
| PINBIND_010_SRAM_TOP | SA_Q[*];SA_QB[*] | DATA_OUT | read_data_observation | sense_amp | Q/QB | SRAM_TOP | dout path | region_fallback | semantic_region_anchor | column_path_output_layer | MAPPED | True |
| PINBIND_011_DFF_ROW | DIN[i] | DATA_IN | write_data_delivery | SRAM_TOP | DIN[i] | DFF_ROW | DIN[i] | top_pin:DIN[0] | din[0] | column_path_input_layer | MAPPED | True |
| PINBIND_012_write_driver | DIN_dff[i] | DATA_IN | write_data_delivery | DFF_ROW | DIN_dff[i] | write_driver | DIN | region_fallback | semantic_region_anchor | column_path_input_layer | MAPPED | True |
| PINBIND_013_write_driver | w_en | TIMING_REPLICA | replica_timing_distribution | CONTROL_LOGIC | w_en | write_driver | EN | region_fallback | semantic_region_anchor | control_timing_layer | MAPPED | True |
| PINBIND_014_bitcell_array | BL[i];BLB[i] | BITLINE_BAR | column_pitch_aligned_bitline_bar | write_driver | BL/BLB | bitcell_array | BL[i]/BLB[i] | region_fallback | semantic_region_anchor | bitline_stack | MAPPED | True |
| PINBIND_015_DELAY_CHAIN | rbl | BITLINE | column_pitch_aligned_bitline | replica_array | RBL/RBLB | DELAY_CHAIN | in | region_fallback | semantic_region_anchor | bitline_stack | MAPPED | True |
| PINBIND_016_SENSE_ENABLE_PATH | rbl_delay | TIMING_REPLICA | replica_timing_distribution | DELAY_CHAIN | out | SENSE_ENABLE_PATH | input | region_fallback | semantic_region_anchor | control_timing_layer | MAPPED | True |
| PINBIND_017_WRITE_ENABLE_PATH | rbl_delay_bar | TIMING_REPLICA | replica_timing_distribution | DELAY_CHAIN | out_bar | WRITE_ENABLE_PATH | input | region_fallback | semantic_region_anchor | control_timing_layer | MAPPED | True |
| PINBIND_018_precharge | PRE | TIMING_REPLICA | replica_timing_distribution | CONTROL_LOGIC | PRE | precharge | ENB | region_fallback | semantic_region_anchor | control_timing_layer | MAPPED | True |
| PINBIND_019_sense_amp | s_en | TIMING_REPLICA | replica_timing_distribution | CONTROL_LOGIC | s_en | sense_amp | EN | region_fallback | semantic_region_anchor | control_timing_layer | MAPPED | True |
| PINBIND_020_DFF_ROW | clk_buf | CLOCK | clock_distribution | CONTROL_LOGIC | clk_buf | DFF_ROW | CLK | top_pin:CLK | clk | clock_distribution_layer | MAPPED | True |
| PINBIND_021_GATED_CLOCK_PATH | gated_clk_bar;gated_clk_buf | CLOCK | clock_distribution | CONTROL_LOGIC | gated_clk_bar/gated_clk_buf | GATED_CLOCK_PATH | internal gates | region_fallback | semantic_region_anchor | clock_distribution_layer | MAPPED | True |
| PINBIND_022_WORDLINE_ENABLE_PATH | wl_en | TIMING_REPLICA | replica_timing_distribution | CONTROL_LOGIC | wl_en | WORDLINE_ENABLE_PATH | derived output | region_fallback | semantic_region_anchor | control_timing_layer | MAPPED | True |
| PINBIND_023_PRECHARGE_ENABLE_PATH | PRE | TIMING_REPLICA | replica_timing_distribution | CONTROL_LOGIC | PRE | PRECHARGE_ENABLE_PATH | derived output | region_fallback | semantic_region_anchor | control_timing_layer | MAPPED | True |
| PINBIND_024_WRITE_ENABLE_PATH | w_en | TIMING_REPLICA | replica_timing_distribution | CONTROL_LOGIC | w_en | WRITE_ENABLE_PATH | derived output | region_fallback | semantic_region_anchor | control_timing_layer | MAPPED | True |
| PINBIND_025_SENSE_ENABLE_PATH | s_en | TIMING_REPLICA | replica_timing_distribution | CONTROL_LOGIC | s_en | SENSE_ENABLE_PATH | derived output | region_fallback | semantic_region_anchor | control_timing_layer | MAPPED | True |
| PINBIND_026_all_modules | VDD;VSS | POWER | power_distribution | VDD/GND | VDD/VSS | all_modules | power pins | top_pin:VDD | vdd | power_rail_layers | MAPPED | True |
| PINBIND_027_CONTROL_LOGIC | clk | CLOCK | clock_distribution | SRAM_TOP | clk | CONTROL_LOGIC | clk | top_pin:clk | clk | clock_distribution_layer | MAPPED | True |
| PINBIND_028_CONTROL_LOGIC | csb | CONTROL | control_enable_distribution | SRAM_TOP | csb | CONTROL_LOGIC | csb | top_pin:csb | csb | control_bus_layer | MAPPED | True |
| PINBIND_029_CONTROL_LOGIC | web | CONTROL | control_enable_distribution | SRAM_TOP | web | CONTROL_LOGIC | web | top_pin:web | web | control_bus_layer | MAPPED | True |
| PINBIND_030_SRAM_TOP | DOUT[i] | DATA_OUT | read_data_observation | sense_amp | dout | SRAM_TOP | DOUT[i] | top_pin:DOUT[0] | dout[0] | column_path_output_layer | MAPPED | True |
| PINBIND_031_ALL_MODULES | VDD | POWER | power_distribution | SRAM_TOP | VDD | ALL_MODULES | VDD | top_pin:VDD | vdd | power_rail_layers | MAPPED | True |
| PINBIND_032_ALL_MODULES | VSS | GROUND | ground_distribution | SRAM_TOP | VSS | ALL_MODULES | GND | top_pin:GND | gnd | power_rail_layers | MAPPED | True |
| PINBIND_033_DELAY_CHAIN | RBL | TIMING_REPLICA | replica_timing_distribution | replica_array | RBL | DELAY_CHAIN | rbl | region_fallback | semantic_region_anchor | control_timing_layer | MAPPED | True |
| PINBIND_033_CONTROL_LOGIC | RBL | TIMING_REPLICA | replica_timing_distribution | replica_array | RBL | CONTROL_LOGIC | delay_in | region_fallback | semantic_region_anchor | control_timing_layer | MAPPED | True |
