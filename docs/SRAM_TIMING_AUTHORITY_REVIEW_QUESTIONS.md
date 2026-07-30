# SRAM Timing Authority Review Questions

Only these three owner-review items remain for project-level functional closure.

1. After `add_cs_startup_clamp`, when does the first valid functional cycle begin?
   Candidate A: first cycle only after startup clamp release plus one full guard cycle.
   Candidate B: first post-release low phase of `gated_clk_bar` is already functional.

2. What is the reviewed top-level write success oracle?
   Candidate A: write completes when internal cell `Q/QB` settles, but top-level debug must infer success through a later `SA_Q/SA_QB` readback.
   Candidate B: there is an exported top-level proxy edge or window that can be frozen as the write sample point.

3. Under disabled `csb/web` combinations, what observable top-level hold behavior is required?
   Candidate A: preserve prior cell state and leave `SA_Q/SA_QB` unchanged until a later selected read.
   Candidate B: preserve state internally, but `SA_Q/SA_QB` may legally float or refresh due to analog front-end behavior.

