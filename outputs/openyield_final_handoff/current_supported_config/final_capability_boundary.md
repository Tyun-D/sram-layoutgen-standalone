# Final Capability Boundary

| claim | 可以 claim | 证据 | 不能外推 |
| --- | --- | --- | --- |
| OpenYield-driven candidate GDS generated | Yes | /data1/qujh/work/sram_layoutgen_step45_clean/outputs/openyield_top_level_assembly/current_supported_config/openyield_top_level_candidate.gds; /data1/qujh/work/sram_layoutgen_step45_clean/docs/openyield_L4_top_level_assembly_report.json | 不能外推为 DRC clean、LVS clean、timing closure 或 signoff-ready。 |
| L5 basic validation passed | Yes | /data1/qujh/work/sram_layoutgen_step45_clean/docs/openyield_L5_validation_report.json | 不能外推为 full validated GDS。 |
| L6 DRC marker triage completed | Yes | /data1/qujh/work/sram_layoutgen_step45_clean/docs/openyield_L6_drc_marker_triage_report.json | 这里只说明 marker 被分类，不说明 marker 被修复。 |
| DRC clean | No | /data1/qujh/work/sram_layoutgen_step45_clean/docs/openyield_L6_drc_marker_triage_report.json | 24687 个 markers 仍存在，不能 claim DRC clean。 |
| LVS clean | No | /data1/qujh/work/sram_layoutgen_step45_clean/docs/openyield_L5_validation_report.json | LVS 仍 blocked by missing netlist。 |
| timing closure | No | /data1/qujh/work/sram_layoutgen_step45_clean/docs/openyield_L5_validation_report.json | timing 仍是 metadata / smoke 级别。 |
| signoff-ready SRAM compiler | No | /data1/qujh/work/sram_layoutgen_step45_clean/outputs/openyield_project_closure/current_supported_config/project_v1_limitation_statement.md | 当前交付物是 candidate GDS，不是 signoff-ready SRAM compiler。 |
