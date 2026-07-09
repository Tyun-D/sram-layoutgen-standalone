# M12 Ten Required Assets Matrix

| asset_id | status_level | next_stage_to_fill | evidence_summary |
| --- | --- | --- | --- |
| NETLIST_SEMANTICS | COMPLETE | REUSE_IN_M11A_AND_LATER | M10 source-backed module/net/instance trace and M9 net binding matrix cover the current supported translator semantics, but this does not expand into a full raw compiler claim. |
| PHYSICAL_IMPLEMENTATION_LIBRARY | PARTIAL | M11A | OpenYield module GDS inventory exists for 20 modules and M9 binds them semantically, but the library is not yet qualified for hardmacro substitution. |
| PIN_BBOX_RAIL_METADATA | PARTIAL | M11B | Per-module pins/bbox/rail artifacts exist and M8R proves top-level rail overlap recovery, but qualified module-by-module extraction and access validation are incomplete. |
| SRAM_CONFIGURATION | PARTIAL | M11H | M11 adds variation support and can derive 8x64_wpr4, 4x32_wpr2, 16x16_wpr1, but word_size/num_words/words_per_row still rely on fallback and M11H gate is missing=True. |
| FLOORPLAN_RULES | PARTIAL | M11C | Locked golden flow reproduces the supported config exactly, but adaptive floorplan rules for variation output and selective hardmacro replacement are not yet proven. |
| PLACEMENT_RULES | PARTIAL | M11C | Placement, abutment, orientation, and pitch rules are documented and reused by the locked translator path, but they are not proven under qualified OpenYield module substitution. |
| ROUTING_RULES | PARTIAL | M12B | Routing semantics and exact-match locked flow are proven, but variable routing adaptation for non-locked variations and qualified module substitution is not yet demonstrated. |
| POWER_PLAN | PARTIAL | M12B | M8R recovered the locked power rail overlap and top-level stitch geometry, but qualified module-boundary rail compatibility and substitution-era stitch policy remain open. |
| GDS_GENERATION_FLOW | COMPLETE | REUSE_AS_BASELINE | The locked layoutgen golden flow and write_standalone entry are proven and reused across M8R, M10, and M11 for current supported delivery. |
| VERIFICATION_AND_TRACE | PARTIAL | M13 | GDS sanity, exact-match diff, and source-backed trace exist, but DRC/LVS/signoff claims remain false and M11H confirmation present=False. |
