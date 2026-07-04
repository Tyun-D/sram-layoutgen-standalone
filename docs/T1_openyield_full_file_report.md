# T1 OpenYield Full File Report

## Summary

- clean_review_gds_generated: `True`
- clean_review_gds_path: `/data1/qujh/work/sram_layoutgen_step45_clean/outputs/T1_clean_m5_review/current_supported_config/openyield_layoutgen_integrated_sram_clean_review.gds`
- clean_gds_sanity_status: `GDS_PARSED_SANITY_PASSED`
- removed_text_count: `74`
- physical_shape_preserved: `True`
- cell_hierarchy_preserved: `True`
- openyield_file_count_total: `130`
- openyield_source_file_count: `94`
- openyield_netlist_candidate_file_count: `37`
- key_entrypoints: `main_sram.py, main_opt.py, main_estimation.py, equivalent_modeling/main_sram.py, demo_run_a_testbench.py`

## Required Answers

1. OpenYield 项目整体是做什么的；
OpenYield 整体更像一个 SRAM 电路网表生成、仿真、yield estimation 和参数优化项目，核心输出围绕 SPICE/PySpice/Xyce，而不是 physical GDS 版图库。

2. 它里面是否真的包含可直接用于版图生成的 GDS module；
没有发现 OpenYield 自带的 `.gds` physical module 库。当前 inventory 中不存在可直接作为 layoutgen physical macro 输入的 OpenYield GDS 模块证据。

3. 它是否更偏网表/优化/算法，而不是 physical layout；
是。目录结构和入口脚本都表明它更偏网表生成、仿真、yield estimation、以及 sizing/architecture optimization，而不是 physical layout。

4. 哪些文件能作为 OpenYield 网表语义来源；
主要是 `main_sram.py`、`config.py`、`sram_compiler/subcircuits/*.py`、`sram_compiler/testbenches/*.py`、`sram_compiler/config_yaml/*.yaml`。

5. 哪些文件能作为 module mapping 来源；
主要是 `sram_compiler/subcircuits/decoder.py`、`wordline_driver.py`、`precharge_and_write_driver.py`、`mux_and_sa.py`、`sram_6t_core.py`、`time_generate.py`，以及相应 YAML 配置。

6. 哪些文件能作为 layoutgen 输入；
下一阶段最适合作为 translator 输入的是 `main_sram.py`、`config.py`、`sram_compiler/config_yaml/*.yaml`、`sram_compiler/subcircuits/*.py`、以及部分 testbench 连接逻辑。

7. 哪些文件不能直接用于 GDS；
`yield_estimation/`、`size_optimization/`、`equivalent_modeling/`、`tran_models/`、图片和说明文档都不能直接用于 GDS 生成。

8. 下一阶段如果要做“网表翻译器”，应该读取哪些 OpenYield 文件；
应优先读取 `main_sram.py`、`config.py`、`sram_compiler/config_yaml/global.yaml`、各模块 YAML，以及 `sram_compiler/subcircuits/*.py` 和 `sram_compiler/testbenches/parameter_factor.py`。

9. 当前 M5 为什么不能证明 GDS 来自 OpenYield 网表；
因为当前证据主要是 M5/OpenYield 文本标签和 wrapper hierarchy。标签只能证明人工标注，不足以证明每个 GDS module、instance、net 都从 OpenYield netlist 被逐步翻译并落到了真实 layoutgen 物理对象上。

10. 需要怎样的 netlist-to-layout trace 才能证明。
需要从 OpenYield module definition/netlist source 到 layoutgen generator binding、instance placement、route/power realization、最终 GDS cell/reference/net correspondence 的可追溯链路，并且每一步都能回溯到源 netlist 语义，而不是仅靠 text label。

## Gate

- next_stage_should_be_netlist_to_layout_translator: `True`
- human_klayout_review_required: `True`
- can_enter_next_stage_before_human_review: `False`
