# Netlist-to-Layout Progress

## Asset Status

### NETLIST_SEMANTICS

- asset_name: `网表 / module / instance / net / pin 连接语义`
- status_level: `COMPLETE`
- evidence_paths: `outputs/M10_raw_openyield_trace/current_supported_config/M10_source_backed_module_trace.csv; outputs/M10_raw_openyield_trace/current_supported_config/M10_source_backed_net_trace.csv; outputs/M10_raw_openyield_trace/current_supported_config/M10_source_backed_instance_trace.csv; outputs/M9_openyield_netlist_translator/current_supported_config/M9_net_binding_matrix.csv`
- blocking_for_next_stage: `False`
- next_action: `Freeze M10 source-backed trace as the semantic baseline for all later qualification work.`

### PHYSICAL_IMPLEMENTATION_LIBRARY

- asset_name: `模块物理实现库，包括 layoutgen cell、OpenYield module GDS、hardmacro 候选`
- status_level: `PARTIAL`
- evidence_paths: `outputs/openyield_module_gds/; docs/mapping/openyield_module_gds_inventory.csv; outputs/M9_openyield_netlist_translator/current_supported_config/M9_module_binding_matrix.csv`
- blocking_for_next_stage: `False`
- next_action: `M11W_WORDLINE_DRIVER_WRAPPER_PIN_REPAIR`

### PIN_BBOX_RAIL_METADATA

- asset_name: `pin / bbox / rail / layer / access metadata`
- status_level: `PARTIAL`
- evidence_paths: `outputs/openyield_module_gds/; docs/mapping/openyield_rail_rule_matrix.csv; outputs/M8R_fix_golden_geometry_delta/current_supported_config/M8R_fixed_reproduction_report.json`
- blocking_for_next_stage: `False`
- next_action: `M11W_WORDLINE_DRIVER_WRAPPER_PIN_REPAIR`

### SRAM_CONFIGURATION

- asset_name: `SRAM 参数配置，包括 word_size、num_words、words_per_row、rows、cols、mux ratio`
- status_level: `PARTIAL`
- claim: `config-aware translator v3 confirmed`
- evidence_paths: `docs/M11_openyield_config_variation_report.json; docs/mapping/M11_spec_field_source_matrix.csv; outputs/M11_openyield_config_variation/current_supported_config/M11_variation_support_report.json`
- remaining_gap: `capacity fallback still exists; word_size / num_words / words_per_row are not fully raw-source-backed`
- blocking_for_next_stage: `False`
- next_action: `No longer block M11A; revisit later only if full raw netlist compiler is required.`

### FLOORPLAN_RULES

- asset_name: `floorplan 规则，包括 array、row path、column path、control、top pin 区域`
- status_level: `PARTIAL`
- evidence_paths: `outputs/M9_openyield_netlist_translator/current_supported_config/M9_placement_routing_power_intent.json; outputs/M10_raw_openyield_trace/current_supported_config/M10_translator_generation_report.json; outputs/M11_openyield_config_variation/current_supported_config/M11_variation_support_report.json`
- blocking_for_next_stage: `True`
- next_action: `After M11A/M11B, run selective substitution smoke and variation generation to prove adaptive floorplan behavior.`

### PLACEMENT_RULES

- asset_name: `placement / abutment / orientation / pitch 对齐规则`
- status_level: `PARTIAL`
- evidence_paths: `docs/mapping/openyield_placement_rule_matrix.csv; outputs/M9_openyield_netlist_translator/current_supported_config/M9_module_binding_matrix.csv; outputs/M8R_fix_golden_geometry_delta/current_supported_config/M8R_fixed_reproduction_report.json`
- blocking_for_next_stage: `True`
- next_action: `Use M11A/M11B outputs to rerun placement smoke for qualified substitution sites.`

### ROUTING_RULES

- asset_name: `WL、BL/BR、control、data、addr、enable 等 routing 规则`
- status_level: `PARTIAL`
- evidence_paths: `outputs/M9_openyield_netlist_translator/current_supported_config/M9_net_binding_matrix.csv; outputs/M8R_fix_golden_geometry_delta/current_supported_config/M8R_fixed_reproduction_report.json; outputs/M10_raw_openyield_trace/current_supported_config/M10_vs_golden_geometry_diff_report.json`
- blocking_for_next_stage: `True`
- next_action: `Generate variation GDS and routing/power adaptation evidence after module qualification.`

### POWER_PLAN

- asset_name: `VDD/GND rail overlap、stitch、abutment、top power pin 策略`
- status_level: `PARTIAL`
- evidence_paths: `outputs/M8R_fix_golden_geometry_delta/current_supported_config/M8R_fixed_reproduction_report.json; docs/mapping/openyield_rail_rule_matrix.csv; outputs/M9_openyield_netlist_translator/current_supported_config/M9_net_binding_matrix.csv`
- blocking_for_next_stage: `True`
- next_action: `After M11B metadata extraction, qualify rail overlap/stitch compatibility for each substitution candidate.`

### GDS_GENERATION_FLOW

- asset_name: `GDS generator / layoutgen golden flow / write_standalone 入口`
- status_level: `COMPLETE`
- evidence_paths: `sram_layoutgen/standalone.py; outputs/M8R_fix_golden_geometry_delta/current_supported_config/M8R_fixed_reproduction_report.json; docs/M10H_confirm_source_backed_translator_report.json; docs/M11_openyield_config_variation_report.json`
- blocking_for_next_stage: `False`
- next_action: `Keep the locked golden flow unchanged while extending inputs around it.`

### VERIFICATION_AND_TRACE

- asset_name: `GDS sanity、golden diff、module/net trace、DRC/LVS feasibility、人工 KLayout review`
- status_level: `PARTIAL`
- evidence_paths: `outputs/M10_raw_openyield_trace/current_supported_config/review_gds_manifest.json; outputs/M11_openyield_config_variation/current_supported_config/review_gds_manifest.json; docs/M10H_confirm_source_backed_translator_report.json; docs/M11_openyield_config_variation_report.json`
- blocking_for_next_stage: `True`
- next_action: `Keep review manifests and diff reports, then advance to DRC/LVS feasibility only after qualification and variation adaptation work.`

## Current Missing Or Partial Assets

- current_missing_or_partial_assets: `PHYSICAL_IMPLEMENTATION_LIBRARY, PIN_BBOX_RAIL_METADATA, SRAM_CONFIGURATION, FLOORPLAN_RULES, PLACEMENT_RULES, ROUTING_RULES, POWER_PLAN, VERIFICATION_AND_TRACE`

## Next Assets To Fill In Order

- next_assets_to_fill_in_order: `M11V2_DEEPER_CONNECTIVITY_EXTRACTION, M12A_VARIATION_GDS_GENERATION, M12B_ROUTING_POWER_ADAPTATION, M13_DRC_LVS_FEASIBILITY_AND_EQUIVALENCE_TRACE`

## Claim Boundary

- can_claim_source_backed_translator_v2: `True`
- can_claim_config_aware_translator_v3: `True`
- can_claim_full_raw_openyield_netlist_compiler: `False`
- can_claim_drc_clean: `False`
- can_claim_lvs_clean: `False`
- can_claim_signoff_ready: `False`
- can_claim_openyield_module_gds_hardmacro_substitution: `False`
- can_claim_sense_amp_smoke_substitution_attempted: `True`
- can_claim_sense_amp_smoke_substitution_passed: `True`
- can_claim_wordline_driver_smoke_substitution_attempted: `True`
- can_claim_wordline_driver_smoke_substitution_passed: `True`
- can_claim_routing_clean: `False`
- can_claim_power_clean: `False`

## M11H Gate

- m11_clean_gds_user_review_passed: `True`
- supported_variations: `8x64_wpr4, 4x32_wpr2, 16x16_wpr1`
- note: `M11H is gate closure only; it does not reopen M11 or add new functionality.`

## M11A Qualification

- first_substitution_candidates: `sense_amp, wordline_driver`
- note: `M11A does not claim module GDS hardmacro substitution complete; M11B metadata extraction is mandatory before any substitution attempt.`

## M11AR Human Review Correction

- human_review_applied: `True`
- unknown_golden_region_markers_are_real_modules: `False`
- direct_hardmacro_replace_count_after: `2`
- first_substitution_candidates_after: `sense_amp, wordline_driver`
- downgraded_modules: `column_mux, write_driver`
- note: `M11B is limited to deep pin/bbox/rail validation for sense_amp and wordline_driver only.`

## M11B Deep Metadata

- ready_for_M11C_modules: `sense_amp`
- not_ready_modules: `wordline_driver`
- note: `M11B remains machine-first; visual completeness and annotation readability stay in human review scope.`

## M11BH Human Review

- m11b_human_review_completed: `True`
- ready_for_M11C_modules_after_human_review: `sense_amp`
- not_ready_modules_after_human_review: `wordline_driver`
- M11C_scope: `sense_amp_only`
- note: `wordline_driver remains a wrapper and pin-resolution follow-up item; it must not enter M11C.`

## M11C Smoke Substitution

- substitution_scope: `sense_amp`
- excluded_modules_confirmed: `wordline_driver, column_mux, write_driver, CONTROL_LOGIC`
- note: `This is a smoke substitution only. It passes M11C human review but still does not qualify any broader hardmacro substitution claim.`

## M11CH Human Review Closure

- m11c_human_review_completed: `True`
- m11c_sense_amp_visual_review_passed: `True`
- m11c_sense_amp_annotation_readable: `True`
- m11c_sense_amp_nearby_power_routing_not_visually_broken: `True`
- remaining_M11C_blockers_before_count: `3`
- remaining_M11C_blockers_after_count: `0`
- next_stage_allowed: `M11D_POST_SENSE_AMP_SUBSTITUTION_ANALYSIS_OR_NEXT_SAFE_CANDIDATE_PLANNING`
- can_enter_M11D_after_this_gate: `True`
- note: `M11CH only clears the M11C human-review gate. It does not replace new modules and does not reopen DRC/LVS/signoff claims.`

## M11D Post Analysis

- real_substitution_proof_status: `PASS_GEOMETRY_FINGERPRINT_MATCH`
- openyield_sense_amp_fingerprint_found_in_M11C: `True`
- hierarchy_delta_status: `ONLY_SENSE_AMP_LEAF_FINGERPRINT_CHANGED`
- unexpected_non_sense_amp_change_count: `0`
- recommended_next_stage: `M11W_WORDLINE_DRIVER_WRAPPER_PIN_REPAIR`
- recommended_next_stage_reason: `M11D proves that sense_amp was a real in-hierarchy OpenYield fingerprint replacement, but it does not make any new module ready. The only previously shortlisted next candidate remains wordline_driver, and M11B still blocks it on unresolved D/G/S wrapper pin geometry.`
- human_klayout_review_required: `False`
- can_enter_next_stage_before_human_review: `True`
- note: `M11D is post-analysis and planning only. It does not perform any new module substitution.`

## M11W Wordline Driver Repair

- repair_strategy_used: `STRATEGY_B_WRAPPER_PIN_EXPOSURE`
- dgs_pins_resolved: `True`
- unresolved_pin_count: `0`
- wrapper_generated: `True`
- wordline_driver_ready_for_smoke_substitution: `True`
- next_stage_allowed: `M11C2_WORDLINE_DRIVER_SMOKE_SUBSTITUTION`
- human_klayout_review_required: `False`
- can_enter_next_stage_before_human_review: `True`
- note: `M11W only repairs wordline_driver wrapper/pin metadata. It does not perform any SRAM top substitution.`

## M11C2 Wordline Driver Smoke Substitution

- substitution_scope: `wordline_driver`
- excluded_modules_confirmed: `sense_amp, column_mux, write_driver, CONTROL_LOGIC, precharge, bitcell_array, dummy_array, replica_array`
- human_klayout_review_required: `False`
- can_enter_next_stage_before_human_review: `True`
- next_stage_allowed: `M11V_ROUTING_POWER_CONNECTIVITY_VERIFICATION_DEEPENING`
- note: `M11C2 passes human review with a routing/power caveat. The isolated smoke substitution is accepted, but nearby routing/power cleanliness remains inconclusive because the baseline layoutgen routing itself may already be limited.`

## M11C2H Human Review Closure

- m11c2_human_review_completed: `True`
- m11c2_wordline_driver_visual_review_passed: `True`
- m11c2_wordline_driver_annotation_readable: `True`
- m11c2_wordline_driver_nearby_power_routing_review_status: `INCONCLUSIVE_BASELINE_ROUTING_LIMITED`
- m11c2_no_obvious_new_break_reported_by_human: `True`
- m11c2_nearby_power_routing_visually_confirmed_clean: `False`
- remaining_M11C2_blockers_before_count: `3`
- remaining_M11C2_blockers_after_count: `0`
- recommended_next_stage: `M11V_ROUTING_POWER_CONNECTIVITY_VERIFICATION_DEEPENING`
- recommended_next_stage_reason: `Because M11C2 passed isolated wordline_driver smoke substitution, but nearby routing/power cleanliness remains visually inconclusive due to baseline layoutgen routing limitations. Verification should be deepened before expanding substitution scope.`
- next_stage_allowed: `M11V_ROUTING_POWER_CONNECTIVITY_VERIFICATION_DEEPENING`
- can_enter_M11V_after_this_gate: `True`
- note: `M11C2H only clears the M11C2 human-review gate with a routing/power caveat. It does not replace new modules and does not reopen routing/power/DRC/LVS/signoff claims.`

## M11V Routing Power Connectivity Verification

- verification_status: `INCONCLUSIVE`
- baseline_power_risk_level: `MEDIUM_BASELINE_LIMITED`
- baseline_routing_risk_level: `HIGH_BASELINE_LIMITED`
- sense_amp_incremental_risk_level: `LOW_INCREMENTAL_RISK`
- wordline_driver_incremental_risk_level: `LOW_INCREMENTAL_RISK`
- recommended_next_stage: `M11V2_DEEPER_CONNECTIVITY_EXTRACTION`
- recommended_next_stage_reason: `Both isolated substitutions keep top bbox, hierarchy placement, and non-target geometry stable, and no new substitution-specific power/routing risk is detected. However, the baseline layoutgen routing/power cleanliness is still not proven and the wordline_driver neighborhood remains machine-inconclusive under that baseline limitation. Deeper extracted connectivity evidence is required before attempting a combined substitution.`
- human_klayout_review_required: `False`
- can_enter_next_stage_before_human_review: `True`
- note: `M11V is a read-only verification stage. It compares baseline, sense_amp-only, and wordline_driver-only GDS outputs to judge incremental routing/power risk without generating any new substitution top.`

## M12O OpenRAM OpenYield Gap Audit

- openram_reference_gds_found: `True`
- openram_reference_top_cell: `sram_1rw_32x16_freepdk45`
- openyield_netlist_candidate_count: `14`
- openyield_single_authoritative_netlist_proven: `False`
- control_logic_gap_status: `OPENRAM_PRESENT_LAYOUTGEN_MISSING_OPENYIELD_PHYSICAL_UNQUALIFIED`
- parameterization_blockers_count: `5`
- external_dependency_blockers_count: `6`
- recommended_next_stage: `M12N_LOCK_OPENYIELD_AUTHORITATIVE_NETLIST`
- recommended_next_stage_reason: `M12O finds a usable OpenRAM full-reference GDS and a rich OpenYield parameter/config codebase, but it does not prove a single authoritative OpenYield complete SRAM top netlist. Locking that authority is a harder blocker than directly continuing M11V2 connectivity deepening, because control-logic alignment, parameterized SRAM planning, and later combined substitution all still depend on one unambiguous netlist source of truth.`
- note: `M12O is an audit/planning stage only. It does not perform any new module substitution or generate a new final SRAM top.`

## M12N OpenYield Authoritative Netlist Lock

- authoritative_netlist_lock_status: `PARTIAL_SUBCIRCUIT_LIBRARY_ONLY`
- authoritative_netlist_type: `TESTBENCH_BACKED_PARAMETERIZED_SPICE_GENERATOR`
- sample_netlist_generation_passed: `True`
- openyield_parameterized_netlist_generator_proven: `True`
- openyield_complete_sram_top_proven: `False`
- openyield_control_logic_source_locked: `True`
- recommended_next_stage: `M12C_CONTROL_LOGIC_GAP_DEFINITION`
- recommended_next_stage_reason: `M12N proves that OpenYield contains a parameterized Python SPICE/testbench generator chain centered on `Sram6TCoreTestbench.create_testbench`, and it can emit a sample SRAM-related netlist. However, that emitted artifact is still a simulation testbench netlist with supplies, stimuli, and measurement scaffolding rather than a locked pure SRAM top authority. The next blocking step is to define how the traced OpenYield control logic and enable paths map onto the OpenRAM/layoutgen control-logic gap before any custom netlist-driven layout flow can be claimed.`
- note: `M12N is a source-lock stage only. It does not generate a final SRAM GDS and does not reopen DRC/LVS/signoff claims.`

## M12N2 Clean OpenYield SRAM Top

- clean_top_extraction_passed: `True`
- clean_top_spice_path: `outputs/M12N2_clean_openyield_sram_top/current_supported_config/openyield_sram_top_v1.sp`
- openyield_local_sha: `1c34428d8b913963c4971d093b1a7c2df97a2509`
- openyield_version_match: `True`
- openyield_worktree_clean: `True`
- time_control_role_status_before: `AMBIGUOUS_REQUIRES_TEAM_CONFIRMATION`
- time_control_role_status_after: `ON_CHIP_CONTROL_LOGIC`
- time_is_testbench_stimulus: `False`
- time_is_design_subcircuit: `True`
- time_is_instantiated_in_sram_design_graph: `True`
- time_outputs_consumed_by_sram_periphery: `True`
- openyield_control_logic_netlist_source_locked: `True`
- openyield_control_logic_physical_implementation_ready: `False`
- can_claim_control_logic_source_locked: `True`
- can_claim_control_logic_mapping_ready: `False`
- can_claim_control_logic_physical_ready: `False`
- can_claim_custom_netlist_driven_layout_generation: `False`
- recommended_next_stage: `M12C_CONTROL_LOGIC_GAP_DEFINITION`
- recommended_next_stage_reason: `The latest OpenYield main source proves that TIME is a real SRAM design subcircuit containing DFFs, gated clocks, delay chains, and enable-generation logic. The control-logic netlist source is therefore locked, while its physical implementation and mapping into the layoutgen/OpenRAM floorplan remain incomplete.`
- next_stage_allowed: `M12C_CONTROL_LOGIC_GAP_DEFINITION`
- can_enter_M12C_after_this_gate: `True`
- human_review_required: `False`
- can_enter_next_stage_before_human_review: `True`
- note: `M12N2R is evidence correction and gate closure only. It does not generate new GDS, does not start control-logic physical implementation, and does not reopen DRC/LVS/signoff claims.`

## M12C Control Logic Gap Definition

- m12n2r_gate_passed: `True`
- openyield_version_verified: `True`
- openyield_sha: `1c34428d8b913963c4971d093b1a7c2df97a2509`
- time_hierarchy_extracted: `True`
- time_module_count: `22`
- time_primitive_count: `12`
- time_instance_count_for_reference_config: `289`
- operation_topology_status: `READ_WRITE_SUPERSET_CANONICAL`
- canonical_physical_operation_topology: `READ_WRITE_SUPERSET`
- canonical_operation_topology_locked: `True`
- physical_module_total_count: `22`
- physical_ready_for_qualification_count: `15`
- physical_partial_count: `3`
- physical_reference_only_count: `1`
- physical_missing_count: `3`
- parameterized_transistor_layout_required_count: `1`
- bbox_metadata_coverage: `18/22`
- pin_geometry_coverage: `18/22`
- power_rail_metadata_coverage: `18/22`
- floorplan_interface_plan_generated: `True`
- candidate_control_region_defined: `True`
- top_bbox_change_expected: `True`
- review_gds_generated: `True`
- review_gds_parsed: `True`
- recommended_next_stage: `M12C2_CONTROL_LOGIC_PHYSICAL_LIBRARY_QUALIFICATION`
- remaining_M12C_blockers_count: `12`
- human_review_required: `False`
- can_enter_next_stage_before_human_review: `True`
- note: `M12C is definition-only. It does not complete control-logic layout, does not replace new SRAM modules, and does not reopen DRC/LVS/signoff claims.`

## M12C2 Progress

- Reclassified NMOS_VTG/PMOS_VTG as PDK device-model references.
- Qualified manifest entries: `7`
- Quarantined candidates: `15`
- Candidate cell DRC scope: `CELL_LEVEL_CANDIDATE_TOP_CELLS`

## M12C3 Primitive Generator Plan

- qualification_audit_complete: `True`
- control_physical_library_reuse_ready: `False`
- raw_candidate_drc_marker_count: `6661`
- duplicate_drc_artifact_detected: `True`
- unique_candidate_drc_marker_count: `3422`
- physical_tech_contract_status: `LOCKED_FREEPDK45_V1`
- trusted_device_generator_found: `True`
- trusted_device_generator_path: `/data1/qujh/OpenRAM/compiler/modules/ptx.py`
- trusted_gate_generator_found: `True`
- contact_via_generator_found: `True`
- parameterized_width_supported: `True`
- parameterized_length_supported: `False`
- can_claim_control_physical_library_qualification_audit_complete: `True`
- can_claim_control_physical_library_reuse_ready: `False`
- can_claim_parameterized_primitive_generator_locked: `True`
- can_claim_parameterized_primitive_generator_implemented: `False`
- primitive_smoke_generation_attempted: `False`
- recommended_next_stage: `M12C3A_IMPLEMENT_PARAMETERIZED_DEVICE_AND_GATE_GENERATOR`
- recommended_next_stage_reason: `The FreePDK45 tech contract and primitive-generator architecture are locked, but the trusted OpenRAM-backed path still lacks callable adapter implementation and channel-length parameter completeness, so the next step is to implement the bounded adapter-backed primitive generator.`

## M12C3R Parameter and Naming Contract Correction

- original_zero_dimension_token_detected: `True`
- original_naming_contract_superseded: `True`
- unit_normalization_failure_count: `0`
- source_pinv_instance_count: `19`
- logical_names_with_multiple_parameter_sets: `['PINV', 'PINV1', 'PINV2']`
- corrected_parameterized_cell_naming_contract_locked: `True`
- source_derived_variant_contract_locked: `True`
- size_alias_collision_prevented_by_corrected_contract: `True`
- required_channel_length_values_nm: `[50]`
- all_current_v1_lengths_equal_50nm: `True`
- openram_import_bootstrap_passed: `True`
- recommended_adapter_execution_mode: `IN_PROCESS_OPENRAM_BOOTSTRAP`
- can_claim_parameterized_primitive_generator_locked: `True`
- can_claim_parameterized_primitive_generator_implemented: `False`
- recommended_next_stage: `M12C3A_IMPLEMENT_PARAMETERIZED_DEVICE_AND_GATE_GENERATOR`
- recommended_next_stage_reason: `Units, source-derived variants, corrected naming/cache identity, fixed-50nm policy, and OpenRAM bootstrap mode are all locked, so adapter implementation can start without reopening the naming or length contract.`

## M12C3A Primitive Generator

- M12C3R correction gate passed and M12C3A concrete primitive generation completed.
- concrete drive scales 16x16: `{'address_bits': 4, 'clk_dff_count': 22, 'ref_dff_count': 22, 'clk_drive_scale': 1.0, 'pre_col_scale': 0.26153846153846155, 'pre_pmos_scale': 1.0, 'pre_drive_scale': 1, 'w_en_scale': 1, 'resolved_scales': {'pdrive': 1.0, 'pdrive2_for_pre': 1, 'w_en_scale': 1}}`
- concrete drive scales 64x8: `{'address_bits': 6, 'clk_dff_count': 16, 'ref_dff_count': 22, 'clk_drive_scale': 1.0, 'pre_col_scale': 0.13846153846153847, 'pre_pmos_scale': 4.0, 'pre_drive_scale': 1, 'w_en_scale': 1, 'resolved_scales': {'pdrive': 1.0, 'pdrive2_for_pre': 1, 'w_en_scale': 1}}`
- generated physical variants: `10` total, `9` PINV plus `1` TRANSMISSION_GATE.
- per-cell DRC total markers: `0`
- deterministic regeneration verified: `True`
- human review gate remains required: `True`
- next stage: `M12C3AH_PRIMITIVE_SMOKE_VISUAL_REVIEW`

## M12C3A3 Repair Progress

- Confirmed the original Transmission Gate short came from source/drain helper metal tying `IN` to both power rails.
- Replaced poly-only control exports with routable Metal1 gate pins through real poly contacts.
- Added machine geometry connectivity extraction that does not treat MOS channels as unconditional shorts.
- Regenerated only `TRANSMISSION_GATE_NW250_PW500_L50` and left reviewed `PINV` geometry unchanged.

## M12C3A4 Label Cleanup Progress

- Confirmed pre-cleanup duplicate wrapper/core labels across all 9 PINV cells and the repaired Transmission Gate.
- Confirmed leaked PTX `G/S/D` labels in recursive hierarchy.
- Implemented export-time reusable GDS sanitization by stripping all recursive text and re-adding only canonical top-level labels.
- Re-ran geometry preservation, connectivity regression, deterministic export, and cell-level DRC on all 10 sanitized primitives.

## M12C3A4R Evidence Closure Progress

- Verified the original M12C3A4 review atlas had 1 structure and 20 missing SREF targets.
- Rebuilt a self-contained review atlas with deterministic DEBUG_BEFORE and REUSABLE_AFTER hierarchies.
- Separated historical failure evidence from current qualified primitive state.
- Verified all reusable outputs, DRC artifacts, and prior geometry/connectivity regressions remained unchanged.

## M12C4 Composite Planning Progress

- Verified the approved reusable primitive contract and forbidden source roots.
- Extracted source-exact hierarchy for DFF/DFF_BUF/ADDR_DFF/DATA_DFF/AND/PNAND/pdrive/delay_chain/TIME from the latest OpenYield source.
- Built the composite dependency DAG and concrete 16x16/64x8 instance expansions.
- Locked primitive binding, interface audit, placement architecture, routing contract, naming/cache contract, implementation waves, and verification gates.

## M12C4R Correction Progress

- Rebuilt the 53-call source child matrix and the 232-row net matrix.
- Proved DFF has 11 child instances with 52 resolved pin-net connections.
- Replaced height-only interface risk with pairwise diagnostic placement and DRC evidence.
- Replaced routing capability guesses with executable M1/Via1/M2 diagnostic evidence.

## M12C4R2 Binding Progress

- Separated 260 all-branch source rows from the historical 232 filtered rows.
- Restored DATA_DFF and conditional TIME branches into explicit coverage matrices.
- Rebuilt source-derived concrete expansion and non-empty active leaf parent-net bindings.
- Verified all 11 DFF child instances against the approved reusable primitive contract.
