# OpenYield SRAM LayoutGen Project Status

## 1. Current Correct Goal

基于原 layoutgen 版图生成器，将 OpenYield 的模块、网表语义和连接关系接入真实 SRAM GDS 生成主干，生成 OpenYield-driven layoutgen-based SRAM GDS。

## 2. Current Route

- S0：全部成果整理与路线重置
- L0：layoutgen 原生成路径与第一轮 OpenYield 模块 GDS 审计
- L1：OpenYield module/net → layoutgen generator 绑定
- L2：重新生成 OpenYield real module GDS
- L3：layoutgen-based OpenYield SRAM top GDS 生成
- L4：真实连接、电源、验证与最终交付

## 3. Important Results So Far

| result_name | path | what_is_valid | what_is_not_valid | can_reuse | reuse_scope | risk |
| --- | --- | --- | --- | --- | --- | --- |
| First-round OpenYield module GDS generation | outputs/openyield_module_gds/ | Module GDS files, pins/bbox/rail metadata, and generator manifests exist for 20 modules. | Not yet proven that every module is the right physical implementation for final SRAM assembly. | True | L0-L2 input audit and regeneration | Must distinguish real module vs candidate vs replaceable artifact. |
| R0 OpenRAM audit | docs/ and OpenRAM source audit artifacts | Rule/reference understanding of SRAM physical organization. | OpenRAM output is not final OpenYield output. | True | L0-L4 reference only | Do not regress into OpenRAM black-box flow. |
| R1 layout intent | outputs/openyield_layout_intent/current_supported_config/ | OpenYield module/net semantics and intent mapping. | Intent alone is not physical proof. | True | L0-L4 semantic driver | Must be bound to real layoutgen generation path. |
| R2 generator architecture | scripts/openyield_R2_generator_architecture_design.py + reports | Architecture decomposition and generator boundary planning. | Does not prove final GDS implementation quality. | True | L0-L4 planning | Must reconnect to real layoutgen assembly path. |
| C0 gap audit | outputs/openyield_complete_gds_gap_audit/current_supported_config/ | Accurate evidence for contract/approximate/missing pin gaps in old prototype route. | Its closure results must be reinterpreted after route reset. | True | L0-L4 risk baseline | Do not treat old closure counts as sufficient physical completeness proof. |
| C1 physical rule extraction | outputs/openyield_complete_gds_rule_extraction/current_supported_config/ | Useful rulebook and comparison baseline. | Not a substitute for real layoutgen generation. | True | L0-L4 rule reference | Must not drift into source-only mimicry. |
| C2 pin access repair | outputs/openyield_pin_access_repair/current_supported_config/ | Repaired/synthesized pin access metadata and access views. | Synthesized pin access cannot alone justify physical-complete claim. | True | L0-L2 audit input and optional metadata hints | Must be re-audited against real layoutgen module generation. |
| C3 floorplan reconstruction | outputs/openyield_complete_floorplan/current_supported_config/ | Useful placement/floorplan intent and review evidence. | Proxy-floorplan GDS is not final real macro assembly. | True | L0-L4 review/reference | Do not keep floorplan_proxy as implementation hierarchy. |
| C4 signal routing | outputs/openyield_complete_signal_routing/current_supported_config/ | Geometry-backed semantic routing prototype and validation schema. | Based on access-view modules, not final physical module hierarchy. | True | L0-L4 evidence/reference | Do not reuse as final physical routing implementation. |
| C5 power stitching | outputs/openyield_complete_power_network/current_supported_config/ | Geometry-backed semantic power connectivity prototype and validation schema. | Still layered on access-view hierarchy. | True | L0-L4 evidence/reference | Do not reuse as final physical power implementation. |
| C6 final access-view GDS | outputs/openyield_complete_sram/current_supported_config/openyield_complete_sram.gds | A parseable OpenYield-connected access-view GDS prototype with report bundle. | Cannot be claimed as real complete SRAM GDS anymore. | True | Review/reference only | Must be explicitly downgraded. |

## 4. Reclassified / Downgraded Results

`outputs/openyield_complete_sram/current_supported_config/openyield_complete_sram.gds` 从 complete SRAM GDS 降级为 access-view prototype。

原因：
- top hierarchy 主要是 `*_access_module`。
- 没有真实 bitcell array 主体。
- 没有达到 layoutgen/OpenRAM 的物理完整度。
- 视觉上不像真实 SRAM macro。
- `DRC marker_count = 431`。
- LVS 未运行。
- 不能 claim DRC/LVS/signoff。

## 5. Reusable Artifacts

| artifact_name | path | artifact_type | why_reusable | reuse_scope | risk |
| --- | --- | --- | --- | --- | --- |
| layoutgen_generator_code | sram_layoutgen/ | generator_codebase | This is the correct底座 for real SRAM GDS generation. | L0-L4 | Must be re-bound to OpenYield semantics carefully. |
| first_round_openyield_module_gds | outputs/openyield_module_gds/ | module_gds_input | Important input candidates and metadata source. | L0-L2 | Not all modules are guaranteed final physical implementations. |
| R1_layout_intent | docs/ + outputs/openyield_layout_intent/current_supported_config/ | semantic_intent | Carries OpenYield layout intent and role mapping. | L0-L4 | Intent must be mapped onto real layoutgen generation flow. |
| R2_generator_architecture | docs/ + scripts/openyield_R2_generator_architecture_design.py | architecture | Defines OpenYield-driven architecture concepts. | L0-L4 | Architecture must not be confused with final physical proof. |
| C0_to_C6_validation_framework | docs/ + scripts/ + tests/ + outputs/openyield_* | audit_and_validation | Provides reusable report schema and regression hooks. | L0-L4 | Some report conclusions must be downgraded/reclassified. |
| openram_source_and_reference_gds | /data1/qujh/OpenRAM + outputs/layout_prototype/baseline_legacy/ | reference_rule_sample | Useful as rule/sample/visual reference only. | L0-L4 | Must not be mistaken for final OpenYield GDS. |
| layoutgen_baseline_reference_gds | outputs/layout_prototype/baseline_legacy/sram_8x64_wpr4_fd45.complete.gds | visual_reference_sample | Useful as review baseline and visual/structural comparator. | L0-L4 review | Do not use as final OpenYield output. |
| module_gds_generators_py | sram_layoutgen/openyield_adapter/module_gds_generators.py | module_generator | Direct hook into first-round OpenYield module GDS generation. | L0-L2 | Must re-audit generated modules before trust. |

## 6. Deprecated / Do-Not-Use-As-Final Artifacts

| artifact_name | path | deprecated_reason | do_not_use_as_final |
| --- | --- | --- | --- |
| openyield_complete_sram_gds_claim | outputs/openyield_complete_sram/current_supported_config/openyield_complete_sram.gds | Reclassified as OpenYield-connected access-view GDS prototype, not real complete SRAM GDS. | True |
| access_module_cells | *_access_module | Cannot serve as SRAM physical implementation主体. | True |
| floorplan_proxy_cells | floorplan_proxy* | Only acceptable for review/floorplan proof, not final physical module hierarchy. | True |
| access_view_route | C4 access-view signal route shapes | Useful as semantic/prototype evidence, not sufficient as physical complete claim basis. | True |
| access_view_power_stitch | C5 access-view power stitch shapes | Useful as prototype geometry evidence, not final physical implementation proof. | True |
| synthesized_pin_complete_claim_support | C2 synthesized pin access | Cannot alone support physical complete claim. | True |

## 7. Required Human Review Rule

每个阶段必须生成 review GDS。每个阶段完成后，不能自动进入下一阶段。必须等待用户在 KLayout 打开 review GDS 并确认。若用户认为视觉/结构路线错误，必须立即停止并纠偏。

## 8. GDS Review Requirements

| review_name | status | source_path | copied_path | top_cell_name | what_to_check_in_klayout | expected_visual_features | known_risks | can_enter_next_stage_after_user_confirmation |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| previous_access_view_final | COPIED | /data1/qujh/work/sram_layoutgen_step45_clean/outputs/openyield_complete_sram/current_supported_config/openyield_complete_sram.gds | /data1/qujh/work/sram_layoutgen_step45_clean/outputs/project_status_reset_review/current_supported_config/previous_access_view_final.gds | openyield_complete_sram | Confirm this looks like access-view/proxy assembly rather than a real SRAM macro. | Access-view style hierarchy, abstract connectivity, smaller GDS footprint. | Cannot be used as final physical SRAM GDS. | True |
| layoutgen_reference | COPIED | /data1/qujh/work/sram_layoutgen_step45_clean/outputs/layout_prototype/baseline_legacy/sram_8x64_wpr4_fd45.complete.gds | /data1/qujh/work/sram_layoutgen_step45_clean/outputs/project_status_reset_review/current_supported_config/layoutgen_reference.gds | sram_8x64_wpr4_fd45 | Use as visual/structural comparator for what a real SRAM macro should resemble. | Dense array-centric macro, real periphery organization, more SRAM-like visual structure. | Reference only; not final OpenYield output. | True |
| first_round_openyield_candidate | COPIED | /data1/qujh/work/sram_layoutgen_step45_clean/outputs/openyield_top_level_assembly/current_supported_config/openyield_top_level_candidate.gds | /data1/qujh/work/sram_layoutgen_step45_clean/outputs/project_status_reset_review/current_supported_config/first_round_openyield_candidate.gds | openyield_top_level_candidate | Assess whether first-round top candidate is closer to real physical assembly than the access-view final. | May expose earlier top-level assembly direction and generator limitations. | Candidate only; may not be structurally valid final macro. | True |

## 9. Cannot Claim

- DRC clean
- LVS clean
- timing closure
- signoff-ready
- tapeout-ready

除非有真实工具证据。

## 10. Next Immediate Task

S0 完成后进入 L0：layoutgen 原生成路径与第一轮 OpenYield module GDS 审计。
