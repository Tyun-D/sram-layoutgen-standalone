# OpenYield Logical to Parameter Map

| local_parameter | openyield_parameter | mapping_rule | source_evidence | supported_now | unsupported_reason | affects_modules | next_required_action |
| --- | --- | --- | --- | --- | --- | --- | --- |
| num_words | num_rows | num_rows = ceil(num_words / words_per_row) | canonical_contract + OpenYield num_rows source usage | True |  | SRAM_TOP;BANK;row_decoder;bitcell_array;CONTROL_LOGIC | Use this canonical rule for local logical-spec ingestion. |
| word_size | num_cols | physical_num_cols = word_size * words_per_row; OpenYield num_cols = physical_num_cols | canonical_contract + OpenYield num_cols source usage | True |  | SRAM_TOP;bitcell_array;column_mux;sense_amp;write_driver;DFF_ROW | Use physical_num_cols as the OpenYield-facing quantity. |
| words_per_row | choose_columnmux | words_per_row=1 -> choose_columnmux=False and column_mux_ratio=1; words_per_row=2 -> choose_columnmux=True and column_mux_ratio=2; words_per_row>2 unsupported | canonical_contract + sram_6t_core_testbench create_read_periphery hard-coded mux_in=2 | True |  | column_mux;sense_amp;routing_semantics | Do not claim support for words_per_row > 2 until column mux is generalized. |
| num_rows | num_rows | identity | global.yaml + decoder/time_generate source | True |  | bitcell_array;row_decoder;wordline_driver;CONTROL_LOGIC;replica_array | Freeze as canonical identity mapping. |
| physical_num_cols | num_cols | identity | global.yaml + time_generate source | True |  | bitcell_array;column_mux;sense_amp;write_driver;DFF_ROW | Freeze as canonical identity mapping. |
| column_mux_ratio | choose_columnmux | column_mux_ratio=1 -> False; column_mux_ratio=2 -> True | sram_6t_core_testbench create_read_periphery | True |  | column_mux;sense_amp;timing_semantics | Treat ratio as derived from words_per_row. |
| addr_size | derived_from_num_rows | addr_size = row_addr_size = ceil(log2(num_rows)) in current OpenYield source | decoder.py + time_generate.py | True |  | SRAM_TOP;row_decoder;DFF_ROW;CONTROL_LOGIC | Column address remains outside current explicit source scope. |
| num_banks | implicit_single_bank | num_banks is frozen to 1 by scope contract | top_bank_contract | True | multi_bank_unsupported | SRAM_TOP;BANK | Do not expose banked topology in L1. |
| num_ports | implicit_single_readwrite_port | num_ports is frozen to 1 by scope contract | top_bank_contract + TIME control semantics | True | multi_port_unsupported | SRAM_TOP;CONTROL_LOGIC | Keep one shared read/write port semantic. |
| write_mask | unsupported | write_mask/write_size/wmask are unsupported in current scope | canonical_contract + source absence | True | write_mask_unsupported | write_driver;CONTROL_LOGIC | Explicitly out of scope; no longer an L0 blocker. |
