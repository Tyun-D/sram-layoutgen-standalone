# M12C4 Composite Routing Contract

- local_pin_escape_layer: `m1`
- primary_intercell_signal_layer: `m2`
- crossover_layer: `m2`
- via_stack: `m1_via1_m2`
- power_layer: `m1`
- ground_layer: `m1`
- route_width_source: `technology/freepdk45/tech/freepdk45.lydrc and freepdk45 tech contract`
- route_spacing_source: `technology/freepdk45/tech/freepdk45.lydrc and freepdk45 tech contract`
- route_grid: `FreePDK45 lambda-aligned deterministic grid`
- pin_access_policy: `escape each top-level primitive pin on m1 before any m2 crossover`
- route_determinism_policy: `sorted net order and fixed Manhattan preference`
- power_stitch_policy: `abut aligned m1 rails only after interface audit pass`
- label_sanitization_policy: `top-level canonical labels only on exported composite GDS`
- routing_contract_status: `LOCKED_COMPOSITE_ROUTING_V1`
