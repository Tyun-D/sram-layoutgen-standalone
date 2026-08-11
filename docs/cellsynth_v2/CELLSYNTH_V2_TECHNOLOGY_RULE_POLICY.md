# CellSynth v2 Technology Rule Policy

TechnologyDB is the single normalized source consumed by placement, geometry generation, routing, compaction and fast DRC prediction. External FreePDK45 DRC/LVS remains the oracle.

## Required TechnologyDB Sections
- layers and purposes
- manufacturing grid and units
- width and spacing rules
- enclosure and extension rules
- well and implant rules
- contact and via rules
- routing directions and layer stack
- conditional rules
- transistor legality
- folding legality
- pin-access rules

## Rule Authority
Every value must record source file, source line/section, unit and confidence. Duplicated or conflicting generator constants are forbidden as silent authority. Unknown rules remain `UNKNOWN_RULE` and cannot be used for formal PASS.
