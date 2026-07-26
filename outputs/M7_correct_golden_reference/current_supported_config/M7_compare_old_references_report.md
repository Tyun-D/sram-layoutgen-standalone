# M7 Compare Old References Report

- hybrid_openyield_rail_overlap_is_golden: `False`
- new_uploaded_reference_is_golden: `True`

## new_golden_reference vs historical_hybrid_openyield_complete

| metric | new_golden_reference | historical_hybrid_openyield_complete | match |
| --- | --- | --- | --- |
| file_size_bytes | 389826 | 286992 | False |
| top_cell | sram_8x64_wpr4_fd45 | hybrid_openyield_rail_overlap | False |
| cell_count | 33 | 30 | False |
| sref_count | 788 | 746 | False |
| boundary_count | 5418 | 3854 | False |
| path_count | 0 | 0 | True |
| bbox | {'x0': -0.1, 'y0': -0.105, 'x1': 36.6225, 'y1': 44.145, 'width': 36.722500000000004, 'height': 44.25, 'shape_count': 5418} | {'x0': -0.1, 'y0': -0.105, 'x1': 42.7725, 'y1': 47.345, 'width': 42.8725, 'height': 47.449999999999996, 'shape_count': 3854} | False |
| layer_datatype_summary | {'1/0': 358, '10/0': 284, '11/0': 1083, '12/0': 389, '13/0': 1446, '13/2': 11, '14/0': 356, '15/0': 552, '15/2': 14, '16/0': 176, '17/0': 73, '17/2': 2, '2/0': 57, '239/0': 38, '3/0': 45, '4/0': 67, '5/0': 58, '6/0': 64, '9/0': 345} | {'1/0': 356, '10/0': 283, '11/0': 802, '12/0': 229, '13/0': 991, '13/2': 11, '14/0': 156, '15/0': 329, '15/2': 14, '17/0': 20, '17/2': 2, '2/0': 54, '239/0': 35, '3/0': 45, '4/0': 66, '5/0': 57, '6/0': 63, '9/0': 341} | False |
| per_layer_shape_count | {'1/0': 358, '10/0': 284, '11/0': 1083, '12/0': 389, '13/0': 1446, '13/2': 11, '14/0': 356, '15/0': 552, '15/2': 14, '16/0': 176, '17/0': 73, '17/2': 2, '2/0': 57, '239/0': 38, '3/0': 45, '4/0': 67, '5/0': 58, '6/0': 64, '9/0': 345} | {'1/0': 356, '10/0': 283, '11/0': 802, '12/0': 229, '13/0': 991, '13/2': 11, '14/0': 156, '15/0': 329, '15/2': 14, '17/0': 20, '17/2': 2, '2/0': 54, '239/0': 35, '3/0': 45, '4/0': 66, '5/0': 57, '6/0': 63, '9/0': 341} | False |
| gen_col_mux_hierarchy_presence | {'exact_instance_count': 32, 'wrapper_instance_count': 32, 'wrapper_cell_names': ['gen_col_mux'], 'present_in_top_hierarchy': True} | {'exact_instance_count': 0, 'wrapper_instance_count': 0, 'wrapper_cell_names': [], 'present_in_top_hierarchy': False} | False |
| tri_gate_hierarchy_presence | {'exact_instance_count': 8, 'wrapper_instance_count': 8, 'wrapper_cell_names': ['tri_gate'], 'present_in_top_hierarchy': True} | {'exact_instance_count': 8, 'wrapper_instance_count': 8, 'wrapper_cell_names': ['tri_gate'], 'present_in_top_hierarchy': True} | True |
| visible_structure_summary | {'bitcell_array_present': True, 'dummy_present': True, 'replica_present': True, 'precharge_present': True, 'mux_present': True, 'sense_amp_present': True, 'write_driver_present': True, 'wl_driver_present': True} | {'bitcell_array_present': True, 'dummy_present': True, 'replica_present': True, 'precharge_present': True, 'mux_present': True, 'sense_amp_present': True, 'write_driver_present': True, 'wl_driver_present': True} | True |
| power_summary.power_rail_overlap_positive_count | None | 33 | False |
| power_summary.same_net_power_overlap_pass | None | True | False |
| power_summary.bitcell_rail_continuity_visible | UNKNOWN | True | False |
| power_summary.rail_stitch_visible | UNKNOWN | True | False |
| cell_hierarchy | DIFF | DIFF | False |


## new_golden_reference vs M6R_reproduced

| metric | new_golden_reference | M6R_reproduced | match |
| --- | --- | --- | --- |
| file_size_bytes | 389826 | 286992 | False |
| top_cell | sram_8x64_wpr4_fd45 | hybrid_openyield_rail_overlap | False |
| cell_count | 33 | 30 | False |
| sref_count | 788 | 746 | False |
| boundary_count | 5418 | 3854 | False |
| path_count | 0 | 0 | True |
| bbox | {'x0': -0.1, 'y0': -0.105, 'x1': 36.6225, 'y1': 44.145, 'width': 36.722500000000004, 'height': 44.25, 'shape_count': 5418} | {'x0': -0.1, 'y0': -0.105, 'x1': 42.7725, 'y1': 47.345, 'width': 42.8725, 'height': 47.449999999999996, 'shape_count': 3854} | False |
| layer_datatype_summary | {'1/0': 358, '10/0': 284, '11/0': 1083, '12/0': 389, '13/0': 1446, '13/2': 11, '14/0': 356, '15/0': 552, '15/2': 14, '16/0': 176, '17/0': 73, '17/2': 2, '2/0': 57, '239/0': 38, '3/0': 45, '4/0': 67, '5/0': 58, '6/0': 64, '9/0': 345} | {'1/0': 356, '10/0': 283, '11/0': 802, '12/0': 229, '13/0': 991, '13/2': 11, '14/0': 156, '15/0': 329, '15/2': 14, '17/0': 20, '17/2': 2, '2/0': 54, '239/0': 35, '3/0': 45, '4/0': 66, '5/0': 57, '6/0': 63, '9/0': 341} | False |
| per_layer_shape_count | {'1/0': 358, '10/0': 284, '11/0': 1083, '12/0': 389, '13/0': 1446, '13/2': 11, '14/0': 356, '15/0': 552, '15/2': 14, '16/0': 176, '17/0': 73, '17/2': 2, '2/0': 57, '239/0': 38, '3/0': 45, '4/0': 67, '5/0': 58, '6/0': 64, '9/0': 345} | {'1/0': 356, '10/0': 283, '11/0': 802, '12/0': 229, '13/0': 991, '13/2': 11, '14/0': 156, '15/0': 329, '15/2': 14, '17/0': 20, '17/2': 2, '2/0': 54, '239/0': 35, '3/0': 45, '4/0': 66, '5/0': 57, '6/0': 63, '9/0': 341} | False |
| gen_col_mux_hierarchy_presence | {'exact_instance_count': 32, 'wrapper_instance_count': 32, 'wrapper_cell_names': ['gen_col_mux'], 'present_in_top_hierarchy': True} | {'exact_instance_count': 0, 'wrapper_instance_count': 0, 'wrapper_cell_names': [], 'present_in_top_hierarchy': False} | False |
| tri_gate_hierarchy_presence | {'exact_instance_count': 8, 'wrapper_instance_count': 8, 'wrapper_cell_names': ['tri_gate'], 'present_in_top_hierarchy': True} | {'exact_instance_count': 8, 'wrapper_instance_count': 8, 'wrapper_cell_names': ['tri_gate'], 'present_in_top_hierarchy': True} | True |
| visible_structure_summary | {'bitcell_array_present': True, 'dummy_present': True, 'replica_present': True, 'precharge_present': True, 'mux_present': True, 'sense_amp_present': True, 'write_driver_present': True, 'wl_driver_present': True} | {'bitcell_array_present': True, 'dummy_present': True, 'replica_present': True, 'precharge_present': True, 'mux_present': True, 'sense_amp_present': True, 'write_driver_present': True, 'wl_driver_present': True} | True |
| power_summary.power_rail_overlap_positive_count | None | None | True |
| power_summary.same_net_power_overlap_pass | None | None | True |
| power_summary.bitcell_rail_continuity_visible | UNKNOWN | UNKNOWN | True |
| power_summary.rail_stitch_visible | UNKNOWN | UNKNOWN | True |
| cell_hierarchy | DIFF | DIFF | False |


## new_golden_reference vs M6_primary_output

| metric | new_golden_reference | M6_primary_output | match |
| --- | --- | --- | --- |
| file_size_bytes | 389826 | 223894 | False |
| top_cell | sram_8x64_wpr4_fd45 | layoutgen_optimized_reproduced_sram | False |
| cell_count | 33 | 30 | False |
| sref_count | 788 | 746 | False |
| boundary_count | 5418 | 2868 | False |
| path_count | 0 | 0 | True |
| bbox | {'x0': -0.1, 'y0': -0.105, 'x1': 36.6225, 'y1': 44.145, 'width': 36.722500000000004, 'height': 44.25, 'shape_count': 5418} | {'x0': -0.1, 'y0': -0.105, 'x1': 42.7725, 'y1': 47.345, 'width': 42.8725, 'height': 47.449999999999996, 'shape_count': 2868} | False |
| layer_datatype_summary | {'1/0': 358, '10/0': 284, '11/0': 1083, '12/0': 389, '13/0': 1446, '13/2': 11, '14/0': 356, '15/0': 552, '15/2': 14, '16/0': 176, '17/0': 73, '17/2': 2, '2/0': 57, '239/0': 38, '3/0': 45, '4/0': 67, '5/0': 58, '6/0': 64, '9/0': 345} | {'1/0': 356, '10/0': 283, '11/0': 736, '12/0': 195, '13/0': 483, '13/2': 11, '14/0': 32, '15/0': 88, '15/2': 14, '17/0': 7, '17/2': 2, '2/0': 54, '239/0': 35, '3/0': 45, '4/0': 66, '5/0': 57, '6/0': 63, '9/0': 341} | False |
| per_layer_shape_count | {'1/0': 358, '10/0': 284, '11/0': 1083, '12/0': 389, '13/0': 1446, '13/2': 11, '14/0': 356, '15/0': 552, '15/2': 14, '16/0': 176, '17/0': 73, '17/2': 2, '2/0': 57, '239/0': 38, '3/0': 45, '4/0': 67, '5/0': 58, '6/0': 64, '9/0': 345} | {'1/0': 356, '10/0': 283, '11/0': 736, '12/0': 195, '13/0': 483, '13/2': 11, '14/0': 32, '15/0': 88, '15/2': 14, '17/0': 7, '17/2': 2, '2/0': 54, '239/0': 35, '3/0': 45, '4/0': 66, '5/0': 57, '6/0': 63, '9/0': 341} | False |
| gen_col_mux_hierarchy_presence | {'exact_instance_count': 32, 'wrapper_instance_count': 32, 'wrapper_cell_names': ['gen_col_mux'], 'present_in_top_hierarchy': True} | {'exact_instance_count': 0, 'wrapper_instance_count': 0, 'wrapper_cell_names': [], 'present_in_top_hierarchy': False} | False |
| tri_gate_hierarchy_presence | {'exact_instance_count': 8, 'wrapper_instance_count': 8, 'wrapper_cell_names': ['tri_gate'], 'present_in_top_hierarchy': True} | {'exact_instance_count': 8, 'wrapper_instance_count': 8, 'wrapper_cell_names': ['tri_gate'], 'present_in_top_hierarchy': True} | True |
| visible_structure_summary | {'bitcell_array_present': True, 'dummy_present': True, 'replica_present': True, 'precharge_present': True, 'mux_present': True, 'sense_amp_present': True, 'write_driver_present': True, 'wl_driver_present': True} | {'bitcell_array_present': True, 'dummy_present': True, 'replica_present': True, 'precharge_present': True, 'mux_present': True, 'sense_amp_present': True, 'write_driver_present': True, 'wl_driver_present': True} | True |
| power_summary.power_rail_overlap_positive_count | None | 33 | False |
| power_summary.same_net_power_overlap_pass | None | True | False |
| power_summary.bitcell_rail_continuity_visible | UNKNOWN | True | False |
| power_summary.rail_stitch_visible | UNKNOWN | True | False |
| cell_hierarchy | DIFF | DIFF | False |


## new_golden_reference vs M3F_complete

| metric | new_golden_reference | M3F_complete | match |
| --- | --- | --- | --- |
| file_size_bytes | 389826 | 286996 | False |
| top_cell | sram_8x64_wpr4_fd45 | openyield_optimized_layoutgen_sram | False |
| cell_count | 33 | 30 | False |
| sref_count | 788 | 746 | False |
| boundary_count | 5418 | 3854 | False |
| path_count | 0 | 0 | True |
| bbox | {'x0': -0.1, 'y0': -0.105, 'x1': 36.6225, 'y1': 44.145, 'width': 36.722500000000004, 'height': 44.25, 'shape_count': 5418} | {'x0': -0.1, 'y0': -0.105, 'x1': 42.7725, 'y1': 47.345, 'width': 42.8725, 'height': 47.449999999999996, 'shape_count': 3854} | False |
| layer_datatype_summary | {'1/0': 358, '10/0': 284, '11/0': 1083, '12/0': 389, '13/0': 1446, '13/2': 11, '14/0': 356, '15/0': 552, '15/2': 14, '16/0': 176, '17/0': 73, '17/2': 2, '2/0': 57, '239/0': 38, '3/0': 45, '4/0': 67, '5/0': 58, '6/0': 64, '9/0': 345} | {'1/0': 356, '10/0': 283, '11/0': 802, '12/0': 229, '13/0': 991, '13/2': 11, '14/0': 156, '15/0': 329, '15/2': 14, '17/0': 20, '17/2': 2, '2/0': 54, '239/0': 35, '3/0': 45, '4/0': 66, '5/0': 57, '6/0': 63, '9/0': 341} | False |
| per_layer_shape_count | {'1/0': 358, '10/0': 284, '11/0': 1083, '12/0': 389, '13/0': 1446, '13/2': 11, '14/0': 356, '15/0': 552, '15/2': 14, '16/0': 176, '17/0': 73, '17/2': 2, '2/0': 57, '239/0': 38, '3/0': 45, '4/0': 67, '5/0': 58, '6/0': 64, '9/0': 345} | {'1/0': 356, '10/0': 283, '11/0': 802, '12/0': 229, '13/0': 991, '13/2': 11, '14/0': 156, '15/0': 329, '15/2': 14, '17/0': 20, '17/2': 2, '2/0': 54, '239/0': 35, '3/0': 45, '4/0': 66, '5/0': 57, '6/0': 63, '9/0': 341} | False |
| gen_col_mux_hierarchy_presence | {'exact_instance_count': 32, 'wrapper_instance_count': 32, 'wrapper_cell_names': ['gen_col_mux'], 'present_in_top_hierarchy': True} | {'exact_instance_count': 0, 'wrapper_instance_count': 0, 'wrapper_cell_names': [], 'present_in_top_hierarchy': False} | False |
| tri_gate_hierarchy_presence | {'exact_instance_count': 8, 'wrapper_instance_count': 8, 'wrapper_cell_names': ['tri_gate'], 'present_in_top_hierarchy': True} | {'exact_instance_count': 8, 'wrapper_instance_count': 8, 'wrapper_cell_names': ['tri_gate'], 'present_in_top_hierarchy': True} | True |
| visible_structure_summary | {'bitcell_array_present': True, 'dummy_present': True, 'replica_present': True, 'precharge_present': True, 'mux_present': True, 'sense_amp_present': True, 'write_driver_present': True, 'wl_driver_present': True} | {'bitcell_array_present': True, 'dummy_present': True, 'replica_present': True, 'precharge_present': True, 'mux_present': True, 'sense_amp_present': True, 'write_driver_present': True, 'wl_driver_present': True} | True |
| power_summary.power_rail_overlap_positive_count | None | 33 | False |
| power_summary.same_net_power_overlap_pass | None | True | False |
| power_summary.bitcell_rail_continuity_visible | UNKNOWN | True | False |
| power_summary.rail_stitch_visible | UNKNOWN | True | False |
| cell_hierarchy | DIFF | DIFF | False |


## new_golden_reference vs M5_integrated

| metric | new_golden_reference | M5_integrated | match |
| --- | --- | --- | --- |
| file_size_bytes | 389826 | 310208 | False |
| top_cell | sram_8x64_wpr4_fd45 | openyield_layoutgen_integrated_sram__source_generated | False |
| cell_count | 33 | 66 | False |
| sref_count | 788 | 1462 | False |
| boundary_count | 5418 | 3646 | False |
| path_count | 0 | 0 | True |
| bbox | {'x0': -0.1, 'y0': -0.105, 'x1': 36.6225, 'y1': 44.145, 'width': 36.722500000000004, 'height': 44.25, 'shape_count': 5418} | {'x0': -0.1, 'y0': -0.105, 'x1': 42.7725, 'y1': 47.4, 'width': 42.8725, 'height': 47.504999999999995, 'shape_count': 3646} | False |
| layer_datatype_summary | {'1/0': 358, '10/0': 284, '11/0': 1083, '12/0': 389, '13/0': 1446, '13/2': 11, '14/0': 356, '15/0': 552, '15/2': 14, '16/0': 176, '17/0': 73, '17/2': 2, '2/0': 57, '239/0': 38, '3/0': 45, '4/0': 67, '5/0': 58, '6/0': 64, '9/0': 345} | {'1/0': 356, '10/0': 283, '11/0': 964, '12/0': 227, '13/0': 760, '13/2': 22, '14/0': 64, '15/0': 176, '15/2': 28, '17/0': 14, '17/2': 4, '2/0': 54, '239/0': 36, '260/0': 3, '261/0': 6, '262/0': 5, '263/0': 6, '265/0': 34, '3/0': 45, '4/0': 66, '5/0': 57, '6/0': 63, '9/0': 373} | False |
| per_layer_shape_count | {'1/0': 358, '10/0': 284, '11/0': 1083, '12/0': 389, '13/0': 1446, '13/2': 11, '14/0': 356, '15/0': 552, '15/2': 14, '16/0': 176, '17/0': 73, '17/2': 2, '2/0': 57, '239/0': 38, '3/0': 45, '4/0': 67, '5/0': 58, '6/0': 64, '9/0': 345} | {'1/0': 356, '10/0': 283, '11/0': 964, '12/0': 227, '13/0': 760, '13/2': 22, '14/0': 64, '15/0': 176, '15/2': 28, '17/0': 14, '17/2': 4, '2/0': 54, '239/0': 36, '260/0': 3, '261/0': 6, '262/0': 5, '263/0': 6, '265/0': 34, '3/0': 45, '4/0': 66, '5/0': 57, '6/0': 63, '9/0': 373} | False |
| gen_col_mux_hierarchy_presence | {'exact_instance_count': 32, 'wrapper_instance_count': 32, 'wrapper_cell_names': ['gen_col_mux'], 'present_in_top_hierarchy': True} | {'exact_instance_count': 0, 'wrapper_instance_count': 0, 'wrapper_cell_names': [], 'present_in_top_hierarchy': False} | False |
| tri_gate_hierarchy_presence | {'exact_instance_count': 8, 'wrapper_instance_count': 8, 'wrapper_cell_names': ['tri_gate'], 'present_in_top_hierarchy': True} | {'exact_instance_count': 16, 'wrapper_instance_count': 16, 'wrapper_cell_names': ['tri_gate'], 'present_in_top_hierarchy': True} | False |
| visible_structure_summary | {'bitcell_array_present': True, 'dummy_present': True, 'replica_present': True, 'precharge_present': True, 'mux_present': True, 'sense_amp_present': True, 'write_driver_present': True, 'wl_driver_present': True} | {'bitcell_array_present': True, 'dummy_present': True, 'replica_present': True, 'precharge_present': True, 'mux_present': True, 'sense_amp_present': True, 'write_driver_present': True, 'wl_driver_present': True} | True |
| power_summary.power_rail_overlap_positive_count | None | 33 | False |
| power_summary.same_net_power_overlap_pass | None | True | False |
| power_summary.bitcell_rail_continuity_visible | UNKNOWN | True | False |
| power_summary.rail_stitch_visible | UNKNOWN | True | False |
| cell_hierarchy | DIFF | DIFF | False |

