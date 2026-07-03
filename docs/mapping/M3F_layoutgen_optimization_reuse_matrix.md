# M3F Layoutgen Optimization Reuse Matrix

| component | path | found | reuse_in_M3F | evidence |
| --- | --- | --- | --- | --- |
| optimized_reference_gds | /data1/qujh/work/sram_layoutgen_step45_clean/outputs/layout_prototype/hybrid_openyield_rail_overlap/hybrid_openyield_rail_overlap.complete.gds | True | reference_and_comparison | hybrid_openyield_rail_overlap.complete.gds was found and used as optimized comparator |
| layout_prototype.generate_layout_prototype | sram_layoutgen/openyield_adapter/layout_prototype.py | True | flow_trace_and_helper_logic | build_module_coverage and packing-plan reconstruction reused |
| standalone.write_standalone | sram_layoutgen/standalone.py | True | direct_final_generation | StandaloneSpec recreated optimized hybrid flags with final top name |
| gate_row_vertical_abutment_report | sram_layoutgen/openyield_adapter/gate_row_packer.py | True | direct_final_power_restore_audit | same_net_power_rail_overlap_packing report regenerated for final M3F GDS |
| cell_rail_overlap_eligibility | sram_layoutgen/openyield_adapter/cell_rail_overlap_eligibility.py | True | audit_input | eligibility data consumed by row-abutment audit |
