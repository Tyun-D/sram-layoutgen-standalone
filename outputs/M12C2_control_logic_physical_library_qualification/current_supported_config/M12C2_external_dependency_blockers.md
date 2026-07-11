# M12C2 External Dependency Blockers

- M12N2-B02: `OPEN` words_per_row > 1 and arbitrary numeric column mux ratio remain unverified.
- M12N2-B03: `OPEN` tech parameter is not connected to a physical PDK abstraction for layout generation.
- M12N2-B04: `OPEN` No complete DRC/LVS/extraction loop is available for the extracted clean top.
- M12N2-B05: `DEFINED_NOT_IMPLEMENTED` Control-logic physical implementation has been defined but is not implemented.
- M12N2-B07: `OPEN` OpenRAM references are still missing a matched full SPICE/LEF/Verilog/config contract for direct cross-flow equivalence.
- M12C-B08: `SPLIT_INTO_REJECTED_AND_QUALIFIED` Existing OpenYield control-logic candidate GDS files were not all trustworthy reusable cells.
- M12C-B09: `PARTIAL_REMAINING` Pin and rail metadata coverage is incomplete across the full TIME primitive hierarchy.
- M12C-B10: `OPEN` Candidate control region insertion is expected to affect or at least challenge the current top-level bbox contract.
- M12C-B11: `OPEN` OpenRAM control logic remains reference-only and cannot be directly reused as final OpenYield implementation.
- M12C-B12: `OPEN` Several transistor-level primitives and size variants still lack a parameterized physical generator plan.
- M12C-B13: `OPEN` FreePDK45 physical tech rule binding is still not connected to the OpenYield control-logic parameter contract.
- M12C-B14: `OPEN` Legal provenance and qualification boundaries for direct standard-cell-style reuse remain incomplete.
