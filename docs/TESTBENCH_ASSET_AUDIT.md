# Testbench Asset Audit

## Summary

- `OpenYield` does contain real upstream testbench code under `sram_compiler/testbenches/`.
- Those upstream assets are `UPSTREAM_REFERENCE_TB`, not `TRUSTED_PROJECT_TB`, because they target the upstream `sram_compiler` configuration/YAML flow rather than the current project's authoritative top-level netlist binding.
- The current project does have trusted module-level SPICE testbenches under `simulation/spice/testbenches/`, but they only prove module smoke behavior and do not close full SRAM functionality.
- No trusted current-project Verilog/behavioral top-level SRAM testbench was discovered.

## OpenYield Findings

- source_commit: `1c34428d8b913963c4971d093b1a7c2df97a2509`
- real upstream testbench files found:
  - `sram_compiler/testbenches/sram_6t_core_testbench.py`
  - `sram_compiler/testbenches/sram_6t_core_MC_testbench.py`
  - `sram_compiler/testbenches/base_testbench.py`
  - `demo_run_a_testbench.py`
- semantic boundary:
  - `sram_6t_core_testbench.py` and `sram_6t_core_MC_testbench.py` are real upstream testbenches for the OpenYield SRAM compiler flow.
  - `demo_run_a_testbench.py` is a yield-estimation driver with hard-coded external paths and therefore is not promotable to a trusted current-project TB.
  - Python module/topology tests in OpenYield were not auto-promoted to circuit-functional TB.

## Current Project Position

- trusted project TB available now:
  - `simulation/spice/testbenches/*.sp` for module-level SPICE smoke.
- trusted project TB not found:
  - no source-backed Verilog top-level SRAM TB
  - no reviewed current-project functional SRAM read/write TB bound to the authoritative clean-top netlist
- practical simulation hierarchy:
  - module-level SPICE regression: `AVAILABLE`
  - current-project logic/Verilog regression: `BLOCKED_BY_MISSING_TRUSTED_VERILOG_ASSETS`
  - representative SRAM functional simulation: `BLOCKED_BY_MISSING_REVIEWED_TOP_LEVEL_TB_AND_SEMANTICS_BINDING`
