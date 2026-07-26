# Final Figure and Table Requirements

| item | source_path | recommended_view | debug_layers_to_hide | resolution | caption_points | already_exists | owner |
| --- | --- | --- | --- | --- | --- | --- | --- |
| OpenRAM baseline layout | technology/freepdk45/gds_lib/*.gds; docs/openram_gds_generation_audit_report.md | 代表 bitcell/column/read path | text/debug | 300dpi | OpenRAM reference baseline only | False | project |
| 简化 layoutgen 8x64_wpr4 | outputs/M2R_full_sram_regen/current_supported_config/openyield_layoutgen_full_sram_M2R.presentation.gds | top-level macro overview | route_guides/debug | 300dpi | generated top-level trial; internal DRC clean; not signoff-complete | False | project |
| OpenYield representative module | outputs/TeamB_9cell_integration/current_supported_config/TEAM_B_9CELL_CLEAN_ATLAS.gds | 9-cell library overview | annotation-only if needed | 300dpi | Team B integrated physical library | True | Team B |
| Team B 9-cell integration atlas | /data1/qujh/TEAM_B_9CELL_INTEGRATION_HUMAN_REVIEW_PACKAGE_LATEST.tar.gz | clean atlas and support atlases | none for review | 300dpi | 0-marker combined DRC and 28/28 negative tests | True | Team B |
| AND2/AND3 zero-gap comparison | outputs/TeamB_and_gate_abutment_optimization/AND2_AND3_ABUTMENT_DECISION.md | baseline vs zero-gap review atlas | debug labels in formal GDS | 300dpi | parent power stitching true while child edge abutment false | True | Team B |
| delay-chain stage/load schematic | docs/figures/delay_chain_stage_load_baseline.mmd | 9x4 and 4x4 baseline | n/a | vector | current baseline fixed; future parameterization roadmap | True | Team B |
| parameter flow diagram | docs/figures/parameter_flow_diagram.mmd | config to verification pipeline | n/a | vector | parameter legality, netlist, placement, routing, verification | True | project |
| three-route architecture comparison | docs/figures/three_route_architecture_comparison.mmd | three-column comparison diagram | n/a | vector | OpenRAM vs simplified layoutgen vs OpenYield | True | project |
| representative area/runtime table | docs/SRAM_CONFIGURATION_INVENTORY.csv | table | n/a | print | only explicit evidence-backed configs | False | project |
| verification summary table | docs/PROJECT_RESULT_STATUS_MATRIX.csv | status matrix | n/a | print | MACHINE_VERIFIED vs HUMAN_REVIEWED vs MERGED | False | project |
