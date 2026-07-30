# Power Routing Correctness Method

- evidence_basis: `raw-source-backed generated SRAM report.json artifacts`, not handwritten power claims
- covered_configs: `sram_16x16_wpr1_fd45`, `sram_4x32_wpr1_fd45`, `sram_8x64_wpr4_fd45`
- validator_scope: `row_side_power_audit`, `array_power_stitching_audit`, `global_power_consistency_audit`, `power_junction_topology_audit`, `drc_clean`

## Positive Checks

- all child VDD endpoints connect with `missing_vdd_pins = 0`
- all child VSS endpoints connect with `missing_gnd_pins = 0`
- array and peripheral VDD resolve to one top-level VDD component
- array and peripheral VSS resolve to one top-level VSS component
- VDD/VSS short freedom is proven by `vdd_gnd_short_free = true`
- per-row VDD/VSS straps are fully connected to expected row counts
- top-ring VDD/VSS connections are present
- source reports are DRC-clean for these configurations

## Limits

- Current negative regression rows are blocked because no raw-GDS geometry mutation harness was found in this worktree.
- These results do not prove IR drop, EM, voltage droop, or dynamic power signoff.
