# Milestone Summary

## Completed

- Candidate `gen_delay_inv` SPICE template emitted in the main repository.
- ngspice syntax smoke passed on the server using the server-local FreePDK45 nominal include.
- Delay chain transient smoke passed and showed propagation from `rbl` to `rbl_delay`.
- External OpenYield source provenance is now recorded with concrete `DelayChain`, `Pinv`, and `time_generate.py` evidence.
- Measurement refinement passed and produced smoke-only delays through both ngspice `.measure` and Python postprocess fallback.
- PVT corner smoke passed for `nom`, `ff`, and `ss` at `VDD=1.0V`, `TEMP=25C`, with the expected delay ordering `ff < nom < ss`.

## Current Limits

- PVT results remain smoke-only and are not timing proof.
- Candidate SPICE has not been fully regenerated from OpenYield source in an automated reproducible path.
- No timing proof, timing closure, physical timing closure, routing closure, placement closure, or time-control GDS claim is available.
- `standalone.py`, routing, and `gds_writer.py` remain unchanged.

## Current Gates

- `can_reproduce_candidate_spice_from_source=False`
- `can_enter_delay_chain_transient_smoke=True`
- `can_enter_timing_metadata_update=True`
- `can_modify_standalone_now=False`
- `can_generate_time_control_gds_now=False`
- `can_claim_openyield_full_integration_now=False`
