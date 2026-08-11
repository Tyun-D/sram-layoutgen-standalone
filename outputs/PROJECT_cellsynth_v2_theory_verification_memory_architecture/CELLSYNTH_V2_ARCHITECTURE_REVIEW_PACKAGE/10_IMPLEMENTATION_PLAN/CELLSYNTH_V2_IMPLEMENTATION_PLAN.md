# CellSynth v2 Implementation Plan

1. Implement `TechnologyDB` loader and remove duplicated rule constants from DFF CellGen code paths.
2. Implement `GoldenSpec` and generated-cell LVS wrapper naming.
3. Implement Level-1 connectivity extraction that explicitly requires vias for layer transitions.
4. Promote symbolic state classes for MOS, trail, OD contour, contact access, pin access and routing topology.
5. Implement lower-bound pruning and canonical-state hashing before generating polygons.
6. Implement layered routing graph and constraint compaction.
7. Wire DRC/LVS counterexamples into candidate repair and cost updates.
8. Add optional PEX and Level-4 characterization only for DRC/LVS-clean top-K candidates.
9. Resume area/PPA optimization only after all architecture gates pass.
