# OpenYield Hardcell Power Rail Continuity Readonly Audit

This report stays in readonly evidence mode. It distinguishes label presence, local rail-shape evidence, and cross-abutment proof instead of collapsing them into one readiness claim.

## Audit Summary

- repo root: `E:\njust\keyan\SRAM Compiler_V2\OpenRAM-stable\deliverables\sram_layoutgen_step45_clean`
- tech dir: `E:\njust\keyan\SRAM Compiler_V2\OpenRAM-stable\deliverables\sram_layoutgen_step45_clean\technology\freepdk45`
- next recommended proof task: `time_control_leaf_bbox_pin_side_inventory`

```json
{
  "hardcell_power_rail_continuity_readonly_audit_available": true,
  "all_required_macro_gds_found": true,
  "all_required_macro_power_metadata_available": false,
  "all_required_macro_spice_checked_or_missing_recorded": true,
  "precharge_power_exception_recorded": true,
  "within_macro_rail_evidence_available": true,
  "abutment_rail_continuity_proven": false,
  "shared_rail_safe": false,
  "can_enter_legal_placement_readonly_audit": true,
  "can_enter_physical_placement_now": false,
  "can_generate_time_control_gds_now": false,
  "can_modify_standalone_now": false
}
```

## Input Assets

```json
{
  "inventory_report": {
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
  },
  "gds_variant_count": 19,
  "spice_macro_count": 13
}
```

## GDS Power Rail / Label Audit

| macro | variant | vdd labels | gnd labels | vdd side | gnd side | policy | within macro | across abutment | shared rail | physical-ready |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| cell_1rw | default_gds_lib | 1 | 1 | top | bottom | top_vdd_bottom_gnd | True | True | False | True |
| dummy_cell_1rw | default_gds_lib | 1 | 1 | top | bottom | top_vdd_bottom_gnd | True | True | False | True |
| replica_cell_1rw | default_gds_lib | 1 | 1 | top | bottom | top_vdd_bottom_gnd | True | True | False | True |
| sense_amp | default_gds_lib | 1 | 2 | left | right | side_rails_or_mixed | True | False | False | True |
| write_driver | default_gds_lib | 1 | 1 | left | left | side_rails_or_mixed | True | False | False | True |
| gen_wl_driver | default_gds_lib | 0 | 0 | right | bottom | side_rails_or_mixed | False | False | False | False |
| gen_wl_driver | openram_replacements | 3 | 3 | top | bottom | top_vdd_bottom_gnd | True | False | False | True |
| gen_col_mux | default_gds_lib | 0 | 0 | unknown | right | side_rails_or_mixed | False | False | False | False |
| gen_col_mux | openram_replacements | 0 | 1 | unknown | right | side_rails_or_mixed | False | False | False | False |
| gen_col_mux_vdd_labeled | openyield_repaired | 1 | 1 | top | right | side_rails_or_mixed | True | False | False | True |
| gen_inv | default_gds_lib | 0 | 0 | top | bottom | top_vdd_bottom_gnd | False | False | False | False |
| gen_inv | openram_replacements | 1 | 1 | top | bottom | top_vdd_bottom_gnd | True | False | False | True |
| gen_nand2 | default_gds_lib | 0 | 0 | top | bottom | top_vdd_bottom_gnd | False | False | False | False |
| gen_nand2 | openram_replacements | 1 | 1 | top | bottom | top_vdd_bottom_gnd | True | False | False | True |
| gen_delay_inv | default_gds_lib | 0 | 0 | left | bottom | side_rails_or_mixed | False | False | False | False |
| gen_delay_inv | openram_replacements | 1 | 1 | top | bottom | top_vdd_bottom_gnd | True | False | False | True |
| gen_precharge | default_gds_lib | 0 | 0 | left | unknown | side_rails_or_mixed | False | False | False | False |
| gen_precharge | openram_replacements | 1 | 0 | top | unknown | unknown | False | False | False | False |
| dff | default_gds_lib | 1 | 1 | top | bottom | top_vdd_bottom_gnd | True | False | False | True |

## SPICE Cross-Check

| macro | spice exists | subckt | power pins | consistency |
| --- | --- | --- | --- | --- |
| cell_1rw | True | cell_1rw | vdd, gnd | power_pins_present |
| dummy_cell_1rw | True | dummy_cell_1rw | vdd, gnd | power_pins_present |
| replica_cell_1rw | True | replica_cell_1rw | vdd, gnd | power_pins_present |
| sense_amp | True | sense_amp | vdd, gnd | power_pins_present |
| write_driver | True | write_driver | vdd, gnd | power_pins_present |
| dff | True | dff | vdd, gnd | power_pins_present |
| gen_inv | False | - | - | missing_power_pins |
| gen_nand2 | False | - | - | missing_power_pins |
| gen_delay_inv | False | - | - | missing_power_pins |
| gen_precharge | False | - | - | spice_missing |
| gen_wl_driver | False | - | - | missing_power_pins |
| gen_col_mux | False | - | - | missing_power_pins |
| gen_col_mux_vdd_labeled | False | - | - | missing_power_pins |

## PRECHARGE Special Decision

| variant | vdd | gnd | spice | metadata planning | physical placement | status |
| --- | --- | --- | --- | --- | --- | --- |
| default_gds_lib | False | False | False | False | False | partial_missing_gnd |
| openram_replacements | True | False | False | True | False | vdd_only_no_local_gnd_exception_metadata_only |

## Macro Variant Comparison

| macro | recommended variant | spice consistency | reason | warnings |
| --- | --- | --- | --- | --- |
| cell_1rw | default_gds_lib | power_pins_present | Storage hardcells should stay on technology/freepdk45/gds_lib/*.gds. | - |
| dff | default_gds_lib | power_pins_present | OpenRAM replacement variant carries the strongest local power metadata among generated-logic candidates. | - |
| dummy_cell_1rw | default_gds_lib | power_pins_present | Storage hardcells should stay on technology/freepdk45/gds_lib/*.gds. | - |
| gen_col_mux | openram_replacements | missing_power_pins | OpenRAM replacement variant carries the strongest local power metadata among generated-logic candidates. | Unrepaired gen_col_mux variants lack complete VDD metadata. |
| gen_col_mux_vdd_labeled | openyield_repaired | missing_power_pins | Repaired column mux exposes explicit VDD/GND labels and is preferred for future planning. | - |
| gen_delay_inv | openram_replacements | missing_power_pins | OpenRAM replacement variant carries the strongest local power metadata among generated-logic candidates. | - |
| gen_inv | openram_replacements | missing_power_pins | OpenRAM replacement variant carries the strongest local power metadata among generated-logic candidates. | - |
| gen_nand2 | openram_replacements | missing_power_pins | OpenRAM replacement variant carries the strongest local power metadata among generated-logic candidates. | - |
| gen_precharge | openram_replacements | spice_missing | OpenRAM replacement carries the clearest power metadata, but remains metadata-only if GND is absent. | PRECHARGE may remain vdd-only and metadata-only; do not treat as physical-ready. |
| gen_wl_driver | openram_replacements | missing_power_pins | OpenRAM replacement variant carries the strongest local power metadata among generated-logic candidates. | - |
| replica_cell_1rw | default_gds_lib | power_pins_present | Storage hardcells should stay on technology/freepdk45/gds_lib/*.gds. | - |
| sense_amp | default_gds_lib | power_pins_present | OpenRAM replacement variant carries the strongest local power metadata among generated-logic candidates. | QB/dout_b remains unresolved; power audit does not prove signal-side compatibility. |
| write_driver | default_gds_lib | power_pins_present | OpenRAM replacement variant carries the strongest local power metadata among generated-logic candidates. | - |

## Unresolved Blockers

- gen_wl_driver:default_gds_lib lacks proven within-macro rail evidence.
- gen_wl_driver:default_gds_lib is not physical-placement ready.
- gen_col_mux:default_gds_lib lacks proven within-macro rail evidence.
- gen_col_mux:default_gds_lib is not physical-placement ready.
- gen_col_mux:openram_replacements lacks proven within-macro rail evidence.
- gen_col_mux:openram_replacements is not physical-placement ready.
- gen_inv:default_gds_lib lacks proven within-macro rail evidence.
- gen_inv:default_gds_lib is not physical-placement ready.
- gen_nand2:default_gds_lib lacks proven within-macro rail evidence.
- gen_nand2:default_gds_lib is not physical-placement ready.
- gen_delay_inv:default_gds_lib lacks proven within-macro rail evidence.
- gen_delay_inv:default_gds_lib is not physical-placement ready.
- gen_precharge:default_gds_lib lacks proven within-macro rail evidence.
- gen_precharge:default_gds_lib is not physical-placement ready.
- gen_precharge:openram_replacements lacks proven within-macro rail evidence.
- gen_precharge:openram_replacements is not physical-placement ready.
- gen_inv has no local SPICE and remains metadata-only for power cross-check.
- gen_nand2 has no local SPICE and remains metadata-only for power cross-check.
- gen_delay_inv has no local SPICE and remains metadata-only for power cross-check.
- gen_precharge has no local SPICE and remains metadata-only for power cross-check.
- gen_wl_driver has no local SPICE and remains metadata-only for power cross-check.
- gen_col_mux has no local SPICE and remains metadata-only for power cross-check.
- gen_col_mux_vdd_labeled has no local SPICE and remains metadata-only for power cross-check.
- PRECHARGE default_gds_lib remains exception-based: partial_missing_gnd.
- PRECHARGE openram_replacements remains exception-based: vdd_only_no_local_gnd_exception_metadata_only.

## Boundary Assertions

```json
{
  "can_modify_standalone_now": false,
  "can_generate_time_control_gds_now": false,
  "can_enter_physical_placement_now": false,
  "standalone_modified": false,
  "routing_modified": false,
  "gds_writer_modified": false
}
```