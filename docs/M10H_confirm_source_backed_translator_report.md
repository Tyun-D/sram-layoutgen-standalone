# M10H Confirm Source-Backed Translator Report

## Reused Artifacts

- M8R/M8RC locked golden layoutgen flow: `outputs/M8R_fix_golden_geometry_delta/current_supported_config/m8r_reproduced_fixed.gds`
  reuse_purpose: locked exact-match geometry baseline for translator-backed physical delivery
- M9/M9H translator v1: `outputs/M9_openyield_netlist_translator/current_supported_config/openyield_netlist_translated_sram.gds`
  reuse_purpose: prior translator semantics, binding bridge, and reviewed translator framing
- M10 raw source-backed trace: `outputs/M10_raw_openyield_trace/current_supported_config/openyield_source_backed_translated_sram.gds`
  reuse_purpose: source-backed module/net/instance/config trace and exact-match source-backed translator v2 evidence
- T1 OpenYield full file analysis: `docs/T1_openyield_full_file_report.json`
  reuse_purpose: key entrypoints, source inventory, and recommended raw-source search set
- R1/M1 OpenYield intent and binding: `outputs/openyield_layout_intent/current_supported_config/;docs/mapping/M1_openyield_to_layoutgen_binding.csv;docs/mapping/M1_openyield_net_to_layoutgen_pin_binding.csv`
  reuse_purpose: semantic role map and module/net binding inputs carried into M9 and hardened in M10
- M7 golden reference: `outputs/M7_correct_golden_reference/current_supported_config/golden_reference.gds`
  reuse_purpose: locked physical comparison target and exact-match baseline

## Deprecated Artifacts

- access_module cells: `*_access_module`
  deprecated_reason: cannot be claimed as physical implementation in M10H gate closure
- floorplan_proxy cells: `floorplan_proxy*`
  deprecated_reason: review-only proxy hierarchy, not valid implementation backing for M10H
- historical hybrid reference: `outputs/layout_prototype/hybrid_openyield_rail_overlap/hybrid_openyield_rail_overlap.complete.gds`
  deprecated_reason: superseded by locked uploaded golden reference and M8R/M8RC exact-match flow

## Human Review Conclusion

- m10_clean_gds_user_review_passed: `True`
- m10_source_backed_translator_v2_confirmed: `True`
- can_claim_source_backed_translator_v2: `True`
- can_claim_full_raw_netlist_compiler: `False`
- capacity_config_fallback_used: `True`
- full_raw_openyield_netlist_compiler: `False`
- source_backed_module_count: `20`
- source_backed_net_count: `34`
- source_backed_instance_count: `20`
- reference_vs_m10_geometry_match: `EXACT_MATCH`
- remaining_M10_blockers_before_count: `1`
- remaining_M10_blockers_after_count: `0`
- next_stage_allowed: `M11_OPENYIELD_CONFIG_EXTRACTION_OR_VARIATION_SUPPORT`
- can_enter_next_stage_after_this_gate: `True`
