# M12C4 Composite Control Cell Generation Plan Summary

- reused_previous_artifacts: M12C3A4R approved primitive contract, reusable primitive reports, historical control logic gap files, and latest OpenYield source
- approved_primitive_root: /data1/qujh/work/sram_layoutgen_step45_clean/outputs/M12C3A4_canonical_primitive_label_cleanup/current_supported_config/reusable_cells
- forbidden_primitive_roots: /data1/qujh/work/sram_layoutgen_step45_clean/outputs/M12C3A_parameterized_device_gate_generator/current_supported_config/cells | /data1/qujh/work/sram_layoutgen_step45_clean/outputs/M12C3A3_transmission_gate_adapter_repair/current_supported_config | /data1/qujh/work/sram_layoutgen_step45_clean/outputs/M12C3A4_canonical_primitive_label_cleanup/current_supported_config/quarantined_debug_originals | /data1/qujh/work/sram_layoutgen_step45_clean/outputs/M12C3A4R_review_atlas_state_normalization/current_supported_config
- why_composite_gds_generation_is_not_allowed_in_M12C4: this stage only locks source-exact topology and implementation contracts
- why_source_exact_topology_is_required_before_placement: guessed topology would invalidate placement, routing, and verification contracts
- why_DRC_clean_primitives_do_not_automatically_form_a_correct_composite: composite nets, crossings, feedback loops, and rail seams still require explicit topology-aware composition
