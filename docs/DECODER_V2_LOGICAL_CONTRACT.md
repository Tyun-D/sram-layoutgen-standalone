# Decoder V2 Logical Contract

- source_commit: `1c34428d8b913963c4971d093b1a7c2df97a2509`
- source_file: `/data1/qujh/work/external/OpenYield/sram_compiler/subcircuits/decoder.py`
- decoder3_8 formal_port_order: `['VDD', 'VSS', 'EN', 'A0', 'A1', 'A2', 'WL0', 'WL1', 'WL2', 'WL3', 'WL4', 'WL5', 'WL6', 'WL7']`
- enable_polarity: `active_high`
- wordline_polarity: `active_high`

## Bit Mapping

- `WL0`: `(A0b & A1b & A2b) & EN`
- `WL1`: `(A0b & A1b & A2) & EN`
- `WL2`: `(A0b & A1 & A2b) & EN`
- `WL3`: `(A0b & A1 & A2) & EN`
- `WL4`: `(A0 & A1b & A2b) & EN`
- `WL5`: `(A0 & A1b & A2) & EN`
- `WL6`: `(A0 & A1 & A2b) & EN`
- `WL7`: `(A0 & A1 & A2) & EN`
