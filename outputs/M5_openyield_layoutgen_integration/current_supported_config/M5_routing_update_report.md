# M5 Routing Update Report

- routing_code_modified: `True`
- openyield_net_count: `34`
- implemented_net_count: `34`
- route_polygon_count: `724`
- route_label_count: `27`

| openyield_net | openyield_pin | local_pin | physical_role |
| --- | --- | --- | --- |
| DEC_WL[i] | A | decoder_input | row_path |
| WL_EN | B | wordline_enable | row_path |
| WL[i] | Z | wl | array_interface |
| VDD | VDD | vdd | power |
| VSS | VSS | gnd | power |
| DIN_dff[i] | DIN | din | column_path |
| w_en | EN | write_enable | column_path |
| BL[i] | BL | bl | bitline |
| BLB[i] | BLB | br | bitline |
| VDD | VDD | vdd | power |
| VSS | VSS | gnd | power |
| SA_IN[*] | IN | bl | column_path |
| SA_INB[*] | INB | br | column_path |
| s_en | EN | en | control |
| SA_Q[*] | Q | dout | read_data |
| VDD | VDD | vdd | power |
| VSS | VSS | gnd | power |
