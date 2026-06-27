# Evidence Timeline

- `2026-06-28`: Generated OpenYield candidate delay chain SPICE templates in the main repository evidence flow.
- `2026-06-28`: Completed candidate SPICE syntax binding checks and server ngspice syntax smoke.
- `2026-06-28`: Completed delay chain ngspice transient smoke from commit `fc85009cd68cacd4c682ec2cdadb576a2583bdb3`; `rbl_delay` response observed, but smoke-only `.measure` remained unsuccessful.
- `2026-06-28`: Cloned external OpenYield source from `https://github.com/ShenShan123/OpenYield.git` into `/data1/qujh/work/external/OpenYield` and recorded source provenance without vendoring the source into the main repository.
- `2026-06-28`: Started delay-chain measurement refinement to correct ngspice `.measure` handling and add Python waveform postprocess fallback.
