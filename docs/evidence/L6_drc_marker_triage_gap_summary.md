# L6 DRC Marker Triage Gap Summary

1. 当前 DRC marker 总数：`24687`。
2. DRC marker 解析方式：直接解析 KLayout `.lyrdb` XML，提取 category/cell/value 几何文本并还原 bbox。
3. marker rule 分布：最高规则为 `GRID: vertexes on layer cont not on grid of 0.0025`，数量 `6495`。
4. marker 空间分布：已完成 module/boundary/tile 级聚类，主导 root cause 为 `LAYER_MAP_OR_DRC_DECK_INTERPRETATION`。
5. marker 映射模块：主要集中在 `bitcell_array, dummy_array, replica_array, sense_amp, write_driver, wordline_driver, precharge, column_mux, DFF_ROW, CONTROL_LOGIC`。
6. 主要 root cause 分类：`LAYER_MAP_OR_DRC_DECK_INTERPRETATION, CONTRACT_PIN_GEOMETRY_PLACEHOLDER, CANDIDATE_GEOMETRY_INTERNAL, MODULE_INTERNAL_HARDMACRO, MODULE_WRAPPER_IMPORT`。
7. classification coverage：`1.0`。
8. 最高优先级修复对象：`LAYER_MAP_OR_DRC_DECK_INTERPRETATION`，优先级 `P1`。
9. 当前仍不能 claim DRC clean，因为 marker 总数仍然很高，且系统性 root-cause 族尚未消除。
10. 是否可以进入 L7 DRC repair planning：`True`。
