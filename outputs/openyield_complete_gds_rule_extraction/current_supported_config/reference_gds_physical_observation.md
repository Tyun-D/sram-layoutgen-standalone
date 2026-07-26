# Reference GDS Physical Observation

- reference_gds_status: `FOUND_EXISTING`
- reference_only: `True`
- gds_path: `/data1/qujh/work/sram_layoutgen_step45_clean/outputs/layout_prototype/baseline_legacy/sram_8x64_wpr4_fd45.complete.gds`
- top_cell: `sram_8x64_wpr4_fd45`
- bbox: `{'x0': 0.0, 'y0': 0.0, 'x1': 36.6225, 'y1': 45.95, 'width': 36.6225, 'height': 45.95}`
- cell_count: `33`
- recursive_instance_count: `2565`
- array_like_dense_region_bbox: `{'x0': 11.905, 'y0': 20.0475, 'x1': 34.655, 'y1': 43.4525, 'width': 22.75, 'height': 23.405}`
- row_periphery_relative_location: `left`
- column_periphery_relative_location: `below`
- power_strap_or_rail_layers: `['1/0', '2/0', '3/0']`
- top_pin_or_label_layers: `['1/0', '11/0', '13/0', '13/1', '15/1', '17/1', '9/0']`

## Visual Conclusions
- Reference macro `sram_8x64_wpr4_fd45` is array-centric: dense `cell_1rw` instances occupy bbox {'x0': 11.905, 'y0': 20.0475, 'x1': 34.655, 'y1': 43.4525, 'width': 22.75, 'height': 23.405}.
- Row periphery sits `left` relative to the dense array region.
- Column periphery sits `below` relative to the dense array region.
- The macro shows repeated bitcell references plus narrow precharge/column/read/write bands instead of one overlay rectangle.
- Top-level pin labels exist on dedicated label layers and accompany real geometry, not label-only inventory rows.

## Largest Shapes
- {'shape_id': 'ref_poly_0', 'layer_hint': '239/0', 'bbox': {'x0': 0.0, 'y0': 0.0, 'x1': 36.6225, 'y1': 45.95, 'width': 36.6225, 'height': 45.95}, 'area': 1682.803875}
- {'shape_id': 'ref_poly_1647', 'layer_hint': '17/0', 'bbox': {'x0': 0.3425, 'y0': 0.2, 'x1': 0.5025, 'y1': 45.75, 'width': 0.16, 'height': 45.55}, 'area': 7.288}
- {'shape_id': 'ref_poly_1648', 'layer_hint': '17/0', 'bbox': {'x0': 12.0, 'y0': 0.2, 'x1': 12.16, 'y1': 45.75, 'width': 0.16, 'height': 45.55}, 'area': 7.288}
- {'shape_id': 'ref_poly_1649', 'layer_hint': '17/0', 'bbox': {'x0': 34.56, 'y0': 0.2, 'x1': 34.72, 'y1': 45.75, 'width': 0.16, 'height': 45.55}, 'area': 7.288}
- {'shape_id': 'ref_poly_1645', 'layer_hint': '17/0', 'bbox': {'x0': 0.05, 'y0': 0.0, 'x1': 0.2, 'y1': 45.95, 'width': 0.15, 'height': 45.95}, 'area': 6.8925}
- {'shape_id': 'ref_poly_1646', 'layer_hint': '17/0', 'bbox': {'x0': 36.4225, 'y0': 0.0, 'x1': 36.5725, 'y1': 45.95, 'width': 0.15, 'height': 45.95}, 'area': 6.8925}
- {'shape_id': 'ref_poly_1643', 'layer_hint': '17/0', 'bbox': {'x0': 0.0, 'y0': 45.75, 'x1': 36.6225, 'y1': 45.9, 'width': 36.6225, 'height': 0.15}, 'area': 5.493375}
- {'shape_id': 'ref_poly_1644', 'layer_hint': '17/0', 'bbox': {'x0': 0.0, 'y0': 0.05, 'x1': 36.6225, 'y1': 0.2, 'width': 36.6225, 'height': 0.15}, 'area': 5.493375}
