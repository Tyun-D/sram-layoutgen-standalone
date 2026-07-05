# OpenYield SRAM LayoutGen Project Status

## 1. Current Correct Goal

继续以用户锁定的 uploaded golden reference 作为唯一物理目标，先修复 layoutgen 复现输出与 golden 的 geometry delta，再等待人工 KLayout review。

## 2. Current Stage

- current_stage: `M8R`
- next_stage: `WAIT_HUMAN_KLAYOUT_REVIEW`
- human_klayout_review_required_every_stage: `True`
- can_enter_next_stage_without_human_review: `False`

## 3. Recorded M8 Failure

- generated_from_layoutgen_source: `True`
- reference_file_copied_as_output: `False`
- reproduced_top_cell_matches_golden: `True`
- cell_count_and_sref_count_match: `True`
- column_mux_and_bitcell_rail_overlap_checks_passed: `True`
- reference_vs_reproduced_geometry_match: `STRUCTURAL_MATCH_WITH_GEOMETRY_DELTA`
- golden_boundary_count: `5418`
- reproduced_boundary_count: `3862`
- missing_boundary_shapes: `1556`
- can_use_this_flow_for_next_netlist_translator: `False`

## 4. Latest M8R Result

- fixed_reproduced_gds_path: `outputs/M8R_fix_golden_geometry_delta/current_supported_config/m8r_reproduced_fixed.gds`
- reference_vs_m8r_geometry_match: `EXACT_MATCH`
- exact_match_achieved: `True`
- can_use_this_flow_for_next_netlist_translator: `True`
- human_klayout_review_required: `True`
