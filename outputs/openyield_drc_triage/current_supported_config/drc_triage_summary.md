# OpenYield L6 DRC Marker Triage Summary

- drc_marker_total_count: `24687`
- drc_marker_classified_count: `24687`
- drc_marker_unclassified_count: `0`
- drc_marker_classification_coverage: `1.0`
- top_marker_rule: `GRID: vertexes on layer cont not on grid of 0.0025`
- top_marker_rule_count: `6495`
- top_root_cause_category: `LAYER_MAP_OR_DRC_DECK_INTERPRETATION`
- top_root_cause_marker_count: `12012`

## Top Rules

- `GRID: vertexes on layer cont not on grid of 0.0025`: `6495`
- `GRID: vertexes on layer metal1 not on grid of 0.0025`: `6347`
- `GRID: vertexes on layer poly not on grid of 0.0025`: `2791`
- `GRID: vertexes on layer active not on grid of 0.0025`: `2436`
- `GRID: vertexes on layer nplus not on grid of 0.0025`: `1351`
- `GRID: vertexes on layer via1 not on grid of 0.0025`: `1274`
- `GRID: vertexes on layer metal2 not on grid of 0.0025`: `1258`
- `GRID: vertexes on layer pplus not on grid of 0.0025`: `1076`
- `GRID: vertexes on layer vtg not on grid of 0.0025`: `460`
- `CONTACT.1`: `354`

## Root Causes

- `LAYER_MAP_OR_DRC_DECK_INTERPRETATION`: `12012` markers, modules=`bitcell_array, dummy_array, replica_array, sense_amp, write_driver`
- `CONTRACT_PIN_GEOMETRY_PLACEHOLDER`: `11944` markers, modules=`DFF_ROW, CONTROL_LOGIC, SENSE_ENABLE_PATH, WRITE_ENABLE_PATH, decoder_gate_cells`
- `CANDIDATE_GEOMETRY_INTERNAL`: `666` markers, modules=`row_decoder`
- `MODULE_INTERNAL_HARDMACRO`: `49` markers, modules=`wordline_driver, column_mux`
- `MODULE_WRAPPER_IMPORT`: `16` markers, modules=`write_driver, sense_amp`

## Gates

- can_claim_L6_drc_triage_completed_now: `True`
- can_enter_L7_drc_repair_planning: `True`
- can_claim_drc_clean_now: `False`
- can_claim_lvs_clean_now: `False`
- can_claim_timing_closure_now: `False`
- can_claim_validated_full_openyield_gds_now: `False`
