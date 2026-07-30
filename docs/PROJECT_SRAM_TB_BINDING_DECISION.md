# Project SRAM TB Binding Decision

- decision: `BLOCKED_BY_SPECIFIC_INTERFACE_GAPS`
- selected_reference: `OpenYield upstream TB source contract`
- current_project_authority: `outputs/M12N2_clean_openyield_sram_top/current_supported_config/openyield_sram_top_v1_16x16.sp`

## Conclusion

- The project can trust the upstream TB as a reference contract, not as a drop-in project TB.
- The current clean-top SPICE proves that many subcircuits exist, including `TIME` and `OPENYIELD_SRAM_TOP_V1`.
- However, the reviewed project evidence still lacks a project-owned top-level functional TB that freezes `clk/csb/web/PRE/TIME` scheduling and pass/fail sampling semantics.

## Specific Gaps

- No reviewed project contract yet defines exact `clk` to `csb/web` sequencing for `write 0/read 0`, `write 1/read 1`, or hold.
- The authoritative core-array subckt `SRAM_6T_CORE_16x16` does not itself expose the control/data/observe pins needed for full SRAM functional proof.
- Treating the upstream Python harness as formal project evidence would over-claim authority and reproducibility.

## Decision

- Do not promote the upstream files to `TRUSTED_PROJECT_TB`.
- Do not fabricate a new project SRAM TB until the missing control/TIME fields are frozen as project evidence.
- Keep module-level SPICE closure active, and keep representative SRAM functional simulation explicitly blocked at field level.
