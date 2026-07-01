# OpenYield Top/Bank Semantic Contract

## SRAM_TOP

- source_mapping: `Sram6TCoreTestbench.create_testbench()`
- bank_model: `contains exactly one implicit BANK object`

## BANK

- explicit_openyield_class_exists: `False`
- bank_count_supported: `1`
- bank_count_gt_1: `unsupported`

## Ports

- power: `['VDD', 'VSS']`
- clock: `['clk']`
- control: `['csb', 'web']`
- address: `A[i]`
- write_data: `DIN[i]`
- read_output_semantic_path: `['sense_amp.Q', 'D_latch.OUT / observation path']`
- storage_array: `['BL[i]', 'BLB[i]', 'WL[i]']`
- replica: `['RBL', 'RBLB', 'RWL']`
- internal_control_timing: `['gated_clk_bar', 'gated_clk_buf', 'wl_en', 'PRE', 's_en', 'w_en', 'rbl_delay', 'rbl_delay_bar']`
