# OpenYield Array Aggregation Integration Report

This smoke report covers the metadata-only OpenYield plan and the limited standalone storage-array integration path. It does not generate GDS, alter routing, merge rails, or touch peripheral macros.

## Summary

- requested enable_openyield_array_aggregation: `True`
- default disabled keeps empty plan: `True`
- enabled plan active: `True`
- rows: `2`
- cols: `16`
- changed GDS flow: `False`
- generated GDS: `False`
- allowed macros: `cell_1rw, dummy_cell_1rw, replica_cell_1rw`
- standalone storage placement replaced: `True`
- standalone instance count: `38`
- metadata-only plan count: `52`
- count matches metadata-only plan: `False`

## Metadata-Only Plans

| role | macro | rows | cols | instances | width | height | power policy | notes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| bitcell_array | cell_1rw | 2 | 16 | 32 | 14.32 | 3.1300000000000003 | tb_shared_hint_only | x=origin_x+col*cell_width, y=origin_y+row*cell_height, orientation=R0. |
| dummy_row | dummy_cell_1rw | 1 | 16 | 16 | 14.319999999999808 | 1.564999999999979 | tb_shared_hint_only | dummy_connectivity_needs_confirmation |
| dummy_column | dummy_cell_1rw | 2 | 1 | 2 | 0.894999999999988 | 3.129999999999958 | tb_shared_hint_only | dummy_connectivity_needs_confirmation |
| replica_column | replica_cell_1rw | 2 | 1 | 2 | 0.894999999999988 | 3.129999999999958 | tb_shared_hint_only | replica_wl_semantics_need_confirmation |

## Standalone Storage Integration

| array | role | macro | rows | cols | pitch_x | pitch_y | orientation | power policy |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| bitcell_array | bitcell_array | cell_1rw | 2 | 16 | 0.895 | 1.5650000000000002 | R0 | tb_shared_hint_only |
| dummy_left_array | dummy_bitcell | dummy_cell_1rw | 2 | 1 | 0.894999999999988 | 1.564999999999979 | R0 | tb_shared_hint_only |
| dummy_right_array | dummy_bitcell | dummy_cell_1rw | 2 | 1 | 0.894999999999988 | 1.564999999999979 | R0 | tb_shared_hint_only |
| replica_bitline_array | replica_bitline | replica_cell_1rw | 2 | 1 | 0.894999999999988 | 1.564999999999979 | R0 | tb_shared_hint_only |

Count note: metadata-only plan includes a dummy row; standalone integration preserves the existing bitcell + left dummy + right dummy + replica column topology.

## Excluded Macros

| macro | reason |
| --- | --- |
| dff | standard_cell_row_required: do not aggregate with storage-array cells. |
| gen_col_mux | missing_power_metadata: vdd is not proven, shared rail is forbidden. |
| gen_nand2 | logic_gate: not part of limited storage-array aggregation. |
| gen_nand4 | logic_gate: not part of limited storage-array aggregation. |
| gen_precharge | peripheral_macro: not part of limited storage-array aggregation. |
| gen_wl_driver | needs_semantic_confirmation: B/wordline_enable semantics still need confirmation. |
| sense_amp | architecture_adapter_required: OpenYield has Q/QB, local sense_amp has single-ended dout. |
| tri_gate | standard_cell_row_required: do not aggregate with storage-array cells. |
| write_driver | rail_needs_manual_review: keep legacy/peripheral placement until rail sharing is proven. |

## Smoke Checks

| check | passed | details |
| --- | --- | --- |
| default_disabled_keeps_empty_plan | True | - |
| explicit_switch_controls_enabled_plan | True | - |
| only_allowed_macros_present | True | observed_macros=['cell_1rw', 'dummy_cell_1rw', 'replica_cell_1rw'] |
| peripheral_macros_excluded | True | disallowed_observed=[] |
| placement_count_matches_expected | True | expected=52, actual=52 |
| gds_flow_unchanged | True | - |
| standalone_default_disabled_keeps_legacy_path | True | - |
| standalone_only_allowed_storage_macros_present | True | observed_macros=['cell_1rw', 'dummy_cell_1rw', 'replica_cell_1rw'] |
| standalone_peripheral_macros_excluded | True | disallowed_observed=[] |
| standalone_storage_instance_count_matches_existing_topology | True | expected=38, actual=38 |
| standalone_gds_and_routing_flow_unchanged | True | - |