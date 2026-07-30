# Project SRAM TB Binding Decision

- decision: `BLOCKED_BY_SPECIFIC_INTERFACE_GAPS`
- selected_reference: `OpenYield upstream TB source contract`
- current_project_authority: `outputs/M12N2_clean_openyield_sram_top/current_supported_config/openyield_sram_top_v1_16x16.sp`

## Conclusion

- The project now has a project-owned control/timing contract draft, but it still contains unresolved schedule/oracle fields.
- `clk/csb/web` and internal `TIME` outputs are interface-bound; exact project pass/fail timing for SRAM write/read remains unresolved.
- A project-adapted SRAM TB must stay blocked until those unresolved fields are frozen.

## Specific Field Blockers

- `TIME_schedule`: no reviewed project cycle contract for write/read sequencing.
- `write_sample_point`: no project-owned readback oracle timing after write.
- `disabled_hold_semantics`: no reviewed hold-mode oracle for this top.
