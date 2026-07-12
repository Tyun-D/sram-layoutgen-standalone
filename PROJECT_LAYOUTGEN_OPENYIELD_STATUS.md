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

## M12C3A Primitive Generator

- M12C3R correction gate passed and M12C3A concrete primitive generation completed.
- concrete drive scales 16x16: `{'address_bits': 4, 'clk_dff_count': 22, 'ref_dff_count': 22, 'clk_drive_scale': 1.0, 'pre_col_scale': 0.26153846153846155, 'pre_pmos_scale': 1.0, 'pre_drive_scale': 1, 'w_en_scale': 1, 'resolved_scales': {'pdrive': 1.0, 'pdrive2_for_pre': 1, 'w_en_scale': 1}}`
- concrete drive scales 64x8: `{'address_bits': 6, 'clk_dff_count': 16, 'ref_dff_count': 22, 'clk_drive_scale': 1.0, 'pre_col_scale': 0.13846153846153847, 'pre_pmos_scale': 4.0, 'pre_drive_scale': 1, 'w_en_scale': 1, 'resolved_scales': {'pdrive': 1.0, 'pdrive2_for_pre': 1, 'w_en_scale': 1}}`
- generated physical variants: `10` total, `9` PINV plus `1` TRANSMISSION_GATE.
- per-cell DRC total markers: `0`
- deterministic regeneration verified: `True`
- human review gate remains required: `True`
- next stage: `M12C3AH_PRIMITIVE_SMOKE_VISUAL_REVIEW`

## M12C3A3 Transmission Gate Repair

- M12C3A machine generation and cell-level DRC had previously passed.
- Human review later found the Transmission Gate `IN` net shorted into both `VDD` and `VSS`, while 9 `PINV` variants passed review.
- This confirms DRC zero markers cannot prove signal-level connectivity semantics.
- M12C3A3 repaired only the OpenRAM-backed Transmission Gate, added Metal1-accessible `CTR_P/CTR_N`, fixed aggregate GDS artifacts, and fixed empty geometry fingerprint digest artifacts.
- Repaired TG machine connectivity passed: `True`.
- Repaired TG DRC clean: `False`.
- Composite CONTROL_LOGIC generation has still not started.
- Another focused human visual review is still required for the repaired Transmission Gate.

## M12C3A3 Transmission Gate Repair

- M12C3A machine generation and cell-level DRC had previously passed.
- Human review later found the Transmission Gate `IN` net shorted into both `VDD` and `VSS`, while 9 `PINV` variants passed review.
- This confirms DRC zero markers cannot prove signal-level connectivity semantics.
- M12C3A3 repaired only the OpenRAM-backed Transmission Gate, added Metal1-accessible `CTR_P/CTR_N`, fixed aggregate GDS artifacts, and fixed empty geometry fingerprint digest artifacts.
- Repaired TG machine connectivity passed: `False`.
- Repaired TG DRC clean: `False`.
- Composite CONTROL_LOGIC generation has still not started.
- Another focused human visual review is still required for the repaired Transmission Gate.

## M12C3A3 Transmission Gate Repair

- M12C3A machine generation and cell-level DRC had previously passed.
- Human review later found the Transmission Gate `IN` net shorted into both `VDD` and `VSS`, while 9 `PINV` variants passed review.
- This confirms DRC zero markers cannot prove signal-level connectivity semantics.
- M12C3A3 repaired only the OpenRAM-backed Transmission Gate, added Metal1-accessible `CTR_P/CTR_N`, fixed aggregate GDS artifacts, and fixed empty geometry fingerprint digest artifacts.
- Repaired TG machine connectivity passed: `True`.
- Repaired TG DRC clean: `True`.
- Composite CONTROL_LOGIC generation has still not started.
- Another focused human visual review is still required for the repaired Transmission Gate.

## M12C3A4 Canonical Primitive Label Cleanup

- 9 `PINV` human checks are formally locked as passed.
- Repaired `TRANSMISSION_GATE` human review is formally locked as passed.
- Wrapper/core duplicate labels, uppercase/lowercase alias overlap, and leaked PTX `G/S/D` labels were confirmed in pre-cleanup primitive exports.
- The issue does not change conductive geometry, but it can confuse LVS, extraction, and top-level pin recognition.
- Sanitized reusable primitive GDS exports were generated with canonical top-level labels only.
- Original debug GDS sources were quarantined from reusable composition outputs.
- Non-text geometry preserved across all primitives: `False`.
- Connectivity preserved across all primitives: `False`.
- Composite CONTROL_LOGIC generation may proceed to planning, but CONTROL_LOGIC physical ready is still false.

## M12C3A4 Canonical Primitive Label Cleanup

- 9 `PINV` human checks are formally locked as passed.
- Repaired `TRANSMISSION_GATE` human review is formally locked as passed.
- Wrapper/core duplicate labels, uppercase/lowercase alias overlap, and leaked PTX `G/S/D` labels were confirmed in pre-cleanup primitive exports.
- The issue does not change conductive geometry, but it can confuse LVS, extraction, and top-level pin recognition.
- Sanitized reusable primitive GDS exports were generated with canonical top-level labels only.
- Original debug GDS sources were quarantined from reusable composition outputs.
- Non-text geometry preserved across all primitives: `True`.
- Connectivity preserved across all primitives: `True`.
- Composite CONTROL_LOGIC generation may proceed to planning, but CONTROL_LOGIC physical ready is still false.

## M12C3A4R Review Atlas Closure

- M12C3A4 reusable label cleanup core gate remains passed.
- The original review atlas was found to contain 20 missing SREF targets and was not self-contained.
- The original test only compared aggregate SHA values and did not validate GDS reference closure.
- The review atlas was rebuilt as a self-contained GDS with deterministic before/after hierarchy renaming.
- Historical failure state and current qualified primitive state are now separated.
- The current Transmission Gate is not shorted.
- Duplicate label cleanup is complete in the current qualified state.
- All 10 reusable primitives remained byte-identical during evidence closure.
- The only approved primitive composition root for M12C4 is `/data1/qujh/work/sram_layoutgen_step45_clean/outputs/M12C3A4_canonical_primitive_label_cleanup/current_supported_config/reusable_cells`.
- CONTROL_LOGIC physical ready, LVS clean, and signoff ready remain false.

## M12C4 Composite Planning

- M12C3A4R evidence gate is passed.
- The 10 reusable primitives under `/data1/qujh/work/sram_layoutgen_step45_clean/outputs/M12C3A4_canonical_primitive_label_cleanup/current_supported_config/reusable_cells` are the only approved physical inputs.
- Historical and current primitive qualification states remain separated.
- Source-exact composite hierarchy extraction was re-derived from the latest OpenYield code.
- Concrete 16x16 and 64x8 expansions were generated without any GDS output.
- Approved child binding, primitive interface compatibility, placement architecture, routing contract, and implementation waves were locked as planning artifacts.
- The first actual composite GDS stage is `M12C4T_PRIMITIVE_INTERFACE_NORMALIZATION`.
- CONTROL_LOGIC physical ready, LVS clean, and signoff ready remain false.

## M12C4R Correction Gate

- M12C4 planning framework is preserved, but the original source-exact claim is corrected.
- The original source net matrix only covered 11/232 rows and DFF coverage was 0/52.
- The original unresolved=0 claim is withdrawn.
- The original interface risk was inferred from a 2.5nm height delta despite aligned rails.
- M12C4R re-qualified the PINV/TG interface with diagnostic GDS and DRC instead of bbox heuristics.
- M12C4R re-qualified the routing backend with an executable M1/Via1/M2 diagnostic.
- Current next stage: `M12C4T_PRIMITIVE_INTERFACE_NORMALIZATION`.
- No formal composite control cell was generated in M12C4R.

## M12C4R Correction Gate

- M12C4 planning framework is preserved, but the original source-exact claim is corrected.
- The original source net matrix only covered 11/232 rows and DFF coverage was 0/52.
- The original unresolved=0 claim is withdrawn.
- The original interface risk was inferred from a 2.5nm height delta despite aligned rails.
- M12C4R re-qualified the PINV/TG interface with diagnostic GDS and DRC instead of bbox heuristics.
- M12C4R re-qualified the routing backend with an executable M1/Via1/M2 diagnostic.
- Current next stage: `M12C4P_COMPOSITE_ROUTING_BACKEND_PREPARATION`.
- No formal composite control cell was generated in M12C4R.

## M12C4R Correction Gate

- M12C4 planning framework is preserved, but the original source-exact claim is corrected.
- The original source net matrix only covered 11/232 rows and DFF coverage was 0/52.
- The original unresolved=0 claim is withdrawn.
- The original interface risk was inferred from a 2.5nm height delta despite aligned rails.
- M12C4R re-qualified the PINV/TG interface with diagnostic GDS and DRC instead of bbox heuristics.
- M12C4R re-qualified the routing backend with an executable M1/Via1/M2 diagnostic.
- Current next stage: `M12C4A_DFF_COMPOSITE_GENERATION`.
- No formal composite control cell was generated in M12C4R.

## M12C4R2 Final Binding Gate

- M12C4R's 52 DFF source pin-net connections remain valid.
- M12C4R's direct-abutment and routing diagnostics remain DRC-clean and unchanged.
- The old 232-row matrix was only the filtered default-environment view, not all-branch source coverage.
- All-branch declared source coverage is now recorded separately from default/config-active matrices.
- DATA_DFF and conditional branches are restored into the source-exact evidence model.
- Concrete expansion and DFF 11-instance approved binding are now data-derived instead of hard-coded.
- Current next stage: `M12C4A_DFF_COMPOSITE_GENERATION`.
- No formal DFF GDS was generated in M12C4R2.

## M12C4A

- M12C4R2 source/binding gate passed.
- M12C4R2 net-role metadata defect corrected.
- M12C4R2 diagnostic unchanged hardcoded defect corrected.
- DFF physical cell generated: `DFF_TG4_INV7_FPDK45_3363e5e66d68`.
- DFF child count / source connection count: `11` / `52`.
- Selected floorplan: `SINGLE_ROW_SOURCE_ORDER`.
- DFF DRC marker count: `1970`.
- Deterministic regeneration verified: `True`.
- LVS remains not proven.
- Higher-level CONTROL_LOGIC generation remains not started.

## M12C4AC

- M12C4A generation failed because 11 signal nets merged through Metal2 same-layer crossings.
- D/Q short was a signal-supernet consequence, not a primitive-level short.
- Failed DRC marker count was 88 and all markers were routing/grid related.
- No Well/Implant primitive interface violation was detected in the failed attempt.
- Failed DFF was quarantined and marked DO_NOT_REUSE / DO_NOT_COMPOSE / DO_NOT_HUMAN_APPROVE.
- Canonical source topology hash unified: `True`.
- Repaired routing architecture: `M1_HORIZONTAL_TRACK_M2_VERTICAL_DROP`.
- Pin access planning passed: `True`.
- Repaired connectivity passed: `False`.
- Repaired DRC marker count: `105`.
- Human review open: `False`.
- LVS remains not proven.
- Higher-level CONTROL_LOGIC generation remains blocked.
