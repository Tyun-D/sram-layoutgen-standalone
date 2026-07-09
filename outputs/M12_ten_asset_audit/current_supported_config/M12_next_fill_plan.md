# M12 Next Fill Plan

- recommended_next_stage: `M11H`

## 1. M11H

- why_now: `Clear the config-aware translator claim gate before expanding substitution work.`
- depends_on: `M11 outputs`
- blocks_assets: `SRAM_CONFIGURATION;VERIFICATION_AND_TRACE`
- entry_condition: `docs/M11H_confirm_config_aware_translator_report.json missing`

## 2. M11A

- why_now: `Qualify OpenYield module GDS before treating them as hardmacro candidates.`
- depends_on: `M11H or accepted M11 claim boundary`
- blocks_assets: `PHYSICAL_IMPLEMENTATION_LIBRARY`
- entry_condition: `Need per-module qualification and replacement boundary`

## 3. M11B

- why_now: `Only qualified modules should feed pin/bbox/rail extraction.`
- depends_on: `M11A`
- blocks_assets: `PIN_BBOX_RAIL_METADATA;POWER_PLAN`
- entry_condition: `Qualified module GDS list available`

## 4. M11C

- why_now: `Selective hardmacro substitution smoke proves floorplan and placement compatibility.`
- depends_on: `M11A;M11B`
- blocks_assets: `FLOORPLAN_RULES;PLACEMENT_RULES`
- entry_condition: `Qualified modules plus verified metadata available`

## 5. M12A

- why_now: `Generate variation GDS for 4x32_wpr2 and 16x16_wpr1.`
- depends_on: `M11H;M11C`
- blocks_assets: `SRAM_CONFIGURATION;ROUTING_RULES`
- entry_condition: `Variation-aware inputs can be driven through the locked flow extensions`

## 6. M12B

- why_now: `Adapt routing and power policy to variation and substitution outputs.`
- depends_on: `M12A`
- blocks_assets: `ROUTING_RULES;POWER_PLAN`
- entry_condition: `Variation GDS evidence exists`

## 7. M13

- why_now: `Only after physical qualification and variation proof should DRC/LVS feasibility and equivalence trace run.`
- depends_on: `M11A;M11B;M11C;M12A;M12B`
- blocks_assets: `VERIFICATION_AND_TRACE`
- entry_condition: `Physical and routing/power deltas materially closed`
