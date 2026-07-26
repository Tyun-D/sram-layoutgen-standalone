# sram_8x64_wpr4_fd45 Report

- Backend: `standalone`
- Spec: 8 x 64, words/row=4
- Legal words/row choices: `1, 2, 4`
- Size: 42.7725 um x 47.3450 um
- Macro area: 2025.0640 um^2
- Useful array area: 492.7104 um^2
- Utilization: 24.33%
- Built-in DRC-lite: violations (48)
- Full signoff-candidate GDS: `/data1/qujh/work/sram_layoutgen_step45_clean/outputs/M10_raw_openyield_trace/current_supported_config/_raw_generation/sram_8x64_wpr4_fd45.gds`
- Presentation GDS: `/data1/qujh/work/sram_layoutgen_step45_clean/outputs/M10_raw_openyield_trace/current_supported_config/_raw_generation/sram_8x64_wpr4_fd45.presentation.gds`
- Complete visual-routing GDS: `/data1/qujh/work/sram_layoutgen_step45_clean/outputs/M10_raw_openyield_trace/current_supported_config/_raw_generation/sram_8x64_wpr4_fd45.complete.gds`
- Debug GDS: `/data1/qujh/work/sram_layoutgen_step45_clean/outputs/M10_raw_openyield_trace/current_supported_config/_raw_generation/sram_8x64_wpr4_fd45.debug.gds`
- Integration DRC GDS: `/data1/qujh/work/sram_layoutgen_step45_clean/outputs/M10_raw_openyield_trace/current_supported_config/_raw_generation/sram_8x64_wpr4_fd45.integration.gds`
- Architecture-view GDS: `/data1/qujh/work/sram_layoutgen_step45_clean/outputs/M10_raw_openyield_trace/current_supported_config/_raw_generation/sram_8x64_wpr4_fd45.architecture.gds`
- Architecture SVG: `/data1/qujh/work/sram_layoutgen_step45_clean/outputs/M10_raw_openyield_trace/current_supported_config/_raw_generation/sram_8x64_wpr4_fd45.architecture.svg`
- Occupancy SVG: `/data1/qujh/work/sram_layoutgen_step45_clean/outputs/M10_raw_openyield_trace/current_supported_config/_raw_generation/sram_8x64_wpr4_fd45.occupancy.svg`
- Route-guide debug GDS: `/data1/qujh/work/sram_layoutgen_step45_clean/outputs/M10_raw_openyield_trace/current_supported_config/_raw_generation/sram_8x64_wpr4_fd45.route_guides.gds`

## Hardcell usage

- array `cell_1rw`: 512
- array `dummy_cell_1rw`: 32
- array `replica_cell_1rw`: 16
- array `sense_amp`: 8
- array `tri_gate`: 8
- array `write_driver`: 8
- instance `dff`: 18
- instance `gen_col_mux_vdd_labeled`: 32
- instance `gen_delay_inv`: 6
- instance `gen_inv`: 2
- instance `gen_nand2`: 22
- instance `gen_precharge`: 33
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
- limited placement plan count: `8`

## OpenYield write driver adapter

- enabled: `True`
- local macro: `write_driver`
- contract path: `/data1/qujh/work/sram_layoutgen_step45_clean/docs/openyield_module_contracts.json`
- power status: `vdd_gnd_metadata_present`
- safe_for_physical_mapping: `True`
- safe_for_shared_rail: `False`
- requires_netlist_rewrite: `False`
- placement count: `8`
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
- `gen_col_mux_vdd_labeled`: 32 instances, slot=0.7050um x 1.8000um, state=`physical`
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
- top-level route guides: `986`

## Banked architecture

- bank_style: `contiguous-openram-origin-array`
- compaction strategy: `occupancy-guided compact perimeter margin`
- boundary margin: `0.3425`um (legacy `1.2`um)
- estimated legacy size: `44.4875um x 49.0600um`, area savings `157.4927um^2` (7.22%)
- data DFF packing strategy: `global macro area search`
- selected data DFF grid: `8` columns x `1` rows, estimated macro area `2025.0640um^2`
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
- placed cell bbox overlaps: `38`
- generated/hardcell overlaps: `0`
- generated/hardcell spacing violations (<0.0um): `0`
- placed cell overlap `row_decode_0` / `row_decode_1` (`row_decoder` / `row_decoder`)
- placed cell overlap `wordline_driver_0` / `wordline_driver_1` (`wordline_driver` / `wordline_driver`)
- placed cell overlap `row_decode_1` / `row_decode_2` (`row_decoder` / `row_decoder`)
- placed cell overlap `wordline_driver_1` / `wordline_driver_2` (`wordline_driver` / `wordline_driver`)
- placed cell overlap `row_decode_2` / `row_decode_3` (`row_decoder` / `row_decoder`)

## Global occupancy map

- method: Exact rectangle decomposition over top-level physical placement objects with module overlays used as semantic labels for a coarse floorplan map.
- occupied area: `1461.1708um^2`
- empty area: `563.8932um^2`
- occupancy ratio: `72.15%`
- largest empty region: `109.9153um^2`
- occupancy SVG: `/data1/qujh/work/sram_layoutgen_step45_clean/outputs/M10_raw_openyield_trace/current_supported_config/_raw_generation/sram_8x64_wpr4_fd45.occupancy.svg`
- largest filled roles: `bitcell_array`=717.1456um^2, `sense_amp`=155.2683um^2, `write_driver`=108.1325um^2, `control_logic`=76.3620um^2, `tri_gate`=73.8525um^2, `wordline_driver`=68.6267um^2, `data_dff`=61.0896um^2, `column_mux`=49.1808um^2, `dummy_bitcell`=44.8216um^2, `precharge`=35.6704um^2
- empty target 1: area=109.9153um^2, rect=(0.000, 26.045) to (6.657, 42.555), nearest=`row_decode_10`/row_decoder@0.000um, `row_decode_11`/row_decoder@0.000um, `row_decode_12`/row_decoder@0.000um
- empty target 2: area=28.7428um^2, rect=(37.990, 11.387) to (42.773, 17.398), nearest=`sense_amp_array`/sense_amp@0.000um, `write_driver_array`/write_driver@0.475um, `column_mux_29`/column_mux@0.475um
- empty target 3: area=28.0840um^2, rect=(0.000, 42.580) to (11.200, 45.087), nearest=`dummy_left_array`/dummy_bitcell@0.000um, `wordline_driver_15`/wordline_driver@0.000um, `row_decode_15`/row_decoder@0.025um
- empty target 4: area=27.8904um^2, rect=(2.123, 14.617) to (12.155, 17.398), nearest=`control_glue_1`/control_glue@0.000um, `control_glue_3`/control_glue@0.000um, `sense_amp_array`/sense_amp@0.000um
- empty target 5: area=24.5942um^2, rect=(0.000, 45.087) to (42.773, 45.663), nearest=`bitcell_array`/bitcell_array@0.000um, `precharge_0`/precharge@0.000um, `precharge_1`/precharge@0.000um
- empty target 6: area=21.5671um^2, rect=(6.062, 6.150) to (42.773, 6.737), nearest=`control_dff_5`/control_logic@0.000um, `tri_gate_array`/tri_gate@0.000um, `write_driver_array`/write_driver@0.000um
- coarse map (`.` means empty):
```text
....................111111111111111111111111112.
................................................
.............34444444444444444444444444444444456
.......77888.34444444444444444444444444444444456
.......77888.34444444444444444444444444444444456
.......77888.34444444444444444444444444444444456
.......77888.34444444444444444444444444444444456
.......77888.34444444444444444444444444444444456
.......77888.34444444444444444444444444444444456
.......77888.34444444444444444444444444444444456
.......77888.34444444444444444444444444444444456
.......77888.34444444444444444444444444444444456
.......77888.34444444444444444444444444444444456
.......77888.34444444444444444444444444444444456
999....77888.34444444444444444444444444444444456
999....77888.34444444444444444444444444444444456
999....77888.34444444444444444444444444444444456
999....77888.34444444444444444444444444444444456
```
- map legend: 1=precharge_array_bbox, 2=replica_precharge, 3=dummy_left_bbox, 4=ARRAY, 5=RBL, 6=dummy_right_bbox, 7=DECODER, 8=WL_DRIVER, 9=replica_timing_delay_bbox, A=column_select_logic_bbox, B=column_mux_array_bbox, C=timing_control_glue_bbox, D=sense_amp_array_bbox, E=control_dff_array, F=write_driver_array_bbox, G=data_latch_trigate_array_bbox, H=data_dff_array

## OpenRAM-style array mirror audit

- method: OpenRAM FreePDK45 bitcell placement mirror.x=True, mirror.y=False: alternate rows use MX while columns remain R0. When limited OpenYield storage aggregation is explicitly enabled, storage cells follow the configured row_orientation_policy while keeping peripheral arrays on the legacy path.
- clean: `True`
- missing required row mirrors: `0`
- arrays using OpenRAM row mirror rule: `bitcell_array` row_offset=0; `dummy_left_array` row_offset=0; `dummy_right_array` row_offset=0; `replica_bitline_array` row_offset=0

## OpenRAM-style array layer audit

- method: Array occupancy audit: generic repeated cells must not overlap, while native OpenRAM storage cells may use designed boundary stitching at abstract bitcell pitch; external KLayout DRC remains the final legality check.
- clean: `True`
- illegal same-layer overlaps from pitch: `0`
- layer 6 / `vtg` summary: `bitcell_array`: x spaced (0.01um), y abut (0.0um); `dummy_left_array`: x single_column (Noneum), y abut (-0.0um); `dummy_right_array`: x single_column (Noneum), y abut (-0.0um); `replica_bitline_array`: x single_column (Noneum), y abut (-0.0um); `sense_amp_array`: x spaced (3.005um), y single_row (Noneum); `write_driver_array`: x spaced (2.87um), y single_row (Noneum); `tri_gate_array`: x spaced (3.02um), y single_row (Noneum)

## Architecture module map

- `ARRAY`: (12.095, 20.048) to (40.735, 45.088), area=717.1456um^2
- `DECODER`: (6.657, 20.068) to (7.695, 42.555), area=23.3308um^2
- `RBL`: (40.735, 20.048) to (41.630, 45.087), area=22.4108um^2
- `SA_SWITCH_LATCH_MUX`: (12.190, 3.288) to (37.990, 17.398), area=364.0380um^2
- `TIMING_CONTROL`: (0.263, 0.243) to (6.062, 26.045), area=149.6545um^2
- `WL_DRIVER`: (7.695, 20.043) to (10.740, 42.580), area=68.6267um^2
- `column_mux_array_bbox`: (12.077, 17.873) to (40.640, 19.753), area=53.6975um^2
- `column_select_logic_bbox`: (0.263, 17.765) to (2.338, 20.687), area=6.0642um^2
- `control_dff_array`: (0.343, 0.243) to (6.062, 14.393), area=80.9380um^2
- `data_dff_array`: (12.190, 0.243) to (35.070, 2.912), area=61.0896um^2
- `data_latch_trigate_array_bbox`: (12.190, 3.288) to (37.990, 6.150), area=73.8525um^2
- `dummy_left_bbox`: (11.200, 20.048) to (12.095, 45.087), area=22.4108um^2
- `dummy_right_bbox`: (41.630, 20.048) to (42.525, 45.087), area=22.4108um^2
- `precharge_array_bbox`: (12.112, 45.663) to (40.642, 47.083), area=40.5126um^2
- `replica_timing_delay_bbox`: (0.263, 20.912) to (2.730, 26.045), area=12.6644um^2
- `sense_amp_array_bbox`: (12.155, 11.387) to (37.990, 17.398), area=155.2684um^2
- `timing_control_glue_bbox`: (0.263, 14.618) to (2.123, 17.540), area=5.4358um^2
- `write_driver_array_bbox`: (12.090, 6.737) to (37.990, 10.912), area=108.1325um^2

## Route metrics

- drawn routes: m1=513.6400um, m2=41.4375um, m3=55.5095um, m4=282.4700um, poly=2.8800um, via1=2.0800um, via2=2.0800um
- route guides: m1=32.2732um, m2=2139.8295um, m3=967.9162um, m4=550.8425um, via1=2.2100um, via2=8.0600um
- routes plus guides: m1=545.9132um, m2=2181.2670um, m3=1023.4257um, m4=833.3125um, poly=2.8800um, via1=4.2900um, via2=10.1400um

## Routing track selection

- col_select algorithm: `DRC-aware candidate route-guide promotion scoring`
- evaluated candidates: `24`
- selected y0: `19.3525`
- score remaining candidate guides: `70`

## Route-guide promotion

- initial route guides: `1138`
- promoted to clean routes: `152`
- remaining route guides: `986`
- promoted by layer: m1=132, m2=9, m3=11
- remaining by layer: m1=66, m2=508, m3=241, m4=13, via1=34, via2=124
- blocked by reason: missing drawn upper/lower route stack=152, same-layer spacing conflict=834

## GDS hierarchy

- `cell_1rw` SREF count: 512
- `dff` SREF count: 18
- `dummy_cell_1rw` SREF count: 32
- `gen_delay_inv` SREF count: 6
- `gen_inv` SREF count: 2
- `gen_nand2` SREF count: 22
- `gen_precharge` SREF count: 33
- `gen_wl_driver` SREF count: 16
- `replica_cell_1rw` SREF count: 16
- `sense_amp` SREF count: 8
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
- `tri_gate` SREF count: 8
- `write_driver` SREF count: 8
- generated stdcells are emitted as GDS child structures: `gen_delay_inv`, `gen_inv`, `gen_nand2`, `gen_precharge`, `gen_wl_driver`

## Layer audit

- matches bundled FreePDK45 layers: `True`
- unknown_clean_boundary_lpps: `none`
- unknown_clean_text_lpps: `none`
- unknown_route_guide_boundary_lpps: `none`
- unknown_route_guide_text_lpps: `none`
- clean boundary LPPs: 1/0=356, 10/0=283, 11/0=736, 12/0=195, 13/0=483, 13/2=11, 14/0=32, 15/0=88, 15/2=14, 17/0=7, 17/2=2, 2/0=54, 239/0=35, 3/0=45, 4/0=66, 5/0=57, 6/0=63, 9/0=341
- clean text LPPs: 1/0=2, 11/0=64, 13/0=27, 13/1=11, 15/1=14, 17/1=2, 9/0=7

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

- total text labels: 127
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
- criterion cell_array_layers_clean: `True`
- criterion structural_consistency_clean: `False`
- criterion used_cells_are_openram_or_bundled_freepdk45_gds: `False`
- criterion external_drc_clean: `False`
- criterion external_lvs_clean: `False`
- criterion external_pex_available: `False`
- blocker: geometry audit found placement outside prBoundary or module overhang
- blocker: structural audit found loose abutment, unused column mux/precharge, or bitline misalignment
- blocker: some used cells are missing GDS or come from synthetic non-OpenRAM generated-cell geometry
- blocker: top-level route guides show intended connectivity but must be replaced by DRC-clean detailed routing
- blocker: external signoff DRC/LVS/PEX has not been run; install KLayout/Magic/netgen or project signoff tools
- blocker: SPICE netlist is structural; complete LVS equivalence must be proven with extracted netlist
