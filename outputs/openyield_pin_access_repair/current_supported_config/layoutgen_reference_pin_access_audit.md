# Layoutgen Reference Pin Access Audit

C2 uses old layoutgen outputs and scripts only as mechanism references, not as final deliverables.

- layoutgen_reference_used: `True`
- current_openyield_contract_route_count: `43`
- current_openyield_contract_power_count: `10`

## Reuse Decisions

| reference_item | source_path | what_it_solves | can_reuse_directly | needs_adaptation | do_not_reuse_reason | mapped_stage | expected_effect_on_complete_gds | risk_if_reused_wrongly |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| baseline_complete_gds | /data1/qujh/work/sram_layoutgen_step45_clean/outputs/layout_prototype/baseline_legacy/sram_8x64_wpr4_fd45.complete.gds | Shows a visually SRAM-like macro with dense array body and periphery organization closer to final pin access expectations. | False | True | Old baseline GDS is not OpenYield-driven and cannot be shipped as the final complete SRAM GDS. | C2/C3/C4/C5 | Improves edge-access synthesis, floorplan anchoring, and route ownership decisions. | Would regress to legacy/non-OpenYield ownership. |
| storage_aggregation_compare | /data1/qujh/work/sram_layoutgen_step45_clean/scripts/openyield_storage_aggregation_compare.py | Documents legacy storage-array placement and dummy/replica grouping logic that is closer to real SRAM structure than the R5 overlay. | False | True | Legacy script still leaves peripheral placement and routing on the old path. | C2/C3 | Helps align array-owned BL/BR/WL access synthesis with prior row/column ownership conventions. | Could reintroduce legacy placement assumptions without OpenYield module mapping. |
| wordline_driver_standalone_smoke | /data1/qujh/work/sram_layoutgen_step45_clean/scripts/openyield_wordlinedriver_standalone_smoke.py | Captures prior wordline-driver pin-label verification and local macro checks. | True | True | Needs translation from standalone smoke metrics into current module access views. | C2/C4 | Improves WL driver output/access confidence and later route landing. | Could preserve label-only assumptions instead of geometry-backed access. |
| rail_overlap_and_abutment_reports | /data1/qujh/work/sram_layoutgen_step45_clean/outputs/layout_prototype/hybrid_openyield_rail_overlap | Shows prior rail overlap/abutment investigations that are directly relevant to synthesized VDD/GND access ownership. | False | True | Old overlap proofs do not equal final power continuity on current OpenYield module composition. | C2/C5 | Improves power access edge planning and future rail stitch decisions. | Could hide rail-intersection-not-connected defects. |

## Risks

- Do not import legacy address-short defects into new routing.
- Do not rely on legacy WL driver power connectivity without current module pin proof.
- Do not reuse top-level power straps as final continuity evidence.
- Do not reuse dummy/replica/tap/cap placement blindly without OpenYield net/module ownership mapping.
