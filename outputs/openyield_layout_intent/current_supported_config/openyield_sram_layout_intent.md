# OpenYield SRAM Layout Intent

## Goal

Define a self-developed OpenYield SRAM layout intent that future R2/R3 generator stages can consume.

## Canonical Parameters

- `word_size` = `4`
source: `DEFAULT_FOR_CURRENT_SUPPORTED_SCOPE`
evidence: `docs/mapping/openyield_canonical_sram_semantic_contract.json;docs/mapping/openyield_module_gds_inventory.csv`
- `num_words` = `4`
source: `DEFAULT_FOR_CURRENT_SUPPORTED_SCOPE`
evidence: `docs/mapping/openyield_canonical_sram_semantic_contract.json`
- `words_per_row` = `1`
source: `DEFAULT_FOR_CURRENT_SUPPORTED_SCOPE`
evidence: `docs/mapping/openyield_canonical_sram_semantic_contract.json;docs/mapping/openyield_logical_to_openyield_parameter_map.csv`
- `num_rows` = `4`
source: `DERIVED_FROM_CONTRACT`
evidence: `docs/mapping/openyield_logical_to_openyield_parameter_map.csv`
- `num_cols` = `4`
source: `DERIVED_FROM_CONTRACT`
evidence: `docs/mapping/openyield_logical_to_openyield_parameter_map.csv`
- `column_mux_ratio` = `1`
source: `DERIVED_FROM_CONTRACT`
evidence: `docs/mapping/openyield_logical_to_openyield_parameter_map.csv`
- `num_banks` = `1`
source: `DERIVED_FROM_CONTRACT`
evidence: `docs/mapping/openyield_canonical_sram_semantic_contract.json;docs/mapping/openyield_top_bank_semantic_contract.json`
- `num_ports` = `1`
source: `DERIVED_FROM_CONTRACT`
evidence: `docs/mapping/openyield_canonical_sram_semantic_contract.json`
- `port_type` = `single_implicit_readwrite`
source: `DERIVED_FROM_CONTRACT`
evidence: `docs/mapping/openyield_canonical_sram_semantic_contract.json;docs/mapping/openyield_top_bank_semantic_contract.json`
- `write_mask_supported` = `False`
source: `DERIVED_FROM_CONTRACT`
evidence: `docs/mapping/openyield_canonical_sram_semantic_contract.json`
- `address_width` = `2`
source: `DERIVED_FROM_CONTRACT`
evidence: `docs/mapping/openyield_logical_to_openyield_parameter_map.csv`
- `row_address_width` = `2`
source: `DERIVED_FROM_CONTRACT`
evidence: `docs/mapping/openyield_logical_to_openyield_parameter_map.csv`
- `column_address_width` = `0`
source: `DERIVED_FROM_CONTRACT`
evidence: `docs/mapping/openyield_logical_to_openyield_parameter_map.csv`
- `data_width` = `4`
source: `DERIVED_FROM_CONTRACT`
evidence: `docs/mapping/openyield_canonical_sram_semantic_contract.json`
- `supported_scope` = `{'single_bank': True, 'single_implicit_readwrite_port': True, 'num_ports_supported': 1, 'write_mask_supported': False, 'words_per_row_supported_values': [1, 2], 'column_mux_ratio_supported_values': [1, 2], 'multi_bank_supported': False, 'multi_port_supported': False}`
source: `DERIVED_FROM_CONTRACT`
evidence: `docs/mapping/openyield_canonical_sram_semantic_contract.json;docs/openyield_layout_generator_architecture_proposal.json`

## Boundary

This intent defines structure, roles, alignment expectations, power and pin contracts. It does not claim a structure-complete SRAM GDS, DRC clean, LVS clean, timing closure, or signoff readiness.

## Source Artifacts

- `docs/openram_gds_generation_audit_report.json`
- `docs/mapping/openram_to_openyield_layoutgen_reuse_matrix.csv`
- `docs/mapping/openyield_canonical_sram_semantic_contract.json`
- `docs/mapping/openyield_module_connection_matrix.csv`
- `docs/mapping/openyield_decoder_wordline_semantic_contract.json`
- `docs/mapping/openyield_time_control_decomposition_contract.json`
- `docs/mapping/openyield_control_path_semantic_contracts.csv`
- `docs/mapping/openyield_module_gds_inventory.csv`
