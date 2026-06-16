# OpenYield Macro Compatibility Report

This report statically compares OpenYield ModuleContract data against `technology/freepdk45/replacement_macros.json`. It does not modify placement, routing, GDS generation, or OpenYield source.

## Inputs

- contracts: `E:\njust\keyan\SRAM Compiler_V2\OpenRAM-stable\deliverables\sram_layoutgen_standalone\docs\openyield_module_contracts.json`
- tech dir: `E:\njust\keyan\SRAM Compiler_V2\OpenRAM-stable\deliverables\sram_layoutgen_standalone\technology\freepdk45`
- contract count: `53`
- replacement macro count: `6`
- alias count: `10`
- catalog macro count: `19`
- missing focus modules: `none`

## Summary

```json
{
  "matched_existing_macro": [
    "SRAM_6T_CELL",
    "DFF",
    "Dummy_CELL",
    "Dummy_Column",
    "Dummy_Row",
    "PRECHARGE",
    "Replica_CELL",
    "Replica_Column",
    "WRITEDRIVER"
  ],
  "candidate_macro_missing": [],
  "macro_exists_pin_mismatch": [
    "COLUMNMUX*",
    "DECODER3_8",
    "SENSEAMP",
    "WORDLINEDRIVER"
  ],
  "no_physical_implementation": [
    "AND2",
    "AND3",
    "DFF_BUF",
    "D_LATCH",
    "PBUFF",
    "PNAND2",
    "PNAND3",
    "TRANSMISSION_GATE",
    "f'PINV{num}'",
    "pdrive",
    "pdrive2_for_pre",
    "wl_pdrive"
  ],
  "composite_required": [
    "SRAM_6T_CORE_*",
    "ADDR_DFF",
    "DATA_DFF",
    "TIME",
    "delay_chain",
    "wen_delay_chain",
    "DECODER_CASCADE"
  ],
  "unsupported_architecture": [
    "SRAM_10T_CELL",
    "SRAM_10T_CORE_*"
  ],
  "non_layout_source": [
    "ColumnMuxFactory",
    "DecoderCascadeFactory",
    "DummyColumnFactory",
    "DummyRowFactory",
    "PrechargeFactory",
    "ReplicaColumnFactory",
    "SenseAmpFactory",
    "BASE_SUBCKT",
    "BaseTestbench",
    "SRAMCellParasiticTester",
    "Sram10TCellFactory",
    "Sram10TCoreFactory",
    "Sram6TCellFactory",
    "Sram6TCoreFactory",
    "Sram6TCoreMcTestbench",
    "Sram6TCoreTestbench",
    "TIMEFactory",
    "WordlineDriverFactory",
    "WriteDriverFactory"
  ],
  "aggregation_status_counts": {
    "abutment_ready": 6,
    "composite_required": 7,
    "needs_stdcell_or_generated_layout": 12,
    "non_layout_source": 19,
    "unknown_need_gds_pin_audit": 7,
    "unsupported_architecture": 2
  },
  "implementation_status_counts": {
    "composite_required": 7,
    "macro_candidate": 13,
    "needs_stdcell_or_generated_layout": 12,
    "non_layout_source": 19,
    "unsupported_architecture": 2
  },
  "power_status_counts": {
    "missing_vdd": 1,
    "no_gnd_required": 1,
    "no_macro": 40,
    "vdd_gnd_alias_ok": 11
  },
  "vdd_gnd_shared_rail_risks": [
    "COLUMNMUX*",
    "DFF",
    "DECODER3_8",
    "PRECHARGE",
    "SENSEAMP",
    "WORDLINEDRIVER",
    "WRITEDRIVER"
  ]
}
```

## Compatibility Table

| module | role | implementation | candidate macros | existing macros | selected macro | pin checks | power | aggregation | notes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| SRAM_6T_CELL | bitcell | macro_candidate | cell_1rw, cell_6t | cell_1rw | cell_1rw | matched:5 | vdd_gnd_alias_ok | abutment_ready | - |
| SRAM_10T_CELL | bitcell_10t | unsupported_architecture | - | - | - | - | no_macro | unsupported_architecture | Current layout generator/replacement macro library is 6T-focused; this OpenYield architecture is unsupported. |
| SRAM_6T_CORE_* | bitcell_array | composite_required | cell_1rw_array, bitcell_array | - | - | missing_macro:5 | no_macro | composite_required | This contract is hierarchical and should not map to one single flat GDS macro.; Pins contain dynamic bus patterns; expand with SRAM size before placement.; Do not map this OpenYield module to one single GDS macro; build it from lower-level contracts. |
| SRAM_10T_CORE_* | bitcell_array_10t | unsupported_architecture | - | - | - | - | no_macro | unsupported_architecture | Pins contain dynamic bus patterns; expand with SRAM size before placement.; Current layout generator/replacement macro library is 6T-focused; this OpenYield architecture is unsupported. |
| COLUMNMUX* | column_mux | macro_candidate | gen_col_mux, column_mux | gen_col_mux | gen_col_mux | matched:6, missing_pin:1 | missing_vdd | unknown_need_gds_pin_audit | Pins contain dynamic bus patterns; expand with SRAM size before placement.; Replacement macro exists, but one or more canonical pins do not match current metadata. |
| ColumnMuxFactory | column_mux | non_layout_source | - | - | - | - | no_macro | non_layout_source | - |
| ADDR_DFF | control_timing | composite_required | - | - | - | - | no_macro | composite_required | This contract is hierarchical and should not map to one single flat GDS macro.; Pins contain dynamic bus patterns; expand with SRAM size before placement.; Do not map this OpenYield module to one single GDS macro; build it from lower-level contracts. |
| DATA_DFF | control_timing | composite_required | - | - | - | - | no_macro | composite_required | This contract is hierarchical and should not map to one single flat GDS macro.; Pins contain dynamic bus patterns; expand with SRAM size before placement.; Do not map this OpenYield module to one single GDS macro; build it from lower-level contracts. |
| DFF | control_timing | macro_candidate | dff | dff | dff | matched:5 | vdd_gnd_alias_ok | unknown_need_gds_pin_audit | This contract is hierarchical and should not map to one single flat GDS macro. |
| TIME | control_timing | composite_required | - | - | - | - | no_macro | composite_required | Composite control/timing module; should become architecture/control contract before placement.; Composed from ADDR_DFF, DATA_DFF, DFF, delay_chain, wen_delay_chain, pdrive, pdrive2_for_pre, wl_pdrive, and logic gates.; This contract is hierarchical and should not map to one single flat GDS macro.; Pins contain dynamic bus patterns; expand with SRAM size before placement.; Do not map this OpenYield module to one single GDS macro; build it from lower-level contracts. |
| delay_chain | control_timing | composite_required | - | - | - | - | no_macro | composite_required | This contract is hierarchical and should not map to one single flat GDS macro.; Do not map this OpenYield module to one single GDS macro; build it from lower-level contracts. |
| wen_delay_chain | control_timing | composite_required | - | - | - | - | no_macro | composite_required | This contract is hierarchical and should not map to one single flat GDS macro.; Do not map this OpenYield module to one single GDS macro; build it from lower-level contracts. |
| DECODER3_8 | decoder | macro_candidate | gen_nand2, gen_nand4, row_decoder | gen_nand2, gen_nand4 | gen_nand2 | matched:2, missing_pin:3 | vdd_gnd_alias_ok | unknown_need_gds_pin_audit | Replacement macro exists, but one or more canonical pins do not match current metadata. |
| DECODER_CASCADE | decoder | composite_required | - | - | - | - | no_macro | composite_required | Pins contain dynamic bus patterns; expand with SRAM size before placement.; Do not map this OpenYield module to one single GDS macro; build it from lower-level contracts. |
| DecoderCascadeFactory | decoder | non_layout_source | - | - | - | - | no_macro | non_layout_source | - |
| DummyColumnFactory | dummy | non_layout_source | - | - | - | - | no_macro | non_layout_source | - |
| DummyRowFactory | dummy | non_layout_source | - | - | - | - | no_macro | non_layout_source | - |
| Dummy_CELL | dummy | macro_candidate | dummy_cell_1rw, dummy_cell_array | dummy_cell_1rw | dummy_cell_1rw | matched:5 | vdd_gnd_alias_ok | abutment_ready | - |
| Dummy_Column | dummy | macro_candidate | dummy_cell_1rw, dummy_cell_array | dummy_cell_1rw | dummy_cell_1rw | matched:5 | vdd_gnd_alias_ok | abutment_ready | Pins contain dynamic bus patterns; expand with SRAM size before placement. |
| Dummy_Row | dummy | macro_candidate | dummy_cell_1rw, dummy_cell_array | dummy_cell_1rw | dummy_cell_1rw | matched:5 | vdd_gnd_alias_ok | abutment_ready | Pins contain dynamic bus patterns; expand with SRAM size before placement. |
| PRECHARGE | precharge | macro_candidate | gen_precharge, precharge_array | gen_precharge | gen_precharge | matched:4 | no_gnd_required | unknown_need_gds_pin_audit | OpenYield PRECHARGE uses ENB; map to active-low precharge enable. |
| PrechargeFactory | precharge | non_layout_source | - | - | - | - | no_macro | non_layout_source | - |
| ReplicaColumnFactory | replica | non_layout_source | - | - | - | - | no_macro | non_layout_source | - |
| Replica_CELL | replica | macro_candidate | replica_cell_1rw, replica_column | replica_cell_1rw | replica_cell_1rw | matched:5 | vdd_gnd_alias_ok | abutment_ready | - |
| Replica_Column | replica | macro_candidate | replica_cell_1rw, replica_column | replica_cell_1rw | replica_cell_1rw | matched:5 | vdd_gnd_alias_ok | abutment_ready | Pins contain dynamic bus patterns; expand with SRAM size before placement. |
| SENSEAMP | sense_amp | macro_candidate | sense_amp, sense_amp_array | sense_amp | sense_amp | matched:6, missing_pin:1 | vdd_gnd_alias_ok | unknown_need_gds_pin_audit | Map IN/INB to selected BL/BR and Q/QB to dout/dout_b or tri-state stage.; Replacement macro exists, but one or more canonical pins do not match current metadata. |
| SenseAmpFactory | sense_amp | non_layout_source | - | - | - | - | no_macro | non_layout_source | - |
| AND2 | support_cell | needs_stdcell_or_generated_layout | - | - | - | - | no_macro | needs_stdcell_or_generated_layout | - |
| AND3 | support_cell | needs_stdcell_or_generated_layout | - | - | - | - | no_macro | needs_stdcell_or_generated_layout | - |
| DFF_BUF | support_cell | needs_stdcell_or_generated_layout | - | - | - | - | no_macro | needs_stdcell_or_generated_layout | - |
| D_LATCH | support_cell | needs_stdcell_or_generated_layout | - | - | - | - | no_macro | needs_stdcell_or_generated_layout | - |
| PBUFF | support_cell | needs_stdcell_or_generated_layout | - | - | - | - | no_macro | needs_stdcell_or_generated_layout | - |
| PNAND2 | support_cell | needs_stdcell_or_generated_layout | - | - | - | - | no_macro | needs_stdcell_or_generated_layout | - |
| PNAND3 | support_cell | needs_stdcell_or_generated_layout | - | - | - | - | no_macro | needs_stdcell_or_generated_layout | - |
| TRANSMISSION_GATE | support_cell | needs_stdcell_or_generated_layout | - | - | - | - | no_macro | needs_stdcell_or_generated_layout | - |
| f'PINV{num}' | support_cell | needs_stdcell_or_generated_layout | - | - | - | - | no_macro | needs_stdcell_or_generated_layout | - |
| pdrive | support_cell | needs_stdcell_or_generated_layout | - | - | - | - | no_macro | needs_stdcell_or_generated_layout | - |
| pdrive2_for_pre | support_cell | needs_stdcell_or_generated_layout | - | - | - | - | no_macro | needs_stdcell_or_generated_layout | - |
| wl_pdrive | support_cell | needs_stdcell_or_generated_layout | - | - | - | - | no_macro | needs_stdcell_or_generated_layout | - |
| BASE_SUBCKT | unknown | non_layout_source | - | - | - | - | no_macro | non_layout_source | - |
| BaseTestbench | unknown | non_layout_source | - | - | - | - | no_macro | non_layout_source | - |
| SRAMCellParasiticTester | unknown | non_layout_source | - | - | - | - | no_macro | non_layout_source | - |
| Sram10TCellFactory | unknown | non_layout_source | - | - | - | - | no_macro | non_layout_source | - |
| Sram10TCoreFactory | unknown | non_layout_source | - | - | - | - | no_macro | non_layout_source | - |
| Sram6TCellFactory | unknown | non_layout_source | - | - | - | - | no_macro | non_layout_source | - |
| Sram6TCoreFactory | unknown | non_layout_source | - | - | - | - | no_macro | non_layout_source | - |
| Sram6TCoreMcTestbench | unknown | non_layout_source | - | - | - | - | no_macro | non_layout_source | - |
| Sram6TCoreTestbench | unknown | non_layout_source | - | - | - | - | no_macro | non_layout_source | - |
| TIMEFactory | unknown | non_layout_source | - | - | - | - | no_macro | non_layout_source | - |
| WORDLINEDRIVER | wordline_driver | macro_candidate | gen_wl_driver, wordline_driver | gen_wl_driver | gen_wl_driver | matched:4, missing_pin:1 | vdd_gnd_alias_ok | unknown_need_gds_pin_audit | A is treated as decoder_input, B as wordline_enable, and Z as wl; confirm polarity against OpenYield timing before physical hookup.; needs_semantic_confirmation; Replacement macro exists, but one or more canonical pins do not match current metadata. |
| WordlineDriverFactory | wordline_driver | non_layout_source | - | - | - | - | no_macro | non_layout_source | - |
| WRITEDRIVER | write_driver | macro_candidate | write_driver, write_driver_array | write_driver | write_driver | matched:6 | vdd_gnd_alias_ok | unknown_need_gds_pin_audit | OpenYield WRITEDRIVER has internal DINB/ENB generation; only DIN/EN are external pins. |
| WriteDriverFactory | write_driver | non_layout_source | - | - | - | - | no_macro | non_layout_source | - |

## Existing Macro Matches

- `SRAM_6T_CELL`
- `DFF`
- `Dummy_CELL`
- `Dummy_Column`
- `Dummy_Row`
- `PRECHARGE`
- `Replica_CELL`
- `Replica_Column`
- `WRITEDRIVER`

## Candidate Macro Missing

none

## Macro Exists But Pin Mismatch

- `COLUMNMUX*`
- `DECODER3_8`
- `SENSEAMP`
- `WORDLINEDRIVER`

## Composite Modules

- `SRAM_6T_CORE_*`
- `ADDR_DFF`
- `DATA_DFF`
- `TIME`
- `delay_chain`
- `wen_delay_chain`
- `DECODER_CASCADE`

## Unsupported Architecture

- `SRAM_10T_CELL`
- `SRAM_10T_CORE_*`

## Non-Layout Sources

- `ColumnMuxFactory`
- `DecoderCascadeFactory`
- `DummyColumnFactory`
- `DummyRowFactory`
- `PrechargeFactory`
- `ReplicaColumnFactory`
- `SenseAmpFactory`
- `BASE_SUBCKT`
- `BaseTestbench`
- `SRAMCellParasiticTester`
- `Sram10TCellFactory`
- `Sram10TCoreFactory`
- `Sram6TCellFactory`
- `Sram6TCoreFactory`
- `Sram6TCoreMcTestbench`
- `Sram6TCoreTestbench`
- `TIMEFactory`
- `WordlineDriverFactory`
- `WriteDriverFactory`

## VDD/GND Shared Rail Risks

- `COLUMNMUX*`
- `DFF`
- `DECODER3_8`
- `PRECHARGE`
- `SENSEAMP`
- `WORDLINEDRIVER`
- `WRITEDRIVER`

## Next Missing Alias Or Macro Work

- Add replacement macro metadata for hardcell macros that already exist as GDS but are not listed in `replacement_macros.json`, such as bitcell, dummy, replica, sense amp, write driver, and DFF cells.
- Confirm `WORDLINEDRIVER.A/B` semantics before physical routing; current contract marks `A -> decoder_input`, `B -> wordline_enable`, and `Z -> wl` with `needs_semantic_confirmation`.
- Use full GDS pin-shape audits before enabling abutment or shared rails for generated replacement macros.