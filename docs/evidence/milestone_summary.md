# Milestone Summary

## Completed

- Candidate `gen_delay_inv` SPICE template emitted in the main repository.
- ngspice syntax smoke passed on the server using the server-local FreePDK45 nominal include.
- Delay chain transient smoke passed and showed propagation from `rbl` to `rbl_delay`.
- External OpenYield source provenance is now recorded with concrete `DelayChain`, `Pinv`, and `time_generate.py` evidence.
- Measurement refinement passed and produced smoke-only delays through both ngspice `.measure` and Python postprocess fallback.
- PVT corner smoke passed for `nom`, `ff`, and `ss` at `VDD=1.0V`, `TEMP=25C`, with the expected delay ordering `ff < nom < ss`.
- Timing metadata summary now records the smoke-only delay chain evidence for downstream review.
- OpenYield source linking, control timing mapping, and source-linked timing metadata audit are now generated, with the next gate set to `metadata_consumer_adapter` and all physical-integration claims still blocked.
- Metadata consumer adapter is now implemented, DELAY_CHAIN timing metadata is consumable through the adapter API, blocked control paths remain blocked/source-identifed-only, and the next gate is `control_path_candidate_generation` or `guarded_adapter_integration`.
- Control path candidate generation wave1 is complete: source-linked contracts exist for `PRECHARGE`, `PRECHARGE_ENABLE_PATH`, `SENSE_ENABLE_PATH`, `WRITE_ENABLE_PATH`, `WORDLINE_ENABLE_PATH`, `GATED_CLOCK_PATH`, and `DFF_ROW`; `PRECHARGE` has a candidate SPICE skeleton and `PRECHARGE_ENABLE_PATH` has a testbench skeleton; next gate is `selected_control_path_spice_smoke` or `guarded_adapter_registry`.
- PRECHARGE ngspice smoke is now complete: the source-linked candidate subckt and transient smoke deck both ran, BL/BLB behavior was checked against active-low ENB inference, and PRECHARGE moved to `source_linked_candidate_spice_smoke_available` while remaining not physical-ready.
- Hybrid OpenYield physical compaction is now available as an explicit opt-in: decoder/control gate cells can be packed into abutted rows with rail-alignment audit artifacts, while routing and `gds_writer.py` remain unchanged.
- Hybrid OpenYield vertical gate-row abutment is now available as an explicit opt-in: decoder/control gate rows can use zero-gap alternating `R0/MX` packing without inserted inter-row power stripes, while routing and `gds_writer.py` remain unchanged.
- An evidence-backed `OpenYield netlist-to-GDS readiness` matrix is now generated: 25 modules/capabilities are classified across source link, physical cell presence, pin mapping, placement, rail, routing, timing, DRC/LVS, and current hybrid integration status.
- An evidence-backed L0 `OpenYield module semantics closure` report is now generated: 25 semantic objects, 20 parameter rows, 25 connection rows, 7 config-variation rows, and 21 OpenYield-to-layoutgen mapping rows are captured in CSV/Markdown/JSON artifacts.

## Current Limits

- All delay metadata remains smoke-only and is not timing proof.
- Candidate SPICE has not been fully regenerated from OpenYield source in an automated reproducible path.
- No timing proof, timing closure, physical timing closure, routing closure, placement closure, or time-control GDS claim is available.
- `standalone.py` now contains explicit opt-in gate-row packing; routing and `gds_writer.py` remain unchanged.
- Gate-row compaction improves placement density, but routing compaction, DRC closure, LVS closure, and full power-rail continuity proof are still pending.
- Vertical gate-row abutment now removes artificial inter-row stripes, but it is still not a claim of full rail signoff, DRC closure, or LVS closure.
- `DELAY_CHAIN` is still metadata-consumable only, while `PRECHARGE`, `PRECHARGE_ENABLE_PATH`, `SENSE_ENABLE_PATH`, `WRITE_ENABLE_PATH`, `WORDLINE_ENABLE_PATH`, `GATED_CLOCK_PATH`, and `DFF_ROW` remain candidate-contract-only rather than physical-ready.
- The largest full-OpenYield-GDS blocker cluster is now explicit: decoder/gate-row physical closure, TIME/DFF/control physical integration, rail continuity, and legacy routing replacement.
- The largest L0-to-L1 blocker is now explicit: OpenYield exposes `num_rows`/`num_cols` semantics cleanly, but not first-class `word_size`/`num_words`/`words_per_row`/bank/port semantics, and `TIME` still needs a stable decomposition contract.

## Current Gates

- `can_reproduce_candidate_spice_from_source=False`
- `can_enter_delay_chain_transient_smoke=True`
- `can_enter_timing_metadata_update=True`
- `can_enter_openyield_source_provenance_linking=True`
- `can_enter_control_timing_mapping_review=True`
- `can_enter_metadata_consumer_adapter=True`
- `can_enter_control_path_candidate_generation=True`
- `can_enter_guarded_adapter_integration=True`
- `can_enter_selected_control_path_spice_smoke=True`
- `can_enter_guarded_adapter_registry=True`
- `can_enter_precharge_enable_path_smoke=True`
- `can_enter_next_control_path_spice_smoke=True`
- `can_modify_standalone_now=False`
- `can_generate_time_control_gds_now=False`
- `can_claim_openyield_full_integration_now=False`
- OpenYield layout prototype generation is now reproducible in guarded legacy/hybrid modes; full physical gap closure is still pending.
- `can_enter_routing_compaction=True`
- `can_enter_power_rail_stitching_verification=True`
- `netlist_to_gds_readiness_matrix_available=True`
- `can_enter_decoder_gate_row_abutment=True`
- `can_enter_delay_chain_physical_gap_closure=True`
- `can_enter_precharge_physical_gap_closure=True`
- `l0_module_semantics_matrix_available=True`
- `can_enter_unrestricted_l1_physical_primitive_closure=False`
- OpenYield L0 semantic contract gaps are now closed for the supported scope: a canonical SRAM semantic contract, logical-to-OpenYield mapping, top/bank contract, TIME decomposition contract, control-path contracts, and decoder-wordline handoff contract are all generated, and L1 physical primitive closure can now begin without claiming physical completion.
- OpenYield L0 semantic contract gaps are now closed for the supported scope: a canonical SRAM semantic contract, logical-to-OpenYield mapping, top/bank contract, TIME decomposition contract, control-path contracts, and decoder-wordline handoff contract are all generated, and L1 physical primitive closure can now begin without claiming physical completion.

- L1 first pass: primitive inventory frozen; L2 gate depends on remaining physical-source blockers.

- L1 first pass: primitive inventory frozen; L2 gate depends on remaining physical-source blockers.

- L1 first pass: primitive inventory frozen; L2 gate depends on remaining physical-source blockers.

- L1 gap closure: required primitive physical sources are closed; flow may enter L2 placement/abutment/rail-rule closure.

- L2 first round: placement, abutment, rail, orientation, pin-access, and module-handoff rules are now frozen in machine-readable matrices plus an L2 rule-library JSON; `bitcell_array`, `dummy_array`, `replica_array`, `row_decoder`, `wordline_decoder`, `decoder_gate_cells`, `wordline_driver`, `wordline_driver_gate_cells`, `column_mux`, `sense_amp`, `write_driver`, `precharge`, `DELAY_CHAIN`, `PRECHARGE_ENABLE_PATH`, `SENSE_ENABLE_PATH`, `WRITE_ENABLE_PATH`, `WORDLINE_ENABLE_PATH`, `GATED_CLOCK_PATH`, `DFF_ROW`, and `CONTROL_LOGIC` can now enter L3 standalone module GDS generation.
- L3 first round: standalone module generators are now implemented for all 20 L3 targets, each target now has a reproducible standalone GDS plus `pins.json`/`bbox.json`/`rail_report.json`/`generation_report`/`generator_manifest`, and the flow can now enter L4 top-level assembly while still keeping all full-GDS/DRC/LVS/timing claims false.
- `can_claim_L2_placement_abutment_rules_closed_now=True`
- `can_enter_L3_module_gds_generation=True`
- `can_claim_L3_module_generators_closed_now=True`
- `can_claim_L3_standalone_module_gds_closed_now=True`
- `can_enter_L4_top_level_assembly=True`
- `can_claim_full_openyield_gds_now=False`
- `can_claim_drc_clean_now=False`
- `can_claim_lvs_clean_now=False`
- `can_claim_timing_closure_now=False`
- L4 first round: a reproducible Python top-level assembly generator now instantiates all 20 required L3 modules into a single-bank SRAM candidate GDS and emits floorplan/pin-map/rail-stitch/routing-handoff metadata, while still keeping validated full-GDS, DRC, LVS, and timing-closure claims false.
- `can_claim_L4_top_level_candidate_gds_generated_now=True`
- `can_enter_L5_validation=False`
- L4 first round: a reproducible Python top-level assembly generator now instantiates all 20 required L3 modules into a single-bank SRAM candidate GDS and emits floorplan/pin-map/rail-stitch/routing-handoff metadata, while still keeping validated full-GDS, DRC, LVS, and timing-closure claims false.
- `can_claim_L4_top_level_candidate_gds_generated_now=True`
- `can_enter_L5_validation=True`
- L5 first round: top-level candidate GDS validation artifacts are now generated across sanity, completeness, placement, pins, rail, routing, risk, DRC smoke, LVS feasibility, and timing metadata; `can_claim_L5_basic_validation_passed_now=False` while `can_claim_validated_full_openyield_gds_now=False`, `can_claim_drc_clean_now=False`, `can_claim_lvs_clean_now=False`, and `can_claim_timing_closure_now=False`.
- L5 first round: top-level candidate GDS validation artifacts are now generated across sanity, completeness, placement, pins, rail, routing, risk, DRC smoke, LVS feasibility, and timing metadata; `can_claim_L5_basic_validation_passed_now=False` while `can_claim_validated_full_openyield_gds_now=False`, `can_claim_drc_clean_now=False`, `can_claim_lvs_clean_now=False`, and `can_claim_timing_closure_now=False`.
- L5 first round: top-level candidate GDS validation artifacts are now generated across sanity, completeness, placement, pins, rail, routing, risk, DRC smoke, LVS feasibility, and timing metadata; `can_claim_L5_basic_validation_passed_now=True` while `can_claim_validated_full_openyield_gds_now=False`, `can_claim_drc_clean_now=False`, `can_claim_lvs_clean_now=False`, and `can_claim_timing_closure_now=False`.
- L5 first round: top-level candidate GDS validation artifacts are now generated across sanity, completeness, placement, pins, rail, routing, risk, DRC smoke, LVS feasibility, and timing metadata; `can_claim_L5_basic_validation_passed_now=True` while `can_claim_validated_full_openyield_gds_now=False`, `can_claim_drc_clean_now=False`, `can_claim_lvs_clean_now=False`, and `can_claim_timing_closure_now=False`.
- L5 hierarchy repair: the only first-round basic-validation blocker (`top_gds_sanity`) was traced to incomplete hierarchy export plus wrapper/source cell-name collisions in the integrated top-level GDS. L4 assembly now imports complete module hierarchies with module-prefixed cell namespaces and redirect handling for self-reference collisions; the regenerated top-level GDS parses cleanly, `remaining_L5_basic_validation_blockers_count=0`, and `can_claim_L5_basic_validation_passed_now=True` while `can_claim_validated_full_openyield_gds_now=False`, `can_claim_drc_clean_now=False`, `can_claim_lvs_clean_now=False`, and `can_claim_timing_closure_now=False`.
- L5 module-completeness normalization: prefixed top-level direct references such as `CONTROL_LOGIC__CONTROL_LOGIC` and `bitcell_array__bitcell_array` are now normalized back to required module names during completeness validation, all 20 required modules are recognized, and `module_completeness_status=PASSED` without changing the still-false DRC/LVS/timing/full-GDS claims.
- L5 first round: top-level candidate GDS validation artifacts are now generated across sanity, completeness, placement, pins, rail, routing, risk, DRC smoke, LVS feasibility, and timing metadata; `can_claim_L5_basic_validation_passed_now=True` while `can_claim_validated_full_openyield_gds_now=False`, `can_claim_drc_clean_now=False`, `can_claim_lvs_clean_now=False`, and `can_claim_timing_closure_now=False`.
- L6 first round: integrated KLayout DRC markers are now extracted, summarized, spatially clustered, mapped onto modules/boundaries, classified into root-cause families, and prioritized for L7 repair planning; `can_claim_L6_drc_triage_completed_now=True` while `can_claim_drc_clean_now=False`, `can_claim_lvs_clean_now=False`, `can_claim_timing_closure_now=False`, and `can_claim_validated_full_openyield_gds_now=False`.
- Step 7 closure planning: the OpenYield-driven SRAM top-level candidate GDS v1.0 deliverable is now bounded by explicit capability claims, limitation statements, finite repair priorities, and a Step 8-ready handoff checklist; `can_claim_project_v1_closure_ready=True` while all DRC/LVS/timing/full-GDS/signoff claims remain false.
