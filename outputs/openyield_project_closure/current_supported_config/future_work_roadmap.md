# Future Work Roadmap

## A. DRC Clean Continuation

- 1. DRC deck / layer map / source geometry grid audit: 先判断 FreePDK45 deck grid 与 imported source geometry 是否系统性不一致。
- 2. imported GDS off-grid snapping 或 deck policy decision: 确定是修 source geometry、做 grid snapping，还是调整 deck policy。
- 3. contract pins 转 geometry-backed pin: 把 contract pin 模块转成 geometry-backed pin/access proof。
- 4. row_decoder candidate geometry cleanup: 对 row_decoder 做 generator-level cleanup。
- 5. hardmacro internal DRC audit: 审计 wordline_driver / column_mux 的 imported hardmacro 内部 DRC。
- 6. wrapper import artifact review: 复核 write_driver / sense_amp 的 wrapper import artifact。
- 7. rerun DRC and compare marker deltas: 每轮修复后重新运行 DRC，并比较 marker delta。
- 8. repeat targeted generator repair until marker count substantially decreases: 持续按 root cause priority 迭代，直到系统性 marker 大幅下降。

## B. LVS / Timing Continuation

- 1. export consistent top-level netlist: 导出与当前 top-level GDS 对齐的顶层网表。
- 2. establish module-to-netlist mapping: 建立 module GDS 到 netlist object 的稳定映射。
- 3. build pin geometry to net mapping: 把 geometry-backed pins 映射到 netlist pins。
- 4. resolve contract pin modules: 先消除 contract pin 模块，再推进 LVS。
- 5. run LVS feasibility smoke: 在 consistent netlist 存在后先跑 feasibility smoke。
- 6. only after LVS feasibility, attempt LVS clean: 只有 feasibility 稳定后才进入 LVS clean 目标。
- 7. timing closure 需建立 path-level evidence: 后续 timing closure 需要 SPEF/RC/path-level evidence，当前不 claim。
