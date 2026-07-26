# M9 Module Binding Matrix

- openyield_module_count: `20`

| openyield_module | openyield_physical_role | implementation_mode | layoutgen_target_generator | layoutgen_target_cell | physical_group_cell |
| --- | --- | --- | --- | --- | --- |
| CONTROL_LOGIC | CONTROL_LOGIC | LAYOUTGEN_FALLBACK_WITH_OPENYIELD_SEMANTICS | StandaloneSRAMGenerator.control_logic_fallback | control_logic;control_glue | openyield_netlist_translated_sram__phys__control_backbone |
| DELAY_CHAIN | DELAY_CHAIN | PARAMETERIZED_LAYOUTGEN_GENERATOR | StandaloneSRAMGenerator.delay_chain_row | gen_delay_inv chain | openyield_netlist_translated_sram__phys__delay_chain |
| DFF_ROW | DFF_ROW | PARAMETERIZED_LAYOUTGEN_GENERATOR | StandaloneSRAMGenerator.data_dff_packing | dff array | openyield_netlist_translated_sram__phys__dff_row |
| GATED_CLOCK_PATH | CLOCK_PATH | LAYOUTGEN_FALLBACK_WITH_OPENYIELD_SEMANTICS | StandaloneSRAMGenerator.control_glue_fallback | control_glue | openyield_netlist_translated_sram__phys__control_backbone |
| PRECHARGE_ENABLE_PATH | ENABLE_PATH | LAYOUTGEN_FALLBACK_WITH_OPENYIELD_SEMANTICS | StandaloneSRAMGenerator.control_glue_fallback | control_glue | openyield_netlist_translated_sram__phys__control_backbone |
| SENSE_ENABLE_PATH | ENABLE_PATH | LAYOUTGEN_FALLBACK_WITH_OPENYIELD_SEMANTICS | StandaloneSRAMGenerator.control_glue_fallback | control_glue | openyield_netlist_translated_sram__phys__control_backbone |
| WORDLINE_ENABLE_PATH | ENABLE_PATH | LAYOUTGEN_FALLBACK_WITH_OPENYIELD_SEMANTICS | StandaloneSRAMGenerator.control_glue_fallback | control_glue | openyield_netlist_translated_sram__phys__control_backbone |
| WRITE_ENABLE_PATH | ENABLE_PATH | LAYOUTGEN_FALLBACK_WITH_OPENYIELD_SEMANTICS | StandaloneSRAMGenerator.control_glue_fallback | control_glue | openyield_netlist_translated_sram__phys__control_backbone |
| bitcell_array | ARRAY_CORE | DIRECT_GENERATOR_BINDING | ArrayAggregationPlanner;StandaloneSRAMGenerator | cell_1rw | openyield_netlist_translated_sram__phys__bitcell_array |
| column_mux | COLUMN_MUX | REAL_CELL_WRAPPER | StandaloneSRAMGenerator.columnmux_adapter | gen_col_mux_vdd_labeled | openyield_netlist_translated_sram__phys__column_mux |
| decoder_gate_cells | ROW_DECODER | PARAMETERIZED_LAYOUTGEN_GENERATOR | StandaloneSRAMGenerator.gate_row_packer | row_decoder role instances | openyield_netlist_translated_sram__phys__row_decoder |
| dummy_array | ARRAY_DUMMY | DIRECT_GENERATOR_BINDING | ArrayAggregationPlanner;StandaloneSRAMGenerator | dummy_cell_1rw | openyield_netlist_translated_sram__phys__dummy_array |
| precharge | COLUMN_PRECHARGE | REAL_CELL_WRAPPER | StandaloneSRAMGenerator.precharge_row | gen_precharge | openyield_netlist_translated_sram__phys__precharge |
| replica_array | ARRAY_REPLICA | DIRECT_GENERATOR_BINDING | ArrayAggregationPlanner;StandaloneSRAMGenerator | replica_cell_1rw;replica_precharge | openyield_netlist_translated_sram__phys__replica_array |
| row_decoder | ROW_DECODER | PARAMETERIZED_LAYOUTGEN_GENERATOR | StandaloneSRAMGenerator.gate_row_packer | row_decoder role instances | openyield_netlist_translated_sram__phys__row_decoder |
| sense_amp | SENSE_AMP | REAL_CELL_WRAPPER | StandaloneSRAMGenerator.senseamp_adapter | sense_amp | openyield_netlist_translated_sram__phys__sense_amp |
| wordline_decoder | ROW_DECODER | PARAMETERIZED_LAYOUTGEN_GENERATOR | StandaloneSRAMGenerator.gate_row_packer | row_decoder role instances | openyield_netlist_translated_sram__phys__row_decoder |
| wordline_driver | WORDLINE_DRIVER | REAL_CELL_WRAPPER | StandaloneSRAMGenerator.wordlinedriver_adapter | gen_wl_driver | openyield_netlist_translated_sram__phys__wordline_driver |
| wordline_driver_gate_cells | WORDLINE_DRIVER | PARAMETERIZED_LAYOUTGEN_GENERATOR | StandaloneSRAMGenerator.gate_row_packer+wordlinedriver_adapter | wordline_driver role instances | openyield_netlist_translated_sram__phys__wordline_driver |
| write_driver | WRITE_DRIVER | REAL_CELL_WRAPPER | StandaloneSRAMGenerator.writedriver_adapter | write_driver | openyield_netlist_translated_sram__phys__write_driver |
