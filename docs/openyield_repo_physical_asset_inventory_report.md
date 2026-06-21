# OpenYield Repo Physical Asset Inventory

This report stays in readonly evidence-collection mode. It inventories filesystem assets and prepares the next proof tasks without modifying standalone integration, routing, or GDS writing.

## Audit Summary

- repo root: `E:\njust\keyan\SRAM Compiler_V2\OpenRAM-stable\deliverables\sram_layoutgen_step45_clean`
- searched roots: `["E:\\njust\\keyan\\SRAM Compiler_V2\\OpenRAM-stable\\deliverables\\sram_layoutgen_step45_clean", "E:\\njust\\keyan\\SRAM Compiler_V2\\OpenRAM-stable\\deliverables\\sram_layoutgen_step45_clean\\technology\\freepdk45", "E:\\njust\\keyan\\SRAM Compiler_V2\\OpenRAM-stable\\deliverables\\sram_layoutgen_step45_clean\\docs", "E:\\njust\\keyan\\SRAM Compiler_V2\\OpenRAM-stable\\deliverables\\sram_layoutgen_step45_clean\\build"]`
- searched extensions: `[".cdl", ".drc", ".gds", ".json", ".lef", ".lib", ".log", ".lydrc", ".lyp", ".lyrdb", ".lyt", ".md", ".net", ".py", ".rb", ".sp", ".spi", ".spice", ".sv", ".tcl", ".v"]`
- recommended next goal: `hardcell_power_rail_continuity_readonly_audit`

## Decision Flags

```json
{
  "repo_physical_asset_inventory_available": true,
  "hardcell_gds_inventory_available": true,
  "spice_inventory_available": true,
  "lef_or_tech_inventory_available": true,
  "drc_deck_inventory_available": true,
  "openram_generated_output_inventory_available": true,
  "layout_writer_inventory_available": true,
  "routing_inventory_available": true,
  "standalone_inventory_available": true,
  "can_enter_hardcell_power_rail_continuity_readonly_audit": true,
  "can_enter_legal_placement_readonly_audit": true,
  "can_enter_routing_obstacle_readonly_audit": true,
  "can_enter_timing_metadata_inventory": true,
  "can_modify_standalone_now": false,
  "can_generate_time_control_gds_now": false,
  "can_enter_physical_placement_now": false
}
```

## Hardcell / Macro GDS Inventory

| macro | role | gds exists | bbox known | vdd | gnd | bindings | openyield bindings | path |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| cell_1rw | bitcell | True | True | True | True | openyield_macro_aliases.json | SRAM_6T_CELL | E:\njust\keyan\SRAM Compiler_V2\OpenRAM-stable\deliverables\sram_layoutgen_step45_clean\technology\freepdk45\gds_lib\cell_1rw.gds |
| cell_2rw | bitcell | True | True | True | True | filesystem_scan | - | E:\njust\keyan\SRAM Compiler_V2\OpenRAM-stable\deliverables\sram_layoutgen_step45_clean\technology\freepdk45\gds_lib\cell_2rw.gds |
| dff | dff | True | True | True | True | openyield_macro_aliases.json | DFF | E:\njust\keyan\SRAM Compiler_V2\OpenRAM-stable\deliverables\sram_layoutgen_step45_clean\technology\freepdk45\gds_lib\dff.gds |
| dummy_cell_1rw | dummy_bitcell | True | True | True | True | openyield_macro_aliases.json | Dummy_CELL, Dummy_Row, Dummy_Column | E:\njust\keyan\SRAM Compiler_V2\OpenRAM-stable\deliverables\sram_layoutgen_step45_clean\technology\freepdk45\gds_lib\dummy_cell_1rw.gds |
| dummy_cell_2rw | dummy_bitcell | True | True | True | True | filesystem_scan | - | E:\njust\keyan\SRAM Compiler_V2\OpenRAM-stable\deliverables\sram_layoutgen_step45_clean\technology\freepdk45\gds_lib\dummy_cell_2rw.gds |
| gen_col_mux | column_mux | True | True | False | False | replacement_macros.json | - | E:\njust\keyan\SRAM Compiler_V2\OpenRAM-stable\deliverables\sram_layoutgen_step45_clean\technology\freepdk45\gds_lib\gen_col_mux.gds |
| gen_delay_inv | hard_macro | True | True | False | False | replacement_macros.json | - | E:\njust\keyan\SRAM Compiler_V2\OpenRAM-stable\deliverables\sram_layoutgen_step45_clean\technology\freepdk45\gds_lib\gen_delay_inv.gds |
| gen_inv | hard_macro | True | True | False | False | replacement_macros.json | - | E:\njust\keyan\SRAM Compiler_V2\OpenRAM-stable\deliverables\sram_layoutgen_step45_clean\technology\freepdk45\gds_lib\gen_inv.gds |
| gen_nand2 | hard_macro | True | True | False | False | replacement_macros.json | - | E:\njust\keyan\SRAM Compiler_V2\OpenRAM-stable\deliverables\sram_layoutgen_step45_clean\technology\freepdk45\gds_lib\gen_nand2.gds |
| gen_nand4 | hard_macro | True | True | False | False | filesystem_scan | - | E:\njust\keyan\SRAM Compiler_V2\OpenRAM-stable\deliverables\sram_layoutgen_step45_clean\technology\freepdk45\gds_lib\gen_nand4.gds |
| gen_nor2 | hard_macro | True | True | False | False | filesystem_scan | - | E:\njust\keyan\SRAM Compiler_V2\OpenRAM-stable\deliverables\sram_layoutgen_step45_clean\technology\freepdk45\gds_lib\gen_nor2.gds |
| gen_precharge | precharge | True | True | False | False | replacement_macros.json | - | E:\njust\keyan\SRAM Compiler_V2\OpenRAM-stable\deliverables\sram_layoutgen_step45_clean\technology\freepdk45\gds_lib\gen_precharge.gds |
| gen_well_tap | hard_macro | True | True | False | False | filesystem_scan | - | E:\njust\keyan\SRAM Compiler_V2\OpenRAM-stable\deliverables\sram_layoutgen_step45_clean\technology\freepdk45\gds_lib\gen_well_tap.gds |
| gen_wl_driver | wordline_driver | True | True | False | False | replacement_macros.json | - | E:\njust\keyan\SRAM Compiler_V2\OpenRAM-stable\deliverables\sram_layoutgen_step45_clean\technology\freepdk45\gds_lib\gen_wl_driver.gds |
| gen_col_mux | column_mux | True | True | False | True | replacement_macros.json, openram_replacements_gds | - | E:\njust\keyan\SRAM Compiler_V2\OpenRAM-stable\deliverables\sram_layoutgen_step45_clean\technology\freepdk45\gds_lib\openram_replacements\gen_col_mux.gds |
| gen_delay_inv | replacement_macro | True | True | True | True | replacement_macros.json, openram_replacements_gds | - | E:\njust\keyan\SRAM Compiler_V2\OpenRAM-stable\deliverables\sram_layoutgen_step45_clean\technology\freepdk45\gds_lib\openram_replacements\gen_delay_inv.gds |
| gen_inv | replacement_macro | True | True | True | True | replacement_macros.json, openram_replacements_gds | - | E:\njust\keyan\SRAM Compiler_V2\OpenRAM-stable\deliverables\sram_layoutgen_step45_clean\technology\freepdk45\gds_lib\openram_replacements\gen_inv.gds |
| gen_nand2 | replacement_macro | True | True | True | True | replacement_macros.json, openram_replacements_gds | - | E:\njust\keyan\SRAM Compiler_V2\OpenRAM-stable\deliverables\sram_layoutgen_step45_clean\technology\freepdk45\gds_lib\openram_replacements\gen_nand2.gds |
| gen_precharge | precharge | True | True | True | False | replacement_macros.json, openram_replacements_gds | - | E:\njust\keyan\SRAM Compiler_V2\OpenRAM-stable\deliverables\sram_layoutgen_step45_clean\technology\freepdk45\gds_lib\openram_replacements\gen_precharge.gds |
| gen_wl_driver | wordline_driver | True | True | True | True | replacement_macros.json, openram_replacements_gds | - | E:\njust\keyan\SRAM Compiler_V2\OpenRAM-stable\deliverables\sram_layoutgen_step45_clean\technology\freepdk45\gds_lib\openram_replacements\gen_wl_driver.gds |
| gen_col_mux_vdd_labeled | column_mux | True | True | True | True | openyield_repaired_gds | - | E:\njust\keyan\SRAM Compiler_V2\OpenRAM-stable\deliverables\sram_layoutgen_step45_clean\technology\freepdk45\gds_lib\openyield_repaired\gen_col_mux_vdd_labeled.gds |
| replica_cell_1rw | replica_bitcell | True | True | True | True | openyield_macro_aliases.json | Replica_CELL, Replica_Column | E:\njust\keyan\SRAM Compiler_V2\OpenRAM-stable\deliverables\sram_layoutgen_step45_clean\technology\freepdk45\gds_lib\replica_cell_1rw.gds |
| replica_cell_2rw | replica_bitcell | True | True | True | True | filesystem_scan | - | E:\njust\keyan\SRAM Compiler_V2\OpenRAM-stable\deliverables\sram_layoutgen_step45_clean\technology\freepdk45\gds_lib\replica_cell_2rw.gds |
| sense_amp | sense_amp | True | True | True | True | openyield_macro_aliases.json | SENSEAMP | E:\njust\keyan\SRAM Compiler_V2\OpenRAM-stable\deliverables\sram_layoutgen_step45_clean\technology\freepdk45\gds_lib\sense_amp.gds |
| tri_gate | hard_macro | True | True | True | True | openyield_macro_aliases.json | tri_gate | E:\njust\keyan\SRAM Compiler_V2\OpenRAM-stable\deliverables\sram_layoutgen_step45_clean\technology\freepdk45\gds_lib\tri_gate.gds |
| write_driver | write_driver | True | True | True | True | openyield_macro_aliases.json | WRITEDRIVER | E:\njust\keyan\SRAM Compiler_V2\OpenRAM-stable\deliverables\sram_layoutgen_step45_clean\technology\freepdk45\gds_lib\write_driver.gds |

## SPICE / CDL Inventory

| macro | subckt | power pins | matches gds | path |
| --- | --- | --- | --- | --- |
| cell_1rw | cell_1rw | vdd, gnd | True | E:\njust\keyan\SRAM Compiler_V2\OpenRAM-stable\deliverables\sram_layoutgen_step45_clean\technology\freepdk45\sp_lib\cell_1rw.sp |
| cell_2rw | cell_2rw | vdd, gnd | True | E:\njust\keyan\SRAM Compiler_V2\OpenRAM-stable\deliverables\sram_layoutgen_step45_clean\technology\freepdk45\sp_lib\cell_2rw.sp |
| dff | dff | vdd, gnd | True | E:\njust\keyan\SRAM Compiler_V2\OpenRAM-stable\deliverables\sram_layoutgen_step45_clean\technology\freepdk45\sp_lib\dff.sp |
| dummy_cell_1rw | dummy_cell_1rw | vdd, gnd | True | E:\njust\keyan\SRAM Compiler_V2\OpenRAM-stable\deliverables\sram_layoutgen_step45_clean\technology\freepdk45\sp_lib\dummy_cell_1rw.sp |
| dummy_cell_2rw | dummy_cell_2rw | vdd, gnd | True | E:\njust\keyan\SRAM Compiler_V2\OpenRAM-stable\deliverables\sram_layoutgen_step45_clean\technology\freepdk45\sp_lib\dummy_cell_2rw.sp |
| replica_cell_1rw | replica_cell_1rw | vdd, gnd | True | E:\njust\keyan\SRAM Compiler_V2\OpenRAM-stable\deliverables\sram_layoutgen_step45_clean\technology\freepdk45\sp_lib\replica_cell_1rw.sp |
| replica_cell_2rw | replica_cell_2rw | vdd, gnd | True | E:\njust\keyan\SRAM Compiler_V2\OpenRAM-stable\deliverables\sram_layoutgen_step45_clean\technology\freepdk45\sp_lib\replica_cell_2rw.sp |
| sense_amp | sense_amp | vdd, gnd | True | E:\njust\keyan\SRAM Compiler_V2\OpenRAM-stable\deliverables\sram_layoutgen_step45_clean\technology\freepdk45\sp_lib\sense_amp.sp |
| tri_gate | tri_gate | vdd, gnd | True | E:\njust\keyan\SRAM Compiler_V2\OpenRAM-stable\deliverables\sram_layoutgen_step45_clean\technology\freepdk45\sp_lib\tri_gate.sp |
| write_driver | write_driver | vdd, gnd | True | E:\njust\keyan\SRAM Compiler_V2\OpenRAM-stable\deliverables\sram_layoutgen_step45_clean\technology\freepdk45\sp_lib\write_driver.sp |

## LEF / Tech Inventory

| asset type | pin info | routing info | path |
| --- | --- | --- | --- |
| drc_deck | True | True | E:\njust\keyan\SRAM Compiler_V2\OpenRAM-stable\deliverables\sram_layoutgen_step45_clean\technology\freepdk45\tech\freepdk45.lydrc |
| klayout_layer_props | True | True | E:\njust\keyan\SRAM Compiler_V2\OpenRAM-stable\deliverables\sram_layoutgen_step45_clean\technology\freepdk45\tech\freepdk45.lyp |
| klayout_tech | True | True | E:\njust\keyan\SRAM Compiler_V2\OpenRAM-stable\deliverables\sram_layoutgen_step45_clean\technology\freepdk45\tech\freepdk45.lyt |

## DRC / KLayout / Verification Inventory

| tool/deck | readonly | requires gds | used before | path |
| --- | --- | --- | --- | --- |
| verification_asset | False | False | True | E:\njust\keyan\SRAM Compiler_V2\OpenRAM-stable\deliverables\sram_layoutgen_step45_clean\build\openyield_hardcell_drc_baseline\cell_1rw_drc.log |
| drc_report | False | False | True | E:\njust\keyan\SRAM Compiler_V2\OpenRAM-stable\deliverables\sram_layoutgen_step45_clean\build\openyield_hardcell_drc_baseline\cell_1rw_drc.lyrdb |
| verification_asset | False | False | True | E:\njust\keyan\SRAM Compiler_V2\OpenRAM-stable\deliverables\sram_layoutgen_step45_clean\build\openyield_hardcell_drc_baseline\dummy_cell_1rw_drc.log |
| drc_report | False | False | True | E:\njust\keyan\SRAM Compiler_V2\OpenRAM-stable\deliverables\sram_layoutgen_step45_clean\build\openyield_hardcell_drc_baseline\dummy_cell_1rw_drc.lyrdb |
| verification_asset | False | False | True | E:\njust\keyan\SRAM Compiler_V2\OpenRAM-stable\deliverables\sram_layoutgen_step45_clean\build\openyield_hardcell_drc_baseline\replica_cell_1rw_drc.log |
| drc_report | False | False | True | E:\njust\keyan\SRAM Compiler_V2\OpenRAM-stable\deliverables\sram_layoutgen_step45_clean\build\openyield_hardcell_drc_baseline\replica_cell_1rw_drc.lyrdb |
| verification_asset | False | False | True | E:\njust\keyan\SRAM Compiler_V2\OpenRAM-stable\deliverables\sram_layoutgen_step45_clean\build\openyield_step4_final_smoke\2x16_wpr1\openyield_alternating_mx\standalone_altmx_drc.log |
| drc_report | False | False | True | E:\njust\keyan\SRAM Compiler_V2\OpenRAM-stable\deliverables\sram_layoutgen_step45_clean\build\openyield_step4_final_smoke\2x16_wpr1\openyield_alternating_mx\standalone_altmx_drc.lyrdb |
| verification_asset | False | False | True | E:\njust\keyan\SRAM Compiler_V2\OpenRAM-stable\deliverables\sram_layoutgen_step45_clean\build\openyield_storage_only_smoke_2x4_mx\storage_only_drc.log |
| drc_report | False | False | True | E:\njust\keyan\SRAM Compiler_V2\OpenRAM-stable\deliverables\sram_layoutgen_step45_clean\build\openyield_storage_only_smoke_2x4_mx\storage_only_drc.lyrdb |
| verification_asset | False | False | True | E:\njust\keyan\SRAM Compiler_V2\OpenRAM-stable\deliverables\sram_layoutgen_step45_clean\build\openyield_storage_only_smoke_2x4_mx\storage_only_drc_report.json |
| verification_asset | False | False | True | E:\njust\keyan\SRAM Compiler_V2\OpenRAM-stable\deliverables\sram_layoutgen_step45_clean\build\openyield_storage_only_smoke_2x4_mx\storage_only_drc_report.md |
| verification_asset | False | False | True | E:\njust\keyan\SRAM Compiler_V2\OpenRAM-stable\deliverables\sram_layoutgen_step45_clean\build\openyield_storage_only_smoke_2x4_stitched\storage_only_2x4_stitched_drc.log |
| drc_report | False | False | True | E:\njust\keyan\SRAM Compiler_V2\OpenRAM-stable\deliverables\sram_layoutgen_step45_clean\build\openyield_storage_only_smoke_2x4_stitched\storage_only_2x4_stitched_drc.lyrdb |
| verification_asset | False | False | True | E:\njust\keyan\SRAM Compiler_V2\OpenRAM-stable\deliverables\sram_layoutgen_step45_clean\build\openyield_storage_only_smoke_2x4_stitched\storage_only_drc.log |
| drc_report | False | False | True | E:\njust\keyan\SRAM Compiler_V2\OpenRAM-stable\deliverables\sram_layoutgen_step45_clean\build\openyield_storage_only_smoke_2x4_stitched\storage_only_drc.lyrdb |
| verification_asset | False | False | True | E:\njust\keyan\SRAM Compiler_V2\OpenRAM-stable\deliverables\sram_layoutgen_step45_clean\build\openyield_storage_only_smoke_2x4_stitched\storage_only_drc_report.json |
| verification_asset | False | False | True | E:\njust\keyan\SRAM Compiler_V2\OpenRAM-stable\deliverables\sram_layoutgen_step45_clean\build\openyield_storage_only_smoke_2x4_stitched\storage_only_drc_report.md |
| verification_asset | False | False | True | E:\njust\keyan\SRAM Compiler_V2\OpenRAM-stable\deliverables\sram_layoutgen_step45_clean\docs\openyield_drc_marker_classification_report.json |
| verification_asset | False | False | True | E:\njust\keyan\SRAM Compiler_V2\OpenRAM-stable\deliverables\sram_layoutgen_step45_clean\docs\openyield_drc_marker_classification_report.md |
| verification_asset | False | False | True | E:\njust\keyan\SRAM Compiler_V2\OpenRAM-stable\deliverables\sram_layoutgen_step45_clean\docs\openyield_hardcell_drc_baseline_report.json |
| verification_asset | False | False | True | E:\njust\keyan\SRAM Compiler_V2\OpenRAM-stable\deliverables\sram_layoutgen_step45_clean\docs\openyield_hardcell_drc_baseline_report.md |
| verification_asset | False | False | True | E:\njust\keyan\SRAM Compiler_V2\OpenRAM-stable\deliverables\sram_layoutgen_step45_clean\docs\openyield_storage_only_drc_smoke_report.json |
| verification_asset | False | False | True | E:\njust\keyan\SRAM Compiler_V2\OpenRAM-stable\deliverables\sram_layoutgen_step45_clean\docs\openyield_storage_only_drc_smoke_report.md |
| signoff_script_or_report | False | False | True | E:\njust\keyan\SRAM Compiler_V2\OpenRAM-stable\deliverables\sram_layoutgen_step45_clean\docs\SIGNOFF.md |
| signoff_script_or_report | True | True | False | E:\njust\keyan\SRAM Compiler_V2\OpenRAM-stable\deliverables\sram_layoutgen_step45_clean\examples\run_external_signoff.ps1 |
| verification_asset | False | False | False | E:\njust\keyan\SRAM Compiler_V2\OpenRAM-stable\deliverables\sram_layoutgen_step45_clean\scripts\__pycache__\openyield_drc_marker_classify.cpython-314.pyc |
| verification_asset | False | False | False | E:\njust\keyan\SRAM Compiler_V2\OpenRAM-stable\deliverables\sram_layoutgen_step45_clean\scripts\__pycache__\openyield_hardcell_drc_baseline.cpython-314.pyc |
| verification_asset | False | False | False | E:\njust\keyan\SRAM Compiler_V2\OpenRAM-stable\deliverables\sram_layoutgen_step45_clean\scripts\__pycache__\openyield_storage_only_drc_smoke.cpython-314.pyc |
| klayout_helper | True | True | False | E:\njust\keyan\SRAM Compiler_V2\OpenRAM-stable\deliverables\sram_layoutgen_step45_clean\scripts\klayout_gds_summary.rb |
| verification_asset | True | False | False | E:\njust\keyan\SRAM Compiler_V2\OpenRAM-stable\deliverables\sram_layoutgen_step45_clean\scripts\openyield_drc_marker_classify.py |
| verification_asset | True | False | False | E:\njust\keyan\SRAM Compiler_V2\OpenRAM-stable\deliverables\sram_layoutgen_step45_clean\scripts\openyield_hardcell_drc_baseline.py |
| verification_asset | True | False | False | E:\njust\keyan\SRAM Compiler_V2\OpenRAM-stable\deliverables\sram_layoutgen_step45_clean\scripts\openyield_storage_only_drc_smoke.py |
| signoff_script_or_report | False | False | False | E:\njust\keyan\SRAM Compiler_V2\OpenRAM-stable\deliverables\sram_layoutgen_step45_clean\sram_layoutgen\__pycache__\signoff.cpython-314.pyc |
| signoff_script_or_report | True | False | False | E:\njust\keyan\SRAM Compiler_V2\OpenRAM-stable\deliverables\sram_layoutgen_step45_clean\sram_layoutgen\signoff.py |
| drc_deck | True | True | False | E:\njust\keyan\SRAM Compiler_V2\OpenRAM-stable\deliverables\sram_layoutgen_step45_clean\technology\freepdk45\tech\freepdk45.lydrc |
| lvs_asset | False | False | False | E:\njust\keyan\SRAM Compiler_V2\OpenRAM-stable\deliverables\sram_layoutgen_step45_clean\technology\freepdk45\tech\freepdk45.lylvs |

## OpenRAM Generated Outputs

- output root: `E:\njust\keyan\SRAM Compiler_V2\OpenRAM-stable\deliverables\sram_layoutgen_step45_clean\build`
- total output files counted: `523`
- counts by extension: `{".gds": 292, ".json": 88, ".lef": 41, ".log": 7, ".lyrdb": 7, ".md": 47, ".sp": 41}`
- top output directories: `[["openyield_step4_final_smoke/2x16_wpr1/openyield_alternating_mx", 14], ["openyield_columnmux_standalone_smoke/columnmux_only", 12], ["openyield_columnmux_standalone_smoke/legacy_default", 12], ["openyield_columnmux_standalone_smoke/senseamp_plus_columnmux", 12], ["openyield_columnmux_standalone_smoke/storage_plus_senseamp_plus_columnmux", 12], ["openyield_read_write_path_semantic_review_legacy_default", 12], ["openyield_read_write_path_semantic_review_read_path_only", 12], ["openyield_read_write_path_semantic_review_read_write_path", 12], ["openyield_read_write_path_semantic_review_storage_plus_read_write_path", 12], ["openyield_read_write_path_semantic_review_write_path_only", 12], ["openyield_senseamp_standalone_legacy_default", 12], ["openyield_senseamp_standalone_senseamp_only", 12], ["openyield_senseamp_standalone_storage_plus_senseamp", 12], ["openyield_standalone_row_policy_legacy_default", 12], ["openyield_standalone_row_policy_openyield_all_r0", 12], ["openyield_standalone_row_policy_openyield_alternating_mx", 12], ["openyield_step4_final_smoke/2x16_wpr1/legacy_default", 12], ["openyield_step4_final_smoke/2x16_wpr1/openyield_all_r0", 12], ["openyield_step4_final_smoke/4x32_wpr2/legacy_default", 12], ["openyield_step4_final_smoke/4x32_wpr2/openyield_all_r0", 12]]`

Representative outputs:

| name | type | config | path |
| --- | --- | --- | --- |
| gen_col_mux_vdd_labeled | gds | - | E:\njust\keyan\SRAM Compiler_V2\OpenRAM-stable\deliverables\sram_layoutgen_step45_clean\build\openyield_colmux_repair\gen_col_mux_vdd_labeled.gds |
| columnmux_only.architecture | gds | - | E:\njust\keyan\SRAM Compiler_V2\OpenRAM-stable\deliverables\sram_layoutgen_step45_clean\build\openyield_columnmux_standalone_smoke\columnmux_only\columnmux_only.architecture.gds |
| columnmux_only.complete | gds | - | E:\njust\keyan\SRAM Compiler_V2\OpenRAM-stable\deliverables\sram_layoutgen_step45_clean\build\openyield_columnmux_standalone_smoke\columnmux_only\columnmux_only.complete.gds |
| columnmux_only.debug | gds | - | E:\njust\keyan\SRAM Compiler_V2\OpenRAM-stable\deliverables\sram_layoutgen_step45_clean\build\openyield_columnmux_standalone_smoke\columnmux_only\columnmux_only.debug.gds |
| columnmux_only | gds | - | E:\njust\keyan\SRAM Compiler_V2\OpenRAM-stable\deliverables\sram_layoutgen_step45_clean\build\openyield_columnmux_standalone_smoke\columnmux_only\columnmux_only.gds |
| columnmux_only.integration | gds | - | E:\njust\keyan\SRAM Compiler_V2\OpenRAM-stable\deliverables\sram_layoutgen_step45_clean\build\openyield_columnmux_standalone_smoke\columnmux_only\columnmux_only.integration.gds |
| columnmux_only.layout | json | - | E:\njust\keyan\SRAM Compiler_V2\OpenRAM-stable\deliverables\sram_layoutgen_step45_clean\build\openyield_columnmux_standalone_smoke\columnmux_only\columnmux_only.layout.json |
| columnmux_only | lef | - | E:\njust\keyan\SRAM Compiler_V2\OpenRAM-stable\deliverables\sram_layoutgen_step45_clean\build\openyield_columnmux_standalone_smoke\columnmux_only\columnmux_only.lef |
| columnmux_only.presentation | gds | - | E:\njust\keyan\SRAM Compiler_V2\OpenRAM-stable\deliverables\sram_layoutgen_step45_clean\build\openyield_columnmux_standalone_smoke\columnmux_only\columnmux_only.presentation.gds |
| columnmux_only.report | json | - | E:\njust\keyan\SRAM Compiler_V2\OpenRAM-stable\deliverables\sram_layoutgen_step45_clean\build\openyield_columnmux_standalone_smoke\columnmux_only\columnmux_only.report.json |
| columnmux_only.report | md | - | E:\njust\keyan\SRAM Compiler_V2\OpenRAM-stable\deliverables\sram_layoutgen_step45_clean\build\openyield_columnmux_standalone_smoke\columnmux_only\columnmux_only.report.md |
| columnmux_only.route_guides | gds | - | E:\njust\keyan\SRAM Compiler_V2\OpenRAM-stable\deliverables\sram_layoutgen_step45_clean\build\openyield_columnmux_standalone_smoke\columnmux_only\columnmux_only.route_guides.gds |
| columnmux_only | sp | - | E:\njust\keyan\SRAM Compiler_V2\OpenRAM-stable\deliverables\sram_layoutgen_step45_clean\build\openyield_columnmux_standalone_smoke\columnmux_only\columnmux_only.sp |
| legacy_default.architecture | gds | - | E:\njust\keyan\SRAM Compiler_V2\OpenRAM-stable\deliverables\sram_layoutgen_step45_clean\build\openyield_columnmux_standalone_smoke\legacy_default\legacy_default.architecture.gds |
| legacy_default.complete | gds | - | E:\njust\keyan\SRAM Compiler_V2\OpenRAM-stable\deliverables\sram_layoutgen_step45_clean\build\openyield_columnmux_standalone_smoke\legacy_default\legacy_default.complete.gds |
| legacy_default.debug | gds | - | E:\njust\keyan\SRAM Compiler_V2\OpenRAM-stable\deliverables\sram_layoutgen_step45_clean\build\openyield_columnmux_standalone_smoke\legacy_default\legacy_default.debug.gds |
| legacy_default | gds | - | E:\njust\keyan\SRAM Compiler_V2\OpenRAM-stable\deliverables\sram_layoutgen_step45_clean\build\openyield_columnmux_standalone_smoke\legacy_default\legacy_default.gds |
| legacy_default.integration | gds | - | E:\njust\keyan\SRAM Compiler_V2\OpenRAM-stable\deliverables\sram_layoutgen_step45_clean\build\openyield_columnmux_standalone_smoke\legacy_default\legacy_default.integration.gds |
| legacy_default.layout | json | - | E:\njust\keyan\SRAM Compiler_V2\OpenRAM-stable\deliverables\sram_layoutgen_step45_clean\build\openyield_columnmux_standalone_smoke\legacy_default\legacy_default.layout.json |
| legacy_default | lef | - | E:\njust\keyan\SRAM Compiler_V2\OpenRAM-stable\deliverables\sram_layoutgen_step45_clean\build\openyield_columnmux_standalone_smoke\legacy_default\legacy_default.lef |
| legacy_default.presentation | gds | - | E:\njust\keyan\SRAM Compiler_V2\OpenRAM-stable\deliverables\sram_layoutgen_step45_clean\build\openyield_columnmux_standalone_smoke\legacy_default\legacy_default.presentation.gds |
| legacy_default.report | json | - | E:\njust\keyan\SRAM Compiler_V2\OpenRAM-stable\deliverables\sram_layoutgen_step45_clean\build\openyield_columnmux_standalone_smoke\legacy_default\legacy_default.report.json |
| legacy_default.report | md | - | E:\njust\keyan\SRAM Compiler_V2\OpenRAM-stable\deliverables\sram_layoutgen_step45_clean\build\openyield_columnmux_standalone_smoke\legacy_default\legacy_default.report.md |
| legacy_default.route_guides | gds | - | E:\njust\keyan\SRAM Compiler_V2\OpenRAM-stable\deliverables\sram_layoutgen_step45_clean\build\openyield_columnmux_standalone_smoke\legacy_default\legacy_default.route_guides.gds |
| legacy_default | sp | - | E:\njust\keyan\SRAM Compiler_V2\OpenRAM-stable\deliverables\sram_layoutgen_step45_clean\build\openyield_columnmux_standalone_smoke\legacy_default\legacy_default.sp |
| senseamp_plus_columnmux.architecture | gds | - | E:\njust\keyan\SRAM Compiler_V2\OpenRAM-stable\deliverables\sram_layoutgen_step45_clean\build\openyield_columnmux_standalone_smoke\senseamp_plus_columnmux\senseamp_plus_columnmux.architecture.gds |
| senseamp_plus_columnmux.complete | gds | - | E:\njust\keyan\SRAM Compiler_V2\OpenRAM-stable\deliverables\sram_layoutgen_step45_clean\build\openyield_columnmux_standalone_smoke\senseamp_plus_columnmux\senseamp_plus_columnmux.complete.gds |
| senseamp_plus_columnmux.debug | gds | - | E:\njust\keyan\SRAM Compiler_V2\OpenRAM-stable\deliverables\sram_layoutgen_step45_clean\build\openyield_columnmux_standalone_smoke\senseamp_plus_columnmux\senseamp_plus_columnmux.debug.gds |
| senseamp_plus_columnmux | gds | - | E:\njust\keyan\SRAM Compiler_V2\OpenRAM-stable\deliverables\sram_layoutgen_step45_clean\build\openyield_columnmux_standalone_smoke\senseamp_plus_columnmux\senseamp_plus_columnmux.gds |
| senseamp_plus_columnmux.integration | gds | - | E:\njust\keyan\SRAM Compiler_V2\OpenRAM-stable\deliverables\sram_layoutgen_step45_clean\build\openyield_columnmux_standalone_smoke\senseamp_plus_columnmux\senseamp_plus_columnmux.integration.gds |
| senseamp_plus_columnmux.layout | json | - | E:\njust\keyan\SRAM Compiler_V2\OpenRAM-stable\deliverables\sram_layoutgen_step45_clean\build\openyield_columnmux_standalone_smoke\senseamp_plus_columnmux\senseamp_plus_columnmux.layout.json |
| senseamp_plus_columnmux | lef | - | E:\njust\keyan\SRAM Compiler_V2\OpenRAM-stable\deliverables\sram_layoutgen_step45_clean\build\openyield_columnmux_standalone_smoke\senseamp_plus_columnmux\senseamp_plus_columnmux.lef |
| senseamp_plus_columnmux.presentation | gds | - | E:\njust\keyan\SRAM Compiler_V2\OpenRAM-stable\deliverables\sram_layoutgen_step45_clean\build\openyield_columnmux_standalone_smoke\senseamp_plus_columnmux\senseamp_plus_columnmux.presentation.gds |
| senseamp_plus_columnmux.report | json | - | E:\njust\keyan\SRAM Compiler_V2\OpenRAM-stable\deliverables\sram_layoutgen_step45_clean\build\openyield_columnmux_standalone_smoke\senseamp_plus_columnmux\senseamp_plus_columnmux.report.json |
| senseamp_plus_columnmux.report | md | - | E:\njust\keyan\SRAM Compiler_V2\OpenRAM-stable\deliverables\sram_layoutgen_step45_clean\build\openyield_columnmux_standalone_smoke\senseamp_plus_columnmux\senseamp_plus_columnmux.report.md |
| senseamp_plus_columnmux.route_guides | gds | - | E:\njust\keyan\SRAM Compiler_V2\OpenRAM-stable\deliverables\sram_layoutgen_step45_clean\build\openyield_columnmux_standalone_smoke\senseamp_plus_columnmux\senseamp_plus_columnmux.route_guides.gds |
| senseamp_plus_columnmux | sp | - | E:\njust\keyan\SRAM Compiler_V2\OpenRAM-stable\deliverables\sram_layoutgen_step45_clean\build\openyield_columnmux_standalone_smoke\senseamp_plus_columnmux\senseamp_plus_columnmux.sp |
| storage_plus_senseamp_plus_columnmux.architecture | gds | - | E:\njust\keyan\SRAM Compiler_V2\OpenRAM-stable\deliverables\sram_layoutgen_step45_clean\build\openyield_columnmux_standalone_smoke\storage_plus_senseamp_plus_columnmux\storage_plus_senseamp_plus_columnmux.architecture.gds |
| storage_plus_senseamp_plus_columnmux.complete | gds | - | E:\njust\keyan\SRAM Compiler_V2\OpenRAM-stable\deliverables\sram_layoutgen_step45_clean\build\openyield_columnmux_standalone_smoke\storage_plus_senseamp_plus_columnmux\storage_plus_senseamp_plus_columnmux.complete.gds |
| storage_plus_senseamp_plus_columnmux.debug | gds | - | E:\njust\keyan\SRAM Compiler_V2\OpenRAM-stable\deliverables\sram_layoutgen_step45_clean\build\openyield_columnmux_standalone_smoke\storage_plus_senseamp_plus_columnmux\storage_plus_senseamp_plus_columnmux.debug.gds |
| storage_plus_senseamp_plus_columnmux | gds | - | E:\njust\keyan\SRAM Compiler_V2\OpenRAM-stable\deliverables\sram_layoutgen_step45_clean\build\openyield_columnmux_standalone_smoke\storage_plus_senseamp_plus_columnmux\storage_plus_senseamp_plus_columnmux.gds |
| storage_plus_senseamp_plus_columnmux.integration | gds | - | E:\njust\keyan\SRAM Compiler_V2\OpenRAM-stable\deliverables\sram_layoutgen_step45_clean\build\openyield_columnmux_standalone_smoke\storage_plus_senseamp_plus_columnmux\storage_plus_senseamp_plus_columnmux.integration.gds |
| storage_plus_senseamp_plus_columnmux.layout | json | - | E:\njust\keyan\SRAM Compiler_V2\OpenRAM-stable\deliverables\sram_layoutgen_step45_clean\build\openyield_columnmux_standalone_smoke\storage_plus_senseamp_plus_columnmux\storage_plus_senseamp_plus_columnmux.layout.json |
| storage_plus_senseamp_plus_columnmux | lef | - | E:\njust\keyan\SRAM Compiler_V2\OpenRAM-stable\deliverables\sram_layoutgen_step45_clean\build\openyield_columnmux_standalone_smoke\storage_plus_senseamp_plus_columnmux\storage_plus_senseamp_plus_columnmux.lef |
| storage_plus_senseamp_plus_columnmux.presentation | gds | - | E:\njust\keyan\SRAM Compiler_V2\OpenRAM-stable\deliverables\sram_layoutgen_step45_clean\build\openyield_columnmux_standalone_smoke\storage_plus_senseamp_plus_columnmux\storage_plus_senseamp_plus_columnmux.presentation.gds |
| storage_plus_senseamp_plus_columnmux.report | json | - | E:\njust\keyan\SRAM Compiler_V2\OpenRAM-stable\deliverables\sram_layoutgen_step45_clean\build\openyield_columnmux_standalone_smoke\storage_plus_senseamp_plus_columnmux\storage_plus_senseamp_plus_columnmux.report.json |
| storage_plus_senseamp_plus_columnmux.report | md | - | E:\njust\keyan\SRAM Compiler_V2\OpenRAM-stable\deliverables\sram_layoutgen_step45_clean\build\openyield_columnmux_standalone_smoke\storage_plus_senseamp_plus_columnmux\storage_plus_senseamp_plus_columnmux.report.md |
| storage_plus_senseamp_plus_columnmux.route_guides | gds | - | E:\njust\keyan\SRAM Compiler_V2\OpenRAM-stable\deliverables\sram_layoutgen_step45_clean\build\openyield_columnmux_standalone_smoke\storage_plus_senseamp_plus_columnmux\storage_plus_senseamp_plus_columnmux.route_guides.gds |
| storage_plus_senseamp_plus_columnmux | sp | - | E:\njust\keyan\SRAM Compiler_V2\OpenRAM-stable\deliverables\sram_layoutgen_step45_clean\build\openyield_columnmux_standalone_smoke\storage_plus_senseamp_plus_columnmux\storage_plus_senseamp_plus_columnmux.sp |
| cell_1rw_drc | log | - | E:\njust\keyan\SRAM Compiler_V2\OpenRAM-stable\deliverables\sram_layoutgen_step45_clean\build\openyield_hardcell_drc_baseline\cell_1rw_drc.log |
| cell_1rw_drc | lyrdb | - | E:\njust\keyan\SRAM Compiler_V2\OpenRAM-stable\deliverables\sram_layoutgen_step45_clean\build\openyield_hardcell_drc_baseline\cell_1rw_drc.lyrdb |
| dummy_cell_1rw_drc | log | - | E:\njust\keyan\SRAM Compiler_V2\OpenRAM-stable\deliverables\sram_layoutgen_step45_clean\build\openyield_hardcell_drc_baseline\dummy_cell_1rw_drc.log |
| dummy_cell_1rw_drc | lyrdb | - | E:\njust\keyan\SRAM Compiler_V2\OpenRAM-stable\deliverables\sram_layoutgen_step45_clean\build\openyield_hardcell_drc_baseline\dummy_cell_1rw_drc.lyrdb |
| replica_cell_1rw_drc | log | - | E:\njust\keyan\SRAM Compiler_V2\OpenRAM-stable\deliverables\sram_layoutgen_step45_clean\build\openyield_hardcell_drc_baseline\replica_cell_1rw_drc.log |
| replica_cell_1rw_drc | lyrdb | - | E:\njust\keyan\SRAM Compiler_V2\OpenRAM-stable\deliverables\sram_layoutgen_step45_clean\build\openyield_hardcell_drc_baseline\replica_cell_1rw_drc.lyrdb |
| sram_4x32_wpr2_fd45.architecture | gds | wpr2 | E:\njust\keyan\SRAM Compiler_V2\OpenRAM-stable\deliverables\sram_layoutgen_step45_clean\build\openyield_read_write_path_semantic_review_legacy_default\sram_4x32_wpr2_fd45.architecture.gds |
| sram_4x32_wpr2_fd45.complete | gds | wpr2 | E:\njust\keyan\SRAM Compiler_V2\OpenRAM-stable\deliverables\sram_layoutgen_step45_clean\build\openyield_read_write_path_semantic_review_legacy_default\sram_4x32_wpr2_fd45.complete.gds |
| sram_4x32_wpr2_fd45.debug | gds | wpr2 | E:\njust\keyan\SRAM Compiler_V2\OpenRAM-stable\deliverables\sram_layoutgen_step45_clean\build\openyield_read_write_path_semantic_review_legacy_default\sram_4x32_wpr2_fd45.debug.gds |
| sram_4x32_wpr2_fd45 | gds | wpr2 | E:\njust\keyan\SRAM Compiler_V2\OpenRAM-stable\deliverables\sram_layoutgen_step45_clean\build\openyield_read_write_path_semantic_review_legacy_default\sram_4x32_wpr2_fd45.gds |
| sram_4x32_wpr2_fd45.integration | gds | wpr2 | E:\njust\keyan\SRAM Compiler_V2\OpenRAM-stable\deliverables\sram_layoutgen_step45_clean\build\openyield_read_write_path_semantic_review_legacy_default\sram_4x32_wpr2_fd45.integration.gds |

## Layout Writer / Routing / Standalone Readonly Inventory

| component | inspected | modified | role | path |
| --- | --- | --- | --- | --- |
| standalone | True | False | top-level generator / integration entry | E:\njust\keyan\SRAM Compiler_V2\OpenRAM-stable\deliverables\sram_layoutgen_step45_clean\sram_layoutgen\standalone.py |
| gds_writer | True | False | GDS emission | E:\njust\keyan\SRAM Compiler_V2\OpenRAM-stable\deliverables\sram_layoutgen_step45_clean\sram_layoutgen\gds_writer.py |
| lef_writer | True | False | LEF writer | E:\njust\keyan\SRAM Compiler_V2\OpenRAM-stable\deliverables\sram_layoutgen_step45_clean\sram_layoutgen\lef_writer.py |
| routing | True | False | geometry primitives used by routing/layout | E:\njust\keyan\SRAM Compiler_V2\OpenRAM-stable\deliverables\sram_layoutgen_step45_clean\sram_layoutgen\geometry.py |
| routing | True | False | route/connectivity verification entry | E:\njust\keyan\SRAM Compiler_V2\OpenRAM-stable\deliverables\sram_layoutgen_step45_clean\sram_layoutgen\verifier.py |
| signoff | True | False | external DRC/LVS helpers | E:\njust\keyan\SRAM Compiler_V2\OpenRAM-stable\deliverables\sram_layoutgen_step45_clean\sram_layoutgen\signoff.py |
| placement | True | False | OpenRAM-style placement | E:\njust\keyan\SRAM Compiler_V2\OpenRAM-stable\deliverables\sram_layoutgen_step45_clean\sram_layoutgen\openram_placement.py |
| power_stitch_script | True | False | storage-only smoke/export | E:\njust\keyan\SRAM Compiler_V2\OpenRAM-stable\deliverables\sram_layoutgen_step45_clean\scripts\openyield_storage_only_gds_smoke.py |
| power_stitch_script | True | False | storage-only DRC smoke | E:\njust\keyan\SRAM Compiler_V2\OpenRAM-stable\deliverables\sram_layoutgen_step45_clean\scripts\openyield_storage_only_drc_smoke.py |
| time_control_readonly | True | False | TIME/control boundary summary | E:\njust\keyan\SRAM Compiler_V2\OpenRAM-stable\deliverables\sram_layoutgen_step45_clean\scripts\openyield_time_control_final_boundary_summary.py |

## Missing Assets

- none

## Usable Assets For Next Proof

```json
{
  "hardcell_focus_macros": [
    {
      "macro_name": "cell_1rw",
      "gds_path": "E:\\njust\\keyan\\SRAM Compiler_V2\\OpenRAM-stable\\deliverables\\sram_layoutgen_step45_clean\\technology\\freepdk45\\gds_lib\\cell_1rw.gds"
    },
    {
      "macro_name": "dff",
      "gds_path": "E:\\njust\\keyan\\SRAM Compiler_V2\\OpenRAM-stable\\deliverables\\sram_layoutgen_step45_clean\\technology\\freepdk45\\gds_lib\\dff.gds"
    },
    {
      "macro_name": "dummy_cell_1rw",
      "gds_path": "E:\\njust\\keyan\\SRAM Compiler_V2\\OpenRAM-stable\\deliverables\\sram_layoutgen_step45_clean\\technology\\freepdk45\\gds_lib\\dummy_cell_1rw.gds"
    },
    {
      "macro_name": "gen_col_mux",
      "gds_path": "E:\\njust\\keyan\\SRAM Compiler_V2\\OpenRAM-stable\\deliverables\\sram_layoutgen_step45_clean\\technology\\freepdk45\\gds_lib\\gen_col_mux.gds"
    },
    {
      "macro_name": "gen_delay_inv",
      "gds_path": "E:\\njust\\keyan\\SRAM Compiler_V2\\OpenRAM-stable\\deliverables\\sram_layoutgen_step45_clean\\technology\\freepdk45\\gds_lib\\gen_delay_inv.gds"
    },
    {
      "macro_name": "gen_inv",
      "gds_path": "E:\\njust\\keyan\\SRAM Compiler_V2\\OpenRAM-stable\\deliverables\\sram_layoutgen_step45_clean\\technology\\freepdk45\\gds_lib\\gen_inv.gds"
    },
    {
      "macro_name": "gen_nand2",
      "gds_path": "E:\\njust\\keyan\\SRAM Compiler_V2\\OpenRAM-stable\\deliverables\\sram_layoutgen_step45_clean\\technology\\freepdk45\\gds_lib\\gen_nand2.gds"
    },
    {
      "macro_name": "gen_precharge",
      "gds_path": "E:\\njust\\keyan\\SRAM Compiler_V2\\OpenRAM-stable\\deliverables\\sram_layoutgen_step45_clean\\technology\\freepdk45\\gds_lib\\gen_precharge.gds"
    },
    {
      "macro_name": "gen_wl_driver",
      "gds_path": "E:\\njust\\keyan\\SRAM Compiler_V2\\OpenRAM-stable\\deliverables\\sram_layoutgen_step45_clean\\technology\\freepdk45\\gds_lib\\gen_wl_driver.gds"
    },
    {
      "macro_name": "gen_col_mux",
      "gds_path": "E:\\njust\\keyan\\SRAM Compiler_V2\\OpenRAM-stable\\deliverables\\sram_layoutgen_step45_clean\\technology\\freepdk45\\gds_lib\\openram_replacements\\gen_col_mux.gds"
    },
    {
      "macro_name": "gen_delay_inv",
      "gds_path": "E:\\njust\\keyan\\SRAM Compiler_V2\\OpenRAM-stable\\deliverables\\sram_layoutgen_step45_clean\\technology\\freepdk45\\gds_lib\\openram_replacements\\gen_delay_inv.gds"
    },
    {
      "macro_name": "gen_inv",
      "gds_path": "E:\\njust\\keyan\\SRAM Compiler_V2\\OpenRAM-stable\\deliverables\\sram_layoutgen_step45_clean\\technology\\freepdk45\\gds_lib\\openram_replacements\\gen_inv.gds"
    },
    {
      "macro_name": "gen_nand2",
      "gds_path": "E:\\njust\\keyan\\SRAM Compiler_V2\\OpenRAM-stable\\deliverables\\sram_layoutgen_step45_clean\\technology\\freepdk45\\gds_lib\\openram_replacements\\gen_nand2.gds"
    },
    {
      "macro_name": "gen_precharge",
      "gds_path": "E:\\njust\\keyan\\SRAM Compiler_V2\\OpenRAM-stable\\deliverables\\sram_layoutgen_step45_clean\\technology\\freepdk45\\gds_lib\\openram_replacements\\gen_precharge.gds"
    },
    {
      "macro_name": "gen_wl_driver",
      "gds_path": "E:\\njust\\keyan\\SRAM Compiler_V2\\OpenRAM-stable\\deliverables\\sram_layoutgen_step45_clean\\technology\\freepdk45\\gds_lib\\openram_replacements\\gen_wl_driver.gds"
    },
    {
      "macro_name": "gen_col_mux_vdd_labeled",
      "gds_path": "E:\\njust\\keyan\\SRAM Compiler_V2\\OpenRAM-stable\\deliverables\\sram_layoutgen_step45_clean\\technology\\freepdk45\\gds_lib\\openyield_repaired\\gen_col_mux_vdd_labeled.gds"
    },
    {
      "macro_name": "replica_cell_1rw",
      "gds_path": "E:\\njust\\keyan\\SRAM Compiler_V2\\OpenRAM-stable\\deliverables\\sram_layoutgen_step45_clean\\technology\\freepdk45\\gds_lib\\replica_cell_1rw.gds"
    },
    {
      "macro_name": "sense_amp",
      "gds_path": "E:\\njust\\keyan\\SRAM Compiler_V2\\OpenRAM-stable\\deliverables\\sram_layoutgen_step45_clean\\technology\\freepdk45\\gds_lib\\sense_amp.gds"
    },
    {
      "macro_name": "write_driver",
      "gds_path": "E:\\njust\\keyan\\SRAM Compiler_V2\\OpenRAM-stable\\deliverables\\sram_layoutgen_step45_clean\\technology\\freepdk45\\gds_lib\\write_driver.gds"
    }
  ],
  "drc_decks": [
    {
      "tool_or_deck": "drc_deck",
      "path": "E:\\njust\\keyan\\SRAM Compiler_V2\\OpenRAM-stable\\deliverables\\sram_layoutgen_step45_clean\\technology\\freepdk45\\tech\\freepdk45.lydrc"
    }
  ],
  "tech_assets": [
    {
      "asset_type": "drc_deck",
      "path": "E:\\njust\\keyan\\SRAM Compiler_V2\\OpenRAM-stable\\deliverables\\sram_layoutgen_step45_clean\\technology\\freepdk45\\tech\\freepdk45.lydrc"
    },
    {
      "asset_type": "klayout_layer_props",
      "path": "E:\\njust\\keyan\\SRAM Compiler_V2\\OpenRAM-stable\\deliverables\\sram_layoutgen_step45_clean\\technology\\freepdk45\\tech\\freepdk45.lyp"
    },
    {
      "asset_type": "klayout_tech",
      "path": "E:\\njust\\keyan\\SRAM Compiler_V2\\OpenRAM-stable\\deliverables\\sram_layoutgen_step45_clean\\technology\\freepdk45\\tech\\freepdk45.lyt"
    }
  ],
  "layout_entrypoints": [
    {
      "component": "standalone",
      "path": "E:\\njust\\keyan\\SRAM Compiler_V2\\OpenRAM-stable\\deliverables\\sram_layoutgen_step45_clean\\sram_layoutgen\\standalone.py"
    },
    {
      "component": "gds_writer",
      "path": "E:\\njust\\keyan\\SRAM Compiler_V2\\OpenRAM-stable\\deliverables\\sram_layoutgen_step45_clean\\sram_layoutgen\\gds_writer.py"
    },
    {
      "component": "lef_writer",
      "path": "E:\\njust\\keyan\\SRAM Compiler_V2\\OpenRAM-stable\\deliverables\\sram_layoutgen_step45_clean\\sram_layoutgen\\lef_writer.py"
    },
    {
      "component": "routing",
      "path": "E:\\njust\\keyan\\SRAM Compiler_V2\\OpenRAM-stable\\deliverables\\sram_layoutgen_step45_clean\\sram_layoutgen\\geometry.py"
    },
    {
      "component": "routing",
      "path": "E:\\njust\\keyan\\SRAM Compiler_V2\\OpenRAM-stable\\deliverables\\sram_layoutgen_step45_clean\\sram_layoutgen\\verifier.py"
    },
    {
      "component": "signoff",
      "path": "E:\\njust\\keyan\\SRAM Compiler_V2\\OpenRAM-stable\\deliverables\\sram_layoutgen_step45_clean\\sram_layoutgen\\signoff.py"
    },
    {
      "component": "placement",
      "path": "E:\\njust\\keyan\\SRAM Compiler_V2\\OpenRAM-stable\\deliverables\\sram_layoutgen_step45_clean\\sram_layoutgen\\openram_placement.py"
    },
    {
      "component": "power_stitch_script",
      "path": "E:\\njust\\keyan\\SRAM Compiler_V2\\OpenRAM-stable\\deliverables\\sram_layoutgen_step45_clean\\scripts\\openyield_storage_only_gds_smoke.py"
    },
    {
      "component": "power_stitch_script",
      "path": "E:\\njust\\keyan\\SRAM Compiler_V2\\OpenRAM-stable\\deliverables\\sram_layoutgen_step45_clean\\scripts\\openyield_storage_only_drc_smoke.py"
    },
    {
      "component": "time_control_readonly",
      "path": "E:\\njust\\keyan\\SRAM Compiler_V2\\OpenRAM-stable\\deliverables\\sram_layoutgen_step45_clean\\scripts\\openyield_time_control_final_boundary_summary.py"
    }
  ],
  "time_metadata_reports": [
    {
      "name": "openyield_time_control_abstract_floorplan_payload_report.json",
      "path": "E:\\njust\\keyan\\SRAM Compiler_V2\\OpenRAM-stable\\deliverables\\sram_layoutgen_step45_clean\\docs\\openyield_time_control_abstract_floorplan_payload_report.json",
      "kind": "time_control_report"
    },
    {
      "name": "openyield_time_control_builder_output_regression_report.json",
      "path": "E:\\njust\\keyan\\SRAM Compiler_V2\\OpenRAM-stable\\deliverables\\sram_layoutgen_step45_clean\\docs\\openyield_time_control_builder_output_regression_report.json",
      "kind": "time_control_report"
    },
    {
      "name": "openyield_time_control_closure_unblock_report.json",
      "path": "E:\\njust\\keyan\\SRAM Compiler_V2\\OpenRAM-stable\\deliverables\\sram_layoutgen_step45_clean\\docs\\openyield_time_control_closure_unblock_report.json",
      "kind": "time_control_report"
    },
    {
      "name": "openyield_time_control_consumer_contract_report.json",
      "path": "E:\\njust\\keyan\\SRAM Compiler_V2\\OpenRAM-stable\\deliverables\\sram_layoutgen_step45_clean\\docs\\openyield_time_control_consumer_contract_report.json",
      "kind": "time_control_report"
    },
    {
      "name": "openyield_time_control_decomposition_report.json",
      "path": "E:\\njust\\keyan\\SRAM Compiler_V2\\OpenRAM-stable\\deliverables\\sram_layoutgen_step45_clean\\docs\\openyield_time_control_decomposition_report.json",
      "kind": "time_control_report"
    },
    {
      "name": "openyield_time_control_evidence_crossing_bundle_report.json",
      "path": "E:\\njust\\keyan\\SRAM Compiler_V2\\OpenRAM-stable\\deliverables\\sram_layoutgen_step45_clean\\docs\\openyield_time_control_evidence_crossing_bundle_report.json",
      "kind": "time_control_report"
    },
    {
      "name": "openyield_time_control_experimental_contract_report.json",
      "path": "E:\\njust\\keyan\\SRAM Compiler_V2\\OpenRAM-stable\\deliverables\\sram_layoutgen_step45_clean\\docs\\openyield_time_control_experimental_contract_report.json",
      "kind": "time_control_report"
    },
    {
      "name": "openyield_time_control_fast_bundle_report.json",
      "path": "E:\\njust\\keyan\\SRAM Compiler_V2\\OpenRAM-stable\\deliverables\\sram_layoutgen_step45_clean\\docs\\openyield_time_control_fast_bundle_report.json",
      "kind": "time_control_report"
    },
    {
      "name": "openyield_time_control_final_boundary_summary_report.json",
      "path": "E:\\njust\\keyan\\SRAM Compiler_V2\\OpenRAM-stable\\deliverables\\sram_layoutgen_step45_clean\\docs\\openyield_time_control_final_boundary_summary_report.json",
      "kind": "time_control_report"
    },
    {
      "name": "openyield_time_control_generated_logic_contract_report.json",
      "path": "E:\\njust\\keyan\\SRAM Compiler_V2\\OpenRAM-stable\\deliverables\\sram_layoutgen_step45_clean\\docs\\openyield_time_control_generated_logic_contract_report.json",
      "kind": "time_control_report"
    },
    {
      "name": "openyield_time_control_goal_progress_audit_report.json",
      "path": "E:\\njust\\keyan\\SRAM Compiler_V2\\OpenRAM-stable\\deliverables\\sram_layoutgen_step45_clean\\docs\\openyield_time_control_goal_progress_audit_report.json",
      "kind": "time_control_report"
    },
    {
      "name": "openyield_time_control_metadata_closure_report.json",
      "path": "E:\\njust\\keyan\\SRAM Compiler_V2\\OpenRAM-stable\\deliverables\\sram_layoutgen_step45_clean\\docs\\openyield_time_control_metadata_closure_report.json",
      "kind": "time_control_report"
    }
  ]
}
```

## Ranked Next Readonly Proof Tasks

| rank | task | ready | reason |
| --- | --- | --- | --- |
| 1 | hardcell_power_rail_continuity_readonly_audit | True | Hardcell GDS plus technology and DRC deck are present. |
| 2 | time_control_leaf_bbox_pin_side_inventory | True | Hardcell GDS and pin labels are present for readonly geometry inventory. |
| 3 | time_control_composite_internal_placement_feasibility_audit | True | Placement readonly entrypoints and tech assets are locatable. |
| 4 | time_control_route_obstacle_inventory | True | Routing-related code and tech assets are locatable. |
| 5 | delay_chain_timing_metadata_inventory | True | TIME/control metadata reports already exist for readonly follow-up. |

## Hardcell Power Rail Continuity Audit Inputs

```json
{
  "tech_dir": "E:\\njust\\keyan\\SRAM Compiler_V2\\OpenRAM-stable\\deliverables\\sram_layoutgen_step45_clean\\technology\\freepdk45",
  "drc_decks": [
    "E:\\njust\\keyan\\SRAM Compiler_V2\\OpenRAM-stable\\deliverables\\sram_layoutgen_step45_clean\\technology\\freepdk45\\tech\\freepdk45.lydrc"
  ],
  "macro_gds_inputs": [
    {
      "macro_name": "cell_1rw",
      "gds_path": "E:\\njust\\keyan\\SRAM Compiler_V2\\OpenRAM-stable\\deliverables\\sram_layoutgen_step45_clean\\technology\\freepdk45\\gds_lib\\cell_1rw.gds"
    },
    {
      "macro_name": "dummy_cell_1rw",
      "gds_path": "E:\\njust\\keyan\\SRAM Compiler_V2\\OpenRAM-stable\\deliverables\\sram_layoutgen_step45_clean\\technology\\freepdk45\\gds_lib\\dummy_cell_1rw.gds"
    },
    {
      "macro_name": "gen_col_mux",
      "gds_path": "E:\\njust\\keyan\\SRAM Compiler_V2\\OpenRAM-stable\\deliverables\\sram_layoutgen_step45_clean\\technology\\freepdk45\\gds_lib\\gen_col_mux.gds"
    },
    {
      "macro_name": "gen_wl_driver",
      "gds_path": "E:\\njust\\keyan\\SRAM Compiler_V2\\OpenRAM-stable\\deliverables\\sram_layoutgen_step45_clean\\technology\\freepdk45\\gds_lib\\gen_wl_driver.gds"
    },
    {
      "macro_name": "gen_col_mux",
      "gds_path": "E:\\njust\\keyan\\SRAM Compiler_V2\\OpenRAM-stable\\deliverables\\sram_layoutgen_step45_clean\\technology\\freepdk45\\gds_lib\\openram_replacements\\gen_col_mux.gds"
    },
    {
      "macro_name": "gen_wl_driver",
      "gds_path": "E:\\njust\\keyan\\SRAM Compiler_V2\\OpenRAM-stable\\deliverables\\sram_layoutgen_step45_clean\\technology\\freepdk45\\gds_lib\\openram_replacements\\gen_wl_driver.gds"
    },
    {
      "macro_name": "replica_cell_1rw",
      "gds_path": "E:\\njust\\keyan\\SRAM Compiler_V2\\OpenRAM-stable\\deliverables\\sram_layoutgen_step45_clean\\technology\\freepdk45\\gds_lib\\replica_cell_1rw.gds"
    },
    {
      "macro_name": "sense_amp",
      "gds_path": "E:\\njust\\keyan\\SRAM Compiler_V2\\OpenRAM-stable\\deliverables\\sram_layoutgen_step45_clean\\technology\\freepdk45\\gds_lib\\sense_amp.gds"
    },
    {
      "macro_name": "write_driver",
      "gds_path": "E:\\njust\\keyan\\SRAM Compiler_V2\\OpenRAM-stable\\deliverables\\sram_layoutgen_step45_clean\\technology\\freepdk45\\gds_lib\\write_driver.gds"
    }
  ]
}
```

## Boundary Assertions

```json
{
  "standalone_modified": false,
  "routing_modified": false,
  "gds_writer_modified": false,
  "legacy_path_unchanged": true
}
```