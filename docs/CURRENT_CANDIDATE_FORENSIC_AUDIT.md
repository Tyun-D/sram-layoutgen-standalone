# Current Candidate Forensic Audit

- generated_at: `2026-08-03T17:29:44Z`
- candidate_id: `candidate_true_wl_driver_array_oriented`
- opened_artifact_kind: `Level_A_final_clean_gds`
- classification: `INTERFACE_ROUTING_HARNESS_MACHINE_PASS, FINAL_SRAM_PHYSICAL_ARCHITECTURE_NOT_APPROVED, POWER_VISUAL_AND_GEOMETRY_WITNESS_REVIEW_PENDING, WL_TIMING_BALANCE_NOT_PROVEN, PLACEMENT_SEARCH_NOT_EXHAUSTED, ARRAY_INTEGRATION_LEVEL=FLOORPLAN_FEASIBILITY_SHELL, FULL_BITCELL_ARRAY_GDS_INTEGRATION=PENDING`
- array_object_type: `approved_nonzero_physical_shell`
- full_bitcell_array_gds_included: `false`
- driver_layout_pattern: `16x1`
- driver_is_single_horizontal_row: `True`
- missing_vdd_endpoint_count: `0`
- missing_vss_endpoint_count: `0`
- power_endpoint_coverage_passed: `False`
- current_candidate_power_status: `CURRENT_CANDIDATE_POWER_FAILED`

## Findings

- The current integrated artifact is a machine-passing interface routing harness, not an approved final SRAM physical architecture.
- The array object is `approved_nonzero_physical_shell`, so the integration level is capped at `FLOORPLAN_FEASIBILITY_SHELL`.
- All 16 WL drivers are placed in one horizontal row, which violates the preferred row-aligned vertical-driver architecture.
- WL routes use unequal lengths, bend counts, and via counts; `WL_GEOMETRY_RC.csv` is the controlling Level B evidence for that imbalance.
- Power witness results are derived from the final clean GDS conductive graph and recorded in `POWER_ENDPOINT_COVERAGE.csv` and `POWER_WITNESS_ATLAS.gds`.
