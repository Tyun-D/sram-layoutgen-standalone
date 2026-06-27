# Milestone Summary

## Completed

- Candidate `gen_delay_inv` SPICE template emitted in the main repository.
- ngspice syntax smoke passed on the server using the server-local FreePDK45 nominal include.
- Delay chain transient smoke passed and showed propagation from `rbl` to `rbl_delay`.
- External OpenYield source provenance is now recorded with concrete `DelayChain`, `Pinv`, and `time_generate.py` evidence.

## Current Limits

- Smoke-only `.measure` has not produced a usable delay value yet.
- Candidate SPICE has not been fully regenerated from OpenYield source in an automated reproducible path.
- No timing proof, timing closure, physical timing closure, routing closure, placement closure, or time-control GDS claim is available.
- `standalone.py`, routing, and `gds_writer.py` remain unchanged.

## Current Gates

- `can_reproduce_candidate_spice_from_source=False`
- `can_enter_delay_chain_transient_smoke=True`
- `can_modify_standalone_now=False`
- `can_generate_time_control_gds_now=False`
- `can_claim_openyield_full_integration_now=False`
