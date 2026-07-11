# M12N2 Clean OpenYield SRAM Top Report

- reused_previous_artifacts: `M12N authority report, matrices, sample testbench netlist, project ledgers, OpenYield generator sources`
- deprecated_previous_artifacts: `treating the M12N sample testbench netlist as the final clean SRAM top; treating target-column D_LATCH as the macro output contract`
- current_stage_inputs: `project ledgers + M12N artifacts + OpenYield source + sample testbench netlist`
- current_stage_delta_from_M12N: `clean-top extraction, graph export, and V1 parameter contract lock`
- why_M12N2_precedes_M12C: `control-logic gap closure needs a clean layout-facing SRAM top boundary first`
- clean_top_extraction_passed: `True`
- parameter_contract_v1_locked: `True`
- sample_16x16_generated: `True`
- sample_64x8_generated: `True`
- parameter_scaling_verified: `True`
- time_control_role_status: `AMBIGUOUS_REQUIRES_TEAM_CONFIRMATION`
- recommended_next_stage: `M12N2H_REQUEST_TIME_ROLE_CONFIRMATION`
