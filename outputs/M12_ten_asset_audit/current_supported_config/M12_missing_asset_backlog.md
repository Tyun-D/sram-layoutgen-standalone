# M12 Missing Asset Backlog

| asset_id | status_level | next_stage_to_fill | next_action |
| --- | --- | --- | --- |
| PHYSICAL_IMPLEMENTATION_LIBRARY | PARTIAL | M11A | Run M11A to qualify which OpenYield module GDS can be treated as reusable hardmacros versus fallback-only candidates. |
| PIN_BBOX_RAIL_METADATA | PARTIAL | M11B | Run M11B on top of M11A results to extract and verify pin/bbox/rail metadata only from qualified module GDS. |
| SRAM_CONFIGURATION | PARTIAL | M11H | First clear M11H gate status, then keep narrowing fallback fields before claiming config-aware translator v3. |
| FLOORPLAN_RULES | PARTIAL | M11C | After M11A/M11B, run selective substitution smoke and variation generation to prove adaptive floorplan behavior. |
| PLACEMENT_RULES | PARTIAL | M11C | Use M11A/M11B outputs to rerun placement smoke for qualified substitution sites. |
| ROUTING_RULES | PARTIAL | M12B | Generate variation GDS and routing/power adaptation evidence after module qualification. |
| POWER_PLAN | PARTIAL | M12B | After M11B metadata extraction, qualify rail overlap/stitch compatibility for each substitution candidate. |
| VERIFICATION_AND_TRACE | PARTIAL | M13 | Keep review manifests and diff reports, then advance to DRC/LVS feasibility only after qualification and variation adaptation work. |
