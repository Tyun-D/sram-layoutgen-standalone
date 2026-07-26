# Final Report Section Evidence Matrix

| section | required_claim | supporting_source | figure_needed | table_needed | data_complete | claim_risk | missing_evidence | next_action |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 摘要 | 项目完成了 Team B 九单元正式闭合并建立了项目级盘点 | docs/TEAM_B_CURRENT_STATUS.json; docs/PROJECT_BASELINE_SNAPSHOT.json |  | 项目成果状态矩阵 | True | low |  | reuse generated matrix |
| 研究背景 | OpenRAM / layoutgen / OpenYield 三路线关系 | docs/OPENRAM_LAYOUTGEN_OPENYIELD_COMPARISON.md | 三路线架构对比图 | comparison matrix | True | low |  | render comparison figure |
| 总体架构 | 主线、外部 OpenYield、Team B 闭环关系 | docs/PROJECT_BASELINE_SNAPSHOT.md; docs/PROJECT_RESULT_SOURCE_INVENTORY.json | 项目成果与来源索引图 |  | True | low |  | draw source topology figure |
| OpenRAM 基线 | OpenRAM 是参考基线不是最终 OpenYield 物理结果 | docs/openram_gds_generation_audit_report.md; docs/M12O_openram_openyield_gap_audit_report.md | OpenRAM baseline view |  | True | low |  | capture representative view |
| 简化 layoutgen | layoutgen 可生成真实 GDS 并作为研究平台 | outputs/M2R_full_sram_regen/current_supported_config/openyield_layoutgen_full_sram_M2R.report.json | M2R top-level view | M2R metrics table | True | medium | external signoff absent | state limitations explicitly |
| OpenYield 语义网表 | OpenYield 语义和权威源已锁定 | docs/openyield_module_contracts.json; docs/OPENYIELD_AUTHORITY_REVALIDATION.json | semantic-to-physical mapping figure | module contract summary | True | low |  | render mapping figure |
| 可定制参数体系 | 项目已区分 fully supported / constrained / partial / roadmap 参数 | docs/CUSTOMIZABLE_SRAM_PARAMETER_CATALOG.csv | parameter flow diagram | parameter catalog | True | low |  | reuse catalog and flow |
| 模块级版图生成 | 模块级物理生成已经在 Team B、DFF、DFF_BUF、primitive 等层面建立 | docs/PROJECT_RESULT_STATUS_MATRIX.csv | module inventory figure | module status matrix | True | medium | other-team source recovery still blocked on Owner A confirmation | proceed to P1 while keeping blocked external request explicit |
| Team B 九单元 | 九单元正式 GDS / negative tests / integration / human review 已闭合 | outputs/TeamB_9cell_integration/current_supported_config/TEAM_B_9CELL_INTEGRATION_GATE.json; docs/TEAM_B_OWNER_HUMAN_REVIEW_APPROVAL.json | 9-cell integration atlas; AND2/AND3 zero-gap delta | Team B gate summary | True | low |  | reuse human review package screenshots |
| 版图验证方法 | 真实 DRC/connectivity/foreign-net/negative tests/human review 闭环 | docs/TEAM_B_FINAL_TECHNICAL_REPORT.json; outputs/M2R_full_sram_regen/current_supported_config/openyield_layoutgen_full_sram_M2R.report.json | verification pipeline | verification summary | True | low |  | reuse verification pipeline |
| 负例驱动验证 | Team B 使用模块级和 integration 负例回归 | outputs/TeamB_9cell_integration/current_supported_config/negative_tests/TEAM_B_9CELL_negative_test_summary.json |  | negative test counts | True | low |  | render negative count table |
| 代表性 SRAM 结果 | 当前显式证据绑定的 SRAM 顶层配置库存已从 5 扩展到 10，并与历史 30/21 说法脱钩 | docs/SRAM_CONFIGURATION_INVENTORY.csv; docs/HISTORICAL_30_CONFIG_21_MODULE_CLAIM_AUDIT.json | representative config views | config inventory | True | medium | no basis to restate 30 as current formal count | use audited 10-config inventory only |
| 三路线比较 | OpenRAM / layoutgen / OpenYield 比较建立在真实证据上 | docs/OPENRAM_LAYOUTGEN_OPENYIELD_COMPARISON.csv | comparison radar/block diagram | comparison matrix | True | low |  | render comparison figure |
| 局限与未来工作 | 不能声称 tapeout/signoff/silicon-proven，且仍有其他组成果待回收 | docs/PROJECT_GAP_REGISTER.csv; docs/PROJECT_P0_CLOSURE_GATE.json |  | gap register summary | True | low |  | reuse gap register |
| 作者贡献 | 版图与电路贡献边界清晰 | docs/PROJECT_AUTHOR_CONTRIBUTION_BOUNDARY.md |  |  | True | low |  | reuse boundary statement |
| 工具辅助边界 | AI/Codex 仅为辅助，关键结果由真实证据闭合 | docs/PROJECT_AUTHOR_CONTRIBUTION_BOUNDARY.md |  |  | True | low |  | reuse boundary statement |
