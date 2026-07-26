# Project v1 Capability Statement

- OpenYield 语义到本地 layoutgen 的映射已建立。
- 当前 scope 支持 single-bank、single-port、words_per_row 1/2。
- 20 个 L3 target modules 已生成 standalone module GDS。
- 20 个模块均有 generator manifest / pins / bbox / rail metadata。
- top-level SRAM candidate GDS 已生成。
- top-level GDS hierarchy 完整。
- top-level GDS 可解析。
- 20 个 required modules 全部实例化。
- L5 basic validation 已通过，remaining_L5_basic_validation_blockers_count=0。
- DRC marker 已完成 100% 分类，coverage=1.0。
- 已形成后续 DRC 修复优先级计划。

当前不能 claim: DRC clean / LVS clean / timing closure / full validated GDS / signoff-ready SRAM compiler / 可流片版图。
