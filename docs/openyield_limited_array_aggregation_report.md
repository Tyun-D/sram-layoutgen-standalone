# OpenYield Limited Array Aggregation Report

This smoke report builds a metadata-only aggregation plan for audited storage-array cells. It does not generate GDS, alter placement, merge rails, or touch peripheral macros.

## Summary

- requested enable_openyield_array_aggregation: `True`
- default disabled keeps empty plan: `True`
- enabled plan active: `True`
- rows: `2`
- cols: `16`
- changed GDS flow: `False`
- generated GDS: `False`
- allowed macros: `cell_1rw, dummy_cell_1rw, replica_cell_1rw`

## Plans

| role | macro | rows | cols | instances | width | height | power policy | notes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| bitcell_array | cell_1rw | 2 | 16 | 32 | 14.32 | 3.1300000000000003 | tb_shared_hint_only | x=origin_x+col*cell_width, y=origin_y+row*cell_height, orientation=R0. |
| dummy_row | dummy_cell_1rw | 1 | 16 | 16 | 14.319999999999808 | 1.564999999999979 | tb_shared_hint_only | dummy_connectivity_needs_confirmation |
| dummy_column | dummy_cell_1rw | 2 | 1 | 2 | 0.894999999999988 | 3.129999999999958 | tb_shared_hint_only | dummy_connectivity_needs_confirmation |
| replica_column | replica_cell_1rw | 2 | 1 | 2 | 0.894999999999988 | 3.129999999999958 | tb_shared_hint_only | replica_wl_semantics_need_confirmation |

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