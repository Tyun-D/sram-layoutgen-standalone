# OpenYield Control Path Intent

- physical_role: `CONTROL_PATH`
- modules: CONTROL_LOGIC, DELAY_CHAIN, PRECHARGE_ENABLE_PATH, SENSE_ENABLE_PATH, WRITE_ENABLE_PATH, WORDLINE_ENABLE_PATH, GATED_CLOCK_PATH, DFF_ROW

## Control Outputs

- precharge_en
- sense_en
- write_en
- wordline_en
- gated_clk
- delay / replica timing signals

## Candidate Geometry Modules

- DELAY_CHAIN
- PRECHARGE_ENABLE_PATH
- SENSE_ENABLE_PATH
- WRITE_ENABLE_PATH
- WORDLINE_ENABLE_PATH
- GATED_CLOCK_PATH
- DFF_ROW
- CONTROL_LOGIC

## Contract Pin Modules

- DELAY_CHAIN
- PRECHARGE_ENABLE_PATH
- SENSE_ENABLE_PATH
- WRITE_ENABLE_PATH
- WORDLINE_ENABLE_PATH
- GATED_CLOCK_PATH
- DFF_ROW
- CONTROL_LOGIC

## R4 Router Requirements

- control router must connect control outputs into row/column/periphery modules through stable bus ownership
- control router must preserve clock/control separation from power stitching
- control router must preserve replica timing signals as dedicated semantic routes rather than collapsing them into generic nets
