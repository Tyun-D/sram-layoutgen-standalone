# legacy_baseline Report

- Backend: `standalone`
- Spec: 8 x 64, words/row=4
- Legal words/row choices: `1, 2, 4`
- Size: 36.6225 um x 45.9500 um
- Macro area: 1682.8039 um^2
- Useful array area: 492.7104 um^2
- Utilization: 29.28%
- Built-in DRC-lite: clean (0)
- Full signoff-candidate GDS: `/data1/qujh/work/sram_layoutgen_step45_clean/outputs/layout_prototype/baseline_legacy/legacy_baseline.gds`
- Presentation GDS: `/data1/qujh/work/sram_layoutgen_step45_clean/outputs/layout_prototype/baseline_legacy/legacy_baseline.presentation.gds`
- Complete visual-routing GDS: `/data1/qujh/work/sram_layoutgen_step45_clean/outputs/layout_prototype/baseline_legacy/legacy_baseline.complete.gds`
- Debug GDS: `/data1/qujh/work/sram_layoutgen_step45_clean/outputs/layout_prototype/baseline_legacy/legacy_baseline.debug.gds`
- Integration DRC GDS: `/data1/qujh/work/sram_layoutgen_step45_clean/outputs/layout_prototype/baseline_legacy/legacy_baseline.integration.gds`
- Architecture-view GDS: `/data1/qujh/work/sram_layoutgen_step45_clean/outputs/layout_prototype/baseline_legacy/legacy_baseline.architecture.gds`
- Architecture SVG: `/data1/qujh/work/sram_layoutgen_step45_clean/outputs/layout_prototype/baseline_legacy/legacy_baseline.architecture.svg`
- Occupancy SVG: `/data1/qujh/work/sram_layoutgen_step45_clean/outputs/layout_prototype/baseline_legacy/legacy_baseline.occupancy.svg`
- Route-guide debug GDS: `/data1/qujh/work/sram_layoutgen_step45_clean/outputs/layout_prototype/baseline_legacy/legacy_baseline.route_guides.gds`

## Hardcell usage

- array `cell_1rw`: 512
- array `dff`: 10
- array `dummy_cell_1rw`: 32
- array `replica_cell_1rw`: 16
- array `sense_amp`: 8
- array `tri_gate`: 8
- array `write_driver`: 8
- instance `dff`: 8
- instance `gen_col_mux`: 32
- instance `gen_delay_inv`: 6
- instance `gen_inv`: 2
- instance `gen_nand2`: 22
- instance `gen_precharge`: 33
- instance `gen_wl_driver`: 16

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

## OpenYield column mux adapter

- enabled: `False`
- local macro: `gen_col_mux`
- source macro: `gen_col_mux`
- repaired alias metadata: `None`
- power status: `legacy_metadata_only`
- safe_for_physical_mapping: `False`
- safe_for_shared_rail: `False`
- uses repaired alias: `False`
- shared rail enabled: `False`
- routing changed: `False`
- gds writer changed: `False`
- write_driver changed: `False`
- wordline_driver changed: `False`
- limited placement plan count: `0`

## OpenYield write driver adapter

- enabled: `False`
- local macro: `write_driver`
- contract path: `None`
- power status: `legacy_metadata_only`
- safe_for_physical_mapping: `False`
- safe_for_shared_rail: `False`
- requires_netlist_rewrite: `False`
- placement count: `0`
- adapter applied to placement: `False`
- routing changed: `False`
- gds writer changed: `False`
- shared rail enabled: `False`
- write_driver changed: `False`
- column mux changed: `False`
- senseamp changed: `False`
- storage aggregation enabled: `False`

## OpenYield wordline driver adapter

- enabled: `False`
- local macro: `gen_wl_driver`
- contract path: `None`
- power status: `legacy_metadata_only`
- safe_for_physical_mapping: `False`
- safe_for_shared_rail: `False`
- can enter limited placement: `False`
- b polarity: `None`
- semantic confirmation: `None`
- placement count: `0`
- adapter applied to placement: `False`
- routing changed: `False`
- gds writer changed: `False`
- shared rail enabled: `False`
- write_driver changed: `False`
- column mux changed: `False`
- senseamp changed: `False`
- storage aggregation enabled: `False`
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
- `gen_col_mux`: 32 instances, slot=0.7050um x 1.8000um, state=`physical`
- `gen_delay_inv`: 6 instances, slot=0.6875um x 2.4700um, state=`physical`
- `gen_inv`: 2 instances, slot=0.6875um x 1.3650um, state=`physical`
- `gen_nand2`: 22 instances, slot=0.9025um x 1.3650um, state=`physical`
- `gen_precharge`: 33 instances, slot=0.7050um x 1.3400um, state=`physical`
- `gen_wl_driver`: 16 instances, slot=2.9650um x 1.3650um, state=`physical`

## Peripheral coverage

- `bitcell_array`: 512
- `column_mux`: 32
- `column_select`: 4
- `control_glue`: 4
- `control_logic`: 10
- `data_dff`: 8
- `delay_chain`: 6
- `dummy_bitcell`: 32
- `precharge`: 32
- `replica_bitline`: 16
- `replica_precharge`: 1
- `row_decoder`: 16
- `sense_amp`: 8
- `tri_gate`: 8
- `wordline_driver`: 16
- `write_driver`: 8
- complete_structural_roles: `True`
- missing_roles: `none`
- top-level route guides: `991`

## Banked architecture

- bank_style: `contiguous-openram-origin-array`
- compaction strategy: `occupancy-guided compact perimeter margin`
- boundary margin: `0.3425`um (legacy `1.2`um)
- estimated legacy size: `38.3375um x 47.6650um`, area savings `144.5531um^2` (7.91%)
- data DFF packing strategy: `global macro area search`
- selected data DFF grid: `8` columns x `1` rows, estimated macro area `1682.8039um^2`
- row-logic folding strategy: `fold top row drivers into occupancy gaps above precharge`
- folded row drivers: `14, 15` using `6` horizontal lanes
- lower_bank_rows: `16`
- upper_bank_rows: `0`
- bank_channel_height_um: `0.0`
- sample_like_floorplan: `False`
- missing architecture modules: `none`
- featured module overlaps: `3`

## Geometry audit

- clean: `True`
- objects outside prBoundary: `0`
- data periphery overhangs: `0`
- allowed data periphery overhangs: `1`
- cell-array pitch violations: `0`
- placed cell bbox overlaps: `0`
- generated/hardcell overlaps: `0`
- generated/hardcell spacing violations (<0.0um): `0`
- allowed overhang `data_dff_array` beyond `SA_SWITCH_LATCH_MUX`: 3.8000um (occupancy_guided_global_data_dff_packing)

## Global occupancy map

- method: Exact rectangle decomposition over top-level physical placement objects with module overlays used as semantic labels for a coarse floorplan map.
- occupied area: `1158.7932um^2`
- empty area: `524.0107um^2`
- occupancy ratio: `68.86%`
- largest empty region: `24.8964um^2`
- occupancy SVG: `/data1/qujh/work/sram_layoutgen_step45_clean/outputs/layout_prototype/baseline_legacy/legacy_baseline.occupancy.svg`
- largest filled roles: `bitcell_array`=493.0348um^2, `sense_amp`=123.2952um^2, `write_driver`=85.9215um^2, `control_logic`=83.7680um^2, `wordline_driver`=73.3236um^2, `data_dff`=61.0896um^2, `tri_gate`=58.6240um^2, `column_mux`=42.6243um^2, `dummy_bitcell`=39.4516um^2, `precharge`=32.1488um^2
- empty target 1: area=24.8964um^2, rect=(32.480, 11.387) to (36.623, 17.398), nearest=`sense_amp_array`/sense_amp@0.000um, `write_driver_array`/write_driver@0.475um, `column_mux_29`/column_mux@0.475um
- empty target 2: area=23.7376um^2, rect=(20.850, 44.102) to (36.623, 45.608), nearest=`wordline_driver_15`/wordline_driver@0.000um, `precharge_12`/precharge@0.220um, `precharge_13`/precharge@0.220um
- empty target 3: area=23.5366um^2, rect=(6.263, 6.737) to (11.900, 10.912), nearest=`write_driver_array`/write_driver@0.000um, `control_dff_array`/control_logic@0.000um, `sense_amp_array`/sense_amp@0.479um
- empty target 4: area=17.8365um^2, rect=(6.263, 6.150) to (36.623, 6.737), nearest=`tri_gate_array`/tri_gate@0.000um, `write_driver_array`/write_driver@0.000um, `control_dff_array`/control_logic@0.000um
- empty target 5: area=17.7600um^2, rect=(0.000, 44.127) to (12.000, 45.608), nearest=`row_decode_14`/row_decoder@0.000um, `wordline_driver_13`/wordline_driver@0.085um, `row_decode_13`/row_decoder@0.110um
- empty target 6: area=17.2949um^2, rect=(32.480, 6.737) to (36.623, 10.912), nearest=`write_driver_array`/write_driver@0.000um, `sense_amp_array`/sense_amp@0.475um, `tri_gate_array`/tri_gate@0.588um
- coarse map (`.` means empty):
```text
................11111.12222.....................
.........11111..333333333333333333333333333334..
................................................
.........11111.51111111222266666666666666666678.
.........11111.51111111222266666666666666666678.
.........11111.51111111222266666666666666666678.
.........11111.51111111222266666666666666666678.
.........11111.51111111222266666666666666666678.
...............51111111222266666666666666666678.
.........11111.51111111222266666666666666666678.
.........11111.51111111222266666666666666666678.
.........11111.51111111222266666666666666666678.
.........11111.51111111222266666666666666666678.
9.99.....11111.51111111222266666666666666666678.
9.99...........51111111222266666666666666666678.
9.99.....11111.51111111222266666666666666666678.
9.99.....11111.51111111222266666666666666666678.
AAA......11111.51111111222266666666666666666678.
```
- map legend: 1=DECODER, 2=WL_DRIVER, 3=precharge_array_bbox, 4=replica_precharge, 5=dummy_left_bbox, 6=ARRAY, 7=RBL, 8=dummy_right_bbox, 9=replica_timing_delay_bbox, A=column_select_logic_bbox, B=column_mux_array_bbox, C=timing_control_glue_bbox, D=sense_amp_array_bbox, E=control_dff_array, F=write_driver_array_bbox, G=data_latch_trigate_array_bbox, H=data_dff_array

## OpenRAM-style array mirror audit

- method: OpenRAM FreePDK45 bitcell placement mirror.x=True, mirror.y=False: alternate rows use MX while columns remain R0. When limited OpenYield storage aggregation is explicitly enabled, storage cells follow the configured row_orientation_policy while keeping peripheral arrays on the legacy path.
- clean: `True`
- missing required row mirrors: `0`
- arrays using OpenRAM row mirror rule: `bitcell_array` row_offset=0; `dummy_left_array` row_offset=0; `dummy_right_array` row_offset=0; `replica_bitline_array` row_offset=0

## OpenRAM-style array layer audit

- method: Array occupancy audit: generic repeated cells must not overlap, while native OpenRAM storage cells may use designed boundary stitching at abstract bitcell pitch; external KLayout DRC remains the final legality check.
- clean: `True`
- illegal same-layer overlaps from pitch: `0`
- layer 6 / `vtg` summary: `bitcell_array`: x overlap (-0.18um), y overlap (-0.2um); `dummy_left_array`: x single_column (Noneum), y overlap (-0.2um); `dummy_right_array`: x single_column (Noneum), y overlap (-0.2um); `replica_bitline_array`: x single_column (Noneum), y overlap (-0.2um); `control_dff_array`: x spaced (0.2um), y spaced (0.2um); `sense_amp_array`: x spaced (2.245um), y single_row (Noneum); `write_driver_array`: x spaced (2.11um), y single_row (Noneum); `tri_gate_array`: x spaced (2.26um), y single_row (Noneum)

## Architecture module map

- `ARRAY`: (11.905, 20.048) to (34.655, 42.088), area=501.4100um^2
- `DECODER`: (6.657, 20.068) to (17.605, 45.608), area=279.5992um^2
- `RBL`: (34.465, 20.048) to (35.360, 42.088), area=19.7258um^2
- `SA_SWITCH_LATCH_MUX`: (12.000, 3.288) to (32.480, 17.398), area=288.9728um^2
- `TIMING_CONTROL`: (0.263, 0.243) to (6.262, 26.937), area=160.1700um^2
- `WL_DRIVER`: (7.895, 20.043) to (20.850, 45.608), area=331.1946um^2
- `column_mux_array_bbox`: (11.887, 17.873) to (34.560, 19.753), area=42.6243um^2
- `column_select_logic_bbox`: (0.263, 18.002) to (2.538, 21.252), area=7.3937um^2
- `control_dff_array`: (0.343, 0.243) to (6.262, 14.393), area=83.7680um^2
- `data_dff_array`: (12.000, 0.343) to (36.280, 2.812), area=59.9716um^2
- `data_latch_trigate_array_bbox`: (12.000, 3.288) to (32.480, 6.150), area=58.6240um^2
- `dummy_left_bbox`: (11.200, 20.048) to (12.095, 42.088), area=19.7258um^2
- `dummy_right_bbox`: (35.170, 20.048) to (36.065, 42.088), area=19.7258um^2
- `precharge_array_bbox`: (11.922, 42.463) to (34.562, 43.883), area=32.1488um^2
- `replica_timing_delay_bbox`: (0.263, 21.477) to (3.130, 26.937), area=15.6565um^2
- `sense_amp_array_bbox`: (11.965, 11.387) to (32.480, 17.398), area=123.2952um^2
- `timing_control_glue_bbox`: (0.263, 14.617) to (2.323, 17.777), area=6.5096um^2
- `write_driver_array_bbox`: (11.900, 6.737) to (32.480, 10.912), area=85.9215um^2

## Route metrics

- drawn routes: m1=407.4000um, m2=50.4050um, m3=67.0735um, m4=274.1000um, poly=2.8800um, via1=2.0800um, via2=2.0800um
- route guides: m1=38.6732um, m2=1960.7810um, m3=850.4987um, m4=470.8925um, via1=2.2100um, via2=8.0600um
- routes plus guides: m1=446.0732um, m2=2011.1860um, m3=917.5722um, m4=744.9925um, poly=2.8800um, via1=4.2900um, via2=10.1400um

## Routing track selection

- col_select algorithm: `DRC-aware candidate route-guide promotion scoring`
- evaluated candidates: `24`
- selected y0: `19.3525`
- score remaining candidate guides: `70`

## Route-guide promotion

- initial route guides: `1138`
- promoted to clean routes: `147`
- remaining route guides: `991`
- promoted by layer: m1=132, m2=7, m3=8
- remaining by layer: m1=66, m2=510, m3=244, m4=13, via1=34, via2=124
- blocked by reason: missing drawn upper/lower route stack=153, same-layer spacing conflict=838

## GDS hierarchy

- `cell_1rw` SREF count: 512
- `dff` SREF count: 18
- `dummy_cell_1rw` SREF count: 32
- `gen_col_mux` SREF count: 32
- `gen_delay_inv` SREF count: 6
- `gen_inv` SREF count: 2
- `gen_nand2` SREF count: 22
- `gen_precharge` SREF count: 33
- `gen_wl_driver` SREF count: 16
- `replica_cell_1rw` SREF count: 16
- `sense_amp` SREF count: 8
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
- `tri_gate` SREF count: 8
- `write_driver` SREF count: 8
- generated stdcells are emitted as GDS child structures: `gen_col_mux`, `gen_delay_inv`, `gen_inv`, `gen_nand2`, `gen_precharge`, `gen_wl_driver`

## Layer audit

- matches bundled FreePDK45 layers: `True`
- unknown_clean_boundary_lpps: `none`
- unknown_clean_text_lpps: `none`
- unknown_route_guide_boundary_lpps: `none`
- unknown_route_guide_text_lpps: `none`
- clean boundary LPPs: 1/0=358, 10/0=284, 11/0=714, 12/0=195, 13/0=496, 13/2=11, 14/0=32, 15/0=83, 15/2=14, 17/0=7, 17/2=2, 2/0=57, 239/0=38, 3/0=45, 4/0=67, 5/0=58, 6/0=64, 9/0=345
- clean text LPPs: 1/0=2, 11/0=67, 13/0=31, 13/1=11, 15/1=14, 17/1=2, 9/0=9

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
- `column_select`: 4/4 touched (100.0%)
- `control_glue`: 4/4 touched (100.0%)
- `delay_chain`: 6/6 touched (100.0%)
- `precharge`: 32/32 touched (100.0%)
- `replica_precharge`: 1/1 touched (100.0%)
- `row_decoder`: 16/16 touched (100.0%)
- `wordline_driver`: 16/16 touched (100.0%)

## Drawn route connectivity audit

- method: bbox intersection between generated instances and drawn top-level route shapes
- all generated roles touched by drawn routes: `True`
- roles with no drawn-route touch: `none`
- roles with partial drawn-route touch: `none`
- `column_mux`: 32/32 touched (100.0%)
- `column_select`: 4/4 touched (100.0%)
- `control_glue`: 4/4 touched (100.0%)
- `delay_chain`: 6/6 touched (100.0%)
- `precharge`: 32/32 touched (100.0%)
- `replica_precharge`: 1/1 touched (100.0%)
- `row_decoder`: 16/16 touched (100.0%)
- `wordline_driver`: 16/16 touched (100.0%)

## Generated pin routing audit

- drawn-route signal pin coverage: `100.0%`
- all generated signal pins covered by drawn routes: `True`
- missing generated signal pins: `0`

## GDS labels

- total text labels: 136
- `addr[0]`: 1
- `addr[1]`: 1
- `addr[2]`: 1
- `addr[3]`: 1
- `addr[4]`: 1
- `addr[5]`: 1
- `clk`: 2
- `csb`: 1
- `din[0]`: 1
- `din[1]`: 1
- `din[2]`: 1
- `din[3]`: 1
- `din[4]`: 1
- `din[5]`: 1
- `din[6]`: 1
- `din[7]`: 1
- `dout[0]`: 1
- `dout[1]`: 1
- `dout[2]`: 1
- `dout[3]`: 1
- `dout[4]`: 1
- `dout[5]`: 1
- `dout[6]`: 1
- `dout[7]`: 1
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
- criterion architecture_floorplan_clean: `False`
- criterion geometry_clean: `True`
- criterion cell_array_mirroring_clean: `True`
- criterion cell_array_layers_clean: `True`
- criterion structural_consistency_clean: `True`
- criterion used_cells_are_openram_or_bundled_freepdk45_gds: `True`
- criterion external_drc_clean: `False`
- criterion external_lvs_clean: `False`
- criterion external_pex_available: `False`
- blocker: top-level route guides show intended connectivity but must be replaced by DRC-clean detailed routing
- blocker: external signoff DRC/LVS/PEX has not been run; install KLayout/Magic/netgen or project signoff tools
- blocker: SPICE netlist is structural; complete LVS equivalence must be proven with extracted netlist
