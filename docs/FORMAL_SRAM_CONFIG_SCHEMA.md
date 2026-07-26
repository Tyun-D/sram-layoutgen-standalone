# Formal SRAM Config Schema

- schema_name: `FORMAL_SRAM_CONFIG_SCHEMA`
- schema_version: `2026-07-26`
- validation_rules: `num_rows * words_per_row == num_words; num_cols / words_per_row == word_size; addr_width = log2(num_words) when num_words is a power of two; num_banks stays 1 unless a canonical multi-bank source contract exists`
- degrade_policy: `Rows without raw-source-backed authority stay in the inventory but must use HISTORICAL_EVIDENCE_ONLY or REFERENCE_ONLY inventory_status.`
