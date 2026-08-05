# Bitcell Array Authority Golden Lock

The authoritative input is `outputs/PROJECT_bitcell_array_layoutgen_reuse_v2/clean.gds`, top cell `sram_capped_replica_bitcell_array`, SHA-256 `555df9b1fcbd9dda7e4c8959942e27b8f093c36b0a8c67a7ac213f9946b9a1ac`.

The formal configuration is 16 rows by 16 columns, `word_size=16`, `words_per_row=1`, one bank, using `cell_1rw`. Source generator, leaf hard macros, layer mapping, reuse contract, Pin map, machine gate, determinism report, and DRC database are locked by SHA in the JSON companion.

Integration may instantiate this cell only as an immutable R0 parent reference. Internal geometry, instance order, dummy/tap/replica policy, and WL/BL/BR ordering must not change. Any future non-R0 parent transform requires a new power, Pin, DRC, hierarchy, and connectivity qualification.
