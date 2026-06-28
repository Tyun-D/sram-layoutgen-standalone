# OpenYield Cell Rail Overlap Eligibility Report

- cell_rail_overlap_eligibility_audit_available: `True`
- all_used_cells_classified: `True`
- eligible_cells_count: `5`
- blocked_cells_count: `16`
- dff_excluded_from_vertical_overlap: `True`

## Cells

| cell | class | overlap_eligible | candidate_overlap_depth_um | blocked_reason | policy |
|---|---|---:|---:|---|---|
| ADDR_DFF_ROW | excluded_dff_pending_manual_review | False | 0.0 | dff_vertical_overlap_excluded_by_policy | dff_domain_no_vertical_overlap_policy |
| DELAY_CHAIN | blocked_unknown | False | 0.0 | missing_gds_or_dimensions | fallback_to_edge_touch_or_spacing |
| DELAY_CHAIN_RBL_PATH | blocked_unknown | False | 0.0 | missing_gds_or_dimensions | fallback_to_edge_touch_or_spacing |
| DFF_ROW | excluded_dff_pending_manual_review | False | 0.0 | dff_vertical_overlap_excluded_by_policy | dff_domain_no_vertical_overlap_policy |
| GATED_CLOCK_PATH | blocked_unknown | False | 0.0 | missing_gds_or_dimensions | fallback_to_edge_touch_or_spacing |
| PRECHARGE | blocked_unknown | False | 0.0 | missing_gds_or_dimensions | fallback_to_edge_touch_or_spacing |
| PRECHARGE_ENABLE_PATH | blocked_unknown | False | 0.0 | missing_gds_or_dimensions | fallback_to_edge_touch_or_spacing |
| RBL_DELAY_PATH | blocked_unknown | False | 0.0 | missing_gds_or_dimensions | fallback_to_edge_touch_or_spacing |
| SENSE_ENABLE_PATH | blocked_unknown | False | 0.0 | missing_gds_or_dimensions | fallback_to_edge_touch_or_spacing |
| WORDLINE_ENABLE_PATH | blocked_unknown | False | 0.0 | missing_gds_or_dimensions | fallback_to_edge_touch_or_spacing |
| WRITE_ENABLE_PATH | blocked_unknown | False | 0.0 | missing_gds_or_dimensions | fallback_to_edge_touch_or_spacing |
| bitcell_array | storage_array_already_supported | False | 0.0 |  | storage_domain_existing_shared_rail_policy |
| cell_1rw | storage_array_already_supported | False | 0.0 |  | storage_domain_existing_shared_rail_policy |
| column_mux | blocked_missing_power_rail_geometry | False | 0.0 | missing_candidate_horizontal_rails | fallback_to_edge_touch_or_spacing |
| dff | excluded_dff_pending_manual_review | False | 0.0 | dff_vertical_overlap_excluded_by_policy | dff_domain_no_vertical_overlap_policy |
| dummy_array | storage_array_already_supported | False | 0.0 |  | storage_domain_existing_shared_rail_policy |
| dummy_cell_1rw | storage_array_already_supported | False | 0.0 |  | storage_domain_existing_shared_rail_policy |
| gen_col_mux | blocked_missing_power_rail_geometry | False | 0.0 | missing_candidate_horizontal_rails | fallback_to_edge_touch_or_spacing |
| gen_col_mux_vdd_labeled | blocked_missing_power_rail_geometry | False | 0.0 | missing_candidate_horizontal_rails | fallback_to_edge_touch_or_spacing |
| gen_delay_inv | eligible_standard_gate_rail_overlap | True | 0.0325 |  | same_net_power_rail_overlap_packing |
| gen_inv | eligible_standard_gate_rail_overlap | True | 0.0325 |  | same_net_power_rail_overlap_packing |
| gen_nand2 | eligible_standard_gate_rail_overlap | True | 0.0325 |  | same_net_power_rail_overlap_packing |
| gen_precharge | blocked_missing_power_rail_geometry | False | 0.0 | missing_candidate_horizontal_rails | fallback_to_edge_touch_or_spacing |
| gen_wl_driver | eligible_standard_gate_rail_overlap | True | 0.0325 |  | same_net_power_rail_overlap_packing |
| replica_array | storage_array_already_supported | False | 0.0 |  | storage_domain_existing_shared_rail_policy |
| replica_cell_1rw | storage_array_already_supported | False | 0.0 |  | storage_domain_existing_shared_rail_policy |
| sense_amp | blocked_missing_power_rail_geometry | False | 0.0 | unable_to_assign_distinct_power_rails | fallback_to_edge_touch_or_spacing |
| tri_gate | blocked_missing_power_rail_geometry | False | 0.0 | missing_candidate_horizontal_rails | fallback_to_edge_touch_or_spacing |
| wordline_driver | eligible_standard_gate_rail_overlap | True | 0.0325 |  | same_net_power_rail_overlap_packing |
| write_driver | blocked_missing_power_rail_geometry | False | 0.0 | missing_candidate_horizontal_rails | fallback_to_edge_touch_or_spacing |
