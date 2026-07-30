# Simulation Input Gap Report

## Inventory Counts

- EXTRACTED_SPICE: `18`
- TESTBENCH: `16`
- TRANSISTOR_SPICE: `47`
- UNKNOWN: `13`

## Gaps

- Trusted Verilog assets discovered: `0`. Current project worktree does not contain authoritative `.v/.sv` sources for the target control modules, so Icarus/Verilator logic regressions are asset-blocked.
- `docs/candidate_spice/*` exists but is explicitly labeled planning-only and is excluded from formal simulation claims.
- `outputs/M12N2_clean_openyield_sram_top/*` and `outputs/M12N_lock_openyield_authoritative_netlist/*` provide authoritative/generated SPICE sources suitable for limited SPICE regressions.
- `outputs/M7_correct_golden_reference/current_supported_config/extracted/full_layout_collection/*/*.sp` provides extracted SRAM-level SPICE and report collateral, but current repo still lacks a documented extraction-rule provenance chain that would justify new post-layout signoff claims.
