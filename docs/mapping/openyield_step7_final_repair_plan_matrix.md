# Step 7 Final Repair Plan Matrix

| priority | root_cause_category | marker_count | affected_modules | expected_fix_location |
| --- | --- | --- | --- | --- |
| P1 | LAYER_MAP_OR_DRC_DECK_INTERPRETATION | 12012 | bitcell_array; dummy_array; replica_array; sense_amp; write_driver; wordline_driver; precharge; column_mux | L6/L7 DRC deck and imported source geometry review |
| P4 | CONTRACT_PIN_GEOMETRY_PLACEHOLDER | 11944 | DFF_ROW; CONTROL_LOGIC; SENSE_ENABLE_PATH; WRITE_ENABLE_PATH; decoder_gate_cells; WORDLINE_ENABLE_PATH; wordline_driver_gate_cells; wordline_decoder; PRECHARGE_ENABLE_PATH; GATED_CLOCK_PATH | L3 pin export / L4 boundary pin realization |
| P3 | CANDIDATE_GEOMETRY_INTERNAL | 666 | row_decoder | L3 module generator / candidate geometry |
| P3 | MODULE_INTERNAL_HARDMACRO | 49 | wordline_driver; column_mux | Imported hardmacro or macro-local cleanup |
| P3 | MODULE_WRAPPER_IMPORT | 16 | write_driver; sense_amp | L3/L4 wrapper import path |
