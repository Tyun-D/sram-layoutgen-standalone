# M12O Configurable SRAM Spec Plan

- reused_previous_artifacts: `M11V isolated substitution verification, M11D sense_amp real-substitution proof, M11W wordline_driver wrapper repair, M12 ten-asset audit baseline`
- deprecated_previous_artifacts: `direct M11V2 continuation as the immediate next step`
- current_stage_inputs: `OpenRAM full reference scan, layoutgen golden GDS, OpenYield module GDS and code/config roots`
- current_stage_delta_from_M11V: `M12O shifts from isolated routing/power verification to reference-authority alignment and parameterized planning.`
- why_M12O_replaces_direct_M11V2_for_now: `Netlist authority and control-logic alignment are larger blockers than deeper connectivity alone.`
- required_parameters: `['word_size', 'num_words', 'words_per_row', 'tech', 'num_rows', 'num_cols']`
- optional_parameters: `['choose_columnmux', 'write_size', 'num_banks', 'corner', 'temperature', 'sram_cell_type']`
- unsupported_parameters: `['full control_logic decomposition selection', 'verified top-level netlist connectivity', 'routing/power closure constraints']`
- sample_A_layoutgen_current: `8x64_wpr4_fd45 -> num_rows=16, num_cols=32`
- sample_B_openram_reference: `{'word_size': 16, 'num_words': 32, 'words_per_row': 'UNKNOWN', 'num_rows': 'UNKNOWN', 'num_cols': 'UNKNOWN', 'tech': 'freepdk45'}`
