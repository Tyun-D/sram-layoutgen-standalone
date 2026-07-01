# OpenYield Netlist-to-GDS Readiness Report

- current hybrid GDS available: `True`
- current hybrid GDS path: `outputs/layout_prototype/hybrid_openyield/hybrid_openyield_prototype.gds`
- module readiness rows: `25`
- OpenYield-driven modules count: `7`
- fallback modules count: `8`
- can claim full OpenYield GDS now: `False`
- can claim DRC clean now: `False`
- can claim LVS clean now: `False`
- can claim timing closure now: `False`

## Current GDS-generatable modules

- bitcell_array
- dummy_array
- replica_array
- sense_amp
- write_driver
- column_mux
- wordline_driver

## Fallback Modules

- DELAY_CHAIN
- PRECHARGE
- PRECHARGE_ENABLE_PATH
- SENSE_ENABLE_PATH
- WRITE_ENABLE_PATH
- WORDLINE_ENABLE_PATH
- GATED_CLOCK_PATH
- DFF_ROW

## Metadata-only Modules

- DELAY_CHAIN

## Candidate-contract-only Modules

- PRECHARGE
- PRECHARGE_ENABLE_PATH
- SENSE_ENABLE_PATH
- WRITE_ENABLE_PATH
- WORDLINE_ENABLE_PATH
- GATED_CLOCK_PATH
- DFF_ROW

## Missing Physical Implementation Modules

- none

## Blocking gaps for full OpenYield GDS

| blocking_gap | why_it_blocks_full_gds | minimum_fix | recommended_next_task |
| --- | --- | --- | --- |
| TIME/DFF/control logic are not physical-ready | DELAY_CHAIN is metadata-only and PRECHARGE/enable-path/DFF control objects remain fallback or candidate-contract only, so full OpenYield time-control replacement is unavailable. | Close DFF row placement hooks and convert candidate control-path contracts into physical leaf-to-placement mappings. | Start with decoder/gate-row abutment plus DFF/control-row placement contract closure before any full control replacement claim. |
| DELAY_CHAIN lacks proven physical integration | Timing metadata is consumable, but the current hybrid still uses a legacy delay-chain macro path and no OpenYield physical placement/routing is claimed. | Add a guarded physical representation and placement hook for DELAY_CHAIN without changing legacy default behavior. | Implement delay-chain physical gap closure after decoder row work. |
| PRECHARGE has source-linked smoke evidence but no OpenYield physical integration | Current hybrid falls back to legacy gen_precharge usage and the OpenYield-side PRECHARGE path has not been physically connected into the layout flow. | Define PRECHARGE physical hook, validate polarity, and bind it into placement metadata. | Do precharge physical representation / placement hook after DELAY_CHAIN. |
| Enable paths and gated clock remain candidate-contract only | PRECHARGE_ENABLE_PATH, SENSE_ENABLE_PATH, WRITE_ENABLE_PATH, WORDLINE_ENABLE_PATH, and GATED_CLOCK_PATH have no physical placement/routing implementation. | Recover/bind leaf cells, validate pins, and add placement-ready control path mappings. | Physical mapping for enable-path control logic. |
| Decoder and gate rows are not signoff-ready | Decoder row rules and preplacement are metadata/proxy based; routing, legal physical placement, and zero-risk handoff are unproven. | Turn decoder gate rows into a guarded placement-capable row domain with rail and handoff proof. | Decoder/gate row abutment and rail stitching audit. |
| VDD/GND rail continuity is not globally proven | Peripheral macros such as sense_amp, write_driver, column_mux, gen_precharge, and many gate rows still lack across-abutment continuity proof or shared-rail safety. | Audit and stitch row/domain rail continuity before enabling shared rail assumptions. | Power rail continuity verification and selective stitching. |
| Routing is still legacy | Current hybrid uses legacy top-level routing rather than OpenYield-driven control/peripheral routing. | Replace or compact legacy routing for OpenYield-driven control/peripheral domains. | Routing compaction / routing replacement after placement and rail closure. |
| DRC/LVS/timing closure are not claimed | Reports explicitly forbid claiming full-chip DRC clean, LVS clean, or timing closure now. | Run guarded sanity/signoff passes after physical integration is materially complete. | DRC/LVS sanity and timing closure audit after routing closure. |

## next_action_priority

| priority | target_module | reason | expected_result | files_to_modify | risk_level | whether_affects_legacy_default | estimated_gate_after_completion |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | decoder_gate_cells | Decoder gate rows already have leaf-cell, row-packing, and metadata feasibility evidence, so this is the highest-leverage path to convert proxies into placement-ready control logic. | Guarded decoder/gate-row abutment with clearer rail continuity and reduced ambiguity for downstream control placement. | sram_layoutgen/openyield_adapter/gate_row_packer.py;sram_layoutgen/openyield_adapter/decoder_*;tests/test_openyield_gate_row_vertical_abutment.py | medium | False | can_enter_decoder_gate_row_abutment=True with fewer placement blockers |
| 2 | DELAY_CHAIN | DELAY_CHAIN is the only control object already admitted for metadata consumption, so adding a physical hook closes a concrete gap rather than starting from candidate-only state. | DELAY_CHAIN transitions from metadata-only to placement-hook-ready without changing legacy default mode. | sram_layoutgen/openyield_adapter/timing_metadata_consumer.py;sram_layoutgen/openyield_adapter/time_control_*;tests/test_openyield_timing_metadata_consumer.py | medium | False | can_enter_delay_chain_physical_gap_closure=True with a concrete placement representation |
| 3 | PRECHARGE | PRECHARGE already has source-linked candidate smoke and a local macro; the missing step is physical hook closure rather than source discovery. | PRECHARGE moves from candidate/spice-only into guarded physical placement readiness. | sram_layoutgen/openyield_adapter/time_control_generated_logic_contracts.py;sram_layoutgen/openyield_adapter/control_path_candidate_generation.py;tests/test_openyield_precharge_spice_smoke.py | medium | False | can_enter_precharge_physical_gap_closure=True with a physical placement hook |
| 4 | PRECHARGE_ENABLE_PATH/SENSE_ENABLE_PATH/WRITE_ENABLE_PATH/WORDLINE_ENABLE_PATH/GATED_CLOCK_PATH | These remain candidate-contract-only and block full control replacement. | Control-path leaf binding and placement-ready mapping. | sram_layoutgen/openyield_adapter/control_path_candidate_generation.py;sram_layoutgen/openyield_adapter/time_control_signal_bindings.py | high | False | candidate_contract_only_modules_count decreases |
| 5 | routing | Current hybrid still uses legacy routing even when modules are OpenYield-driven. | Reduced dependence on legacy top-level routing for OpenYield domains. | sram_layoutgen/standalone.py;sram_layoutgen/*routing* | high | Potentially | can_enter_routing_compaction=True with lower blocker severity |
| 6 | power_rail_stitching | Shared-rail continuity remains explicitly unproven across peripherals and control rows. | Sharper proof of rail continuity and safer row-abutment claims. | sram_layoutgen/openyield_adapter/hardcell_power_rail_continuity.py;sram_layoutgen/openyield_adapter/cell_rail_overlap_eligibility.py | medium | False | can_enter_power_rail_stitching_verification=True with narrower unresolved set |
| 7 | DRC/LVS/timing | Signoff should only be attempted after major physical gaps are closed. | Guarded sanity evidence without overclaiming closure. | sram_layoutgen/signoff.py;sram_layoutgen/verifier.py;scripts/*signoff* | medium | False | drc/lvs/timing blocker language can become more specific |
