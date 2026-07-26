# M8 SRAM SPEC

- word_size: `8`
- num_words: `64`
- words_per_row: `4`
- num_rows: `16`
- num_cols: `32`
- tech: `freepdk45`
- generator_entry_script: `sram_layoutgen/standalone.py`
- generator_function: `write_standalone`
- generator_arguments: `{"word_size": 8, "num_words": 64, "words_per_row": 4, "name": "sram_8x64_wpr4_fd45", "enable_openyield_gate_row_packing": true, "enable_openyield_power_rail_overlap_packing": true}`
