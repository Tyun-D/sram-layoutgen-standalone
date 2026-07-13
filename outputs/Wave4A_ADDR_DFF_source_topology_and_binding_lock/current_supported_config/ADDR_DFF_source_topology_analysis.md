# ADDR_DFF Source Topology Analysis

- logical_module: `ADDR_DFF`
- top_pin_order:
```json
[
  "VDD",
  "VSS",
  "CLK",
  "A0",
  "A1",
  "A2",
  "A3",
  "A_dff0",
  "A_dff1",
  "A_dff2",
  "A_dff3"
]
```
- child_instance_count: `4`
- instances:
```json
[
  {
    "instance_name": "dff_0",
    "logical_child_module": "DFF",
    "connections": [
      "VDD",
      "VSS",
      "A0",
      "A_dff0",
      "CLK"
    ]
  },
  {
    "instance_name": "dff_1",
    "logical_child_module": "DFF",
    "connections": [
      "VDD",
      "VSS",
      "A1",
      "A_dff1",
      "CLK"
    ]
  },
  {
    "instance_name": "dff_2",
    "logical_child_module": "DFF",
    "connections": [
      "VDD",
      "VSS",
      "A2",
      "A_dff2",
      "CLK"
    ]
  },
  {
    "instance_name": "dff_3",
    "logical_child_module": "DFF",
    "connections": [
      "VDD",
      "VSS",
      "A3",
      "A_dff3",
      "CLK"
    ]
  }
]
```
- canonical_net_count: `11`
- canonical_topology_sha256: `870eb1c9374020163e73962b2209062849102469465bc4aa1b3e22edbfb2c980`
