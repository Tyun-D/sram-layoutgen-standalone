# M12N Control Logic Source Matrix

- clock buffer / gated clock: `LOCKED_SEMANTIC_SOURCE` | TIME / pdrive / gating chain inside time_generate
- wordline enable path: `LOCKED_SEMANTIC_SOURCE` | wl_en output within TIME
- precharge enable path: `LOCKED_SEMANTIC_SOURCE` | PRE output within TIME
- sense enable path: `LOCKED_SEMANTIC_SOURCE` | s_en output within TIME
- write enable path: `LOCKED_SEMANTIC_SOURCE` | w_en output within TIME
- address/data flop path: `LOCKED_TESTBENCH_SOURCE` | create_time_circuit + create_D_latch
