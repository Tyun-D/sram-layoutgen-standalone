# M12O OpenRAM OpenYield Gap Audit Report

- reused_previous_artifacts: `M11V verification report, M11D/M11C/M11C2/M11W prior substitution evidence, M11AR correction report, M12 ten-asset audit`
- deprecated_previous_artifacts: `direct immediate M11V2 continuation as the only next route`
- current_stage_inputs: `OpenRAM full reference scan + OpenYield code/config audit + layoutgen golden reference`
- current_stage_delta_from_M11V: `verification-only focus is replaced by reference-authority and parameterization gap closure.`
- why_M12O_replaces_direct_M11V2_for_now: `netlist authority and control-logic alignment block more downstream work than deeper isolated connectivity alone.`
- openram_reference_gds_path: `/data1/qujh/work/sram_layoutgen_step45_clean/external_references/openram_full_reference/E:\njust\keyan\SRAM Compiler_V2\fromSSH\sram_1rw_32x16_freepdk45.gds`
- openyield_authoritative_netlist_candidates: `['sram_compiler/subcircuits/base_subcircuit.py', 'sram_compiler/subcircuits/decoder.py', 'sram_compiler/subcircuits/dummy_row_or_column.py', 'sram_compiler/subcircuits/mux_and_sa.py', 'sram_compiler/subcircuits/precharge_and_write_driver.py', 'sram_compiler/subcircuits/replica_column.py', 'sram_compiler/subcircuits/sram_10t_core.py', 'sram_compiler/subcircuits/sram_6t_core.py', 'sram_compiler/subcircuits/sram_cell_add_equivalent.py', 'sram_compiler/subcircuits/standard_cell.py', 'sram_compiler/subcircuits/time_generate.py', 'sram_compiler/subcircuits/wordline_driver.py', 'sram_compiler/testbenches/sram_6t_core_MC_testbench.py', 'sram_compiler/testbenches/sram_6t_core_testbench.py']`
- control_logic_gap_status: `OPENRAM_PRESENT_LAYOUTGEN_MISSING_OPENYIELD_PHYSICAL_UNQUALIFIED`
- recommended_next_stage: `M12N_LOCK_OPENYIELD_AUTHORITATIVE_NETLIST`
- recommended_next_stage_reason: `M12O finds a usable OpenRAM full-reference GDS and a rich OpenYield parameter/config codebase, but it does not prove a single authoritative OpenYield complete SRAM top netlist. Locking that authority is a harder blocker than directly continuing M11V2 connectivity deepening, because control-logic alignment, parameterized SRAM planning, and later combined substitution all still depend on one unambiguous netlist source of truth.`
