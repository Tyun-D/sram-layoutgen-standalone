# Bitcell Array Physical Authority Lock

`layoutgen_reuse_v2_regenerated_16x16` is locked as an `A_CURRENT_SOURCE_EXACT` standalone array asset.

- GDS: `outputs/PROJECT_bitcell_array_layoutgen_reuse_v2/clean.gds`
- SHA256: `555df9b1fcbd9dda7e4c8959942e27b8f093c36b0a8c67a7ac213f9946b9a1ac`
- Top cell: `sram_capped_replica_bitcell_array`
- Configuration: 16 rows, 16 columns, 16 WL, 16 BL and 16 BR
- Hierarchy: 256 real bitcells, 88 dummy cells, 17 replica cells
- Tap policy: no discrete tap in the locked FreePDK45 LiteRAM storage family
- DRC: 0 markers
- Power: 722/722 endpoints, one VDD component, one VSS component, isolated supplies
- Abutment: horizontal and vertical intended gap = 0
- Determinism: byte-exact A/B regeneration
- Negative suite: 16/16 expected rejections, 0 unexpected passes

This lock approves the standalone array asset only. `FULL_BITCELL_ARRAY_GDS_INTEGRATION` remains `false` until Decoder/WL-driver integration is rebuilt and revalidated against this SHA.
