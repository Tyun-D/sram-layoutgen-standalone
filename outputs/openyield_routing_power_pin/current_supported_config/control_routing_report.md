# Control Routing Report

- route_count: `7`
- blocked_route_count: `0`

## Entries

| net_name | source_module | source_pin | target_module | target_pin | routing_status | uses_contract_pin | route_geometry_bbox | next_required_action |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| precharge_en | CONTROL_LOGIC_inst | precharge_en | precharge_inst | precharge_en | CONTRACT_PIN_BASED_ROUTE | True | {'x0': 12.3925, 'y0': 10.0075, 'x1': 24.6325, 'y1': 16.645, 'width': 12.24, 'height': 6.6375} | Tighten control fanout and exact landing vias during R5 detailed connectivity review. |
| sense_en | CONTROL_LOGIC_inst | sense_en | sense_amp_inst | en | CONTRACT_PIN_BASED_ROUTE | True | {'x0': 14.1775, 'y0': 10.0075, 'x1': 24.6325, 'y1': 18.94, 'width': 10.455, 'height': 8.9325} | Tighten control fanout and exact landing vias during R5 detailed connectivity review. |
| write_en | CONTROL_LOGIC_inst | write_en | write_driver_inst | en | CONTRACT_PIN_BASED_ROUTE | True | {'x0': 15.105, 'y0': 10.0075, 'x1': 24.6325, 'y1': 18.0225, 'width': 9.5275, 'height': 8.015} | Tighten control fanout and exact landing vias during R5 detailed connectivity review. |
| wordline_en | CONTROL_LOGIC_inst | wl_en | wordline_driver_inst | B | CONTRACT_PIN_BASED_ROUTE | True | {'x0': 2.3125, 'y0': 10.0075, 'x1': 24.6325, 'y1': 18.2525, 'width': 22.32, 'height': 8.245} | Tighten control fanout and exact landing vias during R5 detailed connectivity review. |
| clk | CONTROL_LOGIC_inst | clk | DFF_ROW_inst | clk | CONTRACT_PIN_BASED_ROUTE | True | {'x0': 24.6325, 'y0': 10.0075, 'x1': 31.1825, 'y1': 30.415, 'width': 6.55, 'height': 20.4075} | Tighten control fanout and exact landing vias during R5 detailed connectivity review. |
| gated_clk | GATED_CLOCK_PATH_inst | gated_clk | DFF_ROW_inst | clk | CONTRACT_PIN_BASED_ROUTE | True | {'x0': 22.92125, 'y0': 30.34, 'x1': 31.1825, 'y1': 30.415, 'width': 8.26125, 'height': 0.075} | Tighten control fanout and exact landing vias during R5 detailed connectivity review. |
| rbl_delay | DELAY_CHAIN_inst | delay_out | replica_array_inst | RBL | CONTRACT_PIN_BASED_ROUTE | True | {'x0': 12.895, 'y0': 9.1825, 'x1': 30.53, 'y1': 26.95875, 'width': 17.635, 'height': 17.77625} | Tighten control fanout and exact landing vias during R5 detailed connectivity review. |

