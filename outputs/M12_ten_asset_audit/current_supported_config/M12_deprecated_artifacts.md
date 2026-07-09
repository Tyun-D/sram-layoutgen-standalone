# M12 Deprecated Artifacts

- `openyield_complete_sram_gds_claim` path=`outputs/openyield_complete_sram/current_supported_config/openyield_complete_sram.gds` reason=`Reclassified as OpenYield-connected access-view GDS prototype, not real complete SRAM GDS.`
- `access_module_cells` path=`*_access_module` reason=`Cannot serve as SRAM physical implementation主体.`
- `floorplan_proxy_cells` path=`floorplan_proxy*` reason=`Only acceptable for review/floorplan proof, not final physical module hierarchy.`
- `access_view_route` path=`C4 access-view signal route shapes` reason=`Useful as semantic/prototype evidence, not sufficient as physical complete claim basis.`
- `access_view_power_stitch` path=`C5 access-view power stitch shapes` reason=`Useful as prototype geometry evidence, not final physical implementation proof.`
- `synthesized_pin_complete_claim_support` path=`C2 synthesized pin access` reason=`Cannot alone support physical complete claim.`
- `access_module cells` path=`*_access_module` reason=`cannot be claimed as physical implementation in M10H gate closure`
- `floorplan_proxy cells` path=`floorplan_proxy*` reason=`review-only proxy hierarchy, not valid implementation backing for M10H`
- `historical hybrid reference` path=`outputs/layout_prototype/hybrid_openyield_rail_overlap/hybrid_openyield_rail_overlap.complete.gds` reason=`superseded by locked uploaded golden reference and M8R/M8RC exact-match flow`
