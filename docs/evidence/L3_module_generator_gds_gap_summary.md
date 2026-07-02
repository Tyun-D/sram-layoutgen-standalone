# L3 module generator + GDS gap summary

## Generator coverage

- L3 建立了 module generators: `bitcell_array, dummy_array, replica_array, row_decoder, wordline_decoder, decoder_gate_cells, wordline_driver, wordline_driver_gate_cells, column_mux, sense_amp, write_driver, precharge, DELAY_CHAIN, PRECHARGE_ENABLE_PATH, SENSE_ENABLE_PATH, WRITE_ENABLE_PATH, WORDLINE_ENABLE_PATH, GATED_CLOCK_PATH, DFF_ROW, CONTROL_LOGIC`
- hardmacro wrapper generator 输出的 GDS: `wordline_driver, column_mux, sense_amp, write_driver, precharge`
- array generator 输出的 GDS: `bitcell_array, dummy_array, replica_array`
- gate-row generator 输出的 GDS: `row_decoder, wordline_decoder, decoder_gate_cells, wordline_driver_gate_cells`
- composition-backed candidate generator 输出的 GDS: `DELAY_CHAIN, PRECHARGE_ENABLE_PATH, SENSE_ENABLE_PATH, WRITE_ENABLE_PATH, WORDLINE_ENABLE_PATH, GATED_CLOCK_PATH, DFF_ROW, CONTROL_LOGIC`
- 使用 contract pins 的模块: `bitcell_array, dummy_array, replica_array, row_decoder, wordline_decoder, decoder_gate_cells, wordline_driver_gate_cells, precharge, DELAY_CHAIN, PRECHARGE_ENABLE_PATH, SENSE_ENABLE_PATH, WRITE_ENABLE_PATH, WORDLINE_ENABLE_PATH, GATED_CLOCK_PATH, DFF_ROW, CONTROL_LOGIC`
- 生成失败的模块: `none`
- GDS 可复现: `True`
- can_enter_L4_top_level_assembly: `True`
- remaining_L3_blockers: `[]`
