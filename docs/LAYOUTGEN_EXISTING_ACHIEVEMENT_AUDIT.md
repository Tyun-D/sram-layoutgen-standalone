# Layoutgen Existing Achievement Audit

## Conclusion

The evidence package exists at `/data1/qujh/PAPER_EVIDENCE_PACKAGE_20260713_043712.tar.gz` with SHA-256 `4eb62c04deb83eb64f5c07d1ba1a3700bbf47516f9c37da608fcbf806ca275c1`. It contains reusable placement and verification logic, but it does not contain a currently authoritative 16-row bitcell-array asset.

The package's standalone `bitcell_array.gds` is the same 4x4 L3 geometric prototype already rejected for final integration. The previously inventoried hierarchical OpenRAM 2x16 macro is absent from the current filesystem. Existing flat 16x16 outputs have no separately authoritative array hierarchy/pin handoff, while the generated 16x16 report is DRC-dirty and records loose abutment, bitline misalignment, synthetic cells, and missing external DRC/LVS/PEX.

## Reusable Results

| Result | Evidence | Reuse decision |
|---|---|---|
| Native storage pitch and seamless-family placement | `sram_layoutgen/standalone.py`, SHA `c53526ac...` | Mandatory generator input |
| Bitcell/dummy/replica hard macros | `technology/freepdk45/gds_lib/*.gds` | Reusable leaf inputs, not array authority |
| Same-net overlap classification and parent power stitching | `standalone.py`, `verifier.py`, `POWER_RAIL_ASSEMBLY.json` | Mandatory validation contract |
| WL pin extraction and row-aligned driver placement | `standalone.py`, `TOP_LEVEL_PLACEMENT_RULES.json` | Mandatory placement contract |
| Hierarchy, pin-access and foreign-net checks | `verifier.py` | Reusable checks; final-GDS witnesses remain required |

The historical hardcell baseline reports zero DRC markers for `cell_1rw`, `dummy_cell_1rw`, and `replica_cell_1rw`. The same report attributes 40 markers to storage aggregation and sets `storage_aggregation_can_continue=false`; leaf cleanliness therefore cannot be promoted to array cleanliness.

## Authority Boundary

`AUTHORITATIVE_ARRAY_ASSET_NOT_RECOVERED`

No shell, 4x4 prototype, flat clipped region, or built-in DRC result is accepted as a complete bitcell array. The exact missing authority items are listed in the JSON companion file.
