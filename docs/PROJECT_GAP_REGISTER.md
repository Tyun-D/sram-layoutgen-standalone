# Project Gap Register

| gap_id | priority | scope | description | blocking | required_action | expected_output |
| --- | --- | --- | --- | --- | --- | --- |
| P0-001 | P0 | project_status | 项目级 CURRENT_STATUS 与旧 Wave4A 状态文件不一致，缺少项目级新基线 | True | establish PROJECT_CURRENT_STATUS and baseline snapshot | PROJECT_CURRENT_STATUS.json |
| P0-002 | P0 | result_inventory | 历史“30 个 SRAM 配置 / 21 个实现模块”说法未从当前主线显式复核 | True | treat old count as unresolved and require explicit evidence expansion | SRAM_CONFIGURATION_AUDIT.md |
| P0-003 | P0 | other_team_results | 其他组员成果仅发现来源和审阅痕迹，尚未进入主线回收计划 | True | owner review and merge/cherry-pick planning | OTHER_TEAM_RESULT_RECOVERY_PLAN.md |
| P1-001 | P1 | parameterization | 逻辑容量字段仍部分依赖 fallback，尚未形成纯 raw-source-backed public config path | False | replace fallback with first-class config manifest | new config authority audit |
| P1-002 | P1 | decoder_physicalization | decoder 仍停留在规则/代理/临时 wrapper 阶段 | False | complete legal placement and routing closure | decoder machine gate |
| P1-003 | P1 | top_level_signoff | M2R top-level full SRAM 没有外部 DRC/LVS/PEX 和最终 signoff | False | run external signoff toolchain or document exclusion | signoff audit |
| P1-004 | P1 | multi_bank | bank_count 只验证到 1 | False | design and audit multi-bank physical flow | multi-bank config evidence |
| P2-001 | P2 | figures | 三路线比较图与参数流图尚未制图 | False | prepare publication-quality diagrams | figure assets |
| P2-002 | P2 | screenshots | 代表性配置和 OpenRAM/layoutgen top views still need curated screenshots | False | capture clean views | review screenshots |
| P3-001 | P3 | future_extension | delay-chain stage/load、tap spacing、多 PDK 等仍属未来扩展 | False | future design exploration | roadmap items |
