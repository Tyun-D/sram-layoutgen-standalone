# OpenYield Generated Logic Model Recovery Report

- Scope: `recover_generated_logic_spice_or_timing_model_inventory`
- Repo root: `E:\njust\keyan\SRAM Compiler_V2\OpenRAM-stable\deliverables\sram_layoutgen_step45_clean`
- Tech dir: `E:\njust\keyan\SRAM Compiler_V2\OpenRAM-stable\deliverables\sram_layoutgen_step45_clean\technology\freepdk45`

## Audit Summary

```json
{
  "generated_logic_model_recovery_inventory_available": true,
  "all_p0_macros_analyzed": true,
  "all_repo_model_sources_searched": true,
  "usable_model_found_for_all_p0": false,
  "recoverable_source_found_for_all_p0": true,
  "characterization_required_for_any_p0": true,
  "can_enter_model_characterization_plan": true,
  "can_enter_delay_chain_testbench_plan": true,
  "can_enter_timing_proof_now": false,
  "can_enter_physical_timing_closure_now": false,
  "can_enter_physical_routing_now": false,
  "can_enter_physical_placement_now": false,
  "can_generate_time_control_gds_now": false,
  "can_modify_standalone_now": false
}
```

## Searched Roots And Extensions

```json
{
  "searched_roots": [
    "E:\\njust\\keyan\\SRAM Compiler_V2\\OpenRAM-stable\\deliverables\\sram_layoutgen_step45_clean\\technology\\freepdk45",
    "E:\\njust\\keyan\\SRAM Compiler_V2\\OpenRAM-stable\\deliverables\\sram_layoutgen_step45_clean\\technology\\freepdk45\\gds_lib",
    "E:\\njust\\keyan\\SRAM Compiler_V2\\OpenRAM-stable\\deliverables\\sram_layoutgen_step45_clean\\technology\\freepdk45\\gds_lib\\openram_replacements",
    "E:\\njust\\keyan\\SRAM Compiler_V2\\OpenRAM-stable\\deliverables\\sram_layoutgen_step45_clean\\technology\\freepdk45\\gds_lib\\openyield_repaired",
    "E:\\njust\\keyan\\SRAM Compiler_V2\\OpenRAM-stable\\deliverables\\sram_layoutgen_step45_clean\\technology\\freepdk45\\sp_lib",
    "E:\\njust\\keyan\\SRAM Compiler_V2\\OpenRAM-stable\\deliverables\\sram_layoutgen_step45_clean\\technology\\freepdk45\\tech",
    "E:\\njust\\keyan\\SRAM Compiler_V2\\OpenRAM-stable\\deliverables\\sram_layoutgen_step45_clean\\sram_layoutgen",
    "E:\\njust\\keyan\\SRAM Compiler_V2\\OpenRAM-stable\\deliverables\\sram_layoutgen_step45_clean\\scripts",
    "E:\\njust\\keyan\\SRAM Compiler_V2\\OpenRAM-stable\\deliverables\\sram_layoutgen_step45_clean\\docs",
    "E:\\njust\\keyan\\SRAM Compiler_V2\\OpenRAM-stable\\deliverables\\sram_layoutgen_step45_clean\\build",
    "E:\\njust\\keyan\\SRAM Compiler_V2\\OpenRAM-stable\\third_party\\OpenYield"
  ],
  "searched_extensions": [
    ".cdl",
    ".gds",
    ".json",
    ".lef",
    ".lib",
    ".log",
    ".md",
    ".net",
    ".py",
    ".sp",
    ".spi",
    ".spice",
    ".tcl"
  ]
}
```

## P0 Generated Logic Model Inventory

| macro | decision | spice | lib | generator | recover_from_repo | next_action |
| --- | --- | --- | --- | --- | --- | --- |
| gen_inv | recoverable_from_generator_source | False | False | True | partial | materialize_transistor_level_netlist_then_characterize |
| gen_nand2 | recoverable_from_generator_source | False | False | True | partial | materialize_transistor_level_netlist_then_characterize |
| gen_delay_inv | recoverable_from_generator_source | False | False | True | partial | materialize_transistor_level_netlist_then_characterize |

## Secondary Macro Model Inventory

| macro | decision | spice | lib | recover_from_repo | next_action |
| --- | --- | --- | --- | --- | --- |
| gen_precharge | metadata_only_no_recovery_source | False | False | False | characterization_plan_required |
| gen_wl_driver | metadata_only_no_recovery_source | False | False | False | characterization_plan_required |
| gen_col_mux_vdd_labeled | metadata_only_no_recovery_source | False | False | False | characterization_plan_required |
| dff | recoverable_from_existing_spice | True | False | True | plan_characterization_from_existing_spice |
| sense_amp | recoverable_from_existing_spice | True | False | True | plan_characterization_from_existing_spice |
| write_driver | recoverable_from_existing_spice | True | False | True | plan_characterization_from_existing_spice |
| cell_1rw | recoverable_from_existing_spice | True | False | True | plan_characterization_from_existing_spice |
| replica_cell_1rw | recoverable_from_existing_spice | True | False | True | plan_characterization_from_existing_spice |

## Build Output Model Search

| macro | candidate | match_name | usable_without_conversion | risk |
| --- | --- | --- | --- | --- |
| gen_col_mux_vdd_labeled | E:\njust\keyan\SRAM Compiler_V2\OpenRAM-stable\deliverables\sram_layoutgen_step45_clean\build\openyield_colmux_repair\gen_col_mux_vdd_labeled.gds | True | False | candidate_only_not_validated |
| cell_1rw | E:\njust\keyan\SRAM Compiler_V2\OpenRAM-stable\deliverables\sram_layoutgen_step45_clean\build\openyield_hardcell_drc_baseline\cell_1rw_drc.log | False | False | candidate_only_not_validated |
| cell_1rw | E:\njust\keyan\SRAM Compiler_V2\OpenRAM-stable\deliverables\sram_layoutgen_step45_clean\build\openyield_hardcell_drc_baseline\dummy_cell_1rw_drc.log | False | False | candidate_only_not_validated |
| cell_1rw | E:\njust\keyan\SRAM Compiler_V2\OpenRAM-stable\deliverables\sram_layoutgen_step45_clean\build\openyield_hardcell_drc_baseline\replica_cell_1rw_drc.log | False | False | candidate_only_not_validated |
| replica_cell_1rw | E:\njust\keyan\SRAM Compiler_V2\OpenRAM-stable\deliverables\sram_layoutgen_step45_clean\build\openyield_hardcell_drc_baseline\replica_cell_1rw_drc.log | False | False | candidate_only_not_validated |

## Python Generator / Source Recovery Search

| macro | generator_exists | source_type | recover_transistor_level_netlist | requires_characterization |
| --- | --- | --- | --- | --- |
| gen_inv | True | generator_source_only | True | True |
| gen_nand2 | True | generator_source_only | True | True |
| gen_delay_inv | True | generator_source_only | True | True |
| dff | True | existing_spice_only | True | True |
| sense_amp | True | existing_spice_only | True | True |
| write_driver | True | existing_spice_only | True | True |

## Model Recovery Decision Table

| macro | decision | characterization_plan | delay_chain_testbench_plan | timing_proof_now |
| --- | --- | --- | --- | --- |
| gen_inv | recoverable_from_generator_source | True | False | False |
| gen_nand2 | recoverable_from_generator_source | True | False | False |
| gen_delay_inv | recoverable_from_generator_source | True | True | False |
| gen_precharge | metadata_only_no_recovery_source | True | False | False |
| gen_wl_driver | metadata_only_no_recovery_source | True | False | False |
| gen_col_mux_vdd_labeled | metadata_only_no_recovery_source | True | False | False |
| dff | recoverable_from_existing_spice | True | False | False |
| sense_amp | recoverable_from_existing_spice | True | False | False |
| write_driver | recoverable_from_existing_spice | True | False | False |
| cell_1rw | recoverable_from_existing_spice | True | False | False |
| replica_cell_1rw | recoverable_from_existing_spice | True | False | False |

## Timing Object Unblock Matrix

| macro | blocks | decision | usable_spice | usable_lib | equiv_delay_model |
| --- | --- | --- | --- | --- | --- |
| gen_inv | PDRIVE, WL_PDRIVE, PINV, AND2, AND3_COMPOSITE, PNAND3_COMPOSITE | recoverable_from_generator_source | False | False | False |
| gen_nand2 | AND2, AND3_COMPOSITE, PNAND3_COMPOSITE, WRITE_ENABLE_PATH, SENSE_ENABLE_PATH, PRECHARGE_ENABLE_PATH | recoverable_from_generator_source | False | False | False |
| gen_delay_inv | DELAY_CHAIN, WEN_DELAY_CHAIN, RBL_DELAY_PATH | recoverable_from_generator_source | False | False | False |
| gen_precharge | PRECHARGE, PRECHARGE_ENABLE_PATH | metadata_only_no_recovery_source | False | False | False |
| gen_wl_driver | WL_PDRIVE, WORDLINE_ENABLE_PATH | metadata_only_no_recovery_source | False | False | False |
| gen_col_mux_vdd_labeled |  | metadata_only_no_recovery_source | False | False | False |
| dff | DFF_ROW, GATED_CLOCK_PATH | recoverable_from_existing_spice | True | False | False |
| sense_amp | SENSE_ENABLE_PATH | recoverable_from_existing_spice | True | False | False |
| write_driver | WRITE_ENABLE_PATH | recoverable_from_existing_spice | True | False | False |
| cell_1rw | RBL_DELAY_PATH | recoverable_from_existing_spice | True | False | False |
| replica_cell_1rw | DELAY_CHAIN, RBL_DELAY_PATH | recoverable_from_existing_spice | True | False | False |

## Blockers

- gen_inv: Recovery still requires manual netlist materialization plus characterization.
- gen_nand2: Recovery still requires manual netlist materialization plus characterization.
- gen_delay_inv: Recovery still requires manual netlist materialization plus characterization.

## Boundary Assertions

```json
{
  "path_found_is_not_usable_model": true,
  "spice_found_is_not_timing_characterized": true,
  "generator_source_found_is_not_recovered_model": true,
  "build_output_found_is_not_validated_model": true,
  "standalone_modified": false,
  "routing_modified": false,
  "gds_writer_modified": false
}
```

## Next Recommended Proof Task

- `delay_chain_spice_testbench_plan`