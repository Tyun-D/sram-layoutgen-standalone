# M12N Lock OpenYield Authoritative Netlist Report

- reused_previous_artifacts: `M12O authority inventory and gap matrix, OpenYield YAML configs, OpenYield subcircuit/testbench code`
- deprecated_previous_artifacts: `treating every M12O candidate file as a complete SRAM top authority`
- current_stage_inputs: `OpenYield candidate files + entrypoints + YAML config stack`
- current_stage_delta_from_M12O: `M12N turns a broad gap audit into a concrete authority-source lock decision.`
- why_M12N_is_required_before_custom_netlist_driven_layout: `custom layout cannot safely proceed until one netlist or generator chain is chosen as authority.`
- authoritative_netlist_lock_status: `PARTIAL_SUBCIRCUIT_LIBRARY_ONLY`
- authoritative_entrypoint: `sram_compiler/testbenches/sram_6t_core_testbench.py`
- authoritative_top_class_or_function: `Sram6TCoreTestbench.create_testbench`
- sample_netlist_generation_passed: `True`
- recommended_next_stage: `M12C_CONTROL_LOGIC_GAP_DEFINITION`
- recommended_next_stage_reason: `M12N proves that OpenYield contains a parameterized Python SPICE/testbench generator chain centered on `Sram6TCoreTestbench.create_testbench`, and it can emit a sample SRAM-related netlist. However, that emitted artifact is still a simulation testbench netlist with supplies, stimuli, and measurement scaffolding rather than a locked pure SRAM top authority. The next blocking step is to define how the traced OpenYield control logic and enable paths map onto the OpenRAM/layoutgen control-logic gap before any custom netlist-driven layout flow can be claimed.`
