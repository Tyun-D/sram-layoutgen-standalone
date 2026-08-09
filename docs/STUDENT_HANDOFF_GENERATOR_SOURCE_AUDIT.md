# Student Handoff Generator Source Audit

Audit timestamp: 2026-08-09T05:02:51Z

Conclusion: the legacy/simplified generator source is present in current HEAD and is runnable through `python -m sram_layoutgen`.

Generator entrypoint:

- Package root: `sram_layoutgen/`
- CLI: `sram_layoutgen/__main__.py`
- Spec/build/write path: `sram_layoutgen/standalone.py`
- Main callable: `write_standalone(StandaloneSpec(...), out_dir)`

Key source files:

| path | role | SHA256 | tracked |
|---|---|---|---|
| `sram_layoutgen/__main__.py` | CLI/config loader | `9d45373b171e6890d66fce0d805d89e1e5b3b3d3ec23e716dcd0b0ee15e3eb76` | yes |
| `sram_layoutgen/standalone.py` | `StandaloneSpec`, `build_layout`, `write_standalone`, placement/routing/power/pin/report orchestration | `c53526acba2f1ab25606fa7a4b43f46aa00a7863ec179e6887218df327afb23e` | yes |
| `sram_layoutgen/tech.py` | FreePDK45 tech/layer/hardmacro loader | `5c296c65764a3cdc3fc7ce42bb9308b990e5c9e7ad3b0965aa1e5d15093090ed` | yes |
| `sram_layoutgen/gds_writer.py` | GDS writer including hierarchy/debug/route-guide overlays | `86d5ab3898adf08fb7cd54956f7450d93e8c3f2b11a11155f50611c80b2cbd62` | yes |
| `sram_layoutgen/lef_writer.py` | LEF writer | `f9d083a4dd97ed42ba00d0773a5fe492f2bbb5f28f1a82e45f221125373a361e` | yes |
| `sram_layoutgen/netlist_writer.py` | structural SPICE writer | `d5436d3929c4c00c06ed4a46ca609c3ae920014a4ba0037aa10df5c17aa68cae` | yes |
| `sram_layoutgen/geometry.py` | layout database, pins, JSON/SVG serialization | `7052f636f6c8d88f0335ff9f42511962431359d350c01e87d123194ebce7ecfa` | yes |
| `sram_layoutgen/gds_util.py` | GDS hierarchy/layer/text/bbox inspection helpers | `f6269a803a43e83c793a9a56000509522a0314e46ddce314524513f1bb8a7f52` | yes |
| `sram_layoutgen/verifier.py` | built-in geometry/connectivity/power sanity checks | `8d089649db26a150025bfd19087a426f95231302e43a7a6a2bec18aea9e69e5a` | yes |
| `sram_layoutgen/occupancy.py` | occupancy analysis/SVG writer | `515aa7aa995a8c6ba1c9ce3e5ff7ef5543a1e1ad4ec8dd96aa62372eb5b8ed59` | yes |
| `sram_layoutgen/openram_placement.py` | OpenRAM-style origin/mirror placement helpers | `82b2afc61f1bf6eabce6b7cda84445ef45796815343416d18967442daef66843` | yes |
| `sram_layoutgen/stdcell.py` | generated standard-cell helper/pin extraction | `5f6087b82ec40aff9bb022c79937e00c2c181504087807692a72bfd4f0f00e2c` | yes |

Required bundled data/assets:

- `technology/freepdk45/layers.map`
- `technology/freepdk45/replacement_macros.json`
- `technology/freepdk45/openyield_repaired_macro_aliases.json`
- `technology/freepdk45/gds_lib/*.gds`
- `technology/freepdk45/gds_lib/openram_replacements/*.gds`
- `technology/freepdk45/gds_lib/openyield_repaired/*.gds`
- `technology/freepdk45/sp_lib/*.sp`
- optional validation decks: `technology/freepdk45/tech/freepdk45.lydrc`, `.lylvs`, `.lyt`, `.lyp`

Legacy vs OpenYield separation:

- Legacy generator core: `__main__.py`, `standalone.py`, `geometry.py`, `gds_writer.py`, `lef_writer.py`, `netlist_writer.py`, `tech.py`, `gds_util.py`, `stdcell.py`, `openram_placement.py`, `occupancy.py`, `verifier.py`.
- Current OpenYield validation/integration path: `sram_layoutgen/openyield_adapter/*`, `outputs/openyield_*`, `outputs/PROJECT_*`, decoder/P2/P3/full-top integration scripts and reports.
- `standalone.py` imports some `openyield_adapter` helper modules for optional adapters and reuse checks, but the CLI smoke tests succeeded with the default legacy flags and bundled assets.
