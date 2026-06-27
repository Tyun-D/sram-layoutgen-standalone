# Evidence Timeline

- `2026-06-28`: Generated OpenYield candidate delay chain SPICE templates in the main repository evidence flow.
- `2026-06-28`: Completed candidate SPICE syntax binding checks and server ngspice syntax smoke.
- `2026-06-28`: Completed delay chain ngspice transient smoke from commit `fc85009cd68cacd4c682ec2cdadb576a2583bdb3`; `rbl_delay` response observed, but smoke-only `.measure` remained unsuccessful.
- `2026-06-28`: Cloned external OpenYield source from `https://github.com/ShenShan123/OpenYield.git` into `/data1/qujh/work/external/OpenYield` and recorded source provenance without vendoring the source into the main repository.
- `2026-06-28`: Completed delay-chain measurement refinement; rise-to-fall = `1.963452e-10 s`, fall-to-rise = `1.876240e-10 s`, commit = `4eeeee106db316f4d09322c02c4152c28acf5d77`.
- `2026-06-28`: Milestone: delay-chain PVT corner smoke. Result: nom/ff/ss model corners found; nom/ff/ss ngspice transient runs passed; smoke-only delay values extracted; worst smoke delay = `2.157380e-10 s` at `ss`; trend `ff < nom < ss`; `can_enter_timing_metadata_update=True`; still cannot claim delay proof or timing closure. Commit: `fbf2827a9f87234878c0d0c78dd5390a76d344b4`.
- `2026-06-28`: Recorded delay-chain timing metadata summary from smoke-only PVT evidence for downstream provenance linking and control timing mapping review.
