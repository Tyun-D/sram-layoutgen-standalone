# Project v1 Limitation Statement

- DRC markers = 24687，尚未清零。 当前不能 claim DRC clean。
- 当前 top-level GDS 是 candidate layout，不是 signoff layout。 当前终点是可交付候选态，不是可流片版图。
- 部分模块使用 candidate geometry。 这些模块会阻塞 DRC/LVS/timing/signoff claim。
- 部分模块使用 contract pins。 这些模块适合 basic validation，但不适合 DRC/LVS signoff。
- LVS blocked by missing netlist。 当前不能 claim LVS clean。
- timing 仍是 metadata / smoke 级别。 当前不能 claim timing closure。
- 当前仅覆盖 single-bank / single-port / limited words_per_row。 更广 scope 仍未进入当前交付态。
- multi-bank / multi-port / write mask / larger mux ratio 仍 unsupported。 这些功能需要新增独立实现阶段。
- DRC marker 分类依赖当前 deck、当前 GDS 和当前 marker parser，不代表最终物理收敛。 后续若更换 deck 或 source geometry，分类比例可能变化。
