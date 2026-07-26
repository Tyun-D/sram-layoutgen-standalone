# OpenYield Generator Reuse Decision

## Can Reuse

- Custom GDS backend and hierarchy export experience: Existing gds_writer.py and gds_hierarchy_export.py already solve project-local serialization and import concerns.
- Module metadata and generator manifest framework: Module inventories, manifests, bbox, pin, and rail metadata are directly useful to the new registry layer.
- Validation report and evidence framework: Existing JSON/MD report patterns and sanity checks can host R3/R4 audits.
- DRC triage framework: Later validation evidence can still reuse the current external DRC marker analysis flow.
- R1 layout intent framework: R1 is the authoritative semantic/physical contract for the new generator front end.

## Can Adapt

- module_gds_generators.py: Reuse registry conventions and standalone metadata, but not as the full SRAM generator.
- top_level_assembly.py import/write utilities: Selected GDS import and output helpers are reusable after removing candidate-only placement assumptions.
- top_level_validation.py sanity logic: Structural checks and report formatting are reusable as generator-stage validation hooks.
- OpenRAM hierarchy_layout primitive API ideas: Primitive routing and pin-export concepts are informative, but implementation remains self-developed.

## Do Not Reuse Or Extend

- old top_level_candidate.gds: Legacy candidate output is evidence only; it is not the new generator substrate.
- old candidate-only placement strategy: The new floorplanner must be array-centric and generator-owned.
- contract-pin-only signoff assumption: R3/R4 need route- and geometry-backed ownership, not only contract edges.
- patching top_level_assembly into full SRAM generator: That path would preserve the wrong abstraction boundary and technical debt.
- OpenRAM OPTS/global-state architecture: The new flow should remain local, explicit, and intent-driven.
- OpenRAM full save() mixed flow: OpenYield should keep backend serialization separate from generator composition logic.
- OpenRAM multi-bank/multi-port complexity at R3: Current supported scope is intentionally single-bank and single-port.
