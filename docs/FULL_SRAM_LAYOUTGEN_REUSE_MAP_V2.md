# Full SRAM Layoutgen Reuse Map V2

- storage array aggregation: authoritative array reused as-is
- peripheral replication: bank builder uses 16 real unit SREFs
- Pin extraction: bank pin_map.json and interface lock
- hierarchical GDS writing: full_hierarchical_floorplan.gds uses SREF hierarchy
- power stitching: power preplan only; detailed power stitching not started
