# Gate Row Packing Report

- old_gds: `/data1/qujh/work/sram_layoutgen_step45_clean/outputs/layout_prototype/hybrid_openyield/hybrid_openyield_prototype.gds`
- new_gds: `/data1/qujh/work/sram_layoutgen_step45_clean/outputs/layout_prototype/hybrid_openyield_compacted/hybrid_openyield_compacted.gds`
- gds size before bytes: `223500`
- gds size after bytes: `224268`
- packed gate rows count: `16`
- average intra-row gap before um: `not_reconstructed`
- average intra-row gap after um: `0.0`
- rail alignment pass/fail: `True`
- VDD continuity candidate: `True`
- GND continuity candidate: `True`
- fallback cells: `[]`
- blocked cells: `[]`

## Notes

- old average intra-row gap is not reconstructed numerically from the previous GDS; the legacy screenshot and prior prototype visually show sparse gate placement.
- new gate rows are packed with x_next = x_current + cell_width and row pitch derived from legal cell height.
- routing still legacy
- gate placement compacted
- routing compaction not yet performed

## Rows

- decoder_gate_rows_row0: mirror=`R0` origin=(`6.7375`, `20.147500000000004`) width=`3.8675000000000006` cells=`[]`
- decoder_gate_rows_row1: mirror=`MX` origin=(`6.7375`, `21.872500000000006`) width=`3.8675000000000006` cells=`[]`
- decoder_gate_rows_row2: mirror=`R0` origin=(`6.7375`, `23.597500000000004`) width=`3.8675000000000006` cells=`[]`
- decoder_gate_rows_row3: mirror=`MX` origin=(`6.7375`, `25.322500000000005`) width=`3.8675000000000006` cells=`[]`
- decoder_gate_rows_row4: mirror=`R0` origin=(`6.7375`, `27.047500000000007`) width=`3.8675000000000006` cells=`[]`
- decoder_gate_rows_row5: mirror=`MX` origin=(`6.7375`, `28.772500000000004`) width=`3.8675000000000006` cells=`[]`
- decoder_gate_rows_row6: mirror=`R0` origin=(`6.7375`, `30.497500000000006`) width=`3.8675000000000006` cells=`[]`
- decoder_gate_rows_row7: mirror=`MX` origin=(`6.7375`, `32.222500000000004`) width=`3.8675000000000006` cells=`[]`
- decoder_gate_rows_row8: mirror=`R0` origin=(`6.7375`, `33.947500000000005`) width=`3.8675000000000006` cells=`[]`
- decoder_gate_rows_row9: mirror=`MX` origin=(`6.7375`, `35.67250000000001`) width=`3.8675000000000006` cells=`[]`
- decoder_gate_rows_row10: mirror=`R0` origin=(`6.7375`, `37.39750000000001`) width=`3.8675000000000006` cells=`[]`
- decoder_gate_rows_row11: mirror=`MX` origin=(`6.7375`, `39.1225`) width=`3.8675000000000006` cells=`[]`
- decoder_gate_rows_row12: mirror=`R0` origin=(`6.7375`, `40.84750000000001`) width=`3.8675000000000006` cells=`[]`
- decoder_gate_rows_row13: mirror=`MX` origin=(`6.7375`, `42.572500000000005`) width=`3.8675000000000006` cells=`[]`
- decoder_gate_rows_row14: mirror=`R0` origin=(`6.7375`, `44.29750000000001`) width=`3.8675000000000006` cells=`[]`
- decoder_gate_rows_row15: mirror=`MX` origin=(`6.7375`, `46.02250000000001`) width=`3.8675000000000006` cells=`[]`
