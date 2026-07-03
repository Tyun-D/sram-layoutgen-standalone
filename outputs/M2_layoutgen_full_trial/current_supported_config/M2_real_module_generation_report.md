# M2 Real Module Generation Report

- layoutgen_real_generator_used_count: `8`
- first_round_openyield_gds_used_count: `8`
- temporary_wrapper_count: `12`

| openyield_module | physical_role | binding_status | physical_source_class | temporary_wrapper | region | source_note |
| --- | --- | --- | --- | --- | --- | --- |
| CONTROL_LOGIC | CONTROL_LOGIC | CONTROL_COMPOSITE_NEEDS_LAYOUTGEN_REGEN | temporary_wrapper | True | CONTROL_REGION | First-round candidate composite wrapped for M2 review and explicitly marked temporary. |
| DELAY_CHAIN | DELAY_CHAIN | CONTROL_COMPOSITE_NEEDS_LAYOUTGEN_REGEN | temporary_wrapper | True | CONTROL_REGION | First-round candidate composite wrapped for M2 review and explicitly marked temporary. |
| DFF_ROW | DFF_ROW | STD_CELL_ROW_NEEDS_LAYOUTGEN_REGEN | temporary_wrapper | True | CONTROL_REGION | First-round candidate composite wrapped for M2 review and explicitly marked temporary. |
| GATED_CLOCK_PATH | CLOCK_PATH | CLOCK_PATH_NEEDS_LAYOUTGEN_REGEN | temporary_wrapper | True | CONTROL_REGION | First-round candidate composite wrapped for M2 review and explicitly marked temporary. |
| PRECHARGE_ENABLE_PATH | ENABLE_PATH | ENABLE_PATH_NEEDS_LAYOUTGEN_REGEN | temporary_wrapper | True | CONTROL_REGION | First-round candidate composite wrapped for M2 review and explicitly marked temporary. |
| SENSE_ENABLE_PATH | ENABLE_PATH | ENABLE_PATH_NEEDS_LAYOUTGEN_REGEN | temporary_wrapper | True | CONTROL_REGION | First-round candidate composite wrapped for M2 review and explicitly marked temporary. |
| WORDLINE_ENABLE_PATH | ENABLE_PATH | ENABLE_PATH_NEEDS_LAYOUTGEN_REGEN | temporary_wrapper | True | CONTROL_REGION | First-round candidate composite wrapped for M2 review and explicitly marked temporary. |
| WRITE_ENABLE_PATH | ENABLE_PATH | ENABLE_PATH_NEEDS_LAYOUTGEN_REGEN | temporary_wrapper | True | CONTROL_REGION | First-round candidate composite wrapped for M2 review and explicitly marked temporary. |
| bitcell_array | ARRAY_CORE | REAL_ARRAY_BASE_REUSABLE | first_round_openyield_gds | False | ARRAY_CORE_REGION | Reuse first-round OpenYield module GDS directly for M2 review. |
| column_mux | COLUMN_MUX | REAL_HARDMACRO_WRAPPER_REUSABLE_WITH_REPAIRED_SOURCE | first_round_openyield_gds | False | COLUMN_PATH_REGION | Reuse first-round OpenYield module GDS directly for M2 review. |
| decoder_gate_cells | ROW_DECODER | CANDIDATE_ROW_COMPOSITE_NEEDS_LAYOUTGEN_REGEN | temporary_wrapper | True | ROW_PATH_REGION | First-round candidate composite wrapped for M2 review and explicitly marked temporary. |
| dummy_array | ARRAY_DUMMY | REAL_ARRAY_BASE_REUSABLE | first_round_openyield_gds | False | ARRAY_DUMMY_REGION | Reuse first-round OpenYield module GDS directly for M2 review. |
| precharge | COLUMN_PRECHARGE | REAL_HARDMACRO_WRAPPER_REUSABLE | first_round_openyield_gds | False | COLUMN_PATH_REGION | Reuse first-round OpenYield module GDS directly for M2 review. |
| replica_array | ARRAY_REPLICA | REAL_ARRAY_BASE_REUSABLE_WITH_REPLICA_RULES | first_round_openyield_gds | False | ARRAY_REPLICA_REGION | Reuse first-round OpenYield module GDS directly for M2 review. |
| row_decoder | ROW_DECODER | CANDIDATE_ROW_COMPOSITE_NEEDS_LAYOUTGEN_REGEN | temporary_wrapper | True | ROW_PATH_REGION | First-round candidate composite wrapped for M2 review and explicitly marked temporary. |
| sense_amp | SENSE_AMP | REAL_HARDMACRO_WRAPPER_REUSABLE | first_round_openyield_gds | False | COLUMN_PATH_REGION | Reuse first-round OpenYield module GDS directly for M2 review. |
| wordline_decoder | ROW_DECODER | CANDIDATE_ROW_COMPOSITE_NEEDS_LAYOUTGEN_REGEN | temporary_wrapper | True | ROW_PATH_REGION | First-round candidate composite wrapped for M2 review and explicitly marked temporary. |
| wordline_driver | WORDLINE_DRIVER | REAL_HARDMACRO_WRAPPER_REUSABLE | first_round_openyield_gds | False | ROW_PATH_REGION | Reuse first-round OpenYield module GDS directly for M2 review. |
| wordline_driver_gate_cells | WORDLINE_DRIVER | CANDIDATE_ROW_COMPOSITE_NEEDS_LAYOUTGEN_REGEN | temporary_wrapper | True | ROW_PATH_REGION | First-round candidate composite wrapped for M2 review and explicitly marked temporary. |
| write_driver | WRITE_DRIVER | REAL_HARDMACRO_WRAPPER_REUSABLE | first_round_openyield_gds | False | COLUMN_PATH_REGION | Reuse first-round OpenYield module GDS directly for M2 review. |
