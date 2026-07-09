# M12 Ten Required Assets Status

- `NETLIST_SEMANTICS` => `COMPLETE` : M10 source-backed module/net/instance trace and M9 net binding matrix cover the current supported translator semantics, but this does not expand into a full raw compiler claim.
- `PHYSICAL_IMPLEMENTATION_LIBRARY` => `PARTIAL` : OpenYield module GDS inventory exists for 20 modules and M9 binds them semantically, but the library is not yet qualified for hardmacro substitution.
- `PIN_BBOX_RAIL_METADATA` => `PARTIAL` : Per-module pins/bbox/rail artifacts exist and M8R proves top-level rail overlap recovery, but qualified module-by-module extraction and access validation are incomplete.
- `SRAM_CONFIGURATION` => `PARTIAL` : M11 adds variation support and can derive 8x64_wpr4, 4x32_wpr2, 16x16_wpr1, but word_size/num_words/words_per_row still rely on fallback and M11H gate is missing=True.
- `FLOORPLAN_RULES` => `PARTIAL` : Locked golden flow reproduces the supported config exactly, but adaptive floorplan rules for variation output and selective hardmacro replacement are not yet proven.
- `PLACEMENT_RULES` => `PARTIAL` : Placement, abutment, orientation, and pitch rules are documented and reused by the locked translator path, but they are not proven under qualified OpenYield module substitution.
- `ROUTING_RULES` => `PARTIAL` : Routing semantics and exact-match locked flow are proven, but variable routing adaptation for non-locked variations and qualified module substitution is not yet demonstrated.
- `POWER_PLAN` => `PARTIAL` : M8R recovered the locked power rail overlap and top-level stitch geometry, but qualified module-boundary rail compatibility and substitution-era stitch policy remain open.
- `GDS_GENERATION_FLOW` => `COMPLETE` : The locked layoutgen golden flow and write_standalone entry are proven and reused across M8R, M10, and M11 for current supported delivery.
- `VERIFICATION_AND_TRACE` => `PARTIAL` : GDS sanity, exact-match diff, and source-backed trace exist, but DRC/LVS/signoff claims remain false and M11H confirmation present=False.
