# OpenYield Macro Metadata Audit

This audit scans local FreePDK45 GDS/SPICE libraries and OpenYield alias metadata. It does not modify placement, routing, GDS generation, or OpenYield source.

## Inputs

- contracts: `E:\njust\keyan\SRAM Compiler_V2\OpenRAM-stable\deliverables\sram_layoutgen_standalone\docs\openyield_module_contracts.json`
- prior compat report: `E:\njust\keyan\SRAM Compiler_V2\OpenRAM-stable\deliverables\sram_layoutgen_standalone\docs\openyield_macro_compat_report.json`
- tech dir: `E:\njust\keyan\SRAM Compiler_V2\OpenRAM-stable\deliverables\sram_layoutgen_standalone\technology\freepdk45`

## Library Summary

- replacement macros registered: `6`
- alias entries: `10`
- catalog macros after alias/discovery merge: `19`
- local GDS macros scanned: `19`
- local SPICE subckts scanned: `10`

## Missing Macro Resolution

- before alias: `DFF, Dummy_CELL, Dummy_Column, Dummy_Row, Replica_CELL, Replica_Column, SENSEAMP, SRAM_6T_CELL, WRITEDRIVER`
- after alias: `none`
- resolved by alias: `DFF, Dummy_CELL, Dummy_Column, Dummy_Row, Replica_CELL, Replica_Column, SENSEAMP, SRAM_6T_CELL, WRITEDRIVER`

## Focus Macro Audit

| macro | GDS | SPICE | registered | alias targets | pins |
| --- | --- | --- | --- | --- | --- |
| cell_1rw | True | True | False | SRAM_6T_CELL | bl, br, wl, vdd, gnd |
| cell_2rw | True | True | False | - | bl0, br0, bl1, br1, wl0, wl1, vdd, gnd |
| cell_6t | False | False | False | - | - |
| dummy_cell_1rw | True | True | False | Dummy_CELL, Dummy_Column, Dummy_Row | bl, br, wl, vdd, gnd |
| dummy_cell_2rw | True | True | False | - | bl0, br0, bl1, br1, wl0, wl1, vdd, gnd |
| replica_cell_1rw | True | True | False | Replica_CELL, Replica_Column | bl, br, wl, vdd, gnd |
| replica_cell_2rw | True | True | False | - | bl0, br0, bl1, br1, wl0, wl1, vdd, gnd |
| sense_amp | True | True | False | SENSEAMP | bl, br, dout, en, vdd, gnd |
| write_driver | True | True | False | WRITEDRIVER | din, bl, br, en, vdd, gnd |
| tri_gate | True | True | False | tri_gate | in, out, en, en_bar, vdd, gnd |
| dff | True | True | False | DFF | D, Q, clk, vdd, gnd |
| precharge | False | False | False | - | - |
| gen_precharge | True | False | True | - | - |
| gen_col_mux | True | False | True | - | - |
| gen_wl_driver | True | False | True | - | - |
| gen_nand2 | True | False | True | - | - |
| gen_nand4 | True | False | False | - | - |
| row_decoder | False | False | False | - | - |
| wordline_driver | False | False | False | - | - |

## Module Metadata Audit

| module | role | implementation | selected macro | alias | GDS | SPICE | pin status | power | abutment | needs GDS pin audit |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| ADDR_DFF | control_timing | composite_required | - | False | False | False | {} | no_macro | composite_required | False |
| AND2 | support_cell | needs_stdcell_or_generated_layout | - | False | False | False | {} | no_macro | needs_stdcell_or_generated_layout | False |
| AND3 | support_cell | needs_stdcell_or_generated_layout | - | False | False | False | {} | no_macro | needs_stdcell_or_generated_layout | False |
| BASE_SUBCKT | unknown | non_layout_source | - | False | False | False | {} | no_macro | non_layout_source | False |
| BaseTestbench | unknown | non_layout_source | - | False | False | False | {} | no_macro | non_layout_source | False |
| COLUMNMUX* | column_mux | macro_candidate | gen_col_mux | False | True | False | {"missing_pin": 1, "matched": 6} | missing_vdd | unknown_need_gds_pin_audit | False |
| ColumnMuxFactory | column_mux | non_layout_source | - | False | False | False | {} | no_macro | non_layout_source | False |
| DATA_DFF | control_timing | composite_required | - | False | False | False | {} | no_macro | composite_required | False |
| DECODER3_8 | decoder | macro_candidate | gen_nand2 | False | True | False | {"matched": 2, "missing_pin": 3} | vdd_gnd_alias_ok | unknown_need_gds_pin_audit | False |
| DECODER_CASCADE | decoder | composite_required | - | False | False | False | {} | no_macro | composite_required | False |
| DFF | control_timing | macro_candidate | dff | True | True | True | {"matched": 5} | vdd_gnd_alias_ok | unknown_need_gds_pin_audit | True |
| DFF_BUF | support_cell | needs_stdcell_or_generated_layout | - | False | False | False | {} | no_macro | needs_stdcell_or_generated_layout | False |
| D_LATCH | support_cell | needs_stdcell_or_generated_layout | - | False | False | False | {} | no_macro | needs_stdcell_or_generated_layout | False |
| DecoderCascadeFactory | decoder | non_layout_source | - | False | False | False | {} | no_macro | non_layout_source | False |
| DummyColumnFactory | dummy | non_layout_source | - | False | False | False | {} | no_macro | non_layout_source | False |
| DummyRowFactory | dummy | non_layout_source | - | False | False | False | {} | no_macro | non_layout_source | False |
| Dummy_CELL | dummy | macro_candidate | dummy_cell_1rw | True | True | True | {"matched": 5} | vdd_gnd_alias_ok | abutment_ready | True |
| Dummy_Column | dummy | macro_candidate | dummy_cell_1rw | True | True | True | {"matched": 5} | vdd_gnd_alias_ok | abutment_ready | True |
| Dummy_Row | dummy | macro_candidate | dummy_cell_1rw | True | True | True | {"matched": 5} | vdd_gnd_alias_ok | abutment_ready | True |
| PBUFF | support_cell | needs_stdcell_or_generated_layout | - | False | False | False | {} | no_macro | needs_stdcell_or_generated_layout | False |
| PNAND2 | support_cell | needs_stdcell_or_generated_layout | - | False | False | False | {} | no_macro | needs_stdcell_or_generated_layout | False |
| PNAND3 | support_cell | needs_stdcell_or_generated_layout | - | False | False | False | {} | no_macro | needs_stdcell_or_generated_layout | False |
| PRECHARGE | precharge | macro_candidate | gen_precharge | False | True | False | {"matched": 4} | no_gnd_required | unknown_need_gds_pin_audit | False |
| PrechargeFactory | precharge | non_layout_source | - | False | False | False | {} | no_macro | non_layout_source | False |
| ReplicaColumnFactory | replica | non_layout_source | - | False | False | False | {} | no_macro | non_layout_source | False |
| Replica_CELL | replica | macro_candidate | replica_cell_1rw | True | True | True | {"matched": 5} | vdd_gnd_alias_ok | abutment_ready | True |
| Replica_Column | replica | macro_candidate | replica_cell_1rw | True | True | True | {"matched": 5} | vdd_gnd_alias_ok | abutment_ready | True |
| SENSEAMP | sense_amp | macro_candidate | sense_amp | True | True | True | {"matched": 6, "missing_pin": 1} | vdd_gnd_alias_ok | unknown_need_gds_pin_audit | True |
| SRAMCellParasiticTester | unknown | non_layout_source | - | False | False | False | {} | no_macro | non_layout_source | False |
| SRAM_10T_CELL | bitcell_10t | unsupported_architecture | - | False | False | False | {} | no_macro | unsupported_architecture | False |
| SRAM_10T_CORE_* | bitcell_array_10t | unsupported_architecture | - | False | False | False | {} | no_macro | unsupported_architecture | False |
| SRAM_6T_CELL | bitcell | macro_candidate | cell_1rw | True | True | True | {"matched": 5} | vdd_gnd_alias_ok | abutment_ready | True |
| SRAM_6T_CORE_* | bitcell_array | composite_required | - | False | False | False | {"missing_macro": 5} | no_macro | composite_required | False |
| SenseAmpFactory | sense_amp | non_layout_source | - | False | False | False | {} | no_macro | non_layout_source | False |
| Sram10TCellFactory | unknown | non_layout_source | - | False | False | False | {} | no_macro | non_layout_source | False |
| Sram10TCoreFactory | unknown | non_layout_source | - | False | False | False | {} | no_macro | non_layout_source | False |
| Sram6TCellFactory | unknown | non_layout_source | - | False | False | False | {} | no_macro | non_layout_source | False |
| Sram6TCoreFactory | unknown | non_layout_source | - | False | False | False | {} | no_macro | non_layout_source | False |
| Sram6TCoreMcTestbench | unknown | non_layout_source | - | False | False | False | {} | no_macro | non_layout_source | False |
| Sram6TCoreTestbench | unknown | non_layout_source | - | False | False | False | {} | no_macro | non_layout_source | False |
| TIME | control_timing | composite_required | - | False | False | False | {} | no_macro | composite_required | False |
| TIMEFactory | unknown | non_layout_source | - | False | False | False | {} | no_macro | non_layout_source | False |
| TRANSMISSION_GATE | support_cell | needs_stdcell_or_generated_layout | - | False | False | False | {} | no_macro | needs_stdcell_or_generated_layout | False |
| WORDLINEDRIVER | wordline_driver | macro_candidate | gen_wl_driver | False | True | False | {"matched": 4, "missing_pin": 1} | vdd_gnd_alias_ok | unknown_need_gds_pin_audit | False |
| WRITEDRIVER | write_driver | macro_candidate | write_driver | True | True | True | {"matched": 6} | vdd_gnd_alias_ok | unknown_need_gds_pin_audit | True |
| WordlineDriverFactory | wordline_driver | non_layout_source | - | False | False | False | {} | no_macro | non_layout_source | False |
| WriteDriverFactory | write_driver | non_layout_source | - | False | False | False | {} | no_macro | non_layout_source | False |
| delay_chain | control_timing | composite_required | - | False | False | False | {} | no_macro | composite_required | False |
| f'PINV{num}' | support_cell | needs_stdcell_or_generated_layout | - | False | False | False | {} | no_macro | needs_stdcell_or_generated_layout | False |
| pdrive | support_cell | needs_stdcell_or_generated_layout | - | False | False | False | {} | no_macro | needs_stdcell_or_generated_layout | False |
| pdrive2_for_pre | support_cell | needs_stdcell_or_generated_layout | - | False | False | False | {} | no_macro | needs_stdcell_or_generated_layout | False |
| wen_delay_chain | control_timing | composite_required | - | False | False | False | {} | no_macro | composite_required | False |
| wl_pdrive | support_cell | needs_stdcell_or_generated_layout | - | False | False | False | {} | no_macro | needs_stdcell_or_generated_layout | False |

## Unregistered Local GDS/SPICE Macros

- `cell_1rw`
- `cell_2rw`
- `dff`
- `dummy_cell_1rw`
- `dummy_cell_2rw`
- `gen_nand4`
- `gen_nor2`
- `gen_well_tap`
- `replica_cell_1rw`
- `replica_cell_2rw`
- `sense_amp`
- `tri_gate`
- `write_driver`

## Suggested Macro Aliases

| OpenYield module | macro | GDS | SPICE | aggregation hint | notes |
| --- | --- | --- | --- | --- | --- |
| DFF | dff | gds_lib/dff.gds | sp_lib/dff.sp | unknown_need_gds_pin_audit | OpenYield DFF Q is accepted as canonical dout for current contract compatibility. |
| Dummy_CELL | dummy_cell_1rw | gds_lib/dummy_cell_1rw.gds | sp_lib/dummy_cell_1rw.sp | abutment_ready | Dummy bitcells should align with bitcell rails; confirm exact edge pins in GDS before no-gap abutment. |
| Dummy_Column | dummy_cell_1rw | gds_lib/dummy_cell_1rw.gds | sp_lib/dummy_cell_1rw.sp | abutment_ready | OpenYield Dummy_Column is an array composition of dummy_cell_1rw. |
| Dummy_Row | dummy_cell_1rw | gds_lib/dummy_cell_1rw.gds | sp_lib/dummy_cell_1rw.sp | abutment_ready | OpenYield Dummy_Row is an array composition of dummy_cell_1rw. |
| Replica_CELL | replica_cell_1rw | gds_lib/replica_cell_1rw.gds | sp_lib/replica_cell_1rw.sp | abutment_ready | Local replica_cell_1rw SPICE names bitlines bl/br; OpenYield contract names them RBL/RBLB. |
| Replica_Column | replica_cell_1rw | gds_lib/replica_cell_1rw.gds | sp_lib/replica_cell_1rw.sp | abutment_ready | OpenYield Replica_Column is a column composition of replica_cell_1rw. |
| SENSEAMP | sense_amp | gds_lib/sense_amp.gds | sp_lib/sense_amp.sp | unknown_need_gds_pin_audit | Local sense_amp SPICE has a single dout pin; OpenYield SENSEAMP contract has Q and QB. Treat QB/dout_b as unresolved until the GDS/SPICE semantics are confirmed. |
| SRAM_6T_CELL | cell_1rw | gds_lib/cell_1rw.gds | sp_lib/cell_1rw.sp | abutment_ready | SRAM bitcells are expected to abut in arrays, but final enablement still requires GDS pin-shape and rail-continuity audit. |
| WRITEDRIVER | write_driver | gds_lib/write_driver.gds | sp_lib/write_driver.sp | unknown_need_gds_pin_audit | Local write_driver has matching functional pins by SPICE name; abutment requires GDS rail/pin-shape audit. |
| tri_gate | tri_gate | gds_lib/tri_gate.gds | sp_lib/tri_gate.sp | unknown_need_gds_pin_audit | Included for future output path compatibility; not a direct OpenYield top-level contract in the current parser output. |

## Remaining Physical Gaps

- no physical/generated/stdcell implementation: `AND2, AND3, DFF_BUF, D_LATCH, PBUFF, PNAND2, PNAND3, TRANSMISSION_GATE, f'PINV{num}', pdrive, pdrive2_for_pre, wl_pdrive`
- pin mismatch after alias: `COLUMNMUX*, DECODER3_8, SENSEAMP, WORDLINEDRIVER`
- VDD/GND shared rail risks after alias: `COLUMNMUX*, DFF, DECODER3_8, PRECHARGE, SENSEAMP, WORDLINEDRIVER, WRITEDRIVER`

## Placement Aggregation Readiness

- can enter placement aggregation now: `False`

Blocking metadata before placement:

- `Run a real GDS pin-shape audit for alias-augmented hardcells; current aliases use SPICE pins and file presence.`
- `Resolve SENSEAMP dout_b/QB semantic mismatch because local sense_amp SPICE has a single dout pin.`
- `Resolve COLUMNMUX* missing vdd metadata before shared power rails.`
- `Confirm WORDLINEDRIVER A/B polarity and missing B pin in gen_wl_driver before routing wordline_enable.`