# OpenYield SRAM LayoutGen Project Status

## 1. Current Correct Goal

M12N 已完成 OpenYield authoritative SRAM netlist / netlist-generator source 锁定审计。当前已确认 OpenYield 存在可参数化的 Python SPICE/testbench generator 链，但尚未证明一个纯净、单文件或单入口的 authoritative SRAM top netlist 可直接作为 custom netlist-driven layout authority。

## 2. Current Stage

- current_stage: `M12C3`
- next_stage: `M12C3A_IMPLEMENT_PARAMETERIZED_DEVICE_AND_GATE_GENERATOR`
- human_klayout_review_required_every_stage: `False`
- can_enter_next_stage_without_human_review: `True`
- next_stage_allowed: `M12C3A_IMPLEMENT_PARAMETERIZED_DEVICE_AND_GATE_GENERATOR`

## 3. M11V Verification Result

- verification_status: `INCONCLUSIVE`
- verification_risk_level: `MEDIUM`
- baseline_power_risk_level: `MEDIUM_BASELINE_LIMITED`
- baseline_routing_risk_level: `HIGH_BASELINE_LIMITED`
- sense_amp_incremental_risk_level: `LOW_INCREMENTAL_RISK`
- wordline_driver_incremental_risk_level: `LOW_INCREMENTAL_RISK`
- recommended_next_stage: `M11V2_DEEPER_CONNECTIVITY_EXTRACTION`
- can_claim_openyield_module_gds_hardmacro_substitution: `False`
- can_claim_routing_clean: `False`
- can_claim_power_clean: `False`
- can_claim_drc_clean: `False`
- can_claim_lvs_clean: `False`
- can_claim_signoff_ready: `False`

## 3. M12O Gap Audit Result

- openram_reference_gds_found: `True`
- openyield_single_authoritative_netlist_proven: `False`
- openyield_complete_sram_netlist_found: `False`
- control_logic_gap_status: `OPENRAM_PRESENT_LAYOUTGEN_MISSING_OPENYIELD_PHYSICAL_UNQUALIFIED`
- configurable_sram_spec_template_generated: `True`
- recommended_next_stage: `M12N_LOCK_OPENYIELD_AUTHORITATIVE_NETLIST`
- can_claim_custom_netlist_driven_layout_generation: `False`
- can_claim_openyield_authoritative_netlist_locked: `False`
- can_claim_drc_clean: `False`
- can_claim_lvs_clean: `False`
- can_claim_signoff_ready: `False`

## 4. M12N OpenYield Authority Lock Result

- authoritative_netlist_lock_status: `PARTIAL_SUBCIRCUIT_LIBRARY_ONLY`
- authoritative_entrypoint: `sram_compiler/testbenches/sram_6t_core_testbench.py`
- authoritative_top_class_or_function: `Sram6TCoreTestbench.create_testbench`
- openyield_parameterized_netlist_generator_proven: `True`
- openyield_complete_sram_top_proven: `False`
- openyield_control_logic_source_locked: `True`
- recommended_next_stage: `M12C_CONTROL_LOGIC_GAP_DEFINITION`
- can_claim_openyield_authoritative_netlist_locked: `False`
- can_claim_custom_netlist_driven_layout_generation: `False`
- can_claim_drc_clean: `False`
- can_claim_lvs_clean: `False`
- can_claim_signoff_ready: `False`

## 5. M12N2 Clean Top Extraction Result

- clean_top_locked: `True`
- parameter_contract_v1_locked: `True`
- openyield_local_sha: `1c34428d8b913963c4971d093b1a7c2df97a2509`
- openyield_version_match: `True`
- openyield_worktree_clean: `True`
- time_control_role_status: `ON_CHIP_CONTROL_LOGIC`
- time_role_requires_team_confirmation: `False`
- openyield_control_logic_netlist_source_locked: `True`
- openyield_control_logic_physical_implementation_ready: `False`
- remaining_M12N2_blockers_count: `5`
- recommended_next_stage: `M12C_CONTROL_LOGIC_GAP_DEFINITION`
- physical_gds_generation_not_part_of_M12N2: `True`
- reused_M12O_review_gds: `True`
- can_make_physical_implementation_claim: `False`

## 6. M12C Control Logic Gap Definition Result

- m12n2r_gate_passed: `True`
- openyield_sha: `1c34428d8b913963c4971d093b1a7c2df97a2509`
- operation_topology_status: `READ_WRITE_SUPERSET_CANONICAL`
- canonical_physical_operation_topology: `READ_WRITE_SUPERSET`
- canonical_operation_topology_locked: `True`
- physical_module_total_count: `22`
- physical_ready_for_qualification_count: `15`
- physical_partial_count: `3`
- physical_reference_only_count: `1`
- physical_missing_count: `3`
- bbox_metadata_coverage: `18/22`
- pin_geometry_coverage: `18/22`
- power_rail_metadata_coverage: `18/22`
- top_bbox_change_expected: `True`
- recommended_next_stage: `M12C2_CONTROL_LOGIC_PHYSICAL_LIBRARY_QUALIFICATION`
- human_review_required: `False`

## M12C2 Control-Library Qualification

- M12C gate reused: `True`
- operation topology: `READ_WRITE_SUPERSET_CANONICAL`
- MOS model names removed from missing hardmacro set: `True`
- trusted manifest entries: `7`
- TIME candidate status: `CONNECTIVITY_UNPROVEN`
- TRANSMISSION_GATE status: `MISSING_REQUIRES_GENERATOR`
- DFF status: `QUALIFIED_REFERENCE_ONLY`
- next stage: `M12C3_CONTROL_LOGIC_PRIMITIVE_LAYOUT_GENERATOR_PLAN`

## M12C3 Primitive Generator Plan

- M12C2 qualification audit complete: `True`
- reusable physical library ready: `False`
- direct reuse count: `0`
- raw candidate DRC marker count: `6661`
- duplicate candidate DRC artifact detected: `True`
- unique candidate DRC marker count: `3422`
- trusted device generator: `/data1/qujh/OpenRAM/compiler/modules/ptx.py`
- trusted gate generator found: `True`
- contact/via generator found: `True`
- FreePDK45 physical tech contract status: `LOCKED_FREEPDK45_V1`
- primitive generator architecture: `OPENRAM_FREEPDK45_DEVICE_CONTACT_ADAPTER`
- parameterized length supported by trusted backend: `False`
- cell naming/cache contract locked: `True`
- TRANSMISSION_GATE route: `OpenRAM ptx-based adapter composition`
- PINV1-4 route: `distinct parameterized inverter variants with stable cache keys`
- smoke cells generated: `False`
- smoke DRC passed: `False`
- next stage: `M12C3A_IMPLEMENT_PARAMETERIZED_DEVICE_AND_GATE_GENERATOR`

## M12C3R Parameter and Naming Contract Correction

- M12C3 architecture audit complete: `True`
- original M12C3 naming contract valid: `False`
- original naming contract superseded: `True`
- original NW0/PW0/L0 tokens detected: `True`
- original zero-dimension token count: `10`
- PINV logical alias is not a physical variant identifier: `True`
- source-derived PINV instance count: `19`
- logical-name collision detected: `True`
- corrected physical variant count: `19`
- fixed FreePDK45 50 nm length policy: `True`
- arbitrary channel length supported: `False`
- current V1 channel-length requirement satisfied: `True`
- OpenRAM adapter bootstrap mode: `IN_PROCESS_OPENRAM_BOOTSTRAP`
- can_claim_parameterized_primitive_generator_locked: `True`
- can_claim_parameterized_primitive_generator_implemented: `False`
- next stage: `M12C3A_IMPLEMENT_PARAMETERIZED_DEVICE_AND_GATE_GENERATOR`
