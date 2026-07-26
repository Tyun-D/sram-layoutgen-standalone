# OpenYield R4 Routing Power Pin Plan

## WordlineRouter

- Route WL driver outputs to bitcell rows
- Own exactly one WL per physical row
- Keep all WL routes row-pitch aligned

## BitlineRouter

- Route bitcell BL/BR to precharge
- Route bitcell BL/BR to column mux, sense amp, and write driver as required
- Keep all BL/BR routes column-pitch aligned

## ControlRouter

- Route precharge_en to precharge
- Route sense_en to sense_amp
- Route write_en to write_driver
- Route wordline_en to the wordline path
- Route clk and gated_clk through control and DFF paths

## PowerPlanner

- Plan array VDD/GND distribution
- Plan row path VDD/GND distribution
- Plan column path VDD/GND distribution
- Plan control path VDD/GND distribution
- Export top-level VDD/GND pins

## PinLabelExporter

- Export addr pins
- Export din pins
- Export dout pins
- Export clk and control pins
- Export VDD/GND pins

## NetToShapeMapper

- Track OpenYield net name
- Track source instance/pin
- Track target instance/pin
- Track geometry shape ids or bbox handles
- Track routing status

## R5 Support

- Provide semantic-to-geometry net coverage for validation
- Provide route-backed pin export evidence for naming audits
- Provide power and routing audits without claiming signoff closure
