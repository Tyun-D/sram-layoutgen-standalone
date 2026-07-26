# M11 Remaining Gap Report

- M11_GAP_001: Human KLayout review is required for openyield_config_derived_sram_clean_review.gds before any post-M11 stage.
- M11_GAP_002: Fallback still required for: word_size, num_words, words_per_row, num_banks, num_ports, tech, top_cell_name, dummy_enabled, replica_enabled, precharge_enabled, sense_amp_enabled, write_driver_enabled, wordline_driver_enabled, decoder_enabled
- M11_GAP_003: OpenYield raw source exposes num_rows/num_cols/choose_columnmux and architecture variations, but current supported delivery still relies on locked 8x64_wpr4 logical capacity fallback.
