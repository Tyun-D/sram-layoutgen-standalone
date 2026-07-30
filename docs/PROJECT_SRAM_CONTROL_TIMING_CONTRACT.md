# Project SRAM Control Timing Contract

- classification: `PROJECT_ADAPTATION_CONTRACT`
- dut_subckt: `OPENYIELD_SRAM_TOP_V1`
- time_subckt: `TIME`

## Field Status

- `clk`: `CURRENT_TOP_INTERFACE` from `openyield_sram_top_v1_16x16.sp .subckt OPENYIELD_SRAM_TOP_V1`
- `csb`: `UPSTREAM_EXACT` from `sram_6t_core_testbench.py create_time_circuit + OPENYIELD_SRAM_TOP_V1`
- `web`: `UPSTREAM_EXACT` from `sram_6t_core_testbench.py create_time_circuit + OPENYIELD_SRAM_TOP_V1`
- `wl_en`: `CURRENT_TOP_INTERFACE` from `TIME subckt pin list`
- `s_en`: `CURRENT_TOP_INTERFACE` from `TIME subckt pin list`
- `w_en`: `CURRENT_TOP_INTERFACE` from `TIME subckt pin list`
- `PRE`: `CURRENT_TOP_INTERFACE` from `TIME subckt pin list`
- `TIME_schedule`: `UNRESOLVED` from `no project-owned frozen write/read schedule`
- `read_sample_point`: `UPSTREAM_EXACT` from `sram_6t_core_testbench.py read measurements on WL/BL/SA_Q`
- `write_sample_point`: `UNRESOLVED` from `project has no reviewed readback oracle sequence yet`
- `disabled_hold_semantics`: `UNRESOLVED` from `project lacks reviewed top-level hold oracle`

## Decision

- Project-adapted SRAM functional TB remains blocked until unresolved scheduling/oracle fields are frozen as reviewed project evidence.
