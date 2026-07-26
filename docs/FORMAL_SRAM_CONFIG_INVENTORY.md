# Formal SRAM Config Inventory

| config_id | word_size | num_words | words_per_row | num_rows | num_cols | addr_width | num_banks | source_authority | support_level | inventory_status | notes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| formal_8x64_wpr4 | 8 | 64 | 4 | 16 | 32 | 6 | 1 | OPENYIELD_RAW_VARIATION | SUPPORTED_WITH_CONSTRAINTS | CURRENT_SOURCE_BACKED | Variation is backed by OpenYield row/column choice space and current project translation rules. |
| formal_4x32_wpr2 | 4 | 32 | 2 | 16 | 8 | 5 | 1 | OPENYIELD_RAW_VARIATION | SUPPORTED_WITH_CONSTRAINTS | CURRENT_SOURCE_BACKED | Variation is backed by OpenYield row/column choice space and current project translation rules. |
| formal_16x16_wpr1 | 16 | 16 | 1 | 16 | 16 | 4 | 1 | OPENYIELD_RAW_VARIATION | SUPPORTED_WITH_CONSTRAINTS | CURRENT_SOURCE_BACKED | Variation is backed by OpenYield row/column choice space and current project translation rules. |
| formal_current_locked_8x64_wpr4 | 8 | 64 | 4 | 16 | 32 | 6 | 1 | M2R_LOCKED_SPEC | SUPPORTED_WITH_CONSTRAINTS | CURRENT_LOCKED_BASELINE | Current physical top-level delivery remains bound to the M2R locked spec. |
| cfg_16x32_wpr2 | 16 | 32 | 2 | 16 | 32 | 5 | 1 | HISTORICAL_GDS_NAME_DERIVED | PARTIALLY_SUPPORTED | HISTORICAL_EVIDENCE_ONLY | Recovered from historical explicit GDS naming/evidence rather than current raw OpenYield authority. |
| cfg_2x16_wpr1 | 2 | 16 | 1 | 16 | 2 | 4 | 1 | HISTORICAL_GDS_NAME_DERIVED | PARTIALLY_SUPPORTED | HISTORICAL_EVIDENCE_ONLY | Recovered from historical explicit GDS naming/evidence rather than current raw OpenYield authority. |
| cfg_32x16_wpr1 | 32 | 16 | 1 | 16 | 32 | 4 | 1 | HISTORICAL_GDS_NAME_DERIVED | PARTIALLY_SUPPORTED | HISTORICAL_EVIDENCE_ONLY | Recovered from historical explicit GDS naming/evidence rather than current raw OpenYield authority. |
| cfg_32x32_wpr1 | 32 | 32 | 1 | 32 | 32 | 5 | 1 | HISTORICAL_GDS_NAME_DERIVED | PARTIALLY_SUPPORTED | HISTORICAL_EVIDENCE_ONLY | Recovered from historical explicit GDS naming/evidence rather than current raw OpenYield authority. |
| cfg_4x32_wpr1 | 4 | 32 | 1 | 32 | 4 | 5 | 1 | HISTORICAL_GDS_NAME_DERIVED | PARTIALLY_SUPPORTED | HISTORICAL_EVIDENCE_ONLY | Recovered from historical explicit GDS naming/evidence rather than current raw OpenYield authority. |
| cfg_64x64_wpr1 | 64 | 64 | 1 | 64 | 64 | 6 | 1 | HISTORICAL_GDS_NAME_DERIVED | PARTIALLY_SUPPORTED | HISTORICAL_EVIDENCE_ONLY | Recovered from historical explicit GDS naming/evidence rather than current raw OpenYield authority. |
