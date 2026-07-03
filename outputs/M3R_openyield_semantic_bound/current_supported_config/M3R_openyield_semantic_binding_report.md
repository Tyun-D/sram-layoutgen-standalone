# M3R OpenYield Semantic Binding Report

- binding_method: `Preserve M2R layoutgen physical hierarchy and export OpenYield module/net semantics through top-level GDS labels plus explicit mapping tables.`
- m2r_physical_backbone_gds: `/data1/qujh/work/sram_layoutgen_step45_clean/outputs/M2R_full_sram_regen/current_supported_config/openyield_layoutgen_full_sram_M2R.gds`
- semantic_bound_top_gds: `/data1/qujh/work/sram_layoutgen_step45_clean/outputs/M3R_openyield_semantic_bound/current_supported_config/openyield_semantic_bound_full_sram.gds`
- openyield_required_module_count: `20`
- openyield_net_binding_count: `34`
- intent_module_row_count: `20`
- intent_net_row_count: `33`
- intent_parameter_note: `OpenYield intent JSON is narrower than the 8x64_wpr4 backbone baseline; M3R therefore preserves M2R locked physical spec and uses the intent artifacts as semantic evidence rather than as a competing physical dimension source.`
- openyield_intent_source: `/data1/qujh/work/sram_layoutgen_step45_clean/outputs/openyield_layout_intent/current_supported_config/openyield_sram_layout_intent.json`
- m2r_flow_trace_source: `/data1/qujh/work/sram_layoutgen_step45_clean/outputs/M2R_full_sram_regen/current_supported_config/M2R_layoutgen_top_flow_trace.json`
- layoutgen_top_flow_preserved: `True`
