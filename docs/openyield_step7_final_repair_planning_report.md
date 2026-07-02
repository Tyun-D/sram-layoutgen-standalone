# Step 7 Final Repair Planning Report

- top_repair_priority: `P1`
- top_repair_root_cause: `LAYER_MAP_OR_DRC_DECK_INTERPRETATION`
- top_repair_marker_count: `12012`
- can_claim_project_v1_closure_ready: `True`
- can_enter_step8_final_report_handoff: `True`

## Repair Plan

- `P1 LAYER_MAP_OR_DRC_DECK_INTERPRETATION`: markers=`12012`, files=`technology/freepdk45/tech/freepdk45.lydrc; technology/freepdk45/gds_lib/*.gds`
- `P4 CONTRACT_PIN_GEOMETRY_PLACEHOLDER`: markers=`11944`, files=`outputs/openyield_module_gds/<module>/pins.json; sram_layoutgen/openyield_adapter/module_gds_generators.py`
- `P3 CANDIDATE_GEOMETRY_INTERNAL`: markers=`666`, files=`sram_layoutgen/openyield_adapter/module_gds_generators.py`
- `P3 MODULE_INTERNAL_HARDMACRO`: markers=`49`, files=`technology/freepdk45/gds_lib/*.gds; outputs/openyield_module_gds/<module>/generator_manifest.json`
- `P3 MODULE_WRAPPER_IMPORT`: markers=`16`, files=`sram_layoutgen/openyield_adapter/gds_hierarchy_export.py; sram_layoutgen/openyield_adapter/top_level_assembly.py`

## Claims Kept False

- can_claim_drc_clean_now: `False`
- can_claim_lvs_clean_now: `False`
- can_claim_timing_closure_now: `False`
- can_claim_validated_full_openyield_gds_now: `False`
- can_claim_signoff_ready_sram_compiler_now: `False`
