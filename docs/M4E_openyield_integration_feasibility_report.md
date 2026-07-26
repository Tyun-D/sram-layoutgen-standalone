# M4E OpenYield Integration Feasibility Report

## Decision

- go_nogo_decision: `PARTIAL_GO_WITH_DEFINED_SCOPE`
- allowed_next_stage: `M5_IMPLEMENT_OPENYIELD_LAYOUTGEN_INTEGRATION`
- can_directly_implement_next: `False`
- can_partially_implement_next: `True`
- cannot_implement_reason: `A full one-shot replacement is not ready because six control/time modules still require layoutgen fallback semantics, even though fourteen modules can enter direct implementation now. The current intent JSON is still frozen at 4x4 / words_per_row=1 while the restored optimized backbone is 8x64 / words_per_row=4.`
- evaluation_only_once_enforced: `True`
- no_more_evaluation_allowed_after_M4E: `True`

## Counts

- openyield_module_count: `20`
- layoutgen_baseline_module_count: `16`
- module_type_mismatch_count: `12`
- net_mapping_count: `34`
- net_mapping_gap_count: `0`
- direct_generator_binding_count: `3`
- parameterized_generator_binding_count: `6`
- real_cell_wrapper_count: `5`
- layoutgen_fallback_with_openyield_semantics_count: `6`
- not_implementable_now_count: `0`

## Required Modifications

- floorplan_change_required: `True`
- placement_change_required: `True`
- routing_change_required: `True`
- power_change_required: `True`

## Review GDS

- review_gds_path: `/data1/qujh/work/sram_layoutgen_step45_clean/outputs/M4E_openyield_integration_eval/current_supported_config/openyield_integration_feasibility_review.gds`
- review_gds_sanity_status: `GDS_PARSED_SANITY_PASSED`

## Open Questions Resolved

- Q1 module/layer alignment: OpenYield has 20 semantic modules while baseline layoutgen exposes 16 physical role buckets; arrays and hardmacro-backed column/data modules align well, while control and row-path semantics are split more finely in OpenYield.
- Q2 direct generator bindings: Direct generator bindings are viable for bitcell_array, dummy_array, and replica_array because the optimized trunk already generates them through array aggregation and standalone top flow.
- Q3 new wrappers needed: wordline_driver, column_mux, sense_amp, write_driver, and precharge should be bound as real-cell wrappers around layoutgen-owned hardmacros rather than as label-only placeholders.
- Q4 floorplan impact: Floorplan changes are required for row_decoder, wordline_decoder, decoder_gate_cells, DELAY_CHAIN, DFF_ROW, and the six control/time fallback modules because OpenYield splits the row/control perimeter more finely than baseline layoutgen.
- Q5 placement impact: Placement changes are required for every non-array module because semantic ownership must move from baseline-only roles to OpenYield-driven module boundaries inside the optimized trunk.
- Q6 routing impact: Routing changes are required for all non-array modules so WL, BL/BR, DIN/DOUT, address, control, and replica-timing nets are driven by OpenYield net ownership rather than implicit baseline ownership.
- Q7 power impact: Power changes are required for twelve modules. M3F restored optimized power stitching with 15 positive overlap boundaries, but wrapper-backed modules still need OpenYield-driven rail eligibility and shared-rail gating.
- Q8 net hookup: WL and DEC_WL stay on the row path, BL/BR stay on vertical column pitch routes, control/data nets stay on periphery buses, and VDD/VSS must remain on optimized rail-overlap/stitch logic. The next stage must thread all 34 semantic bindings into standalone.py-driven physical hookup.
- Q9 first-round GDS as real physical modules: First-round OpenYield module GDS is usable as physical reference only for arrays and hardmacro wrappers. Candidate row/control composites must not be installed as final physical modules.
- Q10 generator-based re-generation path: Yes. For non-reusable first-round modules, the correct path is to regenerate through the optimized layoutgen trunk using parameterized generator ownership plus OpenYield semantics, not to force the first-round GDS into the final hierarchy.
- Q11 files to modify: Primary files to modify next are sram_layoutgen/standalone.py, sram_layoutgen/openyield_adapter/M3F_optimized_layoutgen_restore.py, array_aggregation.py, module_gds_generators.py, top_level_assembly.py, wordlinedriver_adapter.py, writedriver_adapter.py, architecture_adapter.py, and hardcell_power_rail_continuity.py.
- Q12 minimal viable implementation: The minimum viable implementation is a 14-module integration scope: 3 direct array bindings, 6 parameterized row/control generators, and 5 real-cell wrappers, while the six control/time modules remain on explicit layoutgen fallback with OpenYield semantics.
- Q13 missing pieces for full implementation: Full implementation still lacks native OpenYield physical control/time modules, shared-rail continuity proof for wrapper-backed peripherals, and alignment between the 4x4 intent JSON and the restored 8x64_wpr4 optimized backbone.

## Implementation Scope

- implement_now_modules: `bitcell_array; dummy_array; replica_array; row_decoder; wordline_decoder; decoder_gate_cells; wordline_driver; wordline_driver_gate_cells; column_mux; sense_amp; write_driver; precharge; DELAY_CHAIN; DFF_ROW`
- fallback_modules: `CONTROL_LOGIC; GATED_CLOCK_PATH; PRECHARGE_ENABLE_PATH; SENSE_ENABLE_PATH; WRITE_ENABLE_PATH; WORDLINE_ENABLE_PATH`
- intent_parameter_mismatch: `intent(word_size=4,num_words=4,words_per_row=1) vs optimized(word_size=8,num_words=64,words_per_row=4)`

## Review Gate

- human_klayout_review_required: `True`
- can_enter_next_stage_before_human_review: `False`
- remaining_M4E_blockers_count: `0`
