# M12N2 External Dependency Blockers

- M12N2-B01: `OPEN` | TIME role is not explicitly confirmed as on-chip control logic versus simulation timing model. | resolution_action: `OpenYield 中 time_generate.py 生成的 TIME 子电路，是计划作为 SRAM 宏内部真实片上控制逻辑进行物理实现，还是只作为仿真测试平台中的控制时序模型？`
- M12N2-B02: `OPEN` | words_per_row > 1 and arbitrary numeric column mux ratio remain unverified. | resolution_action: `Add explicit raw-source-backed mux-ratio contract and generate verified >1 words_per_row samples.`
- M12N2-B03: `OPEN` | tech parameter is not connected to a physical PDK abstraction for layout generation. | resolution_action: `Define a physical tech/PDK contract distinct from simulation model includes.`
- M12N2-B04: `OPEN` | No complete DRC/LVS/extraction loop is available for the extracted clean top. | resolution_action: `Create a later physical verification stage after layout integration.`
- M12N2-B05: `OPEN` | Control-logic physical implementation is not completed and cannot be claimed ready. | resolution_action: `Wait for TIME role confirmation, then define control-logic physical gap closure scope.`
- M12N2-B06: `MITIGATED_BY_M12N2` | OpenYield exposes a testbench-backed generator rather than a native pure-SRAM-top generator API. | resolution_action: `Keep using extraction/clean-top export until a native pure-top generator exists.`
- M12N2-B07: `OPEN` | OpenRAM references are still missing a matched full SPICE/LEF/Verilog/config contract for direct cross-flow equivalence. | resolution_action: `Provide or align the missing OpenRAM collateral before any equivalence claim.`
