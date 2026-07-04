# OpenYield Key Entrypoints

| relative_path | status | main_purpose | relevance_category | can_provide_netlist_semantics | can_be_used_in_next_stage | why |
| --- | --- | --- | --- | --- | --- | --- |
| main_sram.py | IDENTIFIED | Primary SRAM simulation entrypoint that loads YAML configs and runs transistor-level SRAM testbenches. | NETLIST_SOURCE | True | True |  |
| main_opt.py | IDENTIFIED | Interactive entrypoint that selects and launches SRAM sizing/architecture optimization demos. | SCRIPT_ENTRYPOINT | False | False |  |
| main_estimation.py | IDENTIFIED | Yield-estimation driver that runs SRAM failure-probability algorithms over SPICE-backed testbenches. | SCRIPT_ENTRYPOINT | False | False |  |
| equivalent_modeling/main_sram.py | IDENTIFIED | Studies or demonstrates equivalent-circuit acceleration for large SRAM simulations. | UTILITY | False | False |  |
| demo_run_a_testbench.py | IDENTIFIED | UNKNOWN | SCRIPT_ENTRYPOINT | False | False |  |
