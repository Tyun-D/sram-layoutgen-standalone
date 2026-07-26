# R1 Layout Intent Gap Summary

R1 的目标是定义 layout intent，而不是生成新的 SRAM physical GDS。

## Boundary

- 旧 `openyield_top_level_candidate.gds` 只作为边界证据，不再继续补丁式扩展。
- 本轮不 claim structure-complete SRAM GDS、DRC clean、LVS clean、timing closure、signoff-ready。

## Module Role Gaps

- All 20 L3 target modules have non-UNKNOWN physical roles.

## Net Role Gaps

- No UNKNOWN net roles remain in the current intent map.

## Exact Next Required Action

- Enter R2 generator architecture design using the canonical parameters, module roles, and net-role map defined by R1.
