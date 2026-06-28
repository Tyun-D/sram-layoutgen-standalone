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

## Current Limits

- All delay metadata remains smoke-only and is not timing proof.
- Candidate SPICE has not been fully regenerated from OpenYield source in an automated reproducible path.
- No timing proof, timing closure, physical timing closure, routing closure, placement closure, or time-control GDS claim is available.
- `standalone.py` now contains explicit opt-in gate-row packing; routing and `gds_writer.py` remain unchanged.
- Gate-row compaction improves placement density, but routing compaction, DRC closure, LVS closure, and full power-rail continuity proof are still pending.

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
