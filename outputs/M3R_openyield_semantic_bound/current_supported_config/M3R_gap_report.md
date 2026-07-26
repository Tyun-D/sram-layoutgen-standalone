# M3R Remaining Gap Report

| gap_id | category | severity | description | blocks_M3R_gate |
| --- | --- | --- | --- | --- |
| M3R_GAP_001 | review_gate | review_only | Human KLayout review is still required to confirm that OpenYield semantic labels and hierarchy traces match user expectations on the preserved SRAM macro. | False |
| M3R_GAP_002 | signoff | review_only | M3R binds semantics onto the physical backbone but does not claim DRC/LVS/signoff closure for the semantic export layer. | False |
