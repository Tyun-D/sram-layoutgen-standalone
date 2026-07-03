# M3F Optimized Layoutgen Flow Trace

- m3r_review_failure_recorded: `True`
- optimized_layoutgen_flow_found: `True`
- optimized_layoutgen_reference_gds_found: `True`
- optimized_layoutgen_code_found: `True`
- optimized_reference_gds: `/data1/qujh/work/sram_layoutgen_step45_clean/outputs/layout_prototype/hybrid_openyield_rail_overlap/hybrid_openyield_rail_overlap.complete.gds`
- optimized_reference_report: `/data1/qujh/work/sram_layoutgen_step45_clean/outputs/layout_prototype/hybrid_openyield_rail_overlap/hybrid_openyield_rail_overlap.report.json`
- final_generation_entry: `sram_layoutgen.standalone.write_standalone`

## Final Generation Spec

- word_size: `8`
- num_words: `64`
- words_per_row: `4`
- name: `openyield_optimized_layoutgen_sram`
- enable_openyield_array_aggregation: `True`
- enable_openyield_senseamp_adapter: `True`
- enable_openyield_columnmux_adapter: `True`
- enable_openyield_writedriver_adapter: `True`
- enable_openyield_wordlinedriver_adapter: `True`
- enable_openyield_gate_row_packing: `True`
- enable_openyield_rail_to_rail_abutment: `True`
- enable_openyield_power_rail_overlap_packing: `True`
- enable_openyield_dff_row_packing: `True`
- exclude_dff_vertical_overlap: `True`
- openyield_storage_row_orientation_policy: `alternating_mx`

## Reused Optimization Components

| component | path | found | reuse_in_M3F | evidence |
| --- | --- | --- | --- | --- |
| optimized_reference_gds | /data1/qujh/work/sram_layoutgen_step45_clean/outputs/layout_prototype/hybrid_openyield_rail_overlap/hybrid_openyield_rail_overlap.complete.gds | True | reference_and_comparison | hybrid_openyield_rail_overlap.complete.gds was found and used as optimized comparator |
| layout_prototype.generate_layout_prototype | sram_layoutgen/openyield_adapter/layout_prototype.py | True | flow_trace_and_helper_logic | build_module_coverage and packing-plan reconstruction reused |
| standalone.write_standalone | sram_layoutgen/standalone.py | True | direct_final_generation | StandaloneSpec recreated optimized hybrid flags with final top name |
| gate_row_vertical_abutment_report | sram_layoutgen/openyield_adapter/gate_row_packer.py | True | direct_final_power_restore_audit | same_net_power_rail_overlap_packing report regenerated for final M3F GDS |
| cell_rail_overlap_eligibility | sram_layoutgen/openyield_adapter/cell_rail_overlap_eligibility.py | True | audit_input | eligibility data consumed by row-abutment audit |
