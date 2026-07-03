| pin_name | pin_category | planned_top_edge | planned_layer | source_internal_net | source_internal_access | pin_status | usable_for_C4_or_C5 | remaining_gap |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| address | ADDRESS | left | M4 | A[*] | DFF_ROW:D[0] | GEOMETRY_BACKED_PIN | True |  |
| din | DATA_IN | left | M4 | DIN[*] | write_driver:din | GEOMETRY_BACKED_PIN | True |  |
| dout | DATA_OUT | right | M4 | DOUT[*] | sense_amp:dout | GEOMETRY_BACKED_PIN | True |  |
| clk | CLOCK | top | M4 | clk | CONTROL_LOGIC:clk | GEOMETRY_BACKED_PIN | True |  |
| control | CONTROL | top | M4 | control[*] | CONTROL_LOGIC:precharge_en | SYNTHESIZED_PIN_FOR_CURRENT_GENERATOR | True |  |
| VDD | POWER | top | M5 | VDD | bitcell_array:VDD | GEOMETRY_BACKED_PIN | True |  |
| GND | GROUND | bottom | M5 | GND | bitcell_array:GND | GEOMETRY_BACKED_PIN | True |  |
