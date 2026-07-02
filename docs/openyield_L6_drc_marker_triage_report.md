# OpenYield L6 DRC Marker Triage Report

- drc_marker_total_count: `24687`
- drc_marker_classified_count: `24687`
- drc_marker_unclassified_count: `0`
- drc_marker_classification_coverage: `1.0`
- top_marker_rule: `GRID: vertexes on layer cont not on grid of 0.0025`
- top_root_cause_category: `LAYER_MAP_OR_DRC_DECK_INTERPRETATION`

## Root Cause Matrix

- `LAYER_MAP_OR_DRC_DECK_INTERPRETATION`: count=`12012`, priority=`P1`, modules=`bitcell_array; dummy_array; replica_array; sense_amp; write_driver; wordline_driver; precharge; column_mux`
- `CONTRACT_PIN_GEOMETRY_PLACEHOLDER`: count=`11944`, priority=`P4`, modules=`DFF_ROW; CONTROL_LOGIC; SENSE_ENABLE_PATH; WRITE_ENABLE_PATH; decoder_gate_cells; WORDLINE_ENABLE_PATH; wordline_driver_gate_cells; wordline_decoder`
- `CANDIDATE_GEOMETRY_INTERNAL`: count=`666`, priority=`P3`, modules=`row_decoder`
- `MODULE_INTERNAL_HARDMACRO`: count=`49`, priority=`P3`, modules=`wordline_driver; column_mux`
- `MODULE_WRAPPER_IMPORT`: count=`16`, priority=`P3`, modules=`write_driver; sense_amp`

## Gates

- can_claim_L6_drc_triage_completed_now: `True`
- can_enter_L7_drc_repair_planning: `True`
- can_claim_drc_clean_now: `False`
- can_claim_lvs_clean_now: `False`
- can_claim_timing_closure_now: `False`
- can_claim_validated_full_openyield_gds_now: `False`
