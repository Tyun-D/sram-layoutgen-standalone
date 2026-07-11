# M12N2R M12C Entry Gate

- recommended_next_stage: `M12C_CONTROL_LOGIC_GAP_DEFINITION`
- recommended_next_stage_reason: `The latest OpenYield main source proves that TIME is a real SRAM design subcircuit containing DFFs, gated clocks, delay chains, and enable-generation logic. The control-logic netlist source is therefore locked, while its physical implementation and mapping into the layoutgen/OpenRAM floorplan remain incomplete.`
- next_stage_allowed: `M12C_CONTROL_LOGIC_GAP_DEFINITION`
- can_enter_M12C_after_this_gate: `True`
- human_review_required: `False`
- can_enter_next_stage_before_human_review: `True`
- openyield_control_logic_netlist_source_locked: `True`
- openyield_control_logic_physical_implementation_ready: `False`
- can_claim_control_logic_source_locked: `True`
- can_claim_control_logic_mapping_ready: `False`
- can_claim_control_logic_physical_ready: `False`
- can_claim_custom_netlist_driven_layout_generation: `False`
