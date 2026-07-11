# M12C3A Parameterized Device Gate Generator Report

Check PINV A/Z pins lie on real accessible metal.
Check VDD/VSS rails are clear and aligned to reasonable cell boundaries.
Check NMOS/PMOS, implant, well, and tap relationships are visually sensible.
Check different-size PINV variants visibly differ in physical geometry.
Check TRANSMISSION_GATE IN/OUT/CTR_P/CTR_N pins are clearly distinguished.
Check TRANSMISSION_GATE contains one NMOS and one PMOS rather than proxy rectangles.
Check the atlas for obvious overlap, fracture, or empty-cell issues.

- status_file_read: `True`
- status_file_updated: `True`
- goal_file_read: `True`
- goal_file_updated: `True`
- progress_file_updated: `True`
- m12c3r_report_loaded: `True`
- m12c3r_gate_passed: `True`
- can_enter_M12C3A_from_M12C3R: `True`
- openyield_version_verified: `True`
- openyield_sha: `1c34428d8b913963c4971d093b1a7c2df97a2509`
- physical_tech_contract_loaded: `True`
- physical_tech_contract_status: `LOCKED_FREEPDK45_V1`
- channel_length_contract_loaded: `True`
- channel_length_policy: `FIXED_TECH_MINIMUM`
- channel_length_nm: `50`
- current_stage_delta_from_M12C3R: `M12C3A resolves symbolic source variants into concrete FreePDK45 widths, instantiates OpenRAM-backed primitive geometry, exports smoke GDS, and runs per-cell DRC.`
- why_symbolic_source_variant_is_not_yet_a_concrete_gds_variant: `Expressions such as 90*drive_scale**0.25 are templates; the adapter must first bind them to a concrete SRAM spec before naming, caching, and GDS export are valid.`
- why_openram_thin_adapter_is_preferred_over_new_proxy_geometry: `OpenRAM already provides FreePDK45 transistor/contact-aware generators, so a thin adapter preserves real device geometry and provenance without inventing proxy rectangles.`
- why_M12C3A_must_stop_before_composite_control_logic: `This stage only locks and verifies P0 primitive smoke cells. Composite gates, DFFs, delay chains, and TIME assembly remain out of scope.`
- concrete_parameter_resolution_completed: `True`
- reference_config_16x16_resolved: `True`
- reference_config_64x8_resolved: `True`
- symbolic_variant_count_before_resolution: `6`
- unresolved_symbolic_variant_count_after_resolution: `0`
- concrete_variant_count: `10`
- distinct_concrete_inverter_variant_count: `9`
- openram_bootstrap_passed: `True`
- openram_backend_execution_mode: `IN_PROCESS_OPENRAM_BOOTSTRAP`
- openram_worktree_modified: `False`
- openram_code_modified: `False`
- openram_code_copied_into_project: `False`
- openram_called_as_external_backend: `True`
- openram_license_type: `BSD-3-Clause`
- pinv_adapter_implemented: `True`
- transmission_gate_adapter_implemented: `True`
- gds_export_implemented: `True`
- spec_export_implemented: `True`
- source_trace_export_implemented: `True`
- generation_cache_implemented: `True`
- requested_actual_parameter_mapping_completed: `True`
- pinv_exact_match_count: `7`
- pinv_grid_rounded_match_count: `2`
- pinv_low_level_ptx_composition_count: `0`
- pinv_unsupported_count: `0`
- transmission_gate_parameter_match: `True`
- primitive_generation_attempted: `True`
- primitive_generation_passed: `True`
- generated_pinv_variant_count: `9`
- generated_transmission_gate_count: `1`
- generated_cell_count: `10`
- all_generated_gds_parsed: `True`
- all_generated_bbox_valid: `True`
- all_generated_real_geometry_present: `True`
- all_generated_pin_sets_verified: `True`
- all_generated_pin_geometry_verified: `True`
- all_generated_power_rails_verified: `True`
- all_generated_well_implant_verified: `True`
- all_generated_contact_verified: `True`
- all_generated_device_counts_verified: `True`
- all_generated_source_trace_complete: `True`
- all_generated_sram_spec_complete: `True`
- distinct_variant_fingerprints_verified: `True`
- deterministic_regeneration_verified: `True`
- incorrect_cache_sharing_count: `0`
- primitive_cell_drc_run: `True`
- primitive_cell_drc_pass_count: `10`
- primitive_cell_drc_fail_count: `0`
- primitive_smoke_total_drc_marker_count: `0`
- primitive_smoke_drc_passed: `True`
- can_claim_parameterized_primitive_generator_locked: `True`
- can_claim_parameterized_primitive_generator_implemented: `True`
- can_claim_generated_p0_primitives_machine_verified: `True`
- can_claim_generated_p0_primitives_drc_clean: `True`
- can_claim_generated_p0_primitives_human_verified: `False`
- can_claim_control_logic_mapping_ready: `False`
- can_claim_control_logic_physical_ready: `False`
- can_claim_custom_netlist_driven_layout_generation: `False`
- can_claim_lvs_clean: `False`
- can_claim_signoff_ready: `False`
- human_review_required: `True`
- human_review_required_item_count: `7`
- recommended_next_stage: `M12C3AH_PRIMITIVE_SMOKE_VISUAL_REVIEW`
- recommended_next_stage_reason: `The bounded OpenRAM-backed primitives now generate concrete FreePDK45 geometry and pass machine verification plus per-cell DRC, but pin accessibility, well/tap relationships, rail boundaries, and transmission-gate visual mapping still require explicit human review.`
- remaining_M12C3A_blockers: `['M12N2-B02', 'M12N2-B04', 'M12N2-B05', 'M12N2-B07', 'M12C-B10', 'M12C-B11', 'M12C-B14', 'M12C3A-B03']`
- remaining_M12C3A_blockers_count: `8`
- can_enter_next_stage_before_human_review: `False`
