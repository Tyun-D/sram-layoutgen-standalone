# M12N Parameter Interface Matrix

- num_rows: `SUPPORTED` | Directly loaded by SRAM_CONFIG and used by testbench/core factories.
- num_cols: `SUPPORTED` | Directly loaded by SRAM_CONFIG and used by testbench/core factories.
- choose_columnmux: `SUPPORTED` | Directly gates column mux behavior in testbench flow.
- corner: `SUPPORTED` | Directly selects PDK model include path.
- temperature: `SUPPORTED` | Runtime simulation parameter, not a direct layout parameter.
- sram_cell_type: `SUPPORTED` | Selects 6T vs 10T cell/core/testbench path.
- word_size: `PARTIAL` | Current flow exposes num_cols instead of a locked word_size contract.
- num_words: `PARTIAL` | Current flow exposes num_rows rather than a raw-source num_words contract.
- words_per_row: `UNKNOWN` | Column-mux behavior exists, but a raw authoritative words_per_row contract is not locked.
- mux_ratio: `PARTIAL` | Presence of column mux is configurable, but ratio is not locked as a top-level scalar.
- tech: `PARTIAL` | Technology is indirectly represented by transistor model paths.
- control_timing_parameters: `SUPPORTED` | Supported for simulation/testbench timing, not yet a pure layout control-path contract.
