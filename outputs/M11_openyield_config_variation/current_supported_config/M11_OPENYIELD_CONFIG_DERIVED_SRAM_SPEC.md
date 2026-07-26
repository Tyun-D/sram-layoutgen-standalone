# M11 OpenYield Config Derived SRAM Spec

- current_supported_config delivery: `8x64_wpr4`
- raw OpenYield derived candidate: `16x16_wpr1`
- raw num_rows/num_cols: `16 / 16`
- capacity_config_fallback_used_after_M11: `True`
- fallback_reason: `Raw OpenYield provides architecture knobs (num_rows/num_cols/choose_columnmux) but not enough first-class logical capacity fields to eliminate the locked 8x64_wpr4 fallback for current_supported_config delivery.`
