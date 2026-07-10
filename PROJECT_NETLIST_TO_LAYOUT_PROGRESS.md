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

- next_assets_to_fill_in_order: `M11V_ROUTING_POWER_CONNECTIVITY_VERIFICATION_DEEPENING, M12A_VARIATION_GDS_GENERATION, M12B_ROUTING_POWER_ADAPTATION, M13_DRC_LVS_FEASIBILITY_AND_EQUIVALENCE_TRACE`

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
