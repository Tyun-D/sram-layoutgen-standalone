# Netlist-to-Layout Goal

## Goal

在已锁定的 layoutgen golden flow 上，把 OpenYield 网表语义、模块候选、配置、floorplan、placement、routing、power 和验证证据收敛成可追溯的 netlist-to-layout 资产闭环。

## Ten Required Assets

- `NETLIST_SEMANTICS`: 网表 / module / instance / net / pin 连接语义 [COMPLETE]
- `PHYSICAL_IMPLEMENTATION_LIBRARY`: 模块物理实现库，包括 layoutgen cell、OpenYield module GDS、hardmacro 候选 [PARTIAL]
- `PIN_BBOX_RAIL_METADATA`: pin / bbox / rail / layer / access metadata [PARTIAL]
- `SRAM_CONFIGURATION`: SRAM 参数配置，包括 word_size、num_words、words_per_row、rows、cols、mux ratio [PARTIAL]
- `FLOORPLAN_RULES`: floorplan 规则，包括 array、row path、column path、control、top pin 区域 [PARTIAL]
- `PLACEMENT_RULES`: placement / abutment / orientation / pitch 对齐规则 [PARTIAL]
- `ROUTING_RULES`: WL、BL/BR、control、data、addr、enable 等 routing 规则 [PARTIAL]
- `POWER_PLAN`: VDD/GND rail overlap、stitch、abutment、top power pin 策略 [PARTIAL]
- `GDS_GENERATION_FLOW`: GDS generator / layoutgen golden flow / write_standalone 入口 [COMPLETE]
- `VERIFICATION_AND_TRACE`: GDS sanity、golden diff、module/net trace、DRC/LVS feasibility、人工 KLayout review [PARTIAL]

## Reuse Boundary

- 必须复用 M7 golden reference、M8R exact-match flow、M9 binding matrices、M10 source-backed trace、M11 config variation evidence、T1 inventory。
- 不能把 access_module、floorplan_proxy、historical hybrid reference、access-view complete SRAM prototype 当作最终物理实现依据。
