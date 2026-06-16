# OpenYield ColumnMux Adapter Report

This Step 5.4 report is read-only. It audits column mux signal semantics and power metadata without modifying standalone placement, routing, or GDS writer.

## Summary

- OpenYield pin list: `VDD, VSS, SA_IN, SA_INB, SEL{i}, BL{i}, BLB{i}`
- local gen_col_mux GDS labels: `['sel', 'bl', 'br', 'bl_out', 'br_out', 'gnd', 'G', 'S', 'D']`
- local SPICE pins: `[]`
- OUT -> mux_out established: `True`
- OUTB -> mux_out_b established: `True`
- VDD metadata present: `False`
- GND metadata present: `True`
- power_status: `missing_power_metadata`
- safe_for_physical_mapping: `True`
- safe_for_shared_rail: `False`
- requires_power_metadata_fix: `True`
- can enter column mux placement: `limited_or_metadata_only`

## Pin Mapping

| OpenYield pin | Local pin | Canonical | Type | Required | Notes |
| --- | --- | --- | --- | --- | --- |
| VDD | - | vdd | missing_power_metadata | False | OpenYield requires VDD.; Local gen_col_mux does not prove a VDD label-backed physical pin. |
| VSS | gnd | gnd | direct_physical_pin | True | - |
| BL | BL | bl | direct_physical_pin | True | - |
| BLB | BR | br | direct_physical_pin | True | - |
| SEL | SEL | column_select | direct_physical_pin | True | - |
| OUT | OUT | mux_out | direct_physical_pin | True | - |
| OUTB | OUTB | mux_out_b | direct_physical_pin | True | - |

## SenseAmp Pairing

- sense_amp mux interface: `{'IN': 'mux_out[group]', 'INB': 'mux_out_b[group]', 'Q': 'dout[group]', 'QB': 'dropped_complementary_output'}`
- column mux can pair with sense_amp adapter: `True`

## Notes

- OUT/OUTB semantics are evaluated independently from power metadata.
- Do not allow shared rail or claim power-complete placement until VDD metadata is proven.
