# AutoCellGen Implementation Audit

AutoCellGen was inspected as an implementation reference only. No source code or PDK data was copied into CellSynth.

## Findings
- `cdlParser` implements netlist parsing concepts: `CONCEPT_ADAPT`.
- `Pairing` and placement classes represent PMOS/NMOS pair/group concepts: `CONCEPT_ADAPT`.
- `PlaceGrid`, `PlaceUnit`, `PlaceGroupUnit`, `Placer`, and `GroupPlacer` demonstrate column/group placement decomposition: `CONCEPT_ADAPT`.
- `RouteGrid`, `Router`, and `RoutingResult` demonstrate an explicit routing-resource model and in-cell routing flow: `CONCEPT_ADAPT`.
- `beol_data` and GDS output flow show separation of BEOL/routing/GDS generation: `CONCEPT_ADAPT`.
- ASAP7 input netlists, placement datasets, generated cells, and process assumptions: `CONCEPT_REJECT` for FreePDK45 formal candidates.
- Z3 integration concept: `CONCEPT_ADOPT`; exact versioning and code reuse require `LICENSE_REVIEW_REQUIRED`.
- README warning that generated cells may have DRC violations means AutoCellGen is not a correctness oracle: `CONCEPT_REJECT` as verification authority.

## License Boundary
The repository license must be reviewed before any code reuse. This stage uses it only to guide architecture decomposition.
