# OpenYield SRAM LayoutGen Project Status

## 1. Current Correct Goal

在已确认的 M10 source-backed translator v2 与 M11 config/variation 证据基础上，审计并补齐 netlist-to-layout 所需的十项资产，明确哪些可复用、哪些必须废弃、哪些仍待补齐。

## 2. Current Stage

- current_stage: `M12`
- next_stage: `WAIT_HUMAN_KLAYOUT_REVIEW`
- human_klayout_review_required_every_stage: `True`
- can_enter_next_stage_without_human_review: `False`

## 3. Goal / Progress Files

- goal_files: `PROJECT_NETLIST_TO_LAYOUT_GOAL.md`
- progress_files: `PROJECT_NETLIST_TO_LAYOUT_PROGRESS.md`

## 4. Ten Required Assets

- NETLIST_SEMANTICS: `COMPLETE` evidence=`outputs/M10_raw_openyield_trace/current_supported_config/M10_source_backed_module_trace.csv; outputs/M10_raw_openyield_trace/current_supported_config/M10_source_backed_net_trace.csv; outputs/M10_raw_openyield_trace/current_supported_config/M10_source_backed_instance_trace.csv; outputs/M9_openyield_netlist_translator/current_supported_config/M9_net_binding_matrix.csv` next=`Freeze M10 source-backed trace as the semantic baseline for all later qualification work.`
- PHYSICAL_IMPLEMENTATION_LIBRARY: `PARTIAL` evidence=`outputs/openyield_module_gds/; docs/mapping/openyield_module_gds_inventory.csv; outputs/M9_openyield_netlist_translator/current_supported_config/M9_module_binding_matrix.csv` next=`Run M11A to qualify which OpenYield module GDS can be treated as reusable hardmacros versus fallback-only candidates.`
- PIN_BBOX_RAIL_METADATA: `PARTIAL` evidence=`outputs/openyield_module_gds/; docs/mapping/openyield_rail_rule_matrix.csv; outputs/M8R_fix_golden_geometry_delta/current_supported_config/M8R_fixed_reproduction_report.json` next=`Run M11B on top of M11A results to extract and verify pin/bbox/rail metadata only from qualified module GDS.`
- SRAM_CONFIGURATION: `PARTIAL` evidence=`docs/M11_openyield_config_variation_report.json; docs/mapping/M11_spec_field_source_matrix.csv; outputs/M11_openyield_config_variation/current_supported_config/M11_variation_support_report.json` next=`First clear M11H gate status, then keep narrowing fallback fields before claiming config-aware translator v3.`
- FLOORPLAN_RULES: `PARTIAL` evidence=`outputs/M9_openyield_netlist_translator/current_supported_config/M9_placement_routing_power_intent.json; outputs/M10_raw_openyield_trace/current_supported_config/M10_translator_generation_report.json; outputs/M11_openyield_config_variation/current_supported_config/M11_variation_support_report.json` next=`After M11A/M11B, run selective substitution smoke and variation generation to prove adaptive floorplan behavior.`
- PLACEMENT_RULES: `PARTIAL` evidence=`docs/mapping/openyield_placement_rule_matrix.csv; outputs/M9_openyield_netlist_translator/current_supported_config/M9_module_binding_matrix.csv; outputs/M8R_fix_golden_geometry_delta/current_supported_config/M8R_fixed_reproduction_report.json` next=`Use M11A/M11B outputs to rerun placement smoke for qualified substitution sites.`
- ROUTING_RULES: `PARTIAL` evidence=`outputs/M9_openyield_netlist_translator/current_supported_config/M9_net_binding_matrix.csv; outputs/M8R_fix_golden_geometry_delta/current_supported_config/M8R_fixed_reproduction_report.json; outputs/M10_raw_openyield_trace/current_supported_config/M10_vs_golden_geometry_diff_report.json` next=`Generate variation GDS and routing/power adaptation evidence after module qualification.`
- POWER_PLAN: `PARTIAL` evidence=`outputs/M8R_fix_golden_geometry_delta/current_supported_config/M8R_fixed_reproduction_report.json; docs/mapping/openyield_rail_rule_matrix.csv; outputs/M9_openyield_netlist_translator/current_supported_config/M9_net_binding_matrix.csv` next=`After M11B metadata extraction, qualify rail overlap/stitch compatibility for each substitution candidate.`
- GDS_GENERATION_FLOW: `COMPLETE` evidence=`sram_layoutgen/standalone.py; outputs/M8R_fix_golden_geometry_delta/current_supported_config/M8R_fixed_reproduction_report.json; docs/M10H_confirm_source_backed_translator_report.json; docs/M11_openyield_config_variation_report.json` next=`Keep the locked golden flow unchanged while extending inputs around it.`
- VERIFICATION_AND_TRACE: `PARTIAL` evidence=`outputs/M10_raw_openyield_trace/current_supported_config/review_gds_manifest.json; outputs/M11_openyield_config_variation/current_supported_config/review_gds_manifest.json; docs/M10H_confirm_source_backed_translator_report.json; docs/M11_openyield_config_variation_report.json` next=`Keep review manifests and diff reports, then advance to DRC/LVS feasibility only after qualification and variation adaptation work.`

## 5. Current Missing Or Partial Assets

- current_missing_or_partial_assets: `PHYSICAL_IMPLEMENTATION_LIBRARY, PIN_BBOX_RAIL_METADATA, SRAM_CONFIGURATION, FLOORPLAN_RULES, PLACEMENT_RULES, ROUTING_RULES, POWER_PLAN, VERIFICATION_AND_TRACE`
- next_assets_to_fill_in_order: `M11H, M11A, M11B, M11C, M12A, M12B, M13`

## 6. Current Claim Boundary

- can_claim_source_backed_translator_v2: `True`
- can_claim_config_aware_translator_v3: `False`
- can_claim_full_raw_openyield_netlist_compiler: `False`
- can_claim_drc_clean: `False`
- can_claim_lvs_clean: `False`
- can_claim_signoff_ready: `False`
- can_claim_openyield_module_gds_hardmacro_substitution: `False`
