# Wave3 DFF_BUF Real Topology Analysis

- source_definition_file: `/data1/qujh/work/external/OpenYield/sram_compiler/subcircuits/time_generate.py`
- source_definition_function: `DFF_BUF.add_dff_buf`
- source_child_instance_count: `3`
- source_child_type_counts: `{'DFF': 1, 'PINV': 2}`
- source_pin_net_connection_count: `13`
- source_top_pin_list: `['VDD', 'VSS', 'D', 'Q', 'QB', 'CLK']`
- source_internal_net_list: `['qint']`

## Child Instantiation Order

- `dff`: `DFF` at line `288` -> `['VDD', 'VSS', 'D', 'qint', 'CLK']`
- `inv1`: `PINV` at line `292` -> `['VDD', 'VSS', 'qint', 'QB']`
- `inv2`: `PINV` at line `296` -> `['VDD', 'VSS', 'QB', 'Q']`
