# SRAM Configuration Audit

- historical claim `30` configurations is **not revalidated** by current explicit mainline evidence.
- explicit evidence-backed configurations in this audit: `5`

| config_id | word_count | word_size | rows | columns | banks | mux_ratio | GDS_available | DRC_status | connectivity_status | formal_or_demo |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| cfg_m2r_8x64_wpr4 | 64 | 8 | 16 | 32 | 1 | 4 | True | PASS_INTERNAL_DRC | ROUTE_AUDIT_PASS_NO_EXTERNAL_LVS | experimental |
| cfg_m2_8x64_wpr4 | 64 | 8 | 16 | 32 | 1 | 4 | True | TRIAL_NOT_SIGNOFFED | TRIAL_STRUCTURAL_ONLY | experimental |
| cfg_m11_8x64_wpr4 | 64 | 8 | 16 | 32 | 1 | 4 | True | GEOMETRY_MATCH_GENERATION_FAILED | NOT_AUDITED_FOR_SIGNOFF | experimental |
| cfg_m11_4x32_wpr2 | 32 | 4 | 16 | 8 | 1 | 2 | False | NOT_GENERATED | NOT_GENERATED | experimental |
| cfg_m11_16x16_wpr1 | 16 | 16 | 16 | 16 | 1 | 1 | True | GENERATED_VARIATION_ONLY | NOT_AUDITED_FOR_SIGNOFF | experimental |
