# OpenYield ColumnMux Power Metadata Report

This Step 5.5 report is read-only. It audits `gen_col_mux` power metadata proof across GDS, SPICE, replacement metadata, local fallback netlist text, and OpenYield source.

## Summary

- replacement GDS: `E:\njust\keyan\SRAM Compiler_V2\OpenRAM-stable\deliverables\sram_layoutgen_step45_clean\technology\freepdk45\gds_lib\openram_replacements\gen_col_mux.gds`
- `gen_col_mux` has VDD label: `False`
- suspected unlabeled VDD shape present: `True`
- local SPICE subckt has VDD: `False`
- OpenYield generator expects VDD: `True`
- power_status: `vdd_shape_unlabeled`
- safe_for_physical_mapping: `True`
- safe_for_shared_rail: `False`
- can_enter_columnmux_placement: `limited_or_metadata_only`
- requires_metadata_fix: `True`
- recommended_fix: `add_gds_label_required`

## GDS Labels

- replacement GDS labels: `['sel', 'bl', 'br', 'bl_out', 'br_out', 'gnd', 'G', 'S', 'D']`

| Label | Layer | X | Y | Matched shape bbox |
| --- | --- | --- | --- | --- |
| sel | 9 | 0.3525 | 0.0525 | {'x0': 0.3275, 'y0': 0.025, 'x1': 0.3775, 'y1': 0.08} |
| bl | 13 | 0.17500000000000002 | 1.73 | {'x0': 0.14, 'y0': 1.6600000000000001, 'x1': 0.21, 'y1': 1.8} |
| br | 13 | 0.6 | 1.73 | {'x0': 0.5650000000000001, 'y0': 1.6600000000000001, 'x1': 0.635, 'y1': 1.8} |
| bl_out | 13 | 0.17500000000000002 | 0.07 | {'x0': 0.14, 'y0': 0.0, 'x1': 0.21, 'y1': 0.14} |
| br_out | 13 | 0.6 | 0.07 | {'x0': 0.5650000000000001, 'y0': 0.0, 'x1': 0.635, 'y1': 0.14} |
| gnd | 11 | 0.705 | 0.87 | {'x0': 0.6725, 'y0': 0.8375, 'x1': 0.7375, 'y1': 0.9025} |
| G | 9 | 0.1525 | 0.36 | {'x0': 0.1275, 'y0': -0.055, 'x1': 0.1775, 'y1': 0.775} |
| S | 11 | 0.045 | 0.36 | {'x0': 0.0125, 'y0': 0.2925, 'x1': 0.0775, 'y1': 0.4275} |
| D | 11 | 0.26 | 0.36 | {'x0': 0.2125, 'y0': 0.14, 'x1': 0.2775, 'y1': 0.44} |

## Suspected Power Shapes

- suspected VDD shapes in replacement GDS: `2`
- `{'layer': 11, 'datatype': 0, 'bbox': {'x0': 0.14, 'y0': 1.6275, 'x1': 0.46, 'y1': 1.6925000000000001}, 'width': 0.32, 'height': 0.06500000000000017, 'reason': 'unlabeled_m1_shape_near_top_boundary'}`
- `{'layer': 11, 'datatype': 0, 'bbox': {'x0': 0.4275, 'y0': 1.3, 'x1': 0.4925, 'y1': 1.6600000000000001}, 'width': 0.065, 'height': 0.3600000000000001, 'reason': 'unlabeled_m1_shape_near_top_boundary'}`

## SPICE And Source Audit

- local `sp_lib` status: `spice_subckt_missing`
- local `sp_lib` subckt ports: `[]`
- local fallback `netlist_writer.py` subckt ports: `['BL', 'BR', 'OUT', 'SEL', 'vdd', 'gnd']`
- fallback subckt uses VDD in device bodies: `False`
- OpenYield source file found: `True`
- OpenYield nodes include VDD/VSS: `True` / `True`
- OpenYield uses PMOS+NMOS transmission gate pair: `True`
- OpenYield internal inverter present: `True`
- OpenYield PMOS devices use VDD: `True`
- `G/S/D` labels explanation: `The replacement GDS carries local transistor terminal labels G/S/D; they are debug/device terminal labels, not exported power pins.`

## Conclusion

- VDD really exists as label-backed pin: `False`
- VDD may exist only as unlabeled local metal: `True`
- metadata alias alone is sufficient: `False`
- GDS label update is required: `True`
- shared rail is allowed now: `False`
- column mux placement can proceed now: `limited_or_metadata_only`

## Notes

- The active replacement macro is technology/freepdk45/gds_lib/openram_replacements/gen_col_mux.gds, not the separate unlabeled technology/freepdk45/gds_lib/gen_col_mux.gds.
- Signal semantics from Step 5.4 remain usable: OUT->mux_out and OUTB->mux_out_b are established.
- This report does not modify standalone placement, routing, GDS writer, or hardcell GDS.
