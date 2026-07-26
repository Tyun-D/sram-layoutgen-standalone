# M1 LayoutGen OpenYield Binding Report

| M1_layoutgen_openyield_binding_available | status_file_read | status_file_updated | layoutgen_generator_inventory_available | first_round_module_physical_audit_available | openyield_to_layoutgen_binding_available | openyield_net_to_layoutgen_pin_binding_available | physical_cell_binding_review_gds_available | review_gds_manifest_available | layoutgen_generator_inventory_count | first_round_openyield_module_audited_count | binding_row_count | pin_binding_row_count | critical_modules_with_binding_or_gap | human_klayout_review_required | can_enter_M2_before_human_review | remaining_M1_blockers | remaining_M1_blockers_count | can_claim_M1_done |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| True | True | True | True | True | True | True | True | True | 8 | 20 | 20 | 34 | True | True | False | [] | 0 | True |

This stage audits the original layoutgen generation path and binds OpenYield modules/nets onto real generator candidates or explicit regeneration gaps. It does not generate a final SRAM top.
