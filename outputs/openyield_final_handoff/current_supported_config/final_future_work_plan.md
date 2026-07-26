# Final Future Work Plan

- 1. P1 `LAYER_MAP_OR_DRC_DECK_INTERPRETATION`: 先做 deck / layer map / imported source geometry grid audit，再决定 source snapping 或 deck policy。
- 2. P4 `CONTRACT_PIN_GEOMETRY_PLACEHOLDER`: 将 contract pin 转为 geometry-backed pin/access proof。
- 3. P3 `CANDIDATE_GEOMETRY_INTERNAL`: 优先做 row_decoder generator-level cleanup。
- 4. P3 `MODULE_INTERNAL_HARDMACRO`: 审计 wordline_driver / column_mux 的 hardmacro internal 问题。
- 5. P3 `MODULE_WRAPPER_IMPORT`: 复核 write_driver / sense_amp 的 wrapper import path。
- 6. 只有在上述修复形成稳定几何与 netlist 对齐后，才适合重新进入 LVS feasibility 与更高层级 timing evidence。
