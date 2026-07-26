# OpenRAM / LayoutGen / OpenYield Comparison

| flow | design_input | parameterization | drc | connectivity_verification | negative_verification | limits |
| --- | --- | --- | --- | --- | --- | --- |
| OpenRAM | classical SRAM compiler spec + bundled macros | mature baseline | reference-only in this repo | not re-proven here | none project-specific | not OpenYield-driven |
| 简化版 layoutgen | locked SRAM spec + write_standalone | explicit 8x64_wpr4, partial variation support | internal DRC clean for M2R | route-touch audits but no external LVS | limited outside Team B | top-level signoff incomplete |
| OpenYield | semantic netlist + config files + module contracts | raw variation space 36, explicit supported examples 3 | Team B 0 markers; top-level mixed | strong on Team B, partial on top-level | Team B module and integration suites strong | project-wide full SRAM signoff not complete |
