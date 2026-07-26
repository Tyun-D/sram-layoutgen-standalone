# sram_32x32_wpr1_fd45 Report

- Backend: `standalone`
- Spec: 32 x 32, words/row=1
- Legal words/row choices: `1, 2`
- Size: 39.2225 um x 74.5950 um
- Macro area: 2925.8024 um^2
- Useful array area: 985.4208 um^2
- Utilization: 33.68%
- Built-in DRC-lite: clean (0)
- Full signoff-candidate GDS: `build\full_layout_collection\sram_32x32_wpr1\sram_32x32_wpr1_fd45.gds`
- Presentation GDS: `build\full_layout_collection\sram_32x32_wpr1\sram_32x32_wpr1_fd45.presentation.gds`
- Complete visual-routing GDS: `build\full_layout_collection\sram_32x32_wpr1\sram_32x32_wpr1_fd45.complete.gds`
- Debug GDS: `build\full_layout_collection\sram_32x32_wpr1\sram_32x32_wpr1_fd45.debug.gds`
- Integration DRC GDS: `build\full_layout_collection\sram_32x32_wpr1\sram_32x32_wpr1_fd45.integration.gds`
- Architecture-view GDS: `build\full_layout_collection\sram_32x32_wpr1\sram_32x32_wpr1_fd45.architecture.gds`
- Architecture SVG: `build\full_layout_collection\sram_32x32_wpr1\sram_32x32_wpr1_fd45.architecture.svg`
- Occupancy SVG: `build\full_layout_collection\sram_32x32_wpr1\sram_32x32_wpr1_fd45.occupancy.svg`
- Route-guide debug GDS: `build\full_layout_collection\sram_32x32_wpr1\sram_32x32_wpr1_fd45.route_guides.gds`

## Hardcell usage

- array `cell_1rw`: 1024
- array `dff`: 10
- array `dummy_cell_1rw`: 64
- array `replica_cell_1rw`: 32
- array `sense_amp`: 32
- array `tri_gate`: 32
- array `write_driver`: 32
- instance `dff`: 32
- instance `gen_col_mux`: 32
- instance `gen_delay_inv`: 6
- instance `gen_inv`: 3
- instance `gen_nand2`: 34
- instance `gen_precharge`: 33
- instance `gen_wl_driver`: 32

## Cell bbox measurement

- method: OpenRAM-style dynamic GDS measurement: use the 239/text marker as logical placement pitch/origin when present, and keep the real drawn-geometry bbox for boundary and overhang audits.
- cells where 239/text marker underestimates real geometry: `cell_1rw`, `dff`, `dummy_cell_1rw`, `gen_col_mux`, `gen_delay_inv`, `gen_inv`, `gen_nand2`, `gen_wl_driver`, `replica_cell_1rw`, `sense_amp`, `tri_gate`, `write_driver`
- `cell_1rw` placement pitch source `logical_text_marker_with_physical_geometry`: 0.7050um x 1.3650um
- `cell_1rw` geometry overhang beyond 239 marker: L=0.0950um, B=0.1200um, R=0.0950um, T=0.1000um
- `dff` placement pitch source `logical_text_marker_with_physical_geometry`: 2.8600um x 2.4700um
- `dff` geometry overhang beyond 239 marker: L=0.0000um, B=0.1000um, R=0.0000um, T=0.1000um
- `dummy_cell_1rw` placement pitch source `logical_text_marker_with_physical_geometry`: 0.7050um x 1.3650um
- `dummy_cell_1rw` geometry overhang beyond 239 marker: L=0.0950um, B=0.1200um, R=0.0950um, T=0.1000um
- `gen_col_mux` placement pitch source `logical_text_marker_with_physical_geometry`: 0.7050um x 1.8000um
- `gen_col_mux` geometry overhang beyond 239 marker: L=0.0000um, B=0.0000um, R=0.0325um, T=0.0000um
- `gen_delay_inv` placement pitch source `logical_text_marker_with_physical_geometry`: 0.6875um x 2.4700um
- `gen_delay_inv` geometry overhang beyond 239 marker: L=0.0000um, B=0.0000um, R=0.0550um, T=0.0350um
- `gen_inv` placement pitch source `logical_text_marker_with_physical_geometry`: 0.6875um x 1.3650um
- `gen_inv` geometry overhang beyond 239 marker: L=0.0000um, B=0.0000um, R=0.0550um, T=0.0350um
- `gen_nand2` placement pitch source `logical_text_marker_with_physical_geometry`: 0.9025um x 1.3650um
- `gen_nand2` geometry overhang beyond 239 marker: L=0.0000um, B=0.0000um, R=0.0550um, T=0.0350um
- `gen_precharge` placement pitch source `logical_text_marker_with_physical_geometry`: 0.7050um x 1.3400um
- `gen_precharge` geometry overhang beyond 239 marker: L=0.0000um, B=0.0000um, R=0.0000um, T=0.0000um
- `gen_wl_driver` placement pitch source `logical_text_marker_with_physical_geometry`: 2.9650um x 1.3650um
- `gen_wl_driver` geometry overhang beyond 239 marker: L=0.0000um, B=0.0000um, R=0.0000um, T=0.0350um
- `replica_cell_1rw` placement pitch source `logical_text_marker_with_physical_geometry`: 0.7050um x 1.3650um
- `replica_cell_1rw` geometry overhang beyond 239 marker: L=0.0950um, B=0.1200um, R=0.0950um, T=0.1000um
- `sense_amp` placement pitch source `logical_text_marker_with_physical_geometry`: 0.7050um x 6.0100um
- `sense_amp` geometry overhang beyond 239 marker: L=0.0350um, B=0.0000um, R=0.0350um, T=0.0000um
- `tri_gate` placement pitch source `logical_text_marker_with_physical_geometry`: 0.7050um x 2.9750um
- `tri_gate` geometry overhang beyond 239 marker: L=0.0000um, B=0.0000um, R=0.0350um, T=0.0000um
- `write_driver` placement pitch source `logical_text_marker_with_physical_geometry`: 0.7050um x 4.1750um
- `write_driver` geometry overhang beyond 239 marker: L=0.1000um, B=0.0000um, R=0.0350um, T=0.0000um

## Generated stdcell usage

- none; non-OpenRAM generated stdcell geometry is not emitted in formal GDS

## Remaining abstract blocks

- none

## Replaceable macro registry

- method: Replaceable peripheral macros are emitted only as physical OpenRAM/FreePDK45 GDS references. A future optimized decoder, wordline driver, mux, or control primitive can replace the GDS/SPICE behind the same named contract; missing physical macros are reported rather than drawn as fake cells.
- manifest: `E:\njust\keyan\SRAM Compiler_V2\OpenRAM-stable\deliverables\sram_layoutgen_standalone\technology\freepdk45\replacement_macros.json`
- abstract macro count: `0`
- physical replacement macro count: `6`
- missing physical macro count: `0`
- physical GDS emitted for abstract macros: `True`
- `gen_col_mux`: 32 instances, slot=0.7050um x 1.8000um, state=`physical`
- `gen_delay_inv`: 6 instances, slot=0.6875um x 2.4700um, state=`physical`
- `gen_inv`: 3 instances, slot=0.6875um x 1.3650um, state=`physical`
- `gen_nand2`: 34 instances, slot=0.9025um x 1.3650um, state=`physical`
- `gen_precharge`: 33 instances, slot=0.7050um x 1.3400um, state=`physical`
- `gen_wl_driver`: 32 instances, slot=2.9650um x 1.3650um, state=`physical`

## Peripheral coverage

- `bitcell_array`: 1024
- `column_mux`: 32
- `column_select`: 1
- `control_glue`: 4
- `control_logic`: 10
- `data_dff`: 32
- `delay_chain`: 6
- `dummy_bitcell`: 64
- `precharge`: 32
- `replica_bitline`: 32
- `replica_precharge`: 1
- `row_decoder`: 32
- `sense_amp`: 32
- `tri_gate`: 32
- `wordline_driver`: 32
- `write_driver`: 32
- complete_structural_roles: `True`
- missing_roles: `none`
- top-level route guides: `2008`

## Banked architecture

- bank_style: `contiguous-openram-origin-array`
- compaction strategy: `occupancy-guided compact perimeter margin`
- boundary margin: `0.3425`um (legacy `1.2`um)
- estimated legacy size: `40.9375um x 76.3100um`, area savings `198.1382um^2` (6.34%)
- data DFF packing strategy: `global macro area search`
- selected data DFF grid: `8` columns x `4` rows, estimated macro area `2925.8024um^2`
- applied control subgroup relocation: `True` group=`column_select_logic_bbox`
- control DFF contracts: `9`
- `control_dff_array[0,0]`: `addr[0]` -> `addr_q[0]` -> row/column decode address spine
- `control_dff_array[0,1]`: `addr[1]` -> `addr_q[1]` -> row/column decode address spine
- `control_dff_array[1,0]`: `addr[2]` -> `addr_q[2]` -> row/column decode address spine
- `control_dff_array[1,1]`: `addr[3]` -> `addr_q[3]` -> row/column decode address spine
- `control_dff_array[2,0]`: `addr[4]` -> `addr_q[4]` -> row/column decode address spine
- `control_dff_array[2,1]`: `web` -> `pchg_en` -> pchg_en global enable bus
- `control_dff_array[3,0]`: `csb` -> `sense_en` -> sense_en global enable bus
- `control_dff_array[3,1]`: `web` -> `write_en` -> write_en global enable bus
- row-logic folding strategy: `linear row drivers`
- folded row drivers: `none` using `6` horizontal lanes
- lower_bank_rows: `32`
- upper_bank_rows: `0`
- bank_channel_height_um: `0.0`
- sample_like_floorplan: `True`
- missing architecture modules: `none`
- featured module overlaps: `0`

## SRAM architecture contract

- method: SRAM architecture contract checks over layout metadata, roles, pins, and route geometry.
- physical_column_ordering: `bit_interleaved`
- clean: `True`
- contract_consistent: `False`
- warnings: `6`
- violations: `0`
- organization: addr_width=`5`, row_addr_width=`5`, col_addr_width=`0`, physical_rows=`32`, physical_cols=`32`
- address split: column=`none`; row=`addr[0]`, `addr[1]`, `addr[2]`, `addr[3]`, `addr[4]`
- column mapping rows: `32`
- column mapping preview:
| physical_col | data_bit | col_sel | mux | mux_d | col_sel_net |
|---:|---:|---:|---|---|---|
| 0 | 0 | 0 | `column_mux_0` | `mux_d[0]` | `col_sel[0]` |
| 1 | 1 | 0 | `column_mux_1` | `mux_d[1]` | `col_sel[0]` |
| 2 | 2 | 0 | `column_mux_2` | `mux_d[2]` | `col_sel[0]` |
| 3 | 3 | 0 | `column_mux_3` | `mux_d[3]` | `col_sel[0]` |
| 4 | 4 | 0 | `column_mux_4` | `mux_d[4]` | `col_sel[0]` |
| 5 | 5 | 0 | `column_mux_5` | `mux_d[5]` | `col_sel[0]` |
| 6 | 6 | 0 | `column_mux_6` | `mux_d[6]` | `col_sel[0]` |
| 7 | 7 | 0 | `column_mux_7` | `mux_d[7]` | `col_sel[0]` |
| 8 | 8 | 0 | `column_mux_8` | `mux_d[8]` | `col_sel[0]` |
| 9 | 9 | 0 | `column_mux_9` | `mux_d[9]` | `col_sel[0]` |
| 10 | 10 | 0 | `column_mux_10` | `mux_d[10]` | `col_sel[0]` |
| 11 | 11 | 0 | `column_mux_11` | `mux_d[11]` | `col_sel[0]` |
| 12 | 12 | 0 | `column_mux_12` | `mux_d[12]` | `col_sel[0]` |
| 13 | 13 | 0 | `column_mux_13` | `mux_d[13]` | `col_sel[0]` |
| 14 | 14 | 0 | `column_mux_14` | `mux_d[14]` | `col_sel[0]` |
| 15 | 15 | 0 | `column_mux_15` | `mux_d[15]` | `col_sel[0]` |
| 16 | 16 | 0 | `column_mux_16` | `mux_d[16]` | `col_sel[0]` |
| 17 | 17 | 0 | `column_mux_17` | `mux_d[17]` | `col_sel[0]` |
| 18 | 18 | 0 | `column_mux_18` | `mux_d[18]` | `col_sel[0]` |
| 19 | 19 | 0 | `column_mux_19` | `mux_d[19]` | `col_sel[0]` |
| 20 | 20 | 0 | `column_mux_20` | `mux_d[20]` | `col_sel[0]` |
| 21 | 21 | 0 | `column_mux_21` | `mux_d[21]` | `col_sel[0]` |
| 22 | 22 | 0 | `column_mux_22` | `mux_d[22]` | `col_sel[0]` |
| 23 | 23 | 0 | `column_mux_23` | `mux_d[23]` | `col_sel[0]` |
| 24 | 24 | 0 | `column_mux_24` | `mux_d[24]` | `col_sel[0]` |
| 25 | 25 | 0 | `column_mux_25` | `mux_d[25]` | `col_sel[0]` |
| 26 | 26 | 0 | `column_mux_26` | `mux_d[26]` | `col_sel[0]` |
| 27 | 27 | 0 | `column_mux_27` | `mux_d[27]` | `col_sel[0]` |
| 28 | 28 | 0 | `column_mux_28` | `mux_d[28]` | `col_sel[0]` |
| 29 | 29 | 0 | `column_mux_29` | `mux_d[29]` | `col_sel[0]` |
| 30 | 30 | 0 | `column_mux_30` | `mux_d[30]` | `col_sel[0]` |
| 31 | 31 | 0 | `column_mux_31` | `mux_d[31]` | `col_sel[0]` |
- address_bus_isolation clean: `True`
- top addr pairwise isolated: `True`
- addr_q pairwise isolated: `True`
- addr to addr_q direct short free: `True`
- address real-route shorts: `0`
- address guide-only overlaps: `0`
- suspicious address shapes: `75`
- suspicious addr shape idx=`409` layer=`m3` purpose=`route` net=`addr[0]` name=`addr_0_to_control_dff` real_nets=`['addr[0]']` guide_nets=`[]` vias=`1`
- suspicious addr shape idx=`410` layer=`m2` purpose=`route_guide` net=`addr[0]` name=`addr_0_control_dff_d_drop` real_nets=`[]` guide_nets=`['addr[0]']` vias=`1`
- suspicious addr shape idx=`411` layer=`m2` purpose=`route` net=`addr[0]` name=`addr_0_control_dff_d_via_m2_landing` real_nets=`['addr[0]']` guide_nets=`[]` vias=`1`
- suspicious addr shape idx=`412` layer=`m3` purpose=`route` net=`addr[0]` name=`addr_0_control_dff_d_via_m3_landing` real_nets=`['addr[0]']` guide_nets=`[]` vias=`1`
- suspicious addr shape idx=`413` layer=`via2` purpose=`route_guide` net=`addr[0]` name=`addr_0_control_dff_d_via` real_nets=`[]` guide_nets=`['addr[0]']` vias=`0`
- suspicious addr shape idx=`416` layer=`m2` purpose=`route_guide` net=`addr_q[0]` name=`addr_q_0_control_dff_q_drop` real_nets=`[]` guide_nets=`['addr_q[0]']` vias=`2`
- suspicious addr shape idx=`417` layer=`m3` purpose=`route_guide` net=`addr_q[0]` name=`addr_q_0_to_decoder` real_nets=`[]` guide_nets=`['addr_q[0]']` vias=`2`
- suspicious addr shape idx=`418` layer=`m2` purpose=`route` net=`addr_q[0]` name=`addr_q_0_q_via_m2_landing` real_nets=`['addr_q[0]']` guide_nets=`[]` vias=`1`
- column_addr_to_select clean: `True`
- column_addr_to_select fully_proven_without_guides: `True`
- column_addr_to_select required endpoints: `0`
- column_addr_to_select proven endpoints: `0`
- column_addr_to_select missing endpoints: `0`
- column_addr_to_select used route guides: `0`
- row path contract clean: `True`; warnings=`0`
- column path contract clean: `True`; critical route-guide nets=`128`
- column-select route-guide shapes: `0`
- BL/BR/mux/sense route-guide shapes: `351`
- read_path_to_sense clean: `True`
- read_path_to_sense fully_proven_without_guides: `False`
- read_path_to_sense required endpoints: `352`
- read_path_to_sense proven endpoints: `352`
- read_path_to_sense missing endpoints: `0`
- read_path_to_sense used route guides: `918`
- write_path_to_selected_blbr clean: `False`
- write_path_to_selected_blbr fully_proven_without_guides: `False`
- write_path_to_selected_blbr required endpoints: `96`
- write_path_to_selected_blbr proven endpoints: `32`
- write_path_to_selected_blbr missing endpoints: `64`
- write_path_to_selected_blbr used route guides: `0`
- unselected_column_strong_drive_audit clean: `False`
- unselected strong-drive proven checks: `0`
- unselected strong-drive warnings: `1`
- write path bit `0` cols=`[0]`: din_to_driver=`True`, driver_to_selected_blbr=`False`, unselected_safe=`False`
- write path bit `1` cols=`[1]`: din_to_driver=`True`, driver_to_selected_blbr=`False`, unselected_safe=`False`
- write path bit `2` cols=`[2]`: din_to_driver=`True`, driver_to_selected_blbr=`False`, unselected_safe=`False`
- write path bit `3` cols=`[3]`: din_to_driver=`True`, driver_to_selected_blbr=`False`, unselected_safe=`False`
- write path bit `4` cols=`[4]`: din_to_driver=`True`, driver_to_selected_blbr=`False`, unselected_safe=`False`
- write path bit `5` cols=`[5]`: din_to_driver=`True`, driver_to_selected_blbr=`False`, unselected_safe=`False`
- write path bit `6` cols=`[6]`: din_to_driver=`True`, driver_to_selected_blbr=`False`, unselected_safe=`False`
- write path bit `7` cols=`[7]`: din_to_driver=`True`, driver_to_selected_blbr=`False`, unselected_safe=`False`
- tap/endcap evidence:
- explicit tap cells: none
- explicit endcap cells: none
- explicit tap GDS files: `gen_well_tap.gds`
- explicit endcap GDS files: none
- tap/endcap conclusion: partial evidence: tap-like GDS exists, but no explicit endcap cell was found and no tap/endcap is inserted in the layout; keep risk open.
- contract warning `tap_cells_not_explicit`: No explicit tap/well_tap role is modeled; hardcell-internal tap evidence is not proven by this audit.
- contract warning `endcap_cells_not_explicit`: No explicit endcap role is modeled; boundary/endcap evidence is not proven by this audit.
- contract warning `critical_column_path_uses_route_guides`: Column path still has route-guide intent; do not claim signoff-clean detailed routing.
- contract warning `read_path_to_sense_uses_route_guides`: read_path_to_sense_uses_route_guides
- contract warning `write_path_to_selected_blbr_not_proven`: Write driver to selected BL/BR is not yet proven; this phase audits only and does not force a write-path rewrite.
- contract warning `unselected_column_not_strongly_driven_not_proven`: No transistor-level select isolation proof is available in the current geometry audit.

## Geometry audit

- clean: `True`
- objects outside prBoundary: `0`
- data periphery overhangs: `0`
- allowed data periphery overhangs: `0`
- cell-array pitch violations: `0`
- placed cell bbox overlaps: `0`
- generated/hardcell overlaps: `0`
- generated/hardcell spacing violations (<0.0um): `0`

## Global occupancy map

- method: Exact rectangle decomposition over top-level physical placement objects with module overlays used as semantic labels for a coarse floorplan map.
- occupied area: `2043.6256um^2`
- empty area: `882.1768um^2`
- occupancy ratio: `69.85%`
- largest empty region: `291.8648um^2`
- occupancy SVG: `build\full_layout_collection\sram_32x32_wpr1\sram_32x32_wpr1_fd45.occupancy.svg`
- largest filled roles: `bitcell_array`=981.5956um^2, `data_dff`=244.3584um^2, `sense_amp`=161.1582um^2, `wordline_driver`=133.6450um^2, `write_driver`=112.2240um^2, `control_logic`=83.7680um^2, `dummy_bitcell`=78.5452um^2, `tri_gate`=76.6577um^2, `row_decoder`=45.4840um^2, `column_mux`=42.6243um^2
- empty target 1: area=291.8648um^2, rect=(0.000, 28.677) to (6.657, 72.517), nearest=`row_decode_0`/row_decoder@0.000um, `row_decode_1`/row_decoder@0.000um, `row_decode_10`/row_decoder@0.000um
- empty target 2: area=138.5511um^2, rect=(36.065, 28.657) to (39.222, 72.537), nearest=`dummy_right_array`/dummy_bitcell@0.000um, `replica_bitline_array`/replica_bitline@0.705um, `replica_precharge`/replica_precharge@0.881um
- empty target 3: area=30.4509um^2, rect=(0.000, 23.462) to (11.965, 26.008), nearest=`sense_amp_array`/sense_amp@0.000um, `control_delay_3`/delay_chain@0.000um, `control_delay_4`/delay_chain@0.000um
- empty target 4: area=22.8385um^2, rect=(3.130, 20.878) to (11.965, 23.462), nearest=`control_delay_5`/delay_chain@0.000um, `sense_amp_array`/sense_amp@0.000um, `control_delay_2`/delay_chain@0.290um
- empty target 5: area=21.6788um^2, rect=(2.322, 14.760) to (39.222, 15.348), nearest=`control_glue_1`/control_glue@0.000um, `write_driver_array`/write_driver@0.000um, `tri_gate_array`/tri_gate@0.000um
- empty target 6: area=18.6307um^2, rect=(0.000, 26.008) to (39.222, 26.483), nearest=`column_mux_0`/column_mux@0.000um, `column_mux_1`/column_mux@0.000um, `column_mux_10`/column_mux@0.000um
- coarse map (`.` means empty):
```text
...............1111111111111111111111111112.....
........3.444.566666666666666666666666666678....
........3.444.566666666666666666666666666678....
........3.444.566666666666666666666666666678....
........3.444.566666666666666666666666666678....
........3.444.566666666666666666666666666678....
........3.444.566666666666666666666666666678....
........3.444.566666666666666666666666666678....
........3.444.566666666666666666666666666678....
........3.444.566666666666666666666666666678....
........3.444.566666666666666666666666666678....
........3.444.566666666666666666666666666678....
........3.444.566666666666666666666666666678....
........3.444.566666666666666666666666666678....
........3.444.566666666666666666666666666678....
........3.444.566666666666666666666666666678....
........3.444.566666666666666666666666666678....
........3.444.566666666666666666666666666678....
```
- map legend: 1=precharge_array_bbox, 2=replica_precharge, 3=DECODER, 4=WL_DRIVER, 5=dummy_left_bbox, 6=ARRAY, 7=RBL, 8=dummy_right_bbox, 9=column_select_logic_bbox, A=column_mux_array_bbox, B=sense_amp_array_bbox, C=replica_timing_delay_bbox, D=timing_control_glue_bbox, E=write_driver_array_bbox, F=control_dff_array, G=data_latch_trigate_array_bbox, H=data_dff_array

## Optimization target audit

- method: Exact empty-region decomposition classified by boundary contact, shape aspect ratio, neighboring modules, and existing route/pin context.
- targets reported: `16` / `32`
- categories: edge_trim=16, packing_slot=8, pin_escape_gap=4, routing_channel=4
- safe auto actions: `16`
- target 1: `edge_trim` score=498.432, area=291.8648um^2, rect=(0.000, 28.677) to (6.657, 72.517), risk=`low`, action=Shrink prBoundary or move adjacent modules inward if containment, port side policy, and DRC-lite remain clean.
- target 2: `edge_trim` score=236.611, area=138.5511um^2, rect=(36.065, 28.657) to (39.222, 72.537), risk=`low`, action=Shrink prBoundary or move adjacent modules inward if containment, port side policy, and DRC-lite remain clean.
- target 3: `edge_trim` score=52.003, area=30.4509um^2, rect=(0.000, 23.462) to (11.965, 26.008), risk=`low`, action=Shrink prBoundary or move adjacent modules inward if containment, port side policy, and DRC-lite remain clean.
- target 4: `edge_trim` score=37.022, area=21.6788um^2, rect=(2.322, 14.760) to (39.222, 15.348), risk=`low`, action=Shrink prBoundary or move adjacent modules inward if containment, port side policy, and DRC-lite remain clean.
- target 5: `edge_trim` score=34.709, area=18.6307um^2, rect=(0.000, 26.008) to (39.222, 26.483), risk=`medium`, action=Shrink prBoundary or move adjacent modules inward if containment, port side policy, and DRC-lite remain clean.
- target 6: `edge_trim` score=29.278, area=17.1439um^2, rect=(3.130, 19.523) to (39.222, 19.997), risk=`low`, action=Shrink prBoundary or move adjacent modules inward if containment, port side policy, and DRC-lite remain clean.
- target 7: `edge_trim` score=28.912, area=16.9300um^2, rect=(0.000, 72.912) to (11.922, 74.332), risk=`low`, action=Shrink prBoundary or move adjacent modules inward if containment, port side policy, and DRC-lite remain clean.
- target 8: `packing_slot` score=27.406, area=22.8385um^2, rect=(3.130, 20.878) to (11.965, 23.462), risk=`medium`, action=Evaluate compact DFF/control packing candidates that occupy this slot without changing SRAM array pitch.
- relocation candidates: `7` accepted / `40` checked
- whole TIMING_CONTROL fits packing slot: `False`
- whole TIMING_CONTROL reject: slot 1: slot too short by 20.6750um
- whole TIMING_CONTROL reject: slot 1: whole control macro changes clk/csb/web, addr, column-select, enable, and power route topology
- whole TIMING_CONTROL reject: slot 2: slot too narrow by 0.3025um
- whole TIMING_CONTROL reject: slot 2: slot too short by 20.5900um
- relocation `column_select_logic_bbox` -> slot 8: fits=`True`, slack=(7.907, 0.000)um, slot=(3.130, 18.003) to (11.900, 19.523), risk=`medium`
- relocation `column_select_logic_bbox` -> slot 6: fits=`True`, slack=(4.875, 0.975)um, slot=(6.263, 11.898) to (12.000, 14.393), risk=`medium`
- relocation `column_select_logic_bbox` -> slot 1: fits=`True`, slack=(7.973, 1.065)um, slot=(3.130, 20.878) to (11.965, 23.462), risk=`medium`
- relocation `column_select_logic_bbox` -> slot 2: fits=`True`, slack=(4.875, 1.150)um, slot=(6.263, 0.343) to (12.000, 3.013), risk=`medium`
- relocation `column_select_logic_bbox` -> slot 3: fits=`True`, slack=(4.875, 1.150)um, slot=(6.263, 3.212) to (12.000, 5.883), risk=`medium`
- relocation `column_select_logic_bbox` -> slot 4: fits=`True`, slack=(4.875, 1.150)um, slot=(6.263, 6.082) to (12.000, 8.752), risk=`medium`

## Left-side compound whitespace

- method: Named two-zone whitespace audit for decoder_left_upper_void plus lower_middle_vertical_packing_voids. Candidate acceptance is conservative: only already-routed moves with clean downstream audits are accepted.
- cleanly_identified: `True`
- total_area: `455.4646um^2`
- decoder_left_upper_void: area=`326.5837um^2`, rect=(0.000, 23.462) to (6.657, 72.517)
- lower_middle_vertical_packing_voids: area=`128.8810um^2`, rect_count=`7`
- lower void rect=(0.000, 23.462) to (11.965, 26.008), area=`30.4509um^2`
- lower void rect=(3.130, 20.878) to (11.965, 23.462), area=`22.8385um^2`
- lower void rect=(6.263, 8.953) to (12.000, 11.623), area=`15.3191um^2`
- lower void rect=(6.263, 6.082) to (12.000, 8.752), area=`15.3191um^2`
- lower void rect=(6.263, 3.212) to (12.000, 5.883), area=`15.3191um^2`
- lower void rect=(6.263, 0.343) to (12.000, 3.013), area=`15.3191um^2`
- lower void rect=(6.263, 11.898) to (12.000, 14.393), area=`14.3151um^2`
- can_reduce_macro_area_by_filling_only: `False`
- estimated_area_reduction_um2: `0.0000`
- why_not_l_shaped: The problem is a compound set of one large upper-left void plus several separated lower/middle packing slots, not one contiguous L-shaped polygon.
- why_not_upper_only: The lower/middle slots between the control/timing column and data path remain significant and are part of the visible waste.
- why_not_simple_prboundary_trim: The lower-left contains control/timing modules, and the memory/WL/decoder/data groups still define the macro envelope; shrinking prBoundary alone would clip real geometry or pins.

## Two-zone floorplan candidates

- accepted_candidate: `None`
- `Candidate A: fill decoder_left_upper_void`: `rejected`, classification=`rejected_due_to_no_boundary_improvement`, area_reduction=`0.0000um^2`, reason=Moving control/timing modules into the upper void would not reduce macro width or height and would require clk/addr/control/power route re-synthesis.
- `Candidate B: fill lower_middle_vertical_packing_voids`: `rejected`, classification=`previous_failed_zero_delta`, area_reduction=`0.0000um^2`, reason=Rejected as an optimization result because the prior two-zone run had zero macro-area, largest-empty-region, and total-empty-area improvement.
- `Candidate C: two-zone control repartition`: `rejected`, classification=`rejected_due_to_audit_failure`, area_reduction=`0.0000um^2`, reason=The full movable_control_timing_group spans clk/csb/web/addr/control fanout; moving it needs route and power re-synthesis outside this phase.
- `Candidate D: control repacking + core-left-shift feasibility`: `rejected`, classification=`rejected_due_to_no_boundary_improvement`, area_reduction=`0.0000um^2`, reason=core_left_shift_rejected_due_to_control_column_blockers
- `Candidate E: bottom-boundary compaction feasibility`: `rejected`, classification=`rejected_due_to_no_boundary_improvement`, area_reduction=`0.0000um^2`, reason=Bottom boundary is still pinned by data/control DFF arrays, lower data path lanes, pins, and power shapes.
- `Candidate F: vertical data DFF repacking into decoder_left_upper_void`: `rejected`, classification=`rejected_due_to_fit_or_scale_gate`, area_reduction=`0.0000um^2`, reason=The 2x8 data-DFF candidate was not legal or not enabled for this SRAM size.
- `Candidate G: move control DFF array/subgroups`: `rejected`, classification=`rejected_due_to_address_route_risk`, area_reduction=`0.0000um^2`, reason=Control-DFF movement changes addr/addr_q topology and is deferred because address_bus_isolation and column_addr_to_select are already clean.
- moved `column_select_logic_bbox` into `lower_middle_vertical_packing_voids`: before=(0.263, 18.003) to (1.085, 19.483), after=(3.355, 26.483) to (4.178, 27.962), move=(3.092, 8.480)um

## Two-zone area vs occupancy objective

- primary_objective: `minimize macro_area`
- classification: `['rejected_due_to_no_boundary_improvement']`
- width_reduction: `0.0000um`
- height_reduction: `0.0000um`
- area_reduction: `0.0000um^2`
- occupancy_improvement: `0.0000%`
- largest_empty_region_reduction: `0.0000um^2`
- total_empty_area_reduction: `0.0000um^2`
- before_floorplan_svg: `build\full_layout_collection\sram_32x32_wpr1\sram_32x32_wpr1_fd45.before_floorplan.svg`
- after_floorplan_svg: `build\full_layout_collection\sram_32x32_wpr1\sram_32x32_wpr1_fd45.after_floorplan.svg`
- left_side_compound_whitespace_svg: `build\full_layout_collection\sram_32x32_wpr1\sram_32x32_wpr1_fd45.left_side_compound_whitespace.svg`
- two_zone_repacking_svg: `build\full_layout_collection\sram_32x32_wpr1\sram_32x32_wpr1_fd45.two_zone_repacking.svg`
- moved_module_arrows_svg: `build\full_layout_collection\sram_32x32_wpr1\sram_32x32_wpr1_fd45.moved_module_arrows.svg`
- accepted_rejected_candidates_svg: `build\full_layout_collection\sram_32x32_wpr1\sram_32x32_wpr1_fd45.accepted_rejected_candidates.svg`

## OpenRAM-style array mirror audit

- method: OpenRAM FreePDK45 bitcell placement mirror.x=True, mirror.y=False: alternate rows use MX while columns remain R0
- clean: `True`
- missing required row mirrors: `0`
- arrays using OpenRAM row mirror rule: `bitcell_array` row_offset=0; `dummy_left_array` row_offset=0; `dummy_right_array` row_offset=0; `replica_bitline_array` row_offset=0

## OpenRAM-style array layer audit

- method: Array occupancy audit: generic repeated cells must not overlap, while native OpenRAM storage cells may use designed boundary stitching at abstract bitcell pitch; external KLayout DRC remains the final legality check.
- clean: `False`
- illegal same-layer overlaps from pitch: `7`
- overlap `sense_amp_array` layer `pwell`: x=0.0000um, y=0.0000um
- overlap `sense_amp_array` layer `nwell`: x=0.0000um, y=0.0000um
- overlap `write_driver_array` layer `pwell`: x=0.0000um, y=0.0000um
- overlap `write_driver_array` layer `via1`: x=0.0000um, y=0.0000um
- overlap `write_driver_array` layer `m2`: x=0.0000um, y=0.0000um
- overlap `tri_gate_array` layer `pwell`: x=0.0000um, y=0.0000um
- overlap `tri_gate_array` layer `nwell`: x=0.0000um, y=0.0000um
- layer 6 / `vtg` summary: `bitcell_array`: x overlap (-0.18um), y overlap (-0.2um); `dummy_left_array`: x single_column (Noneum), y overlap (-0.2um); `dummy_right_array`: x single_column (Noneum), y overlap (-0.2um); `replica_bitline_array`: x single_column (Noneum), y overlap (-0.2um); `control_dff_array`: x spaced (0.2um), y spaced (0.2um); `sense_amp_array`: x spaced (0.265um), y single_row (Noneum); `write_driver_array`: x spaced (0.13um), y single_row (Noneum); `tri_gate_array`: x spaced (0.28um), y single_row (Noneum)

## Architecture module map

- `ARRAY`: (11.905, 28.658) to (34.655, 72.537), area=998.2700um^2
- `DECODER`: (6.657, 28.678) to (7.695, 72.517), area=45.4840um^2
- `RBL`: (34.465, 28.658) to (35.360, 72.537), area=39.2726um^2
- `SA_SWITCH_LATCH_MUX`: (12.000, 11.897) to (38.780, 26.008), area=377.8658um^2
- `TIMING_CONTROL`: (0.263, 0.243) to (6.262, 23.462), area=139.3200um^2
- `WL_DRIVER`: (7.895, 28.653) to (10.940, 72.543), area=133.6450um^2
- `column_mux_array_bbox`: (11.887, 26.483) to (34.560, 28.363), area=42.6243um^2
- `column_select_logic_bbox`: (3.355, 26.483) to (4.178, 27.962), area=1.2173um^2
- `control_dff_array`: (0.343, 0.243) to (6.262, 14.393), area=83.7680um^2
- `data_dff_array`: (12.000, 0.343) to (36.280, 11.422), area=269.0224um^2
- `data_latch_trigate_array_bbox`: (12.000, 11.897) to (38.780, 14.760), area=76.6577um^2
- `dummy_left_bbox`: (11.200, 28.658) to (12.095, 72.537), area=39.2726um^2
- `dummy_right_bbox`: (35.170, 28.658) to (36.065, 72.537), area=39.2726um^2
- `precharge_array_bbox`: (11.922, 72.912) to (34.562, 74.332), area=32.1488um^2
- `replica_timing_delay_bbox`: (0.263, 18.002) to (3.130, 23.462), area=15.6565um^2
- `sense_amp_array_bbox`: (11.965, 19.997) to (38.780, 26.008), area=161.1582um^2
- `timing_control_glue_bbox`: (0.263, 14.617) to (2.323, 17.777), area=6.5096um^2
- `write_driver_array_bbox`: (11.900, 15.347) to (38.780, 19.522), area=112.2240um^2

## Route metrics

- drawn routes: m1=879.5100um, m2=3515.8025um, m3=207.5610um, m4=2143.3625um, poly=2.8800um, via1=21.5800um, via2=23.5950um, via3=20.8600um
- route guides: m1=71.1364um, m2=4816.6823um, m3=1111.8167um, via1=1.4300um, via2=21.6450um
- routes plus guides: m1=950.6464um, m2=8332.4848um, m3=1319.3778um, m4=2143.3625um, poly=2.8800um, via1=23.0100um, via2=45.2400um, via3=20.8600um

## Routing track selection

- col_select algorithm: `DRC-aware candidate route-guide promotion scoring`
- evaluated candidates: `45`
- selected y0: `28.3225`
- score remaining candidate guides: `67`

## Route-guide promotion

- initial route guides: `2241`
- promoted to clean routes: `233`
- remaining route guides: `2008`
- promoted by layer: m1=184, m2=18, m3=31
- remaining by layer: m1=86, m2=1023, m3=544, via1=22, via2=333
- blocked by reason: missing drawn upper/lower route stack=340, same-layer spacing conflict=1668

## GDS hierarchy

- `cell_1rw` SREF count: 1024
- `dff` SREF count: 42
- `dummy_cell_1rw` SREF count: 64
- `gen_col_mux` SREF count: 32
- `gen_delay_inv` SREF count: 6
- `gen_inv` SREF count: 3
- `gen_nand2` SREF count: 34
- `gen_precharge` SREF count: 33
- `gen_wl_driver` SREF count: 32
- `replica_cell_1rw` SREF count: 32
- `sense_amp` SREF count: 32
- `sram_1rw_32x16_freepdk45_contact_10` SREF count: 13
- `sram_1rw_32x16_freepdk45_contact_11` SREF count: 11
- `sram_1rw_32x16_freepdk45_contact_12` SREF count: 5
- `sram_1rw_32x16_freepdk45_contact_13` SREF count: 5
- `sram_1rw_32x16_freepdk45_contact_14` SREF count: 8
- `sram_1rw_32x16_freepdk45_contact_17` SREF count: 6
- `sram_1rw_32x16_freepdk45_contact_22` SREF count: 1
- `sram_1rw_32x16_freepdk45_contact_23` SREF count: 4
- `sram_1rw_32x16_freepdk45_contact_24` SREF count: 1
- `sram_1rw_32x16_freepdk45_nmos_m1_w0_090_sm1_dm1_da_p` SREF count: 2
- `sram_1rw_32x16_freepdk45_nmos_m1_w0_180_sactive_dm1` SREF count: 2
- `sram_1rw_32x16_freepdk45_nmos_m1_w0_180_sm1_dactive` SREF count: 2
- `sram_1rw_32x16_freepdk45_nmos_m1_w0_720_sm1_dm1` SREF count: 2
- `sram_1rw_32x16_freepdk45_nmos_m6_w0_120_sm1_dm1_da_p` SREF count: 1
- `sram_1rw_32x16_freepdk45_pinv_0` SREF count: 1
- `sram_1rw_32x16_freepdk45_pmos_m1_w0_270_sm1_dm1` SREF count: 7
- `sram_1rw_32x16_freepdk45_pmos_m1_w0_270_sm1_dm1_da_p` SREF count: 2
- `sram_1rw_32x16_freepdk45_pmos_m6_w0_360_sm1_dm1_da_p` SREF count: 1
- `sram_1rw_32x16_freepdk45_pnand2` SREF count: 1
- `tri_gate` SREF count: 32
- `write_driver` SREF count: 32
- generated stdcells are emitted as GDS child structures: `gen_col_mux`, `gen_delay_inv`, `gen_inv`, `gen_nand2`, `gen_precharge`, `gen_wl_driver`

## Layer audit

- matches bundled FreePDK45 layers: `True`
- unknown_clean_boundary_lpps: `none`
- unknown_clean_text_lpps: `none`
- unknown_route_guide_boundary_lpps: `none`
- unknown_route_guide_text_lpps: `none`
- clean boundary LPPs: 1/0=358, 10/0=284, 11/0=1293, 12/0=495, 13/0=1360, 13/2=35, 14/0=363, 15/0=463, 15/2=37, 16/0=298, 17/0=120, 17/2=2, 2/0=57, 239/0=38, 3/0=45, 4/0=67, 5/0=58, 6/0=64, 9/0=345
- clean text LPPs: 1/0=2, 11/0=67, 13/0=31, 13/1=35, 15/1=37, 17/1=2, 9/0=9

## Hardcell pin access

- `cell_1rw` pins (7 labels): Q, Q_bar, bl, br, gnd, vdd, wl
- `dff` pins (5 labels): D, Q, clk, gnd, vdd
- `dummy_cell_1rw` pins (5 labels): bl, br, gnd, vdd, wl
- `gen_col_mux` pins (9 labels): D, G, S, bl, bl_out, br, br_out, gnd, sel
- `gen_delay_inv` pins (10 labels): A, D, G, S, Z, gnd, vdd
- `gen_inv` pins (10 labels): A, D, G, S, Z, gnd, vdd
- `gen_nand2` pins (14 labels): A, B, D, G, S, Z, gnd, vdd
- `gen_precharge` pins (7 labels): D, G, S, bl, br, en_bar, vdd
- `gen_wl_driver` pins (35 labels): A, B, D, G, S, Z, gnd, vdd
- `replica_cell_1rw` pins (5 labels): bl, br, gnd, vdd, wl
- `sense_amp` pins (7 labels): bl, br, dout, en, gnd, vdd
- `tri_gate` pins (7 labels): en, en_bar, gnd, in, out, vdd
- `write_driver` pins (6 labels): bl, br, din, en, gnd, vdd

## Abstract macro pin model

- `gen_col_mux` pins (6 labels): BL, BR, OUT, SEL, gnd, vdd
- `gen_delay_inv` pins (4 labels): A, Z, gnd, vdd
- `gen_inv` pins (4 labels): A, Z, gnd, vdd
- `gen_nand2` pins (5 labels): A, B, Z, gnd, vdd
- `gen_precharge` pins (5 labels): BL, BR, EN, gnd, vdd
- `gen_wl_driver` pins (4 labels): A, Z, gnd, vdd

## Connectivity audit

- method: bbox intersection between generated instances and top-level route/route_guide shapes
- all generated roles touched: `True`
- roles with no route/guide touch: `none`
- roles with partial route/guide touch: `none`
- `column_mux`: 32/32 touched (100.0%)
- `column_select`: 1/1 touched (100.0%)
- `control_glue`: 4/4 touched (100.0%)
- `delay_chain`: 6/6 touched (100.0%)
- `precharge`: 32/32 touched (100.0%)
- `replica_precharge`: 1/1 touched (100.0%)
- `row_decoder`: 32/32 touched (100.0%)
- `wordline_driver`: 32/32 touched (100.0%)

## Drawn route connectivity audit

- method: bbox intersection between generated instances and drawn top-level route shapes
- all generated roles touched by drawn routes: `True`
- roles with no drawn-route touch: `none`
- roles with partial drawn-route touch: `none`
- `column_mux`: 32/32 touched (100.0%)
- `column_select`: 1/1 touched (100.0%)
- `control_glue`: 4/4 touched (100.0%)
- `delay_chain`: 6/6 touched (100.0%)
- `precharge`: 32/32 touched (100.0%)
- `replica_precharge`: 1/1 touched (100.0%)
- `row_decoder`: 32/32 touched (100.0%)
- `wordline_driver`: 32/32 touched (100.0%)

## Generated pin routing audit

- drawn-route signal pin coverage: `100.0%`
- all generated signal pins covered by drawn routes: `True`
- missing generated signal pins: `0`

## Semantic connectivity audit

- method: Same-net route, route-guide, and pin geometry intersection against required top pins, DFF pins, and named route waypoints.
- clean: `True`
- violations: `0`

## Port placement audit

- method: Perimeter pin side classification against SRAM port-side policy.
- clean: `True`
- violations: `0`
- `dout` lane: ordered=`True`, axis=`y`, pitch=0.5700um, variation=0.0000um
- `addr` lane: ordered=`True`, axis=`y`, pitch=1.3650um, variation=0.0000um

## Power grid audit

- method: Hardcell/replacement macro vdd/gnd TEXT pin probes against same-net route, route-guide, or top pin geometry.
- clean: `True`
- checked endpoints: `2795`
- `vdd`: 1366/1366 (100.0%)
- `gnd`: 1429/1429 (100.0%)

## Cell abutment contract

- method: Cell abutment contract extracted from real GDS TEXT pins, cell bbox, power rail edge reach, and boundary-side pin access risk for the cells used in this SRAM macro.
- cells with power rails: `dff, gen_delay_inv, gen_inv, gen_nand2, gen_wl_driver, sense_amp, tri_gate, write_driver`
- cells abuttable: `gen_inv, gen_nand2, gen_wl_driver`
- cells not abuttable: `dff, gen_delay_inv, sense_amp, tri_gate, write_driver`
- row-height family `2.470um`: `dff, gen_delay_inv`
- row-height family `1.365um`: `gen_inv, gen_nand2, gen_wl_driver`
- row-height family `6.010um`: `sense_amp`
- row-height family `2.975um`: `tri_gate`
- row-height family `4.175um`: `write_driver`
- pin-access risk `sense_amp.dout` layer=`m2` x=0.0285um

## Row peripheral abutment audit

- method: Row-side peripheral abutment audit: compare observable final gaps against legal abutment pitch, check decoder-driver packing, verify OpenRAM-style linear WL-driver column placement, and verify WL-driver rows stay aligned with storage rows.
- clean: `True`
- wl_driver_placement_style: `openram_linear_abutted_column`
- disable_folded_wl_driver_placement: `True`
- row_logic_folding_strategy: `linear row drivers`
- folded row drivers: `none`
- row_driver_sequence_monotonic: `True`
- logical_row_pitch_um: `1.365`
- driver_slot_height_um: `1.365`
- row_pitch_delta_um: `0.0`
- max_decoder_to_driver_gap_um: `0.335`
- max_driver_to_array_gap_um: `0.16`
- wl_driver_column_bbox: `{'x0': 7.975, 'y0': 28.757500000000004, 'x1': 10.94, 'y1': 72.4375}`
- abutted instance pairs: `31`
- non-abutted instance pairs: `6`
- compaction candidates: `0`
- intentional routing channels: `1`
- WL driver rows `0` -> `1` gap=`0.0`um abutted=`True`
- WL driver rows `1` -> `2` gap=`0.0`um abutted=`True`
- WL driver rows `2` -> `3` gap=`0.0`um abutted=`True`
- WL driver rows `3` -> `4` gap=`-0.0`um abutted=`True`
- WL driver rows `4` -> `5` gap=`0.0`um abutted=`True`
- WL driver rows `5` -> `6` gap=`0.0`um abutted=`True`
- WL driver rows `6` -> `7` gap=`-0.0`um abutted=`True`
- WL driver rows `7` -> `8` gap=`0.0`um abutted=`True`
- WL driver rows `8` -> `9` gap=`0.0`um abutted=`True`
- WL driver rows `9` -> `10` gap=`0.0`um abutted=`True`
- WL driver rows `10` -> `11` gap=`0.0`um abutted=`True`
- WL driver rows `11` -> `12` gap=`-0.0`um abutted=`True`
- WL driver rows `12` -> `13` gap=`0.0`um abutted=`True`
- WL driver rows `13` -> `14` gap=`0.0`um abutted=`True`
- WL driver rows `14` -> `15` gap=`-0.0`um abutted=`True`
- WL driver rows `15` -> `16` gap=`0.0`um abutted=`True`
- row `0` driver `wordline_driver_0` net=`wl[0]` center delta=`0.0`um handoff delta=`-0.5155`um driver_to_array_gap=`0.16`um
- row `1` driver `wordline_driver_1` net=`wl[1]` center delta=`-0.0`um handoff delta=`0.5155`um driver_to_array_gap=`0.16`um
- row `2` driver `wordline_driver_2` net=`wl[2]` center delta=`0.0`um handoff delta=`-0.5155`um driver_to_array_gap=`0.16`um
- row `3` driver `wordline_driver_3` net=`wl[3]` center delta=`0.0`um handoff delta=`0.5155`um driver_to_array_gap=`0.16`um
- row `4` driver `wordline_driver_4` net=`wl[4]` center delta=`0.0`um handoff delta=`-0.5155`um driver_to_array_gap=`0.16`um
- row `5` driver `wordline_driver_5` net=`wl[5]` center delta=`0.0`um handoff delta=`0.5155`um driver_to_array_gap=`0.16`um
- row `6` driver `wordline_driver_6` net=`wl[6]` center delta=`0.0`um handoff delta=`-0.5155`um driver_to_array_gap=`0.16`um
- row `7` driver `wordline_driver_7` net=`wl[7]` center delta=`0.0`um handoff delta=`0.5155`um driver_to_array_gap=`0.16`um
- row `8` driver `wordline_driver_8` net=`wl[8]` center delta=`0.0`um handoff delta=`-0.5155`um driver_to_array_gap=`0.16`um
- row `9` driver `wordline_driver_9` net=`wl[9]` center delta=`0.0`um handoff delta=`0.5155`um driver_to_array_gap=`0.16`um
- row `10` driver `wordline_driver_10` net=`wl[10]` center delta=`0.0`um handoff delta=`-0.5155`um driver_to_array_gap=`0.16`um
- row `11` driver `wordline_driver_11` net=`wl[11]` center delta=`0.0`um handoff delta=`0.5155`um driver_to_array_gap=`0.16`um

## Row-side power audit

- method: Row-side replacement macro power audit over real route/pin/via connected components; route_guide-only reachability is warning-only and does not count as clean.
- clean: `True`
- checked instances: `75`
- checked power pins: `150`
- missing vdd pins: `0`
- missing gnd pins: `0`
- guide-only power connections: `0`

## WL path physical audit

- method: Per-row physical proof from wordline_driver[row].Z through real route geometry into wl_row_rail and storage WL pins.
- clean: `True`
- wl_pairwise_isolation: `True`
- wl_driver_output_shorts: `0`
- guide_only_hits: `0`
- row `0` driver=`wordline_driver_0` net=`wl[0]` proven `35`/`35` shorted_with_rows=`[]` fully_proven_without_guides=`True`
- row `1` driver=`wordline_driver_1` net=`wl[1]` proven `35`/`35` shorted_with_rows=`[]` fully_proven_without_guides=`True`
- row `2` driver=`wordline_driver_2` net=`wl[2]` proven `35`/`35` shorted_with_rows=`[]` fully_proven_without_guides=`True`
- row `3` driver=`wordline_driver_3` net=`wl[3]` proven `35`/`35` shorted_with_rows=`[]` fully_proven_without_guides=`True`
- row `4` driver=`wordline_driver_4` net=`wl[4]` proven `35`/`35` shorted_with_rows=`[]` fully_proven_without_guides=`True`
- row `5` driver=`wordline_driver_5` net=`wl[5]` proven `35`/`35` shorted_with_rows=`[]` fully_proven_without_guides=`True`
- row `6` driver=`wordline_driver_6` net=`wl[6]` proven `35`/`35` shorted_with_rows=`[]` fully_proven_without_guides=`True`
- row `7` driver=`wordline_driver_7` net=`wl[7]` proven `35`/`35` shorted_with_rows=`[]` fully_proven_without_guides=`True`
- row `8` driver=`wordline_driver_8` net=`wl[8]` proven `35`/`35` shorted_with_rows=`[]` fully_proven_without_guides=`True`
- row `9` driver=`wordline_driver_9` net=`wl[9]` proven `35`/`35` shorted_with_rows=`[]` fully_proven_without_guides=`True`
- row `10` driver=`wordline_driver_10` net=`wl[10]` proven `35`/`35` shorted_with_rows=`[]` fully_proven_without_guides=`True`
- row `11` driver=`wordline_driver_11` net=`wl[11]` proven `35`/`35` shorted_with_rows=`[]` fully_proven_without_guides=`True`
- row `12` driver=`wordline_driver_12` net=`wl[12]` proven `35`/`35` shorted_with_rows=`[]` fully_proven_without_guides=`True`
- row `13` driver=`wordline_driver_13` net=`wl[13]` proven `35`/`35` shorted_with_rows=`[]` fully_proven_without_guides=`True`
- row `14` driver=`wordline_driver_14` net=`wl[14]` proven `35`/`35` shorted_with_rows=`[]` fully_proven_without_guides=`True`
- row `15` driver=`wordline_driver_15` net=`wl[15]` proven `35`/`35` shorted_with_rows=`[]` fully_proven_without_guides=`True`

## Array power stitching audit

- method: Per-row array boundary power proof from dummy/replica boundary cell vdd/gnd TEXT-pin access through real route/via stitching into explicit left/right top-level straps.
- clean: `True`
- row vdd rails: `32`/`32`
- row gnd rails: `32`/`32`
- `left_vdd_strap` present=`True` connected_to_top_ring=`True`
- `left_gnd_strap` present=`True` connected_to_top_ring=`True`
- `right_vdd_strap` present=`True` connected_to_top_ring=`True`
- `right_gnd_strap` present=`True` connected_to_top_ring=`True`
- rows missing vdd connection: `0`
- rows missing gnd connection: `0`
- guide-only array power connections: `0`

## Global power consistency audit

- method: Top-level power consistency audit over real route/pin/via components: array straps and row-side macro rails must resolve into the same vdd/gnd anchor components without vdd-gnd shorts.
- clean: `True`
- array_vdd_connected_to_top_vdd: `True`
- array_gnd_connected_to_top_gnd: `True`
- peripheral_vdd_connected_to_top_vdd: `True`
- peripheral_gnd_connected_to_top_gnd: `True`
- array_and_peripheral_vdd_same_component: `True`
- array_and_peripheral_gnd_same_component: `True`
- vdd_gnd_short_free: `True`

## Power junction topology audit

- method: Power junction topology audit over named array-boundary strap ties and row-side power-entry routes; a clean junction must connect directly at the crossing by same-layer overlap or a local via bridge.
- clean: `True`
- checked_junctions: `278`
- direct_junctions: `278`
- indirect_junctions: `0`
- missing_junctions: `0`
- unnecessary_jogs: `0`
- via_arrays_at_junctions: `246`
- guide_only_junctions: `0`

## Array top/bottom boundary audit

- method: Inspect modeled storage arrays for explicit top/bottom dummy or cap rows and compare with local OpenRAM references when available.
- clean: `False`
- valid_rows: `32`
- dummy_left_cols: `1`
- dummy_right_cols: `1`
- dummy_top_rows: `0`
- dummy_bottom_rows: `0`
- top_cap_rows: `0`
- bottom_cap_rows: `0`
- missing_top_dummy_or_cap: `True`
- missing_bottom_dummy_or_cap: `True`
- openram_reference_policy: available=`True` uses_top_bottom_dummy_rows=`True`
- reference_evidence_file: `E:\njust\keyan\SRAM Compiler_V2\OpenRAM-stable\build\deliverable_smoke2_2x16\sram_2x16_b1_wpr1_ctrl2col_freepdk45.sp`
- recommendation: Current standalone array models left/right dummy columns only. Keep this as a flagged risk and prepare a top/bottom dummy-row proposal before inserting new rows.

## Well/substrate tie audit

- method: Conservative well/body/substrate tie audit from used storage-family GDS layer/text evidence plus explicit tap-cell insertion checks. Structural layer presence counts as evidence but not full proof when no explicit tap/tie marker is found.
- clean: `False`
- nwell_tie_evidence: `3`
- pwell_or_substrate_tie_evidence: `3`
- bitcell_internal_tap_evidence: `2`
- dummy_internal_tap_evidence: `1`
- explicit_tap_instances: `0`
- gen_well_tap_available: `True`
- gen_well_tap_gds: `E:\njust\keyan\SRAM Compiler_V2\OpenRAM-stable\deliverables\sram_layoutgen_standalone\technology\freepdk45\gds_lib\gen_well_tap.gds`
- tap_inserted_in_layout: `False`
- rows_without_nearby_tap: `0`
- columns_without_nearby_tap: `0`
- risk `tap_cells_not_explicit`: No explicit tap/well_tap instance is inserted in the generated layout.
- risk `gen_well_tap_available_but_not_inserted`: `gen_well_tap.gds` exists at `E:\njust\keyan\SRAM Compiler_V2\OpenRAM-stable\deliverables\sram_layoutgen_standalone\technology\freepdk45\gds_lib\gen_well_tap.gds`, but the current layout does not instantiate it.
- risk `internal_tap_not_explicitly_labeled`: Used storage-family GDS cells expose vdd/gnd labels and well/contact layers, but no explicit tap/tie text marker was found.

## Boundary/tap decision

- method: Decision table derived from boundary-row evidence, local OpenRAM reference policy, and explicit tap/tie evidence.
- top_bottom_dummy_needed: `True`
- top_bottom_cap_needed: `False`
- explicit_tap_needed: `True`
- explicit_endcap_needed: `False`
- can_reuse_existing_dummy_cell: `True`
- can_reuse_gen_well_tap: `True`
- required_new_cells: `[]`
- risk_if_not_inserted: Local OpenRAM references instantiate top/bottom dummy rows, and explicit tap insertion is not yet proven in this generator.
- recommended_next_action: Prepare a geometry-feasible proposal for top/bottom dummy rows and explicit well-tap insertion without changing array pitch yet.

## Column peripheral abutment analysis

- method: Column-side macro abutment analysis without changing bit_interleaved column ordering or current column pitch.
- write_driver_abuttable: `False`
- sense_amp_abuttable: `False`
- tri_gate_abuttable: `False`
- precharge_pitch_locked: `False`
- col_mux_pitch_locked: `False`
- `write_driver`: cell is not safely abuttable under current pin-access contract
- `sense_amp`: cell is not safely abuttable under current pin-access contract
- `tri_gate`: cell is not safely abuttable under current pin-access contract

## Visual/debug view audit

- visual_confusion_warnings: `1`
- shape purposes: `{'boundary': 1, 'module': 18, 'pin': 74, 'route': 4975, 'route_guide': 2008}`
- presentation.gds excludes `route_guide`; debug.gds and route_guides.gds retain guide/debug overlays for inspection.
- `route_guides_present_in_debug_views`: Debug/route-guide GDS still contains non-signoff guide geometry that can look connected in KLayout.

## Visual power topology warnings

- weird_indirect_power_junctions: `0`
- guide_only_power_marks: `0`
- power_labels_without_geometry: `0`
- missing_tap_visual_evidence: `3`
- `tap_not_inserted`: No explicit tap instance is visible in the generated layout.
- `top_boundary_no_dummy_or_cap`: No explicit top dummy/cap row is visible above the valid bitcell array.
- `bottom_boundary_no_dummy_or_cap`: No explicit bottom dummy/cap row is visible below the valid bitcell array.

## GDS labels

- total text labels: 183
- `addr[0]`: 1
- `addr[1]`: 1
- `addr[2]`: 1
- `addr[3]`: 1
- `addr[4]`: 1
- `clk`: 2
- `csb`: 1
- `din[0]`: 1
- `din[10]`: 1
- `din[11]`: 1
- `din[12]`: 1
- `din[13]`: 1
- `din[14]`: 1
- `din[15]`: 1
- `din[16]`: 1
- `din[17]`: 1
- `din[18]`: 1
- `din[19]`: 1
- `din[1]`: 1
- `din[20]`: 1
- `din[21]`: 1
- `din[22]`: 1
- `din[23]`: 1
- `din[24]`: 1
- `din[25]`: 1
- `din[26]`: 1
- `din[27]`: 1
- `din[28]`: 1
- `din[29]`: 1
- `din[2]`: 1
- `din[30]`: 1
- `din[31]`: 1
- `din[3]`: 1
- `din[4]`: 1
- `din[5]`: 1
- `din[6]`: 1
- `din[7]`: 1
- `din[8]`: 1
- `din[9]`: 1
- `dout[0]`: 1
- `dout[10]`: 1
- `dout[11]`: 1
- `dout[12]`: 1
- `dout[13]`: 1
- `dout[14]`: 1
- `dout[15]`: 1
- `dout[16]`: 1
- `dout[17]`: 1
- `dout[18]`: 1
- `dout[19]`: 1
- `dout[1]`: 1
- `dout[20]`: 1
- `dout[21]`: 1
- `dout[22]`: 1
- `dout[23]`: 1
- `dout[24]`: 1
- `dout[25]`: 1
- `dout[26]`: 1
- `dout[27]`: 1
- `dout[28]`: 1
- `dout[29]`: 1
- `dout[2]`: 1
- `dout[30]`: 1
- `dout[31]`: 1
- `dout[3]`: 1
- `dout[4]`: 1
- `dout[5]`: 1
- `dout[6]`: 1
- `dout[7]`: 1
- `dout[8]`: 1
- `dout[9]`: 1
- `gnd`: 17
- `vdd`: 15
- `web`: 1

## Signoff status

- signoff_ready: `False`
- criterion no_abstract_instances: `True`
- criterion all_structural_roles_present: `True`
- criterion drawn_routes_touch_generated_roles: `True`
- criterion drawn_routes_cover_generated_signal_pins: `True`
- criterion built_in_drc_clean: `True`
- criterion layers_match_freepdk45: `True`
- criterion architecture_floorplan_clean: `True`
- criterion geometry_clean: `True`
- criterion cell_array_mirroring_clean: `True`
- criterion cell_array_layers_clean: `False`
- criterion structural_consistency_clean: `True`
- criterion semantic_connectivity_clean: `True`
- criterion port_placement_clean: `True`
- criterion power_grid_clean: `True`
- criterion row_side_power_clean: `True`
- criterion array_power_stitching_clean: `True`
- criterion global_power_consistency_clean: `True`
- criterion architecture_contract_clean: `True`
- criterion architecture_contract_consistent: `False`
- criterion address_bus_isolation_clean: `True`
- criterion wl_path_physical_clean: `True`
- criterion optimization_targets_reported: `True`
- criterion used_cells_are_openram_or_bundled_freepdk45_gds: `True`
- criterion external_drc_clean: `False`
- criterion external_lvs_clean: `False`
- criterion external_pex_available: `False`
- blocker: cell-array layer audit found physical same-layer overlap from too-small pitch
- blocker: architecture contract audit has warnings requiring human review
- blocker: top-level route guides show intended connectivity but must be replaced by DRC-clean detailed routing
- blocker: external signoff DRC/LVS/PEX has not been run; install KLayout/Magic/netgen or project signoff tools
- blocker: SPICE netlist is structural; complete LVS equivalence must be proven with extracted netlist
