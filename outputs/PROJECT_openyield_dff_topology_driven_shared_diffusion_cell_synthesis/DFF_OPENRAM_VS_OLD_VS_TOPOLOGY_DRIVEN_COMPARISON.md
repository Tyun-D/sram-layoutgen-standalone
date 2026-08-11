# OpenRAM vs Old vs Topology-Driven DFF

OpenRAM is reference-only and is not instantiated or copied.

| Layout | Role | Area | Active islands | Contacts |
|---|---:|---:|---:|---:|
| OpenRAM reference | reference only | 7.6362 | 8 | from layer count 97 |
| previous BEST_AREA | old generated baseline | 32.5779 | 22 | 44 |
| previous BEST_BALANCED | old generated baseline | 33.1545 | 22 | 44 |
| topology-driven recommended | new generated candidate | 10.557 | 5 | 27 |

Human-review conclusions:
1. Previous four-row architecture was large because functional clusters forced extra row bases and kept each MOS as an isolated active rectangle.
2. Logical diffusion sharing failed physically because previous GDS still emitted one ACTIVE polygon per MOS.
3. The graph-theoretic minimum is computed in `OPENYIELD_DFF_GLOBAL_DIFFUSION_GRAPH.json` and `DFF_GLOBAL_TRAIL_COVER_PROOF.json`.
4. The new candidate physically merges shareable source/drain adjacencies into continuous ACTIVE strips.
5. Remaining area gap to OpenRAM is attributable to conservative OpenYield W/L preservation, conservative pin/access routing, and no OpenRAM polygon/library reuse.
