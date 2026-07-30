# Simulation Capability Audit

- logic_level_1_status: `BLOCKED_BY_MISSING_TRUSTED_VERILOG_ASSETS`
- sram_function_level_2_status: `BLOCKED_BY_MISSING_REVIEWED_FUNCTIONAL_TESTBENCH_BINDING`
- spice_level_3_status: `ADVANCED_WITH_REAL_SERVER_EVIDENCE`
- spice_primary: `ngspice`
- spice_secondary_candidate: `Xyce`
- post_layout_status: `NOT_AVAILABLE_WITH_CURRENT_EVIDENCE`

## Notes

- Current SPICE regressions are grounded on `outputs/M12N2_clean_openyield_sram_top/current_supported_config/openyield_sram_top_v1_16x16.sp`.
- `docs/candidate_spice/*` was not used for formal pass/fail evidence.
- Current logic-level closure is blocked by missing trusted Verilog assets, not by simulator availability.
- OpenYield upstream testbench assets were audited in `docs/TESTBENCH_ASSET_AUDIT.*`, but they are not yet trusted current-project SRAM functional TB bindings.
- `delay_chain` root cause is documented and does not currently justify formal circuit/GDS modification.
