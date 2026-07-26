# M5 Remaining Gap Report

| gap_id | module_or_net | category | description | blocks_M5_gate | planned_next_action |
| --- | --- | --- | --- | --- | --- |
| M5_GAP_001 | fallback_control_time_modules | non_blocking_scope_limit | Six control/time modules remain on layoutgen fallback physical backbone with OpenYield semantics instead of native OpenYield physical cells. | False | keep fallback scope explicit until post-review stage |
| M5_GAP_002 | openyield_sram_layout_intent.json | non_blocking_parameter_mismatch | Intent JSON is still narrower than the optimized implementation baseline: intent(word_size=4,num_words=4,words_per_row=1) vs optimized(word_size=8,num_words=64,words_per_row=4). | False | align canonical OpenYield intent parameters after human review |
