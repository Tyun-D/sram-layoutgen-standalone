# OpenYield DFF Array Adapter Audit

This is a metadata-only adapter audit. It does not modify standalone.py, routing, the GDS writer, or any OpenYield source.

## Summary

- OpenYield DFF pin list: `VDD, VSS, D, Q, CLK`
- local DFF GDS labels: `clk, D, Q, gnd, vdd`
- local DFF SPICE pins: `D, Q, clk, vdd, gnd`
- safe_for_physical_mapping: `True`
- safe_for_shared_rail: `False`
- row_placement_ready: `metadata_only`
- dff_adapter_safe_for_metadata_plan: `True`
- dff_array_can_enter_metadata_placement: `True`
- dff_array_can_enter_standalone_placement: `False`
- standalone modified: `False`
- routing modified: `False`
- GDS writer modified: `False`

## Local DFF Audit

- GDS path: `technology\freepdk45\gds_lib\dff.gds`
- SPICE path: `technology\freepdk45\sp_lib\dff.sp`
- GDS bbox: `{"x0": 0.0, "y0": -0.0999999999999994, "x1": 2.8599999999999826, "y1": 2.5699999999999843}`
- VDD/GND metadata complete: `True`
- local QB present: `False`
- local reset/enable/scan present: `False`

## DFF Pin Mapping

| OpenYield pin | role | local target | GDS label | SPICE pin | status | notes |
| --- | --- | --- | --- | --- | --- | --- |
| VDD | power | vdd | True | True | matched | - |
| VSS | ground | gnd | True | True | matched | - |
| D | data_input | d | True | True | matched | - |
| Q | data_output | q | True | True | matched | - |
| CLK | clock | clk | True | True | matched | OpenYield DFF uses CLK; local physical pin is clk, and array-level semantic clock domain may be driven by clk_buf. |
| QB | complementary_output | - | False | False | unused_complementary_output | OpenYield ADDR_DFF/DATA_DFF do not use QB, and the local hardcell does not expose QB. |

## ADDR_DFF Semantic Table

| array | inputs | outputs | input semantics | output semantics | feeds | consumer | status |
| --- | --- | --- | --- | --- | --- | --- | --- |
| ADDR_DFF | CLK, A[i] | A_dff[i] | CLK -> clk_buf / TIME clock domain, A[i] -> addr[i] | A_dff[i] -> addr_q[i] / addr_latched[i] | decoder_input_domain | DECODER_CASCADE.A[i] | dff_array_mappable |

## DATA_DFF Semantic Table

| array | inputs | outputs | input semantics | output semantics | feeds | consumer | status |
| --- | --- | --- | --- | --- | --- | --- | --- |
| DATA_DFF | CLK, DIN[i] | DIN_dff[i] | CLK -> clk_buf / TIME clock domain, DIN[i] -> din[i] | DIN_dff[i] -> din_q[i] / data_latched[i] | write_driver_input_domain | WRITEDRIVER.DIN[i] | dff_array_mappable |

## Notes

- OpenYield DFF pin list is VDD, VSS, D, Q, CLK.
- Local dff GDS exposes clk, D, Q, gnd, vdd and does not expose QB.
- Local dff SPICE subckt order is D Q clk vdd gnd, so the adapter must be name-based rather than order-based.
- ADDR_DFF feeds DECODER_CASCADE, while DATA_DFF feeds WRITEDRIVER.
- Shared rail remains disabled because DFF row-level rail continuity and abutment are not proven by this audit.
- The DFF leaf is safe for metadata-only planning.
