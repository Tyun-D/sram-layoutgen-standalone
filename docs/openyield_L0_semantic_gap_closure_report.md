# OpenYield L0 Semantic Gap Closure Report

This report closes L0 semantic gaps by explicit local contracts. It does not claim physical closure, full OpenYield GDS, DRC, LVS, or timing closure.

## Scope

- can_claim_L0_semantics_closed_now: `True`
- can_enter_L1_physical_primitive_closure: `True`
- can_enter_L2_placement_rule_closure: `False`
- can_enter_L3_module_gds_generation: `False`
- can_claim_full_openyield_gds_now: `False`
- remaining_L0_blockers_count: `0`

## Supported Scope

- single_bank: `True`
- single_implicit_readwrite_port: `True`
- num_ports_supported: `1`
- write_mask_supported: `False`
- column_mux_ratio_supported_values: `[1, 2]`
- choose_columnmux_supported_values: `[False, True]`

## Unsupported Features

- `multi_bank`
- `multi_port`
- `write_mask`
- `write_size`
- `words_per_row_gt_2`
- `column_mux_ratio_gt_2`

## Closure Summary

- Logical-spec parameters are now closed by canonical mapping contract rather than direct OpenYield first-class parameters.
- SRAM_TOP and BANK are closed by explicit local single-bank semantic contracts.
- TIME is closed by stable semantic decomposition boundaries rather than a required physical implementation.
- Enable paths and decoder-wordline handoff are closed as semantic contracts; their physical realization is postponed to L1/L2/L3.

## Gates

| L0_semantic_gap_closure_available | canonical_sram_semantic_contract_available | logical_to_openyield_parameter_map_available | top_bank_semantic_contract_available | time_control_decomposition_contract_available | decoder_wordline_semantic_contract_available | control_path_semantic_contracts_available | module_rows_count | remaining_L0_blockers | remaining_L0_blockers_count | semantics_closed_modules | source_found_ports_known_modules | source_found_ports_partial_modules | source_found_connections_unresolved_modules | local_mapping_unresolved_modules | parameter_rule_unresolved_modules | all_required_modules_have_source_or_contract | all_required_modules_have_ports_or_contract | all_required_modules_have_parameter_rules_or_explicit_scope_limit | all_required_modules_have_connection_mapping_or_contract | all_required_modules_have_local_layoutgen_mapping_or_contract | unsupported_features_explicitly_scoped | unsupported_features | can_claim_L0_semantics_closed_now | can_enter_L1_physical_primitive_closure | can_enter_L2_placement_rule_closure | can_enter_L3_module_gds_generation | can_claim_full_openyield_gds_now | can_claim_drc_clean_now | can_claim_lvs_clean_now | can_claim_timing_closure_now |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| True | True | True | True | True | True | True | 25 | [] | 0 | ['BANK', 'CONTROL_LOGIC', 'DELAY_CHAIN', 'DFF_ROW', 'GATED_CLOCK_PATH', 'PRECHARGE_ENABLE_PATH', 'SENSE_ENABLE_PATH', 'SRAM_TOP', 'WORDLINE_ENABLE_PATH', 'WRITE_ENABLE_PATH', 'bitcell_array', 'column_mux', 'decoder_gate_cells', 'dummy_array', 'power_semantics', 'precharge', 'replica_array', 'routing_semantics', 'row_decoder', 'sense_amp', 'timing_semantics', 'wordline_decoder', 'wordline_driver', 'wordline_driver_gate_cells', 'write_driver'] | [] | [] | [] | [] | [] | True | True | True | True | True | True | ['multi_bank', 'multi_port', 'write_mask', 'write_size', 'words_per_row_gt_2', 'column_mux_ratio_gt_2'] | True | True | False | False | False | False | False | False |
