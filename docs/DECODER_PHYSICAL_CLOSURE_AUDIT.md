# Decoder Physical Closure Audit

- generated_at: `2026-07-26T22:30:00Z`
- status: `BLOCKED_TECHNICAL`
- stale_blocker_removed: `Team B AND2/AND3 are now formal`, but decoder is still metadata-only at the stage-planning and output-handoff level.

## Specific Blockers

1. `docs/openyield_decoder_preplacement_feasibility_report.json`
   stage rows remain `metadata_only=true` and `not_legal_physical_placement=true`; the report still says `physical_layout_generated=false`.
2. `docs/openyield_decoder_output_contract_report.json`
   every decoder output contract and downstream handoff remains `metadata_only=true` with `physical_routing_proven=false`.
3. `sram_layoutgen/openyield_adapter/module_gds_generators.py`
   `RowBasedCandidateGenerator` only places child references, exports contract pins, and writes `rail_status=candidate_row_rail_metadata_exported`; it explicitly marks decoder GDS as `L3_GDS_GENERATED_CANDIDATE_GEOMETRY` and “does not claim final routing or signoff.”
4. repo verification inventory
   no decoder-specific production gate, negative suite, determinism closure, connectivity/foreign-net harness, or final review-atlas pipeline was found; existing tests stop at L3/L4 sanity/readiness boundaries.

## Decision

Decoder physical closure cannot be honestly claimed in the current repo state. This is not a single-marker or single-test issue. It is blocked by:

- missing legal decoder-stage physical authority
- missing decoder internal-routing / power-stitching generator ownership
- missing decoder production gate / negative regression harness

Continue to treat decoder as blocked until a dedicated decoder generator and validation flow are added.
