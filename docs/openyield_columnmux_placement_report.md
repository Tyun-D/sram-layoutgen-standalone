# OpenYield ColumnMux Placement Smoke Report

- placement count: `8`
- mux ratio: `2`
- macro name: `gen_col_mux_vdd_labeled`
- can enter limited placement: `True`
- safe_for_physical_mapping: `True`
- safe_for_shared_rail: `False`

## Repaired Alias

- local macro: `gen_col_mux_vdd_labeled`
- source macro: `gen_col_mux`
- candidate GDS: `E:\njust\keyan\SRAM Compiler_V2\OpenRAM-stable\deliverables\sram_layoutgen_step45_clean\build\openyield_colmux_repair\gen_col_mux_vdd_labeled.gds`

## SenseAmp Pairing

- can pair: `True`
- IN map: `mux_out[group]`
- INB map: `mux_out_b[group]`
- Q map: `dout[group]`
- QB map: `dropped_complementary_output`

## Example Placements

| instance | group | cols | x | y | orientation | macro |
| --- | --- | --- | --- | --- | --- | --- |
| Xcmux_g0 | 0 | 0, 1 | 0.0 | 0.0 | R0 | gen_col_mux_vdd_labeled |
| Xcmux_g1 | 1 | 2, 3 | 1.79 | 0.0 | R0 | gen_col_mux_vdd_labeled |
| Xcmux_g2 | 2 | 4, 5 | 3.58 | 0.0 | R0 | gen_col_mux_vdd_labeled |

## Net Mapping

| OpenYield pin | Local pin | Canonical | Required |
| --- | --- | --- | --- |
| VDD | vdd | vdd | True |
| VSS | gnd | gnd | True |
| SEL | col_sel[group] | column_select | True |
| BL | bl[col0] | bl | True |
| BR | br[col0] | br | True |
| OUT | mux_out[group] | mux_out | True |
| OUTB | mux_out_b[group] | mux_out_b | True |

## Notes

- This plan is generated from repaired alias metadata and existing sense_amp adapter semantics.
- No routing, GDS writer, or standalone placement code is changed.
- Mux ratio greater than one is handled as a grouped semantic plan only.
- Candidate alias uses gen_col_mux_vdd_labeled from the proof GDS.
- Shared rail remains disabled until a separate rail continuity proof exists.
- The placement plan is grouped semantic only when mux_ratio > 1.
- Physical BL/BLB fan-in is intentionally not expanded in this smoke.
- No standalone or routing code paths are changed.
