# openyield_raw_16x16_wpr1_fd45 Report

- Backend: `standalone`
- Spec: 16 x 16, words/row=1
- Legal words/row choices: `1`
- Size: 28.4525 um x 55.9550 um
- Macro area: 1592.0596 um^2
- Useful array area: 246.3552 um^2
- Utilization: 15.47%
- Built-in DRC-lite: violations (46)
- Full signoff-candidate GDS: `/data1/qujh/work/sram_layoutgen_step45_clean/outputs/M11_openyield_config_variation/current_supported_config/_variation_generation/openyield_raw_16x16_wpr1_fd45.gds`
- Presentation GDS: `/data1/qujh/work/sram_layoutgen_step45_clean/outputs/M11_openyield_config_variation/current_supported_config/_variation_generation/openyield_raw_16x16_wpr1_fd45.presentation.gds`
- Complete visual-routing GDS: `/data1/qujh/work/sram_layoutgen_step45_clean/outputs/M11_openyield_config_variation/current_supported_config/_variation_generation/openyield_raw_16x16_wpr1_fd45.complete.gds`
- Debug GDS: `/data1/qujh/work/sram_layoutgen_step45_clean/outputs/M11_openyield_config_variation/current_supported_config/_variation_generation/openyield_raw_16x16_wpr1_fd45.debug.gds`
- Integration DRC GDS: `/data1/qujh/work/sram_layoutgen_step45_clean/outputs/M11_openyield_config_variation/current_supported_config/_variation_generation/openyield_raw_16x16_wpr1_fd45.integration.gds`
- Architecture-view GDS: `/data1/qujh/work/sram_layoutgen_step45_clean/outputs/M11_openyield_config_variation/current_supported_config/_variation_generation/openyield_raw_16x16_wpr1_fd45.architecture.gds`
- Architecture SVG: `/data1/qujh/work/sram_layoutgen_step45_clean/outputs/M11_openyield_config_variation/current_supported_config/_variation_generation/openyield_raw_16x16_wpr1_fd45.architecture.svg`
- Occupancy SVG: `/data1/qujh/work/sram_layoutgen_step45_clean/outputs/M11_openyield_config_variation/current_supported_config/_variation_generation/openyield_raw_16x16_wpr1_fd45.occupancy.svg`
- Route-guide debug GDS: `/data1/qujh/work/sram_layoutgen_step45_clean/outputs/M11_openyield_config_variation/current_supported_config/_variation_generation/openyield_raw_16x16_wpr1_fd45.route_guides.gds`

## Hardcell usage

- array `cell_1rw`: 256
- array `dummy_cell_1rw`: 32
- array `replica_cell_1rw`: 16
- array `sense_amp`: 16
- array `tri_gate`: 16
- array `write_driver`: 16
- instance `dff`: 24
- instance `gen_col_mux_vdd_labeled`: 16
- instance `gen_delay_inv`: 6
- instance `gen_inv`: 3
- instance `gen_nand2`: 18
- instance `gen_precharge`: 17
- instance `gen_wl_driver`: 16

## Cell bbox measurement

- method: OpenRAM-style dynamic GDS measurement: use the 239/text marker as logical placement pitch/origin when present, and keep the real drawn-geometry bbox for boundary and overhang audits.
- cells where 239/text marker underestimates real geometry: `cell_1rw`, `dff`, `dummy_cell_1rw`, `gen_col_mux_vdd_labeled`, `gen_delay_inv`, `gen_inv`, `gen_nand2`, `gen_wl_driver`, `replica_cell_1rw`, `sense_amp`, `tri_gate`, `write_driver`
- `cell_1rw` placement pitch source `logical_text_marker_with_physical_geometry`: 0.7050um x 1.3650um
- `cell_1rw` geometry overhang beyond 239 marker: L=0.0950um, B=0.1200um, R=0.0950um, T=0.1000um
- `dff` placement pitch source `logical_text_marker_with_physical_geometry`: 2.8600um x 2.4700um
- `dff` geometry overhang beyond 239 marker: L=0.0000um, B=0.1000um, R=0.0000um, T=0.1000um
- `dummy_cell_1rw` placement pitch source `logical_text_marker_with_physical_geometry`: 0.7050um x 1.3650um
- `dummy_cell_1rw` geometry overhang beyond 239 marker: L=0.0950um, B=0.1200um, R=0.0950um, T=0.1000um
- `gen_col_mux_vdd_labeled` placement pitch source `logical_text_marker_with_physical_geometry`: 0.7050um x 1.8000um
- `gen_col_mux_vdd_labeled` geometry overhang beyond 239 marker: L=0.0000um, B=0.0000um, R=0.0325um, T=0.0000um
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

## OpenYield column mux adapter

- enabled: `True`
- local macro: `gen_col_mux_vdd_labeled`
- source macro: `gen_col_mux`
- repaired alias metadata: `/data1/qujh/work/sram_layoutgen_step45_clean/technology/freepdk45/openyield_repaired_macro_aliases.json`
- power status: `vdd_label_present`
- safe_for_physical_mapping: `True`
- safe_for_shared_rail: `False`
- uses repaired alias: `True`
- shared rail enabled: `False`
- routing changed: `False`
- gds writer changed: `False`
- write_driver changed: `False`
- wordline_driver changed: `False`
- limited placement plan count: `16`

## OpenYield write driver adapter

- enabled: `True`
- local macro: `write_driver`
- contract path: `/data1/qujh/work/sram_layoutgen_step45_clean/docs/openyield_module_contracts.json`
- power status: `vdd_gnd_metadata_present`
- safe_for_physical_mapping: `True`
- safe_for_shared_rail: `False`
- requires_netlist_rewrite: `False`
- placement count: `16`
- adapter applied to placement: `False`
- routing changed: `False`
- gds writer changed: `False`
- shared rail enabled: `False`
- write_driver changed: `False`
- column mux changed: `True`
- senseamp changed: `True`
- storage aggregation enabled: `True`

## OpenYield wordline driver adapter

- enabled: `True`
- local macro: `gen_wl_driver`
- contract path: `/data1/qujh/work/sram_layoutgen_step45_clean/docs/openyield_module_contracts.json`
- power status: `vdd_gnd_metadata_present`
- safe_for_physical_mapping: `True`
- safe_for_shared_rail: `False`
- can enter limited placement: `True`
- b polarity: `high_active`
- semantic confirmation: `confirmed_active_high`
- placement count: `16`
- adapter applied to placement: `True`
- routing changed: `False`
- gds writer changed: `False`
- shared rail enabled: `False`
- write_driver changed: `False`
- column mux changed: `True`
- senseamp changed: `True`
- storage aggregation enabled: `True`
- decoder changed: `False`
- time control changed: `False`

## Remaining abstract blocks

- none

## Replaceable macro registry

- method: Replaceable peripheral macros are emitted only as physical OpenRAM/FreePDK45 GDS references. A future optimized decoder, wordline driver, mux, or control primitive can replace the GDS/SPICE behind the same named contract; missing physical macros are reported rather than drawn as fake cells.
- manifest: `/data1/qujh/work/sram_layoutgen_step45_clean/technology/freepdk45/replacement_macros.json`
- abstract macro count: `0`
- physical replacement macro count: `6`
- missing physical macro count: `0`
- physical GDS emitted for abstract macros: `True`
- `gen_col_mux_vdd_labeled`: 16 instances, slot=0.7050um x 1.8000um, state=`physical`
- `gen_delay_inv`: 6 instances, slot=0.6875um x 2.4700um, state=`physical`
- `gen_inv`: 3 instances, slot=0.6875um x 1.3650um, state=`physical`
- `gen_nand2`: 18 instances, slot=0.9025um x 1.3650um, state=`physical`
- `gen_precharge`: 17 instances, slot=0.7050um x 1.3400um, state=`physical`
- `gen_wl_driver`: 16 instances, slot=2.9650um x 1.3650um, state=`physical`

## Peripheral coverage

- `bitcell_array`: 256
- `column_mux`: 16
- `column_select`: 1
- `control_glue`: 4
- `control_logic`: 8
- `data_dff`: 16
- `delay_chain`: 6
- `dummy_bitcell`: 32
- `precharge`: 16
- `replica_bitline`: 16
- `replica_precharge`: 1
- `row_decoder`: 16
- `sense_amp`: 16
- `tri_gate`: 16
- `wordline_driver`: 16
- `write_driver`: 16
- complete_structural_roles: `True`
- missing_roles: `none`
- top-level route guides: `901`

## Banked architecture

- bank_style: `contiguous-openram-origin-array`
- compaction strategy: `occupancy-guided compact perimeter margin`
- boundary margin: `0.3425`um (legacy `1.2`um)
- estimated legacy size: `30.1675um x 57.6700um`, area savings `147.7001um^2` (8.49%)
- data DFF packing strategy: `global macro area search`
- selected data DFF grid: `4` columns x `4` rows, estimated macro area `1592.0596um^2`
- row-logic folding strategy: `gate_row_packer_compacted_decoder_rows`
- folded row drivers: `none` using `1` horizontal lanes
- lower_bank_rows: `16`
- upper_bank_rows: `0`
- bank_channel_height_um: `0.0`
- sample_like_floorplan: `True`
- missing architecture modules: `none`
- featured module overlaps: `0`

## Geometry audit

- clean: `False`
- objects outside prBoundary: `0`
- data periphery overhangs: `0`
- allowed data periphery overhangs: `0`
- cell-array pitch violations: `0`
- placed cell bbox overlaps: `36`
- generated/hardcell overlaps: `0`
- generated/hardcell spacing violations (<0.0um): `0`
- placed cell overlap `row_decode_0` / `row_decode_1` (`row_decoder` / `row_decoder`)
- placed cell overlap `wordline_driver_0` / `wordline_driver_1` (`wordline_driver` / `wordline_driver`)
- placed cell overlap `row_decode_1` / `row_decode_2` (`row_decoder` / `row_decoder`)
- placed cell overlap `wordline_driver_1` / `wordline_driver_2` (`wordline_driver` / `wordline_driver`)
- placed cell overlap `row_decode_2` / `row_decode_3` (`row_decoder` / `row_decoder`)

## Global occupancy map

- method: Exact rectangle decomposition over top-level physical placement objects with module overlays used as semantic labels for a coarse floorplan map.
- occupied area: `949.3351um^2`
- empty area: `642.7246um^2`
- occupancy ratio: `59.63%`
- largest empty region: `149.7105um^2`
- occupancy SVG: `/data1/qujh/work/sram_layoutgen_step45_clean/outputs/M11_openyield_config_variation/current_supported_config/_variation_generation/openyield_raw_16x16_wpr1_fd45.occupancy.svg`
- largest filled roles: `bitcell_array`=358.5728um^2, `data_dff`=122.1792um^2, `sense_amp`=85.3420um^2, `wordline_driver`=68.6267um^2, `control_logic`=61.0896um^2, `write_driver`=59.5564um^2, `dummy_bitcell`=44.8216um^2, `tri_gate`=40.5473um^2, `column_mux`=24.5904um^2, `row_decoder`=23.3308um^2
- empty target 1: area=149.7105um^2, rect=(0.000, 28.677) to (6.657, 51.165), nearest=`row_decode_0`/row_decoder@0.000um, `row_decode_1`/row_decoder@0.000um, `row_decode_10`/row_decoder@0.000um
- empty target 2: area=51.9626um^2, rect=(0.000, 21.733) to (12.155, 26.008), nearest=`sense_amp_array`/sense_amp@0.000um, `control_delay_3`/delay_chain@0.000um, `control_delay_4`/delay_chain@0.000um
- empty target 3: area=28.0840um^2, rect=(0.000, 51.190) to (11.200, 53.697), nearest=`dummy_left_array`/dummy_bitcell@0.000um, `wordline_driver_15`/wordline_driver@0.000um, `row_decode_15`/row_decoder@0.025um
- empty target 4: area=27.9121um^2, rect=(2.123, 11.898) to (12.190, 14.670), nearest=`control_glue_1`/control_glue@0.000um, `control_glue_3`/control_glue@0.000um, `tri_gate_array`/tri_gate@0.000um
- empty target 5: area=27.3546um^2, rect=(2.730, 16.600) to (12.090, 19.523), nearest=`control_delay_2`/delay_chain@0.000um, `control_delay_5`/delay_chain@0.000um, `write_driver_array`/write_driver@0.000um
- empty target 6: area=22.7057um^2, rect=(0.000, 26.483) to (12.078, 28.363), nearest=`column_mux_0`/column_mux@0.000um, `wordline_driver_0`/wordline_driver@0.290um, `dummy_left_array`/dummy_bitcell@0.295um
- coarse map (`.` means empty):
```text
....................111111111111.11.11.11.11.2..
...................34444444444444444444444444566
...................34444444444444444444444444566
...........7788888.34444444444444444444444444566
...........7788888.34444444444444444444444444566
...........7788888.34444444444444444444444444566
...........7788888.34444444444444444444444444566
...........7788888.34444444444444444444444444566
...........7788888.34444444444444444444444444566
...........7788888.34444444444444444444444444566
...........7788888.34444444444444444444444444566
...........7788888.34444444444444444444444444566
...........7788888.34444444444444444444444444566
...........7788888.34444444444444444444444444566
...........7788888.34444444444444444444444444566
...........7788888.34444444444444444444444444566
....................999999999999999999999.99....
.....................AAAAAAAAAAAAAAAAAAAAAAA....
```
- map legend: 1=precharge_array_bbox, 2=replica_precharge, 3=dummy_left_bbox, 4=ARRAY, 5=RBL, 6=dummy_right_bbox, 7=DECODER, 8=WL_DRIVER, 9=column_mux_array_bbox, A=sense_amp_array_bbox, B=replica_timing_delay_bbox, C=write_driver_array_bbox, D=timing_control_glue_bbox, E=data_latch_trigate_array_bbox, F=control_dff_array, G=data_dff_array

## OpenRAM-style array mirror audit

- method: OpenRAM FreePDK45 bitcell placement mirror.x=True, mirror.y=False: alternate rows use MX while columns remain R0. When limited OpenYield storage aggregation is explicitly enabled, storage cells follow the configured row_orientation_policy while keeping peripheral arrays on the legacy path.
- clean: `True`
- missing required row mirrors: `0`
- arrays using OpenRAM row mirror rule: `bitcell_array` row_offset=0; `dummy_left_array` row_offset=0; `dummy_right_array` row_offset=0; `replica_bitline_array` row_offset=0

## OpenRAM-style array layer audit

- method: Array occupancy audit: generic repeated cells must not overlap, while native OpenRAM storage cells may use designed boundary stitching at abstract bitcell pitch; external KLayout DRC remains the final legality check.
- clean: `False`
- illegal same-layer overlaps from pitch: `5`
- overlap `sense_amp_array` layer `pwell`: x=0.0000um, y=0.0000um
- overlap `sense_amp_array` layer `nwell`: x=0.0000um, y=0.0000um
- overlap `write_driver_array` layer `pwell`: x=0.0000um, y=0.0000um
- overlap `write_driver_array` layer `nwell`: x=0.0000um, y=0.0000um
- overlap `tri_gate_array` layer `pwell`: x=0.0000um, y=0.0000um
- layer 6 / `vtg` summary: `bitcell_array`: x spaced (0.01um), y abut (0.0um); `dummy_left_array`: x single_column (Noneum), y abut (-0.0um); `dummy_right_array`: x single_column (Noneum), y abut (-0.0um); `replica_bitline_array`: x single_column (Noneum), y abut (-0.0um); `sense_amp_array`: x spaced (0.32um), y single_row (Noneum); `write_driver_array`: x spaced (0.185um), y single_row (Noneum); `tri_gate_array`: x spaced (0.335um), y single_row (Noneum)

## Architecture module map

- `ARRAY`: (12.095, 28.658) to (26.415, 53.698), area=358.5728um^2
- `DECODER`: (6.657, 28.678) to (7.695, 51.165), area=23.3308um^2
- `RBL`: (26.415, 28.658) to (27.310, 53.697), area=22.4108um^2
- `SA_SWITCH_LATCH_MUX`: (12.190, 11.897) to (26.355, 26.008), area=199.8682um^2
- `TIMING_CONTROL`: (0.263, 0.243) to (6.062, 21.732), area=124.6420um^2
- `WL_DRIVER`: (7.695, 28.653) to (10.740, 51.190), area=68.6267um^2
- `column_mux_array_bbox`: (12.077, 26.483) to (26.320, 28.363), area=26.7759um^2
- `column_select_logic_bbox`: (0.263, 14.895) to (1.085, 16.375), area=1.2173um^2
- `control_dff_array`: (0.343, 0.243) to (6.062, 11.523), area=64.5216um^2
- `data_dff_array`: (12.190, 0.243) to (23.630, 11.523), area=129.0432um^2
- `data_latch_trigate_array_bbox`: (12.190, 11.897) to (26.355, 14.760), area=40.5473um^2
- `dummy_left_bbox`: (11.200, 28.658) to (12.095, 53.697), area=22.4108um^2
- `dummy_right_bbox`: (27.310, 28.658) to (28.205, 53.697), area=22.4108um^2
- `precharge_array_bbox`: (12.112, 54.273) to (26.322, 55.693), area=20.1782um^2
- `replica_timing_delay_bbox`: (0.263, 16.600) to (2.730, 21.732), area=12.6644um^2
- `sense_amp_array_bbox`: (12.155, 19.997) to (26.355, 26.008), area=85.3420um^2
- `timing_control_glue_bbox`: (0.263, 11.748) to (2.123, 14.670), area=5.4359um^2
- `write_driver_array_bbox`: (12.090, 15.347) to (26.355, 19.522), area=59.5564um^2

## Route metrics

- drawn routes: m1=279.3000um, m2=32.9325um, m3=70.2545um, m4=334.1300um, poly=1.4400um, via1=2.0800um, via2=2.0800um
- route guides: m1=30.9232um, m2=1404.4970um, m3=630.4067um, m4=364.6825um, via1=1.5600um, via2=9.3600um
- routes plus guides: m1=310.2232um, m2=1437.4295um, m3=700.6612um, m4=698.8125um, poly=1.4400um, via1=3.6400um, via2=11.4400um

## Routing track selection

- col_select algorithm: `DRC-aware candidate route-guide promotion scoring`
- evaluated candidates: `32`
- selected y0: `28.2825`
- score remaining candidate guides: `35`

## Route-guide promotion

- initial route guides: `1030`
- promoted to clean routes: `129`
- remaining route guides: `901`
- promoted by layer: m1=106, m2=10, m3=13
- remaining by layer: m1=56, m2=412, m3=252, m4=13, via1=24, via2=144
- blocked by reason: missing drawn upper/lower route stack=163, same-layer spacing conflict=738

## GDS hierarchy

- `cell_1rw` SREF count: 256
- `dff` SREF count: 24
- `dummy_cell_1rw` SREF count: 32
- `gen_delay_inv` SREF count: 6
- `gen_inv` SREF count: 3
- `gen_nand2` SREF count: 18
- `gen_precharge` SREF count: 17
- `gen_wl_driver` SREF count: 16
- `replica_cell_1rw` SREF count: 16
- `sense_amp` SREF count: 16
- `sram_1rw_32x16_freepdk45_contact_10` SREF count: 11
- `sram_1rw_32x16_freepdk45_contact_11` SREF count: 11
- `sram_1rw_32x16_freepdk45_contact_12` SREF count: 5
- `sram_1rw_32x16_freepdk45_contact_13` SREF count: 5
- `sram_1rw_32x16_freepdk45_contact_14` SREF count: 8
- `sram_1rw_32x16_freepdk45_contact_17` SREF count: 1
- `sram_1rw_32x16_freepdk45_contact_22` SREF count: 1
- `sram_1rw_32x16_freepdk45_contact_23` SREF count: 4
- `sram_1rw_32x16_freepdk45_nmos_m1_w0_090_sm1_dm1_da_p` SREF count: 2
- `sram_1rw_32x16_freepdk45_nmos_m1_w0_180_sactive_dm1` SREF count: 2
- `sram_1rw_32x16_freepdk45_nmos_m1_w0_180_sm1_dactive` SREF count: 2
- `sram_1rw_32x16_freepdk45_nmos_m6_w0_120_sm1_dm1_da_p` SREF count: 1
- `sram_1rw_32x16_freepdk45_pinv_0` SREF count: 1
- `sram_1rw_32x16_freepdk45_pmos_m1_w0_270_sm1_dm1` SREF count: 7
- `sram_1rw_32x16_freepdk45_pmos_m1_w0_270_sm1_dm1_da_p` SREF count: 2
- `sram_1rw_32x16_freepdk45_pmos_m6_w0_360_sm1_dm1_da_p` SREF count: 1
- `sram_1rw_32x16_freepdk45_pnand2` SREF count: 1
- `tri_gate` SREF count: 16
- `write_driver` SREF count: 16
- generated stdcells are emitted as GDS child structures: `gen_delay_inv`, `gen_inv`, `gen_nand2`, `gen_precharge`, `gen_wl_driver`

## Layer audit

- matches bundled FreePDK45 layers: `True`
- unknown_clean_boundary_lpps: `none`
- unknown_clean_text_lpps: `none`
- unknown_route_guide_boundary_lpps: `none`
- unknown_route_guide_text_lpps: `none`
- clean boundary LPPs: 1/0=356, 10/0=283, 11/0=694, 12/0=195, 13/0=396, 13/2=19, 14/0=32, 15/0=96, 15/2=20, 17/0=7, 17/2=2, 2/0=54, 239/0=35, 3/0=45, 4/0=66, 5/0=57, 6/0=63, 9/0=325
- clean text LPPs: 1/0=2, 11/0=64, 13/0=27, 13/1=19, 15/1=20, 17/1=2, 9/0=7

## Hardcell pin access

- `cell_1rw` pins (7 labels): Q, Q_bar, bl, br, gnd, vdd, wl
- `dff` pins (5 labels): D, Q, clk, gnd, vdd
- `dummy_cell_1rw` pins (5 labels): bl, br, gnd, vdd, wl
- `gen_col_mux_vdd_labeled` pins (10 labels): D, G, S, bl, bl_out, br, br_out, gnd, sel, vdd
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

- `gen_col_mux_vdd_labeled` pins (2 labels): gnd, vdd
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
- `column_mux`: 16/16 touched (100.0%)
- `column_select`: 1/1 touched (100.0%)
- `control_glue`: 4/4 touched (100.0%)
- `delay_chain`: 6/6 touched (100.0%)
- `precharge`: 16/16 touched (100.0%)
- `replica_precharge`: 1/1 touched (100.0%)
- `row_decoder`: 16/16 touched (100.0%)
- `wordline_driver`: 16/16 touched (100.0%)

## Drawn route connectivity audit

- method: bbox intersection between generated instances and drawn top-level route shapes
- all generated roles touched by drawn routes: `True`
- roles with no drawn-route touch: `none`
- roles with partial drawn-route touch: `none`
- `column_mux`: 16/16 touched (100.0%)
- `column_select`: 1/1 touched (100.0%)
- `control_glue`: 4/4 touched (100.0%)
- `delay_chain`: 6/6 touched (100.0%)
- `precharge`: 16/16 touched (100.0%)
- `replica_precharge`: 1/1 touched (100.0%)
- `row_decoder`: 16/16 touched (100.0%)
- `wordline_driver`: 16/16 touched (100.0%)

## Generated pin routing audit

- drawn-route signal pin coverage: `100.0%`
- all generated signal pins covered by drawn routes: `True`
- missing generated signal pins: `0`

## GDS labels

- total text labels: 141
- `addr[0]`: 1
- `addr[1]`: 1
- `addr[2]`: 1
- `addr[3]`: 1
- `clk`: 2
- `csb`: 1
- `din[0]`: 1
- `din[10]`: 1
- `din[11]`: 1
- `din[12]`: 1
- `din[13]`: 1
- `din[14]`: 1
- `din[15]`: 1
- `din[1]`: 1
- `din[2]`: 1
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
- `dout[1]`: 1
- `dout[2]`: 1
- `dout[3]`: 1
- `dout[4]`: 1
- `dout[5]`: 1
- `dout[6]`: 1
- `dout[7]`: 1
- `dout[8]`: 1
- `dout[9]`: 1
- `gnd`: 16
- `vdd`: 15
- `web`: 1

## Signoff status

- signoff_ready: `False`
- criterion no_abstract_instances: `True`
- criterion all_structural_roles_present: `True`
- criterion drawn_routes_touch_generated_roles: `True`
- criterion drawn_routes_cover_generated_signal_pins: `True`
- criterion built_in_drc_clean: `False`
- criterion layers_match_freepdk45: `True`
- criterion architecture_floorplan_clean: `True`
- criterion geometry_clean: `False`
- criterion cell_array_mirroring_clean: `True`
- criterion cell_array_layers_clean: `False`
- criterion structural_consistency_clean: `False`
- criterion used_cells_are_openram_or_bundled_freepdk45_gds: `False`
- criterion external_drc_clean: `False`
- criterion external_lvs_clean: `False`
- criterion external_pex_available: `False`
- blocker: geometry audit found placement outside prBoundary or module overhang
- blocker: cell-array layer audit found physical same-layer overlap from too-small pitch
- blocker: structural audit found loose abutment, unused column mux/precharge, or bitline misalignment
- blocker: some used cells are missing GDS or come from synthetic non-OpenRAM generated-cell geometry
- blocker: top-level route guides show intended connectivity but must be replaced by DRC-clean detailed routing
- blocker: external signoff DRC/LVS/PEX has not been run; install KLayout/Magic/netgen or project signoff tools
- blocker: SPICE netlist is structural; complete LVS equivalence must be proven with extracted netlist
