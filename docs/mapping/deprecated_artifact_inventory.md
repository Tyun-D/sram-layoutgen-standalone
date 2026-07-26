| artifact_name | path | deprecated_reason | do_not_use_as_final |
| --- | --- | --- | --- |
| openyield_complete_sram_gds_claim | outputs/openyield_complete_sram/current_supported_config/openyield_complete_sram.gds | Reclassified as OpenYield-connected access-view GDS prototype, not real complete SRAM GDS. | True |
| access_module_cells | *_access_module | Cannot serve as SRAM physical implementation主体. | True |
| floorplan_proxy_cells | floorplan_proxy* | Only acceptable for review/floorplan proof, not final physical module hierarchy. | True |
| access_view_route | C4 access-view signal route shapes | Useful as semantic/prototype evidence, not sufficient as physical complete claim basis. | True |
| access_view_power_stitch | C5 access-view power stitch shapes | Useful as prototype geometry evidence, not final physical implementation proof. | True |
| synthesized_pin_complete_claim_support | C2 synthesized pin access | Cannot alone support physical complete claim. | True |
