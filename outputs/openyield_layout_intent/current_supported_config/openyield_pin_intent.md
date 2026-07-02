# OpenYield Pin Intent

- top-level address pins: A[i]
- top-level data input pins: DIN[i]
- top-level data output pins: DOUT[i]
- clock/control pins: clk, csb, web
- power pins: VDD, GND, VSS

## Geometry-backed Pin Modules

- wordline_driver
- column_mux
- sense_amp
- write_driver

## Contract Pin Modules

- bitcell_array
- dummy_array
- replica_array
- row_decoder
- wordline_decoder
- decoder_gate_cells
- wordline_driver_gate_cells
- precharge
- DELAY_CHAIN
- PRECHARGE_ENABLE_PATH
- SENSE_ENABLE_PATH
- WRITE_ENABLE_PATH
- WORDLINE_ENABLE_PATH
- GATED_CLOCK_PATH
- DFF_ROW
- CONTROL_LOGIC

## Validation Plan

- R4 validates pin placement ownership and routing reachability
- R5 validates exported top-level pins against GDS/LEF/SPICE naming consistency
