# Final Limitations And Risks

- DRC markers = 24687，当前不能 claim DRC clean。
- 当前 top-level GDS 是 candidate layout，不是 signoff layout，也不是可流片版图。
- 部分模块仍使用 candidate geometry，会阻塞 DRC/LVS/timing/signoff claim。
- 部分模块仍使用 contract pins，适合 basic validation，但不适合 DRC/LVS signoff。
- LVS blocked by missing netlist，当前不能 claim LVS clean。
- timing 仍是 metadata / smoke 级别，当前不能 claim timing closure。
- 当前 scope 仅覆盖 single-bank / single-port / words_per_row 1/2 / column_mux_ratio 1/2。
- multi-bank / multi-port / write mask / write_size / words_per_row > 2 / column_mux_ratio > 2 均不在当前支持范围内。
- 当前 DRC marker 分类依赖当前 deck、当前 GDS 和当前 parser，不代表最终物理收敛。
