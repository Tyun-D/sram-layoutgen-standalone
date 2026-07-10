# M11C2 Real Substitution Proof

- `baseline_target_cell` status=`FOUND` details=`{"name": "gen_wl_driver", "bbox": [-0.055, -0.0325, 3.02, 1.4], "polygon_count": 9, "reference_count": 2, "label_count": 5, "layer_summary": {"11/0": 8, "239/0": 1}, "label_summary": {"A@11/0": 1, "B@11/0": 1, "Z@11/0": 1, "gnd@11/0": 1, "vdd@11/0": 1}}`
- `m11w_wrapper_fingerprint` status=`FOUND` details=`{"wrapper_top_cell": "M11W_wordline_driver_wrapper_candidate", "replacement_cell": "gen_wl_driver", "wrapper_marker_cell": "M11W_wordline_driver_wrapper_marker", "marker_polygon_count": 3, "marker_label_count": 3, "marker_layers": ["11/0", "9/0"], "shift_applied": [-0.08, -0.105], "dgs_labels_after_replacement": ["D", "G", "S"]}`
- `replacement_target_cell` status=`FOUND` details=`{"name": "gen_wl_driver", "bbox": [-0.055, -0.033, 3.02, 1.4], "polygon_count": 12, "reference_count": 2, "label_count": 8, "layer_summary": {"11/0": 10, "239/0": 1, "9/0": 1}, "label_summary": {"A@11/0": 1, "B@11/0": 1, "D@11/0": 1, "G@9/0": 1, "S@11/0": 1, "Z@11/0": 1, "gnd@11/0": 1, "vdd@11/0": 1}}`
- `dgs_labels_introduced` status=`PASS` details=`{"baseline_dgs": [], "output_dgs": ["D", "G", "S"]}`
- `label_only_substitution` status=`PASS` details=`False`
- `outside_placement_substitution` status=`PASS` details=`False`
- `real_substitution_proof_status` status=`PASS_WRAPPER_DGS_GEOMETRY_MATCH` details=`M11W wrapper-derived D/G/S marker geometry is present inside gen_wl_driver while the top-level placement count remains unchanged.`
