# SRAM SPEC TEMPLATE

- reused_previous_artifacts: `M11 config variation evidence, layoutgen 8x64_wpr4 baseline, OpenRAM external full reference name-derived spec`
- deprecated_previous_artifacts: `none; this is a planning template`
- current_stage_inputs: `OpenYield global.yaml, main_sram.py, OpenRAM reference GDS name, layoutgen current sample`
- current_stage_delta_from_M11V: `turns isolated smoke evidence into configurable-SRAM planning requirements`
- why_M12O_replaces_direct_M11V2_for_now: `parameterized generation cannot proceed safely without a locked OpenYield top-level authority`
- required_parameters: `['word_size', 'num_words', 'words_per_row', 'tech', 'num_rows', 'num_cols']`
- optional_parameters: `['choose_columnmux', 'write_size', 'num_banks', 'corner', 'temperature', 'sram_cell_type']`
- derived_parameters: `{'num_rows': 'num_words / words_per_row', 'num_cols': 'word_size * words_per_row'}`
- unsupported_parameters: `['full control_logic decomposition selection', 'verified top-level netlist connectivity', 'routing/power closure constraints']`
- sample_A_layoutgen_current num_rows/num_cols source: `derived from word_size=8, num_words=64, words_per_row=4 -> rows=16, cols=32`
- sample_B_openram_reference words_per_row source: `UNKNOWN because only the external OpenRAM GDS name is available in the chosen full-reference directory.`
