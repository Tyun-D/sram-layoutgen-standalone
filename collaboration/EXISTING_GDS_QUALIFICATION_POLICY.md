# Existing GDS Qualification Policy

No module may be redrawn or reused only because a matching name exists in history or on disk.

## Mandatory Steps Before Any Module Stage

1. Search `technology/freepdk45/gds_lib`.
2. Search `outputs/`.
3. Search Git history for prior candidate, quarantine, review-only, and release artifacts.
4. Read top cell, labels, references, and bbox from every candidate.
5. Compare the candidate against the locked OpenYield source topology and the approved child-binding closure.
6. Assign exactly one status:

- `APPROVED_SOURCE_EXACT_REUSE`
- `QUALIFICATION_REQUIRED`
- `LEGACY_BLACKBOX_REFERENCE_ONLY`
- `INCOMPATIBLE_REGENERATION_REQUIRED`
- `SOURCE_BINDING_UNRESOLVED`

## Interpretation Rules

- Legacy GDS is never auto-classified as source-exact.
- Review-only atlases, access views, wrappers, and quarantine artifacts are not reusable composition sources.
- Approved reusable GDS already frozen for `PINV`, `TRANSMISSION_GATE`, `DFF`, and `DFF_BUF` stays Owner-A controlled and read-only to Team B.
- `technology/freepdk45/gds_lib/` is inventory-only for Team B. No edits are allowed.

## Current Team-B Starting Observations

- `PNAND2`, `PNAND3`, `AND2`, `AND3`, `pdrive`, `pdrive2_for_pre`, `wl_pdrive`, `wen_delay_chain`, and `TIME` have no approved module-level source-exact GDS in the current baseline.
- `delay_chain` has candidate and legacy-like artifacts in `outputs/`, but they remain `QUALIFICATION_REQUIRED` until source/binding closure and evidence review explicitly approve reuse.
