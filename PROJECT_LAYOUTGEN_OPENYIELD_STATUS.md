# OpenYield SRAM LayoutGen Project Status

## 1. Current Correct Goal

继续以用户锁定的 uploaded golden reference 作为唯一物理目标，并以已确认通过人工 KLayout review 的可复现 layoutgen golden flow 作为后续 M9 OpenYield netlist-to-layout translator 的唯一物理基线。

## 2. Current Stage

- current_stage: `M8RC`
- next_stage: `M9_OPENYIELD_NETLIST_TO_LAYOUT_TRANSLATOR`
- human_klayout_review_required_every_stage: `True`
- can_enter_next_stage_without_human_review: `True`

## 3. M8RC Confirmation

- m8r_reproduced_fixed_clean_review_passed: `True`
- m8r_fixed_gds_vs_golden_reference: `EXACT_MATCH`
- current_reproducible_layoutgen_golden_flow_locked: `True`
- can_use_this_flow_for_next_netlist_translator: `True`
- next_stage_allowed: `M9_OPENYIELD_NETLIST_TO_LAYOUT_TRANSLATOR`

## 4. Locked Reproducible Golden Flow

- fixed_reproduced_gds_path: `outputs/M8R_fix_golden_geometry_delta/current_supported_config/m8r_reproduced_fixed.gds`
- fixed_clean_review_gds_path: `outputs/M8R_fix_golden_geometry_delta/current_supported_config/m8r_reproduced_fixed_clean_review.gds`
- reference_vs_m8r_geometry_match: `EXACT_MATCH`
- can_use_this_flow_for_next_netlist_translator: `True`
- can_enter_M9_after_this_gate: `True`
