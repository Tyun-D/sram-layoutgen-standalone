# OPENYIELD_SRAM_SPEC_V1

- scope: `layout-facing clean SRAM top extracted from the OpenYield testbench-backed generator`
- supported_now: `num_rows, num_cols, num_words=num_rows, word_size=num_cols, choose_columnmux=false, words_per_row=1, mux_ratio=1, sram_cell_type=6T, corner, temperature, control_timing_parameters`
- unsupported_now: `words_per_row > 1, arbitrary column mux ratio, arbitrary PDK physical generation, custom-netlist-driven final GDS`
- authority_boundary: `V1 is proven only for choose_columnmux=false and the generated 16x16 / 64x8 clean-top samples.`
