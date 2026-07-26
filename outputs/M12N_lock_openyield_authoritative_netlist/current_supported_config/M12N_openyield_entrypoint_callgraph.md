# M12N OpenYield Entrypoint Callgraph

- main_sram.py: `Sram6TCoreMcTestbench.run_mc_simulation` -> `SPICE testbench netlist (.sp via str(circuit))` (PRIMARY_GENERATOR_WRAPPER_BUT_IMPORT_FAILS)
- equivalent_modeling/main_sram.py: `Sram6TCoreMcTestbench.run_mc_simulation` -> `SPICE testbench netlist + CSV experiment outputs` (EXPERIMENT_WRAPPER)
- demo_run_a_testbench.py: `Sram6TCoreMcTestbench.run_mc_simulation` -> `SPICE testbench netlist for demo simulation` (DEMO_WRAPPER)
- sram_compiler/testbenches/sram_6t_core_testbench.py: `Sram6TCoreTestbench.create_testbench` -> `PySpice Circuit rendered as SPICE testbench netlist` (LOW_LEVEL_GENERATOR_WORKS)
- sram_compiler/testbenches/sram_6t_core_MC_testbench.py: `Sram6TCoreMcTestbench.run_mc_simulation` -> `SPICE testbench netlist + simulator run artifacts` (SIMULATION_DRIVER)
- main_opt.py: `algorithm dispatch in optimization demos` -> `optimization orchestration` (NOT_A_NETLIST_AUTHORITY)
- main_estimation.py: `estimation routines` -> `estimation flow, not top netlist authority` (NOT_A_NETLIST_AUTHORITY)
