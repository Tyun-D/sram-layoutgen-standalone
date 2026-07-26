# M3F OpenYield Semantic Binding Report

- openyield_semantic_binding_present: `True`
- binding_method: `OpenYield semantics are bound through optimized layoutgen generation flags, adapter metadata, and physical role ownership matrices rather than annotation-only labels.`
- openyield_label_only_binding_count: `0`
- openyield_physical_binding_count: `20`
- native_openyield_physical_implementation_count: `8`
- semantic_on_layoutgen_backbone_count: `12`
- m3r_label_heavy_route_replaced: `True`

| openyield_module | optimized_binding_mode | module_present_in_gds | layoutgen_role_instance_count | power_connection_status | openyield_native_physical_implementation | text_label_only_binding | physical_cell_source | fallback_used |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| CONTROL_LOGIC | optimized_layoutgen_backbone_semantic_role_binding | True | 14 | bundled_freepdk45_power_rails_via_optimized_layoutgen_backbone | False | False | layoutgen optimized gate/control backbone | False |
| DELAY_CHAIN | optimized_layoutgen_backbone_semantic_role_binding | True | 6 | bundled_freepdk45_power_rails | False | False | legacy gen_delay_inv macro chain | True |
| DFF_ROW | optimized_layoutgen_backbone_semantic_role_binding | True | 8 | bundled_freepdk45_power_rails | False | False | legacy control-logic composition | True |
| GATED_CLOCK_PATH | optimized_layoutgen_backbone_semantic_role_binding | True | 4 | bundled_freepdk45_power_rails | False | False | legacy control-logic composition | True |
| PRECHARGE_ENABLE_PATH | optimized_layoutgen_backbone_semantic_role_binding | True | 4 | bundled_freepdk45_power_rails | False | False | legacy control-logic composition | True |
| SENSE_ENABLE_PATH | optimized_layoutgen_backbone_semantic_role_binding | True | 4 | bundled_freepdk45_power_rails | False | False | legacy control-logic composition | True |
| WORDLINE_ENABLE_PATH | optimized_layoutgen_backbone_semantic_role_binding | True | 4 | bundled_freepdk45_power_rails | False | False | legacy control-logic composition | True |
| WRITE_ENABLE_PATH | optimized_layoutgen_backbone_semantic_role_binding | True | 4 | bundled_freepdk45_power_rails | False | False | legacy control-logic composition | True |
| bitcell_array | optimized_openyield_storage_array_aggregation | True | 512 | bundled_freepdk45_power_rails | True | False | cell_1rw hardcell array | False |
| column_mux | optimized_column_mux_adapter | True | 32 | shared_rail_disabled | True | False | gen_col_mux_vdd_labeled | False |
| decoder_gate_cells | optimized_layoutgen_gate_row_packing_physical_role_binding | True | 16 | bundled_freepdk45_power_rails_via_optimized_layoutgen_backbone | False | False | layoutgen optimized gate/control backbone | False |
| dummy_array | optimized_openyield_storage_array_aggregation | True | 32 | bundled_freepdk45_power_rails | True | False | dummy_cell_1rw hardcell array | False |
| precharge | optimized_layoutgen_backbone_semantic_role_binding | True | 32 | bundled_freepdk45_power_rails | False | False | legacy gen_precharge macro | True |
| replica_array | optimized_openyield_storage_array_aggregation | True | 17 | bundled_freepdk45_power_rails | True | False | replica_cell_1rw hardcell array | False |
| row_decoder | optimized_layoutgen_gate_row_packing_physical_role_binding | True | 16 | bundled_freepdk45_power_rails_via_optimized_layoutgen_backbone | False | False | layoutgen optimized gate/control backbone | False |
| sense_amp | optimized_sense_amp_adapter | True | 8 | bundled_freepdk45_power_rails | True | False | legacy sense_amp hardmacro | False |
| wordline_decoder | optimized_layoutgen_gate_row_packing_physical_role_binding | True | 16 | bundled_freepdk45_power_rails_via_optimized_layoutgen_backbone | False | False | layoutgen optimized gate/control backbone | False |
| wordline_driver | optimized_wordline_driver_adapter | True | 16 | shared_rail_disabled | True | False | gen_wl_driver | False |
| wordline_driver_gate_cells | optimized_wordline_driver_adapter_on_layoutgen_row_path | True | 16 | bundled_freepdk45_power_rails_via_optimized_layoutgen_backbone | True | False | layoutgen optimized gate/control backbone | False |
| write_driver | optimized_write_driver_adapter | True | 8 | shared_rail_disabled | True | False | write_driver | False |
