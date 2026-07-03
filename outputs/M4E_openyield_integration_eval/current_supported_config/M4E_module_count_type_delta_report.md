# M4E Module Count / Type Delta Report

- openyield_module_count: `20`
- layoutgen_baseline_module_count: `16`
- module_type_mismatch_count: `12`
- intent_parameter_mismatch: `{'openyield_intent_word_size': 4, 'openyield_intent_num_words': 4, 'openyield_intent_words_per_row': 1, 'optimized_layoutgen_word_size': 8, 'optimized_layoutgen_num_words': 64, 'optimized_layoutgen_words_per_row': 4}`
- summary: `OpenYield exposes 20 semantic modules while baseline layoutgen exposes 16 physical role buckets; the delta is mostly caused by finer-grained OpenYield control and row-path decomposition.`

## Layoutgen Baseline Roles

- `bitcell_array`
- `column_mux`
- `column_select`
- `control_glue`
- `control_logic`
- `data_dff`
- `delay_chain`
- `dummy_bitcell`
- `precharge`
- `replica_bitline`
- `replica_precharge`
- `row_decoder`
- `sense_amp`
- `tri_gate`
- `wordline_driver`
- `write_driver`

## OpenYield Semantic Split Modules

- `row_decoder`
- `wordline_decoder`
- `decoder_gate_cells`
- `wordline_driver_gate_cells`
- `CONTROL_LOGIC`
- `GATED_CLOCK_PATH`
- `PRECHARGE_ENABLE_PATH`
- `SENSE_ENABLE_PATH`
- `WORDLINE_ENABLE_PATH`
- `WRITE_ENABLE_PATH`
- `DFF_ROW`
- `DELAY_CHAIN`
