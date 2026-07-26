# M2R Module Usage Matrix

| openyield_module | physical_role | binding_status | layoutgen_role | layoutgen_role_instance_count | physical_source_class | implementation | uses_first_round_openyield_gds | temporary_wrapper |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| CONTROL_LOGIC | CONTROL_LOGIC | CONTROL_COMPOSITE_NEEDS_LAYOUTGEN_REGEN | control_logic | 10 | layoutgen_top_flow_role | control DFF array / control glue | False | False |
| DELAY_CHAIN | DELAY_CHAIN | CONTROL_COMPOSITE_NEEDS_LAYOUTGEN_REGEN | delay_chain | 6 | layoutgen_top_flow_role | gen_delay_inv chain | False | False |
| DFF_ROW | DFF_ROW | STD_CELL_ROW_NEEDS_LAYOUTGEN_REGEN | data_dff | 8 | layoutgen_top_flow_role | data DFF array | False | False |
| GATED_CLOCK_PATH | CLOCK_PATH | CLOCK_PATH_NEEDS_LAYOUTGEN_REGEN | control_glue | 4 | layoutgen_top_flow_role | control glue | False | False |
| PRECHARGE_ENABLE_PATH | ENABLE_PATH | ENABLE_PATH_NEEDS_LAYOUTGEN_REGEN | control_glue | 4 | layoutgen_top_flow_role | control glue | False | False |
| SENSE_ENABLE_PATH | ENABLE_PATH | ENABLE_PATH_NEEDS_LAYOUTGEN_REGEN | control_glue | 4 | layoutgen_top_flow_role | control glue | False | False |
| WORDLINE_ENABLE_PATH | ENABLE_PATH | ENABLE_PATH_NEEDS_LAYOUTGEN_REGEN | control_glue | 4 | layoutgen_top_flow_role | control glue | False | False |
| WRITE_ENABLE_PATH | ENABLE_PATH | ENABLE_PATH_NEEDS_LAYOUTGEN_REGEN | control_glue | 4 | layoutgen_top_flow_role | control glue | False | False |
| bitcell_array | ARRAY_CORE | REAL_ARRAY_BASE_REUSABLE | bitcell_array | 512 | layoutgen_top_flow_role | cell_1rw array | False | False |
| column_mux | COLUMN_MUX | REAL_HARDMACRO_WRAPPER_REUSABLE_WITH_REPAIRED_SOURCE | column_mux | 32 | layoutgen_top_flow_role | gen_col_mux column path | False | False |
| decoder_gate_cells | ROW_DECODER | CANDIDATE_ROW_COMPOSITE_NEEDS_LAYOUTGEN_REGEN | row_decoder | 16 | layoutgen_top_flow_role | layoutgen generated decoder logic | False | False |
| dummy_array | ARRAY_DUMMY | REAL_ARRAY_BASE_REUSABLE | dummy_bitcell | 32 | layoutgen_top_flow_role | dummy_cell_1rw boundary arrays | False | False |
| precharge | COLUMN_PRECHARGE | REAL_HARDMACRO_WRAPPER_REUSABLE | precharge | 32 | layoutgen_top_flow_role | gen_precharge column path | False | False |
| replica_array | ARRAY_REPLICA | REAL_ARRAY_BASE_REUSABLE_WITH_REPLICA_RULES | replica_bitline | 16 | layoutgen_top_flow_role | replica_cell_1rw array plus replica precharge | False | False |
| row_decoder | ROW_DECODER | CANDIDATE_ROW_COMPOSITE_NEEDS_LAYOUTGEN_REGEN | row_decoder | 16 | layoutgen_top_flow_role | layoutgen generated decoder chain | False | False |
| sense_amp | SENSE_AMP | REAL_HARDMACRO_WRAPPER_REUSABLE | sense_amp | 8 | layoutgen_top_flow_role | sense_amp array | False | False |
| wordline_decoder | ROW_DECODER | CANDIDATE_ROW_COMPOSITE_NEEDS_LAYOUTGEN_REGEN | row_decoder | 16 | layoutgen_top_flow_role | layoutgen generated decoder chain | False | False |
| wordline_driver | WORDLINE_DRIVER | REAL_HARDMACRO_WRAPPER_REUSABLE | wordline_driver | 16 | layoutgen_top_flow_role | gen_wl_driver row path | False | False |
| wordline_driver_gate_cells | WORDLINE_DRIVER | CANDIDATE_ROW_COMPOSITE_NEEDS_LAYOUTGEN_REGEN | wordline_driver | 16 | layoutgen_top_flow_role | gen_wl_driver row path | False | False |
| write_driver | WRITE_DRIVER | REAL_HARDMACRO_WRAPPER_REUSABLE | write_driver | 8 | layoutgen_top_flow_role | write_driver array | False | False |
